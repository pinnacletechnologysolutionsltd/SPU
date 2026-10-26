#!/usr/bin/env python3
"""Offline counter extraction: known totals, damaged evidence, output refusal."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments.surd_cpu_trace_analysis import analyze, PASS

REFERENCE = {'0': {'length': 1, 'index': 0, 'name': 'fixture'}}
ROWS = ['INS -1 115 0 8 0 0 4 0 0 0 0',
        'INS 0 112 0 2 0 0 0 0 0 0 0',
        'INS 0 116 0 12 3 4 2 1 1 1 0',
        *['INS 0 118 1 6 4 0 0 0 1 0 0'] * 8,
        'GROUP 0 90', PASS]


class TraceTests(unittest.TestCase):
    def test_measured_totals(self):
        report = analyze('\n'.join(ROWS), REFERENCE)
        d = report['records']['0']
        self.assertEqual(d['instruction_cycles'], 62)
        self.assertEqual(d['issuer_control_cycles'], 28)
        self.assertEqual(d['normalization_cycles'], 35)
        self.assertEqual(d['alignment_cycles'], 4)
        self.assertEqual(d['rescue_requests'], 1)
        self.assertEqual(d['normalizer_requests_all_reasons'], 9)
        self.assertEqual(d['retired_instructions'], 10)
        self.assertEqual(d['tuple_transfer_cycles'], 2)
        self.assertEqual(d['instruction_counts']['SADD'], 1)
        self.assertTrue(d['boundary_count_matches'])
        self.assertEqual(report['lengths']['1']['totals']['total_cycles'], 90)
        self.assertEqual(report['exact_readback_agreement'],
                         'NOT_ESTABLISHED_BY_COUNTER_EXTRACTION')

    def test_failure_and_incomplete_boundary_are_reported(self):
        rows = ROWS.copy()
        rows[3] = 'INS 0 118 1 6 4 0 0 0 1 0 2'
        d = analyze('\n'.join(rows[:-1]), REFERENCE)
        self.assertEqual(d['records']['0']['failures'], 1)
        self.assertFalse(d['records']['0']['boundary_count_matches'])
        self.assertFalse(d['runtime_pass_marker'])

    def test_corrupt_and_truncated_trace_refused(self):
        cases = [ROWS[:-2], ROWS + ['GROUP 0 90'], ROWS + [ROWS[1]],
                 ROWS + ['INS corrupt'], ROWS + ['INS 1 112 0 2 0 0 0 0 0 0 0'],
                 ['GROUP 0 90'], [r.replace('GROUP 0 90', 'GROUP 0 1') for r in ROWS]]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                analyze('\n'.join(rows), REFERENCE)
        for bad in ('INS 0 115 0 2 3 0 0 0 0 0 0',
                    'INS 0 115 0 8 0 0 0 2 1 0 0',
                    'INS 0 115 0 -1 0 0 0 0 0 0 0'):
            with self.subTest(row=bad), self.assertRaises(ValueError):
                analyze('\n'.join([bad, 'GROUP 0 90']), REFERENCE)

    def test_cli_provenance_and_output_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            log, ref, output = (base / n for n in ('runtime.log', 'reference.json', 'report.json'))
            log.write_text('\n'.join(ROWS))
            ref.write_text(json.dumps(REFERENCE))
            cmd = [sys.executable, str(ROOT / 'software/experiments/surd_cpu_trace_analysis.py'),
                   '--runtime-log', str(log), '--reference-records', str(ref), '--output', str(output)]
            subprocess.run(cmd, check=True, capture_output=True)
            before = output.read_bytes()
            report = json.loads(before)
            self.assertEqual(len(report['inputs'][str(log)]), 64)
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
