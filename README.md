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
