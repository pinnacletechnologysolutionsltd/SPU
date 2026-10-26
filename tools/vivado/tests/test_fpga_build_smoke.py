#!/usr/bin/env python3
"""Fast stub smoke test for the lightweight FPGA build entry point."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
ENTRY = ROOT / 'tools/vivado/fpga_build.py'
FILELIST = 'tools/vivado/filelists/tensegrity_link_top.f'
XDC = 'hardware/boards/artix7/spu_a7_tensegrity_link_g1.xdc'


class BuildSmoke(unittest.TestCase):
    def test_worker_writes_manifest_reports_and_terminal_state(self):
        with tempfile.TemporaryDirectory(prefix='spu-fpga-build-smoke-') as tmp:
            root = Path(tmp)
            run_dir = root / 'run'
            fake = root / 'vivado-stub'
            fake.write_text(r'''#!/usr/bin/env python3
import pathlib, sys
if sys.argv[1:] == ['-version']:
    print('Vivado smoke stub 2026.1')
    raise SystemExit(0)
args=sys.argv[1:]
out=pathlib.Path(args[args.index('-outdir')+1])
for key in ('-log','-journal'):
    pathlib.Path(args[args.index(key)+1]).write_text('stub\n')
(out/'synth_timing_summary.rpt').write_text('stub timing\n')
(out/'synth_utilization.rpt').write_text('stub utilization\n')
(out/'COMPLETE').write_text('complete\n')
''')
            fake.chmod(0o755)
            command = [sys.executable, '-B', str(ENTRY), '--worker', '--smoke',
                       '--stage', 'synth', '--run-dir', str(run_dir), '--vivado', str(fake),
                       '--timeout', '30', '--top', 'spu_a7_tensegrity_link_top',
                       '--part', 'xc7a100tfgg676-1', '--filelist', FILELIST, '--xdc', XDC]
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((run_dir / 'manifest.json').read_text())
            self.assertEqual(manifest['status'], 'COMPLETE')
            self.assertEqual(manifest['vivado_version'], 'Vivado smoke stub 2026.1')
            self.assertEqual(len(manifest['timing_reports']), 1)
            self.assertEqual(len(manifest['utilization_reports']), 1)
            self.assertIn('hardware/boards/artix7/spu_a7_tensegrity_link_top.v', manifest['input_sha256'])


if __name__ == '__main__':
    unittest.main()
