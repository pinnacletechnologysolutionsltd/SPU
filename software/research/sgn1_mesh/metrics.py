"""Common logical costs from checked traces; no physical resource estimates."""
from collections import Counter

from .wire import FIELDS, decode, encode, integer


def packet_bits(packet, ports):
    raw = encode(packet, ports)
    if decode(raw, ports) != {name: packet[name] for name in FIELDS}:
        raise AssertionError('WIRE_ROUNDTRIP')
    return len(raw) * 8


def state_bits(state, ports):
    integer(state['accumulator'], -(1 << 63), (1 << 63) - 1)
    if state['preference'] not in ('INBOX', 'FANOUT'):
        raise ValueError('STATE_PREFERENCE')
    for source, sequence in state['seen']:
        integer(source, 0, 62)
        integer(sequence, 0, (1 << 32) - 1)
    return (65 + sum(packet_bits(p, ports) for p in state['inbox'])
            + sum(packet_bits(t['packet'], ports) + 4 for t in state['pending'])
            + 38 * len(state['seen']))


def observe(rows, result, ports, checked_summary):
    """Caller must pass independent checker output for this exact trace."""
    labels = {(int(r.get('kind', 'unicast') == 'wavefront'), r['source'], r['sequence']): r
              for r in rows}
    for key, row in labels.items():
        packet_bits(dict(kind=key[0], source=key[1], sequence=key[2], payload=row['payload'],
                         target=row.get('target'), sender=-1 if key[0] else 0,
                         egress=-1 if key[0] else 0), ports)
    links, services = Counter(), Counter()
    contention, inbox_wait, fanout_wait = [0] * 63, [0] * 63, [0] * 63
    deliveries, wave_last = [], {}
    messages = updates = peak_global = peak_flights = 0
    peak_nodes = [0] * 63
    for frame in result['frames']:
        live_flight = sum(packet_bits(f['packet'], ports) for f in frame['inflight'])
        peak_flights = max(peak_flights, live_flight)
        for flight in frame['inflight']:
            links[(flight['sender'], flight['egress'])] += 1
            messages += 1
        for phase in ('before', 'after'):
            bits = [state_bits(n[phase], ports) for n in frame['nodes']]
            peak_global = max(peak_global, sum(bits))
            peak_nodes = [max(a, b) for a, b in zip(peak_nodes, bits)]
        for node in frame['nodes']:
            i, before, after, event = node['id'], node['before'], node['after'], node['event']
            contention[i] += int(bool(before['inbox']) and bool(before['pending']))
            inbox_wait[i] += len(after['inbox'])
            fanout_wait[i] += len(after['pending'])
            services[event['service']] += 1
            if event['service'] not in ('LOCAL_DELIVERY', 'FIRST_VISIT'):
                continue
            updates += 1
            p = event['packet']
            key = p['kind'], p['source'], p['sequence']
            latency = frame['tick'] - labels[key]['tick'] + 1
            if p['kind']:
                wave_last[key] = max(wave_last.get(key, 0), latency)
            else:
                deliveries.append(dict(source=p['source'], sequence=p['sequence'],
                                       target=p['target'], ticks=latency))
    if updates != checked_summary['deliveries'] + checked_summary['first_visits']:
        raise AssertionError('MEASUREMENT_UPDATES')
    ticks = len(result['frames'])
    return dict(evidence_level='B_SIMULATED_LOGICAL_MODEL', host_injections=len(rows),
                messages=messages, modeled_bytes=15 * messages, updates=updates,
                messages_per_update=dict(numerator=messages, denominator=updates),
                drain_ticks=ticks, unicast_latencies=deliveries,
                wavefront_latencies=[dict(source=k[1], sequence=k[2], ticks=v)
                                    for k, v in sorted(wave_last.items())],
                contention_ticks=contention, inbox_wait_item_ticks=inbox_wait,
                fanout_wait_item_ticks=fanout_wait, service_classes=dict(sorted(services.items())),
                link_use=[dict(sender=s, egress=e, transmissions=n, occupied_ticks=n,
                               observed_ticks=ticks) for (s, e), n in sorted(links.items())],
                peak_node_logical_bits=peak_nodes, peak_global_logical_bits=peak_global,
                peak_inflight_logical_bits=peak_flights, normalization_operations=0,
                queue_peaks={k: v for k, v in checked_summary.items() if k.startswith('peak_')},
                service_operations=checked_summary['service_operations'],
                admission_comparisons=checked_summary['admission_comparisons'],
                physical_cost='UNMEASURED')
