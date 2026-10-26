#!/usr/bin/env python3
"""Reserved formal software-stage entry; never launches jobs or allocates attempts."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('fixtures', 'supplement', 'kernels', 'controls', 'mutations', 'output'):
        p.add_argument('--' + flag, required=True)
    return p


def hashes(paths):
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def write(directory, name, value):
    path = directory / name
    if path.exists():
        raise RuntimeError('Refuse evidence overwrite: ' + str(path))
    path.write_text(json.dumps(codec.plain(value), indent=2, sort_keys=True) + '\n')


def main(argv=None):
    global codec, qualification
    args = parser().parse_args(argv)
    target = Path(args.output).resolve()
    if target.exists():
        raise RuntimeError('Refuse existing output directory: ' + str(target))
    if not target.is_relative_to(ROOT / 'build'):
        raise RuntimeError('Evidence output must be a new child of repository build/')
    plan_path = ROOT / 'spu_strategy/aor_s1_implementation_execution_plan_2026-10-14.json'
    plan = json.loads(plan_path.read_text())
    if not plan['budget_authorized'] or plan['stages'][0]['current_authorization'] != 'AUTHORIZED':
        raise RuntimeError('Software execution has no owner allocation')
    stage_output = ROOT / plan['stages'][0]['evidence_directory'] / 'results'
    if target != stage_output.resolve():
        raise RuntimeError('Output differs from frozen stage command')
    seal_path = ROOT / plan['source_freeze']
    seal = json.loads(seal_path.read_text())
    for name, expected in seal['sources'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Pre-import source freeze mismatch: ' + name)
    from software.research.aor_s1_verification import codec, qualification
    codec.check_hashes(ROOT, plan['input_hashes'])
    supplied = {k: Path(getattr(args, k)).resolve() for k in
                ('fixtures', 'supplement', 'kernels', 'controls', 'mutations')}
    for p in supplied.values():
        if str(p.relative_to(ROOT)) not in plan['input_hashes']:
            raise RuntimeError('Unfrozen supplied fixture path: ' + str(p))
    packets = {k: codec.load(v) for k, v in supplied.items()}
    groups = dict(operation=packets['fixtures']['fixtures'] + packets['supplement']['fixtures'],
                  kernel=packets['kernels']['fixtures'],
                  comparator=packets['controls']['comparator_fixtures'],
                  alias=packets['controls']['alias_fixtures'])
    codec.unique_ids(groups.values())
    controls = packets['mutations']['controls']
    codec.unique_ids([controls])
    if [len(groups[k]) for k in ('operation', 'kernel', 'comparator', 'alias')] != [91, 5, 11, 13]:
        raise RuntimeError('Frozen fixture coverage mismatch')
    if [sum(c['layer'] == layer for c in controls) for layer in ('CANDIDATE', 'ORACLE', 'CHECKER_META')] != [11, 4, 11]:
        raise RuntimeError('Frozen mutation coverage mismatch')
    source_paths = [ROOT / p for p in plan['future_candidate_files'] + plan['future_verifier_files']]
    source_paths += list((ROOT / 'software/research/aor_s1_verification').glob('*.py'))
    source_paths = sorted(set(source_paths))
    frozen = hashes(source_paths)
    if any(seal['sources'].get(name) != digest for name, digest in frozen.items()):
        raise RuntimeError('Executed module is outside frozen source identity')
    target.mkdir(parents=True)
    write(target, 'identity.json', dict(sources=frozen, inputs=plan['input_hashes'],
                                      argv=sys.argv, python=sys.version, platform=platform.platform()))
    command = [sys.executable, 'software/tests/test_aor_s1.py']
    try:
        test = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        write(target, 'unit_command.json', dict(command=command, returncode=test.returncode,
                                               stdout=test.stdout, stderr=test.stderr))
        if test.returncode:
            raise RuntimeError('Focused unit/development tests failed')
        result = qualification.run(groups, controls)
        write(target, 'acceptance.json', result)
        after = hashes(source_paths)
        write(target, 'source_after.json', after)
        codec.check_hashes(ROOT, plan['input_hashes'])
        if after != frozen:
            raise RuntimeError('MIXED_SOURCE_EXECUTION')
        for name, expected in seal['sources'].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                raise RuntimeError('Frozen configuration/source changed during execution: ' + name)
        if not result['passed']:
            raise RuntimeError('Fixture or mutation acceptance failed; inspect acceptance.json')
        write(target, 'PASS.json', dict(status='FOCUSED_SOFTWARE_PASS',
                                      remaining='REPOSITORY_OR_SYNTHESIS_GATES_PENDING'))
        print('FOCUSED_SOFTWARE_PASS / REPOSITORY_OR_SYNTHESIS_GATES_PENDING')
        return 0
    except Exception as error:
        write(target, 'FAILURE.json', dict(error=repr(error), traceback=traceback.format_exc()))
        print('SOFTWARE_STAGE_FAILED: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
