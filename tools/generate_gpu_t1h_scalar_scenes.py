#!/usr/bin/env python3
"""Generate T1h scalar-profile A/B/C wire fixtures from frozen T1g scenes."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_BITS = 252
T1H_RECORD_BITS = 300
SCENE_BITS = 4 * T1H_RECORD_BITS
SCENES = {
    "a": (
        "gpu_t1f_scene_wire_127b.hex",
        "abf881178c4384f9210575aa2992c784cb6e19fcd10f149b81631e39591c8fda",
        ((1000, 2000, 4000), (6000, 9000, 12000),
         (14000, 16000, 20000), (24000, 28000, 32000)),
    ),
    "b": (
        "gpu_t1f_coverage_scene_wire_127b.hex",
        "80bb103e43e1fc06a98e1d03166a673b35ea4e70c1c2b5fd34ff2caf177fb607",
        ((1500, 3000, 4500), (6500, 10000, 13500),
         (14500, 18000, 21500), (24500, 29000, 33500)),
    ),
    "c": (
        "gpu_t1g_scene_c_wire_127b.hex",
        "5aad8b1b1954875ea78fb11192d94a19652e027aea8f33e1656ec950b50abca5",
        ((2000, 4000, 6000), (7000, 11000, 15000),
         (15000, 19000, 23000), (25000, 30000, 35000)),
    ),
}


def main() -> int:
    for scene_id, (source_name, expected_sha, attributes) in SCENES.items():
        source = ROOT / "fixtures" / source_name
        source_text = source.read_bytes()
        actual_sha = hashlib.sha256(source_text).hexdigest()
        if actual_sha != expected_sha:
            raise SystemExit(f"{source_name} SHA mismatch: {actual_sha}")
        wire = bytes.fromhex(source_text.decode("ascii").strip())
        if len(wire) != 127 or wire[0] != 0xA5:
            raise SystemExit(f"{source_name} must be a 127-byte A5 transaction")

        old_scene = int.from_bytes(wire[1:], "little")
        new_scene = 0
        for primitive, values in enumerate(attributes):
            old_record = (old_scene >> (primitive * RECORD_BITS)) & ((1 << RECORD_BITS) - 1)
            if len(set(values)) != 3 or not all(0 <= value <= 0xFFFF for value in values):
                raise SystemExit(f"invalid frozen attributes in scene {scene_id}, primitive {primitive}")
            record = old_record
            for vertex, value in enumerate(values):
                record |= value << (RECORD_BITS + vertex * 16)
            new_scene |= record << (primitive * T1H_RECORD_BITS)

        payload = new_scene.to_bytes(SCENE_BITS // 8, "little")
        output_wire = b"\xA5" + payload
        output = ROOT / "fixtures" / f"gpu_t1h_scene_{scene_id}_wire_151b.hex"
        output.write_text(output_wire.hex() + "\n", encoding="ascii")
        print(f"wrote {output.relative_to(ROOT)} ({len(output_wire)} wire bytes)")
        print(f"wire_sha256={hashlib.sha256(output_wire).hexdigest()}")
        print(f"hex_file_sha256={hashlib.sha256(output.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
