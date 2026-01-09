.text
    # ==========================
    # Minisys Minimal BIOS
    # Target: Call main (jal ra, main)
    # ==========================
    
    # The linker (linker.py) will automatically patch the beginning of this BIOS
    # with a direct JAL ra instruction to the 'main' label if it exists in the user program.
    # 
    # This simulates a function call, so 'main' can theoretically return (though usually it doesn't).
    # 
    # Placeholder for patched code:
    nop
    nop
    nop
    nop

    # Safety Loop (in case JAL returns)
loop:
    jal x0, loop
