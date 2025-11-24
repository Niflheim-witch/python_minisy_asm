# ====== 简化版 minisys-bios.asm ======
.text
    # 初始化栈指针 (x2)
    lui x2, 1
    
    # 关闭LED
    addi x23, x0, 0xFC60   # LED基址
    sw x0, 0(x23)          # 关LED
    
    # 关闭数码管
    addi x20, x0, 0xFC04   # 位码基址
    addi x22, x0, 8        # 关闭位码值
    sw x22, 0(x20)         # 关数码管
    
    # 跳转到用户程序的main函数
    jal main
    nop
    
    # 程序结束，执行ecall
    ecall
# ====== 简化版 minisys-bios.asm ======
