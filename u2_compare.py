import argparse

# Device info
# 1 page = (2k + 64)=2112 bytes
# 1 block = 64 pages
# 1 device = 1024 blocks = 65536 pages

PAGESIZE = 2112
BLOCKSIZE = PAGESIZE * 64

# return uppercase hex string without 0x
def hexu(value):
    return str(hex(value))[2:].upper()

# check bad block table at requested index. true = valid block, false = bad block
def check_bbtable(blob, index):
    offset = index // 8
    bitpos = index % 8
    value = blob[8 + offset]
    testbit = value >> (7 - bitpos)
    return bool(testbit & 1)

# return big endian 32 bit integer
def int32(blob, offset):
    value = (blob[offset] << 24) + (blob[offset+1] << 16) + (blob[offset+2] << 8) + (blob[offset+3])
    return value

# write big endian 32 bit integer
def writeint32(blob, value, offset):
    blob[offset + 0] = (value & 0xFF000000) >> 24
    blob[offset + 1] = (value & 0x00FF0000) >> 16
    blob[offset + 2] = (value & 0x0000FF00) >> 8
    blob[offset + 3] =  value & 0x000000FF
    return True

# return asset table offset
def toc(index):
    return 0x840 + (index * 0x10)

# check if assets match
def assetmatch(blob1, blob2, index, bb):
    mismatch = 0
    entry1_nand_block = int32(data1, toc(index) + 0x0)
    entry1_offset     = int32(data1, toc(index) + 0x4)
    entry1_size       = int32(data1, toc(index) + 0x8)
    entry1_type       =       data1[toc(index) + 0xC]
    entry1_pos = (entry1_nand_block * BLOCKSIZE) + entry1_offset
    entry2_nand_block = int32(data2, toc(index) + 0x0)
    entry2_offset     = int32(data2, toc(index) + 0x4)
    entry2_size       = int32(data2, toc(index) + 0x8)
    entry2_type       =       data2[toc(index) + 0xC]
    entry2_pos = (entry2_nand_block * BLOCKSIZE) + entry2_offset

    if (entry1_size != entry2_size):
        mismatch = 1
    else:
        badblock0 = False;
        badblock1 = False;
        for i in range(entry1_size):
            if (blob1[entry1_pos + i] != blob2[entry2_pos + i]):
                mismatch = mismatch + 1
                if (i + entry2_offset) < (BLOCKSIZE):
                    badblock0 = True;
                else:
                    badblock1 = True;
                    
    if (mismatch == 0):
        # data matches
        return True
    else:
        print('\nAsset #' + str(index) + ': data mismatch!\nTOC entry position = ' + hexu(toc(index)))
        print('\nOriginal:')
        print('NAND Block = ' + hexu(entry1_nand_block))
        print('Block Offset = ' + hexu(entry1_offset))
        print('File Offset = ' + hexu(entry1_pos))
        print('Size = ' + hexu(entry1_size))

        print('\nTest:')
        print('NAND Block = ' + hexu(entry2_nand_block))
        print('Block Offset = ' + hexu(entry2_offset))
        print('File Offset = ' + hexu(entry2_pos))
        print('Size = ' + hexu(entry2_size))

        if (badblock0 == True): bb.append(entry2_nand_block)
        if (badblock1 == True):
            bb.append(entry2_nand_block+1)
            print('\nAsset ' + str(index) + ' crosses block boundary, stored on blocks ' + hexu(entry2_nand_block) + ' and ' + hexu(entry2_nand_block+1));
        
        return False

# copy known good block to empty block
def bytecopy(blob_orig, blob_fix, block_fix, block_free, block_orig, writeblocks):
    print('Relocating block ' + hexu(block_fix) + ' to ' + hexu(block_free) + ' using data from original block ' + hexu(block_orig))

    for i in range(BLOCKSIZE):
        blob_fix[(block_free * BLOCKSIZE) + i] = blob_orig[(block_orig * BLOCKSIZE) + i]

    writeblocks.append(block_free)
    return 1

# fix blob2 (bytearray) using blob1 (known good u2) for asset=index using block at freeblock
def fixasset(blob1, blob2, index, freeblock, writeblocks):

    print('Fixing Asset #' + str(index))
    entry1_nand_block = int32(data1, toc(index) + 0x0)
    entry1_offset     = int32(data1, toc(index) + 0x4)
    entry1_size       = int32(data1, toc(index) + 0x8)
    entry1_type       =       data1[toc(index) + 0xC]
    entry1_pos = (entry1_nand_block * BLOCKSIZE) + entry1_offset
    entry2_nand_block = int32(data2, toc(index) + 0x0)
    entry2_offset     = int32(data2, toc(index) + 0x4)
    entry2_size       = int32(data2, toc(index) + 0x8)
    entry2_type       =       data2[toc(index) + 0xC]
    entry2_pos = (entry2_nand_block * BLOCKSIZE) + entry2_offset

    
    cross_boundary = True;
    if (entry2_size + entry2_offset) < (BLOCKSIZE):
        cross_boundary = False;

    usedblocks = 0

    # skip bad blocks
    while(True):
        if (check_bbtable(blob2, freeblock) == True) and (check_bbtable(blob2, freeblock + 1) == True): # two blocks good
            break
        else:
            freeblock = freeblock + 1
            usedblocks = usedblocks + 1
            continue
    
    writeint32(blob2, freeblock, toc(index))
    usedblocks = usedblocks + bytecopy(blob1, blob2, entry2_nand_block, freeblock, entry1_nand_block, writeblocks)
    
    if (cross_boundary == True):
        entry1_nand_block = entry1_nand_block + 1
        entry2_nand_block = entry2_nand_block + 1        
        usedblocks = usedblocks + bytecopy(blob1, blob2, entry2_nand_block, freeblock + 1, entry1_nand_block, writeblocks)
        
    return usedblocks

def writeblocksegment(blob, block):
    offset = BLOCKSIZE * block
    filename = 'block-' + str(block) + '.bin'
    blockdata = bytearray()    
    for i in range(BLOCKSIZE):
        blockdata.append(blob[offset + i])
    f = open(filename, 'wb')
    f.write(blockdata)
    f.close()
    return filename

if __name__ == "__main__":

    print("Starting")
    p = argparse.ArgumentParser(description='Compare CV1000 U2 dumps.')
    p.add_argument('good_file', type=str, help='Known good U2 dump (e.g. from MAME romset)')
    p.add_argument('test_file', type=str, help='U2 dump from PCB to test')
    p.add_argument('fixed_file', type=str, help='Fixed U2 output filename')
    args = p.parse_args()

    f1 = open(args.good_file, 'rb')
    f2 = open(args.test_file, 'rb')

    print('Reading ' + args.good_file + '...', end='')
    data1 = f1.read()
    print('done.\nReading ' + args.test_file + '...', end='')
    data2 = f2.read()
    print('done.')

    f2.close()
    f1.close()
    
    assetentry = 0
    badblocks = list()
    badassets = list()
    writeblocks = list([0])
    free_nand_block = 0

    while(True):

        # update estimated free nand block
        currentnandblock = int32(data2, toc(assetentry) + 0x0)
        if (currentnandblock > free_nand_block):
            free_nand_block = currentnandblock

        # check for bad assets
        if (assetmatch(data1, data2, assetentry, badblocks) == False):
            badassets.append(assetentry)

        # advance to next entry until no more entries
        assetentry = assetentry + 1
        if (int32(data1, toc(assetentry)) == 0xFFFFFFFF):
            break
        else:
            continue

    # find free NAND block, assuming first 4 bytes are FF
    while(True):
        free_nand_block = free_nand_block + 1
        if ((int32(data2, free_nand_block * BLOCKSIZE) == 0xFFFFFFFF)):
            break
        else:
            continue
       

    if (len(badassets) > 0):
        print('\nBad assets: ')
        for badasset in badassets:
            print(str(badasset))

        print('\nBad blocks: ')
        for badblock in badblocks:
            print(hexu(badblock))

        print('\nBad assets detected, attempting fix.')
        print('Starting free NAND block ' + hexu(free_nand_block) + ', offset ' + hexu(free_nand_block * BLOCKSIZE))
        
        data3 = bytearray(data2)

        for badasset in badassets:
            free_nand_block = free_nand_block + fixasset(data1, data3, badasset, free_nand_block, writeblocks)

        print('Writing ' + args.fixed_file + '...', end='')
        f3 = open(args.fixed_file, 'wb')
        f3.write(data3)
        f3.close()
        print('done.')

        print('\nThese blocks need to be written to NAND:')
        for writeblock in writeblocks:
            print(writeblocksegment(data3, writeblock))
        
    else:
        print('\nNo bad assets found.')    

    print("\nDone.")
