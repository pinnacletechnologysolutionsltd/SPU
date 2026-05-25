#!/usr/bin/env python3
"""flash_layout.py — Generate SPI flash image for SPU-13 program loader.

Reads .bin files from software/programs/ and assembles a raw binary image
for direct programming to W25Q128JV SPI flash via minipro.

Layout (64 KB sector alignment):
  0x000000  Bootloader + VE hydration tables (existing)
  0x010000  Program image (up to 512 bytes = 64 × 64-bit words)
            - Header: program length byte (number of words)
            - Data:  64-bit big-endian instruction words
            - Footer: 0xFFFFFFFF_FFFFFFFF (end-of-program marker)

The sequencer reads from 0x010000, assembles words, stops at the marker.
"""

import struct, sys, os

def pack_program(bin_path: str) -> bytes:
    """Pack a .bin file into the flash format: [len_byte][words...][terminator]"""
    with open(bin_path, 'rb') as f:
        data = f.read()
    num_words = len(data) // 8
    if len(data) % 8 != 0:
        print(f"  WARNING: {bin_path} size {len(data)} not multiple of 8, truncating")
        data = data[:num_words * 8]
    # Header: 1 byte = program length
    result = bytes([num_words & 0xFF])
    # Program words: big-endian 64-bit
    for i in range(num_words):
        w = int.from_bytes(data[i*8:(i+1)*8], 'big')
        result += struct.pack('>Q', w)
    # Terminator: FFFF_FFFF_FFFF_FFFF
    result += struct.pack('>Q', 0xFFFFFFFF_FFFFFFFF)
    return result


def main():
    program_dir = os.path.join(os.path.dirname(__file__), '..', 'software', 'programs')
    
    # Default: use the QLDI marker test
    default_prog = 'call_demo.bin'  # test CALL/RET
    
    prog_name = sys.argv[1] if len(sys.argv) > 1 else default_prog
    prog_path = os.path.join(program_dir, prog_name)
    
    if not os.path.exists(prog_path):
        # Search
        for root, dirs, files in os.walk(program_dir):
            for f in files:
                if f == prog_name:
                    prog_path = os.path.join(root, f)
                    break
    
    if not os.path.exists(prog_path):
        print(f"ERROR: {prog_name} not found")
        available = [f for f in os.listdir(program_dir) if f.endswith('.bin')]
        print(f"Available: {available}")
        sys.exit(1)
    
    print(f"Packing: {prog_path}")
    prog_data = pack_program(prog_path)
    print(f"  Program: {len(prog_data)} bytes (header + words + terminator)")
    
    # Build 64 KB sector starting at 0x010000
    sector = bytearray(65536)  # 64 KB blank sector
    sector[:len(prog_data)] = prog_data
    
    output_path = os.path.join(os.path.dirname(__file__), 'build', 'spu13_program.bin')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(sector)
    
    print(f"Written: {output_path}")
    print(f"  {len(sector)} bytes (64 KB sector for 0x010000)")
    print()
    print("Flash command:")
    print(f"  minipro -p W25Q128JV -w {output_path} -s")
    print()
    
    # Also generate full flash image with library primitives
    lib_output = os.path.join(os.path.dirname(__file__), 'build', 'spu13_wildberger_lib.bin')
    full_image = bytearray(65536 * 16)  # 1 MB for all library sectors
    
    # Sector 1 (0x010000): Program image
    full_image[0x00000:0x00000+len(prog_data)] = prog_data
    
    # Sectors 2-8: Library primitives (placeholders)
    lib_files = [
        ('wildberger_spread.bin', '0x020000', 'spread + collinearity'),
        ('wildberger_geometry.bin', '0x030000', '5 primitives'),
        ('wildberger_calculus.bin', '0x040000', 'tangents + Faulhaber'),
        ('wildberger_layer2.bin', '0x050000', 'quadrance + Pell'),
        ('wildberger_chromogeometry.bin', '0x060000', 'chromogeometry triple'),
        ('wildberger_higher_dim.bin', '0x070000', 'cross matrix + diagonal'),
    ]
    
    for lib_file, addr_str, desc in lib_files:
        lib_path = os.path.join(program_dir, lib_file)
        if os.path.exists(lib_path):
            addr = int(addr_str, 16)
            offset = addr - 0x010000
            lib_data = pack_program(lib_path)
            full_image[offset:offset+len(lib_data)] = lib_data
            print(f"  {addr_str}: {lib_file} ({desc}) — {len(lib_data)} bytes")
    
    with open(lib_output, 'wb') as f:
        f.write(full_image)
    print(f"\nFull library image: {lib_output}")
    print(f"Flash: minipro -p W25Q128JV -w {lib_output}")


if __name__ == '__main__':
    main()
