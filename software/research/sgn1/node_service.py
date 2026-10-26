"""One inbox item or one FIFO fanout task per node and synchronous tick."""
from collections import deque
from dataclasses import dataclass, field

from .literals import PORTS
from .local_routing import select_port

PORT_INDEX = {pair: i for i, (pair, _) in enumerate(PORTS)}


@dataclass
class Node:
    accumulator: int = 0
    inbox: deque = field(default_factory=deque)
    pending: deque = field(default_factory=deque)
    seen: set = field(default_factory=set)
    preference: str = 'INBOX'

    def snapshot(self):
        return dict(accumulator=self.accumulator, inbox=[p.record() for p in self.inbox],
                    pending=[dict(packet=p.record(), port=list(port)) for p, port in self.pending],
                    seen=[list(i) for i in sorted(self.seen)], preference=self.preference)


def service(node, node_id, coordinates, links):
    event = dict(service='IDLE', packet=None, port=None)
    if not node.inbox and not node.pending:
        return event, None
    inbox = bool(node.inbox) and (not node.pending or node.preference == 'INBOX')
    if inbox:
        packet = node.inbox.popleft()
        node.preference = 'FANOUT'
        if packet.kind:
            identity = packet.source, packet.sequence
            if identity in node.seen:
                event['service'] = 'DUPLICATE_SUPPRESSION'
            else:
                event['service'] = 'FIRST_VISIT'
                node.seen.add(identity)
                node.accumulator += packet.payload
                node.pending.extend((packet, pair) for pair in sorted(links[node_id]))
            port = None
        elif packet.target == node_id:
            event['service'] = 'LOCAL_DELIVERY'
            node.accumulator += packet.payload
            port = None
        else:
            event['service'] = 'FORWARD'
            delta = tuple(a - b for a, b in zip(coordinates[packet.target], coordinates[node_id]))
            port = select_port(delta, tuple(links[node_id]))
    else:
        packet, port = node.pending.popleft()
        node.preference = 'INBOX'
        event['service'] = 'FANOUT'
    event.update(packet=packet.record(), port=list(port) if port is not None else None)
    if port is None:
        return event, None
    receiver, ingress = links[node_id][port]
    egress = PORT_INDEX[port]
    sent = packet.transmitted(node_id, egress, receiver)
    return event, (node_id, egress, receiver, ingress, sent)
