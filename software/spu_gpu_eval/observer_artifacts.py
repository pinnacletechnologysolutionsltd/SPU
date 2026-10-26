"""Atomic artifact writer for the GPU-SOM-0A observation sidecar."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import packet
from .device_model import prepare_scene, render_rgb8
from .observer import (PIXEL_CAPACITY, TILE_CAPACITY, TILE_SIZE, TILES_X, ObserverError,
                       _json_bytes, extract_tile_features)
from .scene import HEIGHT, PROFILE, WIDTH, Scene, parse_scene_bytes

ROOT = Path(__file__).resolve().parents[2]
PPM_HEADER = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
SOURCE_FILES = (
    "software/spu_gpu_eval/__init__.py", "software/spu_gpu_eval/scene.py",
    "software/spu_gpu_eval/packet.py", "software/spu_gpu_eval/device_packet.py",
    "software/spu_gpu_eval/device_arithmetic.py", "software/spu_gpu_eval/device_model.py",
    "software/spu_gpu_eval/device_preview.py", "software/spu_gpu_eval/observer.py",
    "software/spu_gpu_eval/observer_artifacts.py", "software/spu_gpu_eval/cli.py",
)
FIXTURE_FILES = (
    "examples/gpu/t1d_two_triangle.json",
    "examples/gpu/t1d_two_triangle_vertex_b.json",
    "fixtures/gpu_t1d_scene_reference.json",
)


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _output_target(out_dir: str | Path) -> Path:
    base = (ROOT / "build/gpu_evaluation/gpu_som_0a").resolve()
    candidate = Path(out_dir)
    target = candidate if candidate.is_absolute() else ROOT / candidate
    target = Path(os.path.abspath(target))
    if target == base or base not in target.parents:
        raise ObserverError("--out must name a new directory under build/gpu_evaluation/gpu_som_0a")
    if target.exists() or target.is_symlink():
        raise ObserverError(f"output path already exists: {target.name}")
    return target


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _rename_noreplace(source: Path, target: Path) -> None:
    """Atomically publish a directory without replacing a concurrent target."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise ObserverError("atomic no-replace directory publication is unavailable")
    renameat2.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                          ctypes.c_uint)
    renameat2.restype = ctypes.c_int
    result = renameat2(-100, os.fsencode(source), -100, os.fsencode(target), 1)
    if result == 0:
        return
    error = ctypes.get_errno()
    if error == errno.EEXIST:
        raise ObserverError(f"output path appeared during generation: {target.name}")
    raise OSError(error, os.strerror(error), str(target))


def _build_artifacts(raw: bytes, scene: Scene) -> dict[str, bytes]:
    # Snapshot provenance before feature extraction begins.
    source_hashes = {path: _hash((ROOT / path).read_bytes()) for path in SOURCE_FILES}
    fixture_hashes = {path: _hash((ROOT / path).read_bytes()) for path in FIXTURE_FILES}
    packet_bytes = packet.compile_packet(scene)
    prepared = prepare_scene(packet_bytes)
    preview = PPM_HEADER + render_rgb8(prepared)
    features = extract_tile_features(prepared)
    manifest = {
        "format": "spu_gpu_som_0a_manifest_v1", "profile": PROFILE,
        "repository_head": _git("rev-parse", "HEAD"),
        "repository_worktree": "dirty" if _git("status", "--porcelain") else "clean",
        "input_scene_sha256": _hash(raw), "source_sha256": source_hashes,
        "fixture_sha256": fixture_hashes, "scene_packet_sha256": _hash(packet_bytes),
        "tile_features_sha256": _hash(features), "device_preview_sha256": _hash(preview),
        "tile_size": TILE_SIZE, "tile_records": TILE_CAPACITY,
        "pixel_decisions": PIXEL_CAPACITY, "device_model": True,
        "physical_observation": False, "cycle_timing_model": False,
    }
    artifacts = {"scene_packet.bin": packet_bytes, "device_preview.ppm": preview,
                 "tile_features.json": features, "manifest.json": _json_bytes(manifest)}
    _validate_artifacts(artifacts)
    return artifacts


def _validate_artifacts(artifacts: dict[str, bytes]) -> None:
    expected_files = {"scene_packet.bin", "device_preview.ppm", "tile_features.json", "manifest.json"}
    if set(artifacts) != expected_files:
        raise ObserverError("artifact set is incomplete or contains unexpected files")
    manifest = json.loads(artifacts["manifest.json"])
    for filename, field in (("scene_packet.bin", "scene_packet_sha256"),
                            ("tile_features.json", "tile_features_sha256"),
                            ("device_preview.ppm", "device_preview_sha256")):
        if _hash(artifacts[filename]) != manifest[field]:
            raise ObserverError(f"{filename} hash does not match manifest")
    features = json.loads(artifacts["tile_features.json"])
    if (manifest.get("tile_records") != TILE_CAPACITY
            or manifest.get("pixel_decisions") != PIXEL_CAPACITY
            or manifest.get("tile_size") != TILE_SIZE
            or len(features["tiles"]) != TILE_CAPACITY
            or sum(tile["sample_count"] for tile in features["tiles"]) != PIXEL_CAPACITY
            or features["pixel_decisions"] != PIXEL_CAPACITY):
        raise ObserverError("feature artifact is incomplete")
    for index, tile in enumerate(features["tiles"]):
        expected_origin = ((index % TILES_X) * TILE_SIZE, (index // TILES_X) * TILE_SIZE)
        if (tile["tile_x"], tile["tile_y"]) != expected_origin:
            raise ObserverError("tile order or coordinates are inconsistent")
        if sum(tile["coverage_counts"].values()) != TILE_SIZE * TILE_SIZE:
            raise ObserverError("tile coverage counts are inconsistent")
        if sum(entry["count"] for entry in tile["rgb444_histogram"]) != TILE_SIZE * TILE_SIZE:
            raise ObserverError("tile RGB histogram is inconsistent")


def write_observation(scene_path: str | Path, out_dir: str | Path) -> Path:
    source = Path(scene_path)
    if not source.is_absolute():
        source = Path.cwd() / source
    raw = source.read_bytes()
    scene = parse_scene_bytes(raw)
    target = _output_target(out_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".gpu_som_0a_stage_", dir=target.parent))
    try:
        artifacts = _build_artifacts(raw, scene)
        for name, content in artifacts.items():
            (stage / name).write_bytes(content)
        written = {path.name: path.read_bytes() for path in stage.iterdir() if path.is_file()}
        if written != artifacts:
            raise ObserverError("staged artifact readback differs from validated artifacts")
        _validate_artifacts(written)
        _rename_noreplace(stage, target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return target
