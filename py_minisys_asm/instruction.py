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

# Lambda functions for register extraction with global matches (RV32I format)
def rs1_to_bin():
    # For R-type: instruction rd, rs1, rs2
    # For I-type: instruction rd, rs1, imm
    # _reg_matches[1] = rd, _reg_matches[2] = rs1, _reg_matches[3] = rs2
    return reg_to_bin(_reg_matches[2]) if len(_reg_matches) > 2 else reg_to_bin(None)

def rs2_to_bin():
    # For R-type: instruction rd, rs1, rs2
    # For S-type: instruction rs2, imm(rs1)
    return reg_to_bin(_reg_matches[3]) if len(_reg_matches) > 3 else reg_to_bin(None)

def rd_to_bin():
    # For R-type: instruction rd, rs1, rs2
    # For I-type: instruction rd, rs1, imm
    # For U-type and J-type: instruction rd, imm
    return reg_to_bin(_reg_matches[1]) if len(_reg_matches) > 1 else reg_to_bin(None)

def imm_to_bin(len_=12):
    # Ensure _reg_matches has enough elements and the appropriate element is not None
    if len(_reg_matches) > 6 and _reg_matches[6] is not None:
        # RISC-V立即数通常是有符号的
        return literal_to_bin(_reg_matches[6], len_, signed=True)
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

def var_to_bin():
    return var_to_addr_bin(_reg_matches[6], 16)


# =================== RV32I R-type Instructions ===================
# Format: funct7 | rs2 | rs1 | funct3 | rd | opcode

# ADD - rd, rs1, rs2
new_instruction('add', 'Word Addition', '(rd)←(rs1)+(rs2)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],  # funct7 for ADD
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '000'],       # funct3 for ADD/SUB
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# SUB - rd, rs1, rs2
new_instruction('sub', 'Word Subtraction', '(rd)←(rs1)-(rs2)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0100000'],  # funct7 for SUB
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '000'],       # funct3 for ADD/SUB
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# SLL - rd, rs1, rs2
new_instruction('sll', 'Shift Left Logical', '(rd)←(rs1)<<(rs2[4:0])', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],  # funct7 for SLL
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '001'],       # funct3 for SLL
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# SLT - rd, rs1, rs2
new_instruction('slt', 'Set Less Than', 'if (rs1<rs2) rd=1 else rd=0 (signed)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],  # funct7 for SLT
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '010'],       # funct3 for SLT
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# SLTU - rd, rs1, rs2
new_instruction('sltu', 'Set Less Than Unsigned', 'if (rs1<rs2) rd=1 else rd=0 (unsigned)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],  # funct7 for SLTU
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '011'],       # funct3 for SLTU
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# XOR - rd, rs1, rs2
new_instruction('xor', 'Bitwise XOR', '(rd)←(rs1)^(rs2)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],  # funct7 for XOR
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '100'],       # funct3 for XOR
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# SRL - rd, rs1, rs2
new_instruction('srl', 'Shift Right Logical', '(rd)←(rs1)>>_L (rs2[4:0])', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],  # funct7 for SRL
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '101'],       # funct3 for SRL/SRA
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# SRA - rd, rs1, rs2
new_instruction('sra', 'Shift Right Arithmetic', '(rd)←(rs1)>>_A (rs2[4:0])', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0100000'],  # funct7 for SRA
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '101'],       # funct3 for SRL/SRA
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# OR - rd, rs1, rs2
new_instruction('or', 'Bitwise OR', '(rd)←(rs1)|(rs2)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],  # funct7 for OR
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '110'],       # funct3 for OR
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# AND - rd, rs1, rs2
new_instruction('and', 'Bitwise AND', '(rd)←(rs1)&(rs2)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],  # funct7 for AND
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '111'],       # funct3 for AND
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],     # R-type opcode
])

# =================== End of RV32I R-type Instructions ===================

# =================== RV32M Instructions (Multiplication and Division) ===================
# Format: funct7 | rs2 | rs1 | funct3 | rd | opcode
# Opcode: 0110011 (same as R-type arithmetic)
# Funct7: 0000001 (MULDIV)

# MUL - rd, rs1, rs2
new_instruction('mul', 'Multiply', '(rd)←(rs1)*(rs2) (low 32 bits)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000001'],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],
])

# MULH - rd, rs1, rs2
new_instruction('mulh', 'Multiply High Signed', '(rd)←((rs1)*(rs2)) >> 32 (signed)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000001'],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '001'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],
])

# MULHSU - rd, rs1, rs2
new_instruction('mulhsu', 'Multiply High Signed-Unsigned', '(rd)←((rs1)*(rs2)) >> 32 (signed x unsigned)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000001'],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '010'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],
])

# MULHU - rd, rs1, rs2
new_instruction('mulhu', 'Multiply High Unsigned', '(rd)←((rs1)*(rs2)) >> 32 (unsigned)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000001'],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '011'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],
])

# DIV - rd, rs1, rs2
new_instruction('div', 'Divide Signed', '(rd)←(rs1)/(rs2) (signed)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000001'],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '100'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],
])

# DIVU - rd, rs1, rs2
new_instruction('divu', 'Divide Unsigned', '(rd)←(rs1)/(rs2) (unsigned)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000001'],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '101'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],
])

# REM - rd, rs1, rs2
new_instruction('rem', 'Remainder Signed', '(rd)←(rs1)%(rs2) (signed)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000001'],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '110'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],
])

# REMU - rd, rs1, rs2
new_instruction('remu', 'Remainder Unsigned', '(rd)←(rs1)%(rs2) (unsigned)', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000001'],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '111'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110011'],
])

# =================== RV32I I-type Instructions ===================
# Format: imm[11:0] | rs1 | funct3 | rd | opcode

# I型指令 (加载指令)
new_instruction('lb', 'Load Byte', '(rd)←M[rs1+imm]', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],  # imm[11:0]
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0000011'],
])

new_instruction('lh', 'Load Halfword', '(rd)←M[rs1+imm]', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '001'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0000011'],
])

new_instruction('lw', 'Load Word', '(rd)←M[rs1+imm]', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '010'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0000011'],
])

new_instruction('lbu', 'Load Byte Unsigned', '(rd)←M[rs1+imm]', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '100'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0000011'],
])

new_instruction('lhu', 'Load Halfword Unsigned', '(rd)←M[rs1+imm]', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '101'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0000011'],
])

# I型指令 (算术/逻辑立即数指令)
new_instruction('addi', 'Add Immediate', '(rd)←rs1 + imm', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

new_instruction('slti', 'Set Less Than Immediate', 'if (rs1<imm) rd=1 else rd=0', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '010'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

new_instruction('sltiu', 'Set Less Than Immediate Unsigned', 'if (rs1<imm) rd=1 else rd=0', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '011'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

new_instruction('xori', 'Xor Immediate', '(rd)←rs1 ^ imm', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '100'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

new_instruction('ori', 'Or Immediate', '(rd)←rs1 | imm', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '110'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

new_instruction('andi', 'And Immediate', '(rd)←rs1 & imm', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '111'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

# I型指令 (移位立即数指令)
new_instruction('slli', 'Shift Left Logical Immediate', '(rd)←rs1 << shamt', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],
    [24, 20, 'shamt', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '001'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

new_instruction('srli', 'Shift Right Logical Immediate', '(rd)←rs1 >> shamt', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0000000'],
    [24, 20, 'shamt', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '101'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

new_instruction('srai', 'Shift Right Arithmetic Immediate', '(rd)←rs1 >>> shamt', 
               param_pattern(3), [
    [31, 25, 'funct7', noop, 'fixed', '0100000'],
    [24, 20, 'shamt', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '101'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010011'],
])

# I型指令 (跳转指令)
new_instruction('jalr', 'Jump and Link Register', '(rd)←PC+4; PC=(rs1+imm)&~1', 
               param_pattern(3), [
    [31, 20, 'imm', imm_to_bin, 'immed', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '1100111'],
])

# I型指令 (系统调用和断点指令)
new_instruction('ecall', 'Environment Call', 'Invoke System Call', 
               param_pattern(0), [
    [31, 20, 'imm', noop, 'fixed', '000000000000'],
    [19, 15, 'rs1', noop, 'fixed', '00000'],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'rd', noop, 'fixed', '00000'],
    [6, 0, 'opcode', noop, 'fixed', '1110011'],
])

new_instruction('ebreak', 'Environment Break', 'Breakpoint', 
               param_pattern(0), [
    [31, 20, 'imm', noop, 'fixed', '000000000001'],
    [19, 15, 'rs1', noop, 'fixed', '00000'],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'rd', noop, 'fixed', '00000'],
    [6, 0, 'opcode', noop, 'fixed', '1110011'],
])

# I型指令 (内存屏障指令)
new_instruction('fence', 'Memory Fence', 'Memory Barrier', 
               param_pattern(0), [
    [31, 20, 'imm', noop, 'fixed', '000000000000'],
    [19, 15, 'rs1', noop, 'fixed', '00000'],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'rd', noop, 'fixed', '00000'],
    [6, 0, 'opcode', noop, 'fixed', '0001111'],
])

# =================== U-type Instructions ===================

# U型指令 (长立即数指令)
# 格式: imm[31:12] | rd | opcode

new_instruction('lui', 'Load Upper Immediate', '(rd)←imm[31:12] << 12', 
               param_pattern(2), [
    [31, 12, 'imm[31:12]', imm_to_bin, 'immed', ''],  # 将在组装时处理
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0110111'],  # LUI opcode
])

new_instruction('auipc', 'Add Upper Immediate to PC', '(rd)←PC + (imm[31:12] << 12)', 
               param_pattern(2), [
    [31, 12, 'imm[31:12]', imm_to_bin, 'immed', ''],  # 将在组装时处理
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '0010111'],  # AUIPC opcode
])

# =================== J-type Instructions ===================

# J型指令 (无条件跳转指令)
# 格式: imm[20|10:1|11|19:12] | rd | opcode

new_instruction('jal', 'Jump and Link', '(rd)←PC+4; PC←PC+imm', 
               param_pattern(2), [
    [31, 31, 'imm[20]', imm_to_bin, 'immed', ''],  # 将在组装时处理
    [30, 21, 'imm[10:1]', noop, 'fixed', '0000000000'],  # 将在组装时处理
    [20, 20, 'imm[11]', noop, 'fixed', '0'],  # 将在组装时处理
    [19, 12, 'imm[19:12]', noop, 'fixed', '00000000'],  # 将在组装时处理
    [11, 7, 'rd', rd_to_bin, 'reg', ''],
    [6, 0, 'opcode', noop, 'fixed', '1101111'],  # JAL opcode
])

# =================== S-type Instructions ===================

# S型指令 (存储指令)
# 格式: imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode

new_instruction('sb', 'Store Byte', 'M[rs1+imm]←(rs2)[7:0]', 
               param_pattern(3), [
    [31, 25, 'imm[11:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'imm[4:0]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '0100011'],
])

new_instruction('sh', 'Store Halfword', 'M[rs1+imm]←(rs2)[15:0]', 
               param_pattern(3), [
    [31, 25, 'imm[11:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '001'],
    [11, 7, 'imm[4:0]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '0100011'],
])

new_instruction('sw', 'Store Word', 'M[rs1+imm]←(rs2)', 
               param_pattern(3), [
    [31, 25, 'imm[11:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '010'],
    [11, 7, 'imm[4:0]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '0100011'],
])

# =================== RV32I B-type Instructions ===================
# Format: imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode

# BEQ - rs1, rs2, imm
new_instruction('beq', 'Branch if Equal', 'if (rs1 == rs2) PC = PC + imm', 
               param_pattern(3), [
    [31, 25, 'imm[12|10:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '000'],
    [11, 7, 'imm[4:1|11]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '1100011'],
])

# BNE - rs1, rs2, imm
new_instruction('bne', 'Branch if Not Equal', 'if (rs1 != rs2) PC = PC + imm', 
               param_pattern(3), [
    [31, 25, 'imm[12|10:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '001'],
    [11, 7, 'imm[4:1|11]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '1100011'],
])

# BLT - rs1, rs2, imm
new_instruction('blt', 'Branch if Less Than', 'if (rs1 < rs2) PC = PC + imm', 
               param_pattern(3), [
    [31, 25, 'imm[12|10:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '100'],
    [11, 7, 'imm[4:1|11]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '1100011'],
])

# BGE - rs1, rs2, imm
new_instruction('bge', 'Branch if Greater Than or Equal', 'if (rs1 >= rs2) PC = PC + imm', 
               param_pattern(3), [
    [31, 25, 'imm[12|10:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '101'],
    [11, 7, 'imm[4:1|11]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '1100011'],
])

# BLTU - rs1, rs2, imm
new_instruction('bltu', 'Branch if Less Than Unsigned', 'if (rs1 < rs2) PC = PC + imm (unsigned)', 
               param_pattern(3), [
    [31, 25, 'imm[12|10:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '110'],
    [11, 7, 'imm[4:1|11]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '1100011'],
])

# BGEU - rs1, rs2, imm
new_instruction('bgeu', 'Branch if Greater Than or Equal Unsigned', 'if (rs1 >= rs2) PC = PC + imm (unsigned)', 
               param_pattern(3), [
    [31, 25, 'imm[12|10:5]', imm_to_bin, 'immed', ''],
    [24, 20, 'rs2', rs2_to_bin, 'reg', ''],
    [19, 15, 'rs1', rs1_to_bin, 'reg', ''],
    [14, 12, 'funct3', noop, 'fixed', '111'],
    [11, 7, 'imm[4:1|11]', noop, 'fixed', '00000'],  # 将在组装时处理
    [6, 0, 'opcode', noop, 'fixed', '1100011'],
])

# MIPS格式的乘法除法指令已被移除
# 以下是RV32I标准指令集支持的所有指令类型:
# - R-type: add, sub, sll, slt, sltu, xor, srl, sra, or, and
# - I-type: lb, lh, lw, lbu, lhu, addi, slti, sltiu, xori, ori, andi, slli, srli, srai, jalr, ecall, ebreak, fence
# - S-type: sb, sh, sw
# - B-type: beq, bne, blt, bge, bltu, bgeu
# - U-type: lui, auipc
# - J-type: jal

# MIPS格式的指令已被移除，只保留RV32I格式的指令
# 以下是RV32I格式的I-type指令（在文件前面已定义）:
# - addi, slti, sltiu, xori, ori, andi, slli, srli, srai
# - lb, lh, lw, lbu, lhu

# =================== RV32I B-type Instructions ===================
# Format: imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode

# =================== RV32I J-type Instructions ===================
# Format: imm[20|10:1|11|19:12] | rd | opcode

# =================== RV32I U-type Instructions ===================
# Format: imm[31:12] | rd | opcode

# =================== End of RV32I Instructions ===================