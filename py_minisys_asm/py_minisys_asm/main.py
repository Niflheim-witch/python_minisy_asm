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
    data_seg_to_coe, text_seg_to_coe, coe_to_txt, convert_linked_to_coe
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
    parser.add_argument('-l', '--link', action='store_true',
                       help='Link with BIOS and interrupt handlers')
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
        os.makedirs(output_dir, exist_ok=True)
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
    # Read input file
    content = read_input_file(args.in_file)
    
    # Create output directory
    ensure_output_directory(args.out_dir)
    
    # Define output file paths
    base_name = os.path.splitext(os.path.basename(args.in_file))[0]
    text_coe_path = os.path.join(args.out_dir, f'{base_name}_text.coe')
    data_coe_path = os.path.join(args.out_dir, f'{base_name}_data.coe')
    serial_txt_path = os.path.join(args.out_dir, f'{base_name}_serial.txt')
    
    # Assemble the program
    program = assemble_file(content, args.debug)
    
    if args.link:
        # Link with BIOS and interrupt handlers
        if args.debug:
            print("Linking with BIOS and interrupt handlers...")
        
        try:
            # Link the program with real BIOS and interrupt handlers
            linked_memory, data_map = link_all(program, use_real_bios=True)
            
            # Convert linked program to COE files
            convert_linked_to_coe(
                linked_memory, data_map,
                text_coe_path, data_coe_path
            )
            
            if args.debug:
                print(f"Linked successfully!")
                print(f"Total memory entries: {len(linked_memory)}")
                print(f"Data map entries: {len(data_map)}")
                
        except Exception as e:
            raise SevereError(f"Linking error: {str(e)}")
    else:
        # Generate separate COE files
        if args.debug:
            print("Generating COE files...")
        
        # Generate text segment COE
        text_seg_to_coe(program, text_coe_path)
        
        # Generate data segment COE if there is data
        if program.data_seg.vars:
            data_seg_to_coe(program, data_coe_path)
        else:
            # Create empty data COE file
            data_coe_path = None
            with open(data_coe_path, 'w', encoding='utf-8') as f:
                f.write('memory_initialization_radix=16;\n')
                f.write('memory_initialization_vector=\n')
        
        if args.debug:
            print("COE files generated successfully!")
    
    # Generate serial TXT file
    if args.debug:
        print("Generating serial TXT file...")
    
    coe_to_txt(text_coe_path, data_coe_path, serial_txt_path)
    
    if args.debug:
        print(f"Serial TXT file generated: {serial_txt_path}")
    
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
        print(f"Assembly completed successfully!")
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