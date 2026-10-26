#!/usr/bin/env python3
"""Independent T1k two-axis grid shading oracle over frozen T1i scenes."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, TB, decode, load_scene, oracle


def compile_and_run(production: bool) -> tuple[int, str]:
    fixtures = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    tb_text = TB
    for key, scene in zip(("SCENE_A", "SCENE_B", "SCENE_C"), fixtures):
        tb_text = tb_text.replace(f"@@{key}@@", scene[0])
    params = ["-P", "t1i_uv_tb.GRID=1", "-P", "t1i_uv_tb.OUT_REG=1"]
    if production:
        params += [
            "-P", "t1i_uv_tb.H_ACTIVE=640", "-P", "t1i_uv_tb.H_FP=16",
            "-P", "t1i_uv_tb.H_SYNC=96", "-P", "t1i_uv_tb.H_BP=48",
            "-P", "t1i_uv_tb.V_ACTIVE=480", "-P", "t1i_uv_tb.V_FP=10",
            "-P", "t1i_uv_tb.V_SYNC=2", "-P", "t1i_uv_tb.V_BP=33",
            "-P", "t1i_uv_tb.CHECK_W=80", "-P", "t1i_uv_tb.CHECK_H=100",
        ]
    with tempfile.TemporaryDirectory(prefix="spu_t1k_grid_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1k_grid_tb.v"
        out = temp / "t1k_grid_tb.vvp"
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


def check_illegal_profiles_rejected() -> int:
    cases = [
        ("no_t1i", ".T1I_UV_SCENE(0),.GPU_POST_WINNER_REG(1)",
         "T1K_requires_registered_prepared_t1i_without_diagnostics_or_t1j"),
        ("no_output_register", ".T1I_UV_SCENE(1),.GPU_POST_WINNER_REG(0)",
         "T1K_requires_registered_prepared_t1i_without_diagnostics_or_t1j"),
        ("with_t1j", ".T1I_UV_SCENE(1),.GPU_POST_WINNER_REG(1),.T1J_PROC_SHADE(1)",
         "T1K_requires_registered_prepared_t1i_without_diagnostics_or_t1j"),
        ("with_uv_diag", ".T1I_UV_SCENE(1),.T1I_UV_DIAG(1),.GPU_POST_WINNER_REG(1)",
         "T1K_requires_registered_prepared_t1i_without_diagnostics_or_t1j"),
    ]
    errors = 0
    for name, options, marker in cases:
        invalid = f"""module invalid_profile_tb;
        spu_gpu_top #(.DEVICE(\"A7\"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(1),.T1K_GRID_SHADE(1),{options}) dut();
        endmodule
        """
        with tempfile.TemporaryDirectory(prefix=f"spu_t1k_{name}_") as temp_dir:
            tb = Path(temp_dir) / "invalid.v"
            out = Path(temp_dir) / "invalid.vvp"
            tb.write_text(invalid)
            compiled = subprocess.run(
                ["iverilog", "-g2012", "-s", "invalid_profile_tb", "-o", str(out),
                 str(tb), *[str(ROOT / p) for p in RTL_FILES]],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        if compiled.returncode == 0 or marker not in compiled.stderr:
            print(f"FAIL: illegal T1k profile {name} was not rejected")
            print(compiled.stderr[-2000:])
            errors += 1
    return errors


def check_oracle(output: str, production: bool) -> int:
    fixtures = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    decoded = [decode(scene[1]) for scene in fixtures]
    width, height = (640, 480) if production else (80, 100)
    total = errors = 0
    changed = [0, 0]
    first_a: dict[tuple[int, int], int] = {}
    lane_colors = [[[0, 0] for _ in range(4)] for _ in range(3)]

    for line in output.splitlines():
        if not line.startswith("T1KPIX "):
            continue
        sid, x, y, valid, lane, red, green, blue = map(int, line.split()[1:])
        scene_index = 0 if sid == 3 else sid
        expected_valid, expected_lane, u, v = oracle(decoded[scene_index], x, y)
        white = expected_valid and ((u & 0xFFF) < 1024 or (v & 0xFFF) < 1024)
        expected_rgb = 15 if white else 0
        if (valid, lane, red, green, blue) != (
            expected_valid, expected_lane, expected_rgb, expected_rgb, expected_rgb
        ):
            errors += 1
            if errors <= 12:
                print(f"MISMATCH scene={sid} xy=({x},{y}) expected="
                      f"{(expected_valid, expected_lane, expected_rgb)} got="
                      f"{(valid, lane, red, green, blue)}")
        observed = int(bool(red or green or blue))
        if expected_valid:
            lane_colors[scene_index][expected_lane][observed] += 1
        if sid == 0:
            first_a[(x, y)] = observed
        elif sid in (1, 2):
            changed[sid - 1] += observed != first_a.get((x, y), -1)
        elif observed != first_a.get((x, y), -1):
            errors += 1
            if errors <= 12:
                print(f"MISMATCH return-A grid at ({x},{y})")
        total += 1

    expected_frames = 4 * width * height
    if total != expected_frames:
        errors += 1
        print(f"FAIL: T1k pixel count expected={expected_frames} got={total}")
    if not all(all(sum(colors) > 0 and colors[0] > 0 and colors[1] > 0
                   for colors in scene) for scene in lane_colors):
        errors += 1
        print("FAIL: each lane must win both grid and interior colors in A/B/C")
    if min(changed) == 0:
        errors += 1
        print(f"FAIL: B/C grid did not differ from A: {changed}")
    if "PASS: T1k grid classes " not in output:
        errors += 1
        print("FAIL: testbench did not report grid scene/return checks")
    if f"PASS: T1i A/B/C/A full-frame U/V activation pixels={expected_frames}" not in output:
        errors += 1
        print("FAIL: testbench did not report complete A/B/C/A scan")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true",
                        help="use 640x480 timing; run through the detached job runner")
    args = parser.parse_args()
    result, output = compile_and_run(args.production)
    if result:
        print(output[-5000:])
        return 1
    errors = check_oracle(output, args.production)
    errors += check_illegal_profiles_rejected()
    if errors:
        print(output[-3000:])
        print(f"FAIL: T1k independent grid oracle errors={errors}")
        return 1
    if args.production:
        print("PASS: T1k independent production 640x480 A/B/C/A grid oracle "
              "(1,228,800 pixels)")
    else:
        print("PASS: T1k independent 80x100 A/B/C/A grid oracle (32,000 pixels)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
