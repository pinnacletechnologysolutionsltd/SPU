#!/usr/bin/env python3
# generate_pmod_rom.py
# Converts RPLU default parameters from the C codebase into a raw binary
# .bin file formatted for the autonomous PMOD Hardware Bootloader.
#
# Payload sequence format (11 bytes per payload):
#   Byte 0:    {4'b0, sel[2:0], material[0]}
#   Byte 1:    {6'b0, addr[9:8]}
#   Byte 2:    {addr[7:0]}
#   Byte 3-10: {data[63:0]} (Big Endian)

import struct
import sys

# Constants
Q32 = 1 << 32

def to_q32(x):
    """Convert float to Q32.32 fixed-point integer representing 64-bits"""
    if x < 0:
        return (1 << 64) - int(-x * Q32)
    return int(x * Q32)

def pack_payload(sel, material, addr, data64):
    """Packs fields into an 11-byte buffer."""
    buf = bytearray(11)
    buf[0] = ((sel & 0x7) << 1) | (material & 0x1)
    buf[1] = (addr >> 8) & 0x3
    buf[2] = addr & 0xFF
    struct.pack_into(">Q", buf, 3, data64 & 0xFFFFFFFFFFFFFFFF)
    return buf

def main():
    payloads = []
    
    # ---------------------------------------------------------
    # 1. Transcendental Math Constants (sel=0, material=0)
    # Essential fixed-point irrational baselines for physics scaling.
    # ---------------------------------------------------------
    math_bases = [
        to_q32(3.141592653589793),  # Pi
        to_q32(6.283185307179586),  # Tau (2*Pi)
        to_q32(2.718281828459045),  # Euler's (e)
        to_q32(1.414213562373095),  # Sqrt(2)
        to_q32(1.732050807568877),  # Sqrt(3)
        to_q32(2.236067977499790),  # Sqrt(5)
        to_q32(1.618033988749895),  # Golden Ratio (Phi)
        to_q32(0.618033988749895),  # Golden Conjugate (1/Phi)
    ]
    for i, data in enumerate(math_bases):
        payloads.append(pack_payload(sel=0, material=0, addr=i, data64=data))

    # ---------------------------------------------------------
    # 2. Physics & Resonance Constants (sel=0, material=1)
    # ---------------------------------------------------------
    physics_bases = [
        to_q32(2.99792458),         # Speed of Light (scaled C)
        to_q32(0.00729735),         # Fine Structure Constant (Alpha)
        to_q32(6.67430),            # Gravitational Constant (scaled G)
        to_q32(0.02585),            # Room Temp Thermal Energy (kT in eV/scaled)
    ]
    for i, data in enumerate(physics_bases):
        payloads.append(pack_payload(sel=0, material=1, addr=i, data64=data))

    # ---------------------------------------------------------
    # 3. Essential Periodic Table (sel=1, material=1)
    # Encoded: (AtomicMass * density_ratio) as Q32
    # Gives the core specific "heft" or inertia points to anchor physics limits.
    # ---------------------------------------------------------
    elements = [
        to_q32(1.008 * 0.089),   # Hydrogen (H)  - Vaporous, extremely light
        to_q32(12.011 * 2.260),  # Carbon (C)    - Structural, baseline
        to_q32(14.007 * 1.250),  # Nitrogen (N)  - Ambient damping
        to_q32(15.999 * 1.429),  # Oxygen (O)    - Activating agent
        to_q32(28.085 * 2.329),  # Silicon (Si)  - Crystalline resonance
        to_q32(55.845 * 7.874),  # Iron (Fe)     - Heavy magnetic inertia
        to_q32(196.97 * 19.30),  # Gold (Au)     - Ultra-heavy noble damping
    ]
    for i, data in enumerate(elements):
        payloads.append(pack_payload(sel=1, material=1, addr=i, data64=data))

    # ---------------------------------------------------------
    # 4. Thomson Problem Vector Bases (sel=2, addr 0..12) 
    # 13 ideal spatial coordinates on a sphere.
    # (Simplified evenly distributed spherical coordinates)
    # ---------------------------------------------------------
    # In practice, SAS expects 13 vectors. Using structured Q32 representations:
    for i in range(13):
        # We store placeholder geometric vectors. 
        # (A real optimization curve would seed the true asymmetric 13-sphere layout)
        magic_val = to_q32((i + 1) * 0.076923) # distributing 1/13th segments
        payloads.append(pack_payload(sel=2, material=0, addr=i, data64=magic_val))

    # ---------------------------------------------------------
    # 5. Pade Evaluator Bootstraps (Already Required for RPLU)
    # ---------------------------------------------------------
    PADE_NUM = [
        0x0000000100000000, 0xffffffff80000000, 0x000000001b6db6db,
        0xfffffffffcf3cf3d, 0x0000000000270270
    ]
    for i, data in enumerate(PADE_NUM):
        payloads.append(pack_payload(sel=3, material=0, addr=i, data64=data))

    PADE_DEN = [
        0x0000000100000000, 0x0000000080000000, 0x000000001b6db6db,
        0x00000000030c30c3, 0x0000000000270270
    ]
    for i, data in enumerate(PADE_DEN):
        payloads.append(pack_payload(sel=4, material=0, addr=i, data64=data))

    # Output to stdout or file
    filename = "pmod_bootrom.bin"
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    with open(filename, "wb") as f:
        for p in payloads:
            f.write(p)

    print(f"Generated {filename}: {len(payloads)} payloads ({len(payloads) * 11} bytes).")
    print("Burn to PMOD Flash with: openFPGALoader --external-flash pmod_bootrom.bin")

if __name__ == "__main__":
    main()
