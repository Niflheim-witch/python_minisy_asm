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
