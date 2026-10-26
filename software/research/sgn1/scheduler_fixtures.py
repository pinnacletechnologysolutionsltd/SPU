"""Frozen fixture loader and literal-checkpoint checker; no simulator imports."""
import hashlib
import json
from pathlib import Path

from .trace_checker import need

ROOT = Path(__file__).resolve().parents[3]
BINDINGS = {
    'contract_sgn1_phase_a_2026-10-12.md': 'ebdf883e6afa9d53ac3eaf29272a86eec6f1a15e4c9f84b4592925260a29bf96',
    'sgn1_phase_a_fixture_plan_2026-10-12.json': '289c2860aca4ea4607151e181da3995b2adda2e7e88b5816104bd9cde97bac8b',
}


def frozen_plan():
    for name, digest in BINDINGS.items():
        observed = hashlib.sha256((ROOT / 'spu_strategy' / name).read_bytes()).hexdigest()
        need(observed == digest, 'FIXTURE_BINDING', name, observed, digest)
    return json.loads((ROOT / 'spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json').read_text())


def radius_of(fixture):
    return 1 if fixture.get('profile', fixture['id']).startswith('FCC_R1') else 2


def check_fixture(fixture, result, summary):
    if 'expected_accumulators_by_node_id' in fixture:
        need(summary['accumulators'] == fixture['expected_accumulators_by_node_id'], 'FIXTURE_SUM', fixture['id'])
    for field, observed in (('expected_deliveries', 'deliveries'),
                            ('expected_unicast_deliveries', 'deliveries'),
                            ('expected_first_visits', 'first_visits')):
        if field in fixture:
            need(summary[observed] == fixture[field], 'FIXTURE_COUNT', fixture['id'], field)
    for checkpoint in fixture.get('checkpoints', ()):
        tick, node = checkpoint['tick'], checkpoint['node']
        need(tick < len(result['frames']), 'UNVERIFIED', 'checkpoint', tick)
        observation = result['frames'][tick]['nodes'][node]
        before, after, event = observation['before'], observation['after'], observation['event']
        for name, expected in checkpoint.items():
            if name in ('tick', 'node'):
                continue
            if name == 'pre_service_unicast_sequences':
                actual = [p['sequence'] for p in before['inbox'] if p['kind'] == 0]
            elif name in ('accumulator', 'post_service_accumulator'):
                actual = after['accumulator']
            elif name == 'served_sequence':
                actual = event['packet']['sequence']
            elif name == 'pending_fanout':
                actual = len(after['pending'])
            elif name == 'egress_pair':
                actual = event['port']
            elif name == 'service':
                actual = event['service']
            elif name == 'sends':
                actual = sum(f['sender'] == node for f in result['frames'][tick]['inflight'])
            else:
                raise AssertionError(('UNVERIFIED', 'unsupported checkpoint', name))
            need(actual == expected, 'CHECKPOINT', fixture['id'], tick, node, name, actual, expected)
