#!/usr/bin/env python3
"""Host-only fixed AOR comparison; campaign authorization required before running."""
import argparse
import json
from pathlib import Path
import resource
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from software.research.aor1.cohorts import NAMES,run
from software.research.aor1.comparators import counter_steps,direct_pell
from software.research.aor1.oracle import Mathematics


def measure(call):
    tracemalloc.start()
    start, cpu = time.perf_counter(),time.process_time()
    try:
        result = call()
        elapsed, process_cpu = time.perf_counter()-start,time.process_time()-cpu
        _,peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return dict(wall_seconds=elapsed,process_cpu_seconds=process_cpu,
                peak_traced_python_bytes=peak,
                process_rss_high_water_kB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                rss_scope='Process lifetime high-water mark, not per-arm unique memory',result=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    rows = []
    for index,name in enumerate(NAMES):
        order = ('aor','mantissa_counter') if index % 2 == 0 else ('mantissa_counter','aor')
        paired = {arm:measure(lambda arm=arm:run(name,arm)) for arm in order}
        if paired['aor']['result'] != paired['mantissa_counter']['result']:
            raise AssertionError(('Paired result/accounting mismatch',name))
        rows.append(dict(cohort=name,order=order,paired=paired))
        (args.output/'paired_rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    limited = measure(lambda:counter_steps(1_000_000))
    if limited['result']['exponent'] != 1_000_000:
        raise AssertionError('Limited exponent counter')
    direct = []
    for steps in (1,12,24,48):
        integers = measure(lambda:direct_pell(steps,False))
        checked = measure(lambda:direct_pell(steps,True))
        oracle = Mathematics()
        exact = oracle.evaluate('EXPAND',(1,0,steps))
        r = integers['result']
        if (r['real'],r['radical'],0) != exact:
            raise AssertionError('Independent Pell agreement')
        direct.append(dict(steps=steps,arbitrary_precision=integers,signed64=checked,
                           oracle_charged_units=oracle.attempted))
    report = dict(status='COMPLETE_HOST_SOFTWARE_COMPARISON',paired=rows,
                  limited_counter=limited,direct_pell=direct,
                  representation_storage=dict(coefficients_bits=128,exponent_bits=32,
                                              total_logical_bits=160),
                  shared_checked_engine=True,timing_instrumentation='tracemalloc enabled equally',
                  limitations=['Single sample per arm, no statistical speedup claim',
                               'Both full representations use the same checked engine',
                               'Limited counter lacks general-mantissa operations',
                               'Materialized Pell comparison has a separate domain/size limit',
                               'No CPU instruction count, RTL, resource, energy or board result'])
    (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],paired_cohorts=len(rows))))


if __name__ == '__main__':
    main()
