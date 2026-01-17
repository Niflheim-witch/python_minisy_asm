#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minisys Format Converter Implementation
"""

from typing import List, Tuple, Optional
from .assembler import AsmProgram
from .utils import SevereError


def data_seg_to_coe(asm_program: AsmProgram, output_path: str) -> None:
    """
    Convert data segment to COE format file
    
    Args:
        asm_program: Assembled program
        output_path: Path to output COE file
    """
    coe_lines = [
        'memory_initialization_radix=16;',
        'memory_initialization_vector='
    ]
    
    # Process all variables in order of their addresses
    sorted_vars = sorted(asm_program.data_seg.vars.items(), 
                        key=lambda x: asm_program.data_seg.addrs[x[0]])
    
    current_addr = 0x10000
    
    # Process each variable
    for var_name, components in sorted_vars:
        var_addr = asm_program.data_seg.addrs[var_name]
        
        # Add padding zeros if there's a gap between variables
        if var_addr > current_addr:
            padding_bytes = var_addr - current_addr
            padding_words = (padding_bytes + 3) // 4  # Round up to nearest word
            coe_lines.extend(['00' for _ in range(padding_words)])
            current_addr = var_addr + padding_bytes
        
        # Process each component of the variable
        for comp in components:
            if comp.type == 'byte':
                # Process byte values
                try:
                    # Handle different value formats
                    if isinstance(comp.value, str):
                        # Check for character literals
                        if comp.value.startswith('"') and comp.value.endswith('"'):
                            val = ord(comp.value[1:-1])
                        elif comp.value.startswith('\'') and comp.value.endswith('\''):
                            val = ord(comp.value[1:-1])
                        else:
                            # Numeric value (could be hex, decimal, etc.)
                            val = int(comp.value, 0)
                    else:
                        val = int(comp.value)
                    
                    # Ensure value is within byte range
                    if not (0 <= val <= 255):
                        raise SevereError(f"Byte value {val} out of range")
                    # Add as a single byte (padded to word with zeros)
                    coe_lines.append(f"000000{val:02X}".lower())
                    current_addr += 1
                    
                except ValueError as e:
                    raise SevereError(f"Invalid byte value '{comp.value}': {str(e)}")
                except Exception as e:
                    raise SevereError(f"Error processing byte component: {str(e)}")
            
            elif comp.type == 'half':
                # Process halfword values
                try:
                    # Handle different value formats
                    if isinstance(comp.value, str):
                        val = int(comp.value, 0)
                    else:
                        val = int(comp.value)
                    
                    # Ensure value is within halfword range
                    if not (0 <= val <= 65535):
                        raise SevereError(f"Halfword value {val} out of range")
                    # Add as a halfword (padded to word with zeros)
                    coe_lines.append(f"0000{val & 0xFFFF:04X}".lower())
                    current_addr += 2
                    
                except ValueError as e:
                    raise SevereError(f"Invalid halfword value '{comp.value}': {str(e)}")
                except Exception as e:
                    raise SevereError(f"Error processing half component: {str(e)}")
            
            elif comp.type == 'word':
                # Process word values
                try:
                    # Handle different value formats
                    if isinstance(comp.value, str):
                        val = int(comp.value, 0)
                    else:
                        val = int(comp.value)
                    
                    # Ensure value is within word range
                    if not (0 <= val <= 4294967295):
                        raise SevereError(f"Word value {val} out of range")
                    # Add as a word
                    coe_lines.append(f"{val & 0xFFFFFFFF:08X}".lower())
                    current_addr += 4
                    
                except ValueError as e:
                    raise SevereError(f"Invalid word value '{comp.value}': {str(e)}")
                except Exception as e:
                    raise SevereError(f"Error processing word component: {str(e)}")
            
            elif comp.type == 'asciiz':
                # Process string with null terminator
                try:
                    string_val = comp.value
                    
                    # Process each character in the string
                    for char in string_val:
                        # Get ASCII value
                        char_val = ord(char)
                        if char_val > 127:
                            raise SevereError(f"Character '{char}' has invalid ASCII value {char_val}")
                        
                        # Add as a single byte (padded to word with zeros)
                        coe_lines.append(f"000000{char_val:02X}".lower())
                        current_addr += 1
                    
                    # Add null terminator
                    coe_lines.append("00000000")
                    current_addr += 1
                    
                except Exception as e:
                    raise SevereError(f"Error processing asciiz component: {str(e)}")
            
            elif comp.type == 'space':
                # Process space directive
                try:
                    size = int(comp.value)
                    if size < 0:
                        raise SevereError("Space size cannot be negative")
                    
                    # Add zeros for the specified number of bytes
                    for i in range(size):
                        coe_lines.append("00000000")
                    current_addr += size
                    
                except ValueError as e:
                    raise SevereError(f"Invalid space size '{comp.value}': {str(e)}")
                except Exception as e:
                    raise SevereError(f"Error processing space component: {str(e)}")
            
            else:
                raise SevereError(f"Unknown data type: {comp.type}")
    
    # Ensure we don't exceed memory limits
    if current_addr > 0x00100000:  # 1MB data segment limit
        raise SevereError("Data segment exceeds memory limit")
    
    # Add trailing semicolon to the last line
    if len(coe_lines) > 2:
        coe_lines[-1] += ';'
    else:
        # If no data, add a dummy zero with semicolon
        coe_lines.append('00000000;')
    
    # Join all lines with newlines (no commas between lines for COE vector format usually, 
    # but Xilinx COE expects space or comma or newline separated values)
    # Standard format:
    # memory_initialization_radix=16;
    # memory_initialization_vector=
    # val1, val2, val3, ... valN;
    
    # Let's format it properly with commas
    header = coe_lines[:2]
    data_values = coe_lines[2:]
    
    # Remove the semicolon we just added to handle it in the join
    if data_values:
        if data_values[-1].endswith(';'):
            data_values[-1] = data_values[-1][:-1]
            
        # Join data values with comma and newline
        data_str = ',\n'.join(data_values) + ';'
        
        # Combine header and data
        coe_content = '\n'.join(header) + '\n' + data_str
    else:
        # Empty data segment
        coe_content = '\n'.join(header) + '\n00000000;'
    
    # Write to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(coe_content)
    except Exception as e:
        raise SevereError(f"Failed to write data COE file: {str(e)}")


def text_seg_to_coe(asm_program: AsmProgram, output_path: str, 
                   start_address: int = 0x00000800) -> None:
    """
    Convert text segment to COE format file
    
    Args:
        asm_program: Assembled program
        output_path: Path to output COE file
        start_address: Starting address for the text segment
    """
    coe_lines = [
        'memory_initialization_radix=16;',
        'memory_initialization_vector='
    ]
    
    # Calculate start index (convert address to word index)
    start_index = start_address // 4
    
    # Add padding for BIOS area (0x00000000 to start_address - 1)
    # In a real system, the BIOS would be included here
    # For simplicity, we'll just add zeros
    padding_count = start_index
    coe_lines.extend(['00000000' for _ in range(padding_count)])
    
    # Process each instruction
    for instruction in asm_program.text_seg.instructions:
        try:
            # Convert instruction to hex format
            instr_hex = instruction.to_hex(zero_x=False).lower()
            # Ensure it's 8 hex digits
            instr_hex = instr_hex.zfill(8)
            coe_lines.append(instr_hex)
        except Exception as e:
            raise SevereError(f"Error converting instruction to hex: {str(e)}")
            
    # Add trailing semicolon to the last line
    if len(coe_lines) > 2:
        # Format with commas
        header = coe_lines[:2]
        data_values = coe_lines[2:]
        data_str = ',\n'.join(data_values) + ';'
        coe_content = '\n'.join(header) + '\n' + data_str
    else:
        coe_content = '\n'.join(coe_lines) + '\n00000000;'
        
    # Write to file
    
    # Ensure we don't exceed memory limits
    total_size = (padding_count + len(asm_program.text_seg.instructions)) * 4
    # Write to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(coe_content)
    except Exception as e:
        raise SevereError(f"Failed to write text COE file: {str(e)}")


def coe_to_txt(text_coe_path: str, data_coe_path: Optional[str], 
               output_path: str) -> None:
    """
    Convert COE files to UART serial text format
    
    Args:
        text_coe_path: Path to text segment COE file
        data_coe_path: Path to data segment COE file (optional)
        output_path: Path to output TXT file
    """
    # Read text COE file
    try:
        with open(text_coe_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        raise SevereError(f"Failed to read text COE file: {str(e)}")
    
    # Extract text data
    text_data_lines = text_content.split(';')
    if len(text_data_lines) < 2:
        raise SevereError("Invalid text COE file format")
    
    # Get the vector data
    text_vector_line = text_data_lines[1].strip()
    if not text_vector_line.startswith('memory_initialization_vector='):
        raise SevereError("Invalid text COE file format")
    
    # Split the vector into hex values
    text_values = text_vector_line[len('memory_initialization_vector='):].split(',')
    text_values = [val.strip() for val in text_values if val.strip()]
    
    # Read data COE file if provided
    data_values = []
    if data_coe_path:
        try:
            with open(data_coe_path, 'r', encoding='utf-8') as f:
                data_content = f.read()
        except Exception as e:
            raise SevereError(f"Failed to read data COE file: {str(e)}")
        
        # Extract data
        data_data_lines = data_content.split(';')
        if len(data_data_lines) < 2:
            raise SevereError("Invalid data COE file format")
        
        # Get the vector data
        data_vector_line = data_data_lines[1].strip()
        if not data_vector_line.startswith('memory_initialization_vector='):
            raise SevereError("Invalid data COE file format")
        
        # Split the vector into hex values
        data_values = data_vector_line[len('memory_initialization_vector='):].split(',')
        data_values = [val.strip() for val in data_values if val.strip()]
    
    # Create serial output
    serial_lines = []
    
    # Add handshake signal for program
    serial_lines.append('03020000')  # Program handshake
    
    # Add program data
    for val in text_values:
        # Ensure each value is 8 hex digits
        val = val.zfill(8)
        serial_lines.append(val)
    
    # Add handshake signal for data (if data exists)
    if data_values:
        serial_lines.append('03030000')  # Data handshake
        
        # Add data values
        for val in data_values:
            # Ensure each value is 8 hex digits
            val = val.zfill(8)
            serial_lines.append(val)
    
    # Join all lines
    serial_content = '\n'.join(serial_lines)
    
    # Write to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(serial_content)
    except Exception as e:
        raise SevereError(f"Failed to write serial TXT file: {str(e)}")


def coe_to_hex(text_coe_path: str, data_coe_path: Optional[str], output_path: str, start_address: str = '@00000000', skip_words: int = 0) -> None:
    """
    Convert COE files to a simple HEX file (raw hex values, one per line)
    
    Args:
        text_coe_path: Path to input text COE file
        data_coe_path: Path to input data COE file (optional)
        output_path: Path to output HEX file
        start_address: The start address string (e.g. '@00000000')
        skip_words: Number of words to skip from the beginning of the text segment
    """
    try:
        with open(text_coe_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        raise SevereError(f"Failed to read text COE file: {str(e)}")
    
    # Extract text data
    text_data_lines = text_content.split(';')
    if len(text_data_lines) < 2:
        raise SevereError("Invalid text COE file format")
    
    # Get the vector data
    text_vector_line = text_data_lines[1].strip()
    if not text_vector_line.startswith('memory_initialization_vector='):
        raise SevereError("Invalid text COE file format")
    
    # Split the vector into hex values
    # Handle both comma-separated and newline/space-separated formats
    raw_values = text_vector_line[len('memory_initialization_vector='):]
    text_values = raw_values.replace(',', ' ').split()
    
    # Skip words if requested
    if skip_words > 0:
        if skip_words < len(text_values):
            text_values = text_values[skip_words:]
        else:
            text_values = []

    # Remove trailing zeros
    while text_values and int(text_values[-1], 16) == 0:
        text_values.pop()
    
    # Read data COE file if provided
    data_values = []
    if data_coe_path:
        try:
            with open(data_coe_path, 'r', encoding='utf-8') as f:
                data_content = f.read()
        except Exception as e:
            raise SevereError(f"Failed to read data COE file: {str(e)}")
        
        # Extract data
        data_data_lines = data_content.split(';')
        if len(data_data_lines) < 2:
            raise SevereError("Invalid data COE file format")
        
        # Get the vector data
        data_vector_line = data_data_lines[1].strip()
        if not data_vector_line.startswith('memory_initialization_vector='):
            raise SevereError("Invalid data COE file format")
        
        # Split the vector into hex values
        data_values = data_vector_line[len('memory_initialization_vector='):].split(',')
        data_values = [val.strip() for val in data_values if val.strip()]
    
    # Create hex output
    hex_lines = []
    
    # Add start address for Verilog $readmemh compatibility
    hex_lines.append(start_address)
    
    # Add program data
    for val in text_values:
        # Ensure each value is 8 hex digits
        val = val.zfill(8)
        hex_lines.append(val)
        
    # Add data values
    for val in data_values:
        # Ensure each value is 8 hex digits
        val = val.zfill(8)
        hex_lines.append(val)
    
    # Join all lines
    hex_content = '\n'.join(hex_lines)
    
    # Write to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(hex_content)
    except Exception as e:
        raise SevereError(f"Failed to write HEX file: {str(e)}")


def convert_linked_to_coe(linked_memory: List[str], data_map: List[int], 
                         text_coe_path: str, data_coe_path: str, show_zeros: bool = True) -> None:
    """
    Convert linked memory to COE files
    
    Args:
        linked_memory: List of hex strings representing the full memory image
        data_map: List of data values for the data memory
        text_coe_path: Path to output text COE file
        data_coe_path: Path to output data COE file
        show_zeros: Whether to print zero values to console
    """
    # Write text COE file
    try:
        with open(text_coe_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write('memory_initialization_radix=16;\n')
            f.write('memory_initialization_vector=\n')
            
            # Write each line
            for i, line in enumerate(linked_memory):
                # For the last line, don't add a comma
                if i == len(linked_memory) - 1:
                    f.write(line)
                else:
                    f.write(f"{line}\n")
    except Exception as e:
        raise SevereError(f"Failed to write linked text COE file: {str(e)}")
    
    # Write data COE file
    try:
        with open(data_coe_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write('memory_initialization_radix=16;\n')
            f.write('memory_initialization_vector=\n')
            
            # Convert data map to hex strings (4 bytes per entry)
            # Process data in chunks of 4 bytes
            data_lines = []
            for i in range(0, len(data_map), 4):
                word = 0
                # Process up to 4 bytes, padding with zeros if needed
                for j in range(4):
                    if i + j < len(data_map):
                        word |= (data_map[i + j] & 0xFF) << ((3 - j) * 8)
                # Format as 8 hex digits
                hex_value = f"{word:08X}".lower()
                data_lines.append(hex_value)
            
            # Write each data line
            for i, line in enumerate(data_lines):
                # For the last line, don't add a comma
                if i == len(data_lines) - 1:
                    f.write(line)
                else:
                    f.write(f"{line}\n")
    except Exception as e:
        raise SevereError(f"Failed to write linked data COE file: {str(e)}")