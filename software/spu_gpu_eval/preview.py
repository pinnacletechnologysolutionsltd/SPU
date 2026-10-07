"""Deterministic PPM preview and source-bound experiment artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import packet, reference, scene as scene_module
from .scene import HEIGHT, WIDTH, Scene, parse_scene_bytes


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REFERENCE = ROOT / "fixtures" / "gpu_t1d_scene_reference.json"
PROFILE_SOURCES = (
    "hardware/rtl/gpu/spu_scene_loader.v",
    "hardware/rtl/gpu/spu_scene_unpack.v",
    "hardware/rtl/gpu/spu_scene_profile_unpack.v",
    "hardware/rtl/gpu/spu_edge_stepper.v",
    "hardware/rtl/gpu/spu_depth_math.v",
    "hardware/rtl/gpu/spu_reciprocal_core.v",
    "hardware/rtl/gpu/spu_attr_stepper.v",
    "hardware/rtl/gpu/spu_depth_compare.v",
)
MODULE_SOURCES = (
    "software/spu_gpu_eval/__init__.py",
    "software/spu_gpu_eval/scene.py",
    "software/spu_gpu_eval/packet.py",
    "software/spu_gpu_eval/reference.py",
    "software/spu_gpu_eval/preview.py",
    "software/spu_gpu_eval/cli.py",
)
PPM_HEADER = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")


class PreviewError(ValueError):
    """Raised for invalid preview output paths or I/O failures."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def _sample_document(scene: Scene) -> bytes:
    frozen = json.loads(FIXTURE_REFERENCE.read_text(encoding="utf-8"))
    expectations = list(frozen["diagnostic_pixels"])
    expectations.append({
        "x": 320, "y": 0, "coverage": "overlap", "near": "tie_triangle0", "rgb": [15, 0, 0]
    })
    samples = []
    for baseline in expectations:
        actual = reference.pixel_decision(scene, baseline["x"], baseline["y"])
        samples.append({
            "baseline_fixture_expectation": baseline,
            "actual_scene_decision": actual,
        })
    return _json_bytes({
        "format": "spu_gpu_pixel_decisions_v1",
        "expectation_scope": "frozen baseline fixture; actual values describe the input scene",
        "samples": samples,
    })


def build_artifacts(scene_raw: bytes, scene: Scene) -> dict[str, bytes]:
    packet_bytes = packet.compile_packet(scene)
    ppm = PPM_HEADER + reference.render_rgb8(scene)
    decisions = _sample_document(scene)
    source_hashes = {
        path: _sha256((ROOT / path).read_bytes()) for path in MODULE_SOURCES
    }
    profile_hashes = {
        path: _sha256((ROOT / path).read_bytes()) for path in PROFILE_SOURCES
    }
    dirty = bool(_git_value("status", "--porcelain"))
    manifest = {
        "format": "spu_gpu_scene_preview_manifest_v1",
        "profile": scene_module.PROFILE,
        "schema": scene_module.FORMAT,
        "repository_head": _git_value("rev-parse", "HEAD"),
        "repository_worktree": "dirty" if dirty else "clean",
        "input_scene_sha256": _sha256(scene_raw),
        "reference_fixture_sha256": _sha256(FIXTURE_REFERENCE.read_bytes()),
        "compiler_reference_source_sha256": source_hashes,
        "profile_source_sha256": profile_hashes,
        "packet_sha256": _sha256(packet_bytes),
        "preview_sha256": _sha256(ppm),
        "device_model": False,
        "physical_observation": False,
    }
    return {
        "scene_packet.bin": packet_bytes,
        "preview.ppm": ppm,
        "pixel_decisions.json": decisions,
        "manifest.json": _json_bytes(manifest),
    }


def _output_target(out_dir: str | Path) -> Path:
    base = (ROOT / "build" / "gpu_evaluation").resolve()
    candidate = Path(out_dir)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    target = candidate.resolve()
    if target == base or base not in target.parents:
        raise PreviewError("--out must name a new directory under build/gpu_evaluation")
    if target.exists() or target.is_symlink():
        raise PreviewError(f"output path already exists: {target.name}")
    return target


def write_preview(scene_path: str | Path, out_dir: str | Path) -> Path:
    source = Path(scene_path)
    if not source.is_absolute():
        source = Path.cwd() / source
    try:
        scene_raw = source.read_bytes()
        parsed = parse_scene_bytes(scene_raw)
    except (OSError, scene_module.SceneError) as exc:
        raise PreviewError(str(exc)) from exc

    target = _output_target(out_dir)
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".s1_preview_", dir=parent))
    try:
        for name, data in build_artifacts(scene_raw, parsed).items():
            (stage / name).write_bytes(data)
        if target.exists() or target.is_symlink():
            raise PreviewError(f"output path appeared during generation: {target.name}")
        os.rename(stage, target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return target
