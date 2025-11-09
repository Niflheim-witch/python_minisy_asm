# Minisys Assembler (Python Version)

这是Minisys汇编器的Python实现，用于将Minisys汇编语言程序转换为机器码，并具有链接功能。

## 功能特性

- 将Minisys汇编代码转换为机器码
- 支持完整的MIPS指令集
- 数据段指令支持（.data, .byte, .half, .word, .asciiz, .space）
- 宏定义和宏展开
- 与BIOS和中断处理程序的链接功能
- COE格式和UART串行格式输出
- 简洁易用的命令行界面

## 安装指南

使用pip安装Minisys汇编器：

```bash
cd py_minisys_asm
pip install -e .
```

安装完成后，您可以在任何位置运行`minisys-asm`命令。

## 使用方法

### 命令行语法

```bash
minisys-asm <input_file> <output_directory> [options]
```

### 可用选项
- `-l`, `--link`：与BIOS和中断处理程序链接
- `-d`, `--debug`：启用调试输出

### 使用示例

**基本汇编**：
```bash
minisys-asm example.s output/
```

**带链接功能**：
```bash
minisys-asm example.s output/ -l
```

**启用调试**：
```bash
minisys-asm example.s output/ -d
```

## 输出文件

汇编器生成以下输出文件：

- `<base_name>_text.coe`：包含程序文本段的COE文件
- `<base_name>_data.coe`：包含程序数据段的COE文件（如果有）
- `<base_name>_serial.txt`：用于加载到Minisys系统的UART串行格式文件

## 内存布局

Minisys系统使用哈佛架构，内存布局如下：

- **指令内存（64KB）**：地址范围 0x00000000 - 0x0000FFFF
  - BIOS区域：0x00000000 - 0x000007FF（2KB）
  - 用户程序区域：0x00000800 - 0x0000EFFC（60KB）
  - 中断处理程序区域：0x0000F000 - 0x0000FFFC（4KB）

## BIOS功能

当使用`-l`选项链接时，BIOS会：
1. 初始化系统组件
2. 在串行端口上显示"SEU61522"
3. 跳转到用户程序入口点（0x00000800）

## 支持的指令

### R型指令
- add, addu, sub, subu, and, or, xor, nor, slt, sltu
- sll, srl, sra, sllv, srlv, srav
- mult, multu, div, divu
- mfhi, mflo, mthi, mtlo
- jr, jalr

### I型指令
- addi, addiu, andi, ori, xori, slti, sltiu
- lw, sw, lh, lhu, lb, lbu, sh, sb
- beq, bne, bgez, bgtz, blez, bltz, lui

### J型指令
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
    la $a0, \str
    li $v0, 4
    syscall
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
    la $a0, hello_str
    li $v0, 4
    syscall
    
    li $v0, 10
    syscall
```