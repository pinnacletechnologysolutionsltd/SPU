#!/usr/bin/env python3
"""Detached scheduler qualification coordinator; refuses artifact overwrite."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.research.sgn1.scheduler_qualification import qualify_seed
from software.research.sgn1.trace_checker import need


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = sorted((ROOT / 'software/research/sgn1').glob('*.py')) + [Path(__file__).resolve()]
    sources += [ROOT / 'spu_strategy/contract_sgn1_scheduler_qualification_2026-10-13.md',
                ROOT / 'spu_strategy/contract_sgn1_phase_a_2026-10-12.md',
                ROOT / 'spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json']
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (args.output / 'source_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    if args.worker:
        report = qualify_seed(args.output)
        report['hash_seed'] = os.environ['PYTHONHASHSEED']
    else:
        children = []
        for seed in ('0', '1', '17'):
            child = args.output / ('seed_' + seed)
            command = [sys.executable, str(Path(__file__).resolve()), '--worker', '--output', str(child)]
            run = subprocess.run(command, env=dict(os.environ, PYTHONHASHSEED=seed))
            need(run.returncode == 0, 'SEED_WORKER_FAILED', seed, run.returncode)
            report = json.loads((child / 'result.json').read_text())
            child_manifest = json.loads((child / 'source_manifest.json').read_text())
            need(child_manifest == manifest, 'SOURCE_CHANGED', seed)
            children.append(report)
        hashes = {run['trace_sha256'] for report in children for run in report['runs']}
        need(len(hashes) == 1, 'HASH_SEED_DETERMINISM', sorted(hashes))
        report = dict(status='PASS_SCHEDULER_FCC_HOST_ONLY', hash_seeds=[0, 1, 17],
                      cases_per_order_per_seed=4148, all_pairs_per_order_per_seed=4138,
                      traffic_and_checkpoint_cases=10, node_orders=['forward', 'reverse'],
                      trace_sha256=hashes.pop(), seeds=children,
                      phase_a_closeout='NOT ACHIEVED; mesh/cost comparison remains outstanding')
    current = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    need(current == manifest, 'SOURCE_CHANGED_DURING_RUN')
    (args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], output=str(args.output))), flush=True)


if __name__ == '__main__':
    main()
