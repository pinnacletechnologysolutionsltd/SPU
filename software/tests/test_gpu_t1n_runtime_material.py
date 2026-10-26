#!/usr/bin/env python3
"""Independent T1n runtime material-opcode oracle and state-transition audit."""

from __future__ import annotations

import subprocess
import tempfile
import argparse
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, TB, decode, load_scene, oracle


def compile_run(opcodes: tuple[int, int, int], production: bool = False) -> tuple[int, str]:
    fixtures = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    tb_text = TB
    for key, scene in zip(("SCENE_A", "SCENE_B", "SCENE_C"), fixtures):
        tb_text = tb_text.replace(f"@@{key}@@", scene[0])
    params = [
        "-P", "t1i_uv_tb.T1N=1",
        "-P", f"t1i_uv_tb.T1N_OP_A=8'h{opcodes[0]:02x}",
        "-P", f"t1i_uv_tb.T1N_OP_B=8'h{opcodes[1]:02x}",
        "-P", f"t1i_uv_tb.T1N_OP_C=8'h{opcodes[2]:02x}",
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
    with tempfile.TemporaryDirectory(prefix="spu_t1n_runtime_material_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1n_runtime_material_tb.v"
        out = temp / "t1n_runtime_material_tb.vvp"
        tb.write_text(tb_text)
        compiled = subprocess.run(
            ["iverilog", "-g2012", "-s", "t1i_uv_tb", *params, "-o", str(out),
             str(tb), *[str(ROOT / p) for p in RTL_FILES]],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if compiled.returncode:
            return 1, compiled.stderr
        simulated = subprocess.run(
            ["vvp", str(out)], cwd=ROOT, text=True, capture_output=True,
            check=False, timeout=1500 if production else 60,
        )
    return simulated.returncode, simulated.stdout + simulated.stderr


def material_result(op: int, u: int, v: int) -> bool:
    pu, pv = bool((u >> 12) & 1), bool((v >> 12) & 1)
    if op == 0:
        return pu
    if op == 1:
        return pv
    if op == 2:
        return pu ^ pv
    if op == 3:
        return pu and pv
    if op == 4:
        return pu or pv
    if op == 5:
        return not pu
    raise ValueError(op)


def check_oracle(opcodes: tuple[int, int, int], output: str,
                 production: bool = False) -> int:
    fixtures = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    decoded = [decode(scene[1]) for scene in fixtures]
    width, height = (640, 480) if production else (80, 100)
    expected_per_frame = width * height
    expected_pixels = 4 * expected_per_frame
    frame_counts = [0] * 4
    lane_seen = [[False] * 4 for _ in range(4)]
    first_a: dict[tuple[int, int], tuple[int, int, int]] = {}
    changed_b = changed_c = return_mismatches = errors = 0
    ops_by_frame = (opcodes[0], opcodes[1], opcodes[2], opcodes[0])

    for line in output.splitlines():
        if not line.startswith("T1NPIX "):
            continue
        (sid, x, y, got_valid, got_lane, got_r, got_g, got_b,
         got_op, got_generation) = map(int, line.split()[1:])
        scene_index = 0 if sid in (0, 3) else sid
        expected_op = ops_by_frame[sid]
        valid, lane, u, v = oracle(decoded[scene_index], x, y)
        result = material_result(expected_op, u, v)
        rgb = ((15, 15, 0) if result else (0, 0, 15)) if valid else (0, 0, 0)
        expected_generation = 1 if sid in (0, 2) else 0
        if (got_valid, got_lane, (got_r, got_g, got_b), got_op, got_generation) != (
            valid, lane, rgb, expected_op, expected_generation
        ):
            errors += 1
            if errors <= 10:
                print(f"MISMATCH frame={sid} xy=({x},{y}) op={expected_op} "
                      f"expected={(valid, lane, rgb, expected_op, expected_generation)} "
                      f"got={(got_valid, got_lane, (got_r, got_g, got_b), got_op, got_generation)}")
        frame_counts[sid] += 1
        if valid:
            lane_seen[sid][lane] = True
        if sid == 0:
            first_a[(x, y)] = rgb
        elif sid == 1:
            changed_b += rgb != first_a.get((x, y))
        elif sid == 2:
            changed_c += rgb != first_a.get((x, y))
        elif rgb != first_a.get((x, y)):
            return_mismatches += 1

    if frame_counts != [expected_per_frame] * 4:
        errors += 1
        print(f"FAIL: expected {expected_per_frame:,} pixels per scene, received {frame_counts}")
    if any(not all(lanes) for lanes in lane_seen):
        errors += 1
        print(f"FAIL: not all lanes won in each scene: {lane_seen}")
    if not changed_b or not changed_c or return_mismatches:
        errors += 1
        print(f"FAIL: scene distinction/return opcodes={opcodes} B={changed_b} C={changed_c} "
              f"return mismatches={return_mismatches}")
    if "PASS: T1n invalid opcode rejected without bank/generation advance" not in output:
        errors += 1
        print("FAIL: invalid-opcode rejection/recovery assertion missing")
    if "PASS: T1n runtime opcode A/B/C/A" not in output:
        errors += 1
        print("FAIL: T1n transition pass marker missing")
    if f"PASS: T1i A/B/C/A full-frame U/V activation pixels={expected_pixels}" not in output:
        errors += 1
        print("FAIL: full reduced frame marker missing")
    return errors


def check_illegal_profiles() -> int:
    cases = [
        ({"FOUR_PRIMITIVE_SCENE": 0}, "T1N_requires_registered_prepared_t1i_without_static_material_or_diagnostics"),
        ({"T1L_PIPELINE_PARTITION": 0}, "T1N_requires_registered_prepared_t1i_without_static_material_or_diagnostics"),
        ({"GPU_POST_WINNER_REG": 0}, "T1N_requires_registered_prepared_t1i_without_static_material_or_diagnostics"),
        ({"T1M_FRAGMENT_ALU": 1}, "T1N_requires_registered_prepared_t1i_without_static_material_or_diagnostics"),
        ({"T1N_RUNTIME_MATERIAL": 2}, "T1N_runtime_material_enable_must_be_0_or_1"),
    ]
    errors = 0
    for overrides, guard in cases:
        params = {
            "DEVICE": '"A7"', "ENABLE_HDMI": 0, "PREPARED_SCENE": 1,
            "FOUR_PRIMITIVE_SCENE": 1, "T1I_UV_SCENE": 1,
            "T1L_PIPELINE_PARTITION": 1, "T1N_RUNTIME_MATERIAL": 1,
            "GPU_POST_WINNER_REG": 1,
        }
        params.update(overrides)
        param_text = ",".join(f".{key}({value})" for key, value in params.items())
        tb = f"module invalid_t1n_profile_tb; spu_gpu_top #({param_text}) dut(); endmodule\n"
        with tempfile.TemporaryDirectory(prefix="spu_t1n_bad_profile_") as temp_dir:
            temp = Path(temp_dir)
            tb_path, out = temp / "invalid_profile.v", temp / "invalid_profile.vvp"
            tb_path.write_text(tb)
            compiled = subprocess.run(
                ["iverilog", "-g2012", "-s", "invalid_t1n_profile_tb", "-o", str(out),
                 str(tb_path), *[str(ROOT / p) for p in RTL_FILES]],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        if compiled.returncode == 0 or guard not in compiled.stderr:
            errors += 1
            print(f"FAIL: illegal T1n profile not rejected by {guard}: {overrides}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true",
                        help="run frozen A/B/C/A at 640x480 and check every pixel")
    args = parser.parse_args()
    errors = 0
    # Q0's frozen scene assignment: A=PASS_U, B=PASS_V, C=XOR.
    result, output = compile_run((0, 1, 2), args.production)
    if result:
        print(output[-5000:])
        return 1
    errors += check_oracle((0, 1, 2), output, args.production)

    if args.production:
        if errors:
            print(f"FAIL: T1n production runtime material oracle errors={errors}")
            return 1
        print("PASS: T1n independent production 640x480 A/B/C/A oracle "
              "(1,228,800 pixels)")
        return 0

    # Exercise all remaining legal runtime values without changing fixture data.
    for op in range(6):
        result, output = compile_run((op, op, op))
        if result:
            print(output[-5000:])
            return 1
        errors += check_oracle((op, op, op), output)
    errors += check_illegal_profiles()
    if errors:
        print(f"FAIL: T1n runtime material oracle errors={errors}")
        return 1
    print("PASS: T1n reduced independent oracle; six runtime opcodes, A/B/C/A "
          "generation alignment, invalid rejection, and recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
