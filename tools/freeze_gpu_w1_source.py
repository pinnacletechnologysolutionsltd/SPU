#!/usr/bin/env python3
"""Create a deterministic, content-addressed source bundle for GPU-W1."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import sys


ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "software/tests/test_gpu_scene_compiler_s1.py",
    "software/tests/test_gpu_device_model_s2.py",
    "software/tests/test_gpu_pixel_inspect_s3.py",
    "software/tests/test_gpu_quadray_covariance_scene.py",
    "software/tests/test_gpu_workbench_w1.py",
    "software/tests/test_gpu_workbench_w1c.py",
)
FIXTURES = (
    "fixtures/gpu_t1d_scene_reference.json",
    "fixtures/gpu_t1d_scene_wire_64b.bin",
    "fixtures/golden_core_quadray_projection_reference.json",
    "fixtures/golden_core_t1d_tetra_views_reference.json",
    "fixtures/gpu_scene_diversity_reference.json",
    "fixtures/gpu_workbench_w1_scene_catalog.json",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _source_paths() -> list[str]:
    paths = {path.relative_to(ROOT).as_posix()
             for path in (ROOT / "software/spu_gpu_eval").glob("*.py")}
    paths.update(TESTS)
    paths.update(FIXTURES)
    paths.add("software/lib/gc2b_weighted_cycle.py")
    paths.add("spu_strategy/contract_gpu_w1a_inventory_2026-10-17.md")
    paths.add("spu_strategy/contract_gpu_w1c_local_viewer_2026-10-17.md")
    paths.add("software/spu_gpu_eval/viewer.html")
    paths.add("tools/freeze_gpu_w1_source.py")
    for directory in ("examples/gpu", "hardware/rtl/gpu"):
        paths.update(path.relative_to(ROOT).as_posix()
                     for path in (ROOT / directory).rglob("*") if path.is_file())
    paths.update(("hardware/rtl/arch/gpu_reciprocal_lut_q15.mem",
                  "hardware/rtl/hal/hal_vga.v"))
    missing = sorted(path for path in paths if not (ROOT / path).is_file())
    if missing:
        raise SystemExit("missing source snapshot inputs: " + ", ".join(missing))
    return sorted(paths)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 tools/freeze_gpu_w1_source.py <new-output-dir>")
    output = Path(sys.argv[1])
    if not output.is_absolute():
        output = ROOT / output
    base = (ROOT / "build/gpu_evaluation").resolve()
    output = output.resolve()
    if output == base or base not in output.parents or output.exists():
        raise SystemExit("output must be a new directory under build/gpu_evaluation")
    paths = _source_paths()
    members = [(path, (ROOT / path).read_bytes()) for path in paths]
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, data in members:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
    payload = stream.getvalue()
    digest = _sha(payload)
    output.mkdir(parents=True)
    archive_path = output / f"gpu_w1_source_{digest}.tar"
    archive_path.write_bytes(payload)
    manifest = {
        "format": "spu_gpu_w1_source_snapshot_v1",
        "archive": archive_path.name,
        "archive_sha256": digest,
        "base_commit": _git("rev-parse", "HEAD"),
        "base_worktree": "dirty" if _git("status", "--porcelain") else "clean",
        "python": sys.version.split()[0],
        "files": {name: _sha(data) for name, data in members},
        "reproduction": [
            "git checkout --detach <base_commit>",
            f"sha256sum {archive_path.name}",
            f"tar -xf {archive_path.name} -C <checkout-root>",
            "python3 software/tests/test_gpu_scene_compiler_s1.py",
            "python3 software/tests/test_gpu_device_model_s2.py",
            "python3 software/tests/test_gpu_pixel_inspect_s3.py",
            "python3 software/tests/test_gpu_workbench_w1.py",
            "python3 software/tests/test_gpu_workbench_w1c.py",
        ],
    }
    (output / f"gpu_w1_source_{digest}.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"archive={archive_path.relative_to(ROOT)}")
    print(f"sha256={digest}")
    print(f"files={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
