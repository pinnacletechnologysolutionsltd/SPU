"""Prepared qualification controls. NOT RUN; execute only after authorization."""
from copy import deepcopy
import unittest

from .metrics import observe, state_bits
from .oracle import oracle_data
from .simulator import MeshSimulator
from .topology import select_port, topology
from .trace_checker import check_trace
from .wire import decode, encode


def row(source=0, target=62, sequence=0, payload=3, tick=0, ordinal=0, wave=False):
    data = dict(source=source, sequence=sequence, payload=payload, tick=tick, ordinal=ordinal)
    data.update(kind='wavefront') if wave else data.update(target=target)
    return data


class PreparedChecks(unittest.TestCase):
    def checked(self, rows, reverse=False):
        result = MeshSimulator(rows, reverse).run(4096)
        summary = check_trace(rows, result)
        return result, summary

    def test_all_pairs_and_literal_graph(self):
        nodes, adjacency, distances = oracle_data()
        coordinates, links = topology()
        self.assertEqual(coordinates, nodes)
        self.assertEqual(sum(map(len, adjacency)), 276)
        self.assertEqual(max(map(len, adjacency)), 6)
        self.assertEqual(max(max(d) for d in distances), 10)
        for source in range(63):
            self.assertEqual(sorted(j for j, _ in links[source].values()), list(adjacency[source]))
            for target in range(63):
                current, steps = source, 0
                while current != target:
                    delta = tuple(a - b for a, b in zip(nodes[target], nodes[current]))
                    port = select_port(delta, tuple(links[current]))
                    current = links[current][port][0]
                    steps += 1
                    self.assertLessEqual(steps, 10)
                self.assertEqual(steps, distances[source][target])

    def test_wave_and_order(self):
        rows = [row(wave=True)]
        result, summary = self.checked(rows)
        reverse, other = self.checked(rows, True)
        self.assertEqual(result, reverse)
        self.assertEqual(summary, other)
        self.assertEqual(summary['first_visits'], 63)
        self.assertEqual(summary['suppressions'], 214)
        self.assertEqual(summary['accumulators'], [3] * 63)
        metrics = observe(rows, result, 6, summary)
        self.assertEqual(metrics['messages'], 276)
        self.assertEqual(metrics['modeled_bytes'], 4140)

    def test_admission_and_next_tick(self):
        rows = [row(target=9, sequence=1), row(source=9, target=9, sequence=2,
                tick=1, ordinal=1)]
        result, _ = self.checked(rows)
        self.assertEqual(result['frames'][0]['nodes'][9]['event']['service'], 'IDLE')
        self.assertEqual([p['sequence'] for p in result['frames'][1]['nodes'][9]['before']['inbox']], [1, 2])
        self.assertEqual(result['frames'][1]['nodes'][9]['event']['packet']['sequence'], 1)

    def test_checker_negative_controls(self):
        rows = [row()]
        result, _ = self.checked(rows)
        for name in ('tick', 'inflight', 'accumulator', 'event', 'stats', 'frames'):
            with self.subTest(control=name):
                bad = deepcopy(result)
                if name == 'tick':
                    bad['frames'][0]['tick'] = 1
                elif name == 'inflight':
                    bad['frames'][0]['inflight'] = []
                elif name == 'accumulator':
                    bad['frames'][0]['nodes'][0]['after']['accumulator'] = 1
                elif name == 'event':
                    bad['frames'][0]['nodes'][0]['event']['service'] = 'IDLE'
                elif name == 'stats':
                    bad['stats']['service_operations'] += 1
                else:
                    bad['frames'].pop()
                with self.assertRaises(AssertionError):
                    check_trace(rows, bad)

    def test_wire_literal_and_negative_controls(self):
        packet = dict(kind=0, source=1, sequence=7, payload=-3, target=2, sender=0, egress=0)
        expected = ((1 << 112) | (7 << 80) | (((1 << 64) - 3) << 16) | (2 << 10)).to_bytes(15, 'big')
        self.assertEqual(encode(packet, 6), expected)
        self.assertEqual(decode(expected, 6), packet)
        for field, value in (('source', True), ('source', 63), ('sequence', 1 << 32),
                             ('payload', 1 << 63), ('payload', -(1 << 63) - 1),
                             ('target', None), ('egress', 1), ('sender', -1)):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                encode(dict(packet, **{field: value}), 6)
        for raw in (b'', bytes([128]) + bytes(14), expected[:-1]):
            with self.assertRaises(ValueError):
                decode(raw, 6)
        for payload in (-(1 << 63), (1 << 63) - 1):
            bounded = dict(packet, payload=payload)
            self.assertEqual(decode(encode(bounded, 12), 12), bounded)
        wave = dict(packet, kind=1, target=None, sender=-1, egress=-1)
        self.assertEqual(decode(encode(wave, 6), 6), wave)
        with self.assertRaises(ValueError):
            encode(dict(wave, sender=0, egress=6), 6)
        with self.assertRaises(ValueError):
            encode(dict(wave, sender=0), 12)

    def test_storage_literal_and_accumulator_control(self):
        state = dict(accumulator=0, preference='INBOX', inbox=[], pending=[], seen=[])
        self.assertEqual(state_bits(state, 6), 65)
        packet = dict(kind=1, source=0, sequence=0, payload=3, target=None, sender=-1, egress=-1)
        full = dict(state, inbox=[packet], pending=[dict(packet=packet, port=[1, 0, 0])], seen=[[0, 0]])
        self.assertEqual(state_bits(full, 6), 65 + 120 + 124 + 38)
        with self.assertRaises(ValueError):
            state_bits(dict(state, accumulator=1 << 63), 6)

    def test_wave_service_controls(self):
        rows = [row(wave=True)]
        result, _ = self.checked(rows)
        for mode in ('same_tick_fanout', 'seen_update', 'preference', 'duplicate_add', 'missing_observation'):
            with self.subTest(control=mode):
                bad = deepcopy(result)
                node = bad['frames'][0]['nodes'][0]
                if mode == 'same_tick_fanout':
                    node['event']['service'] = 'FANOUT'
                elif mode == 'seen_update':
                    node['after']['seen'] = []
                elif mode == 'preference':
                    node['after']['preference'] = 'INBOX'
                elif mode == 'missing_observation':
                    del node['after']['pending']
                else:
                    duplicate = next(n for f in bad['frames'] for n in f['nodes']
                                     if n['event']['service'] == 'DUPLICATE_SUPPRESSION')
                    duplicate['after']['accumulator'] += 3
                with self.assertRaises(AssertionError):
                    check_trace(rows, bad)


if __name__ == '__main__':
    unittest.main()
