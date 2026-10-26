"""Conservative explicit-path dependency graph; omissions remain protected."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from retention_paths import references

TEXT_SUFFIXES = {'.json', '.md', '.txt', '.log', '.py', '.sh', '.yaml', '.yml'}
TEXT_LIMIT = 2 * 1024 * 1024


def dependency_graph(repo: Path, build_records: list[dict], input_paths=None) -> dict:
    if input_paths is not None:
        inputs = {repo / name for name in input_paths}
    else:
        inputs = {repo / row['path'] for row in build_records
                  if row['type'] == 'file' and Path(row['path']).suffix in TEXT_SUFFIXES}
        for name in ('docs', 'research', 'spu_strategy', 'tools'):
            for base, dirs, files in os.walk(repo / name, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
                inputs.update(Path(base) / f for f in files if Path(f).suffix in TEXT_SUFFIXES)
    edges, inspected, skipped = [], [], []
    for path in sorted(inputs):
        name = path.relative_to(repo).as_posix()
        if not path.resolve().is_relative_to(repo.resolve()):
            skipped.append({'path': name, 'reason': 'input escapes repository'})
            continue
        if not path.exists():
            skipped.append({'path': name, 'reason': 'input missing'})
            continue
        if path.is_symlink() or path.stat().st_size > TEXT_LIMIT:
            skipped.append({'path': name, 'reason': 'symlink or exceeds 2 MiB content limit'})
            continue
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
        identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        if identity(before) != identity(after):
            skipped.append({'path': name, 'reason': 'input changed during read'})
            continue
        if len(raw) > TEXT_LIMIT:
            skipped.append({'path': name, 'reason': 'grew beyond content limit'})
            continue
        try:
            text = raw.decode('utf-8')
        except UnicodeError:
            skipped.append({'path': name, 'reason': 'not UTF-8 text'})
            continue
        inspected.append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest()})
        targets = references(repo, text)
        for target in sorted(targets):
            destination = repo / target
            if '..' in Path(target).parts:
                resolution = 'unsafe_or_ambiguous'
            elif not destination.exists() and not destination.is_symlink():
                resolution = 'missing_or_pattern'
            elif destination.is_symlink():
                resolution = 'symlink_requires_review'
            else:
                resolution = 'exists'
            edges.append({'from': name, 'to': target, 'resolution': resolution,
                          'kind': 'explicit_text_reference; semantic review required'})
    return {'format': 'spu_retention_dependencies_v2', 'complete': False,
            'normalization': 'known-root absolute, repo-relative and dot-relative; external absolute excluded',
            'fixed_input_set': input_paths is not None,
            'scope': 'bounded UTF-8 text in Surd tree, docs, research, strategy and tools',
            'limitations': ['source-local and dynamically constructed paths need manual review',
                            'external absolute paths and whitespace within artifact names are not inferred',
                            'references may describe history or commands, not acceptance dependencies',
                            'absence of an edge never establishes disposability',
                            'other build campaigns and binary contents are not scanned',
                            'live metadata/content scan is not a quiescent source freeze'],
            'inputs': inspected, 'skipped_inputs': skipped, 'edges': edges}
