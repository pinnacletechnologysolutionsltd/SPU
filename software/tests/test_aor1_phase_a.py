#!/usr/bin/env python3
"""AOR-1 independent software qualification; not hardware or ISA conformance."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from software.research.aor1.qualification import (
    qualify_literals,qualify_boundaries,qualify_independent_cases)
from software.research.aor1.negative_controls import NAMES,run_defect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='New evidence directory; refuses overwrite')
    parser.add_argument('--negative',choices=NAMES)
    args = parser.parse_args()
    if args.negative:
        # Every defect must produce a nonzero command exit, not a swallowed error.
        run_defect(args.negative)
        raise RuntimeError('Deliberate defective observation escaped checker')
    if args.output:
        args.output.mkdir(parents=True,exist_ok=False)
    ordinary = qualify_literals()
    boundaries = qualify_boundaries()
    independent = qualify_independent_cases()
    controls = []
    for name in NAMES:
        command = [sys.executable,str(Path(__file__).resolve()),'--negative',name]
        result = subprocess.run(command,capture_output=True,text=True,timeout=30)
        # A qualified rejection is the checker's AssertionError, not an import error.
        if result.returncode == 0 or 'AssertionError' not in result.stderr:
            raise AssertionError((name,'Negative control did not fail in checker',result.stderr))
        controls.append(dict(name=name,exit_code=result.returncode,stderr=result.stderr))
    report = dict(status='PASS_AOR1_SOFTWARE_ONLY',ordinary=ordinary,boundaries=boundaries,
                  independent_cases=independent,negative_controls=controls,
                  scope='Host software, no ISA, RTL, routed timing or board claims')
    if args.output:
        (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],ordinary=len(ordinary),
                         boundaries=len(boundaries),negative_controls=len(controls))))


if __name__ == '__main__':
    main()
