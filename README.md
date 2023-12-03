# u2_compare
Fix CAVE PCBs with graphics issues by comparing CV1000 U2 dumps and generating relocated NAND blocks

usage: u2_compare.py good_file test_file fixed_file

Compare CV1000 U2 dumps.

  good_file:    Known good U2 dump (e.g. from MAME romset)
  test_file:    U2 dump from CAVE CV1000 PCB to test / repair
  fixed_file:   Name of fixed file to output

Example:
py u2_compare.py u2-original u2 u2-fixed

This will compare known good "u2-original" to "u2" and check for errors.
If errors are found, it will attempt to relocate the bad assets to empty blocks at the end of NAND,
write a fixed U2 file, and also generate individual blocks (decimal numbering) for writing to the NAND.

Example program output:

py u2_compare.py u2-original u2 u2-fixed
Starting
Reading u2-original...done.
Reading u2...done.

Asset #960: data mismatch!
TOC entry position = 4440

Original:
NAND Block = 15E
Block Offset = 1AC9E
File Offset = 2D38C9E
Size = E1A7

Test:
NAND Block = 15E
Block Offset = 1AC9E
File Offset = 2D38C9E
Size = E1A7

Asset 960 crosses block boundary, stored on blocks 15E and 15F

Asset #990: data mismatch!
TOC entry position = 4620

Original:
NAND Block = 16B
Block Offset = 15BAD
File Offset = 2EE0BAD
Size = E750

Test:
NAND Block = 16C
Block Offset = 15BAD
File Offset = 2F01BAD
Size = E750

Asset 990 crosses block boundary, stored on blocks 16C and 16D

Bad assets:
960
990

Bad blocks:
15F
16D

Bad assets detected, attempting fix.
Starting free NAND block 2D3, offset 5D33000
Fixing Asset #960
Relocating block 15E to 2D3 using data from original block 15E
Relocating block 15F to 2D4 using data from original block 15F
Fixing Asset #990
Relocating block 16C to 2D5 using data from original block 16B
Relocating block 16D to 2D6 using data from original block 16C
Writing u2-fixed...done.

These blocks need to be written to NAND:
block-0.bin
block-723.bin
block-724.bin
block-725.bin
block-726.bin

Done.
