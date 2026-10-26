"""Synthetic launcher/terminal/schema tests; no registered entry invocation."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from launch_w31 import finalize,sandbox
from w31_table import validate


class Controls(unittest.TestCase):
    def test_terminal_cases(self):
        for rc,done,pins,expected in [(0,True,True,'COMPLETE'),(0,False,True,'FAILED'),
                 (124,False,True,'TIMEOUT'),(137,False,True,'FAILED'),
                 (90,True,True,'FAILED'),(153,True,True,'FAILED'),(0,True,False,'FAILED')]:
            with tempfile.TemporaryDirectory(prefix='w31_synthetic_') as d:
                leaf=Path(d)
                if done: (leaf/'RUNNER_DONE').touch()
                self.assertEqual(finalize(leaf,rc,pins),expected)
                self.assertEqual(sum((leaf/n).exists() for n in ('COMPLETE','FAILED','TIMEOUT')),1)
                self.assertEqual(json.loads((leaf/'terminal.json').read_text())['returncode'],rc)

    def test_metadata_failure(self):
        with tempfile.TemporaryDirectory(prefix='w31_synthetic_') as d:
            leaf=Path(d); (leaf/'RUNNER_DONE').touch(); (leaf/'terminal.json').mkdir()
            self.assertEqual(finalize(leaf,0,True),'FAILED')
            self.assertTrue((leaf/'FINALIZE_FAILED').exists())
            self.assertFalse((leaf/'COMPLETE').exists())

    def test_journal_failure(self):
        with tempfile.TemporaryDirectory(prefix='w31_synthetic_') as d:
            leaf=Path(d); (leaf/'RUNNER_DONE').touch()
            journal=io.StringIO()
            with patch.object(journal,'write',side_effect=OSError('synthetic full disk')):
                self.assertEqual(finalize(leaf,0,True,journal,1),'FAILED')

    def test_no_marker_unavailable(self):
        with tempfile.TemporaryDirectory(prefix='w31_synthetic_') as d:
            leaf=Path(d)
            with patch.object(Path,'touch',side_effect=OSError('synthetic refusal')):
                with self.assertRaisesRegex(RuntimeError,'RESULT_UNAVAILABLE'):
                    finalize(leaf,1,True)

    def test_namespace_command(self):
        cmd=sandbox(Path('/tmp/synthetic_w31'))
        self.assertIn('--unshare-net',cmd)
        self.assertNotIn(str(Path.cwd()),cmd)
        self.assertNotIn('research/qcg_0/p0',' '.join(cmd))

    def test_schema_rejects_incomplete(self):
        with self.assertRaises(ValueError):
            validate(dict(schema='qcg0-independent-w31-stages-v1',preparations=[],routes=[]))


if __name__=='__main__': unittest.main()
