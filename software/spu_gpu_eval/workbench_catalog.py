"""Frozen, hash-checked scene allowlist for GPU-W1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "fixtures/gpu_workbench_w1_scene_catalog.json"
FORMAT = "spu_gpu_workbench_scene_catalog_v1"


class CatalogError(ValueError):
    """Raised when a catalogue or frozen scene fails validation."""


def load_catalog() -> tuple[dict[str, str], ...]:
    try:
        raw = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot read scene catalogue: {exc}") from exc
    if (not isinstance(raw, dict)
            or set(raw) != {"format", "profile", "scenes"}
            or raw.get("format") != FORMAT):
        raise CatalogError("unsupported scene catalogue format")
    if raw.get("profile") != "t1d-two-triangle-v1" or not isinstance(raw.get("scenes"), list):
        raise CatalogError("unsupported scene catalogue profile")
    entries = []
    seen = set()
    for entry in raw["scenes"]:
        if not isinstance(entry, dict) or set(entry) != {"id", "path", "sha256", "group"}:
            raise CatalogError("invalid scene catalogue entry")
        scene_id, relative = entry["id"], entry["path"]
        digest_pin = entry["sha256"]
        group = entry["group"]
        if (not isinstance(scene_id, str) or not scene_id or scene_id in seen
                or not isinstance(relative, str) or not relative
                or Path(relative).is_absolute() or ".." in Path(relative).parts
                or not isinstance(digest_pin, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest_pin) is None
                or not isinstance(group, str) or not group):
            raise CatalogError("invalid or duplicate scene ID/path")
        path = (ROOT / relative).resolve()
        if ROOT not in path.parents:
            raise CatalogError(f"scene path escapes repository: {scene_id}")
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise CatalogError(f"scene is unavailable: {scene_id}") from exc
        digest = hashlib.sha256(data).hexdigest()
        if digest != digest_pin:
            raise CatalogError(f"frozen scene hash mismatch: {scene_id}")
        seen.add(scene_id)
        entries.append({**entry, "absolute_path": str(path)})
    if not entries:
        raise CatalogError("scene catalogue is empty")
    return tuple(entries)


def find_scene(scene_id: str) -> dict[str, str]:
    for entry in load_catalog():
        if entry["id"] == scene_id:
            return entry
    raise CatalogError(f"unknown scene ID: {scene_id}")
