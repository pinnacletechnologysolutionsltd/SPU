"""Independent dict-based single-service reference using oracle graph and BFS.

No node-service, local-selector, packet or simulator imports.
"""
from copy import deepcopy

from .literals import PORTS


def empty_state():
    return dict(accumulator=0, inbox=[], pending=[], seen=[], preference='INBOX')


def root_record(row):
    kind = int(row.get('kind', 'unicast') == 'wavefront')
    return dict(kind=kind, source=row['source'], sequence=row['sequence'],
                payload=row['payload'], target=row.get('target'),
                sender=-1 if kind else 0, egress=-1 if kind else 0, path=[row['source']])


def packet_key(packet):
    return tuple(packet[k] for k in ('kind', 'source', 'sequence', 'sender', 'egress'))


def ports_at(node_id, nodes, adjacency):
    by_delta = {delta: pair for pair, delta in PORTS}
    return dict(sorted((by_delta[tuple(b - a for a, b in zip(nodes[node_id], nodes[j]))], j)
                       for j in adjacency[node_id]))


def transition(before, node_id, nodes, adjacency, distances):
    state = deepcopy(before)
    event = dict(service='IDLE', packet=None, port=None)
    if not state['inbox'] and not state['pending']:
        return event, state, None
    available = ports_at(node_id, nodes, adjacency)
    if state['inbox'] and (not state['pending'] or state['preference'] == 'INBOX'):
        packet = state['inbox'].pop(0)
        state['preference'] = 'FANOUT'
        port = None
        if packet['kind']:
            identity = [packet['source'], packet['sequence']]
            if identity in state['seen']:
                event['service'] = 'DUPLICATE_SUPPRESSION'
            else:
                event['service'] = 'FIRST_VISIT'
                state['seen'] = sorted(state['seen'] + [identity])
                state['accumulator'] += packet['payload']
                state['pending'] += [dict(packet=deepcopy(packet), port=list(pair)) for pair in available]
        elif node_id == packet['target']:
            event['service'] = 'LOCAL_DELIVERY'
            state['accumulator'] += packet['payload']
        else:
            event['service'] = 'FORWARD'
            target = packet['target']
            improving = [pair for pair, j in available.items()
                         if distances[j][target] < distances[node_id][target]]
            if not improving:
                raise AssertionError(('REFERENCE_ROUTE_STALL', node_id, target))
            port = improving[0]
    else:
        task = state['pending'].pop(0)
        packet, port = task['packet'], tuple(task['port'])
        state['preference'] = 'INBOX'
        event['service'] = 'FANOUT'
    event.update(packet=deepcopy(packet), port=list(port) if port is not None else None)
    if port is None:
        return event, state, None
    index = {pair: i for i, (pair, _) in enumerate(PORTS)}
    receiver = available[port]
    sent = deepcopy(packet)
    sent['path'].append(receiver)
    if sent['kind']:
        sent.update(sender=node_id, egress=index[port])
    flight = dict(sender=node_id, egress=index[port], receiver=receiver,
                  ingress=index[port[::-1]], packet=sent)
    return event, state, flight
