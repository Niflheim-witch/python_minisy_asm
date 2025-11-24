# Test file to verify BIOS memory protection
.data
user_var: .word 0

.text
test_bios_write:
    # Try to write to BIOS memory area (should fail)
    li x1, 42
    sw x1, 0(x0)  # Writing to address 0x0 (BIOS area)
    
    # Try to write to user area (should succeed)
    li x1, 100
    sw x1, user_var
    
    # Try to read from BIOS area (should succeed - read is allowed)
    lw x2, 0(x0)
    
    ret