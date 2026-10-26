#!/usr/bin/env python3
"""Run one frozen Golden Core scene through Python T1d and standalone SIM-1."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "examples/gpu/golden_core_tetra_views/identity.json"
OUT_BASE = ROOT / "build/gpu_evaluation"
PPM_HEADER = b"P6\n640 480\n255\n"
EXPECTED_RGB_BYTES = 640 * 480 * 3


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"command failed with exit {result.returncode}: {command}")


def repository_identity(repository: Path) -> tuple[str, bool]:
    revision = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    status = subprocess.run(
        ["git", "-C", str(repository), "status", "--porcelain"],
        cwd=ROOT, check=True, capture_output=True, text=True).stdout
    return revision, not bool(status.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim1", type=Path,
                        default=ROOT.parent / "spu-sim/build/release/spu-sim",
                        help="standalone SIM-1 executable (default: ../spu-sim/build/release/spu-sim)")
    parser.add_argument("--out", type=Path, required=True,
                        help="new output directory beneath build/gpu_evaluation")
    parser.add_argument("--expected-spu-revision",
                        help="require this SPU repository commit")
    parser.add_argument("--expected-sim1-revision",
                        help="require this standalone SIM-1 repository commit")
    parser.add_argument("--require-clean-checkouts", action="store_true",
                        help="reject either repository if its worktree is dirty")
    args = parser.parse_args()

    sim1 = args.sim1.resolve()
    if not sim1.is_file():
        parser.error(f"SIM-1 executable not found: {sim1}; build it using its README")
    sim_repo = sim1.parent.parent.parent
    rom = sim_repo / "hardware/rtl/arch/gpu_reciprocal_lut_q15.mem"
    if not rom.is_file():
        parser.error(f"SIM-1 reciprocal ROM not found: {rom}")
    try:
        spu_revision, spu_clean = repository_identity(ROOT)
        sim1_revision, sim1_clean = repository_identity(sim_repo)
    except subprocess.CalledProcessError as error:
        parser.error(f"could not identify repository revision: {error}")
    if args.expected_spu_revision and spu_revision != args.expected_spu_revision:
        parser.error(f"SPU revision {spu_revision} does not match expected {args.expected_spu_revision}")
    if args.expected_sim1_revision and sim1_revision != args.expected_sim1_revision:
        parser.error(f"SIM-1 revision {sim1_revision} does not match expected {args.expected_sim1_revision}")
    if args.require_clean_checkouts and not (spu_clean and sim1_clean):
        parser.error(f"clean checkouts required; SPU clean={spu_clean}, SIM-1 clean={sim1_clean}")

    out = args.out if args.out.is_absolute() else ROOT / args.out
    out = out.resolve()
    if OUT_BASE.resolve() not in out.parents:
        parser.error(f"output must be a child of {OUT_BASE}")
    if out.exists():
        parser.error(f"refusing to overwrite existing output: {out}")

    run([sys.executable, "-m", "software.spu_gpu_eval.cli", "device-preview",
         str(SCENE.relative_to(ROOT)), "--out", str(out)])
    packet = out / "scene_packet.bin"
    python_ppm = (out / "device_preview.ppm").read_bytes()
    if not python_ppm.startswith(PPM_HEADER) or len(python_ppm) != len(PPM_HEADER) + EXPECTED_RGB_BYTES:
        raise RuntimeError("Python T1d device-preview did not produce the expected 640x480 PPM")

    raw_output = out / "sim1_frame.rgb8"
    run([str(sim1), "gpu", "render", str(packet), "--output", str(raw_output),
         "--rom", str(rom)])
    sim1_rgb = raw_output.read_bytes()
    python_rgb = python_ppm[len(PPM_HEADER):]
    if len(sim1_rgb) != EXPECTED_RGB_BYTES:
        raise RuntimeError(f"SIM-1 returned {len(sim1_rgb)} RGB bytes; expected {EXPECTED_RGB_BYTES}")

    match = sim1_rgb == python_rgb
    (out / "sim1_frame.ppm").write_bytes(PPM_HEADER + sim1_rgb)
    comparison = {
        "format": "gc_t1d_newcomer_comparison_v1",
        "scene": str(SCENE.relative_to(ROOT)),
        "scene_sha256": sha256(SCENE.read_bytes()),
        "scene_packet_sha256": sha256(packet.read_bytes()),
        "spu_repository_revision": spu_revision,
        "spu_worktree_clean": spu_clean,
        "expected_spu_revision": args.expected_spu_revision,
        "sim1_repository_revision": sim1_revision,
        "sim1_worktree_clean": sim1_clean,
        "expected_sim1_revision": args.expected_sim1_revision,
        "sim1_executable": str(sim1),
        "sim1_executable_sha256": sha256(sim1.read_bytes()),
        "reciprocal_rom": str(rom),
        "reciprocal_rom_sha256": sha256(rom.read_bytes()),
        "python_path": "host-CPU finite-width T1d device model",
        "sim1_path": "standalone C++ SIM-1 gpu.scene.t1d.two-triangle-v1 renderer",
        "frame_bytes": len(sim1_rgb),
        "python_rgb8_sha256": sha256(python_rgb),
        "sim1_rgb8_sha256": sha256(sim1_rgb),
        "byte_exact_match": match,
        "display_file": "sim1_frame.ppm",
        "physical_observation": False,
    }
    (out / "cross_renderer_comparison.json").write_text(
        json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    print(f"complete-frame comparison: {'PASS' if match else 'FAIL'}")
    print(f"SPU revision: {spu_revision} (clean={spu_clean})")
    print(f"SIM-1 revision: {sim1_revision} (clean={sim1_clean})")
    print(f"Python RGB8 SHA-256: {comparison['python_rgb8_sha256']}")
    print(f"SIM-1 RGB8 SHA-256:  {comparison['sim1_rgb8_sha256']}")
    print(f"inspect image: {out / 'sim1_frame.ppm'}")
    print(f"evidence: {out / 'cross_renderer_comparison.json'}")
    return 0 if match else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
