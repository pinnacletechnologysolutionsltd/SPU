#!/usr/bin/env python3
"""Verify a RET-1 JSON manifest against a restored tree without changing it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from retention_git import states
from retention_tree import digest, member_path, scan


FORMAT = 'spu_retention_tree_v1'


def freeze(root: Path) -> dict:
    entries = scan(root)
    state = states(root, entries)
    # Git inspection must not alter the captured tree.
    if scan(root) != entries:
        raise ValueError('tree changed while freezing')
    return {'format': FORMAT, 'entries': entries, 'git': state}


def load_manifest(path: Path, sha256: str) -> dict:
    if digest(path) != sha256:
        raise ValueError('manifest digest mismatch')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    manifest = json.loads(path.read_text(), object_pairs_hook=unique)
    if set(manifest) != {'format', 'entries', 'git'} or manifest['format'] != FORMAT:
        raise ValueError('unsupported manifest format; legacy text is not accepted')
    for name in manifest['entries']:
        member_path(name)
    return manifest


def verify(root: Path, manifest: dict) -> None:
    if manifest.get('format') != FORMAT:
        raise ValueError('unsupported manifest format')
    actual = freeze(root)
    if actual != manifest:
        expected = manifest['entries']
        found = actual['entries']
        changed = sorted(n for n in found.keys() & expected.keys() if found[n] != expected[n])
        raise ValueError(f'restore mismatch: missing={sorted(expected.keys()-found.keys())[:8]}, '
                         f'extra={sorted(found.keys()-expected.keys())[:8]}, '
                         f'changed={changed[:8]}, git_equal={actual["git"] == manifest["git"]}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    try:
        verify(args.root, load_manifest(args.manifest, args.manifest_sha256))
    except Exception as error:
        parser.exit(2, f'FAIL: {error}\n')
    print('PASS: exact tree and Git state parity; self-contained supported links')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
