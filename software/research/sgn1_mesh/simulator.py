"""Prepared mesh tick engine using only frozen generic packet/state helpers."""
from functools import cmp_to_key

from .reference import frozen_module
from .service import service
from .topology import topology


class MeshSimulator:
    def __init__(self, rows, reverse=False):
        self.coordinates, self.links = topology()
        self.nodes = [frozen_module('node_service').Node() for _ in self.coordinates]
        self.schedule = frozen_module('packets').injections(rows, len(self.nodes))
        self.order = tuple(reversed(range(63))) if reverse else tuple(range(63))
        self.inflight, self.tick = [], 0
        self.stats = dict(service_operations=0, admission_comparisons=0, peak_inbox=0,
                          peak_fanout=0, peak_seen=0, peak_total_inbox=0, peak_total_fanout=0)

    def _arrivals(self):
        def compare(left, right):
            self.stats['admission_comparisons'] += 1
            a = left[2], left[3], left[4].key()
            b = right[2], right[3], right[4].key()
            return (a > b) - (a < b)
        return sorted(self.inflight, key=cmp_to_key(compare))

    def _peaks(self):
        for field, attr in (('inbox', 'inbox'), ('fanout', 'pending'), ('seen', 'seen')):
            counts = [len(getattr(n, attr)) for n in self.nodes]
            self.stats['peak_' + field] = max(self.stats['peak_' + field], max(counts))
            if field != 'seen':
                key = 'peak_total_' + field
                self.stats[key] = max(self.stats[key], sum(counts))

    def step(self):
        for _, _, receiver, _, packet in self._arrivals():
            self.nodes[receiver].inbox.append(packet)
        for _, packet in self.schedule.get(self.tick, ()):
            self.nodes[packet.source].inbox.append(packet)
        self._peaks()
        before = [n.snapshot() for n in self.nodes]
        events, outgoing = {}, []
        for node_id in self.order:
            event, flight = service(self.nodes[node_id], node_id, self.coordinates, self.links)
            events[node_id] = event
            self.stats['service_operations'] += int(event['service'] != 'IDLE')
            if flight is not None:
                outgoing.append(flight)
        self.inflight = sorted(outgoing, key=lambda f: (f[2], f[3], f[4].key()))
        self._peaks()
        flights = [dict(sender=s, egress=e, receiver=r, ingress=i, packet=p.record())
                   for s, e, r, i, p in self.inflight]
        frame = dict(tick=self.tick, nodes=[dict(id=i, before=before[i], event=events[i],
                     after=n.snapshot()) for i, n in enumerate(self.nodes)], inflight=flights)
        self.tick += 1
        return frame

    def done(self):
        return (all(t < self.tick for t in self.schedule) and not self.inflight
                and all(not n.inbox and not n.pending for n in self.nodes))

    def run(self, tick_limit):
        if type(tick_limit) is not int or tick_limit <= 0:
            raise ValueError('INVALID_TICK_LIMIT')
        frames = []
        while not self.done() and self.tick < tick_limit:
            frames.append(self.step())
        return dict(status='DRAINED' if self.done() else 'SIMULATION_TICK_LIMIT',
                    frames=frames, stats=dict(self.stats))
