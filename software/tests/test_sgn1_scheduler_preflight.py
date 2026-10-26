#!/usr/bin/env python3
"""Short implementation preflight; full scheduler qualification is a later gate."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.research.sgn1.conservation import Accounting
from software.research.sgn1.graph_oracle import check_graph, reference_graph
from software.research.sgn1.schedule_reference import empty_state, root_record
from software.research.sgn1.scheduler_fixtures import check_fixture, frozen_plan
from software.research.sgn1.simulator import Simulator
from software.research.sgn1.topology import topology
from software.research.sgn1.trace_checker import check_trace


class SchedulerPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = frozen_plan()['scheduling_fixtures']

    def test_generated_topology_against_oracle(self):
        for radius in (1, 2):
            nodes, links = topology(radius)
            adjacency = tuple(tuple(sorted(dest for dest, _ in row.values())) for row in links)
            check_graph(radius, nodes, adjacency)

    def test_frozen_checkpoints_and_node_order(self):
        for fixture in self.fixtures:
            normal = Simulator(1, fixture['injections']).run(fixture['tick_limit'])
            reverse = Simulator(1, fixture['injections'], reverse=True).run(fixture['tick_limit'])
            self.assertEqual(normal, reverse)
            summary = check_trace(1, fixture['injections'], normal)
            check_fixture(fixture, normal, summary)

    def test_future_injection_and_tick_limit(self):
        rows = [dict(tick=3, source=6, target=6, sequence=0, payload=-7, ordinal=0)]
        short = Simulator(1, rows).run(2)
        self.assertEqual(short['status'], 'SIMULATION_TICK_LIMIT')
        with self.assertRaisesRegex(AssertionError, 'SIMULATION_TICK_LIMIT'):
            check_trace(1, rows, short)
        result = Simulator(1, rows).run(4)
        self.assertEqual(check_trace(1, rows, result)['accumulators'][6], -7)

    def test_trace_mutations(self):
        fixture = self.fixtures[1]
        original = Simulator(1, fixture['injections']).run(fixture['tick_limit'])
        for kind, reason in (('accumulator', 'STATE_UPDATE'), ('seen', 'SEEN_BEFORE_SERVICE'),
                             ('pending', 'FIFO_STATE'), ('preference', 'PREFERENCE_UPDATE'),
                             ('event', 'SERVICE_EVENT'), ('link', 'LINK_COMMIT'),
                             ('missing', 'UNVERIFIED')):
            altered = deepcopy(original)
            node = altered['frames'][0]['nodes'][6]
            if kind == 'accumulator':
                node['after']['accumulator'] += 1
            elif kind == 'seen':
                node['before']['seen'] = [[6, 0]]
            elif kind == 'pending':
                node['after']['pending'].pop()
            elif kind == 'preference':
                node['after']['preference'] = 'INBOX'
            elif kind == 'event':
                altered['frames'][4]['nodes'][6]['event']['service'] = 'IDLE'
            elif kind == 'link':
                altered['frames'][1]['inflight'].clear()
            else:
                del node['after']['inbox']
            with self.assertRaisesRegex(AssertionError, reason):
                check_trace(1, fixture['injections'], altered)

    def test_identity_conservation_and_duplicates(self):
        rows = [dict(tick=0, source=6, target=6, sequence=0, payload=3, ordinal=0)]
        adjacency = reference_graph(1)[1]
        for copies in (0, 2):
            accounting = Accounting(rows, adjacency)
            accounting.admit(0)
            states = [empty_state() for _ in adjacency]
            states[6]['inbox'] = [root_record(rows[0])] * copies
            with self.assertRaisesRegex(AssertionError, 'CONSERVATION'):
                accounting.boundary(states, [])
        accounting = Accounting(rows, adjacency)
        event = dict(service='LOCAL_DELIVERY', packet=root_record(rows[0]), port=None)
        accounting.consume(6, event)
        with self.assertRaisesRegex(AssertionError, 'DUPLICATE_DELIVERY'):
            accounting.consume(6, event)

    def test_injection_validation(self):
        row = dict(tick=0, source=6, target=6, sequence=0, payload=3, ordinal=0)
        for field, value in (('tick', True), ('tick', -1), ('target', 13), ('payload', 0.0), ('kind', 'bad')):
            with self.assertRaises(ValueError):
                Simulator(1, [dict(row, **{field: value})])
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_INJECTION_ID'):
            Simulator(1, [row, dict(row, ordinal=1)])
        with self.assertRaises(ValueError):
            Simulator(1, [dict(row, kind='wavefront')])

    def test_redundant_ticks_are_rejected(self):
        rows = [dict(tick=0, source=6, target=6, sequence=0, payload=3, ordinal=0)]
        simulation = Simulator(1, rows)
        result = simulation.run(10)
        result['frames'].append(simulation.step())
        result['stats'] = dict(simulation.stats)
        with self.assertRaisesRegex(AssertionError, 'TERMINATION_TICK'):
            check_trace(1, rows, result)


if __name__ == '__main__':
    unittest.main()
