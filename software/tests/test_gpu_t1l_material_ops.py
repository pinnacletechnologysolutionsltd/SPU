#!/usr/bin/env python3
"""Independent T1l material-operator oracle over frozen T1i scenes."""

from __future__ import annotations

import subprocess
import tempfile
import argparse
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, TB, decode, load_scene, oracle


def compile_and_run(operator: int, production: bool = False,
                    pipeline_partition: bool = False) -> tuple[int, str]:
    scenes = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    tb_text = TB
    for key, scene in zip(("SCENE_A", "SCENE_B", "SCENE_C"), scenes):
        tb_text = tb_text.replace(f"@@{key}@@", scene[0])
    params = ["-P", "t1i_uv_tb.T1L_MAT=" + str(operator),
              "-P", "t1i_uv_tb.OUT_REG=1",
              "-P", "t1i_uv_tb.T1L_PIPE=" + str(int(pipeline_partition))]
    if production:
        params += [
            "-P", "t1i_uv_tb.H_ACTIVE=640", "-P", "t1i_uv_tb.H_FP=16",
            "-P", "t1i_uv_tb.H_SYNC=96", "-P", "t1i_uv_tb.H_BP=48",
            "-P", "t1i_uv_tb.V_ACTIVE=480", "-P", "t1i_uv_tb.V_FP=10",
            "-P", "t1i_uv_tb.V_SYNC=2", "-P", "t1i_uv_tb.V_BP=33",
            "-P", "t1i_uv_tb.CHECK_W=80", "-P", "t1i_uv_tb.CHECK_H=100",
        ]
    with tempfile.TemporaryDirectory(prefix=f"spu_t1l_op{operator}_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1l_material_tb.v"
        out = temp / "t1l_material_tb.vvp"
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


def expected_white(operator: int, u: int, v: int) -> bool:
    if operator == 1:
        return bool(((u >> 12) ^ (v >> 12)) & 1)
    if operator == 2:
        return ((u >> 10) & 0b11) == 0 or ((v >> 10) & 0b11) == 0
    if operator == 3:
        return bool((u >> 12) & 1)
    if operator == 4:
        return bool((v >> 12) & 1)
    raise ValueError(operator)


def check_oracle(operator: int, output: str, production: bool = False) -> int:
    fixtures = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    decoded = [decode(scene[1]) for scene in fixtures]
    errors = total = 0
    seen_lanes = [[False] * 4 for _ in range(3)]
    color_counts = [0, 0]
    first_a: dict[tuple[int, int], int] = {}
    changed = [0, 0]
    width, height = (640, 480) if production else (80, 100)

    for line in output.splitlines():
        if not line.startswith("T1LPIX "):
            continue
        sid, x, y, valid, lane, red = map(int, line.split()[1:])
        scene_index = 0 if sid == 3 else sid
        expected_valid, expected_lane, u, v = oracle(decoded[scene_index], x, y)
        white = expected_valid and expected_white(operator, u, v)
        expected_red = 15 if white else 0
        if (valid, lane, red) != (expected_valid, expected_lane, expected_red):
            errors += 1
            if errors <= 10:
                print(f"MISMATCH op={operator} scene={sid} xy=({x},{y}) "
                      f"expected={(expected_valid, expected_lane, expected_red)} "
                      f"got={(valid, lane, red)}")
        if expected_valid:
            seen_lanes[scene_index][expected_lane] = True
            color_counts[int(white)] += 1
        pattern = int(white)
        if sid == 0:
            first_a[(x, y)] = pattern
        elif sid in (1, 2):
            changed[sid - 1] += pattern != first_a.get((x, y), -1)
        elif pattern != first_a.get((x, y), -1):
            errors += 1
            if errors <= 10:
                print(f"MISMATCH op={operator} return-A pixel ({x},{y})")
        total += 1

    if total != 4 * width * height:
        errors += 1
        print(f"FAIL: op={operator} expected {4 * width * height} pixels, got {total}")
    if not all(all(lanes) for lanes in seen_lanes):
        errors += 1
        print(f"FAIL: op={operator} did not observe every winning lane: {seen_lanes}")
    if not all(color_counts) or not all(changed):
        errors += 1
        print(f"FAIL: op={operator} color/scene coverage colors={color_counts} changes={changed}")
    marker = f"PASS: T1l material op={operator} "
    if marker not in output or "A-return-mismatches=0" not in output:
        errors += 1
        print(f"FAIL: testbench transition/reset/alignment marker missing for op={operator}")
    expected_total = 4 * width * height
    if f"PASS: T1i A/B/C/A full-frame U/V activation pixels={expected_total}" not in output:
        errors += 1
        print(f"FAIL: complete A/B/C/A scan marker missing for op={operator}")
    return errors


def check_illegal_profiles_rejected() -> int:
    cases = [
        ("no_t1i", ".T1I_UV_SCENE(0),.GPU_POST_WINNER_REG(1)",
         "T1L_requires_registered_prepared_t1i_without_diagnostics_or_t1j_t1k"),
        ("no_output_register", ".T1I_UV_SCENE(1),.GPU_POST_WINNER_REG(0)",
         "T1L_requires_registered_prepared_t1i_without_diagnostics_or_t1j_t1k"),
        ("with_t1h", ".T1I_UV_SCENE(1),.T1H_SCALAR_SCENE(1),.GPU_POST_WINNER_REG(1)",
         "T1L_requires_registered_prepared_t1i_without_diagnostics_or_t1j_t1k"),
        ("with_uv_diag", ".T1I_UV_SCENE(1),.T1I_UV_DIAG(1),.GPU_POST_WINNER_REG(1)",
         "T1L_requires_registered_prepared_t1i_without_diagnostics_or_t1j_t1k"),
        ("with_t1j", ".T1I_UV_SCENE(1),.T1J_PROC_SHADE(1),.GPU_POST_WINNER_REG(1)",
         "T1L_requires_registered_prepared_t1i_without_diagnostics_or_t1j_t1k"),
        ("with_t1k", ".T1I_UV_SCENE(1),.T1K_GRID_SHADE(1),.GPU_POST_WINNER_REG(1)",
         "T1L_requires_registered_prepared_t1i_without_diagnostics_or_t1j_t1k"),
        ("invalid_value", ".T1I_UV_SCENE(1),.GPU_POST_WINNER_REG(1),.T1L_MATERIAL_OP(5)",
         "T1L_material_op_must_be_0_through_4"),
    ]
    errors = 0
    for name, options, marker in cases:
        invalid = f"""module invalid_profile_tb;
        spu_gpu_top #(.DEVICE(\"A7\"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(1),.T1L_MATERIAL_OP(1),{options}) dut();
        endmodule
        """
        with tempfile.TemporaryDirectory(prefix=f"spu_t1l_{name}_") as temp_dir:
            tb = Path(temp_dir) / "invalid.v"
            out = Path(temp_dir) / "invalid.vvp"
            tb.write_text(invalid)
            compiled = subprocess.run(
                ["iverilog", "-g2012", "-s", "invalid_profile_tb", "-o", str(out),
                 str(tb), *[str(ROOT / p) for p in RTL_FILES]],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        if compiled.returncode == 0 or marker not in compiled.stderr:
            print(f"FAIL: illegal T1l profile {name} was not rejected")
            print(compiled.stderr[-1800:])
            errors += 1
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true",
                        help="run only U-stripes at production 640x480 timing")
    parser.add_argument("--pipeline-partition", action="store_true",
                        help="enable the opt-in T1l pre-winner register stage")
    args = parser.parse_args()
    errors = 0
    operators = (3,) if (args.production or args.pipeline_partition) else range(1, 5)
    for operator in operators:
        result, output = compile_and_run(operator, args.production,
                                         args.pipeline_partition)
        if result:
            print(output[-5000:])
            return 1
        errors += check_oracle(operator, output, args.production)
    if not args.production:
        errors += check_illegal_profiles_rejected()
    if errors:
        print(f"FAIL: T1l material operator oracle errors={errors}")
        return 1
    if args.production:
        print("PASS: T1l independent production 640x480 A/B/C/A U-stripe oracle "
              "(1228800 pixels)")
    elif args.pipeline_partition:
        print("PASS: T1l pre-winner partition reduced A/B/C/A U-stripe oracle")
    else:
        print("PASS: T1l independent A/B/C/A material oracle; four compile-time operators, "
              "128000 pixels, winner lanes, invalid black, reset and output alignment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
