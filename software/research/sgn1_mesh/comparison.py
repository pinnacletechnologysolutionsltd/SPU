"""Prepared seed worker: recheck qualified FCC records and independently run mesh."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

from .metrics import observe
from .reference import ROOT, frozen_module, plan, verify_reference
from .simulator import MeshSimulator
from .trace_checker import check_trace

FCC_SHA = 'c7f965b888ec647198beb4fa7ec7c7885311ab8a2f5d43f1191b4d9aebc128c6'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'


def qualify_seed(output):
    verify_reference()
    seed = os.environ.get('PYTHONHASHSEED')
    if seed not in ('0', '1', '17'):
        raise ValueError('UNFROZEN_HASH_SEED')
    output.mkdir(parents=True, exist_ok=False)
    fixtures = [f for f in plan()['traffic_fixtures'] if f['id'].startswith('FCC_R2')]
    expected = dict(case for f in fixtures for case in frozen_module('scheduler_qualification').fixture_cases(f))
    if len(expected) != 3973:
        raise AssertionError('COMPARISON_FIXTURE_COUNT')
    runs = []
    for mode in ('forward', 'reverse'):
        fcc_digest, mesh_digest, metrics_digest = (hashlib.sha256() for _ in range(3))
        names, full_count = set(), 0
        retained = ROOT / f'build/sgn1/scheduler_20261013/qualification_01/artifacts/seed_{seed}/{mode}_traces.jsonl.gz'
        with gzip.open(retained, 'rb') as source, gzip.open(output / f'{mode}_mesh.jsonl.gz', 'wb') as traces, \
                gzip.open(output / f'{mode}_metrics.jsonl.gz', 'wb') as costs:
            for line in source:
                fcc_digest.update(line)
                full_count += 1
                record = json.loads(line)
                if record['radius'] != 2:
                    continue
                name, rows = record['id'], record['inputs']
                if name in names or name not in expected or rows != expected[name]:
                    raise AssertionError(('INPUT_MAPPING', name))
                names.add(name)
                fcc = record['result']
                fcc_summary = frozen_module('trace_checker').check_trace(2, rows, fcc)
                mesh = MeshSimulator(rows, reverse=(mode == 'reverse')).run(4096)
                mesh_summary = check_trace(rows, mesh)
                for field in ('accumulators', 'deliveries', 'first_visits'):
                    if mesh_summary[field] != fcc_summary[field]:
                        raise AssertionError(('APPLICATION_EQUIVALENCE', name, field))
                measured = dict(id=name, fcc=observe(rows, fcc, 12, fcc_summary),
                                mesh=observe(rows, mesh, 6, mesh_summary))
                if name == 'FCC_R2_wavefront':
                    if (measured['fcc']['messages'], measured['mesh']['messages'],
                            fcc_summary['suppressions'], mesh_summary['suppressions']) != (480, 276, 418, 214):
                        raise AssertionError('WAVEFRONT_ANALYTIC_LABELS')
                mesh_line = canonical(dict(id=name, inputs=rows, result=mesh))
                cost_line = canonical(measured)
                traces.write(mesh_line)
                costs.write(cost_line)
                mesh_digest.update(mesh_line)
                metrics_digest.update(cost_line)
        if names != set(expected) or full_count != 4148 or fcc_digest.hexdigest() != FCC_SHA:
            raise AssertionError('REFERENCE_TRACE_BINDING')
        runs.append(dict(mode=mode, cases=len(names), mesh_sha256=mesh_digest.hexdigest(),
                         metrics_sha256=metrics_digest.hexdigest(), fcc_sha256=fcc_digest.hexdigest()))
    if any(runs[0][k] != runs[1][k] for k in ('mesh_sha256', 'metrics_sha256')):
        raise AssertionError('MESH_NODE_ORDER_DETERMINISM')
    verify_reference()
    report = dict(status='PASS_SEED_SOFTWARE_ONLY', hash_seed=seed, runs=runs,
                  physical_cost='UNMEASURED', host_speed_comparison='NOT PERFORMED')
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(qualify_seed(Path(sys.argv[1])), sort_keys=True))
