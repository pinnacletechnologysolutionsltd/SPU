#!/usr/bin/env python3
"""T1r palette-pair RTL checks and independent frozen-scene oracle."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, decode, load_scene, oracle

RTL = [*RTL_FILES, "hardware/rtl/gpu/spu_material_palette_select4.v"]
TB = ROOT / "hardware/tests/common/spu_gpu_t1r_palette_pair_tb.v"
PALETTES = (0x1C, 0x2A, 0x31, 0x07)


def verify_encoding() -> None:
    expected = (((0, 0, 1), (1, 1, 0)),
                ((0, 1, 0), (1, 0, 1)),
                ((1, 0, 0), (0, 1, 1)),
                ((1, 1, 1), (0, 0, 0)))
    for lane, byte in enumerate(PALETTES):
        false_rgb = tuple((byte >> bit) & 1 for bit in range(3))
        true_rgb = tuple((byte >> bit) & 1 for bit in range(3, 6))
        assert (false_rgb, true_rgb) == expected[lane], (lane, byte)
        assert byte & 0xC0 == 0
    for table in range(16):
        for pair in range(4):
            assert ((table >> pair) & 1) in (0, 1)


def verify_frozen_packet_and_coverage() -> None:
    _, scene = load_scene("gpu_t1i_scene_a_wire_175b.hex")
    wire = bytes((0xA5,)) + scene.to_bytes(174, "little") + bytes((0x06,) * 4)
    wire += bytes((0x00,) * 4) + bytes(PALETTES)
    assert len(wire) == 187 and wire[0] == 0xA5
    assert wire[175:179] == bytes((0x06,) * 4)
    assert wire[179:183] == bytes((0x00,) * 4)
    assert wire[183:187] == bytes(PALETTES)

    lanes = decode(scene)
    winner_counts = [0] * 4
    predicate_pairs = [set() for _ in range(4)]
    overlap_pixels = 0
    for y in range(480):
        for x in range(640):
            valid, lane, u, v = oracle(lanes, x, y)
            if valid:
                winner_counts[lane] += 1
                predicate_pairs[lane].add((((u & 1) << 1) | (v & 1)))
            coverage = sum(
                all(a * x + b * y + c >= 0 for a, b, c in tri_edges)
                for tri_edges, _uv, _u, _v, _depth in lanes
            )
            overlap_pixels += coverage > 1
    assert winner_counts == [773, 742, 488, 438], winner_counts
    assert predicate_pairs == [set(range(4))] * 4, predicate_pairs
    assert overlap_pixels > 0, overlap_pixels


def run_rtl() -> str:
    with tempfile.TemporaryDirectory(prefix="spu_t1r_palette_pair_") as directory:
        root = Path(directory)
        executable = root / "t1r.vvp"
        compiled = subprocess.run(
            ["iverilog", "-g2012", "-s", "spu_gpu_t1r_palette_pair_tb",
             "-o", str(executable), str(TB), *[str(ROOT / path) for path in RTL]],
            cwd=ROOT, capture_output=True, text=True, check=False)
        if compiled.returncode:
            raise AssertionError(compiled.stdout + compiled.stderr)
        result = subprocess.run(["vvp", str(executable)], cwd=ROOT,
                                capture_output=True, text=True, check=False,
                                timeout=240)
        if result.returncode or "PASS: T1r 186-byte loader windows" not in result.stdout:
            raise AssertionError(result.stdout[-8000:] + result.stderr[-2000:])
        if "FAIL:" in result.stdout:
            raise AssertionError(result.stdout[-8000:])
        return result.stdout


def verify_mutual_exclusion() -> None:
    source = '''module bad_t1r_profile;
    spu_gpu_top #(.DEVICE("A7"), .ENABLE_HDMI(0), .PREPARED_SCENE(1),
        .FOUR_PRIMITIVE_SCENE(1), .T1I_UV_SCENE(1),
        .T1L_PIPELINE_PARTITION(1), .GPU_POST_WINNER_REG(1),
        .T1Q_TRUTH_TABLE_MATERIAL(1), .T1R_PALETTE_PAIR_MATERIAL(1)) dut();
    endmodule
'''
    with tempfile.TemporaryDirectory(prefix="spu_bad_t1r_") as directory:
        root = Path(directory)
        tb, executable = root / "bad.v", root / "bad.vvp"
        tb.write_text(source)
        result = subprocess.run(
            ["iverilog", "-g2012", "-s", "bad_t1r_profile", "-o", str(executable),
             str(tb), *[str(ROOT / path) for path in RTL]],
            cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "T1R_requires_registered_prepared_t1i" in result.stderr, result.stderr


def main() -> int:
    verify_encoding()
    verify_frozen_packet_and_coverage()
    verify_mutual_exclusion()
    output = run_rtl()
    print(output, end="")
    print("PASS: T1r palette encoding, four-lane fixture coverage, packet layout, and profile exclusion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
