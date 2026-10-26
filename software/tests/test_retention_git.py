#!/usr/bin/env python3
"""Dirty Git, detached-object and pointer controls for RET-1."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from retention_archive import package, restore
from retention_git import git
from verify_restore import freeze, verify


class GitRestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'source'
        self.repo = self.root / 'repo'
        self.repo.mkdir(parents=True)
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'RET1 fixture')
        git(self.repo, 'config', 'user.email', 'ret1@example.invalid')
        (self.repo / 'tracked').write_text('base')
        (self.repo / '.gitignore').write_text('ignored\n')
        git(self.repo, 'add', '.')
        git(self.repo, '-c', 'commit.gpgsign=false', 'commit', '-qm', 'base')

    def roundtrip(self):
        pins = package(self.root, self.base / 'package')
        restored = self.base / 'restored'
        restore(self.base / 'package', restored, pins)
        return restored

    def test_detached_dirty_staged_untracked_ignored(self):
        git(self.repo, 'checkout', '--detach', '-q')
        (self.repo / 'tracked').write_text('unreachable detached commit')
        git(self.repo, 'commit', '-qam', 'detached')
        (self.repo / 'tracked').write_text('staged-only blob')
        git(self.repo, 'add', 'tracked')
        staged = git(self.repo, 'rev-parse', ':tracked').decode().strip()
        (self.repo / 'tracked').write_text('worktree differs from index')
        (self.repo / 'untracked').write_text('untracked')
        (self.repo / 'ignored').write_text('ignored but retained')
        restored = self.roundtrip()
        expected = freeze(restored)
        self.root.rename(self.base / 'unavailable')
        verify(restored, expected)
        self.assertEqual(git(restored / 'repo', 'show', ':tracked'), b'staged-only blob')
        self.assertEqual((restored / 'repo/ignored').read_text(), 'ignored but retained')
        # A status mismatch must fail even with the tree entries deliberately updated.
        (restored / 'repo/untracked').unlink()
        updated = freeze(restored)
        updated['git'] = expected['git']
        with self.assertRaises(ValueError):
            verify(restored, updated)
        # Staged-only objects are necessary even when unreachable from any commit.
        obj = restored / 'repo/.git/objects' / staged[:2] / staged[2:]
        obj.unlink()
        with self.assertRaises((ValueError, subprocess.CalledProcessError)):
            freeze(restored)

    def test_clean_becoming_dirty(self):
        expected = freeze(self.root)
        (self.repo / 'tracked').write_text('changed')
        updated = freeze(self.root)
        updated['git'] = expected['git']
        with self.assertRaises(ValueError):
            verify(self.root, updated)

    def test_relative_pointer_and_missing_administration(self):
        (self.repo / '.git').rename(self.root / 'admin')
        (self.repo / '.git').write_text('gitdir: ../admin\n')
        expected = freeze(self.root)
        restored = self.roundtrip()
        verify(restored, expected)
        (restored / 'repo/.git').unlink()
        with self.assertRaises(ValueError):
            verify(restored, expected)
        (restored / 'repo/.git').write_text('gitdir: ../missing\n')
        with self.assertRaises((ValueError, subprocess.CalledProcessError)):
            verify(restored, expected)

    def test_external_pointer_and_alternates(self):
        admin = self.base / 'external-admin'
        (self.repo / '.git').rename(admin)
        (self.repo / '.git').write_text(f'gitdir: {admin}\n')
        with self.assertRaises(ValueError):
            freeze(self.root)
        (self.repo / '.git').unlink()
        admin.rename(self.repo / '.git')
        alternate = self.repo / '.git/objects/info/alternates'
        alternate.write_text(str(admin) + '\n')
        with self.assertRaises(ValueError):
            freeze(self.root)

    def test_external_config_include(self):
        external = self.base / 'external-config'
        external.write_text('[user]\n name = external\n')
        git(self.repo, 'config', 'include.path', str(external))
        with self.assertRaises(ValueError):
            freeze(self.root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
