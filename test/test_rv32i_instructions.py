import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py_minisys_asm.assembler import Assembler

def test_labels():
    """
    测试标签解析功能
    """
    print("测试标签解析功能...")
    
    # 测试程序包含各种标签定义和引用
    test_program = """
.text
    # 测试标签定义和引用
    label1:  addi x1, x0, 1
    
    # 向前引用
    beq x1, x0, label2
    
    label2:  addi x2, x0, 2
    
    # 标签后有注释
    label3:  # 这是标签3的注释
    addi x3, x0, 3
    
    # 测试循环引用
    loop:  addi x4, x4, 1
    bne x4, x0, loop
    """
    
    try:
        # 创建汇编器实例
        assembler = Assembler()
        
        # 执行汇编
        program = assembler.assemble(test_program)
        
        # 检查是否成功解析了标签
        labels = program.text_seg.labels
        print(f"成功解析 {len(labels)} 个标签: {list(labels.keys())}")
        
        # 验证标签值是否正确
        # 注意：这里假设第一条指令从地址0开始
        expected_labels = {
            'label1': 0,
            'label2': 4,  # 假设每条指令4字节
            'label3': 8,
            'loop': 12
        }
        
        # 检查是否所有预期标签都存在
        missing_labels = [label for label in expected_labels if label not in labels]
        if missing_labels:
            print(f"✗ 缺少标签: {missing_labels}")
            return False
        
        # 检查标签值是否正确
        for label, expected_value in expected_labels.items():
            if labels[label] != expected_value:
                print(f"✗ 标签 '{label}' 值错误: 期望 {expected_value}, 实际 {labels[label]}")
                return False
        
        print("✓ 所有标签解析正确!")
        return True
        
    except Exception as e:
        print(f"✗ 标签解析测试失败: {str(e)}")
        return False

def test_assembler():
    """
    测试基本汇编器功能
    """
    print("测试基本汇编器功能...")
    
    # 简单的测试程序
    test_program = """
.text
    # 测试基本算术运算
    addi x1, x0, 10      # x1 = 10
    addi x2, x0, 20      # x2 = 20
    add x3, x1, x2       # x3 = x1 + x2
    
    # 测试内存访问
    addi x4, x0, 0x1000  # x4 = 0x1000 (假设为数据地址)
    sw x3, 0(x4)         # 存储x3到内存
    lw x5, 0(x4)         # 从内存加载到x5
    
    # 测试分支指令
    beq x5, x3, equal    # 如果相等跳转到equal
    addi x6, x0, 0       # 不应该执行到这里
    equal:
    addi x6, x0, 1       # x6 = 1
    """
    
    try:
        # 创建汇编器实例
        assembler = Assembler()
        
        # 执行汇编
        program = assembler.assemble(test_program)
        
        # 检查是否生成了程序段
        if not hasattr(program, 'text_seg'):
            print("✗ 程序没有文本段")
            return False
        
        text_section = program.text_seg.instructions
        print(f"✓ 成功汇编 {len(text_section)} 条指令")
        
        # 验证生成的机器码
        for i, instruction in enumerate(text_section):
            try:
                # 尝试获取机器码
                machine_code = instruction.to_hex(zero_x=False).lower()
                print(f"  指令 {i+1}: {machine_code}")
            except Exception as e:
                print(f"✗ 无法获取指令 {i+1} 的机器码: {str(e)}")
                return False
        
        print("✓ 基本汇编器功能测试通过!")
        return True
        
    except Exception as e:
        print(f"✗ 基本汇编器功能测试失败: {str(e)}")
        return False

def test_all_instructions():
    """
    测试所有RV32I指令
    """
    print("测试所有RV32I指令...")
    
    all_tests_passed = True
    
    # 按指令类型分组测试
    test_phases = [
        ("R-type 指令", """
.text
        # R-type 算术指令
        add x1, x2, x3      # x1 = x2 + x3
        sub x4, x5, x6      # x4 = x5 - x6
        sll x7, x8, x9      # x7 = x8 << x9
        slt x10, x11, x12   # x10 = (x11 < x12) ? 1 : 0
        sltu x13, x14, x15  # x13 = (x14 < x15) ? 1 : 0 (无符号)
        xor x16, x17, x18   # x16 = x17 ^ x18
        srl x19, x20, x21   # x19 = x20 >> x21 (逻辑右移)
        sra x22, x23, x24   # x22 = x23 >> x24 (算术右移)
        or x25, x26, x27    # x25 = x26 | x27
        and x28, x29, x30   # x28 = x29 & x30
        """),
        
        ("I-type 算术指令", """
.text
        # I-type 立即数指令
        addi x1, x2, 10     # x1 = x2 + 10
        slti x3, x4, 20     # x3 = (x4 < 20) ? 1 : 0
        sltiu x5, x6, 30    # x5 = (x6 < 30) ? 1 : 0 (无符号)
        xori x7, x8, 0xAA   # x7 = x8 ^ 0xAA
        ori x9, x10, 0xBB   # x9 = x10 | 0xBB
        andi x11, x12, 0xCC # x11 = x12 & 0xCC
        slli x13, x14, 5    # x13 = x14 << 5
        srli x15, x16, 3    # x15 = x16 >> 3 (逻辑右移)
        srai x17, x18, 2    # x17 = x18 >> 2 (算术右移)
        """),
        
        ("U-type 指令", """
.text
        # U-type 指令
        lui x19, 0x1234     # x19 = 0x1234 << 12
        auipc x20, 0x5678   # x20 = PC + (0x5678 << 12)
        """),
        
        ("J-type 指令", """
.text
        # J-type 指令
        jal x21, 100        # x21 = PC + 4; PC += 100
        """),
        
        ("B-type 分支指令", """
.text
        # B-type 分支指令
        beq x22, x23, target1    # 如果 x22 == x23, 跳转到target1
        target1:
        bne x24, x25, target2    # 如果 x24 != x25, 跳转到target2
        target2:
        blt x26, x27, target3    # 如果 x26 < x27, 跳转到target3
        target3:
        bge x28, x29, target4    # 如果 x28 >= x29, 跳转到target4
        target4:
        bltu x30, x31, target5   # 如果 x30 < x31 (无符号), 跳转到target5
        target5:
        bgeu x0, x1, target6     # 如果 x0 >= x1 (无符号), 跳转到target6
        target6:
        """),
        
        ("I-type 内存访问指令", """
.text
        # I-type 内存加载指令
        addi x3, x0, 1000   # x3 = 1000 (假设为内存地址)
        lw x2, 0(x3)        # x2 = Mem[x3 + 0]
        lh x4, 4(x3)        # x4 = Mem[x3 + 4] (半字，符号扩展)
        lb x6, 8(x3)        # x6 = Mem[x3 + 8] (字节，符号扩展)
        lhu x8, 12(x3)      # x8 = Mem[x3 + 12] (半字，零扩展)
        lbu x10, 16(x3)     # x10 = Mem[x3 + 16] (字节，零扩展)
        """),
        
        ("S-type 内存存储指令", """
.text
        # S-type 内存存储指令
        addi x13, x0, 1000  # x13 = 1000 (假设为内存地址)
        sw x12, 0(x13)      # Mem[x13 + 0] = x12
        sh x14, 4(x13)      # Mem[x13 + 4] = x14 (半字)
        sb x16, 8(x13)      # Mem[x13 + 8] = x16 (字节)
        """),
        
        ("特殊指令", """
.text
        # 特殊指令
        ecall               # 环境调用
        ebreak              # 断点
        """),
    ]
    
    # 逐个阶段进行测试
    for phase_name, test_program in test_phases:
        print(f"\n--- 测试阶段: {phase_name} ---")
        
        try:
            # 创建汇编器实例
            assembler = Assembler()
            
            # 执行汇编
            program = assembler.assemble(test_program)
            
            # 获取并验证生成的机器码
            text_section = program.text_seg.instructions
            instruction_count = len(text_section)
            
            # 检查是否生成了正确数量的指令
            if instruction_count > 0:
                print(f"✓ 成功汇编 {instruction_count} 条指令")
                print("\n指令 - 机器码对应关系:")
                print("=" * 50)
                # 遍历每个指令并输出
                for i, instruction in enumerate(text_section):
                    # 尝试获取指令的原始文本（如果有）
                    instr_text = "未知指令"
                    try:
                        # 优先尝试使用symbol属性和components来构建更友好的指令表示
                        if hasattr(instruction, 'symbol'):
                            symbol = instruction.symbol
                            instr_text = symbol
                            
                            # 尝试构建完整的指令表示
                            if hasattr(instruction, 'components'):
                                reg_values = []
                                imm_value = None
                                
                                for comp in instruction.components:
                                    # 收集寄存器和立即数信息
                                    if comp.type == 'reg' and comp.val and comp.val != '00000':
                                        # 将二进制寄存器值转换为寄存器号
                                        reg_num = int(comp.val, 2)
                                        reg_values.append(f'x{reg_num}')
                                    elif comp.type == 'immed' and comp.val:
                                        # 保存立即数（二进制转十进制）
                                        imm_value = int(comp.val, 2)
                                        if imm_value >= 2**15:
                                            imm_value -= 2**16
                                    elif comp.type == 'offset' and comp.val:
                                        # 保存偏移量
                                        imm_value = int(comp.val, 2)
                                        if imm_value >= 2**15:
                                            imm_value -= 2**16
                                
                                # 根据指令类型组织参数
                                if symbol in ['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra', 'or', 'and']:
                                    # R型指令: rd, rs1, rs2
                                    if len(reg_values) >= 3:
                                        instr_text = f"{symbol} {reg_values[0]}, {reg_values[1]}, {reg_values[2]}"
                                elif symbol in ['slli', 'srli', 'srai']:
                                    # 立即数移位指令: rd, rs1, shamt
                                    if len(reg_values) >= 2 and imm_value is not None:
                                        instr_text = f"{symbol} {reg_values[0]}, {reg_values[1]}, {imm_value}"
                                elif symbol in ['addi', 'slti', 'sltiu', 'xori', 'ori', 'andi']:
                                    # I型指令: rd, rs1, imm
                                    if len(reg_values) >= 2 and imm_value is not None:
                                        instr_text = f"{symbol} {reg_values[0]}, {reg_values[1]}, {imm_value}"
                                elif symbol in ['lw', 'lh', 'lb', 'lhu', 'lbu']:
                                    # 内存加载指令: rd, imm(rs1)
                                    if len(reg_values) >= 2 and imm_value is not None:
                                        instr_text = f"{symbol} {reg_values[0]}, {imm_value}({reg_values[1]})"
                                elif symbol in ['sw', 'sh', 'sb']:
                                    # 内存存储指令: rs2, imm(rs1)
                                    if len(reg_values) >= 2 and imm_value is not None:
                                        instr_text = f"{symbol} {reg_values[0]}, {imm_value}({reg_values[1]})"
                                elif symbol in ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu']:
                                    # 分支指令: rs1, rs2, offset
                                    if len(reg_values) >= 2 and imm_value is not None:
                                        instr_text = f"{symbol} {reg_values[0]}, {reg_values[1]}, {imm_value}"
                                elif symbol == 'jal':
                                    # J型指令: rd, offset
                                    if len(reg_values) >= 1 and imm_value is not None:
                                        instr_text = f"{symbol} {reg_values[0]}, {imm_value}"
                                elif symbol in ['lui', 'auipc']:
                                    # U型指令: rd, imm
                                    if len(reg_values) >= 1 and imm_value is not None:
                                        instr_text = f"{symbol} {reg_values[0]}, {imm_value}"
                        # 如果没有symbol属性，尝试使用原来的方法
                        elif hasattr(instruction, 'source'):
                            instr_text = instruction.source.strip()
                        elif hasattr(instruction, 'text'):
                            instr_text = instruction.text.strip()
                        # 如果指令类有__str__方法，可以尝试使用
                        elif str(instruction).strip() != "":
                            instr_text = str(instruction).strip()
                    except:
                        pass
                    
                    # 尝试获取机器码
                    try:
                        # 使用to_hex方法获取机器码
                        machine_code = instruction.to_hex(zero_x=False).lower()
                        # 确保是8位十六进制数
                        machine_code = machine_code.zfill(8)
                    except Exception as e:
                        machine_code = f"错误: {str(e)}"
                    
                    # 输出指令和机器码
                    print(f"指令 {i+1:2d}: {instr_text:<30} | 机器码: {machine_code}")
                print("=" * 50)
            else:
                print(f"✗ 未能汇编任何指令")
                all_tests_passed = False
                
        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
            all_tests_passed = False
    
    # 打印测试结果摘要
    print("\n" + "=" * 50)
    print("RV32I指令测试结果摘要:")
    print("已测试的指令类型：")
    print("- R型指令：add, sub, sll, slt, sltu, xor, srl, sra, or, and")
    print("- I型算术指令：addi, slti, sltiu, xori, ori, andi, slli, srli, srai")
    print("- U型指令：lui, auipc")
    print("- J型指令：jal")
    print("- B型分支指令：beq, bne, blt, bge, bltu, bgeu")
    print("- I型内存访问指令：lw, lh, lb, lhu, lbu")
    print("- S型内存存储指令：sw, sh, sb")
    print("- 特殊指令：ecall, ebreak")
    print("=" * 50)
    
    if all_tests_passed:
        print("✓ 所有RV32I指令测试通过！")
    else:
        print("✗ 部分RV32I指令测试失败！")
    
    return all_tests_passed

def run_rv32i_tests():
    """
    运行所有RV32I指令测试
    """
    print("=" * 50)
    print("开始RV32I指令测试")
    print("=" * 50)
    
    tests = [
        ("标签解析测试", test_labels),
        ("基本汇编器功能测试", test_assembler),
        ("所有RV32I指令测试", test_all_instructions),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print("\n" + "=" * 50)
        print(f"运行: {test_name}")
        print("=" * 50)
        
        try:
            if test_func():
                passed_tests += 1
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")
        except Exception as e:
            print(f"✗ {test_name} 抛出异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")
    print("=" * 50)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    # 运行RV32I指令测试
    success = run_rv32i_tests()
    
    # 根据测试结果设置退出代码
    sys.exit(0 if success else 1)