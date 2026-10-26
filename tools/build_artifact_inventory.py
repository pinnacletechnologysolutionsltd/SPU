#!/usr/bin/env python3
"""Create a read-only metadata inventory of build artifacts."""

from __future__ import annotations

import argparse, json, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


MARKERS = {"COMPLETE", "FAILED", "TIMEOUT"}
SNAPSHOT_DIRS = {"checkout", "clean_checkout", "worktree", "worktrees"}
LIMIT = 100


def fail_io(error: OSError) -> None:
    raise error


def inventory(root: Path) -> dict[str, object]:
    totals = Counter()
    extensions: Counter[str] = Counter()
    markers: Counter[str] = Counter()
    top: dict[str, dict[str, object]] = {}
    largest: list[tuple[int, str]] = []
    same_name_size: dict[tuple[str, int], list[str]] = defaultdict(list)
    git_paths: list[str] = []
    snapshot_paths: list[str] = []

    def bucket(relative: Path) -> dict[str, object]:
        name = relative.parts[0] if relative.parts else "."
        if name not in top:
            top[name] = {"regular_file_count": 0, "apparent_bytes": 0,
                         "directory_count": 0, "symlink_count": 0,
                         "result_json_count": 0, "terminal_markers": Counter()}
        return top[name]

    for current, dirs, files in os.walk(root, topdown=True, followlinks=False,
                                        onerror=fail_io):
        base = Path(current)
        rel_base = base.relative_to(root)
        if rel_base.parts:
            totals["directory_count"] += 1
            bucket(rel_base)["directory_count"] += 1
            if base.name == ".git":
                git_paths.append(rel_base.as_posix())
        for name in list(dirs):
            path = base / name
            if path.is_symlink():
                dirs.remove(name)
                totals["symlink_count"] += 1
                bucket(path.relative_to(root))["symlink_count"] += 1
                continue
            if name in SNAPSHOT_DIRS or "worktree" in name.lower() or "checkout" in name.lower():
                snapshot_paths.append(path.relative_to(root).as_posix())
        for name in files:
            path = base / name
            relative = path.relative_to(root)
            if path.is_symlink():
                totals["symlink_count"] += 1
                bucket(relative)["symlink_count"] += 1
                continue
            size = path.stat(follow_symlinks=False).st_size
            item = bucket(relative)
            totals["regular_file_count"] += 1
            totals["apparent_bytes"] += size
            item["regular_file_count"] += 1
            item["apparent_bytes"] += size
            extension = path.suffix.lower() or "[no extension]"
            extensions[extension] += 1
            if name == "result.json":
                totals["result_json_count"] += 1
                item["result_json_count"] += 1
            if name in MARKERS:
                markers[name] += 1
                item["terminal_markers"][name] += 1
            if name == ".git":
                git_paths.append(relative.as_posix())
            largest.append((size, relative.as_posix()))
            same_name_size[(name, size)].append(relative.as_posix())

    candidates = [
        {"basename": name, "apparent_bytes": size, "path_count": len(paths),
         "sample_paths": sorted(paths)[:12], "content_hash_checked": False}
        for (name, size), paths in same_name_size.items() if len(paths) > 1
    ]
    candidates.sort(key=lambda row: (-row["path_count"] * row["apparent_bytes"],
                                     row["basename"], row["apparent_bytes"]))
    clean_top = {}
    for name, row in sorted(top.items()):
        clean_top[name] = {**row, "terminal_markers": dict(sorted(row["terminal_markers"].items()))}
    return {
        "format": "spu_build_artifact_inventory_v1",
        "scanned_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "regular_file_count": totals["regular_file_count"],
        "directory_count": totals["directory_count"],
        "symlink_count": totals["symlink_count"],
        "apparent_bytes": totals["apparent_bytes"],
        "result_json_count": totals["result_json_count"],
        "terminal_markers": dict(sorted(markers.items())),
        "git_metadata_paths": sorted(git_paths),
        "git_metadata_count": len(git_paths),
        "snapshot_directory_paths": sorted(snapshot_paths),
        "snapshot_directory_count": len(snapshot_paths),
        "extension_counts": dict(sorted(extensions.items())),
        "top_level": clean_top,
        "largest_files": [
            {"apparent_bytes": size, "path": path}
            for size, path in sorted(largest, reverse=True)[:LIMIT]
        ],
        "same_name_size_review_candidates": candidates[:LIMIT],
        "same_name_size_candidate_group_count": len(candidates),
        "same_name_size_candidate_groups_truncated": len(candidates) > LIMIT,
        "content_hashes_computed": False,
        "cleanup_authorized": False,
        "review_note": "Metadata only. Check contracts, evidence references, active worktrees, and generators before any disposition.",
        "scan_errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="existing build tree to inventory")
    parser.add_argument("--out", required=True, type=Path, help="new report directory under build/repository_cleanup")
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        cleanup_root = (root / "repository_cleanup").resolve(strict=True)
        output = args.out.resolve(strict=False)
        if not root.is_dir() or not cleanup_root.is_dir():
            raise ValueError("--root and its repository_cleanup directory must exist")
        if cleanup_root not in output.parents:
            raise ValueError("--out must be a new child of <root>/repository_cleanup")
        if output.exists() or args.out.is_symlink():
            raise ValueError("--out already exists; choose a fresh report directory")
        report = inventory(root)
        encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
        output.mkdir(parents=True, exist_ok=False)
        (output / "inventory.json").write_bytes(encoded)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"inventory written to {output / 'inventory.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
