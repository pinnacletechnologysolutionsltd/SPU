"""No-replace atomic directory publication for scene-diversity artifacts."""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
import tempfile
from pathlib import Path

from .scene_diversity import SceneDiversityError


def rename_noreplace(source: Path, target: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise SceneDiversityError("atomic no-replace directory publication is unavailable")
    renameat2.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                          ctypes.c_uint)
    renameat2.restype = ctypes.c_int
    if renameat2(-100, os.fsencode(source), -100, os.fsencode(target), 1) == 0:
        return
    error = ctypes.get_errno()
    if error == errno.EEXIST:
        raise SceneDiversityError("output path appeared during generation")
    raise OSError(error, os.strerror(error), str(target))


def publish(target: Path, artifacts: dict[str, bytes]) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        raise SceneDiversityError(f"output path already exists: {target}")
    stage = Path(tempfile.mkdtemp(prefix=".scene_diversity_stage_", dir=target.parent))
    try:
        for name, content in artifacts.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        for name, content in artifacts.items():
            if (stage / name).read_bytes() != content:
                raise SceneDiversityError("staged artifact readback mismatch")
        rename_noreplace(stage, target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return target
