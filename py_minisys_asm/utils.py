#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minisys Assembler Utility Functions
"""

import re
from typing import Any, Dict, List, Tuple, Union, Optional


class SevereError(Exception):
    """Severe error that should terminate the assembler"""
    pass


class AssemblerError(Exception):
    """Generic assembler error"""
    pass


class Warning(Exception):
    """Warning message"""
    pass


# Assertion function with message
def assert_(condition: bool, message: str) -> None:
    """Assert with custom message"""
    if not condition:
        raise SevereError(message)


# Get size of data types
def sizeof(type_: str) -> int:
    """Get size in bytes of a data type"""
    sizes = {
        'byte': 1,
        'half': 2,
        'word': 4,
        'asciiz': 1,  # per character, plus null terminator
        'space': 1    # per byte
    }
    return sizes.get(type_, 0)


# Get offset for data types
def get_offset(type_: str) -> int:
    """Get offset alignment for data types"""
    offsets = {
        'byte': 1,
        'half': 2,
        'word': 4,
        'asciiz': 1,
        'space': 1
    }
    return offsets.get(type_, 0)


# Convert a literal value to binary
def literal_to_bin(value: str, width: int, signed: bool = False) -> str:
    """Convert a literal value to binary string with specified width"""
    try:
        # Handle hexadecimal values
        is_hex = False
        if value.startswith('0x') or value.startswith('0X'):
            num = int(value[2:], 16)
            is_hex = True
        # Handle binary values
        elif value.startswith('0b') or value.startswith('0B'):
            num = int(value[2:], 2)
        # Handle decimal values
        elif value.startswith('+') or value.startswith('-') or value.isdigit():
            num = int(value)
        else:
            # Try to parse as character if it's a single quote
            if len(value) == 3 and value[0] == "'" and value[2] == "'":
                num = ord(value[1])
            else:
                raise ValueError(f"Invalid literal: {value}")
        
        # 特殊处理十六进制值：对于十六进制表示的数，直接截断到指定宽度
        if is_hex:
            # 直接保留低width位
            num = num & ((1 << width) - 1)
        elif signed:
            # 对于有符号十进制数，检查范围
            max_val = (1 << (width - 1)) - 1
            min_val = -(1 << (width - 1))
            
            # Check if value is within range
            if num < min_val or num > max_val:
                raise ValueError(f"Value {num} out of range for {width}-bit signed integer")
            
            # If negative, compute two's complement
            if num < 0:
                num = (1 << width) + num
        else:
            # For unsigned decimal values
            max_val = (1 << width) - 1
            if num < 0 or num > max_val:
                raise ValueError(f"Value {num} out of range for {width}-bit unsigned integer")
        
        # Convert to binary string with leading zeros
        binary_str = bin(num)[2:].zfill(width)
        
        # Ensure the binary string is exactly the requested width
        if len(binary_str) > width:
            binary_str = binary_str[-width:]
        return binary_str
    except Exception as e:
        raise AssemblerError(f"Error converting {value} to {width}-bit binary: {str(e)}")

# Decimal to binary conversion function (for backward compatibility)
def dec_to_bin(value: int, width: int) -> str:
    """Convert decimal number to binary string with specified width"""
    if value < 0:
        # Handle negative numbers using two's complement
        value = (1 << width) + value
    binary_str = bin(value)[2:].zfill(width)
    # Ensure the binary string is exactly the requested width
    if len(binary_str) > width:
        binary_str = binary_str[-width:]
    return binary_str

# Convert variable address to binary
def var_to_addr_bin(var_name: str, width: int) -> str:
    """Convert variable name to its address in binary"""
    # This function should get the variable address from the current assembler
    from .assembler import get_current_assembler
    assembler = get_current_assembler()
    if assembler and var_name in assembler.program.data_seg.addrs:
        addr = assembler.program.data_seg.addrs[var_name]
        return dec_to_bin(addr, width)
    raise AssemblerError(f"Undefined variable: {var_name}")

# Convert binary to hexadecimal (completely rewritten to ensure correctness)
def bin_to_hex(bin_str, zero_x=True):
    """Convert binary string to hexadecimal string with optional '0x' prefix"""
    # 对于RV32I指令，确保输出始终为8个十六进制字符（32位）
    # 首先确保二进制字符串为32位
    if len(bin_str) < 32:
        bin_str = bin_str.zfill(32)
    elif len(bin_str) > 32:
        bin_str = bin_str[-32:]
    
    # Convert to hexadecimal
    try:
        hex_str = hex(int(bin_str, 2))[2:].upper()
        # 确保十六进制字符串为8个字符
        hex_str = hex_str.zfill(8)
        # Add '0x' prefix if requested
        if zero_x:
            return '0x' + hex_str
        return hex_str
    except Exception as e:
        raise AssemblerError(f"Error converting binary to hex: {str(e)}")


# Get current assembler instance
# This is imported after definition in assembler.py to avoid circular import
def _get_current_assembler():
    """Get the current active assembler instance"""
    try:
        from .assembler import get_current_assembler
        return get_current_assembler()
    except ImportError:
        return None


# Convert a label to binary offset
def label_to_bin(label: str, width: int, is_branch_or_jump: bool = False) -> str:
    """Convert a label to binary offset with specified width
    
    Args:
        label: The label name
        width: The width of the binary string in bits
        is_branch_or_jump: Whether this is for a branch or jump instruction
    
    Returns:
        Binary string representation of the offset
    """
    # Get current assembler instance
    assembler = _get_current_assembler()
    if not assembler:
        raise SevereError("No active assembler instance found")
    
    # Get label address
    try:
        label_addr = assembler.get_label_addr(label)
    except SevereError:
        # Try to interpret as a number if label not found
        try:
            # Treat as immediate value if it's a number
            return literal_to_bin(label, width, True)
        except ValueError:
            raise SevereError(f"Undefined label: {label}")
    
    # Get current PC value
    current_pc = assembler.get_pc()
    
    # Calculate offset based on instruction type
    if is_branch_or_jump:
        # For branch instructions (B-type)
        if width == 12:
            # B-type branch: offset is (label_addr - (current_pc + 4)) // 2
            offset = (label_addr - (current_pc + 4)) // 2
        # For jump instructions (J-type)
        elif width == 20:
            # J-type jump: offset is (label_addr - (current_pc + 4)) // 2
            offset = (label_addr - (current_pc + 4)) // 2
        else:
            # Default to direct offset
            offset = label_addr - current_pc
    else:
        # Direct address for memory operations
        offset = label_addr
    
    # Convert to binary with proper handling of width
    try:
        binary_str = literal_to_bin(str(offset), width, True)
        
        # Ensure the binary string is exactly the requested width
        if len(binary_str) > width:
            binary_str = binary_str[-width:]
        elif len(binary_str) < width:
            # For signed values, sign-extend
            sign_bit = binary_str[0] if binary_str else '0'
            binary_str = binary_str.zfill(width)
            # If negative, fill with 1s
            if sign_bit == '1' and len(binary_str) < width:
                binary_str = sign_bit * (width - len(binary_str)) + binary_str
        
        return binary_str
    except ValueError as e:
        raise SevereError(f"Error converting label '{label}' to binary: {str(e)}")


# Check if a string is a valid register name
def is_valid_register(reg: str) -> bool:
    """Check if a string is a valid register name"""
    # Match RV32I register format (x0-x31)
    return bool(re.match(r'^[xX]([0-9]|[12][0-9]|3[01])$', reg))


# Check if a string is a valid label name
def is_valid_label(label: str) -> bool:
    """Check if a string is a valid label name"""
    # Label must start with letter or underscore, followed by letters, numbers, or underscores
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label))


# Check if a string is a valid immediate value
def is_valid_immediate(imm: str) -> bool:
    """Check if a string is a valid immediate value"""
    try:
        # Try to parse as integer
        # Handle hexadecimal
        if imm.startswith('0x') or imm.startswith('0X'):
            int(imm[2:], 16)
        # Handle binary
        elif imm.startswith('0b') or imm.startswith('0B'):
            int(imm[2:], 2)
        # Handle decimal
        else:
            int(imm)
        return True
    except ValueError:
        return False


# Helper function to handle sign extension
def sign_extend(value: str, from_width: int, to_width: int) -> str:
    """Sign-extend a binary string from from_width to to_width bits"""
    if len(value) != from_width:
        raise ValueError(f"Input value must be {from_width} bits long")
    
    # Get the sign bit
    sign_bit = value[0]
    
    # Extend with sign bit
    extended = sign_bit * (to_width - from_width) + value
    
    return extended


# Helper function to zero extend
def zero_extend(value: str, from_width: int, to_width: int) -> str:
    """Zero-extend a binary string from from_width to to_width bits"""
    if len(value) != from_width:
        raise ValueError(f"Input value must be {from_width} bits long")
    
    # Extend with zeros
    extended = value.zfill(to_width)
    
    return extended


# Helper function to split a binary string into parts for different instruction formats
def split_binary_for_format(binary: str, format_type: str) -> Dict[str, str]:
    """Split a binary string into parts according to RISC-V instruction format"""
    parts = {}
    
    # Ensure binary is 32 bits
    if len(binary) != 32:
        binary = binary.zfill(32)
        if len(binary) > 32:
            binary = binary[-32:]
    
    # Split based on format type
    if format_type == 'R':
        # R-type: 7 bits opcode, 5 bits rd, 3 bits funct3, 5 bits rs1, 5 bits rs2, 7 bits funct7
        parts = {
            'opcode': binary[25:32],
            'rd': binary[20:25],
            'funct3': binary[17:20],
            'rs1': binary[12:17],
            'rs2': binary[7:12],
            'funct7': binary[0:7]
        }
    elif format_type == 'I':
        # I-type: 7 bits opcode, 5 bits rd, 3 bits funct3, 5 bits rs1, 12 bits imm
        parts = {
            'opcode': binary[25:32],
            'rd': binary[20:25],
            'funct3': binary[17:20],
            'rs1': binary[12:17],
            'imm': binary[0:12]
        }
    elif format_type == 'S':
        # S-type: 7 bits opcode, 5 bits imm[4:0], 3 bits funct3, 5 bits rs1, 5 bits rs2, 7 bits imm[11:5]
        parts = {
            'opcode': binary[25:32],
            'imm[4:0]': binary[20:25],
            'funct3': binary[17:20],
            'rs1': binary[12:17],
            'rs2': binary[7:12],
            'imm[11:5]': binary[0:7]
        }
    elif format_type == 'B':
        # B-type: 7 bits opcode, 5 bits imm[11|4:1|12], 3 bits funct3, 5 bits rs1, 5 bits rs2, 7 bits imm[10:5]
        parts = {
            'opcode': binary[25:32],
            'imm[4:1|11]': binary[20:25],  # imm[11] followed by imm[4:1]
            'funct3': binary[17:20],
            'rs1': binary[12:17],
            'rs2': binary[7:12],
            'imm[12|10:5]': binary[0:7]   # imm[12] followed by imm[10:5]
        }
    elif format_type == 'U':
        # U-type: 7 bits opcode, 5 bits rd, 20 bits imm[31:12]
        parts = {
            'opcode': binary[25:32],
            'rd': binary[20:25],
            'imm[31:12]': binary[0:20]
        }
    elif format_type == 'J':
        # J-type: 7 bits opcode, 5 bits rd, 1 bit imm[20], 10 bits imm[10:1], 1 bit imm[11], 8 bits imm[19:12]
        parts = {
            'opcode': binary[25:32],
            'rd': binary[20:25],
            'imm[19:12]': binary[12:20],
            'imm[11]': binary[11:12],
            'imm[10:1]': binary[1:11],
            'imm[20]': binary[0:1]
        }
    
    return parts


# Helper function to combine binary parts into a single binary string
def combine_binary_parts(parts: Dict[str, str], format_type: str) -> str:
    """Combine binary parts into a single binary string according to RISC-V instruction format"""
    # Ensure all required parts are present
    required_parts = {}
    if format_type == 'R':
        required_parts = ['opcode', 'rd', 'funct3', 'rs1', 'rs2', 'funct7']
    elif format_type == 'I':
        required_parts = ['opcode', 'rd', 'funct3', 'rs1', 'imm']
    elif format_type == 'S':
        required_parts = ['opcode', 'imm[4:0]', 'funct3', 'rs1', 'rs2', 'imm[11:5]']
    elif format_type == 'B':
        required_parts = ['opcode', 'imm[4:1|11]', 'funct3', 'rs1', 'rs2', 'imm[12|10:5]']
    elif format_type == 'U':
        required_parts = ['opcode', 'rd', 'imm[31:12]']
    elif format_type == 'J':
        required_parts = ['opcode', 'rd', 'imm[19:12]', 'imm[11]', 'imm[10:1]', 'imm[20]']
    
    for part in required_parts:
        if part not in parts:
            raise ValueError(f"Missing required part: {part}")
    
    # Combine parts based on format type
    binary = ''
    if format_type == 'R':
        binary = parts['funct7'] + parts['rs2'] + parts['rs1'] + parts['funct3'] + parts['rd'] + parts['opcode']
    elif format_type == 'I':
        binary = parts['imm'] + parts['rs1'] + parts['funct3'] + parts['rd'] + parts['opcode']
    elif format_type == 'S':
        binary = parts['imm[11:5]'] + parts['rs2'] + parts['rs1'] + parts['funct3'] + parts['imm[4:0]'] + parts['opcode']
    elif format_type == 'B':
        binary = parts['imm[12|10:5]'] + parts['rs2'] + parts['rs1'] + parts['funct3'] + parts['imm[4:1|11]'] + parts['opcode']
    elif format_type == 'U':
        binary = parts['imm[31:12]'] + parts['rd'] + parts['opcode']
    elif format_type == 'J':
        binary = parts['imm[20]'] + parts['imm[10:1]'] + parts['imm[11]'] + parts['imm[19:12]'] + parts['rd'] + parts['opcode']
    
    # Ensure the binary string is 32 bits
    if len(binary) != 32:
        binary = binary.zfill(32)
        if len(binary) > 32:
            binary = binary[-32:]
    
    return binary


# Bin to hex conversion is handled by the earlier function definition


# Helper function to convert hexadecimal to binary
def hex_to_bin(hex_str: str, width: int = 32) -> str:
    """Convert a hexadecimal string to binary with specified width"""
    # Convert to binary
    binary = bin(int(hex_str, 16))[2:]
    
    # Ensure the binary string is exactly the requested width
    binary = binary.zfill(width)
    if len(binary) > width:
        binary = binary[-width:]
    
    return binary


# Helper function to calculate twos complement
def twos_complement(value: str, width: int) -> str:
    """Calculate two's complement of a binary string"""
    # Ensure binary string is the correct width
    value = value.zfill(width)
    if len(value) > width:
        value = value[-width:]
    
    # Invert all bits
    inverted = ''.join('1' if bit == '0' else '0' for bit in value)
    
    # Add 1
    # Convert to integer, add 1, convert back to binary
    result = bin(int(inverted, 2) + 1)[2:]
    
    # Ensure the result is the correct width
    result = result.zfill(width)
    if len(result) > width:
        result = result[-width:]
    
    return result


# Helper function to format binary output
def format_binary(binary: str, group_size: int = 4) -> str:
    """Format a binary string by grouping bits"""
    # Remove any existing spaces
    binary = binary.replace(' ', '')
    
    # Group bits
    groups = [binary[i:i+group_size] for i in range(0, len(binary), group_size)]
    
    # Join groups with spaces
    formatted = ' '.join(groups)
    
    return formatted