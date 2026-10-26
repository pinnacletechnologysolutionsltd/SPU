"""Independent list/dict mesh transition, BFS selector, no adapter imports."""
from copy import deepcopy


def empty_state():
    return dict(accumulator=0, inbox=[], pending=[], seen=[], preference='INBOX')


def packet_key(packet):
    return tuple(packet[k] for k in ('kind', 'source', 'sequence', 'sender', 'egress'))


def root_record(row):
    wave = int(row.get('kind', 'unicast') == 'wavefront')
    return dict(kind=wave, source=row['source'], sequence=row['sequence'], payload=row['payload'],
                target=row.get('target'), sender=-1 if wave else 0,
                egress=-1 if wave else 0, path=[row['source']])


def transition(before, node_id, nodes, adjacency, distances):
    state = deepcopy(before)
    event = dict(service='IDLE', packet=None, port=None)
    if not state['inbox'] and not state['pending']:
        return event, state, None
    available = dict(sorted((tuple(b - a for a, b in zip(nodes[node_id], nodes[j])), j)
                            for j in adjacency[node_id]))
    if state['inbox'] and (not state['pending'] or state['preference'] == 'INBOX'):
        packet = state['inbox'].pop(0)
        state['preference'], port = 'FANOUT', None
        if packet['kind']:
            identity = [packet['source'], packet['sequence']]
            if identity in state['seen']:
                event['service'] = 'DUPLICATE_SUPPRESSION'
            else:
                event['service'] = 'FIRST_VISIT'
                state['seen'] = sorted(state['seen'] + [identity])
                state['accumulator'] += packet['payload']
                state['pending'] += [dict(packet=deepcopy(packet), port=list(p)) for p in available]
        elif node_id == packet['target']:
            event['service'] = 'LOCAL_DELIVERY'
            state['accumulator'] += packet['payload']
        else:
            event['service'] = 'FORWARD'
            improving = [p for p, j in available.items()
                         if distances[j][packet['target']] < distances[node_id][packet['target']]]
            if not improving:
                raise AssertionError(('REFERENCE_ROUTE_STALL', node_id, packet['target']))
            port = improving[0]
    else:
        task = state['pending'].pop(0)
        packet, port = task['packet'], tuple(task['port'])
        state['preference'] = 'INBOX'
        event['service'] = 'FANOUT'
    event.update(packet=deepcopy(packet), port=list(port) if port is not None else None)
    if port is None:
        return event, state, None
    # Deliberately literal, separate from the candidate's port table.
    ports = ((-1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0), (1, 0, 0))
    egress, ingress = ports.index(port), ports.index(tuple(-v for v in port))
    receiver, sent = available[port], deepcopy(packet)
    sent['path'].append(receiver)
    if sent['kind']:
        sent.update(sender=node_id, egress=egress)
    return event, state, dict(sender=node_id, egress=egress, receiver=receiver,
                              ingress=ingress, packet=sent)
