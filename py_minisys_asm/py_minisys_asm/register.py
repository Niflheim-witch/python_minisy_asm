#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minisys Register Definitions
"""

from .utils import assert_, dec_to_bin


# Register names in order
register_names = [
    'zero', 'at',
    'v0', 'v1',
    'a0', 'a1', 'a2', 'a3',
    't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7',
    's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7',
    't8', 't9',
    'k0', 'k1',
    'gp', 'sp', 'fp',
    'ra',
]


def reg_to_bin(reg: str) -> str:
    """
    Convert register name/number to 5-bit binary
    
    @example: $1, 1, sp, $sp
    """
    # Handle None case - default to $zero
    if reg is None:
        return dec_to_bin(0, 5)  # $zero is register 0
    
    # Remove $ and whitespace
    reg = reg.replace('$', '').strip()
    
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