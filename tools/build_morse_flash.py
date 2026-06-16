#!/usr/bin/env python3
"""
build_morse_flash.py — Generate SPI flash image with Morse periodic table.

Reads material_morse_vectors.csv and packs V(r) + dissociation tables into a
flash sector at 0x080000 (sector 8, 512 KB after bootloader).  The RPLU
skel can load these at boot or the config interface can stream updates
from SD card / UART at runtime.

Flash layout (sector 8, offset 0x080000):
  0x080000  Header: magic (4B) + num_elements (2B) + reserved (2B) + table_size (2B) + entry_size (2B)
  0x080010  Element directory: 16B per element (name[8], Z[2], entries[2], v_offset[4])
  0x080100  V(r) tables: NUM_ELEMENTS × (entries × 8 bytes) — 64-bit {P[31:0], Q[31:0]}
  0x100000  Dissociation tables: 1 bit per V(r) entry, packed into bytes

Usage:
  python3 tools/build_morse_flash.py [--output build/morse_periodic_table.bin]
"""

import csv
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / "hardware/rtl/arch/material_morse_vectors.csv"
SECTOR_SIZE = 65536  # 64 KB
MORSE_SECTOR_OFFSET = 0x80000  # sector 8

MAGIC = 0x4D525345  # "MRSE"
MATERIAL_ORDER = [
    "carbon",
    "iron",
    "aluminum",
    "silicon",
    "titanium",
    "nickel",
    "copper",
    "tungsten",
]
ATOMIC_NUMBERS = {
    "carbon": 6,
    "iron": 26,
    "aluminum": 13,
    "silicon": 14,
    "titanium": 22,
    "nickel": 28,
    "copper": 29,
    "tungsten": 74,
}


def pack_pq(p_int: int, q_int: int) -> bytes:
    """Pack P|Q into 64-bit big-endian {P[31:0], Q[31:0]}."""
    p32 = p_int & 0xFFFFFFFF
    q32 = q_int & 0xFFFFFFFF
    return struct.pack(">II", p32, q32)


def main():
    output = sys.argv[1] if len(sys.argv) > 1 else str(
        REPO / "build" / "morse_periodic_table.bin"
    )

    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run tools/generate_morse_csv.py first.")
        return 1

    # Parse CSV
    elements = {}  # name → [(r, V, p_int, q_int, dissoc)]
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["material"]
            if name not in elements:
                elements[name] = []
            elements[name].append(
                (
                    float(row["r"]),
                    float(row["V"]),
                    int(row["p_int"]),
                    int(row["q_int"]),
                    int(row["dissoc"]),
                )
            )

    ordered_names = [name for name in MATERIAL_ORDER if name in elements]
    ordered_names.extend(name for name in elements if name not in ordered_names)

    num_elements = len(ordered_names)
    entries_per = len(elements[ordered_names[0]])
    print(f"Elements: {num_elements}, entries/element: {entries_per}")

    # Calculate layout
    header_size = 16
    dir_entry_size = 16
    dir_size = num_elements * dir_entry_size
    v_table_start = header_size + dir_size  # relative to sector start
    v_bytes_per_element = entries_per * 8  # 64-bit per entry
    v_table_size = num_elements * v_bytes_per_element
    dissoc_start = v_table_start + v_table_size
    dissoc_bytes_per_element = (entries_per + 7) // 8  # packed bits
    dissoc_size = num_elements * dissoc_bytes_per_element
    total_size = dissoc_start + dissoc_size

    # Pad to sector boundary
    padded_size = ((total_size + SECTOR_SIZE - 1) // SECTOR_SIZE) * SECTOR_SIZE
    sectors_needed = padded_size // SECTOR_SIZE
    print(f"V table: {v_table_size} bytes")
    print(f"Dissoc table: {dissoc_size} bytes")
    print(f"Total: {total_size} bytes ({sectors_needed} sectors)")

    # Build image
    image = bytearray(padded_size)

    # Header
    struct.pack_into(">IHHHH", image, 0, MAGIC, num_elements, 0, entries_per, 8)

    # Element directory
    v_offset = v_table_start
    d_offset = dissoc_start
    for i, name in enumerate(ordered_names):
        rows = elements[name]
        name_bytes = name.encode("ascii")[:8].ljust(8, b"\0")
        z = ATOMIC_NUMBERS.get(name, 0)
        dir_pos = header_size + i * dir_entry_size
        struct.pack_into(
            ">8sHHII",
            image,
            dir_pos,
            name_bytes,
            z,
            entries_per,
            v_offset,
            d_offset,
        )
        v_offset += v_bytes_per_element
        d_offset += dissoc_bytes_per_element

    # V(r) tables
    for i, name in enumerate(ordered_names):
        rows = elements[name]
        v_base = v_table_start + i * v_bytes_per_element
        for j, (r, v, p_int, q_int, dissoc) in enumerate(rows):
            image[v_base + j * 8 : v_base + j * 8 + 8] = pack_pq(p_int, q_int)

    # Dissociation tables (1 bit per entry, packed MSB first)
    for i, name in enumerate(ordered_names):
        rows = elements[name]
        d_base = dissoc_start + i * dissoc_bytes_per_element
        for j, (r, v, p_int, q_int, dissoc) in enumerate(rows):
            if dissoc:
                byte_idx = j // 8
                bit_idx = 7 - (j % 8)  # MSB first
                image[d_base + byte_idx] |= 1 << bit_idx

    # Write output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image)

    print(f"\nWrote: {output_path} ({len(image)} bytes)")
    print()
    print("Flash layout:")
    print(f"  Sector 8 (0x{MORSE_SECTOR_OFFSET:06X}): Morse Periodic Table")
    print(f"    Header: 0x{MORSE_SECTOR_OFFSET:06X}")
    print(f"    Directory: 0x{MORSE_SECTOR_OFFSET + header_size:06X}")
    print(f"    V tables: 0x{MORSE_SECTOR_OFFSET + v_table_start:06X}")
    print(f"    Dissoc tables: 0x{MORSE_SECTOR_OFFSET + dissoc_start:06X}")
    print(f"  Sectors {8}-{8 + sectors_needed - 1}: 0x{MORSE_SECTOR_OFFSET:06X}-0x{MORSE_SECTOR_OFFSET + padded_size:06X}")
    print()
    print("To flash:")
    print(
        f"  minipro -p W25Q128JV -w {output_path} -s"
    )
    print()
    print("To merge with existing bootloader:")
    print("  1. Backup: minipro -p W25Q128JV -r build/flash_backup.bin")
    print(
        f"  2. Merge:  dd if={output_path} of=build/flash_backup.bin bs=1 seek={MORSE_SECTOR_OFFSET} conv=notrunc"
    )
    print("  3. Write:  minipro -p W25Q128JV -w build/flash_backup.bin -s")
    print()
    print("Runtime update (RPLU cfg interface):")
    print("  cfg_wr_en=1, cfg_wr_sel=0, cfg_wr_material=0..15, cfg_wr_addr=0..1023, cfg_wr_data={P[31:0],Q[31:0]}")
    print("  cfg_wr_en=1, cfg_wr_sel=1, cfg_wr_material=0..15, cfg_wr_addr=0..1023, cfg_wr_data[0]=dissoc_bit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
