#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minisys Instruction Definitions
"""

import re
from typing import List, Dict, Callable, Any
from .register import reg_to_bin
from .utils import assert_, bin_to_hex, label_to_bin, literal_to_bin, var_to_addr_bin


# Define instruction component types
InstructionComponentType = str  # 'fixed', 'reg', 'immed', 'c0sel', 'offset', 'addr', 'shamt', 'code'


class InstructionComponent:
    """
    Instruction Component
    """
    def __init__(self, l_bit: int, r_bit: int, desc: str, to_binary: Callable, 
                 type_: InstructionComponentType, val: str):
        self.l_bit = l_bit        # Left bit position (higher)
        self.r_bit = r_bit        # Right bit position (lower)
        self.desc = desc          # Component description
        self.to_binary = to_binary  # Function to calculate binary value
        self.type = type_         # Component type
        self.val = val            # Component value (empty for variable)


class Instruction:
    """
    Instruction class
    """
    def __init__(self, symbol: str, desc: str, pseudo: str, ins_pattern: re.Pattern, 
                 components: List[InstructionComponent]):
        self._symbol = symbol          # Instruction mnemonic
        self._desc = desc              # Instruction description
        self._pseudo = pseudo          # Instruction pseudocode
        self._ins_pattern = ins_pattern  # Regular expression pattern
        # Create copies of components
        self._components = []
        for comp in components:
            self._components.append(InstructionComponent(
                comp.l_bit, comp.r_bit, comp.desc,
                comp.to_binary, comp.type, comp.val
            ))
    
    @classmethod
    def new_instance(cls, base_on):
        """Create a new instance based on another instruction"""
        return cls(
            base_on.symbol, base_on.desc, base_on.pseudo,
            base_on.ins_pattern, base_on.components
        )
    
    @property
    def symbol(self) -> str:
        return self._symbol
    
    @symbol.setter
    def symbol(self, symbol: str):
        self._symbol = symbol
    
    @property
    def desc(self) -> str:
        return self._desc
    
    @desc.setter
    def desc(self, desc: str):
        self._desc = desc
    
    @property
    def pseudo(self) -> str:
        return self._pseudo
    
    @pseudo.setter
    def pseudo(self, pseudo: str):
        self._pseudo = pseudo
    
    @property
    def ins_pattern(self) -> re.Pattern:
        return self._ins_pattern
    
    @ins_pattern.setter
    def ins_pattern(self, ins_pattern: re.Pattern):
        self._ins_pattern = ins_pattern
    
    @property
    def components(self) -> List[InstructionComponent]:
        return self._components
    
    @components.setter
    def components(self, components: List[InstructionComponent]):
        self._components = components
    
    def set_component(self, desc: str, val: str) -> None:
        """
        Set component value by description
        """
        index = next((i for i, comp in enumerate(self._components) 
                     if comp.desc == desc), None)
        assert_(index is not None, f"Unknown instruction component: {desc}")
        self._components[index].val = val
    
    def to_binary(self) -> str:
        """
        Convert instruction to binary
        """
        # Check if all components have values
        assert_(not any(not comp.val.strip() for comp in self._components),
                "Attempting to convert incomplete instruction to binary")
        
        # Concatenate all component values
        return ''.join(comp.val for comp in self._components)
    
    def to_hex(self, zero_x: bool = True) -> str:
        """
        Convert instruction to hexadecimal
        """
        return bin_to_hex(self.to_binary(), zero_x)


# Global regular expression matches for instruction parsing
_reg_matches = None


def set_reg_matches(matches):
    """Set the global register matches"""
    global _reg_matches
    # Ensure matches is a list with at least 7 elements to avoid index errors
    if isinstance(matches, list):
        # Pad with None if necessary
        while len(matches) < 7:
            matches.append(None)
    _reg_matches = matches
    # Ensure registers have valid values to prevent None issues in shift instructions


def noop() -> str:
    """No-operation function for fixed components"""
    return ""


# Define MinisysInstructions
MinisysInstructions = []


def new_instruction(symbol: str, desc: str, pseudo: str, 
                    ins_pattern: re.Pattern, 
                    components: List[tuple]) -> None:
    """
    Add a new instruction to MinisysInstructions
    """
    instruction_components = []
    for l_bit, r_bit, desc_, to_binary, type_, val in components:
        instruction_components.append(InstructionComponent(
            l_bit, r_bit, desc_, to_binary, type_, val
        ))
    MinisysInstructions.append(Instruction(
        symbol, desc, pseudo, ins_pattern, instruction_components
    ))


def param_pattern(num: int) -> re.Pattern:
    """
    Generate regex pattern for instruction parameters
    """
    if num < 1:
        return re.compile(r'^$')
    else:
        # Create pattern like ^([\w$-]+),([\w$-]+)$ for num parameters
        pattern = '^' + ','.join([r'([\w$-]+)' for _ in range(num)]) + '$'
        return re.compile(pattern)


# =================== R-type Instructions ===================

# Lambda functions for register extraction with global matches
def rs_to_bin():
    return reg_to_bin(_reg_matches[2])

def rt_to_bin():
    return reg_to_bin(_reg_matches[3])

def rd_to_bin():
    return reg_to_bin(_reg_matches[4])

def rs1_to_bin():
    return reg_to_bin(_reg_matches[1])

def rt1_to_bin():
    return reg_to_bin(_reg_matches[2])

def imm_to_bin(len_=16):
    # Ensure _reg_matches has enough elements and the appropriate element is not None
    if len(_reg_matches) > 6 and _reg_matches[6] is not None:
        return literal_to_bin(_reg_matches[6], len_)
    # Default to 0 if no immediate provided
    return '0' * len_

def offset_to_bin():
    # Import label_to_bin here to avoid circular import issues
    from .utils import label_to_bin
    # Try to get offset from the appropriate position
    if len(_reg_matches) > 6 and _reg_matches[6] is not None:
        return label_to_bin(_reg_matches[6], 16, True)
    # Default to 0
    return '0000000000000000'

def addr_to_bin():
    # Import label_to_bin here to avoid circular import issues
    from .utils import label_to_bin
    # Try to get address from the appropriate position
    if len(_reg_matches) > 1 and _reg_matches[1] is not None:
        return label_to_bin(_reg_matches[1], 26, False)
    # Default to 0
    return '0' * 26

def shamt_to_bin():
    # Ensure _reg_matches has at least 7 elements and the 7th element is not None
    if len(_reg_matches) > 6 and _reg_matches[6] is not None:
        return literal_to_bin(_reg_matches[6], 5)
    # Default to 0 if no shamt provided
    return '00000'

def c0sel_to_bin():
    return literal_to_bin(_reg_matches[3], 6)

def var_to_bin():
    return var_to_addr_bin(_reg_matches[6], 16)


# Add all R-type instructions
new_instruction('add', 'Word Addition', '(rd)←(rs)+(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '100000'],
])

new_instruction('addu', 'Unsigned Addition', '(rd)←(rs)+(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '100001'],
])

new_instruction('sub', 'Word Subtraction', '(rd)←(rs)-(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '100010'],
])

new_instruction('subu', 'Unsigned Subtraction', '(rd)←(rs)-(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '100011'],
])

new_instruction('and', 'Bitwise AND', '(rd)←(rs)&(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '100100'],
])

new_instruction('or', 'Bitwise OR', '(rd)←(rs)|(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '100101'],
])

new_instruction('xor', 'Bitwise XOR', '(rd)←(rs)^(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '100110'],
])

new_instruction('nor', 'Bitwise NOR', '(rd)←~((rs)|(rt))', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '100111'],
])

new_instruction('slt', 'Set Less Than', 'if (rs<rt) rd=1 else rd=0', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '101010'],
])

new_instruction('sltu', 'Set Less Than Unsigned', 'if (rs<rt) rd=1 else rd=0', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '101011'],
])

new_instruction('sll', 'Shift Left Logical', '(rd)←(rt)<<shamt', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', noop, 'fixed', '00000'],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', shamt_to_bin, 'shamt', ''],
    [5, 0, 'func', noop, 'fixed', '000000'],
])

new_instruction('srl', 'Shift Right Logical', '(rd)←(rt)>>_L shamt', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', noop, 'fixed', '00000'],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', shamt_to_bin, 'shamt', ''],
    [5, 0, 'func', noop, 'fixed', '000010'],
])

new_instruction('sra', 'Shift Right Arithmetic', '(rd)←(rt)>>_A shamt', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', noop, 'fixed', '00000'],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', shamt_to_bin, 'shamt', ''],
    [5, 0, 'func', noop, 'fixed', '000011'],
])

new_instruction('sllv', 'Shift Left Logical Variable', '(rd)←(rt)<<(rs)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '000100'],
])

new_instruction('srlv', 'Shift Right Logical Variable', '(rd)←(rt)>>_L (rs)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '000110'],
])

new_instruction('srav', 'Shift Right Arithmetic Variable', '(rd)←(rt)>>_A (rs)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '000111'],
])

new_instruction('mult', 'Multiply', '(HI,LO)←(rs)*(rt)', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs1_to_bin, 'reg', ''],
    [20, 16, 'rt', rt1_to_bin, 'reg', ''],
    [15, 6, 'rd+shamt', noop, 'fixed', '0000000000'],
    [5, 0, 'func', noop, 'fixed', '011000'],
])

new_instruction('multu', 'Multiply Unsigned', '(HI,LO)←(rs)*(rt)', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs1_to_bin, 'reg', ''],
    [20, 16, 'rt', rt1_to_bin, 'reg', ''],
    [15, 6, 'rd+shamt', noop, 'fixed', '0000000000'],
    [5, 0, 'func', noop, 'fixed', '011001'],
])

new_instruction('div', 'Divide', '(HI)←(rs)%(rt), (LO)←(rs)/(rt)', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs1_to_bin, 'reg', ''],
    [20, 16, 'rt', rt1_to_bin, 'reg', ''],
    [15, 6, 'rd+shamt', noop, 'fixed', '0000000000'],
    [5, 0, 'func', noop, 'fixed', '011010'],
])

new_instruction('divu', 'Divide Unsigned', '(HI)←(rs)%(rt), (LO)←(rs)/(rt)', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs1_to_bin, 'reg', ''],
    [20, 16, 'rt', rt1_to_bin, 'reg', ''],
    [15, 6, 'rd+shamt', noop, 'fixed', '0000000000'],
    [5, 0, 'func', noop, 'fixed', '011011'],
])

new_instruction('mfhi', 'Move From HI', '(rd)←(HI)', 
               param_pattern(1), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 16, 'rs+rt', noop, 'fixed', '0000000000'],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '010000'],
])

new_instruction('mflo', 'Move From LO', '(rd)←(LO)', 
               param_pattern(1), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 16, 'rs+rt', noop, 'fixed', '0000000000'],
    [15, 11, 'rd', rd_to_bin, 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '010010'],
])

new_instruction('mthi', 'Move To HI', '(HI)←(rs)', 
               param_pattern(1), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs1_to_bin, 'reg', ''],
    [20, 6, 'rt+rd+shamt', noop, 'fixed', '000000000000000'],
    [5, 0, 'func', noop, 'fixed', '010001'],
])

new_instruction('mtlo', 'Move To LO', '(LO)←(rs)', 
               param_pattern(1), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs1_to_bin, 'reg', ''],
    [20, 6, 'rt+rd+shamt', noop, 'fixed', '000000000000000'],
    [5, 0, 'func', noop, 'fixed', '010011'],
])

new_instruction('mfc0', 'Move From C0', '(rt)=C0 register value', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '010000'],
    [25, 21, 'rs', noop, 'fixed', '00000'],
    [20, 16, 'rt', lambda: reg_to_bin(_reg_matches[1]), 'reg', ''],
    [15, 11, 'rd', lambda: reg_to_bin(_reg_matches[2]), 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', c0sel_to_bin, 'c0sel', ''],
])

new_instruction('mtc0', 'Move To C0', 'C0 register value=(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '010000'],
    [25, 21, 'rs', noop, 'fixed', '00100'],
    [20, 16, 'rt', lambda: reg_to_bin(_reg_matches[1]), 'reg', ''],
    [15, 11, 'rd', lambda: reg_to_bin(_reg_matches[2]), 'reg', ''],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', c0sel_to_bin, 'c0sel', ''],
])

# =================== I-type Instructions ===================

new_instruction('addi', 'Add Immediate', '(rt)←(rs)+imm', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '001000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', imm_to_bin, 'immed', ''],
])

new_instruction('addiu', 'Add Immediate Unsigned', '(rt)←(rs)+imm', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '001001'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', imm_to_bin, 'immed', ''],
])

new_instruction('andi', 'AND Immediate', '(rt)←(rs)&imm', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '001100'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', imm_to_bin, 'immed', ''],
])

new_instruction('ori', 'OR Immediate', '(rt)←(rs)|imm', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '001101'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', imm_to_bin, 'immed', ''],
])

new_instruction('xori', 'XOR Immediate', '(rt)←(rs)^imm', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '001110'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', imm_to_bin, 'immed', ''],
])

new_instruction('slti', 'Set Less Than Immediate', 'if (rs<imm) rt=1 else rt=0', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '001010'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', imm_to_bin, 'immed', ''],
])

new_instruction('sltiu', 'Set Less Than Immediate Unsigned', 'if (rs<imm) rt=1 else rt=0', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '001011'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', imm_to_bin, 'immed', ''],
])

new_instruction('lw', 'Load Word', '(rt)←M[rs+imm]', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '100011'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', var_to_bin, 'offset', ''],
])

new_instruction('sw', 'Store Word', 'M[rs+imm]←(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '101011'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', var_to_bin, 'offset', ''],
])

new_instruction('lh', 'Load Halfword', '(rt)←M[rs+imm]', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '100001'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', var_to_bin, 'offset', ''],
])

new_instruction('lhu', 'Load Halfword Unsigned', '(rt)←M[rs+imm]', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '100101'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', var_to_bin, 'offset', ''],
])

new_instruction('lb', 'Load Byte', '(rt)←M[rs+imm]', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '100000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', var_to_bin, 'offset', ''],
])

new_instruction('lbu', 'Load Byte Unsigned', '(rt)←M[rs+imm]', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '100100'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', var_to_bin, 'offset', ''],
])

new_instruction('sh', 'Store Halfword', 'M[rs+imm]←(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '101001'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', var_to_bin, 'offset', ''],
])

new_instruction('sb', 'Store Byte', 'M[rs+imm]←(rt)', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '101000'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', var_to_bin, 'offset', ''],
])

new_instruction('beq', 'Branch on Equal', 'if (rs==rt) PC=PC+4+imm*4', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000100'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', offset_to_bin, 'offset', ''],
])

new_instruction('bne', 'Branch on Not Equal', 'if (rs!=rt) PC=PC+4+imm*4', 
               param_pattern(3), [
    [31, 26, 'op', noop, 'fixed', '000101'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', offset_to_bin, 'offset', ''],
])

new_instruction('bgez', 'Branch on Greater or Equal Zero', 'if (rs>=0) PC=PC+4+imm*4', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000001'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', noop, 'fixed', '00001'],
    [15, 0, 'imm', offset_to_bin, 'offset', ''],
])

new_instruction('bgtz', 'Branch on Greater Than Zero', 'if (rs>0) PC=PC+4+imm*4', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000111'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', noop, 'fixed', '00000'],
    [15, 0, 'imm', offset_to_bin, 'offset', ''],
])

new_instruction('blez', 'Branch on Less or Equal Zero', 'if (rs<=0) PC=PC+4+imm*4', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000110'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', noop, 'fixed', '00000'],
    [15, 0, 'imm', offset_to_bin, 'offset', ''],
])

new_instruction('bltz', 'Branch on Less Than Zero', 'if (rs<0) PC=PC+4+imm*4', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000001'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', noop, 'fixed', '00000'],
    [15, 0, 'imm', offset_to_bin, 'offset', ''],
])

new_instruction('lui', 'Load Upper Immediate', '(rt)←imm<<16', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '001111'],
    [25, 21, 'rs', noop, 'fixed', '00000'],
    [20, 16, 'rt', rt_to_bin, 'reg', ''],
    [15, 0, 'imm', imm_to_bin, 'immed', ''],
])

new_instruction('bgezal', 'Branch on Greater or Equal Zero and Link', 'R31=PC+8; if (rs>=0) PC=PC+4+imm*4', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000001'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', noop, 'fixed', '10001'],
    [15, 0, 'imm', offset_to_bin, 'offset', ''],
])

new_instruction('bltzal', 'Branch on Less Than Zero and Link', 'R31=PC+8; if (rs<0) PC=PC+4+imm*4', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000001'],
    [25, 21, 'rs', rs_to_bin, 'reg', ''],
    [20, 16, 'rt', noop, 'fixed', '10000'],
    [15, 0, 'imm', offset_to_bin, 'offset', ''],
])

new_instruction('eret', 'Exception Return', 'PC=EPC; Restore Status', 
               param_pattern(0), [
    [31, 26, 'op', noop, 'fixed', '010000'],
    [25, 16, 'rs+rt', noop, 'fixed', '0000000000'],
    [15, 11, 'rd', noop, 'fixed', '00000'],
    [10, 6, 'shamt', noop, 'fixed', '00000'],
    [5, 0, 'func', noop, 'fixed', '011000'],
])

# =================== J-type Instructions ===================

new_instruction('j', 'Jump', 'PC=PC[31:28]||addr||00', 
               param_pattern(1), [
    [31, 26, 'op', noop, 'fixed', '000010'],
    [25, 0, 'addr', addr_to_bin, 'addr', ''],
])

new_instruction('jal', 'Jump and Link', 'R31=PC+8; PC=PC[31:28]||addr||00', 
               param_pattern(1), [
    [31, 26, 'op', noop, 'fixed', '000011'],
    [25, 0, 'addr', addr_to_bin, 'addr', ''],
])

# =================== Special Instructions ===================

new_instruction('jr', 'Jump Register', 'PC=(rs)', 
               param_pattern(1), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs1_to_bin, 'reg', ''],
    [20, 6, 'rt+rd+shamt', noop, 'fixed', '000000000000000'],
    [5, 0, 'func', noop, 'fixed', '001000'],
])

new_instruction('jalr', 'Jump and Link Register', 'R31=PC+8; PC=(rs)', 
               param_pattern(2), [
    [31, 26, 'op', noop, 'fixed', '000000'],
    [25, 21, 'rs', rs1_to_bin, 'reg', ''],
    [20, 16, 'rt', rt1_to_bin, 'reg', ''],
    [15, 6, 'rd+shamt', noop, 'fixed', '0000000000'],
    [5, 0, 'func', noop, 'fixed', '001001'],
])

new_instruction('syscall', 'System Call', 'Invoke System Call', 
               param_pattern(0), [
    [31, 0, 'all', noop, 'fixed', '00000000000000000000000000110000'],
])

new_instruction('nop', 'No Operation', 'No Operation', 
               param_pattern(0), [
    [31, 0, 'all', noop, 'fixed', '00000000000000000000000000000000'],
])

new_instruction('break', 'Breakpoint', 'Breakpoint', 
               param_pattern(0), [
    [31, 0, 'all', noop, 'fixed', '00000000000000000000000000001101'],
])