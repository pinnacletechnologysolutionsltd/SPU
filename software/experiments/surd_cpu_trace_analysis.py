#!/usr/bin/env python3
"""Extract measured INS/GROUP kernel counters without executing CPU work."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

OPS = dict(zip(range(0x70, 0x78),
               ('SLI', 'SLD', 'SRD', 'SMUL', 'SADD', 'SSUB', 'SNORM', 'SSTAT')))
FIELDS = ('instruction_cycles', 'normalization_cycles', 'alignment_cycles',
          'product_check_cycles', 'rescue_requests',
          'normalizer_requests_all_reasons', 'stalls')
PASS = 'PASS canonical CPU directed execution and complete kernel stream'


def analyze(log, reference):
    """Validate trace structure; counters alone never establish tuple agreement."""
    groups, elapsed, closed = {}, {}, set()
    for line in log.splitlines():
        words = line.split()
        if not words or words[0] not in ('INS', 'GROUP'):
            continue
        try:
            nums = list(map(int, words[1:]))
        except ValueError as exc:
            raise ValueError('noninteger trace field') from exc
        if words[0] == 'GROUP':
            if len(nums) != 2 or min(nums) < 0:
                raise ValueError('invalid GROUP row')
            group, cycles = nums
            key = str(group)
            if key in closed or key not in groups:
                raise ValueError('duplicate or empty GROUP')
            elapsed[key] = cycles
            closed.add(key)
            continue
        if len(nums) != 11:
            raise ValueError('INS requires eleven fields')
        group, op, tag, lat, norm, align, prod, rescue, starts, stalls, status = nums
        if group < -1 or op not in OPS or tag not in (0, 1) or min(nums[3:]) < 0:
            raise ValueError('invalid INS field')
        if lat == 0 or norm + align + prod > lat or status > 15:
            raise ValueError('inconsistent instruction cycle/status accounting')
        if rescue > starts or starts > lat or rescue > lat:
            raise ValueError('inconsistent normalizer request accounting')
        if group == -1:  # Directed diagnostics are outside retained kernels.
            continue
        key = str(group)
        if key in closed:
            raise ValueError('instruction after GROUP terminal row')
        d = groups.setdefault(key, Counter())
        for field, value in zip(FIELDS, (lat, norm, align, prod, rescue, starts, stalls)):
            d[field] += value
        d['retired_instructions'] += 1
        d['failures'] += int(status != 0)
        d['scheduled_boundary_reductions'] += int(op == 0x76 and tag == 1 and status == 0)
        if op in (0x70, 0x71, 0x72):
            d['tuple_transfer_instructions'] += 1
            d['tuple_transfer_cycles'] += lat
        d['opcode_' + OPS[op]] += 1
    if not reference or set(groups) != set(reference) or closed != set(reference):
        raise ValueError('missing or unexpected kernel groups')
    result, cohorts = {}, {}
    for key, expected in reference.items():
        d = groups[key]
        length = expected['length']
        if type(length) is not int or length <= 0:
            raise ValueError('invalid reference chain length')
        d['total_cycles'] = elapsed[key]
        d['issuer_control_cycles'] = elapsed[key] - d['instruction_cycles']
        if d['issuer_control_cycles'] < 0:
            raise ValueError('group shorter than issued instructions')
        result[key] = {field: d[field] for field in (*FIELDS, 'retired_instructions',
            'failures', 'scheduled_boundary_reductions', 'tuple_transfer_instructions',
            'tuple_transfer_cycles', 'total_cycles', 'issuer_control_cycles')}
        result[key].update(length=length, index=expected.get('index'), name=expected.get('name'),
                           instruction_counts={name: d['opcode_' + name] for name in OPS.values()},
                           expected_scheduled_boundary_reductions=8 * length,
                           boundary_count_matches=d['scheduled_boundary_reductions'] == 8 * length)
        cohort = cohorts.setdefault(str(length), {'records': 0, 'totals': Counter(), 'cycles': []})
        cohort['records'] += 1
        cohort['totals'].update({field: value for field, value in result[key].items()
                                 if type(value) is int and field in d})
        cohort['cycles'].append(elapsed[key])
    for cohort in cohorts.values():
        cycles = cohort.pop('cycles')
        cohort.update(min_cycles=min(cycles), max_cycles=max(cycles))
    return dict(schema='surd_cpu_trace_analysis_v1', records=result, lengths=cohorts,
                runtime_pass_marker=PASS in log.splitlines(),
                exact_readback_agreement='NOT_ESTABLISHED_BY_COUNTER_EXTRACTION',
                fallback_execution='NOT_OBSERVABLE_IN_THIS_TRACE',
                scope='simulation counters; boot/reset excluded; kernel transfers and issuer included')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-log', type=Path, required=True)
    p.add_argument('--reference-records', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    raw, reference = args.runtime_log.read_bytes(), args.reference_records.read_bytes()
    report = analyze(raw.decode(), json.loads(reference))
    report['inputs'] = {str(path): hashlib.sha256(data).hexdigest() for path, data in
                        ((args.runtime_log, raw), (args.reference_records, reference))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as f:
        f.write(json.dumps(report, indent=2) + '\n')
    print(f'Extracted {len(report["records"])} kernel groups: {args.output}')


if __name__ == '__main__':
    main()
