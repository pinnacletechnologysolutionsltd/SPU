"""Ordered operand validation and canonical-domain checks."""
from .budget import Refusal
from .comparator import boundary

OPERATIONS = ('canonicalize', 'step', 'conjugate', 'multiply', 'same_k_sum',
              'norm', 'sign', 'equality', 'unit_inverse')


def validate(operation, arguments, meter):
    """Validate every operand before entering any domain or zero shortcut.

    The fixture codec alone converts arrays to tuples; no fields are coerced.
    """
    meter.test('operation.identity',
               lambda: type(operation) is str and operation in OPERATIONS,
               'INVALID_ENCODING')
    arity = 2 if operation in ('step', 'multiply', 'same_k_sum', 'equality') else 1
    meter.test('arguments.arity',
               lambda: type(arguments) is tuple and len(arguments) == arity,
               'INVALID_INPUT')
    descriptors = arguments[:1] if operation == 'step' else arguments
    for i, descriptor in enumerate(descriptors):
        meter.test(f'input{i}.shape',
                   lambda: type(descriptor) is tuple and len(descriptor) == 3,
                   'INVALID_INPUT')
        for field, value, width in zip(('a', 'b', 'k'), descriptor, (64, 64, 32)):
            meter.action(f'input{i}.{field}.type', lambda: type(value).__name__)
            if type(value) is not int:
                raise Refusal('INVALID_INPUT')
            meter.width(f'input{i}.{field}.width', value, width, 'INVALID_INPUT')
    if operation == 'step':
        increment = arguments[1]
        meter.action('increment.type', lambda: type(increment).__name__)
        if type(increment) is not int:
            raise Refusal('INVALID_INPUT')
        meter.width('increment.width', increment, 32, 'INVALID_INPUT')
    return descriptors


def canonical(descriptor, label, meter):
    a, b, k = descriptor
    if meter.test(label + '.zero', lambda: a == b == 0):
        meter.test(label + '.canonical_zero', lambda: k == 0, 'NONCANONICAL_INPUT')
        return
    lower = meter.action(label + '.lower',
                         lambda: boundary(a, b, counters=meter.primitive_counts))
    if lower < 0:
        raise Refusal('NONCANONICAL_INPUT')
    upper = meter.action(label + '.upper',
                         lambda: boundary(a, b, True, meter.primitive_counts))
    if upper >= 0:
        raise Refusal('NONCANONICAL_INPUT')
