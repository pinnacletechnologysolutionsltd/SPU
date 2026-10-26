#!/usr/bin/env python3
"""Hardlink accounting and conservative dependency-graph controls."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from audit_build_storage import metadata, summarize
from retention_dependencies import dependency_graph, TEXT_LIMIT


class StorageReviewTests(unittest.TestCase):
    def test_inode_allocation_hidden_and_external_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            root = repo / 'build/spu_surd_register'
            root.mkdir(parents=True)
            file = root / '.hidden'
            file.write_bytes(b'evidence' * 1024)
            os.link(file, root / 'same-inode')
            os.link(file, repo / 'outside-scope')
            (root / 'external-link').symlink_to(repo)
            rows = metadata(repo, root)
            result = summarize(rows)
            self.assertEqual(result['regular_file_count'], 2)
            self.assertEqual(result['apparent_bytes_by_path'], 2 * file.stat().st_size)
            self.assertEqual(result['allocated_bytes_unique_regular_inodes'], file.stat().st_blocks * 512)
            self.assertEqual(result['hardlinked_inode_count'], 1)
            self.assertEqual(result['inodes_with_links_outside_scope'], 1)
            self.assertIsNone(result['reclaimable_bytes'])
            self.assertEqual(len(rows), 3)

    def test_reference_graph_explicit_incompleteness(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            root = repo / 'build/spu_surd_register'
            root.mkdir(parents=True)
            (root / 'source.tar').write_bytes(b'archive')
            (root / 'result.json').write_text('{"source":"build/spu_surd_register/source.tar"}')
            (repo / 'docs').mkdir()
            (repo / 'docs/qualification.md').write_text(
                '`build/spu_surd_register/result.json` and `build/missing.json`')
            (root / 'huge.log').write_bytes(b'x' * (TEXT_LIMIT + 1))
            graph = dependency_graph(repo, metadata(repo, root))
            self.assertFalse(graph['complete'])
            self.assertTrue(graph['skipped_inputs'])
            self.assertTrue(any(e['to'] == 'build/spu_surd_register/source.tar' and
                                e['resolution'] == 'exists' for e in graph['edges']))
            self.assertTrue(any(e['to'] == 'build/missing.json' and
                                e['resolution'] == 'missing_or_pattern' for e in graph['edges']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
