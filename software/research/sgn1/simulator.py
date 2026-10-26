"""Deterministic synchronous host model with canonical, complete tick records."""
from functools import cmp_to_key

from .node_service import Node, service
from .packets import injections
from .topology import topology


def flight_record(flight):
    sender, egress, receiver, ingress, packet = flight
    return dict(sender=sender, egress=egress, receiver=receiver, ingress=ingress,
                packet=packet.record())


class Simulator:
    def __init__(self, radius, rows, reverse=False):
        self.coordinates, self.links = topology(radius)
        self.nodes = [Node() for _ in self.coordinates]
        self.schedule = injections(rows, len(self.nodes))
        self.order = tuple(reversed(range(len(self.nodes)))) if reverse else tuple(range(len(self.nodes)))
        self.inflight, self.tick = [], 0
        self.stats = dict(service_operations=0, admission_comparisons=0,
                          peak_inbox=0, peak_fanout=0, peak_seen=0,
                          peak_total_inbox=0, peak_total_fanout=0)

    def _ordered_arrivals(self):
        def compare(left, right):
            self.stats['admission_comparisons'] += 1
            a, b = (left[2], left[3], left[4].key()), (right[2], right[3], right[4].key())
            return (a > b) - (a < b)
        return sorted(self.inflight, key=cmp_to_key(compare))

    def _peaks(self):
        for field, attr in (('inbox', 'inbox'), ('fanout', 'pending'), ('seen', 'seen')):
            counts = [len(getattr(node, attr)) for node in self.nodes]
            self.stats['peak_' + field] = max(self.stats['peak_' + field], max(counts))
            if field != 'seen':
                key = 'peak_total_' + field
                self.stats[key] = max(self.stats[key], sum(counts))

    def step(self):
        for _, _, receiver, _, packet in self._ordered_arrivals():
            self.nodes[receiver].inbox.append(packet)
        for _, packet in self.schedule.get(self.tick, ()):
            self.nodes[packet.source].inbox.append(packet)
        self._peaks()
        before = [node.snapshot() for node in self.nodes]
        events, outgoing = {}, []
        for node_id in self.order:
            event, flight = service(self.nodes[node_id], node_id, self.coordinates, self.links)
            events[node_id] = event
            self.stats['service_operations'] += int(event['service'] != 'IDLE')
            if flight is not None:
                outgoing.append(flight)
        # Commit only after every node has used its allowance.
        self.inflight = sorted(outgoing, key=lambda f: (f[2], f[3], f[4].key()))
        self._peaks()
        frame = dict(tick=self.tick, nodes=[dict(id=i, before=before[i], event=events[i],
                     after=node.snapshot()) for i, node in enumerate(self.nodes)],
                     inflight=[flight_record(f) for f in self.inflight])
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
