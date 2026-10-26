"""Separate mesh service implementation; frozen FCC service is never patched."""
from .topology import INDEX, select_port


def service(node, node_id, coordinates, links):
    event = dict(service='IDLE', packet=None, port=None)
    if not node.inbox and not node.pending:
        return event, None
    inbox = bool(node.inbox) and (not node.pending or node.preference == 'INBOX')
    if inbox:
        packet = node.inbox.popleft()
        node.preference = 'FANOUT'
        port = None
        if packet.kind:
            identity = packet.source, packet.sequence
            if identity in node.seen:
                event['service'] = 'DUPLICATE_SUPPRESSION'
            else:
                event['service'] = 'FIRST_VISIT'
                node.seen.add(identity)
                node.accumulator += packet.payload
                node.pending.extend((packet, p) for p in sorted(links[node_id]))
        elif node_id == packet.target:
            event['service'] = 'LOCAL_DELIVERY'
            node.accumulator += packet.payload
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
    sent = packet.transmitted(node_id, INDEX[port], receiver)
    return event, (node_id, INDEX[port], receiver, ingress, sent)
