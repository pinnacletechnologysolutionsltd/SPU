"""Independent predicates return rejection sets without receiving mutation IDs."""
from .codec import identical
from .oracle import Expansion, answer, comparator
from . import schedule


def semantic_label(op):
    return {'multiply': 'REJECT_PRODUCT_VALUE', 'sign': 'REJECT_EMBEDDING_SIGN',
            'norm': 'REJECT_NORM_VALUE', 'equality': 'REJECT_EQUALITY'}.get(op, 'REJECT_VALUE')


def operation(fixture, observed, oracle_record=None):
    labels = set()
    expected = schedule.operation(fixture)
    op = fixture['operation']
    literal = fixture['expected_result']
    if observed['status'] != fixture['expected_status']:
        labels.add('REJECT_STATUS')
    if not identical(observed['result'], literal):
        labels.add(semantic_label(op))
    if observed['charged_units'] != fixture['expected_charged_units']:
        labels.add('REJECT_WORK_COUNT')
    for field in ('status', 'result', 'destination', 'events', 'next_action', 'adjustments'):
        if not identical(observed[field], expected[field]):
            labels.add('REJECT_SCHEDULE_' + field.upper())
    if observed['charged_units'] != len(observed['events']):
        labels.add('REJECT_WORK_COUNT')
    if not identical(expected['result'], literal) or expected['status'] != fixture['expected_status']:
        labels.add('REJECT_FROZEN_EXPECTATION')
    if expected['charged_units'] != fixture['expected_charged_units']:
        labels.add('REJECT_FROZEN_WORK_COUNT')
    if observed['status'] != 'OK' and not identical(observed['destination'], fixture['initial_destination']):
        labels.add('REJECT_ATOMIC_REFUSAL')
    if op in ('multiply', 'conjugate', 'unit_inverse') and observed['adjustments'] > 1:
        labels.add('REJECT_LOCAL_ADJUSTMENT_BOUND')
    if op == 'norm' and fixture['expected_status'] == 'NORM_OVERFLOW':
        if observed['status'] != 'NORM_OVERFLOW' or observed['result'] is not None:
            labels.add('REJECT_NORM_PUBLICATION')
    if isinstance(literal, list) and isinstance(observed['result'], (tuple, list)):
        if observed['result'][2] != literal[2]:
            labels.add('REJECT_EXPONENT')
    record = answer(fixture) if oracle_record is None else oracle_record
    if fixture['expected_status'] == 'OK':
        if 'expanded_value' in record:
            expansion = Expansion()
            target = expansion.value(literal)
            if not identical(record['expanded_value'], target):
                labels.add(semantic_label(op))
            result = observed['result']
            if type(result) in (tuple, list) and len(result) == 3:
                if not identical(expansion.value(result), target):
                    labels.add(semantic_label(op))
        elif not identical(record.get('result'), literal):
            labels.add(semantic_label(op))
    if 'expected_next_uncharged_action' in fixture:
        if observed['next_action'] != fixture['expected_next_uncharged_action']:
            labels.add('REJECT_NEXT_ACTION')
    return labels


def kernel(fixture, observed):
    labels = set()
    expected = schedule.kernel(fixture)
    literal = dict(status=fixture['expected_status'], result=fixture['expected_result'],
                   charged_units=fixture['expected_scan_adjustment_units'],
                   adjustments=fixture.get('expected_adjustments', fixture.get('expected_adjustments_completed')))
    for field, value in literal.items():
        if not identical(observed[field], value) or not identical(expected[field], value):
            labels.add('REJECT_KERNEL_LITERAL_' + field.upper())
    for field in ('status', 'result', 'charged_units', 'adjustments', 'events', 'next_action'):
        if not identical(observed[field], expected[field]):
            labels.add('REJECT_KERNEL_' + field.upper())
    if observed['charged_units'] != fixture['expected_scan_adjustment_units']:
        labels.add('REJECT_TERMINAL_SCAN_CHARGE')
    if not identical(observed['events'], expected['events']):
        labels.add('REJECT_TERMINAL_SCAN_CHARGE')
    return labels


def comparison(fixture, observed):
    labels = set()
    expected = comparator(*fixture['mantissa'])
    for field, value in expected.items():
        if not identical(fixture[field], value):
            labels.add('REJECT_FROZEN_COMPARATOR')
        if not identical(observed[field], value):
            labels.add('REJECT_COMPARATOR_' + field.upper())
    if observed['embedding_sign'] != expected['embedding_sign']:
        labels.add('REJECT_EMBEDDING_SIGN')
    if observed['conjugate_embedding_sign'] != expected['conjugate_embedding_sign']:
        labels.add('REJECT_EMBEDDING_SIGN')
    if expected['upper_sign'] == 0 and observed['balanced'] != expected['balanced']:
        labels.add('REJECT_UPPER_ENDPOINT')
    if expected['lower_sign'] == 0 and observed['balanced'] != expected['balanced']:
        labels.add('REJECT_LOWER_ENDPOINT')
    return labels


def alias(fixture, observed):
    labels = set()
    if observed['status'] != fixture['expected_status']:
        labels.add('REJECT_STATUS')
    if not identical(observed['post_state'], fixture['expected_post_state']):
        labels.add('REJECT_ALIAS_PUBLICATION')
        if fixture['expected_status'] != 'OK':
            labels.add('REJECT_ATOMIC_REFUSAL')
    if not identical(observed['input_snapshot'], fixture['pre_state']):
        labels.add('REJECT_INPUT_MUTATION')
    return labels
