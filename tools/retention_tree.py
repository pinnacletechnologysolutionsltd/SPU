"""Exact, non-following inventory for self-contained RET-1 packages."""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path, PurePosixPath


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def member_path(name: str) -> str:
    if (not isinstance(name, str) or not name or name.startswith('/')
            or any(part in ('', '.', '..') for part in name.split('/'))
            or any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in name)):
        raise ValueError(f'unsupported member path: {name!r}')
    return PurePosixPath(name).as_posix()


def confined(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f'external dependency: {path}')
    return resolved


def scan(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir():
        raise ValueError('tree root must be a real directory')
    entries = {}

    def visit(directory: Path) -> None:
        for path in sorted(directory.iterdir()):
            name = member_path(path.relative_to(root).as_posix())
            info = path.lstat()
            row = {'mode': stat.S_IMODE(info.st_mode)}
            if stat.S_ISLNK(info.st_mode):
                target = os.readlink(path)
                if Path(target).is_absolute():
                    raise ValueError(f'absolute link requires separate migration: {name}')
                confined(path, root)
                row.update(type='symlink', target=target)
            elif stat.S_ISDIR(info.st_mode):
                row.update(type='directory')
            elif stat.S_ISREG(info.st_mode):
                row.update(type='file', size=info.st_size, sha256=digest(path))
                after = path.lstat()
                if (info.st_ino, info.st_dev, info.st_size, info.st_mtime_ns, info.st_ctime_ns) != (
                        after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    raise ValueError(f'file changed during scan: {name}')
            else:
                raise ValueError(f'unsupported special file: {name}')
            entries[name] = row
            if row['type'] == 'directory':
                visit(path)

    visit(root)
    return entries
