"""D1 simulation for the frozen T1d repeatability diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SHA256 = (
    "aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee"
)
EXPECTED_PAYLOAD_CRC = 0x7920


def crc16_ccitt(payload: bytes) -> int:
    crc = 0xFFFF
    for value in payload:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def parse_offsets(value: str) -> list[int]:
    offsets = [int(item, 10) for item in value.split(",") if item]
    if not offsets or any(item < 0 or item > 3 for item in offsets):
        raise ValueError("offsets must be a non-empty comma-separated list in 0..3")
    return offsets


def run() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--phase-offsets", default="0,1,2,3")
    parser.add_argument("--reset-offsets", default="0,1,2,3")
    args = parser.parse_args()

    fixture = args.fixture if args.fixture.is_absolute() else ROOT / args.fixture
    wire = fixture.read_bytes()
    if len(wire) != 64 or wire[0] != 0xA5:
        raise AssertionError("T1d diagnostic fixture must be 64 bytes beginning with A5")
    if hashlib.sha256(wire).hexdigest() != FIXTURE_SHA256:
        raise AssertionError("T1d diagnostic fixture SHA-256 differs from frozen value")
    if crc16_ccitt(wire[1:]) != EXPECTED_PAYLOAD_CRC:
        raise AssertionError("T1d diagnostic fixture CRC differs from frozen value")

    phase_offsets = parse_offsets(args.phase_offsets)
    reset_offsets = parse_offsets(args.reset_offsets)
    if len(phase_offsets) != len(reset_offsets):
        raise ValueError("phase-offsets and reset-offsets must have equal length")

    source_files = [
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
        "hardware/rtl/gpu/spu_prepared_scalar_attribute4.v",
        "hardware/rtl/hal/hal_vga.v",
        "hardware/rtl/hal/hal_hdmi_tmds.v",
        "hardware/rtl/hal/hal_hdmi_serdes_a7.v",
        "hardware/rtl/hal/hal_hdmi.v",
        "hardware/rtl/gpu/spu_gpu_top.v",
        "hardware/boards/artix7/spu_a7_gpu_vga_top.v",
        "hardware/tests/common/spu_t1d_repeatability_diag_tb.v",
    ]
    sources = [str(ROOT / item) for item in source_files]

    with tempfile.TemporaryDirectory(prefix="spu_t1d_diag_") as temp_dir:
        temp = Path(temp_dir)
        vvp = temp / "t1d_repeatability_diag.vvp"
        compile_cmd = [
            "iverilog", "-g2012", "-DGPU_T1D_DIAG", "-DGPU_T1D_UART",
            "-s", "spu_t1d_repeatability_diag_tb", "-o", str(vvp), *sources,
        ]
        compiled = subprocess.run(
            compile_cmd, cwd=ROOT, text=True, capture_output=True, check=False
        )
        if compiled.returncode != 0:
            raise RuntimeError(
                "D1 diagnostic simulation compile failed:\n"
                + compiled.stdout + compiled.stderr
            )

        for phase, reset in zip(phase_offsets, reset_offsets):
            command = [
                "vvp", str(vvp),
                f"+START_PHASE={phase}", f"+RESET_PHASE={reset}",
            ]
            result = subprocess.run(
                command, cwd=ROOT, text=True, capture_output=True,
                timeout=45, check=False,
            )
            print(f"--- D1 phase={phase} reset={reset} ---")
            print(result.stdout, end="")
            if result.returncode != 0:
                print(result.stderr, end="")
                raise RuntimeError(f"D1 diagnostic simulation failed for phase={phase}, reset={reset}")
            if "PASS: T1d repeatability diagnostic D1" not in result.stdout:
                raise AssertionError(
                    f"D1 diagnostic simulation did not report PASS for phase={phase}, reset={reset}"
                )

    print("PASS: T1d repeatability diagnostic D1 phase/reset matrix")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
