# Minisys Assembler Example Program
# This program demonstrates basic assembly language features

.data
hello_str:   .asciiz "Hello, Minisys!\n"
number:      .word 42
counter:     .word 0
array:       .space 100

.text
.globl main

main:
    # Display hello message
    la $a0, hello_str  # Load address of hello_str
    li $v0, 4          # System call for print string
    syscall            # Execute system call
    
    # Load number and display it
    lw $a0, number     # Load number into $a0
    li $v0, 1          # System call for print integer
    syscall            # Execute system call
    
    # Print newline
    li $a0, 10         # ASCII code for newline
    li $v0, 11         # System call for print character
    syscall            # Execute system call
    
    # Simple loop - count from 0 to 4
    li $t0, 0          # Initialize counter to 0
    li $t1, 5          # Set loop limit to 5
    
loop:
    beq $t0, $t1, loop_end  # Exit loop if counter == 5
    
    # Display current count
    move $a0, $t0      # Move counter to $a0
    li $v0, 1          # System call for print integer
    syscall            # Execute system call
    
    # Print space
    li $a0, 32         # ASCII code for space
    li $v0, 11         # System call for print character
    syscall            # Execute system call
    
    # Update counter
    addi $t0, $t0, 1   # Increment counter by 1
    j loop             # Jump back to loop start
    
loop_end:
    # Print newline
    li $a0, 10         # ASCII code for newline
    li $v0, 11         # System call for print character
    syscall            # Execute system call
    
    # Exit program
    li $v0, 10         # System call for exit
    syscall            # Execute system call