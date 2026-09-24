#!/usr/bin/env python3
"""Generate T1i A/B/C coordinate fixtures from frozen T1g geometry."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_BITS = 252
T1I_RECORD_BITS = 348
SCENE_BITS = 4 * T1I_RECORD_BITS
SCENES = {
    "a": (
        "gpu_t1f_scene_wire_127b.hex",
        "abf881178c4384f9210575aa2992c784cb6e19fcd10f149b81631e39591c8fda",
        (
            ((0, 0), (8192, 1024), (1024, 8192)),
            ((12288, 4096), (20480, 5120), (13312, 12288)),
            ((24576, 12288), (32768, 13312), (25600, 20480)),
            ((36864, 20480), (45056, 21504), (37888, 28672)),
        ),
        (0, 0),
    ),
    "b": (
        "gpu_t1f_coverage_scene_wire_127b.hex",
        "80bb103e43e1fc06a98e1d03166a673b35ea4e70c1c2b5fd34ff2caf177fb607",
        None,
        (2048, 1024),
    ),
    "c": (
        "gpu_t1g_scene_c_wire_127b.hex",
        "5aad8b1b1954875ea78fb11192d94a19652e027aea8f33e1656ec950b50abca5",
        None,
        (1024, 4096),
    ),
}
BASE_UV = SCENES["a"][2]


def main() -> int:
    for scene_id, (source_name, expected_sha, explicit_uv, offset) in SCENES.items():
        source_text = (ROOT / "fixtures" / source_name).read_bytes()
        actual_sha = hashlib.sha256(source_text).hexdigest()
        if actual_sha != expected_sha:
            raise SystemExit(f"{source_name} SHA mismatch: {actual_sha}")
        wire = bytes.fromhex(source_text.decode("ascii").strip())
        if len(wire) != 127 or wire[0] != 0xA5:
            raise SystemExit(f"{source_name} must be a 127-byte A5 transaction")
        old_scene = int.from_bytes(wire[1:], "little")
        uv_table = explicit_uv if explicit_uv is not None else tuple(
            tuple((u + offset[0], v + offset[1]) for u, v in primitive)
            for primitive in BASE_UV
        )
        new_scene = 0
        for lane, vertices in enumerate(uv_table):
            old_record = (old_scene >> (lane * RECORD_BITS)) & ((1 << RECORD_BITS) - 1)
            record = old_record
            for vertex, (u, v) in enumerate(vertices):
                if not (0 <= u <= 0xFFFF and 0 <= v <= 0xFFFF):
                    raise SystemExit(f"coordinate out of range in scene {scene_id}, lane {lane}")
                record |= u << (252 + vertex * 32)
                record |= v << (268 + vertex * 32)
            new_scene |= record << (lane * T1I_RECORD_BITS)
        payload = new_scene.to_bytes(SCENE_BITS // 8, "little")
        output_wire = b"\xA5" + payload
        output = ROOT / "fixtures" / f"gpu_t1i_scene_{scene_id}_wire_175b.hex"
        output.write_text(output_wire.hex() + "\n", encoding="ascii")
        print(f"wrote {output.relative_to(ROOT)} ({len(output_wire)} wire bytes)")
        print(f"wire_sha256={hashlib.sha256(output_wire).hexdigest()}")
        print(f"hex_file_sha256={hashlib.sha256(output.read_bytes()).hexdigest()}")
        print(f"decoded_payload_sha256={hashlib.sha256(payload).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
