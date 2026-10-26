"""Short deterministic mathematical preparation checks, never a qualification campaign."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from time import perf_counter

from .checker import check_roots, need
from .comparators import run
from .controls import qualify
from .fixtures import simple_roots, workload_plan
from .linear import rank
from .mapping import (constrained_block_basis, extended_block_basis, d4_to_quadray_and_scalar,
                      restore_d4, e8_to_blocks, restore_blocks)
from .roots import roots, reflect
from .surd_arm import run as surd_run


def exact_json(value):
    if type(value) is Fraction:
        return dict(numerator=value.numerator, denominator=value.denominator)
    raise TypeError(type(value).__name__)


def prepare(output):
    output = Path(output)
    if (output / 'math_preparation.json').exists():
        raise ValueError('OUTPUT_EXISTS')
    output.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    profiles = [check_roots(system, roots(system)) for system in ('D4', 'E8')]
    mapping_checks = 0
    for scaled in roots('D4'):
        physical = tuple(v // 2 for v in scaled)
        need(restore_d4(*d4_to_quadray_and_scalar(physical)) == physical, 'D4_BRIDGE')
        mapping_checks += 1
    for scaled in roots('E8'):
        need(restore_blocks(e8_to_blocks(scaled)) == scaled, 'E8_EXTENDED_BRIDGE')
        mapping_checks += 1
    need(rank(constrained_block_basis()) == 6, 'QUADRAY_BLOCK_RANK')
    need(rank(extended_block_basis()) == 8, 'EXTENDED_BLOCK_RANK')
    for system in ('D4', 'E8'):
        generators = simple_roots(system)
        need(rank(generators) == len(generators), 'GENERATOR_RANK')
        need(set(generators) <= set(roots(system)), 'GENERATOR_MEMBERSHIP')
        orbit, pending = {generators[0]}, [generators[0]]
        while pending:
            current = pending.pop()
            for alpha in generators:
                transformed = reflect(current, alpha)
                if transformed not in orbit:
                    orbit.add(transformed)
                    pending.append(transformed)
        need(orbit == set(roots(system)), 'SIMPLE_GENERATOR_ORBIT', system)
    plan = workload_plan()
    # Four explicit small comparison checks; larger words are prepared, not run.
    selected = [case for case in plan['proposed_cases'] if case['id'].split('/')[2:] == ['2', '1']]
    comparisons = []
    for case in selected:
        outputs = {arm: run(case, arm) for arm in ('coordinates', 'matrix', 'generator_word')}
        outputs['surd_bridge'] = surd_run(case)
        need(len({tuple(v['scaled_output']) for v in outputs.values()}) == 1, 'COMPARISON_VALUE', case['id'])
        expected = tuple(case['scaled_input'])
        for token in case['generator_word']:
            expected = reflect(expected, simple_roots(case['system'])[token])
        need(tuple(outputs['coordinates']['scaled_output']) == expected, 'COMPARISON_ORACLE')
        n, length = len(expected), len(case['generator_word'])
        counts = outputs['coordinates']['accounting']['operations']
        need(counts['multiply'] == 2 * n * length and counts['add'] == n * length
             and counts['subtract'] == n * length and counts['exact_quotient'] == length,
             'COORDINATE_OPERATION_LABELS')
        comparisons.append(dict(id=case['id'], arms=outputs))
    report = dict(status='PREPARATION_CHECK_PASS_NOT_QUALIFIED', profiles=profiles,
                  mapping_root_roundtrips=mapping_checks, constrained_quadray_rank=6,
                  extended_encoding_rank=8, negative_controls=qualify(), comparison_smoke=comparisons,
                  proposed_workload_cases=len(plan['proposed_cases']), qualified_campaign='NOT RUN',
                  hardware='NOT ACCESSED', unresolved=['General compact descriptor', 'AOR-S1 mapping',
                  'Complete primitive cost instrumentation', 'Bounded refusal profile', 'Workload usefulness'],
                  host_seconds=perf_counter() - started)
    for path in sorted(Path(__file__).parent.glob('*.py')):
        report.setdefault('source_sha256', {})[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output / 'math_preparation.json').write_text(json.dumps(report, indent=2, default=exact_json) + '\n')
    (output / 'workload_plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'profiles', 'mapping_root_roundtrips',
          'proposed_workload_cases', 'host_seconds')}, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    prepare(parser.parse_args().output)
