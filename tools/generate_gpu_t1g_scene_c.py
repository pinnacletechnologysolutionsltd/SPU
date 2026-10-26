#!/usr/bin/env python3
"""Generate T1g Scene C by translating the frozen T1f main scene by (8,8)."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures" / "gpu_t1f_scene_wire_127b.hex"
OUTPUT = ROOT / "fixtures" / "gpu_t1g_scene_c_wire_127b.hex"
SOURCE_SHA256 = "abf881178c4384f9210575aa2992c784cb6e19fcd10f149b81631e39591c8fda"
RECORD_BITS = 252
SCENE_BITS = 4 * RECORD_BITS


def signed(value: int, width: int) -> int:
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def encoded(value: int, width: int) -> int:
    return value & ((1 << width) - 1)


def main() -> int:
    source_bytes = SOURCE.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f"unexpected Scene A source SHA-256: {digest}")
    wire = bytes.fromhex(source_bytes.decode("ascii").strip())
    if len(wire) != 127 or wire[0] != 0xA5:
        raise SystemExit("Scene A must decode to 127 bytes beginning with A5")
    scene = int.from_bytes(wire[1:], "little")
    if scene.bit_length() > SCENE_BITS:
        raise SystemExit("Scene A payload exceeds four records")

    moved = scene
    for index in range(4):
        shift = index * RECORD_BITS
        record = (scene >> shift) & ((1 << RECORD_BITS) - 1)
        coeffs = []
        for edge in range(3):
            a_pos = edge * 64
            b_pos = a_pos + 16
            c_pos = a_pos + 32
            a = signed((record >> a_pos) & 0xFFFF, 16)
            b = signed((record >> b_pos) & 0xFFFF, 16)
            c = signed((record >> c_pos) & 0xFFFFFFFF, 32)
            translated_c = c - 8 * a - 8 * b
            coeffs.append((a_pos, b_pos, c_pos, a, b, translated_c))
        translated = record
        for a_pos, b_pos, c_pos, a, b, c in coeffs:
            translated &= ~(((1 << 32) - 1) << c_pos)
            translated |= encoded(c, 32) << c_pos
        moved &= ~(((1 << RECORD_BITS) - 1) << shift)
        moved |= translated << shift

    output_wire = b"\xA5" + moved.to_bytes(126, "little")
    OUTPUT.write_text(output_wire.hex() + "\n", encoding="ascii")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(output_wire)} wire bytes)")
    print(f"wire_sha256={hashlib.sha256(output_wire).hexdigest()}")
    print(f"hex_file_sha256={hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
