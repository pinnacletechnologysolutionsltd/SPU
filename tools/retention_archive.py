"""Create and restore strict RET-1 archives; never prune or overwrite."""
from __future__ import annotations

import json
import os
import tarfile
from pathlib import Path
from retention_tree import digest, member_path
from verify_restore import freeze, load_manifest, verify


def package(source: Path, output: Path) -> dict:
    if output.resolve().is_relative_to(source.resolve()):
        raise ValueError('package output must be outside source')
    manifest = freeze(source)
    output.mkdir(parents=True, exist_ok=False)
    manifest_path = output / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    archive_path = output / 'payload.tar'
    with tarfile.open(archive_path, 'w', dereference=True) as archive:
        for name in sorted(manifest['entries']):
            path = source / name
            # gettarinfo with dereference would follow links; provide their exact type.
            info = tarfile.TarInfo(name)
            row = manifest['entries'][name]
            info.mode = row['mode']
            if row['type'] == 'directory':
                info.type = tarfile.DIRTYPE
            elif row['type'] == 'symlink':
                info.type = tarfile.SYMTYPE
                info.linkname = row['target']
            else:
                info.size = row['size']
            if row['type'] == 'file':
                with path.open('rb') as stream:
                    archive.addfile(info, stream)
            else:
                archive.addfile(info)
    verify(source, manifest)
    result = {'manifest_sha256': digest(manifest_path), 'archive_sha256': digest(archive_path)}
    (output / 'SHA256.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def restore(package_dir: Path, destination: Path, pins: dict) -> None:
    archive_path = package_dir / 'payload.tar'
    manifest = load_manifest(package_dir / 'manifest.json', pins['manifest_sha256'])
    if digest(archive_path) != pins['archive_sha256']:
        raise ValueError('archive digest mismatch')
    if destination.exists() or destination.is_symlink():
        raise ValueError('restore destination already exists')
    with tarfile.open(archive_path, 'r:') as archive:
        members = archive.getmembers()
        names = [member_path(m.name.rstrip('/') if m.isdir() else m.name) for m in members]
        if len(set(names)) != len(names) or set(names) != set(manifest['entries']):
            raise ValueError('archive member set mismatch or duplicates')
        for name, member in zip(names, members):
            row = manifest['entries'][name]
            kind = 'file' if member.isfile() else 'directory' if member.isdir() else 'symlink' if member.issym() else 'unsupported'
            if kind != row['type'] or member.mode != row['mode']:
                raise ValueError(f'archive type/mode mismatch: {name}')
            if kind == 'symlink' and member.linkname != row['target']:
                raise ValueError(f'archive link mismatch: {name}')
            if kind == 'file' and member.size != row['size']:
                raise ValueError(f'archive size mismatch: {name}')
            parent = Path(name).parent
            while parent != Path('.'):
                if manifest['entries'].get(parent.as_posix(), {}).get('type') != 'directory':
                    raise ValueError('member parent must be a declared real directory')
                parent = parent.parent
        destination.mkdir(parents=True, exist_ok=False)
        # Directories first, files second, links last: no extraction through links.
        for kind in ('directory', 'file', 'symlink'):
            for name, member in sorted(zip(names, members), key=lambda item: item[0]):
                row = manifest['entries'][name]
                if row['type'] != kind:
                    continue
                target = destination / name
                if kind == 'directory':
                    target.mkdir()
                elif kind == 'file':
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise ValueError('missing archive stream')
                    with stream, target.open('xb') as output:
                        while chunk := stream.read(1024 * 1024):
                            output.write(chunk)
                else:
                    os.symlink(row['target'], target)
        verify_modes = sorted(manifest['entries'], key=lambda n: (-n.count('/'), n))
        for name in verify_modes:
            row = manifest['entries'][name]
            if row['type'] != 'symlink':
                os.chmod(destination / name, row['mode'])
    verify(destination, manifest)
