import sys
import os
import unittest

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py_minisys_asm.assembler import Assembler
from py_minisys_asm.linker import link_all, USER_SIZE

class TestMinisysAssembler(unittest.TestCase):
    def setUp(self):
        self.assembler = Assembler()

    def test_m_extension(self):
        """Test RISC-V M Extension instructions"""
        print("\nTesting M Extension Instructions...")
        
        # Test case: mul x1, x2, x3
        # funct7=0000001, rs2=00011(x3), rs1=00010(x2), funct3=000, rd=00001(x1), opcode=0110011
        # Binary: 0000001 00011 00010 000 00001 0110011
        # Hex: 023100B3
        
        # Test case: div x4, x5, x6
        # funct7=0000001, rs2=00110(x6), rs1=00101(x5), funct3=100, rd=00100(x4), opcode=0110011
        # Binary: 0000001 00110 00101 100 00100 0110011
        # Hex: 0262C233

        code = """
        .text
        mul x1, x2, x3
        mulh x2, x3, x4
        mulhsu x3, x4, x5
        mulhu x4, x5, x6
        div x5, x6, x7
        divu x6, x7, x8
        rem x7, x8, x9
        remu x8, x9, x10
        """
        
        program = self.assembler.assemble(code)
        instructions = program.text_seg.instructions
        
        # Verify instruction count
        self.assertEqual(len(instructions), 8)
        
        # Verify machine code for first few instructions
        self.assertEqual(instructions[0].to_hex(zero_x=False).upper(), "023100B3") # mul
        self.assertEqual(instructions[4].to_hex(zero_x=False).upper(), "027342B3") # div x5, x6, x7
        
        print("✓ M Extension instructions assembled correctly")

    def test_rv32i_instructions(self):
        """Test basic RV32I instructions"""
        print("\nTesting RV32I Instructions...")
        
        code = """
        .text
        add x1, x2, x3
        sub x4, x5, x6
        lui x7, 1       # x7 = 0x1000 (User Data Area)
        lw x8, 0(x7)
        sw x9, 4(x7)
        beq x1, x2, label
        label:
        jal x0, label
        """
        
        program = self.assembler.assemble(code)
        instructions = program.text_seg.instructions
        
        self.assertEqual(len(instructions), 7)
        print("✓ RV32I instructions assembled correctly")

    def test_memory_protection(self):
        """Test Memory Layout and Protection"""
        print("\nTesting Memory Protection...")
        
        # 1. Test valid program size
        # USER_SIZE is now 0xE800 (59392 bytes)
        # Let's create a program that fits
        valid_code = ".text\n" + "nop\n" * 100
        program = self.assembler.assemble(valid_code)
        try:
            link_all(program)
            print("✓ Valid program size accepted")
        except Exception as e:
            self.fail(f"Valid program rejected: {e}")

        # 2. Test program exceeding memory limit
        # Create a program larger than USER_SIZE
        # Each instruction is 4 bytes
        # We need > 59392 / 4 = 14848 instructions
        
        # We can simulate a large program by manually manipulating the instruction list
        # to avoid parsing a huge string which is slow
        large_program = self.assembler.assemble("nop")
        # Multiply instructions to exceed limit
        large_program.text_seg.instructions = large_program.text_seg.instructions * 15000
        
        print(f"Attempting to link program with {len(large_program.text_seg.instructions) * 4} bytes (Limit: {USER_SIZE})")
        
        with self.assertRaises(ValueError) as cm:
            link_all(large_program)
        
        print(f"✓ Oversized program rejected as expected: {cm.exception}")
        
        # Verify the error message relates to size
        self.assertIn("User program too large", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
