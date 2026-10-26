#!/usr/bin/env python3
"""Independent reduced oracle for T1p winner-selected predicate bits."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, TB, decode, load_scene, oracle
from test_gpu_t1o_per_primitive_material import RUNS as T1O_RUNS, pack_ops


XOR = (2, 2, 2, 2)
FROZEN = (
    (0xCC, 0xCC, 0xCC, 0xCC),
    (0x89, 0x8E, 0xAA, 0xD9),
    (0xBD, 0xD8, 0x8E, 0xF8),
)
ENDPOINTS = (
    (0x00, 0xFF, 0x00, 0xFF),
    (0xFF, 0x00, 0xFF, 0x00),
    (0x0F, 0xF0, 0x0F, 0xF0),
)
CASES = (
    ((XOR, XOR, XOR), FROZEN),
    (T1O_RUNS[0], ENDPOINTS),
    (T1O_RUNS[1], FROZEN),
)


def result(op: int, selector: int, u: int, v: int) -> bool:
    pu = bool((u >> (selector & 15)) & 1)
    pv = bool((v >> (selector >> 4)) & 1)
    return (pu, pv, pu ^ pv, pu and pv, pu or pv, not pu)[op]


def packed(values: tuple[int, int, int, int]) -> int:
    return sum(value << (8 * lane) for lane, value in enumerate(values))


def check_layout(scene: int) -> None:
    payload = scene.to_bytes(174, "little") + bytes(XOR) + bytes(FROZEN[0])
    wire = b"\xA5" + payload
    assert len(payload) == 182 and len(wire) == 183
    assert wire[175:179] == bytes(XOR)
    assert wire[179:183] == bytes(FROZEN[0])


def check_discriminator(lanes) -> None:
    won = [[] for _ in range(4)]
    for y in range(480):
        for x in range(640):
            valid, lane, u, v = oracle(lanes, x, y)
            if valid:
                won[lane].append((u, v))
    expected_winners = (773, 742, 488, 438)
    expected_distances = ((383, 386, 425), (392, 373, 383),
                          (271, 259, 246), (223, 243, 224))
    for lane, pixels in enumerate(won):
        assert len(pixels) == expected_winners[lane]
        a, b, c = (scene[lane] for scene in FROZEN)
        distances = tuple(sum(result(2, x, u, v) != result(2, z, u, v)
                              for u, v in pixels) for x, z in ((a, b), (b, c), (c, a)))
        assert distances == expected_distances[lane], (lane, distances)
        for selector in (b, c):
            u_only = (a & 0xF0) | (selector & 0x0F)
            v_only = (selector & 0xF0) | (a & 0x0F)
            assert any(result(2, a, u, v) != result(2, u_only, u, v)
                       for u, v in pixels)
            assert any(result(2, a, u, v) != result(2, v_only, u, v)
                       for u, v in pixels)


def simulate(op_sets, selector_sets, production: bool = False) -> str:
    scene_hex, _ = load_scene("gpu_t1i_scene_a_wire_175b.hex")
    tb = TB
    for name in ("SCENE_A", "SCENE_B", "SCENE_C"):
        tb = tb.replace(f"@@{name}@@", scene_hex)
    params = ["-P", "t1i_uv_tb.T1P=1", "-P", "t1i_uv_tb.T1L_PIPE=1",
              "-P", "t1i_uv_tb.OUT_REG=1"]
    for name, ops, selectors in zip("ABC", op_sets, selector_sets):
        params += ["-P", f"t1i_uv_tb.T1P_OPS_{name}=32'h{pack_ops(ops):08x}",
                   "-P", f"t1i_uv_tb.T1P_SEL_{name}=32'h{packed(selectors):08x}"]
    if production:
        params += [
            "-P", "t1i_uv_tb.H_ACTIVE=640", "-P", "t1i_uv_tb.H_FP=16",
            "-P", "t1i_uv_tb.H_SYNC=96", "-P", "t1i_uv_tb.H_BP=48",
            "-P", "t1i_uv_tb.V_ACTIVE=480", "-P", "t1i_uv_tb.V_FP=10",
            "-P", "t1i_uv_tb.V_SYNC=2", "-P", "t1i_uv_tb.V_BP=33",
            "-P", "t1i_uv_tb.CHECK_W=640", "-P", "t1i_uv_tb.CHECK_H=480",
        ]
    with tempfile.TemporaryDirectory(prefix="spu_t1p_predicate_") as directory:
        root = Path(directory)
        source, executable = root / "tb.v", root / "tb.vvp"
        source.write_text(tb)
        built = subprocess.run(
            ["iverilog", "-g2012", "-s", "t1i_uv_tb", *params,
             "-o", str(executable), str(source), *[str(ROOT / p) for p in RTL_FILES]],
            cwd=ROOT, capture_output=True, text=True, check=False)
        if built.returncode:
            raise AssertionError(built.stdout + built.stderr)
        run = subprocess.run(["vvp", str(executable)], cwd=ROOT,
                             capture_output=True, text=True, check=False,
                             timeout=1500 if production else 180)
        if run.returncode:
            raise AssertionError(run.stdout[-8000:] + run.stderr[-2000:])
        return run.stdout


def check_output(output: str, lanes, op_sets, selector_sets,
                 production: bool = False) -> list[set[int]]:
    ops_by_frame = (*op_sets, op_sets[0])
    selectors_by_frame = (*selector_sets, selector_sets[0])
    counts = [0] * 4
    winner_seen = [set() for _ in range(4)]
    opcode_seen = [set() for _ in range(4)]
    selector_seen = [set() for _ in range(4)]
    first = {}
    changed = [0, 0, 0]
    for line in output.splitlines():
        if not line.startswith("T1PPIX "):
            continue
        sid, x, y, got_valid, got_lane, r, g, b, got_op, got_selector, \
            got_generation, hsync, vsync, active = map(int, line.split()[1:])
        valid, lane, u, v = oracle(lanes, x, y)
        op = ops_by_frame[sid][lane]
        selector = selectors_by_frame[sid][lane]
        rgb = ((15, 15, 0) if result(op, selector, u, v) else (0, 0, 15)) \
            if valid else (0, 0, 0)
        expected = (valid, lane, *rgb, op, selector,
                    1 if sid in (0, 2) else 0, 1, 1, 1)
        got = (got_valid, got_lane, r, g, b, got_op, got_selector,
               got_generation, hsync, vsync, active)
        assert got == expected, (sid, x, y, expected, got)
        counts[sid] += 1
        if valid:
            winner_seen[sid].add(lane)
            opcode_seen[lane].add(op)
            selector_seen[lane].add(selector)
        if sid == 0:
            first[(x, y)] = rgb
        else:
            changed[sid - 1] += rgb != first[(x, y)]
    pixels_per_frame = 640 * 480 if production else 80 * 100
    assert counts == [pixels_per_frame] * 4, counts
    assert all(seen == {0, 1, 2, 3} for seen in winner_seen), winner_seen
    assert changed[0] and changed[1] and changed[2] == 0, changed
    for lane in range(4):
        assert f"PASS: T1p invalid opcode lane {lane} rejected" in output
    assert "PASS: T1p per-primitive predicates A/B/C/A" in output
    if production:
        assert (f"PASS: T1i A/B/C/A full-frame U/V activation "
                f"pixels={4 * pixels_per_frame}") in output
    assert "FAIL:" not in output
    return opcode_seen, selector_seen


def check_illegal_profiles() -> None:
    cases = (
        ({"FOUR_PRIMITIVE_SCENE": 0}, "T1P_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"T1L_PIPELINE_PARTITION": 0}, "T1P_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"GPU_POST_WINNER_REG": 0}, "T1P_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"T1O_PER_PRIMITIVE_MATERIAL": 1}, "T1P_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"T1N_RUNTIME_MATERIAL": 1}, "T1P_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"T1P_PER_PRIMITIVE_PREDICATES": 2}, "T1P_per_primitive_predicates_enable_must_be_0_or_1"),
    )
    for overrides, guard in cases:
        params = {"DEVICE": '"A7"', "ENABLE_HDMI": 0,
                  "PREPARED_SCENE": 1, "FOUR_PRIMITIVE_SCENE": 1,
                  "T1I_UV_SCENE": 1, "T1L_PIPELINE_PARTITION": 1,
                  "GPU_POST_WINNER_REG": 1,
                  "T1P_PER_PRIMITIVE_PREDICATES": 1}
        params.update(overrides)
        names = ",".join(f".{name}({value})" for name, value in params.items())
        tb = f"module bad_t1p; spu_gpu_top #({names}) dut(); endmodule\n"
        with tempfile.TemporaryDirectory(prefix="spu_bad_t1p_") as directory:
            root = Path(directory)
            source, executable = root / "tb.v", root / "tb.vvp"
            source.write_text(tb)
            built = subprocess.run(
                ["iverilog", "-g2012", "-s", "bad_t1p", "-o", str(executable),
                 str(source), *[str(ROOT / p) for p in RTL_FILES]],
                cwd=ROOT, capture_output=True, text=True, check=False)
        assert built.returncode and guard in built.stderr, (overrides, built.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true",
                        help="run frozen 640x480 XOR selector A/B/C/A oracle")
    args = parser.parse_args()
    _, scene = load_scene("gpu_t1i_scene_a_wire_175b.hex")
    lanes = decode(scene)
    check_layout(scene)
    check_discriminator(lanes)
    all_ops = [set() for _ in range(4)]
    all_selectors = [set() for _ in range(4)]
    for op_sets, selector_sets in CASES[:1] if args.production else CASES:
        seen_ops, seen_selectors = check_output(
            simulate(op_sets, selector_sets, args.production), lanes,
            op_sets, selector_sets, args.production)
        for lane in range(4):
            all_ops[lane].update(seen_ops[lane])
            all_selectors[lane].update(seen_selectors[lane])
    if args.production:
        assert all(seen == {2} for seen in all_ops), all_ops
        assert all(seen == {scene[lane] for scene in FROZEN}
                   for lane, seen in enumerate(all_selectors)), all_selectors
        print("PASS: T1p independent production 640x480 A/B/C/A selector "
              "oracle (1,228,800 pixels; XOR; exact return A)")
        return 0
    assert all(seen == set(range(6)) for seen in all_ops), all_ops
    assert all({0x00, 0xFF}.issubset(seen) for seen in all_selectors), all_selectors
    check_illegal_profiles()
    print("PASS: T1p reduced independent oracle; 96,000 pixels, four winner lanes, "
          "all opcodes and endpoint selectors per lane, atomic A/B/C/A, "
          "invalid-opcode recovery, exact return A")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
