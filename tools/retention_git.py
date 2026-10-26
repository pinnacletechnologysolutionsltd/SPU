"""Read-only Git state checks for independently recoverable packages."""
from __future__ import annotations

import base64
import os
import subprocess
from pathlib import Path
from retention_tree import confined


def git(root: Path, *args: str) -> bytes:
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    return subprocess.run(
        ['git', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false',
         '-c', 'core.hooksPath=/dev/null', '-C', str(root), *args],
        env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=20).stdout


def states(root: Path, entries: dict) -> dict:
    result = {}
    for name, entry in sorted(entries.items()):
        if Path(name).name != '.git':
            continue
        if entry['type'] not in ('file', 'directory'):
            raise ValueError('Git pointer must be a regular file or directory')
        worktree = (root / name).parent
        if entry['type'] == 'file':
            pointer = (root / name).read_text().rstrip('\n')
            if not pointer.startswith('gitdir: ') or Path(pointer[8:]).is_absolute():
                raise ValueError('Git pointer requires a relative self-contained gitdir')
        admin_paths = {}
        for flag in ('--absolute-git-dir', '--git-common-dir'):
            raw = git(worktree, 'rev-parse', flag).decode().rstrip('\n')
            admin = Path(raw) if Path(raw).is_absolute() else worktree / raw
            admin = confined(admin, root)
            if not admin.is_dir():
                raise ValueError(f'missing Git administration: {name}')
            admin_paths[flag] = admin.relative_to(root.resolve()).as_posix()
            if (admin / 'gitdir').is_file():
                backlink = Path((admin / 'gitdir').read_text().rstrip('\n'))
                if backlink.is_absolute():
                    raise ValueError('absolute Git backlink requires separate migration')
                confined(admin / backlink, root)
            if (admin / 'objects/info/alternates').exists() or (admin / 'objects/info/http-alternates').exists():
                raise ValueError('Git alternates require separate migration')
        actual_top = Path(git(worktree, 'rev-parse', '--show-toplevel').decode().rstrip('\n'))
        if actual_top.resolve() != worktree.resolve():
            raise ValueError('Git worktree identity mismatch')
        config = git(worktree, 'config', '--local', '--no-includes', '--null', '--list')
        for record in config.split(b'\0'):
            key = record.split(b'\n', 1)[0].lower()
            if key.startswith((b'include.', b'includeif.')):
                raise ValueError('Git config includes require separate dependency review')
        git(worktree, 'cat-file', '-e', 'HEAD^{commit}')
        git(worktree, 'fsck', '--full', '--no-reflogs')
        result[worktree.relative_to(root).as_posix()] = {
            'admin_paths': admin_paths,
            'head': git(worktree, 'rev-parse', 'HEAD').decode().strip(),
            'status_z_b64': base64.b64encode(git(
                worktree, 'status', '--porcelain=v1', '-z', '--untracked-files=all')).decode(),
            'index_z_b64': base64.b64encode(git(worktree, 'ls-files', '--stage', '-z')).decode(),
        }
    return result
