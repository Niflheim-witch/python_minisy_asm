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
USER_SIZE = 0x0000E800       # 58KB user program space
INT_ADDR = 0x0000F000        # Interrupt handler starting address
INT_SIZE = 0x00001000        # 4KB interrupt handler space
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
    bios_instructions = _load_bios()
    
    # Check if 'main' label exists and patch BIOS jump target
    # This is to support hardware that starts execution at a specific address (e.g. 0x2000)
    # and needs to jump to the actual main function which might not be at 0x2800
    if 'main' in asm_program.text_seg.labels:
        main_offset = asm_program.text_seg.labels['main']
        print(f"DEBUG: Found main at offset {main_offset}")
        # Physical Address Calculation:
        # Base (BIOS Start) = 0x2000 (800 words, per user hardware spec)
        # User Offset = 0x800 (Size of BIOS in logic space)
        # Main Offset = asm_program.text_seg.labels['main']
        target_addr = 0x2000 + 0x800 + main_offset
        print(f"DEBUG: Target address {hex(target_addr)}")
        
        # Calculate hi20 and lo12 for lui/addi (handling sign extension)
        # If lo_12 is negative (bit 11 is 1), addi will subtract, so we need to add 1 to hi_20
        # hi_20 = (target_addr + 0x800) >> 12
        # lo_12 = target_addr & 0xFFF
        
        # Adjust lo_12 for assembler (it expects signed integer for addi)
        # If lo_12 >= 2048 (0x800), it represents a negative number in 12-bit 2's complement
        # if lo_12 >= 0x800:
        #    lo_12_signed = lo_12 - 0x1000
        # else:
        #    lo_12_signed = lo_12
            
        print(f"DEBUG: Using JAL instruction for main jump")
        
        # Calculate Jump Offset for JAL
        # Target Address = 0x2000 (Base) + 0x800 (User Offset) + main_offset
        # Current PC = 0x2000
        # Offset = Target - PC = 0x800 + main_offset
        jump_offset = 0x800 + main_offset
        
        # JAL Instruction Encoding (J-type)
        # 31    | 30:21     | 20      | 19:12      | 11:7 | 6:0
        # imm[20] | imm[10:1] | imm[11] | imm[19:12] | rd   | opcode
        
        imm = jump_offset
        rd = 1      # x1 (ra) - Use Call convention instead of Jump
        opcode = 0x6F # 1101111 (JAL)
        
        imm_20 = (imm >> 20) & 1
        imm_10_1 = (imm >> 1) & 0x3FF
        imm_11 = (imm >> 11) & 1
        imm_19_12 = (imm >> 12) & 0xFF
        
        inst_val = (imm_20 << 31) | (imm_10_1 << 21) | (imm_11 << 20) | (imm_19_12 << 12) | (rd << 7) | opcode
        jal_hex = f"{inst_val:08x}".lower()
        
        # Create patch instruction list (only 1 instruction)
        # We don't need the assembler here since we manually encoded it
        patch_instructions = [jal_hex]
        
        try:
            print(f"DEBUG: Patch manually encoded. JAL offset={jump_offset}, hex={jal_hex}")
            
            # Patch the beginning of BIOS instructions
            # First, fill the entire BIOS text region with Zeros (NOPs) for safety
            # But keep the size consistent
            bios_size_words = len(bios_instructions)
            for k in range(bios_size_words):
                bios_instructions[k] = '00000000'
                
            # Then apply the patch instructions at the beginning
            for i, instr_hex in enumerate(patch_instructions):
                if i < len(bios_instructions):
                    print(f"DEBUG: Patching BIOS[{i}]: -> {instr_hex}")
                    bios_instructions[i] = instr_hex
        except Exception as e:
            print(f"Warning: Failed to patch BIOS with main address: {e}")

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
    data_segment_start = 0x00010000  # Standard MIPS data segment address
    
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
    # PREFER custom BIOS if it exists (for debugging specific user programs)
    # Changed to use the MINIMAL jump BIOS (no stack init)
    custom_bios = os.path.join(snippet_path, 'custom_bios_minimal_jump.asm')
    bios_file = custom_bios if os.path.exists(custom_bios) else os.path.join(snippet_path, 'minisys-bios.asm')
    
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
             # Return empty BIOS if assembly resulted in no instructions
            print("Warning: BIOS assembly resulted in 0 instructions.")
            return ['00000000'] * (BIOS_SIZE // 4)
        
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
        # If unable to load real BIOS, return empty BIOS (all NOPs)
        print(f"Warning: Could not load BIOS: {e}")
        return ['00000000'] * (BIOS_SIZE // 4)

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

