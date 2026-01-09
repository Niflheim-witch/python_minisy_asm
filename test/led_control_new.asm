.data

.text
delay:
    addi sp, sp, -24
    sw ra, 20(sp)
    sw s0, 16(sp)
    addi s0, sp, 24
    lui  t0, 7
    addi t0, t0, 1328
    sw t0, -12(s0)
.lop1:
    lw t0, -12(s0)
    addi t1, x0, 0
    slt t2, t1, t0
    beq t2, x0, .end2
    lw t0, -12(s0)
    addi t1, x0, 1
    sub t2, t0, t1
    sw t2, -12(s0)
    jal x0, .lop1
.end2:
    addi a0, x0, 0
    jal x0, .L_ret_delay_0
.L_ret_delay_0:
    lw s0, 16(sp)
    lw ra, 20(sp)
    addi sp, sp, 24
    jalr x0, 0(ra)

.globl main
main:
    lui sp, 0x00010
    addi sp, sp, -24
    sw ra, 20(sp)
    sw s0, 16(sp)
    addi s0, sp, 24
    addi t0, x0, 1
    sw t0, -12(s0)
.lop4:
    addi t0, x0, 1
    beq t0, x0, .end5
    lw t0, -12(s0)
    addi t1, x0, -928
    sw t0, 0(t1)
    lw t0, -12(s0)
    addi t1, x0, 1
    sll t2, t0, t1
    sw t2, -12(s0)
    lw t0, -12(s0)
    lui  t1, 16
    addi t1, t1, 0
    sub t2, t0, t1
    sltiu t2, t2, 1
    beq t2, x0, .L_end_if7
    addi t0, x0, 1
    sw t0, -12(s0)
.L_end_if7:
    jal ra, delay
    addi t0, a0, 0
    jal x0, .lop4
.end5:
    addi a0, x0, 0
    jal x0, .L_ret_main_3
.L_ret_main_3:
    lw s0, 16(sp)
    lw ra, 20(sp)
    addi sp, sp, 24
    jalr x0, 0(ra)