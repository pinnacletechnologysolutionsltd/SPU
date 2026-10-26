"""Named observation mutations and independent per-identity ledger controls."""
from copy import deepcopy

from .conservation import Accounting
from .graph_oracle import reference_graph
from .schedule_reference import empty_state, root_record
from .simulator import Simulator
from .trace_checker import check_trace


def reject(name, reason, operation):
    try:
        operation()
    except AssertionError as error:
        if error.args[0][0] != reason:
            raise AssertionError(('WRONG_REJECTION', name, reason, error.args))
        return dict(control=name, reason=reason, first_counterexample=error.args[0])
    raise AssertionError(('ESCAPED_CONTROL', name))


def qualify_controls(plan):
    fifo, wave = plan['scheduling_fixtures']
    original = Simulator(1, wave['injections']).run(wave['tick_limit'])
    fifo_trace = Simulator(1, fifo['injections']).run(fifo['tick_limit'])
    controls = []
    for name, reason in (
        ('wrong_accumulator', 'STATE_UPDATE'), ('premature_seen', 'SEEN_BEFORE_SERVICE'),
        ('dropped_fanout', 'FIFO_STATE'), ('wrong_preference', 'PREFERENCE_UPDATE'),
        ('cost_free_suppression', 'SERVICE_EVENT'), ('hidden_link_drop', 'LINK_COMMIT'),
        ('missing_observation', 'UNVERIFIED'), ('same_tick_fanout', 'SERVICE_EVENT'),
        ('wrong_fifo', 'ADMISSION_STATE'), ('duplicate_application', 'STATE_UPDATE'),
    ):
        altered = deepcopy(fifo_trace if name == 'wrong_fifo' else original)
        node = altered['frames'][0]['nodes'][6]
        if name == 'wrong_accumulator': node['after']['accumulator'] += 1
        elif name == 'premature_seen': node['before']['seen'] = [[6, 0]]
        elif name == 'dropped_fanout': node['after']['pending'].pop()
        elif name == 'wrong_preference': node['after']['preference'] = 'INBOX'
        elif name == 'cost_free_suppression': altered['frames'][4]['nodes'][6]['event']['service'] = 'IDLE'
        elif name == 'hidden_link_drop': altered['frames'][1]['inflight'].clear()
        elif name == 'missing_observation': del node['after']['inbox']
        elif name == 'same_tick_fanout': node['event']['service'] = 'FANOUT'
        elif name == 'duplicate_application': altered['frames'][4]['nodes'][6]['after']['accumulator'] += 3
        else: altered['frames'][1]['nodes'][8]['before']['inbox'].reverse()
        rows = fifo['injections'] if name == 'wrong_fifo' else wave['injections']
        controls.append(reject(name, reason, lambda: check_trace(1, rows, altered)))
    adjacency = reference_graph(1)[1]
    row = dict(tick=0, source=6, target=6, sequence=0, payload=3, ordinal=0)
    for copies in (0, 2):
        ledger = Accounting([row], adjacency)
        ledger.admit(0)
        states = [empty_state() for _ in adjacency]
        states[6]['inbox'] = [root_record(row)] * copies
        controls.append(reject('unicast_copies_' + str(copies), 'CONSERVATION',
                               lambda: ledger.boundary(states, [])))
    ledger = Accounting([row], adjacency)
    event = dict(service='LOCAL_DELIVERY', packet=root_record(row), port=None)
    ledger.consume(6, event)
    controls.append(reject('duplicate_delivery', 'DUPLICATE_DELIVERY', lambda: ledger.consume(6, event)))
    for change in (-1, 1):
        ledger = Accounting(wave['injections'], adjacency)
        ledger.admit(0)
        ledger.consume(6, original['frames'][0]['nodes'][6]['event'])
        states = deepcopy([n['after'] for n in original['frames'][0]['nodes']])
        if change == -1: states[6]['pending'].pop()
        else: states[6]['pending'].append(deepcopy(states[6]['pending'][0]))
        controls.append(reject('wavefront_copy_delta_' + str(change), 'CONSERVATION',
                               lambda: ledger.boundary(states, [])))
    simulation = Simulator(1, [row])
    altered = simulation.run(10)
    altered['frames'].append(simulation.step())
    altered['stats'] = dict(simulation.stats)
    controls.append(reject('redundant_tick', 'TERMINATION_TICK', lambda: check_trace(1, [row], altered)))
    return controls
