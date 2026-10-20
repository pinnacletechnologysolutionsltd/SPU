"""Deterministic T1d ideal/device preview artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import packet, reference, scene as scene_module
from .device_model import pixel_decision, prepare_scene, render_rgb8
from .scene import HEIGHT, WIDTH, Scene, parse_scene_bytes


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures/gpu_t1d_scene_reference.json"
HEADER = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
MODULES = (
    "software/spu_gpu_eval/__init__.py", "software/spu_gpu_eval/scene.py",
    "software/spu_gpu_eval/packet.py", "software/spu_gpu_eval/reference.py",
    "software/spu_gpu_eval/preview.py", "software/spu_gpu_eval/cli.py",
    "software/spu_gpu_eval/device_packet.py", "software/spu_gpu_eval/device_arithmetic.py",
    "software/spu_gpu_eval/device_model.py", "software/spu_gpu_eval/device_loader.py",
    "software/spu_gpu_eval/device_preview.py",
)
PROFILE = (
    "hardware/rtl/gpu/spu_gpu_top.v", "hardware/rtl/gpu/spu_video_timing.v",
    "hardware/rtl/gpu/spu_scene_loader.v", "hardware/rtl/gpu/spu_scene_unpack.v",
    "hardware/rtl/gpu/spu_scene_profile_unpack.v", "hardware/rtl/gpu/spu_prepared_scene_control.v",
    "hardware/rtl/gpu/spu_dual_raster.v", "hardware/rtl/gpu/spu_raster_unit.v",
    "hardware/rtl/gpu/spu_edge_stepper.v", "hardware/rtl/gpu/spu_depth_dispatch.v",
    "hardware/rtl/gpu/spu_depth_math.v", "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_shared_mult35.v", "hardware/rtl/gpu/spu_attr_stepper.v",
    "hardware/rtl/gpu/spu_depth_compare.v", "hardware/rtl/arch/gpu_reciprocal_lut_q15.mem",
    "hardware/rtl/hal/hal_vga.v",
)


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def build_artifacts(raw: bytes, scene: Scene) -> dict[str, bytes]:
    wire = packet.compile_packet(scene)
    prepared = prepare_scene(wire)
    ideal = HEADER + reference.render_rgb8(scene)
    device = HEADER + render_rgb8(prepared)
    ideal_pixels, device_pixels = ideal[len(HEADER):], device[len(HEADER):]
    equal = sum(ideal_pixels[i:i + 3] == device_pixels[i:i + 3]
                for i in range(0, len(ideal_pixels), 3))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expectations = list(fixture["diagnostic_pixels"])
    expectations.append({"x": 320, "y": 0, "coverage": "overlap", "near": "tie_triangle0", "rgb": [15, 0, 0]})
    samples = [{
        "baseline_fixture_expectation": expected,
        "actual_ideal_decision": reference.pixel_decision(scene, expected["x"], expected["y"]),
        "actual_device_decision": pixel_decision(prepared, expected["x"], expected["y"]),
    } for expected in expectations]
    comparison = _json({
        "format": "spu_gpu_pixel_comparison_s2_v1",
        "expectation_scope": "frozen baseline fixture; actual values describe the input scene",
        "samples": samples,
        "full_frame_rgb": {"pixels": WIDTH * HEIGHT, "exact_match_pixels": equal,
                           "different_pixels": WIDTH * HEIGHT - equal},
    })
    module_hashes = {path: _hash((ROOT / path).read_bytes()) for path in MODULES}
    profile_hashes = {path: _hash((ROOT / path).read_bytes()) for path in PROFILE}
    manifest = {
        "format": "spu_gpu_device_preview_manifest_s2_v1",
        "profile": scene_module.PROFILE,
        "schema": scene_module.FORMAT,
        "repository_head": _git("rev-parse", "HEAD"),
        "repository_worktree": "dirty" if _git("status", "--porcelain") else "clean",
        "input_scene_sha256": _hash(raw),
        "reference_fixture_sha256": _hash(FIXTURE.read_bytes()),
        "software_source_sha256": module_hashes,
        "profile_source_sha256": profile_hashes,
        "scene_packet_sha256": _hash(wire),
        "ideal_preview_sha256": _hash(ideal),
        "device_preview_sha256": _hash(device),
        "pixel_comparison_sha256": _hash(comparison),
        "device_model": True,
        "physical_observation": False,
        "cycle_timing_model": False,
        "material_behavior": "flat RGB444 per triangle",
    }
    return {
        "scene_packet.bin": wire, "ideal_preview.ppm": ideal,
        "device_preview.ppm": device, "pixel_comparison.json": comparison,
        "manifest.json": _json(manifest),
    }


def write_device_preview(scene_path: str | Path, out_dir: str | Path) -> Path:
    source = Path(scene_path)
    if not source.is_absolute():
        source = Path.cwd() / source
    raw = source.read_bytes()
    scene = parse_scene_bytes(raw)
    base = (ROOT / "build/gpu_evaluation").resolve()
    candidate = Path(out_dir)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    target = candidate.resolve()
    if target == base or base not in target.parents:
        raise ValueError("--out must name a new directory under build/gpu_evaluation")
    if target.exists() or target.is_symlink():
        raise ValueError(f"output path already exists: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".s2_device_preview_", dir=target.parent))
    try:
        for name, data in build_artifacts(raw, scene).items():
            (stage / name).write_bytes(data)
        if target.exists() or target.is_symlink():
            raise ValueError(f"output path appeared during generation: {target.name}")
        os.rename(stage, target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return target
