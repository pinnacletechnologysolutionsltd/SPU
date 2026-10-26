"""C0 five-trial host timing; checksums and comparisons happen outside clocks."""
import hashlib
from statistics import median
from time import perf_counter_ns
from software.experiments import spu_lossless_cpu_c0 as c0

TRIALS = 5
REPETITIONS = 100
WARMUPS = 3


def checksum(outputs):
    return hashlib.sha256(repr(outputs).encode('utf-8')).hexdigest()


def measured(operation, expected):
    totals, consumed = [], []
    for _ in range(WARMUPS):
        outputs = operation()
        if outputs != expected:
            raise ValueError('warmup output mismatch')
        consumed.append(checksum(outputs))
    for _ in range(TRIALS):
        start = perf_counter_ns()
        outputs = operation()
        elapsed = perf_counter_ns()-start
        if outputs != expected:
            raise ValueError('timed output mismatch')
        consumed.append(checksum(outputs))
        totals.append(elapsed)
    return {'trial_totals_ns': totals, 'median_ns': int(median(totals)),
            'output_checksum': consumed[-1]}


def benchmark(inputs, streams):
    output = c0.kernel(inputs)
    result = {'trials': TRIALS, 'repetitions': REPETITIONS, 'warmups_per_path': WARMUPS,
              'clock': 'perf_counter_ns', 'baseline': {}, 'representations': {}}

    def baseline(count):
        return [c0.kernel(inputs) for _ in range(count)]

    for count in (1, REPETITIONS):
        record = measured(lambda: baseline(count), [output]*count)
        record['kernel_executions_per_trial'] = count
        result['baseline'][str(count)] = record
    for mode, stream in streams.items():
        name = c0.MODES[mode]

        def once(count):
            decoded = c0.decode(stream)
            return [c0.kernel(decoded) for _ in range(count)]

        def anew():
            return [c0.kernel(c0.decode(stream)) for _ in range(REPETITIONS)]

        paths = {}
        for label, operation, count, decodes in (
                ('decode_once_kernel_once', lambda: once(1), 1, 1),
                ('decode_once_kernel_100', lambda: once(REPETITIONS), REPETITIONS, 1),
                ('decode_each_kernel_100', anew, REPETITIONS, REPETITIONS)):
            record = measured(operation, [output]*count)
            baseline_ns = result['baseline'][str(count)]['median_ns']
            record.update(kernel_executions_per_trial=count, decode_operations_per_trial=decodes,
                          exact_ratio_to_baseline={'numerator': record['median_ns'], 'denominator': baseline_ns},
                          end_to_end_improves=record['median_ns'] < baseline_ns)
            paths[label] = record
        encoding = measured(lambda: [c0.encode(inputs, mode) for _ in range(REPETITIONS)],
                            [stream]*REPETITIONS)
        encoding.update(encode_operations_per_trial=REPETITIONS,
                        constructs_all_candidates=(mode == 5))
        paths['encoding_alone'] = encoding
        result['representations'][name] = paths
    return result
