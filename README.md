# Minisys Assembler (Python Version)

这是Minisys汇编器的Python实现，用于将Minisys汇编语言程序转换为机器码，并提供与BIOS和中断处理程序的链接功能。

## 功能特性

- 将Minisys汇编代码转换为机器码
- 支持完整的RISC-V指令集（RV32I）
- 数据段指令支持（.data, .byte, .half, .word, .asciiz, .space）
- 宏定义和宏展开功能
- 与BIOS和中断处理程序的自动链接功能
- COE格式输出（用于FPGA配置）
- UART串行格式输出（serial.txt）用于系统加载
- 简洁易用的命令行界面
- BIOS-only汇编模式支持

## 安装指南

使用pip安装Minisys汇编器：

```bash
cd py_minisys_asm
pip install -e .
```

安装完成后，您可以在任何位置运行`minisys-asm`命令。

## 使用方法

### 命令行语法

汇编器支持两种运行方式：

**1. 作为Python模块运行（推荐）**：
```bash
python -m py_minisys_asm.main <input_file> <output_directory> [options]
```

**2. 通过安装后的命令运行**：
```bash
minisys-asm <input_file> <output_directory> [options]
```

### 可用选项
- `-s`, `--bios-only`：仅汇编BIOS并输出到指定目录
- `-d`, `--debug`：启用调试输出

### 使用示例

**标准汇编（自动链接）**：
```bash
# 作为Python模块运行
python -m py_minisys_asm.main example.s output/

# 或通过安装后的命令运行
minisys-asm example.s output/
```

**BIOS-only模式**：
```bash
# 作为Python模块运行
python -m py_minisys_asm.main dummy.asm bios_output -s

# 或通过安装后的命令运行
minisys-asm dummy.asm bios_output -s
```

**启用调试输出**：
```bash
# 作为Python模块运行
python -m py_minisys_asm.main example.s output/ -d

# 或通过安装后的命令运行
minisys-asm example.s output/ -d
```

**同时使用多个选项**：
```bash
# 作为Python模块运行，同时启用BIOS-only模式和调试输出
python -m py_minisys_asm.main dummy.asm bios_output -d -s
```

## 输出文件

汇编器生成以下输出文件：

- `<base_name>_text.coe`：包含程序文本段（指令）的COE格式文件
- `<base_name>_data.coe`：包含程序数据段的COE格式文件（如果有）
- `<base_name>_serial.txt`：用于通过UART串行接口加载到Minisys系统的格式文件
  - 包含程序握手信号（03020000）
  - 包含数据握手信号（03030000）
  - 每行一个8位十六进制值，便于串行传输

## 内存布局

Minisys系统使用哈佛架构，内存布局如下：

- **指令内存（64KB）**：地址范围 0x00000000 - 0x0000FFFF
  - BIOS区域：0x00000000 - 0x000007FF（2KB）
  - 用户程序区域：0x00000800 - 0x0000EFFC（60KB）
  - 中断处理程序区域：0x0000F000 - 0x0000FFFC（4KB）

> **注意**：根据链接器配置，用户程序将自动加载到0x00000800地址开始的区域。

## BIOS功能

BIOS（基本输入/输出系统）负责系统初始化和程序引导，其主要功能包括：

1. 初始化系统栈指针（x2寄存器）
2. 关闭LED指示灯和数码管显示
3. 跳转到用户程序的main函数入口点
4. 程序结束时执行系统调用（ecall）

在标准模式下，汇编器会自动将用户程序与BIOS链接，无需额外选项。

## 支持的指令

### R型指令（寄存器操作指令）
- add, sub, and, or, xor, sll, srl, sra, slt, sltu
- sllv, srlv, srav
- mult, multu, div, divu
- mfhi, mflo, mthi, mtlo
- jr, jalr

### I型指令（立即数指令）
- addi, andi, ori, xori, slti, sltiu, lui, auipc
- lw, sw, lh, lhu, lb, lbu, sh, sb
- beq, bne, blt, bge, bltu, bgeu
- bgez, bgtz, blez, bltz

### J型指令（跳转指令）
- j, jal, bgezal, bltzal

### 特殊指令
- nop, syscall, mfc0, mtc0, eret

## 数据指令

- `.byte`：定义字节值
- `.half`：定义半字（2字节）值
- `.word`：定义字（4字节）值
- `.asciiz`：定义以空字符结尾的ASCII字符串
- `.space`：在内存中保留空间

## 宏定义示例

在汇编代码中定义和使用宏：

```assembly
.macro PRINT_STRING(str)
    la a0, \str
    li a7, 4
    ecall
.end_macro

PRINT_STRING(hello_str)
```

## 简单程序示例

```assembly
.data
hello_str: .asciiz "Hello Minisys!\n"

.text
.globl main
main:
    la a0, hello_str
    li a7, 4
    ecall
    
    li a7, 10
    ecall
```