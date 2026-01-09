#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minisys Assembler Main Entry Point
"""

import os
import sys
import argparse
from typing import Optional, Tuple
from .assembler import Assembler, AsmProgram
from .linker import link_all
from .convert import (
    data_seg_to_coe, text_seg_to_coe, coe_to_txt, coe_to_hex, convert_linked_to_coe
)
from .utils import SevereError


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Minisys Assembler - Convert assembly code to machine code'
    )
    
    # Required arguments
    parser.add_argument('in_file', help='Input assembly file path')
    parser.add_argument('out_dir', help='Output directory path')
    
    # Optional arguments
    parser.add_argument('-s', '--bios-only', action='store_true',
                       help='Assemble BIOS only and write to output, ignore user program')
    parser.add_argument('--hex', action='store_true',
                       help='Generate HEX file output')
    parser.add_argument('-d', '--debug', action='store_true',
                       help='Enable debug output')
    
    return parser.parse_args()


def read_input_file(file_path: str) -> str:
    """
    Read input assembly file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise SevereError(f"Input file not found: {file_path}")
    except Exception as e:
        raise SevereError(f"Error reading input file: {str(e)}")


def ensure_output_directory(dir_path: str) -> None:
    """
    Ensure output directory exists
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        raise SevereError(f"Error creating output directory: {str(e)}")


def assemble_file(content: str, debug: bool = False) -> AsmProgram:
    """
    Assemble the input content
    """
    try:
        assembler = Assembler()
        program = assembler.assemble(content)
        
        if debug:
            print(f"Assembly successful!")
            print(f"Data segment size: {program.data_seg.total_size} bytes")
            print(f"Text segment size: {program.text_seg.total_size} bytes")
            print(f"Variables: {len(program.data_seg.vars)}")
            print(f"Labels: {len(program.text_seg.labels)}")
            print(f"Instructions: {len(program.text_seg.instructions)}")
        
        return program
    except SevereError:
        raise
    except Exception as e:
        raise SevereError(f"Assembly error: {str(e)}")


def handle_assembly(args: argparse.Namespace) -> Tuple[str, str, str]:
    """
    Handle the full assembly process
    
    Returns:
        Tuple of (text_coe_path, data_coe_path, serial_txt_path)
    """
    # Create output directory
    ensure_output_directory(args.out_dir)
    
    # Define output file paths
    if args.bios_only:
        # For BIOS-only mode, use fixed output filenames
        text_coe_path = os.path.join(args.out_dir, 'bios_text.coe')
        data_coe_path = os.path.join(args.out_dir, 'bios_data.coe')
        serial_txt_path = os.path.join(args.out_dir, 'bios_serial.txt')
        
        # Handle BIOS-only assembly
        return handle_bios_only_assembly(text_coe_path, data_coe_path, serial_txt_path, args.debug)
    else:
        # Normal mode - default to linking
        # Read input file
        content = read_input_file(args.in_file)
        
        # Define output file paths based on input file
        base_name = os.path.splitext(os.path.basename(args.in_file))[0]
        text_coe_path = os.path.join(args.out_dir, f'{base_name}_text.coe')
        data_coe_path = os.path.join(args.out_dir, f'{base_name}_data.coe')
        serial_txt_path = os.path.join(args.out_dir, f'{base_name}_serial.txt')
        
        # Assemble the program
        program = assemble_file(content, args.debug)
        
        # Default to linking with BIOS and interrupt handlers
        if args.debug:
            print("Linking with BIOS and interrupt handlers...")
        
        try:
            # Link the program with real BIOS and interrupt handlers
            linked_memory, data_map = link_all(program, use_real_bios=True)
            
            # Convert linked program to COE files
            convert_linked_to_coe(
                linked_memory, data_map,
                text_coe_path, data_coe_path,
                show_zeros=False  # 只输出非零机器码
            )
            
            if args.debug:
                print(f"Linked successfully!")
                print(f"Total memory entries: {len(linked_memory)}")
                print(f"Data map entries: {len(data_map)}")
                
        except Exception as e:
            raise SevereError(f"Linking error: {str(e)}")
    
    # Generate serial TXT file
    if args.debug:
        print("Generating serial TXT file...")
    
    coe_to_txt(text_coe_path, data_coe_path, serial_txt_path)
    
    if args.debug:
        print(f"Serial TXT file generated: {serial_txt_path}")
    
    # Generate HEX file if requested
    if args.hex:
        base_name = os.path.splitext(os.path.basename(args.in_file))[0]
        hex_path = os.path.join(args.out_dir, f'{base_name}.hex')
        
        if args.debug:
            print("Generating HEX file...")
            
        # For normal user programs, we skip the BIOS (first 512 words / 2KB)
        # and start at address 0x800
        # coe_to_hex(text_coe_path, data_coe_path, hex_path, start_address='@00000800', skip_words=512)
        
        # Output FULL memory (starting from 0x00000800) to include BIOS
        # Hardware executes from 0x800 (word address), which is 0x2000 (byte address)
        coe_to_hex(text_coe_path, data_coe_path, hex_path, start_address='@00000800', skip_words=0)
        
        if args.debug:
            print(f"HEX file generated: {hex_path}")

    return text_coe_path, data_coe_path, serial_txt_path


def handle_bios_only_assembly(text_coe_path: str, data_coe_path: str, serial_txt_path: str, debug: bool) -> Tuple[str, str, str]:
    """
    Handle BIOS-only assembly process
    
    Returns:
        Tuple of (text_coe_path, data_coe_path, serial_txt_path)
    """
    if debug:
        print("Assembling BIOS only...")
    
    try:
        # Import _load_bios function from linker module
        from .linker import _load_bios, _get_snippet_path
        
        # Get snippet path to locate BIOS file
        snippet_path = _get_snippet_path()
        bios_file = os.path.join(snippet_path, 'minisys-bios.asm')
        
        if debug:
            print(f"Loading BIOS from: {bios_file}")
        
        # Load and assemble BIOS
        bios_instructions = _load_bios()
        
        if debug:
            print(f"BIOS assembly successful, {len(bios_instructions)} instructions")
        
        # Create memory with only BIOS
        memory_size = 64 * 1024  # 64KB
        linked_memory = ['00000000'] * memory_size
        
        # Fill memory with BIOS instructions
        for i, instr in enumerate(bios_instructions):
            if i < memory_size:
                linked_memory[i] = instr
        
        # Create empty data map
        data_map = {}
        
        # Convert to COE files
        convert_linked_to_coe(
            linked_memory, data_map,
            text_coe_path, data_coe_path,
            show_zeros=False
        )
        
        if debug:
            print(f"BIOS COE files generated successfully!")
        
    except Exception as e:
        raise SevereError(f"BIOS-only assembly error: {str(e)}")
    
    return text_coe_path, data_coe_path, serial_txt_path

def main() -> int:
    """
    Main function
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Handle assembly
        text_coe, data_coe, serial_txt = handle_assembly(args)
        
        # Print success message
        operation = "BIOS-only assembly" if args.bios_only else "Assembly with linking"
        print(f"{operation} completed successfully!")
        print(f"Output files:")
        print(f"  - Text COE: {text_coe}")
        print(f"  - Data COE: {data_coe}")
        print(f"  - Serial TXT: {serial_txt}")
        
        return 0
        
    except SevereError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAssembly interrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())