#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minisys Linker Implementation
"""

import os
from typing import List, Dict, Tuple
from .assembler import AsmProgram, Assembler
from .instruction import Instruction


# Memory layout constants
BIOS_ADDR = 0x00000000       # BIOS starting address
BIOS_SIZE = 0x00000800       # 2KB BIOS
USER_ADDR = 0x00000800       # User program starting address
USER_SIZE = 0x0000F000       # 60KB user program space
INT_ADDR = 0x0000F000        # Interrupt handler starting address
INT_SIZE = 0x00000FFC        # 4KB interrupt handler space
TOTAL_MEM_SIZE = 0x00010000  # 64KB total memory


def count_ins(lines: List[str]) -> int:
    """
    Count the number of instructions after macro expansion
    """
    count = 0
    in_macro = False
    
    for line in lines:
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
        
        # Check for macro start/end
        if line.startswith('.macro'):
            in_macro = True
            continue
        if line == '.end_macro':
            in_macro = False
            continue
        
        # Skip macro definitions
        if in_macro:
            continue
        
        # Count instructions (skip labels)
        if not line.endswith(':'):
            # If it's not just a label, count as an instruction
            parts = line.split(':')
            if len(parts) == 1 or parts[1].strip():
                count += 1
    
    return count


def link_all(asm_program: AsmProgram, user_code_start: int = USER_ADDR, use_real_bios: bool = True) -> Tuple[List[str], List[int]]:
    """
    Link all segments together with BIOS and interrupt handlers
    
    Args:
        asm_program: Assembled program
        user_code_start: Starting address for user code
        use_real_bios: Whether to use real BIOS and interrupt handler files
        
    Returns:
        Tuple of (linked_hex_lines, data_map)
        linked_hex_lines: List of hex strings representing the full memory image
        data_map: List of data values for the data memory
    """
    # Create memory buffer (64KB)
    memory = ['00000000'] * (TOTAL_MEM_SIZE // 4)  # Each entry is 4 bytes
    data_map = []
    
    # 1. Add BIOS
    if use_real_bios:
        bios_instructions = _load_bios()
    else:
        bios_instructions = _create_simple_bios()
    
    # Add BIOS to memory
    for i, instr_hex in enumerate(bios_instructions):
        if i * 4 < BIOS_SIZE:
            memory[i] = instr_hex
    
    # 2. Add user program code
    user_code_index = user_code_start // 4
    
    # Check if user program fits
    if len(asm_program.text_seg.instructions) * 4 > USER_SIZE:
        raise ValueError(f"User program too large: {len(asm_program.text_seg.instructions) * 4} bytes, maximum is {USER_SIZE} bytes")
    
    # Add user instructions to memory
    for i, instruction in enumerate(asm_program.text_seg.instructions):
        try:
            memory[user_code_index + i] = instruction.to_hex(zero_x=False).lower()
        except Exception as e:
            raise ValueError(f"Error converting instruction {i} to hex: {str(e)}")
    
    # 3. Add interrupt handler
    if use_real_bios:
        int_instructions = _load_interrupt_handler()
    else:
        int_instructions = ['00000000'] * (INT_SIZE // 4)  # NOP填充
    
    # Add interrupt handler to memory
    int_code_index = INT_ADDR // 4
    for i, instr_hex in enumerate(int_instructions):
        if int_code_index + i < len(memory):
            memory[int_code_index + i] = instr_hex
    int_index = INT_ADDR // 4
    
    # Create simple interrupt handler that does nothing but return
    # This is a placeholder
    int_handler = [
        '00000000',  # nop
        '00000000',  # nop
        '00000000',  # nop
        '00000000',  # nop
        '00000000',  # nop
        '00000000',  # nop
        '00000000',  # nop
        '00000000'   # nop
    ]
    
    for i, instr_hex in enumerate(int_handler):
        if int_index + i < len(memory):
            memory[int_index + i] = instr_hex
    
    # 4. Create data map for data memory
    # Extract data segment values
    data_segment_start = 0x10010000  # Standard MIPS data segment address
    
    # Process each variable in data segment
    for var_name, components in sorted(asm_program.data_seg.vars.items(), 
                                     key=lambda x: asm_program.data_seg.addrs[x[0]]):
        var_addr = asm_program.data_seg.addrs[var_name]
        
        for comp in components:
            # Generate data values based on component type
            if comp.type == 'byte':
                # Convert byte value to hex (1 byte)
                try:
                    # Handle both numeric and character literals
                    if isinstance(comp.value, str):
                        # Check if it's a character in quotes
                        if comp.value.startswith('"') and comp.value.endswith('"'):
                            val = ord(comp.value[1:-1])
                        elif comp.value.startswith('\'') and comp.value.endswith('\''):
                            val = ord(comp.value[1:-1])
                        else:
                            # Try to parse as number
                            val = int(comp.value, 0)  # Auto-detect base
                    else:
                        val = int(comp.value)
                    
                    # Add to data map (only lower 8 bits)
                    data_map.append(val & 0xFF)
                    
                except ValueError as e:
                    raise ValueError(f"Invalid byte value: {comp.value}")
            
            elif comp.type == 'half':
                # Convert half value to hex (2 bytes)
                try:
                    val = int(comp.value, 0) if isinstance(comp.value, str) else int(comp.value)
                    
                    # Add to data map (lower 16 bits, split into two bytes)
                    data_map.append((val >> 8) & 0xFF)  # High byte
                    data_map.append(val & 0xFF)        # Low byte
                    
                except ValueError as e:
                    raise ValueError(f"Invalid half value: {comp.value}")
            
            elif comp.type == 'word':
                # Convert word value to hex (4 bytes)
                try:
                    val = int(comp.value, 0) if isinstance(comp.value, str) else int(comp.value)
                    
                    # Add to data map (32 bits, split into four bytes)
                    data_map.append((val >> 24) & 0xFF)  # Byte 3
                    data_map.append((val >> 16) & 0xFF)  # Byte 2
                    data_map.append((val >> 8) & 0xFF)   # Byte 1
                    data_map.append(val & 0xFF)          # Byte 0
                    
                except ValueError as e:
                    raise ValueError(f"Invalid word value: {comp.value}")
            
            elif comp.type == 'asciiz':
                # Convert string to ASCII bytes, add null terminator
                string_val = comp.value
                for char in string_val:
                    data_map.append(ord(char))
                # Add null terminator
                data_map.append(0)
            
            elif comp.type == 'space':
                # Add zeros for space
                size = int(comp.value)
                data_map.extend([0] * size)
            
            else:
                raise ValueError(f"Unknown data type: {comp.type}")
    
    # Ensure data map doesn't exceed memory limits
    max_data_size = 0x00100000  # 1MB data segment (simplified)
    if len(data_map) > max_data_size:
        raise ValueError(f"Data segment too large: {len(data_map)} bytes")
    
    return memory, data_map


def _get_snippet_path() -> str:
    """
    获取snippet目录的路径
    """
    # 尝试从包内获取snippet目录
    snippet_path = os.path.join(os.path.dirname(__file__), 'snippet')
    
    # 如果包内不存在，尝试使用根目录下的package/snippet
    if not os.path.exists(snippet_path):
        snippet_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'package', 'snippet')
    
    return snippet_path

def _load_bios() -> List[str]:
    """
    加载并汇编真实的BIOS文件
    
    Returns:
        List of hex instruction strings
    """
    snippet_path = _get_snippet_path()
    bios_file = os.path.join(snippet_path, 'minisys-bios.asm')
    
    try:
        # 读取BIOS文件内容
        with open(bios_file, 'r', encoding='utf-8') as f:
            bios_code = f.read()
        
        # 汇编BIOS代码
        assembler = Assembler()
        bios_program = assembler.assemble(bios_code)
        
        # 检查汇编后的指令数量
        instr_count = len(bios_program.text_seg.instructions)
        
        if instr_count == 0:
            # 尝试使用简化的BIOS
            return _create_simple_bios()
        
        # 转换为十六进制指令
        bios_hex = []
        for i, instr in enumerate(bios_program.text_seg.instructions):
            try:
                hex_val = instr.to_hex(zero_x=False).lower()
                bios_hex.append(hex_val)
            except Exception:
                bios_hex.append('00000000')  # 出错时使用NOP
        
        # 填充BIOS区域
        while len(bios_hex) * 4 < BIOS_SIZE:
            bios_hex.append('00000000')  # nop
        
        # 限制在BIOS大小内
        result = bios_hex[:BIOS_SIZE // 4]
        return result
    except Exception as e:
        # 如果无法加载真实BIOS，使用简化版本
        return _create_simple_bios()

def _load_interrupt_handler() -> List[str]:
    """
    加载并汇编真实的中断处理程序
    
    Returns:
        List of hex instruction strings
    """
    snippet_path = _get_snippet_path()
    entry_file = os.path.join(snippet_path, 'minisys-interrupt-entry.asm')
    handler_file = os.path.join(snippet_path, 'minisys-interrupt-handler.asm')
    
    try:
        # 读取中断处理程序文件内容
        with open(entry_file, 'r', encoding='utf-8') as f:
            entry_code = f.read()
        
        with open(handler_file, 'r', encoding='utf-8') as f:
            handler_code = f.read()
        
        # 合并中断处理程序代码
        int_code = entry_code + '\n' + handler_code
        
        # 汇编中断处理程序代码
        assembler = Assembler()
        int_program = assembler.assemble(int_code)
        
        # 转换为十六进制指令
        int_hex = []
        for instr in int_program.text_seg.instructions:
            try:
                int_hex.append(instr.to_hex(zero_x=False).lower())
            except Exception:
                int_hex.append('00000000')  # 出错时使用NOP
        
        # 填充中断处理程序区域
        while len(int_hex) * 4 < INT_SIZE:
            int_hex.append('00000000')  # nop
        
        # 限制在中断处理程序大小内
        return int_hex[:INT_SIZE // 4]
    except Exception as e:
        # 如果无法加载真实中断处理程序，使用NOP填充
        return ['00000000'] * (INT_SIZE // 4)

def _create_simple_bios() -> List[str]:
    """
    创建简化版本的BIOS作为备用
    
    Returns:
        List of hex instruction strings
    """
    bios = []
    
    # 初始化栈指针
    bios.append('3C1C0001')  # lui $sp, 1
    
    # 显示'SEU61522'
    # 简化版本只显示字符串
    bios.append('34085345')  # li $t0, 0x5345  # 'SE'
    bios.append('00000000')  # nop
    bios.append('34085530')  # li $t0, 0x5530  # 'U0'
    bios.append('00000000')  # nop
    bios.append('34083931')  # li $t0, 0x3931  # '91'
    bios.append('00000000')  # nop
    bios.append('34083732')  # li $t0, 0x3732  # '72'
    bios.append('00000000')  # nop
    
    # 跳转到用户代码 (0x00000800)
    bios.append('08000200')  # j 0x00000800
    
    # 填充BIOS区域
    while len(bios) * 4 < BIOS_SIZE:
        bios.append('00000000')  # nop
    
    return bios[:BIOS_SIZE // 4]