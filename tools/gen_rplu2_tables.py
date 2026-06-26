#!/usr/bin/env python3
"""gen_rplu2_tables.py — Generate RPLU v2 boot table binary for SPI flash.

Flash record format (each = 16 bytes big-endian):
  Header[7:0]:  sel(3) @ bit[2:0] of byte[6:5], material(4) @ byte[6:4], addr(10) @ byte[5:3]
  Data[7:0]:    64-bit payload

Offset in SPI flash: 0x110000 (FLASH_RPLU_CFG_BASE)
"""

import struct
import sys
import os

SPU_CMD_WRITE_RPLU_CFG = 0xA5
NUM_PADE_COEFFS = 4       # 00-11: c0..c3 for numerator/denominator

def rplu_header(sel, material, addr):
    """Pack 64-bit header matching spu_rplu_header() in spu_link.c"""
    return ((SPU_CMD_WRITE_RPLU_CFG & 0xFF) << 56) | \
           ((sel & 0x7) << 48) | \
           ((material & 0xF) << 44) | \
           ((addr & 0x3FF) << 34)

def pade_coeff_record(sel, idx, c0, c1, c2, c3):
    """Generate two 16-byte records for one Padé coefficient.
    
    sel=1 for numerator, sel=2 for denominator.
    First record: low pair (c0, c1) with addr bit[3]=0
    Second record: high pair (c2, c3) with addr bit[3]=1, commits coefficient
    """
    records = []
    # Low pair
    hdr = rplu_header(sel, 0, (idx << 1) | 0)
    data = (c1 << 32) | c0
    records.append(struct.pack('>QQ', hdr, data))
    # High pair + commit
    hdr = rplu_header(sel, 0, (idx << 1) | 1)
    data = (c3 << 32) | c2
    records.append(struct.pack('>QQ', hdr, data))
    return records

def btu_row_record(row_addr, c0, c1, c2, c3):
    """Generate one 16-byte record for a BTU row.
    
    sel=3. Each record writes one row pair (4 M31 coefficients).
    """
    hdr = rplu_header(3, 0, row_addr & 0x3FF)
    data = (c3 << 48) | (c2 << 32) | (c1 << 16) | c0
    return struct.pack('>QQ', hdr, data)

def quadray_kappa_record(kappa):
    """Generate one 16-byte record for quadray target kappa.
    
    sel=6. kappa is the target M31 quadrance invariant.
    """
    hdr = rplu_header(6, 0, 0)
    data = kappa & 0xFFFFFFFF
    return struct.pack('>QQ', hdr, data)

def main():
    records = bytearray()

    # ── Padé numerator coefficients (sel=1) ──────────────────────────
    # Identity default: p(z) = 1
    # p_0(z) = 1  (c0=1, c1=c2=c3=0)
    # p_1(z) = 1  p_2(z) = 1  p_3(z) = 1
    for i in range(NUM_PADE_COEFFS):
        for rec in pade_coeff_record(1, i, 1, 0, 0, 0):
            records.extend(rec)

    # ── Padé denominator coefficients (sel=2) ────────────────────────
    # Identity default: q(z) = 1
    for i in range(NUM_PADE_COEFFS):
        for rec in pade_coeff_record(2, i, 1, 0, 0, 0):
            records.extend(rec)

    # ── BTU rows (sel=3) ─────────────────────────────────────────────
    # Zero-initialized: 64 rows × 4 M31 coefficients
    for row in range(64):
        records.extend(btu_row_record(row, 0, 0, 0, 0))

    # ── Quadray target kappa (sel=6) ─────────────────────────────────
    # Default: 0 (point variety / origin)
    records.extend(quadray_kappa_record(0))

    # ── Write output ─────────────────────────────────────────────────
    output_dir = os.path.join(os.path.dirname(__file__), 'build')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'rplu2_boot_tables.bin')

    with open(output_path, 'wb') as f:
        f.write(records)

    num_records = len(records) // 16
    print(f"RPLU v2 boot tables: {output_path}")
    print(f"  {num_records} records × 16 bytes = {len(records)} bytes")
    print(f"  Flash offset: 0x110000")
    print()
    print("Records:")
    print(f"  Padé numerator   (sel=1): {NUM_PADE_COEFFS * 2} records")
    print(f"  Padé denominator (sel=2): {NUM_PADE_COEFFS * 2} records")
    print(f"  BTU rows         (sel=3): 64 records")
    print(f"  Quadray kappa    (sel=6): 1 record")
    print()
    print("Flash command:")
    print(f"  minipro -p W25Q128JV -w {output_path} -s")

if __name__ == '__main__':
    main()
