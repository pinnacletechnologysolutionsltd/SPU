"""C1 one-path benchmark command; standard library, no child processes."""
import argparse
import dis
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_surd_batch_c1 as c1
from software.experiments.spu_lossless_cpu_c0_run import digest, fresh_directory, write_json
from software.experiments.spu_lossless_cpu_c0_timing import measured, TRIALS, REPETITIONS, WARMUPS
from software.tests.test_spu_surd_batch_c1 import oracle, maintained
PATHS = ('baseline', 'aos_kernel', 'soa_kernel', 'decode_once_aos', 'layout_once_soa',
         'aos_e2e', 'soa_e2e', 'shared_eager_kernel', 'shared_boundary_kernel',
         'shared_eager_e2e', 'shared_boundary_e2e', 'checked8_e2e', 'checked16_e2e', 'checked32_e2e')

def fraction_counts(operation):
    counts, instructions = dict(gcd=0, integer_division=0, add=0, multiply=0, subtract=0), {}
    gcd = c1.math.gcd
    def counted_gcd(*values):
        counts['gcd'] += 1
        return gcd(*values)
    def trace(frame, event, arg):
        if frame.f_globals.get('__name__') != 'fractions':
            return None
        if event == 'call':
            frame.f_trace_opcodes = True
            if frame.f_code not in instructions:
                instructions[frame.f_code] = {x.offset: x for x in dis.get_instructions(frame.f_code)}
            key = {'_add':'add', '_mul':'multiply', '_sub':'subtract'}.get(frame.f_code.co_name)
            if key: counts[key] += 1
        if event == 'opcode':
            ins = instructions[frame.f_code].get(frame.f_lasti)
            if ins and (ins.opname == 'BINARY_FLOOR_DIVIDE' or ins.opname == 'BINARY_OP' and ins.argrepr == '//'):
                counts['integer_division'] += 1
        return trace
    previous = sys.gettrace()
    try:
        c1.math.gcd = counted_gcd
        sys.settrace(trace)
        operation()
    finally:
        sys.settrace(previous)
        c1.math.gcd = gcd
    return counts

def run(out, plan_path, size, path):
    plan = json.loads(plan_path.read_text())
    evidence_root = ROOT / 'build/spu_lossless_reduction/c1_surd_batch_20261006'
    if out.resolve() == evidence_root.resolve() or not out.resolve().is_relative_to(evidence_root.resolve()):
        raise ValueError('output must be a fresh child of the C1 evidence root')
    fresh_directory(out)
    report = dict(status='FAIL', path=path, batch_size=size, hardware_operations=0,
                  device_equivalence_tested=False, plan_sha256=digest(plan_path))
    write_json(out/'results.json', report)
    try:
        for source, expected_hash in plan['hashes'].items():
            if digest(ROOT/source) != expected_hash:
                raise ValueError('frozen source/input changed: '+source)
        records = json.loads((ROOT/plan['inputs']).read_text())['records']
        original = tuple(c1.c0.reconstruct(r['original_int64_values']) for r in records)
        rows = tuple(c1.triples(x) for x in original)
        expected = tuple(oracle(row) for row in rows)
        correctness = {}
        for eager in (False, True):
            candidate = c1.batch_aos(tuple(c1.shared_block(row) for row in rows), eager)
            correctness['shared_eager' if eager else 'shared_boundary'] = candidate == expected
        correctness['maintained'] = tuple(map(maintained, original)) == expected
        correctness['aos'] = c1.batch_aos(rows) == expected
        correctness['soa'] = c1.batch_soa(c1.to_soa(rows)) == expected
        correctness['reconstruction'] = all(c1.c0.decode(c1.c0.encode(x, 2)) == x for x in original)
        if path.startswith('checked'):
            checked = c1.Trace(int(path[7:path.index('_')]))
            correctness['shared_boundary'] &= c1.batch_aos(tuple(c1.shared_block(row) for row in rows), False, checked) == expected
        report['correctness'] = correctness
        candidate_name = ('shared_eager' if 'shared_eager' in path else 'shared_boundary') if ('shared' in path or 'checked' in path) else ('soa' if 'soa' in path else 'aos')
        if not correctness['maintained'] or not correctness['reconstruction'] or not correctness[candidate_name]:
            raise ValueError('candidate correctness failed; timing excluded')
        batch = tuple(original[i % len(original)] for i in range(size))
        aos = tuple(rows[i % len(rows)] for i in range(size))
        want = tuple(expected[i % len(expected)] for i in range(size))
        columns, shared = c1.to_soa(aos), tuple(c1.shared_block(row) for row in aos)
        streams = tuple(c1.c0.encode(x, 2) for x in batch)
        def decode():
            return tuple(c1.triples(c1.c0.decode(stream)) for stream in streams)
        def operation():
            prepared = decode() if path == 'decode_once_aos' else aos
            cols = c1.to_soa(aos) if path == 'layout_once_soa' else columns
            outputs = []
            for _ in range(REPETITIONS):
                if path == 'baseline':
                    result = tuple(c1.c0.kernel(x) for x in batch)
                elif path == 'soa_kernel' or path == 'layout_once_soa':
                    result = c1.batch_soa(cols)
                elif path == 'decode_once_aos' or path == 'aos_kernel':
                    result = c1.batch_aos(prepared)
                elif path == 'aos_e2e':
                    result = c1.batch_aos(decode())
                elif path == 'soa_e2e':
                    result = c1.batch_soa(c1.to_soa(decode()))
                else:
                    block = shared if path.endswith('_kernel') else tuple(c1.shared_block(row) for row in decode())
                    width = int(path[7:path.index('_')]) if path.startswith('checked') else None
                    trace = c1.Trace(width) if width else None
                    result = c1.batch_aos(block, 'eager' in path, trace)
                outputs.append(result)
            return outputs
        expected_raw = [tuple(c1.c0.kernel(x) for x in batch)]*REPETITIONS if path == 'baseline' else [want]*REPETITIONS
        report['timing'] = measured(operation, expected_raw)
        trace = c1.Trace(int(path[7:path.index('_')]) if path.startswith('checked') else None)
        trace_rows = shared if 'shared' in path or 'checked' in path else aos
        traced = c1.batch_aos(trace_rows, 'boundary' not in path and 'checked' not in path, trace)
        if traced != want:
            raise ValueError('checked-width output mismatch')
        report.update(status='PASS', identity=dict(python=sys.version, platform=platform.platform()),
                      counts_per_batch=trace.counts, observed_signed_widths=trace.widths,
                      distinct_inputs=min(size, len(records)), repetitions_in_batch=max(0, size-len(records)),
                      trials=TRIALS, repetitions=REPETITIONS, warmups=WARMUPS,
                      kernel_executions_per_trial=size*REPETITIONS,
                      canonical_output_digest=hashlib.sha256(repr(want).encode()).hexdigest(),
                      width_model='checked wide Python model; no native narrow execution',
                      count_scope='candidate triple engine only; baseline counts are an equivalent triple reference',
                      python_object_memory='NOT_MEASURED')
        report['cost_scope'] = plan['paths'][path]
        report['maintained_fraction_counts_per_batch'] = fraction_counts(lambda: tuple(c1.c0.kernel(x) for x in batch))
        report['preprocessing_counts_per_batch'] = dict(triples_lcm=7*size, triples_integer_division=14*size, triples_products=14*size,
                                                       shared_block_lcm=1*size, shared_integer_division=14*size, shared_products=14*size)
        report['materialization_counts_per_batch'] = dict(fraction_gcd=16*size, fraction_integer_division=32*size)
        report['expanded_buffers'] = dict(original_int64_equivalent_bytes=224*size,
                                          triple_int64_equivalent_bytes=168*size,
                                          retained_stream_bytes=sum(map(len, streams)),
                                          soa_additional_same_values_int64_equivalent_bytes=168*size)
    except Exception as error:
        report['error'] = type(error).__name__+': '+str(error)
    write_json(out/'results.json', report)
    (out/('COMPLETE' if report['status'] == 'PASS' else 'FAILED')).write_text(report['status']+'\n')
    print(report['status'], out/'results.json')
    return 0 if report['status'] == 'PASS' else 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--batch-size', type=int, choices=(1, 16, 64), required=True)
    parser.add_argument('--path', choices=PATHS, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.out, args.plan, args.batch_size, args.path))
