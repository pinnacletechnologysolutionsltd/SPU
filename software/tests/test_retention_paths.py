#!/usr/bin/env python3
"""Absolute/relative normalization and known-reference regression controls."""
import json
import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from retention_dependencies import dependency_graph
from retention_paths import references
from regenerate_retention_graph import regenerate


class ReferenceTests(unittest.TestCase):
    def test_absolute_checkout_with_hardware_component(self):
        root = Path('/home/user/Projects/hardware/SPU')
        expected = 'build/campaign/stderr.log'
        self.assertEqual(references(root, json.dumps({'path': str(root / expected)})), {expected})

    def test_relative_forms_and_delimiters(self):
        root = Path('/repo')
        text = '`build/a.json`, "./docs/report.md"; --log=/repo/build/b.log\nsoftware/x.py'
        self.assertEqual(references(root, text), {'build/a.json', 'docs/report.md', 'build/b.log', 'software/x.py'})

    def test_prefix_collisions_external_and_embedded_suffixes(self):
        root = Path('/repo')
        text = '/repo-other/build/a /external/hardware/SPU/build/b notbuild/c foo/build/d'
        self.assertEqual(references(root, text), set())

    def test_root_with_spaces_and_literal_regex_characters(self):
        root = Path('/tmp/a project[1]/hardware/SPU')
        self.assertEqual(references(root, json.dumps(str(root / 'build/log.txt'))), {'build/log.txt'})

    def test_lexical_traversal_is_not_resolved_away(self):
        self.assertEqual(references(Path('/repo'), '/repo/build/../outside'), {'build/../outside'})

    def test_actual_capture_shape_and_source_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'hardware/SPU'
            directory = root / 'build/integrated_context_candidate_01'
            directory.mkdir(parents=True)
            streams = {}
            for name in ('stdout', 'stderr', 'tool'):
                path = directory / (name + '.log')
                path.write_text('fixture')
                streams[name] = {'path': str(path)}
            capture = directory / 'capture.json'
            capture.write_text(json.dumps({'streams': streams}))
            relative = capture.relative_to(root).as_posix()
            graph = dependency_graph(root, [], input_paths=[relative])
            self.assertEqual({e['to'] for e in graph['edges']},
                             {str(p.relative_to(root)) for p in directory.glob('*.log')})
            self.assertTrue(all(e['resolution'] == 'exists' for e in graph['edges']))
            self.assertEqual(len(graph['inputs'][0]['sha256']), 64)
            self.assertTrue(graph['fixed_input_set'])

    def test_fixed_inputs_missing_escape_and_unsafe_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            (root / 'docs').mkdir(parents=True)
            (root / 'docs/report.md').write_text('build/../outside')
            (root / 'docs/external.md').symlink_to(Path(tmp) / 'outside')
            graph = dependency_graph(root, [], input_paths=['docs/report.md', 'docs/missing.md', 'docs/external.md'])
            self.assertEqual(graph['edges'][0]['resolution'], 'unsafe_or_ambiguous')
            self.assertEqual(len(graph['skipped_inputs']), 2)
            self.assertFalse(graph['complete'])

    def test_regeneration_preserves_prior_and_separates_source_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            capture_name = 'build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/capture.json'
            capture = root / capture_name
            capture.parent.mkdir(parents=True)
            streams = {}
            for name in ('stdout', 'stderr', 'tool'):
                log = capture.parent / (name + '.log')
                log.write_text('fixture')
                streams[name] = {'path': str(log)}
            capture.write_text(json.dumps({'streams': streams}))
            (root / 'docs').mkdir()
            (root / 'docs/change.md').write_text('build/old')
            (root / 'docs/missing.md').write_text('build/previous')
            prior = dependency_graph(root, [], input_paths=[capture_name, 'docs/change.md', 'docs/missing.md'])
            for edge in prior['edges']:
                if edge['from'] == capture_name:
                    edge['to'] = 'hardware/SPU/' + edge['to']
                    edge['resolution'] = 'missing_or_pattern'
            prior_path = root / 'prior.json'
            old_bytes = json.dumps(prior).encode()
            prior_path.write_bytes(old_bytes)
            (root / 'docs/change.md').write_text('build/new')
            (root / 'docs/missing.md').unlink()
            (root / 'tools').mkdir()
            for name in ('regenerate_retention_graph.py', 'retention_dependencies.py', 'retention_paths.py', 'retention_tree.py'):
                shutil.copyfile(Path(__file__).resolve().parents[2] / 'tools' / name, root / 'tools' / name)
            output = root / 'build/repository_cleanup/fresh'
            with contextlib.redirect_stdout(io.StringIO()):
                regenerate(root, prior_path, output)
            result = json.loads((output / 'regeneration_result.json').read_text())
            self.assertEqual(prior_path.read_bytes(), old_bytes)
            self.assertEqual(result['actual_capture_gate']['status'], 'PASS')
            self.assertEqual(result['unchanged_inspected_inputs'], 1)
            self.assertEqual(result['identity_change_counts'], {'changed_content': 1, 'not_inspected_now': 1})
            self.assertEqual(result['unchanged_source_edge_comparison']['removed'], 3)
            self.assertEqual(result['unchanged_source_edge_comparison']['added'], 3)
            with self.assertRaises(ValueError):
                regenerate(root, prior_path, output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
