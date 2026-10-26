#!/usr/bin/env python3
"""Independent T1m Boolean material ALU oracle over frozen T1i scenes."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, TB, decode, load_scene, oracle


OPERATORS = {
    0: "PASS_U",
    1: "PASS_V",
    2: "XOR",
    3: "AND",
    4: "OR",
    5: "NOT_U",
}


def compile_and_run(operator: int, production: bool = False) -> tuple[int, str]:
    scenes = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    tb_text = TB
    for key, scene in zip(("SCENE_A", "SCENE_B", "SCENE_C"), scenes):
        tb_text = tb_text.replace(f"@@{key}@@", scene[0])
    params = [
        "-P", "t1i_uv_tb.T1M_ALU=1",
        "-P", f"t1i_uv_tb.T1M_OP={operator}",
        "-P", "t1i_uv_tb.T1L_PIPE=1",
        "-P", "t1i_uv_tb.OUT_REG=1",
    ]
    if production:
        params += [
            "-P", "t1i_uv_tb.H_ACTIVE=640", "-P", "t1i_uv_tb.H_FP=16",
            "-P", "t1i_uv_tb.H_SYNC=96", "-P", "t1i_uv_tb.H_BP=48",
            "-P", "t1i_uv_tb.V_ACTIVE=480", "-P", "t1i_uv_tb.V_FP=10",
            "-P", "t1i_uv_tb.V_SYNC=2", "-P", "t1i_uv_tb.V_BP=33",
            "-P", "t1i_uv_tb.CHECK_W=80", "-P", "t1i_uv_tb.CHECK_H=100",
        ]
    with tempfile.TemporaryDirectory(prefix=f"spu_t1m_op{operator}_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1m_fragment_alu_tb.v"
        out = temp / "t1m_fragment_alu_tb.vvp"
        tb.write_text(tb_text)
        compiled = subprocess.run(
            ["iverilog", "-g2012", "-s", "t1i_uv_tb", *params,
             "-o", str(out), str(tb), *[str(ROOT / p) for p in RTL_FILES]],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if compiled.returncode:
            return 1, compiled.stderr
        simulated = subprocess.run(
            ["vvp", str(out)], cwd=ROOT, text=True, capture_output=True,
            check=False,
        )
    return simulated.returncode, simulated.stdout + simulated.stderr


def material_result(operator: int, u: int, v: int) -> bool:
    pred_u = bool((u >> 12) & 1)
    pred_v = bool((v >> 12) & 1)
    if operator == 0:
        return pred_u
    if operator == 1:
        return pred_v
    if operator == 2:
        return pred_u ^ pred_v
    if operator == 3:
        return pred_u and pred_v
    if operator == 4:
        return pred_u or pred_v
    if operator == 5:
        return not pred_u
    raise ValueError(operator)


def check_oracle(operator: int, output: str, production: bool = False) -> int:
    fixtures = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    decoded = [decode(scene[1]) for scene in fixtures]
    width, height = (640, 480) if production else (80, 100)
    expected_total = 4 * width * height
    counts = [0, 0]
    seen_lanes = [[False] * 4 for _ in range(3)]
    first_a: dict[tuple[int, int], tuple[int, int, int]] = {}
    changed_b = changed_c = return_mismatches = errors = total = 0

    for line in output.splitlines():
        if not line.startswith("T1MPIX "):
            continue
        sid, x, y, got_valid, got_lane, got_r, got_g, got_b = map(int, line.split()[1:])
        scene_index = 0 if sid == 3 else sid
        expected_valid, expected_lane, u, v = oracle(decoded[scene_index], x, y)
        result = material_result(operator, u, v)
        valid_fragment = expected_valid
        expected_rgb = ((15, 15, 0) if result else (0, 0, 15)) if valid_fragment else (0, 0, 0)
        if (got_valid, got_lane, (got_r, got_g, got_b)) != (
            int(valid_fragment), expected_lane, expected_rgb
        ):
            errors += 1
            if errors <= 10:
                print(f"MISMATCH op={operator} scene={sid} xy=({x},{y}) "
                      f"expected={(int(valid_fragment), expected_lane, expected_rgb)} "
                      f"got={(got_valid, got_lane, (got_r, got_g, got_b))}")
        if valid_fragment:
            seen_lanes[scene_index][expected_lane] = True
            counts[int(result)] += 1
        color = expected_rgb
        key = (x, y)
        if sid == 0:
            first_a[key] = color
        elif sid == 1:
            changed_b += color != first_a.get(key)
        elif sid == 2:
            changed_c += color != first_a.get(key)
        elif color != first_a.get(key):
            return_mismatches += 1
        total += 1

    if total != expected_total:
        errors += 1
        print(f"FAIL: expected {expected_total} pixels, received {total}")
    if not all(all(lanes) for lanes in seen_lanes):
        errors += 1
        print(f"FAIL: not all winning lanes observed: {seen_lanes}")
    if not all(counts) or not changed_b or not changed_c or return_mismatches:
        errors += 1
        print(f"FAIL: colors/scenes op={operator} counts={counts} "
              f"changedB={changed_b} changedC={changed_c} return={return_mismatches}")
    if f"PASS: T1m ALU op={operator} " not in output:
        errors += 1
        print(f"FAIL: T1m simulation marker missing for {OPERATORS[operator]}")
    return errors


def check_illegal_profiles() -> int:
    cases = [
        ("unprepared", {"PREPARED_SCENE": 0},
         "T1M_requires_registered_prepared_t1i_uv_and_exclusive_mode"),
        ("no_partition", {"T1L_PIPELINE_PARTITION": 0},
         "T1M_requires_registered_prepared_t1i_uv_and_exclusive_mode"),
        ("old_material", {"T1L_MATERIAL_OP": 3},
         "T1M_requires_registered_prepared_t1i_uv_and_exclusive_mode"),
        ("no_output_register", {"GPU_POST_WINNER_REG": 0},
         "T1M_requires_registered_prepared_t1i_uv_and_exclusive_mode"),
        ("invalid_op", {"T1M_ALU_OP": 6},
         "T1M_fragment_alu_op_must_be_0_through_5"),
        ("with_diagnostic", {"T1I_UV_DIAG": 1},
         "T1M_requires_registered_prepared_t1i_uv_and_exclusive_mode"),
    ]
    errors = 0
    for name, overrides, expected_guard in cases:
        params = {
            "DEVICE": '"A7"', "ENABLE_HDMI": 0, "PREPARED_SCENE": 1,
            "FOUR_PRIMITIVE_SCENE": 1, "T1I_UV_SCENE": 1,
            "T1L_PIPELINE_PARTITION": 1, "T1M_FRAGMENT_ALU": 1,
            "T1M_ALU_OP": 2, "GPU_POST_WINNER_REG": 1,
        }
        params.update(overrides)
        param_text = ",".join(f".{key}({value})" for key, value in params.items())
        tb = ("module invalid_t1m_profile_tb;\n"
              f"spu_gpu_top #({param_text}) dut();\n"
              "endmodule\n")
        with tempfile.TemporaryDirectory(prefix=f"spu_t1m_bad_{name}_") as temp_dir:
            temp = Path(temp_dir)
            tb_path = temp / "invalid_profile.v"
            out = temp / "invalid_profile.vvp"
            tb_path.write_text(tb)
            compiled = subprocess.run(
                ["iverilog", "-g2012", "-s", "invalid_t1m_profile_tb", "-o", str(out),
                 str(tb_path), *[str(ROOT / p) for p in RTL_FILES]],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        if compiled.returncode == 0 or expected_guard not in compiled.stderr:
            errors += 1
            print(f"FAIL: illegal profile {name} was not rejected by T1m guard")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true",
                        help="run only XOR over the production A/B/C/A profile")
    args = parser.parse_args()
    operators = (2,) if args.production else tuple(OPERATORS)
    errors = 0
    for operator in operators:
        result, output = compile_and_run(operator, args.production)
        if result:
            print(output[-5000:])
            return 1
        errors += check_oracle(operator, output, args.production)
    if not args.production:
        errors += check_illegal_profiles()
    if errors:
        print(f"FAIL: T1m fragment ALU oracle errors={errors}")
        return 1
    if args.production:
        print("PASS: T1m independent production 640x480 A/B/C/A XOR oracle "
              "(1228800 pixels)")
    else:
        print("PASS: T1m independent reduced A/B/C/A oracle; six ALU operations, "
              "blue/yellow mapping, invalid black, four winner lanes and alignment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
