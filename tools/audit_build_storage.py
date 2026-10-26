#!/usr/bin/env python3
"""RET-1 read-only Surd allocation/dependency review; no deletion interface."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import subprocess
from retention_dependencies import dependency_graph


def metadata(repo: Path, root: Path) -> list[dict]:
    records = []
    for base, dirs, files in os.walk(root, followlinks=False,
                                     onerror=lambda error: (_ for _ in ()).throw(error)):
        for name in sorted(dirs + files):
            path = Path(base) / name
            info = path.lstat()
            kind = ('symlink' if stat.S_ISLNK(info.st_mode) else 'directory'
                    if stat.S_ISDIR(info.st_mode) else 'file' if stat.S_ISREG(info.st_mode) else 'special')
            records.append({'path': path.relative_to(repo).as_posix(), 'type': kind,
                            'apparent_bytes': info.st_size, 'allocated_bytes': info.st_blocks * 512,
                            'device': info.st_dev, 'inode': info.st_ino, 'nlink': info.st_nlink,
                            'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns})
        dirs[:] = [name for name in dirs if not (Path(base) / name).is_symlink()]
    return records


def summarize(records: list[dict]) -> dict:
    regular = [row for row in records if row['type'] == 'file']
    inodes = {(row['device'], row['inode']): row for row in regular}
    counts = Counter((row['device'], row['inode']) for row in regular)
    return {'regular_file_count': len(regular),
            'apparent_bytes_by_path': sum(row['apparent_bytes'] for row in regular),
            'allocated_bytes_unique_regular_inodes': sum(row['allocated_bytes'] for row in inodes.values()),
            'allocated_bytes_unique_all_inodes': sum(row['allocated_bytes'] for row in
                {(r['device'], r['inode']): r for r in records}.values()),
            'hardlinked_inode_count': sum(row['nlink'] > 1 for row in inodes.values()),
            'inodes_with_links_outside_scope': sum(row['nlink'] > counts[key] for key, row in inodes.items()),
            'reclaimable_bytes': None,
            'note': 'st_blocks counts allocation, not guaranteed release; reflinks/snapshots may share extents'}


def audit(repo: Path, output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise ValueError('output must be fresh')
    parent = repo / 'build/repository_cleanup'
    if not output.resolve().is_relative_to(parent.resolve()) or output.resolve() == parent.resolve():
        raise ValueError('output must be a new child of build/repository_cleanup')
    root = repo / 'build/spu_surd_register'
    records = metadata(repo, root)
    graph = dependency_graph(repo, records)
    groups = defaultdict(list)
    for row in records:
        relative = Path(row['path']).relative_to('build/spu_surd_register')
        groups[str(Path('build/spu_surd_register') / Path(*relative.parts[:2]))].append(row)
    protected = []
    for path, rows in sorted(groups.items()):
        markers = [r['path'] for r in rows if Path(r['path']).name in ('COMPLETE', 'FAILED', 'TIMEOUT')]
        protected.append({'path': path, 'outcome': 'PROTECT', 'protected': True,
                          'measurements': summarize(rows), 'terminal_marker_paths': markers,
                          'reason': 'mixed or unresolved evidence; graph incomplete; no quiescence/copy qualification',
                          'archive_uri': None, 'archive_sha256': None,
                          'restoration_qualified': False, 'owner_deletion_approval': None})
    result = {'format': 'spu_retention_manifest_v1', 'scanned_at_utc': datetime.now(timezone.utc).isoformat(),
              'scope': str(root), 'measurements': summarize(records),
              'allowed_outcomes': ['PROTECT', 'ARCHIVE_THEN_REVIEW', 'ELIGIBLE_FOR_APPROVAL'],
              'outcome_counts': {'PROTECT': len(protected), 'ARCHIVE_THEN_REVIEW': 0, 'ELIGIBLE_FOR_APPROVAL': 0},
              'cleanup_authorized': False, 'approved_deletions': [], 'approved_reclamation_bytes': 0,
              'verified_reclamation_estimate_bytes': None, 'entries': protected}
    output.mkdir(parents=True, exist_ok=False)
    for name, value in [('file_metadata.json', records), ('dependency_graph.json', graph),
                        ('retention_manifest.json', result)]:
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    command = ['btrfs', 'filesystem', 'du', '--raw', '-s', str(root)]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=300)
        allocation = {'command': command, 'exit_code': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        allocation = {'command': command, 'unavailable': str(error)}
    (output / 'btrfs_allocation.json').write_text(json.dumps(allocation, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'measurements': result['measurements'],
                      'outcome_counts': result['outcome_counts'], 'dependency_edges': len(graph['edges'])}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    audit(repo, args.out.absolute())


if __name__ == '__main__':
    main()
