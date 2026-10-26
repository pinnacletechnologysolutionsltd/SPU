#!/usr/bin/env python3
"""C0 experiment runner. Uses no subprocess, hardware, or nonstandard dependency."""
import argparse
import hashlib
import json
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_lossless_cpu_c0 as c0
from software.experiments import spu_lossless_cpu_c0_timing as timing
from software.tests.test_spu_lossless_cpu_c0 import check_correctness

SOURCES = ['software/experiments/spu_lossless_cpu_c0.py',
           'software/experiments/spu_lossless_cpu_c0_timing.py',
           'software/experiments/spu_lossless_cpu_c0_run.py',
           'software/tests/test_spu_lossless_cpu_c0.py',
           'spu_strategy/contract_spu_lossless_cpu_c0_2026-10-05.md']


def fresh_directory(out):
    out.mkdir(parents=True, exist_ok=False)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def run(out, preflight_path):
    allowed = ROOT / 'build/spu_lossless_reduction/c0_cpu_20261005'
    if not out.resolve().is_relative_to(allowed.resolve()) or out.resolve() == allowed.resolve():
        raise ValueError('output must be a fresh child of the C0 evidence root')
    fresh_directory(out)
    preflight = json.loads(preflight_path.read_text())
    report = {'contract': 'SPU lossless CPU storage experiment C0', 'status': 'FAIL',
              'hardware_operations': 0, 'device_equivalence_tested': False,
              'identity': {'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine()},
              'preflight': preflight, 'source_hashes': {p: digest(ROOT/p) for p in SOURCES},
              'correctness': {}, 'sizes': {}, 'timing': {}, 'limits': {
                  'command_timeout_seconds': 60, 'timing_trials': timing.TRIALS,
                  'repetitions': timing.REPETITIONS, 'max_software_repairs': 2,
                  'child_processes': 0, 'device_equivalence': 'DEVICE_EQUIVALENCE_NOT_TESTED'}}
    write_json(out/'results.json', report)
    try:
        for path, expected in preflight['hashes'].items():
            if digest(ROOT/path) != expected:
                raise ValueError('preflight input/source changed: '+path)
        correctness = check_correctness()
        report['correctness'] = correctness
        if not correctness['passed']:
            raise ValueError('correctness failed; timing prohibited')
        inputs = c0.original()
        values = c0.flatten(inputs)
        input_record = {'workload': 'sample_robot_vector + joint_60 forward/inverse',
                        'input_source': 'software/lib/rational_robotics.py',
                        'maintained_tests': 'software/tests/test_rational_robotics.py',
                        'reference': 'six_step_kinematics_trace()[0] + inverse closure + direct Fraction fixture',
                        'selection_rationale': 'One retained vector and joint; 28 reusable integers; existing serializer.',
                        'numeric_rules': 'Maintained unbounded integers and Fraction; no finite-width rounding or overflow.',
                        'values': values, 'logical_input': c0.maintained_value(inputs),
                        'axis_id': 3, 'order': 'a,b,c,d,f,g,h; p numerator/denominator then q numerator/denominator',
                        'artificial_shared_factors': False}
        write_json(out/'inputs.json', input_record)
        report['input_hash'] = digest(out/'inputs.json')
        streams = {mode: c0.encode(inputs, mode) for mode in c0.MODES}
        formulas = c0.independent_sizes(values)
        for mode, stream in streams.items():
            (out/(c0.MODES[mode]+'.bin')).write_bytes(stream)
        report['sizes'] = {
            'complete_bytes': {c0.MODES[m]: len(s) for m,s in streams.items()},
            'independent_complete_bytes': {c0.MODES[m]: n for m,n in formulas.items()},
            'selected_mode': c0.MODES[streams[5][5]], 'tie_rule': 'minimum (complete bytes, numeric tag)',
            'exclusions': c0.candidate_streams(values)[1],
            'framing': '5-byte C0 schema/axis/block prefix, mode tag, uint32 count; no offsets needed for one block',
            'scale_metadata': 'All 14 positive denominators are explicit packed integers; no implicit dropped scale.',
            'actual_representation': 'Existing quadray_to_trace_value/q3_to_trace_value Fraction-string dictionaries; compact ASCII JSON with C0 framing. No maintained native CPU binary format exists.',
            'raw_maintained_json_bytes': len(c0.json_payload(inputs)),
            'raw_int64_bytes': 8*len(values),
            'decoded_buffer_storage': {'equivalent_raw_int64_bytes': 8*len(values),
                                       'representation': '28 original integers, reconstructed Fraction/Q3 objects',
                                       'python_object_bytes_measured': False},
            'coefficient_width_bits': [(2*v if v >= 0 else -2*v-1).bit_length() for v in values]}
        report['sizes']['storage_improves_vs'] = {
            c0.MODES[m]: {'fixed_i64': len(s)<len(streams[0]), 'maintained_json': len(s)<len(streams[4])}
            for m,s in streams.items()}
        report['timing'] = timing.benchmark(inputs, streams)
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = type(error).__name__+': '+str(error)
    write_json(out/'results.json', report)
    packet = out/'review_packet'
    for path in set(SOURCES + list(preflight['hashes'])):
        target = packet/path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/path, target)
    shutil.copyfile(preflight_path, out/'preflight.json')
    print(report['status'], out/'results.json')
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--preflight', type=Path, required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.out, arguments.preflight))
