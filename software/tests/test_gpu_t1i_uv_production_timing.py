#!/usr/bin/env python3
"""T1i A/B/C/A oracle replay with the production 640x480 raster timing."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from test_gpu_t1i_uv import ROOT, RTL_FILES, TB, decode, load_scene, oracle


def main() -> int:
    fixtures = [load_scene(f"gpu_t1i_scene_{name}_wire_175b.hex") for name in "abc"]
    tb_text = TB
    for key, scene in zip(("SCENE_A", "SCENE_B", "SCENE_C"), fixtures):
        tb_text = tb_text.replace(f"@@{key}@@", scene[0])

    with tempfile.TemporaryDirectory(prefix="spu_t1i_uv_640x480_") as temp_dir:
        temp = Path(temp_dir)
        tb = temp / "t1i_uv_640x480_tb.v"
        out = temp / "t1i_uv_640x480_tb.vvp"
        tb.write_text(tb_text)
        compiled = subprocess.run(
            ["iverilog", "-g2012", "-s", "t1i_uv_tb",
             "-P", "t1i_uv_tb.H_ACTIVE=640", "-P", "t1i_uv_tb.H_FP=16",
             "-P", "t1i_uv_tb.H_SYNC=96", "-P", "t1i_uv_tb.H_BP=48",
             "-P", "t1i_uv_tb.V_ACTIVE=480", "-P", "t1i_uv_tb.V_FP=10",
             "-P", "t1i_uv_tb.V_SYNC=2", "-P", "t1i_uv_tb.V_BP=33",
             "-P", "t1i_uv_tb.OUT_REG=1",
             "-P", "t1i_uv_tb.CHECK_W=80", "-P", "t1i_uv_tb.CHECK_H=100",
             "-o", str(out), str(tb), *[str(ROOT / item) for item in RTL_FILES]],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if compiled.returncode:
            print(compiled.stderr)
            return 1
        simulated = subprocess.run(
            ["vvp", str(out)], cwd=ROOT, text=True,
            capture_output=True, check=False,
        )

    if simulated.returncode:
        print(simulated.stderr)
        return 1
    errors = 0
    counts = [0, 0, 0, 0]
    decoded = [decode(scene[1]) for scene in fixtures]
    for line in simulated.stdout.splitlines():
        if line.startswith("FAIL:"):
            print(line)
            errors += 1
        if not line.startswith("PIX "):
            continue
        _, sid_s, x_s, y_s, valid_s, lane_s, u_s, v_s = line.split()
        sid, x, y, valid, lane, u, v = map(
            int, (sid_s, x_s, y_s, valid_s, lane_s, u_s, v_s)
        )
        expected = oracle(decoded[0 if sid == 3 else sid], x, y)
        if (valid, lane, u, v) != expected:
            errors += 1
            if errors <= 12:
                print(f"MISMATCH scene={sid} xy=({x},{y}) expected={expected} got={(valid,lane,u,v)}")
        counts[sid] += 1

    if counts != [8000] * 4:
        errors += 1
        print(f"FAIL: production-timing ROI sample counts expected={[8000] * 4} got={counts}")
    expected_total = 4 * 640 * 480
    if f"PASS: T1i A/B/C/A full-frame U/V activation pixels={expected_total}" not in simulated.stdout:
        errors += 1
        print(simulated.stdout[-2500:])
    if errors:
        print(f"FAIL: T1i production-timing U/V oracle errors={errors}")
        return 1
    print("PASS: T1i production 640x480 A/B/C/A timing; 32,000 ROI samples match the independent U/V oracle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
