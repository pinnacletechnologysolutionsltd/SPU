"""Full frozen FCC scheduler fixtures, canonical traces and matched summaries."""
import gzip
import hashlib
import json
from time import perf_counter

from .scheduler_controls import qualify_controls
from .scheduler_fixtures import check_fixture, frozen_plan, radius_of
from .simulator import Simulator
from .trace_checker import check_trace, need


def fixture_cases(fixture):
    if 'cases' not in fixture:
        yield fixture['id'], fixture['injections']
        return
    rule = fixture['injection_rule']
    need(rule == dict(tick=0, sequence=0, payload='source_id+1', ordinal=0),
         'UNSUPPORTED_INJECTION_RULE', fixture['id'])
    size = 13 if radius_of(fixture) == 1 else 63
    need(fixture['cases'] == [[s, t] for s in range(size) for t in range(size)],
         'ALL_PAIR_COVERAGE', fixture['id'])
    for source, target in fixture['cases']:
        yield f"{fixture['id']}/{source}/{target}", [dict(
            tick=0, source=source, target=target, sequence=0, payload=source + 1, ordinal=0)]


def qualify_seed(output):
    plan, report = frozen_plan(), []
    fixtures = plan['traffic_fixtures'] + plan['scheduling_fixtures']
    total_start = perf_counter()
    for reverse in (False, True):
        digest = hashlib.sha256()
        mode = 'reverse' if reverse else 'forward'
        cases, pair_cases, summaries = 0, 0, []
        with gzip.open(output / f'{mode}_traces.jsonl.gz', 'wb') as traces:
            for fixture in fixtures:
                started = perf_counter()
                counts = dict(cases=0, max_ticks=0, services=0, suppressions=0,
                              peak_inbox=0, peak_fanout=0, peak_seen=0,
                              peak_total_inbox=0, peak_total_fanout=0, admission_comparisons=0)
                for name, rows in fixture_cases(fixture):
                    result = Simulator(radius_of(fixture), rows, reverse=reverse).run(fixture['tick_limit'])
                    summary = check_trace(radius_of(fixture), rows, result)
                    check_fixture(fixture, result, summary)
                    if 'cases' in fixture:
                        need(summary['deliveries'] == 1, 'ALL_PAIR_DELIVERY', name)
                        expected = [0] * len(summary['accumulators'])
                        expected[rows[0]['target']] = rows[0]['payload']
                        need(summary['accumulators'] == expected, 'ALL_PAIR_SUM', name)
                        pair_cases += 1
                    else:
                        summaries.append(dict(id=fixture['id'], summary=summary))
                    canonical = json.dumps(dict(id=name, radius=radius_of(fixture), inputs=rows,
                                                result=result), sort_keys=True, separators=(',', ':')).encode() + b'\n'
                    digest.update(canonical)
                    traces.write(canonical)
                    cases += 1
                    counts['cases'] += 1
                    counts['max_ticks'] = max(counts['max_ticks'], summary['ticks'])
                    counts['services'] += summary['service_operations']
                    counts['suppressions'] += summary['suppressions']
                    counts['admission_comparisons'] += summary['admission_comparisons']
                    for field in ('peak_inbox', 'peak_fanout', 'peak_seen', 'peak_total_inbox', 'peak_total_fanout'):
                        counts[field] = max(counts[field], summary[field])
                print(json.dumps(dict(mode=mode, fixture=fixture['id'], **counts,
                                      host_seconds=perf_counter() - started)), flush=True)
        need(pair_cases == 4138 and cases == 4148, 'CASE_COVERAGE', cases, pair_cases)
        report.append(dict(mode=mode, cases=cases, all_pairs=pair_cases,
                           trace_sha256=digest.hexdigest(), traffic_summaries=summaries))
    need(report[0]['trace_sha256'] == report[1]['trace_sha256'], 'NODE_ORDER_DETERMINISM')
    controls = qualify_controls(plan)
    need(len(controls) == 16, 'NEGATIVE_CONTROL_COVERAGE', len(controls))
    return dict(status='PASS_SCHEDULER_FCC_HOST_ONLY', runs=report, negative_controls=controls,
                host_seconds=perf_counter() - total_start,
                scope='FCC_R1/R2; no mesh baseline, AOR, finite buffers, RTL or silicon claim')
