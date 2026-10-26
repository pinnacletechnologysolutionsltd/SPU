"""Independent full-tick checker: admission, service, commit and conservation."""
from copy import deepcopy
from functools import lru_cache

from .conservation import Accounting
from .graph_oracle import reference_graph
from .routing_oracle import bfs_distances, check_path
from .schedule_reference import empty_state, packet_key, root_record, transition


def need(condition, reason, *detail):
    if not condition:
        raise AssertionError((reason,) + detail)


@lru_cache(maxsize=2, typed=True)
def oracle_data(radius):
    """Reuse immutable oracle tuples across fresh-state cases, never node state."""
    nodes, adjacency = reference_graph(radius)
    return nodes, adjacency, bfs_distances(radius)


def check_trace(radius, rows, result):
    need(type(result) is dict, 'UNVERIFIED', 'result type')
    need(set(('status', 'frames', 'stats')) <= result.keys(), 'UNVERIFIED', 'result fields')
    nodes, adjacency, distances = oracle_data(radius)
    previous = [empty_state() for _ in nodes]
    prior_flights, operations = [], 0
    account = Accounting(rows, adjacency)
    peaks = dict(peak_inbox=0, peak_fanout=0, peak_seen=0,
                 peak_total_inbox=0, peak_total_fanout=0)
    need(set(peaks) | {'service_operations', 'admission_comparisons'} <= result['stats'].keys(),
         'UNVERIFIED', 'statistics')
    for tick, frame in enumerate(result['frames']):
        need(set(('tick', 'nodes', 'inflight')) <= frame.keys(), 'UNVERIFIED', tick)
        need(frame['tick'] == tick, 'TICK_ORDER', tick, frame['tick'])
        need(len(frame['nodes']) == len(nodes), 'UNVERIFIED', 'node observations', tick)
        admitted = deepcopy(previous)
        for flight in sorted(prior_flights, key=lambda f: (f['receiver'], f['ingress'], packet_key(f['packet']))):
            admitted[flight['receiver']]['inbox'].append(deepcopy(flight['packet']))
        for row in sorted((r for r in rows if r['tick'] == tick), key=lambda r: r['ordinal']):
            admitted[row['source']]['inbox'].append(root_record(row))
        account.admit(tick)
        expected_flights, after = [], []
        for node_id, observation in enumerate(frame['nodes']):
            need(set(('id', 'before', 'event', 'after')) <= observation.keys(), 'UNVERIFIED', tick, node_id)
            for state in (observation['before'], observation['after']):
                need(set(empty_state()) <= state.keys(), 'UNVERIFIED', 'state fields', tick, node_id)
                need(type(state['accumulator']) is int, 'OBSERVATION_TYPE', tick, node_id)
                for packet in state['inbox']:
                    account.validate_packet(packet)
                for task in state['pending']:
                    need({'packet', 'port'} <= task.keys(), 'UNVERIFIED', 'fanout fields')
                    account.validate_packet(task['packet'])
            need({'service', 'packet', 'port'} <= observation['event'].keys(), 'UNVERIFIED', 'event fields')
            need(observation['id'] == node_id, 'NODE_ORDER', tick, node_id)
            need(observation['before'].get('seen') == admitted[node_id]['seen'], 'SEEN_BEFORE_SERVICE', tick, node_id)
            need(observation['before'] == admitted[node_id], 'ADMISSION_STATE', tick, node_id)
            event, state, flight = transition(admitted[node_id], node_id, nodes, adjacency, distances)
            need(observation['event'] == event, 'SERVICE_EVENT', tick, node_id, observation['event'], event)
            need(observation['after'].get('accumulator') == state['accumulator'], 'STATE_UPDATE', tick, node_id)
            need(observation['after'].get('seen') == state['seen'], 'SEEN_UPDATE', tick, node_id)
            need(observation['after'].get('preference') == state['preference'], 'PREFERENCE_UPDATE', tick, node_id)
            need(observation['after'] == state, 'FIFO_STATE', tick, node_id)
            account.consume(node_id, observation['event'])
            operations += int(event['service'] != 'IDLE')
            if event['service'] == 'LOCAL_DELIVERY':
                packet = event['packet']
                check_path(packet['source'], node_id, packet['path'], adjacency, distances)
            if flight is not None:
                expected_flights.append(flight)
            after.append(observation['after'])
        expected_flights.sort(key=lambda f: (f['receiver'], f['ingress'], packet_key(f['packet'])))
        need(frame['inflight'] == expected_flights, 'LINK_COMMIT', tick)
        used_links = [(f['sender'], f['egress']) for f in frame['inflight']]
        need(len(set(used_links)) == len(used_links), 'LINK_CAPACITY', tick)
        account.boundary(after, frame['inflight'])
        if (all(row['tick'] <= tick for row in rows) and not frame['inflight']
                and all(not state['inbox'] and not state['pending'] for state in after)):
            need(tick == len(result['frames']) - 1, 'TERMINATION_TICK', tick)
        for states in (admitted, after):
            for name, field in (('inbox', 'inbox'), ('fanout', 'pending'), ('seen', 'seen')):
                counts = [len(state[field]) for state in states]
                peaks['peak_' + name] = max(peaks['peak_' + name], max(counts))
                if name != 'seen':
                    peaks['peak_total_' + name] = max(peaks['peak_total_' + name], sum(counts))
        previous, prior_flights = after, frame['inflight']
    need(result['status'] == 'DRAINED', 'SIMULATION_TICK_LIMIT', len(result['frames']))
    need(not prior_flights and all(not s['inbox'] and not s['pending'] for s in previous), 'PREMATURE_TERMINATION')
    account.final()
    need(result['stats'].get('service_operations') == operations, 'SERVICE_COUNT')
    for field, value in peaks.items():
        need(result['stats'].get(field) == value, 'STORAGE_PEAK', field, value)
    comparisons = result['stats'].get('admission_comparisons')
    need(type(comparisons) is int and comparisons >= 0, 'UNVERIFIED', 'admission sorting cost')
    return dict(ticks=len(result['frames']), deliveries=sum(account.delivered.values()),
                first_visits=sum(account.first.values()), suppressions=sum(account.suppressed.values()),
                accumulators=account.sums, **result['stats'])
