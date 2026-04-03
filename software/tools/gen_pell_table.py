#!/usr/bin/env python3
"""
gen_pell_table.py — SPU-13 Flash Table Generator
Generates the binary blobs burned to W25Q128JVSQ at flash offsets.

Flash layout (W25Q128JVSQ = 16MB = 0x1000000):
  0x000000 – 0x03FFFF : FPGA bitstream    (256KB reserved, UP5K ~150KB)
  0x040000 – 0x07FFFF : Safe Soul fallback bootloader
  0x080000 – 0x0FFFFF : Ghost OS kernel / Lithic-L programs
  0x100000 – 0x1000FF : Pell table         (13 steps × 8 bytes = 104 bytes)
  0x100100 – 0x1001FF : Golden Prime LUT   (13 primes × 4 bytes = 52 bytes)
  0x100200 – 0x1003FF : Reserved for QROT velocity table
  0x200000 +          : bloom.bin, world data (14MB free)

Usage:
    python3 gen_pell_table.py
    # Outputs: software/flash/pell_13.bin
    #          software/flash/golden_prime_lut.bin
    #          software/flash/flash_map.txt  (human-readable manifest)
"""

import sys
import os
import struct

# Bring in RationalSurd from spu_vm — single source of truth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from spu_vm import RationalSurd, rs_lt

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'flash')

# ---------------------------------------------------------------------------
# Pell sequence in Q(√3)
# ---------------------------------------------------------------------------
# The Pell rotor r = (2 + 1·√3).  r^n = (a_n + b_n·√3)
# Recurrence: (a+b√3)(2+√3) = (2a+3b) + (a+2b)√3
# Sequence:  r^0=(1,0), r^1=(2,1), r^2=(7,4), r^3=(26,15), ...
# Q(r^n) = a_n² - 3b_n² = 1  for all n  (unit quadrance — always laminar)

def pell_sequence(steps: int) -> list[RationalSurd]:
    """Generate the first `steps` elements of the Pell orbit in Q(√3)."""
    seq = [RationalSurd(1, 0)]          # r^0 = identity
    rotor = RationalSurd(2, 1)
    for _ in range(steps - 1):
        seq.append(seq[-1] * rotor)
    return seq

# ---------------------------------------------------------------------------
# Golden Primes (Laminar addressing strides — minimum 2-power dissonance)
# ---------------------------------------------------------------------------

def is_prime(n: int) -> bool:
    if n < 2: return False
    if n in (2, 3): return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def cubic_dissonance(p: int) -> float:
    """Distance from nearest power of 2 in log₂ space. Lower = more laminar."""
    import math
    d = abs(math.log2(p) - round(math.log2(p)))
    return 1.0 / (d + 1e-6)

def golden_primes(count: int = 13, search_max: int = 65535) -> list[int]:
    """Find `count` primes with minimum cubic dissonance (most laminar strides)."""
    candidates = [(p, cubic_dissonance(p))
                  for p in range(search_max, search_max // 2, -1)
                  if is_prime(p)]
    candidates.sort(key=lambda x: x[1])
    return [p for p, _ in candidates[:count]]

# ---------------------------------------------------------------------------
# Binary serialization
# ---------------------------------------------------------------------------

def pack_rational_surd(rs: RationalSurd) -> bytes:
    """Pack a RationalSurd as two signed 32-bit big-endian integers (8 bytes)."""
    return struct.pack('>ii', rs.a, rs.b)

def pack_prime(p: int) -> bytes:
    """Pack a 32-bit unsigned prime (4 bytes big-endian)."""
    return struct.pack('>I', p)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    NUM_PELL  = 13
    NUM_PRIME = 13

    # ── Pell table ──────────────────────────────────────────────────────────
    pell = pell_sequence(NUM_PELL)
    pell_bin = b''.join(pack_rational_surd(r) for r in pell)
    pell_path = os.path.join(OUT_DIR, 'pell_13.bin')
    with open(pell_path, 'wb') as f:
        f.write(pell_bin)

    print(f"Pell table  ({len(pell_bin):>4d} bytes) → {pell_path}")
    print(f"  Flash offset: 0x100000")
    for i, r in enumerate(pell):
        q = r.quadrance()
        print(f"  [{i:02d}] ({r.a:>12d} + {r.b:>12d}·√3)  Q={q}")

    # ── Golden Prime LUT ────────────────────────────────────────────────────
    primes = golden_primes(NUM_PRIME)
    prime_bin = b''.join(pack_prime(p) for p in primes)
    prime_path = os.path.join(OUT_DIR, 'golden_prime_lut.bin')
    with open(prime_path, 'wb') as f:
        f.write(prime_bin)

    print(f"\nGolden Primes ({len(prime_bin):>4d} bytes) → {prime_path}")
    print(f"  Flash offset: 0x100100")
    for i, p in enumerate(primes):
        print(f"  [{i:02d}] {p}")

    # ── Flash map manifest ───────────────────────────────────────────────────
    map_path = os.path.join(OUT_DIR, 'flash_map.txt')
    with open(map_path, 'w') as f:
        f.write("W25Q128JVSQ Flash Map — SPU-13 iCEsugar\n")
        f.write("=" * 48 + "\n")
        f.write(f"  0x000000 – 0x03FFFF  FPGA bitstream        (256KB)\n")
        f.write(f"  0x040000 – 0x07FFFF  Safe Soul fallback\n")
        f.write(f"  0x080000 – 0x0FFFFF  Ghost OS / Lithic-L\n")
        f.write(f"  0x100000 – 0x100067  Pell table            ({len(pell_bin)} bytes)\n")
        f.write(f"  0x100100 – 0x100133  Golden Prime LUT      ({len(prime_bin)} bytes)\n")
        f.write(f"  0x100200 – 0x1003FF  QROT velocity table   (reserved)\n")
        f.write(f"  0x200000 – 0xFFFFFF  bloom.bin / world data (~14MB free)\n")
        f.write("\nPell steps (a, b) where value = a + b·√3:\n")
        for i, r in enumerate(pell):
            f.write(f"  r^{i:02d}: a={r.a}, b={r.b}\n")
        f.write("\nGolden Primes (IVM addressing strides):\n")
        for i, p in enumerate(primes):
            f.write(f"  GP[{i:02d}]: {p}\n")

    print(f"\nFlash map   → {map_path}")
    print(f"\n  To burn pell_13.bin via T48:")
    print(f"    Write pell_13.bin at offset 0x100000 into W25Q128JVSQ")
    print(f"  Total data table footprint: {len(pell_bin) + len(prime_bin)} bytes"
          f" of 16,777,216 available")

if __name__ == '__main__':
    main()
