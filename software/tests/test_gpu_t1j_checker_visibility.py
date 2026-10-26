#!/usr/bin/env python3
"""Independent oracle for the T1j two-visible-color checker diagnostic."""

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
    params = ["-P", "t1i_uv_tb.VIS_DIAG=1",
              "-P", "t1i_uv_tb.OUT_REG=1"]
    if production:
        params += [
            "-P", "t1i_uv_tb.H_ACTIVE=640", "-P", "t1i_uv_tb.H_FP=16",
            "-P", "t1i_uv_tb.H_SYNC=96", "-P", "t1i_uv_tb.H_BP=48",
            "-P", "t1i_uv_tb.V_ACTIVE=480", "-P", "t1i_uv_tb.V_FP=10",
            "-P", "t1i_uv_tb.V_SYNC=2", "-P", "t1i_uv_tb.V_BP=33",
            "-P", "t1i_uv_tb.CHECK_W=80", "-P", "t1i_uv_tb.CHECK_H=100",
        ]
    with tempfile.TemporaryDirectory(prefix="spu_t1j_vis_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1j_vis_tb.v"
        out = temp / "t1j_vis_tb.vvp"
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
        ("no_t1j", ".T1J_PROC_SHADE(0),.T1I_UV_SCENE(1),.GPU_POST_WINNER_REG(1)"),
        ("no_post_register", ".T1J_PROC_SHADE(1),.T1I_UV_SCENE(1),.GPU_POST_WINNER_REG(0)"),
        ("with_t1k", ".T1J_PROC_SHADE(1),.T1I_UV_SCENE(1),.GPU_POST_WINNER_REG(1),.T1K_GRID_SHADE(1)"),
        ("with_uv_diag", ".T1J_PROC_SHADE(1),.T1I_UV_SCENE(1),.T1I_UV_DIAG(1),.GPU_POST_WINNER_REG(1)"),
    ]
    errors = 0
    marker = "T1J_checker_visibility_requires_registered_t1j_without_diagnostics"
    for name, options in cases:
        invalid = f"""module invalid_profile_tb;
        spu_gpu_top #(.DEVICE(\"A7\"),.ENABLE_HDMI(0),.PREPARED_SCENE(1),
            .FOUR_PRIMITIVE_SCENE(1),.T1J_CHECKER_VIS_DIAG(1),{options}) dut();
        endmodule
        """
        with tempfile.TemporaryDirectory(prefix=f"spu_t1j_vis_{name}_") as temp_dir:
            tb = Path(temp_dir) / "invalid.v"
            out = Path(temp_dir) / "invalid.vvp"
            tb.write_text(invalid)
            compiled = subprocess.run(
                ["iverilog", "-g2012", "-s", "invalid_profile_tb", "-o", str(out),
                 str(tb), *[str(ROOT / p) for p in RTL_FILES]],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        if compiled.returncode == 0 or marker not in compiled.stderr:
            print(f"FAIL: illegal T1j visibility profile {name} was not rejected")
            print(compiled.stderr[-2000:])
            errors += 1
    return errors


def check_oracle(output: str, production: bool) -> int:
    fixtures = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    decoded = [decode(scene[1]) for scene in fixtures]
    width, height = (640, 480) if production else (80, 100)
    total = errors = 0
    changed = [0, 0]
    first_a: dict[tuple[int, int], tuple[int, int, int]] = {}
    lane_colors = [[[False, False] for _ in range(4)] for _ in range(3)]

    for line in output.splitlines():
        if not line.startswith("T1JVPIX "):
            continue
        sid, x, y, valid, lane, red, green, blue = map(int, line.split()[1:])
        scene_index = 0 if sid == 3 else sid
        expected_valid, expected_lane, u, v = oracle(decoded[scene_index], x, y)
        checker = expected_valid and (((u >> 12) ^ (v >> 12)) & 1)
        expected_rgb = (15, 15, 15) if checker else ((0, 0, 15) if expected_valid else (0, 0, 0))
        if (valid, lane, red, green, blue) != (
            expected_valid, expected_lane, *expected_rgb
        ):
            errors += 1
            if errors <= 12:
                print(f"MISMATCH scene={sid} xy=({x},{y}) expected="
                      f"{(expected_valid, expected_lane, *expected_rgb)} got="
                      f"{(valid, lane, red, green, blue)}")
        if expected_valid:
            lane_colors[scene_index][expected_lane][int(bool(checker))] = True
        color = (red, green, blue)
        if sid == 0:
            first_a[(x, y)] = color
        elif sid in (1, 2):
            changed[sid - 1] += color != first_a.get((x, y))
        elif color != first_a.get((x, y)):
            errors += 1
            if errors <= 12:
                print(f"MISMATCH return-A visibility color at ({x},{y})")
        total += 1

    expected_frames = 4 * width * height
    if total != expected_frames:
        errors += 1
        print(f"FAIL: T1j visibility pixel count expected={expected_frames} got={total}")
    if not all(all(all(classes) for classes in scene) for scene in lane_colors):
        errors += 1
        print("FAIL: every winning lane must render both checker colors in A/B/C")
    if min(changed) == 0:
        errors += 1
        print(f"FAIL: B/C visibility pattern did not differ from A: {changed}")
    if "PASS: T1j visibility colors " not in output:
        errors += 1
        print("FAIL: testbench did not report visibility colors and return-A checks")
    if f"PASS: T1i A/B/C/A full-frame U/V activation pixels={expected_frames}" not in output:
        errors += 1
        print("FAIL: testbench did not report the complete A/B/C/A scan")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true",
                        help="use production 640x480 timing; detached-runner invocation required")
    args = parser.parse_args()
    result, output = compile_and_run(args.production)
    if result:
        print(output[-5000:])
        return 1
    errors = check_oracle(output, args.production)
    errors += check_illegal_profiles_rejected()
    if errors:
        print(output[-3000:])
        print(f"FAIL: T1j checker visibility oracle errors={errors}")
        return 1
    label = "production 640x480" if args.production else "80x100"
    print(f"PASS: T1j two-visible-color checker oracle ({label}, "
          f"{4 * (640 * 480 if args.production else 80 * 100):,} pixels)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
