# RV32I Assembler Example Program
# This program demonstrates basic RV32I assembly language features

.data
number:      .word 42
array:       .space 100

.text
.globl _start

_start:
    # Load number and perform some arithmetic operations
    lw x10, number     # Load number into x10 (a0)
    
    # Simple arithmetic operations
    addi x11, x0, 10   # Set x11 (a1) to 10
    add x12, x10, x11  # Add x10 and x11, result in x12 (a2)
    sub x13, x10, x11  # Subtract x11 from x10, result in x13 (a3)
    
    # Store results in memory
    sw x12, 0(x0)      # Store sum at address 0
    sw x13, 4(x0)      # Store difference at address 4
    
    # Simple loop - count from 0 to 4
    addi x20, x0, 0    # Initialize counter (x20) to 0
    addi x21, x0, 5    # Set loop limit (x21) to 5
    
loop:
    beq x20, x21, loop_end  # Exit loop if counter == 5
    
    # Arithmetic with loop counter
    slli x22, x20, 2   # Shift left by 2 (multiply by 4)
    add x23, x20, x22  # x23 = x20 + (x20 * 4)
    
    # Store result in array
    lw x24, array      # Load array address into x24
    add x25, x24, x20  # Calculate actual address: array + offset
    sw x23, 0(x25)     # Store at calculated address
    
    # Update counter
    addi x20, x20, 1   # Increment counter by 1
    jal x0, loop       # Jump back to loop start
    
loop_end:
    # Program done - infinite loop
    addi x0, x0, 0     # No-op
    jal x0, loop_end   # Loop forever