"""Cycle/structure model for a fixed-width exact Surd multiply fast path.

This is an architectural estimate, not RTL simulation or synthesis. It models
four parallel coefficient products, a result/fit stage, and an iterative
normalizer used only after a non-fitting raw result.
"""
from math import gcd

from software.experiments import surd_register_exact as ex
from software.experiments.surd_register_e2e import cases, val, pair_mul


def euclid_steps(a, b):
    a, b = abs(a), abs(b)
    steps = 0
    while b:
        a, b = b, a % b
        steps += 1
    return steps


def normalize_work(r):
    first = euclid_steps(r.a, r.b)
    g = gcd(abs(r.a), abs(r.b))
    second = euclid_steps(g, r.d)
    return first + second


def multiply(x, y):
    result, mids = ex.raw('MUL', x, y)
    return result, mids


def model_chain(width, name, x, y):
    """FIT_RESCUE chain with exact destination preservation on failed rescue."""
    state = x
    reference = val(x)
    events = []
    for step in range(2):
        raw, mids = multiply(state, y)
        reference = pair_mul(reference, val(y))
        if val(raw) != reference:
            raise AssertionError('raw datapath result differs from exact reference')
        fits = ex.valid(raw, width)
        norm_cycles = 0
        committed = raw
        outcome = 'fast_commit'
        if not fits:
            outcome = 'normalization_rescue'
            norm_cycles = normalize_work(raw)
            committed = ex.normalize(raw)
            if not ex.valid(committed, width):
                outcome = 'overflow_preserve_destination'
                committed = state
        if outcome != 'overflow_preserve_destination' and val(committed) != reference:
            raise AssertionError('committed result differs from exact reference')
        events.append({
            'step': step + 1,
            'outcome': outcome,
            'raw_widths': ex.widths(raw),
            'largest_raw_intermediate_bits': max(
                ex.uw(v) if k == 'dd' else ex.sw(v) for k, v in mids.items()),
            'euclid_mod_steps': norm_cycles,
            'result_exact': True,
        })
        state = committed
        if outcome == 'overflow_preserve_destination':
            break
    return events


def row(width, workload, x, y):
    events = model_chain(width, workload, x, y)
    # One registered multiply stage plus one registered combine/fit/commit
    # stage. A restoring remainder engine takes N bit cycles per Euclid step;
    # three final exact quotient operations each take N cycles.
    n = 2 * width + 2
    for event in events:
        event['fast_path_latency_cycles'] = 2
        event['normalization_latency_cycles'] = (
            event['euclid_mod_steps'] * n + (3 * n if event['euclid_mod_steps'] else 0))
        event['total_latency_cycles'] = 2 + event['normalization_latency_cycles']
    return {
        'width': width,
        'workload': workload,
        'events': events,
        'chain_latency_cycles': sum(e['total_latency_cycles'] for e in events),
        'fast_lane_initiation_interval_cycles': 1,
        'shared_normalizer_initiation_interval_cycles': max(
            [1] + [e['normalization_latency_cycles'] for e in events]),
        'normalizer_width_bits': n,
        'normalizer_gcd_mod_steps': sum(e['euclid_mod_steps'] for e in events),
    }


def structure(width):
    # Operator and state counts; deliberately not converted to LUT/area units.
    return {
        'width': width,
        'surd_multiplier_count': 5,
        'integer_multiplier_count': 1,
        'multiplier_width': f'{width}x{width}',
        'multiplier_bit_product_ratio': 5,
        'surd_accumulator_count': 2,
        'surd_accumulator_width_bits': 2 * width + 2,
        'denominator_product_width_bits': 2 * width,
        'normalizer_remainder_datapath_width_bits': 2 * width + 2,
        'normalizer_final_quotients': 3,
        'fit_checks': 3,
        'destination_commit_rule': 'commit only if raw or normalized tuple fits; otherwise preserve destination and set overflow',
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', help='write model JSON to this new evidence path')
    args = parser.parse_args()
    widths = (16, 32, 64)
    output = {
        'format': 'SPU_SURD_REGISTER_HW_FASTPATH_MODEL_V1',
        'status': 'MODEL_ONLY_NOT_RTL_OR_SYNTHESIS',
        'assumptions': {
            'fast_path': 'five parallel W-bit coefficient/denominator multipliers; one cycle multiply, one cycle combine-fit-commit',
            'normalizer': 'separate restoring-remainder unit; one 2W+2-bit cycle per Euclid quotient/remainder step; three final exact divisions',
            'integer_baseline': 'one W-by-W integer multiplier with one-cycle latency and one-cycle initiation interval',
            'exclusions': 'clock frequency, routing, stalls from register hazards, queues, energy, LUT/FF mapping, software conversions',
        },
        'structure': [structure(w) for w in widths],
        'workloads': [],
    }
    for w in widths:
        for name, (x, y) in cases(w).items():
            output['workloads'].append(row(w, name, x, y))
    import json
    rendered = json.dumps(output, indent=2, sort_keys=True) + '\n'
    if args.output:
        from pathlib import Path
        path = Path(args.output)
        if path.exists():
            raise FileExistsError(f'refusing to overwrite {path}')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered)
    else:
        print(rendered, end='')


if __name__ == '__main__':
    main()
