#!/usr/bin/env python3
"""gen_rplu2_tables.py — Generate RPLU v2 boot table binary for SPI flash.

Flash record format (each = 16 bytes big-endian):
  Header[7:0]:  sel(3) @ bit[2:0] of byte[6:5], material(4) @ byte[6:4], addr(10) @ byte[5:3]
  Data[7:0]:    64-bit payload

Offset in SPI flash: 0x110000 (FLASH_RPLU_CFG_BASE)
"""

import argparse
import struct
import os

SPU_CMD_WRITE_RPLU_CFG = 0xA5
NUM_PADE_COEFFS = 5       # [4/4] Padé: coefficients 0..4

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
    hdr = rplu_header(sel, 0, idx)
    data = (c1 << 32) | c0
    records.append(struct.pack('>QQ', hdr, data))
    # High pair + commit
    hdr = rplu_header(sel, 0, 0x8 | idx)
    data = (c3 << 32) | c2
    records.append(struct.pack('>QQ', hdr, data))
    return records

def btu_row_record(row_addr, c0, c1, c2, c3):
    """Generate two 16-byte records for a BTU row.

    sel=3. addr[5:0] selects the row and addr[6] selects the lane pair.
    Pair 0 writes lanes c0/c1; pair 1 writes lanes c2/c3.
    """
    records = []
    row = row_addr & 0x3F
    hdr = rplu_header(3, 0, row)
    data = ((c1 & 0xFFFFFFFF) << 32) | (c0 & 0xFFFFFFFF)
    records.append(struct.pack('>QQ', hdr, data))
    hdr = rplu_header(3, 0, 0x40 | row)
    data = ((c3 & 0xFFFFFFFF) << 32) | (c2 & 0xFFFFFFFF)
    records.append(struct.pack('>QQ', hdr, data))
    return records

def quadray_kappa_record(kappa):
    """Generate one 16-byte record for quadray target kappa.
    
    sel=6. kappa is the target M31 quadrance invariant.
    """
    hdr = rplu_header(6, 0, 0)
    data = kappa & 0xFFFFFFFF
    return struct.pack('>QQ', hdr, data)

def checksum(records):
    total = 0
    for offset in range(0, len(records), 16):
        header = int.from_bytes(records[offset:offset + 8], 'big')
        data = int.from_bytes(records[offset + 8:offset + 16], 'big')
        total = (
            total
            + ((header >> 32) & 0xFFFFFFFF)
            + (header & 0xFFFFFFFF)
            + ((data >> 32) & 0xFFFFFFFF)
            + (data & 0xFFFFFFFF)
        ) & 0xFFFFFFFF
    return total

def profile_constants(profile):
    num = [(0, 0, 0, 0) for _ in range(NUM_PADE_COEFFS)]
    den = [(0, 0, 0, 0) for _ in range(NUM_PADE_COEFFS)]
    btu = [(0, 0, 0, 0) for _ in range(64)]
    kappa = 0

    if profile == 'default':
        num[0] = (1, 0, 0, 0)
        den[0] = (1, 0, 0, 0)
    elif profile == 'consume_probe':
        # Strong hardware-consumption profile:
        #   SOM feature (2,0,0,0) chooses node 1.
        #   BTU row 1 emits Quadray/A31 coordinate (1,0,0,0).
        #   kappa=3 makes the Quadray variety coherent.
        #   Constant Padé numerator=2 and denominator=1 yields thimble c0=2.
        num[0] = (2, 0, 0, 0)
        den[0] = (1, 0, 0, 0)
        btu[1] = (1, 0, 0, 0)
        kappa = 3
    else:
        raise ValueError(f"unknown profile: {profile}")

    return num, den, btu, kappa

def build_records(profile):
    records = bytearray()
    num_coeffs, den_coeffs, btu_rows, kappa = profile_constants(profile)

    # ── Padé numerator coefficients (sel=1) ──────────────────────────
    for i, coeff in enumerate(num_coeffs):
        for rec in pade_coeff_record(1, i, *coeff):
            records.extend(rec)

    # ── Padé denominator coefficients (sel=2) ────────────────────────
    for i, coeff in enumerate(den_coeffs):
        for rec in pade_coeff_record(2, i, *coeff):
            records.extend(rec)

    # ── BTU rows (sel=3) ─────────────────────────────────────────────
    for row, coeff in enumerate(btu_rows):
        for rec in btu_row_record(row, *coeff):
            records.extend(rec)

    # ── Quadray target kappa (sel=6) ─────────────────────────────────
    records.extend(quadray_kappa_record(kappa))

    return records

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--profile',
        choices=('default', 'consume_probe'),
        default='default',
        help='table profile to generate',
    )
    parser.add_argument(
        '--output',
        help='output path; defaults to tools/build/rplu2_boot_tables.bin',
    )
    args = parser.parse_args()

    records = build_records(args.profile)

    # ── Write output ─────────────────────────────────────────────────
    output_dir = os.path.join(os.path.dirname(__file__), 'build')
    os.makedirs(output_dir, exist_ok=True)
    output_path = args.output or os.path.join(output_dir, 'rplu2_boot_tables.bin')

    with open(output_path, 'wb') as f:
        f.write(records)

    num_records = len(records) // 16
    print(f"RPLU v2 boot tables: {output_path}")
    print(f"  Profile: {args.profile}")
    print(f"  {num_records} records × 16 bytes = {len(records)} bytes")
    print(f"  Checksum: 0x{checksum(records):08X}")
    print(f"  Flash offset: 0x110000")
    print()
    print("Records:")
    print(f"  Padé numerator   (sel=1): {NUM_PADE_COEFFS * 2} records")
    print(f"  Padé denominator (sel=2): {NUM_PADE_COEFFS * 2} records")
    print(f"  BTU rows         (sel=3): 128 records")
    print(f"  Quadray kappa    (sel=6): 1 record")
    print()
    print("Flash command:")
    print(f"  tools/rp2040_flash_pmod.py --port <tty> write {output_path} --offset 0x110000")

if __name__ == '__main__':
    main()
