#!/usr/bin/env python3
"""RET-1 archive positive and deliberately damaged restoration controls."""
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from retention_archive import package, restore
from retention_tree import digest
from verify_restore import freeze, load_manifest, verify


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        (self.source / 'empty').mkdir()
        (self.source / 'file with spaces').write_bytes(b'exact evidence\x00\xff')
        (self.source / '.hidden').write_text('preserve')
        (self.source / 'link').symlink_to('file with spaces')
        self.pkg = self.base / 'package'
        self.pins = package(self.source, self.pkg)
        self.target = self.base / 'restored'
        restore(self.pkg, self.target, self.pins)
        self.manifest = load_manifest(self.pkg / 'manifest.json', self.pins['manifest_sha256'])

    def test_independent_restore(self):
        self.source.rename(self.base / 'unavailable-source')
        verify(self.target, self.manifest)
        self.assertEqual(os.readlink(self.target / 'link'), 'file with spaces')
        self.assertTrue((self.target / 'empty').is_dir())

    def test_file_controls(self):
        file = self.target / 'file with spaces'
        for content in (b'corruption', b'exact evidencE\x00\xff'):
            with self.subTest(content=content):
                file.write_bytes(content)
                with self.assertRaises(ValueError):
                    verify(self.target, self.manifest)
        file.unlink()
        with self.assertRaises(ValueError):
            verify(self.target, self.manifest)

    def test_directory_and_link_sets(self):
        for kind in ('directory', 'symlink', 'file'):
            extra = self.target / 'extra'
            with self.subTest(extra=kind):
                if kind == 'directory':
                    extra.mkdir()
                elif kind == 'symlink':
                    extra.symlink_to('.hidden')
                else:
                    extra.write_text('extra')
                with self.assertRaises(ValueError):
                    verify(self.target, self.manifest)
                extra.rmdir() if kind == 'directory' else extra.unlink()
        (self.target / 'empty').rmdir()
        with self.assertRaises(ValueError):
            verify(self.target, self.manifest)
        (self.target / 'empty').mkdir()
        (self.target / 'link').unlink()
        with self.assertRaises(ValueError):
            verify(self.target, self.manifest)
        (self.target / 'link').symlink_to('.hidden')
        with self.assertRaises(ValueError):
            verify(self.target, self.manifest)

    def test_mode_and_type(self):
        (self.target / '.hidden').chmod(0o700)
        with self.assertRaises(ValueError):
            verify(self.target, self.manifest)
        (self.target / '.hidden').unlink()
        (self.target / '.hidden').mkdir()
        with self.assertRaises(ValueError):
            verify(self.target, self.manifest)

    def test_unsupported_links_special_files_and_names(self):
        for link in (str(self.source / '.hidden'), str(self.base / 'outside'), '../outside'):
            with self.subTest(link=link):
                (self.target / 'link').unlink()
                (self.target / 'link').symlink_to(link)
                with self.assertRaises(ValueError):
                    freeze(self.target)
                self.assertEqual(os.readlink(self.target / 'link'), link)
        (self.target / 'link').unlink()
        bad = self.target / 'bad\nname'
        bad.touch()
        with self.assertRaises(ValueError):
            freeze(self.target)
        bad.unlink()
        os.mkfifo(self.target / 'fifo')
        with self.assertRaises(ValueError):
            freeze(self.target)

    def test_digest_and_output_refusal(self):
        with self.assertRaises(ValueError):
            load_manifest(self.pkg / 'manifest.json', '0' * 64)
        with self.assertRaises(ValueError):
            restore(self.pkg, self.target, self.pins)
        with self.assertRaises(FileExistsError):
            package(self.source, self.pkg)
        with (self.pkg / 'payload.tar').open('ab') as stream:
            stream.write(b'corrupt')
        with self.assertRaises(ValueError):
            restore(self.pkg, self.base / 'bad', self.pins)

    def test_archive_member_attacks(self):
        for name, kind in (('../escape', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
                           ('.hidden', tarfile.REGTYPE), ('extra', tarfile.LNKTYPE)):
            with self.subTest(name=name, kind=kind):
                package_dir = self.base / ('attack' + str(len(list(self.base.iterdir()))))
                pins = package(self.source, package_dir)
                with tarfile.open(package_dir / 'payload.tar', 'a') as archive:
                    info = tarfile.TarInfo(name)
                    info.type = kind
                    archive.addfile(info)
                pins['archive_sha256'] = digest(package_dir / 'payload.tar')
                with self.assertRaises(ValueError):
                    restore(package_dir, self.base / 'attack-restore', pins)
                self.assertFalse((self.base / 'escape').exists())

    def test_duplicate_manifest_keys(self):
        path = self.base / 'duplicate.json'
        path.write_text('{"format":"spu_retention_tree_v1","entries":{},"entries":{},"git":{}}')
        with self.assertRaises(ValueError):
            load_manifest(path, digest(path))


if __name__ == '__main__':
    unittest.main(verbosity=2)
