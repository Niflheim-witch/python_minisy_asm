#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minisys Register Definitions
"""

from .utils import assert_, dec_to_bin


# Register names in order
register_names = [
    'x0',    # 零寄存器（hardwired zero）
    'x1',    # 返回地址（return address）
    'x2',    # 栈指针（stack pointer）
    'x3',    # 全局指针（global pointer）
    'x4',    # 线程指针（thread pointer）
    'x5',    # t0（临时寄存器）
    'x6',    # t1（临时寄存器）
    'x7',    # t2（临时寄存器）
    'x8',    # s0/fp（保存寄存器/帧指针）
    'x9',    # s1（保存寄存器）
    'x10',   # a0（函数参数/返回值）
    'x11',   # a1（函数参数/返回值）
    'x12',   # a2（函数参数）
    'x13',   # a3（函数参数）
    'x14',   # a4（函数参数）
    'x15',   # a5（函数参数）
    'x16',   # a6（函数参数）
    'x17',   # a7（函数参数）
    'x18',   # s2（保存寄存器）
    'x19',   # s3（保存寄存器）
    'x20',   # s4（保存寄存器）
    'x21',   # s5（保存寄存器）
    'x22',   # s6（保存寄存器）
    'x23',   # s7（保存寄存器）
    'x24',   # s8（保存寄存器）
    'x25',   # s9（保存寄存器）
    'x26',   # s10（保存寄存器）
    'x27',   # s11（保存寄存器）
    'x28',   # t3（临时寄存器）
    'x29',   # t4（临时寄存器）
    'x30',   # t5（临时寄存器）
    'x31',   # t6（临时寄存器）
]


def reg_to_bin(reg: str) -> str:
    """
    将RV32I寄存器名或编号转换为5位二进制
    
    @example: x1, 1, sp, zero
    """
    # Handle None case - default to x0
    if reg is None:
        return dec_to_bin(0, 5)  # x0 is register 0
    
    # Remove whitespace
    reg = reg.strip().lower()
    
    # RISC-V 寄存器别名映射
    aliases = {
        'zero': 'x0',
        'ra': 'x1',
        'sp': 'x2',
        'gp': 'x3',
        'tp': 'x4',
        't0': 'x5',
        't1': 'x6',
        't2': 'x7',
        's0': 'x8',
        'fp': 'x8',  # 别名：帧指针
        's1': 'x9',
        'a0': 'x10',
        'a1': 'x11',
        'a2': 'x12',
        'a3': 'x13',
        'a4': 'x14',
        'a5': 'x15',
        'a6': 'x16',
        'a7': 'x17',
        's2': 'x18',
        's3': 'x19',
        's4': 'x20',
        's5': 'x21',
        's6': 'x22',
        's7': 'x23',
        's8': 'x24',
        's9': 'x25',
        's10': 'x26',
        's11': 'x27',
        't3': 'x28',
        't4': 'x29',
        't5': 'x30',
        't6': 'x31'
    }
    
    # 如果是别名，转换为标准名称
    if reg in aliases:
        reg = aliases[reg]
    
    try:
        # Try to parse as number
        reg_number = int(reg)
    except ValueError:
        # Try to find by name
        if reg not in register_names:
            assert_(False, f"Invalid register name: {reg}")
        reg_number = register_names.index(reg)
    
    # Validate register number
    assert_(reg_number >= 0 and reg_number <= 31, f"Invalid register: {reg}")
    
    # Convert to 5-bit binary
    return dec_to_bin(reg_number, 5)