#!/usr/bin/env python3
"""Measure one T1d diagnostic simulation outside the repository runner."""

import argparse
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "hardware/tests/common/sim_xilinx_bufg.v",
    "hardware/rtl/peripherals/whisper/spu_uart_rx.v",
    "hardware/rtl/peripherals/whisper/spu_t1d_diag_uart_tx.v",
    "hardware/rtl/peripherals/whisper/spu_t1d_diag_record.v",
    "hardware/rtl/gpu/spu_video_timing.v",
    "hardware/rtl/gpu/spu_edge_stepper.v",
    "hardware/rtl/gpu/spu_attr_stepper.v",
    "hardware/rtl/gpu/spu_raster_unit.v",
    "hardware/rtl/gpu/spu_dual_raster.v",
    "hardware/rtl/gpu/spu_depth_compare.v",
    "hardware/rtl/gpu/spu_depth_math.v",
    "hardware/rtl/gpu/spu_depth_dispatch.v",
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v",
    "hardware/rtl/gpu/spu_scene_loader.v",
    "hardware/rtl/gpu/spu_scene_unpack.v",
    "hardware/rtl/gpu/spu_scene_profile_unpack.v",
    "hardware/rtl/gpu/spu_prepared_scene_control.v",
    "hardware/rtl/gpu/spu_depth_dispatch4.v",
    "hardware/rtl/gpu/spu_depth_compare4.v",
    "hardware/rtl/gpu/spu_prepared_scalar_attribute4.v",
    "hardware/rtl/hal/hal_vga.v",
    "hardware/rtl/hal/hal_hdmi_tmds.v",
    "hardware/rtl/hal/hal_hdmi_serdes_a7.v",
    "hardware/rtl/hal/hal_hdmi.v",
    "hardware/rtl/gpu/spu_gpu_top.v",
    "hardware/boards/artix7/spu_a7_gpu_vga_top.v",
    "hardware/tests/common/spu_t1d_repeatability_diag_tb.v",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, default=0)
    parser.add_argument("--reset", type=int, default=0)
    parser.add_argument("--run-timeout", type=int, default=150)
    parser.add_argument("--compile-only", action="store_true")
    args = parser.parse_args()
    if args.phase not in range(4) or args.reset not in range(4):
        parser.error("phase and reset must be in 0..3")
    if args.run_timeout < 61:
        parser.error("run-timeout must exceed the repository's 60-second cap")
    with tempfile.TemporaryDirectory(prefix="t1d_runtime_", dir=ROOT / "build") as directory:
        binary = Path(directory) / "diag.vvp"
        command = ["iverilog", "-g2012", "-DGPU_T1D_DIAG", "-DGPU_T1D_UART",
                   "-s", "spu_t1d_repeatability_diag_tb", "-o", str(binary),
                   *(str(ROOT / source) for source in SOURCES)]
        started = time.monotonic()
        compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        compile_seconds = time.monotonic() - started
        if compiled.returncode:
            print(compiled.stdout + compiled.stderr, flush=True)
            raise SystemExit(f"COMPILE FAILED exit={compiled.returncode}")
        print(f"compile_wall_seconds={compile_seconds:.3f}", flush=True)
        if args.compile_only:
            print("PASS: isolated D1 compile", flush=True)
            return
        command = ["vvp", str(binary), f"+START_PHASE={args.phase}",
                   f"+RESET_PHASE={args.reset}"]
        started = time.monotonic()
        try:
            result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                    text=True, timeout=args.run_timeout)
        except subprocess.TimeoutExpired as error:
            elapsed = time.monotonic() - started
            print(f"TIMEOUT: vvp wall_seconds={elapsed:.3f} cap={args.run_timeout}",
                  flush=True)
            if error.stdout:
                print(error.stdout.decode(errors="replace")[-2000:], flush=True)
            raise SystemExit(124)
        elapsed = time.monotonic() - started
        print(f"vvp_wall_seconds={elapsed:.3f}", flush=True)
        print(f"vvp_exit={result.returncode}", flush=True)
        print(result.stdout[-4000:] + result.stderr[-2000:], flush=True)
        verdict = "PASS: T1d repeatability diagnostic D1" in result.stdout
        if result.returncode or not verdict or "FAIL:" in result.stdout:
            raise SystemExit(1)
        print("PASS: isolated T1d diagnostic completed semantically", flush=True)


if __name__ == "__main__":
    main()
