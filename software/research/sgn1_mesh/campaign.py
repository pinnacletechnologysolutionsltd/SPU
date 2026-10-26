"""Prepared one-attempt driver. No execution authority is implied by this file."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from .reference import BASE, ROOT, verify_reference

PREPARATION = ROOT / 'build/sgn1/mesh_cost_20261013/preparation_01'


def sources():
    manifest = json.loads((PREPARATION / 'source_manifest.json').read_text())
    for name, digest in manifest.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise AssertionError(('PREPARED_SOURCE_CHANGED', name))
    return manifest


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    manifest = sources()
    verify_reference()
    reports = []
    for seed in ('0', '1', '17'):
        environment = dict(os.environ, PYTHONHASHSEED=seed)
        subprocess.run([sys.executable, '-m', 'software.research.sgn1_mesh.preflight'],
                       cwd=ROOT, env=environment, check=True)
        child = output / f'seed_{seed}'
        subprocess.run([sys.executable, '-m', 'software.research.sgn1_mesh.comparison', str(child)],
                       cwd=ROOT, env=environment, check=True)
        reports.append(json.loads((child / 'result.json').read_text()))
    for key in ('mesh_sha256', 'metrics_sha256'):
        hashes = {run[key] for report in reports for run in report['runs']}
        if len(hashes) != 1:
            raise AssertionError(('HASH_SEED_DETERMINISM', key, sorted(hashes)))
    gates = [['bash', 'tools/verify_repo.sh'],
             [sys.executable, 'software/tests/test_rotc_vm_rtl_trace.py'],
             [sys.executable, 'software/tests/test_irotc_vm_trace.py'],
             [sys.executable, 'software/tests/test_rational_robotics.py'],
             [sys.executable, 'software/tests/test_rational_som.py'],
             [sys.executable, 'software/tests/test_lucas_mac_oracle.py'],
             [sys.executable, 'software/tests/test_pade_batch_inversion.py']]
    for command in gates:
        subprocess.run(command, cwd=ROOT, check=True)
    if sources() != manifest:
        raise AssertionError('PREPARATION_CHANGED')
    verify_reference()
    report = dict(status='PASS_COMPARISON_SOFTWARE_ONLY', seeds=reports,
                  mesh_executions=3973 * 6, fcc_retained_traces_rechecked=3973 * 6,
                  structural=dict(evidence_level='A_MATHEMATICAL', nodes_each=63,
                                  fcc=dict(undirected_links=240, max_degree=12, diameter=6),
                                  mesh=dict(undirected_links=138, max_degree=6, diameter=10),
                                  equal_total_link_budget=False),
                  reference_manifest=str(BASE / 'source_manifest.json'),
                  physical_cost='UNMEASURED', phase_a_closeout='NOT AUTOMATIC')
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, sort_keys=True), flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python3 -m software.research.sgn1_mesh.campaign OUTPUT')
    main(Path(sys.argv[1]).resolve())
