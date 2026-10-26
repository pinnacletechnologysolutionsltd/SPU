#!/usr/bin/env python3
"""Independent T1o per-primitive runtime material oracle."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, TB, decode, load_scene, oracle


PRIMARY = (5, 4, 3, 2)
RUNS = (
    (PRIMARY, (0, 5, 4, 3), (1, 0, 5, 4)),
    ((2, 1, 0, 0), (3, 2, 1, 1), (4, 3, 2, 5)),
)


def pack_ops(ops: tuple[int, int, int, int]) -> int:
    return sum(op << (8 * lane) for lane, op in enumerate(ops))


def material_result(op: int, u: int, v: int) -> bool:
    pred_u, pred_v = bool((u >> 12) & 1), bool((v >> 12) & 1)
    operations = (
        pred_u,
        pred_v,
        pred_u ^ pred_v,
        pred_u and pred_v,
        pred_u or pred_v,
        not pred_u,
    )
    if not 0 <= op < len(operations):
        raise ValueError(op)
    return operations[op]


def verify_packet_layout(scene: int) -> int:
    payload = scene.to_bytes(174, "little") + bytes(PRIMARY)
    wire = bytes((0xA5,)) + payload
    if len(payload) != 178 or len(wire) != 179 or wire[175:179] != bytes(PRIMARY):
        print(f"FAIL: T1o packet layout length/tail mismatch "
              f"payload={len(payload)} wire={len(wire)} tail={wire[175:179].hex()}")
        return 1
    print("PASS: T1o packet layout payload=178 wire=179 tail=05/04/03/02")
    return 0


def verify_primary_fixture(decoded) -> int:
    pixels = [[oracle(decoded, x, y) for x in range(640)] for y in range(480)]
    counts = [0, 0, 0, 0]
    for row in pixels:
        for valid, lane, _u, _v in row:
            if valid:
                counts[lane] += 1
    boundaries = sum(
        pixels[y][x][0] and pixels[y][x - 1][0] and
        pixels[y][x][1] != pixels[y][x - 1][1]
        for y in range(480) for x in range(1, 640)
    ) + sum(
        pixels[y][x][0] and pixels[y - 1][x][0] and
        pixels[y][x][1] != pixels[y - 1][x][1]
        for y in range(1, 480) for x in range(640)
    )
    distinctions = []
    for lane, assigned in enumerate(PRIMARY):
        for other in PRIMARY:
            if other == assigned:
                continue
            distinctions.append(sum(
                valid and winner == lane and
                material_result(assigned, u, v) != material_result(other, u, v)
                for row in pixels for valid, winner, u, v in row
            ))
    if counts != [773, 742, 488, 438] or boundaries != 115 or min(distinctions) != 38:
        print(f"FAIL: frozen A discriminator changed counts={counts} "
              f"boundaries={boundaries} minimum-distinction={min(distinctions)}")
        return 1
    print("PASS: frozen A discriminator winner-counts=773/742/488/438 "
          "boundaries=115 minimum-distinction=38")
    return 0


def compile_run(op_sets: tuple[tuple[int, int, int, int], ...],
                production: bool = False) -> tuple[int, str]:
    scene_hex, _scene = load_scene("gpu_t1i_scene_a_wire_175b.hex")
    tb_text = TB
    for name in ("SCENE_A", "SCENE_B", "SCENE_C"):
        tb_text = tb_text.replace(f"@@{name}@@", scene_hex)
    params = [
        "-P", "t1i_uv_tb.T1O=1",
        "-P", f"t1i_uv_tb.T1O_OPS_A=32'h{pack_ops(op_sets[0]):08x}",
        "-P", f"t1i_uv_tb.T1O_OPS_B=32'h{pack_ops(op_sets[1]):08x}",
        "-P", f"t1i_uv_tb.T1O_OPS_C=32'h{pack_ops(op_sets[2]):08x}",
        "-P", "t1i_uv_tb.T1L_PIPE=1",
        "-P", "t1i_uv_tb.OUT_REG=1",
    ]
    if production:
        params += [
            "-P", "t1i_uv_tb.H_ACTIVE=640", "-P", "t1i_uv_tb.H_FP=16",
            "-P", "t1i_uv_tb.H_SYNC=96", "-P", "t1i_uv_tb.H_BP=48",
            "-P", "t1i_uv_tb.V_ACTIVE=480", "-P", "t1i_uv_tb.V_FP=10",
            "-P", "t1i_uv_tb.V_SYNC=2", "-P", "t1i_uv_tb.V_BP=33",
            "-P", "t1i_uv_tb.CHECK_W=640", "-P", "t1i_uv_tb.CHECK_H=480",
        ]
    with tempfile.TemporaryDirectory(prefix="spu_t1o_material_") as temp_dir:
        temp = Path(temp_dir)
        tb_path, out = temp / "t1o_tb.v", temp / "t1o_tb.vvp"
        tb_path.write_text(tb_text)
        compiled = subprocess.run(
            ["iverilog", "-g2012", "-s", "t1i_uv_tb", *params,
             "-o", str(out), str(tb_path), *[str(ROOT / p) for p in RTL_FILES]],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if compiled.returncode:
            return compiled.returncode, compiled.stdout + compiled.stderr
        simulated = subprocess.run(
            ["vvp", str(out)], cwd=ROOT, text=True, capture_output=True,
            check=False, timeout=1500 if production else 180,
        )
    return simulated.returncode, simulated.stdout + simulated.stderr


def check_run(decoded, op_sets, output: str,
              production: bool = False) -> tuple[int, list[set[int]]]:
    errors = 0
    seen = [set() for _ in range(4)]
    frame_counts = [0, 0, 0, 0]
    lane_seen = [[False] * 4 for _ in range(4)]
    first_a: dict[tuple[int, int], tuple[int, int, int]] = {}
    changed_b = changed_c = return_mismatches = 0
    by_frame = (op_sets[0], op_sets[1], op_sets[2], op_sets[0])
    for line in output.splitlines():
        if not line.startswith("T1OPIX "):
            continue
        values = tuple(map(int, line.split()[1:]))
        (sid, x, y, got_valid, got_lane, got_r, got_g, got_b, got_op,
         got_generation, got_hsync, got_vsync, got_active) = values
        valid, lane, u, v = oracle(decoded, x, y)
        expected_op = by_frame[sid][lane]
        result = material_result(expected_op, u, v)
        rgb = ((15, 15, 0) if result else (0, 0, 15)) if valid else (0, 0, 0)
        generation = 1 if sid in (0, 2) else 0
        expected = (valid, lane, rgb, expected_op, generation, 1, 1, 1)
        got = (got_valid, got_lane, (got_r, got_g, got_b), got_op,
               got_generation, got_hsync, got_vsync, got_active)
        if got != expected:
            errors += 1
            if errors <= 10:
                print(f"MISMATCH frame={sid} xy=({x},{y}) expected={expected} got={got}")
        frame_counts[sid] += 1
        if valid:
            lane_seen[sid][lane] = True
            seen[lane].add(expected_op)
        if sid == 0:
            first_a[(x, y)] = rgb
        elif sid == 1:
            changed_b += rgb != first_a[(x, y)]
        elif sid == 2:
            changed_c += rgb != first_a[(x, y)]
        elif rgb != first_a[(x, y)]:
            return_mismatches += 1
    width, height = (640, 480) if production else (80, 100)
    pixels_per_frame = width * height
    total_pixels = 4 * pixels_per_frame
    if frame_counts != [pixels_per_frame] * 4:
        errors += 1
        print(f"FAIL: expected {pixels_per_frame:,} pixels per frame, "
              f"received {frame_counts}")
    if any(not all(frame) for frame in lane_seen):
        errors += 1
        print(f"FAIL: every primitive did not win in every frame: {lane_seen}")
    if not changed_b or not changed_c or return_mismatches:
        errors += 1
        print(f"FAIL: tuple transition/return B={changed_b} C={changed_c} "
              f"return={return_mismatches}")
    for lane in range(4):
        marker = f"PASS: T1o invalid opcode lane {lane} rejected"
        if marker not in output:
            errors += 1
            print(f"FAIL: missing invalid-tail rejection marker for lane {lane}")
    required = (
        "PASS: T1o per-primitive runtime A/B/C/A",
        f"PASS: T1i A/B/C/A full-frame U/V activation pixels={total_pixels}",
    )
    for marker in required:
        if marker not in output:
            errors += 1
            print(f"FAIL: missing simulation marker: {marker}")
    if "FAIL:" in output:
        errors += 1
        print("FAIL: RTL testbench emitted a failure marker")
    return errors, seen


def check_illegal_profiles() -> int:
    cases = [
        ({"FOUR_PRIMITIVE_SCENE": 0}, "T1O_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"T1L_PIPELINE_PARTITION": 0}, "T1O_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"GPU_POST_WINNER_REG": 0}, "T1O_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"T1N_RUNTIME_MATERIAL": 1}, "T1O_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"T1M_FRAGMENT_ALU": 1}, "T1O_requires_registered_prepared_t1i_without_other_material_modes"),
        ({"T1O_PER_PRIMITIVE_MATERIAL": 2}, "T1O_per_primitive_material_enable_must_be_0_or_1"),
    ]
    errors = 0
    for overrides, guard in cases:
        params = {
            "DEVICE": '"A7"', "ENABLE_HDMI": 0, "PREPARED_SCENE": 1,
            "FOUR_PRIMITIVE_SCENE": 1, "T1I_UV_SCENE": 1,
            "T1L_PIPELINE_PARTITION": 1, "T1O_PER_PRIMITIVE_MATERIAL": 1,
            "GPU_POST_WINNER_REG": 1,
        }
        params.update(overrides)
        text = ",".join(f".{key}({value})" for key, value in params.items())
        tb = f"module invalid_t1o_profile_tb; spu_gpu_top #({text}) dut(); endmodule\n"
        with tempfile.TemporaryDirectory(prefix="spu_t1o_bad_profile_") as temp_dir:
            temp = Path(temp_dir)
            tb_path, out = temp / "invalid.v", temp / "invalid.vvp"
            tb_path.write_text(tb)
            result = subprocess.run(
                ["iverilog", "-g2012", "-s", "invalid_t1o_profile_tb",
                 "-o", str(out), str(tb_path), *[str(ROOT / p) for p in RTL_FILES]],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        if result.returncode == 0 or guard not in result.stderr:
            errors += 1
            print(f"FAIL: illegal T1o profile not rejected by {guard}: {overrides}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true",
                        help="run the frozen 640x480 A/B/C/A opcode-tuple oracle")
    args = parser.parse_args()
    _scene_hex, scene = load_scene("gpu_t1i_scene_a_wire_175b.hex")
    decoded = decode(scene)
    errors = verify_packet_layout(scene) + verify_primary_fixture(decoded)
    all_seen = [set() for _ in range(4)]
    selected_runs = RUNS[:1] if args.production else RUNS
    for op_sets in selected_runs:
        result, output = compile_run(op_sets, args.production)
        if result:
            print(output[-8000:])
            return 1
        run_errors, seen = check_run(decoded, op_sets, output, args.production)
        errors += run_errors
        for lane in range(4):
            all_seen[lane].update(seen[lane])
    if args.production:
        if errors:
            print(f"FAIL: T1o production oracle errors={errors}")
            return 1
        print("PASS: T1o independent production 640x480 A/B/C/A oracle "
              "(1,228,800 pixels; tuples 5432/0543/1054/5432)")
        return 0
    if any(values != set(range(6)) for values in all_seen):
        errors += 1
        print(f"FAIL: all legal opcodes were not exercised for every primitive: {all_seen}")
    errors += check_illegal_profiles()
    if errors:
        print(f"FAIL: T1o independent oracle errors={errors}")
        return 1
    print("PASS: T1o reduced independent oracle; winner-selected per-primitive "
          "operations, all six encodings per lane, atomic transitions, four-byte "
          "invalid rejection, and recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
