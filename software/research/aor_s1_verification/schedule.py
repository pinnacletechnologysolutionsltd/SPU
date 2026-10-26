"""Descriptor/domain/control replay independent of candidate implementation."""
from .codec import arguments, destination
from .oracle import ordering
from .schedule_arithmetic import Replay

OPERATIONS = ('canonicalize', 'step', 'conjugate', 'multiply', 'same_k_sum',
              'norm', 'sign', 'equality', 'unit_inverse')


def perform(m, op, args):
    valid = type(op) is str and op in OPERATIONS
    m.action('operation.identity', valid, None if valid else 'INVALID_ENCODING')
    arity = 2 if op in ('step', 'multiply', 'same_k_sum', 'equality') else 1
    valid = type(args) is tuple and len(args) == arity
    m.action('arguments.arity', valid, None if valid else 'INVALID_INPUT')
    descriptors = args[:1] if op == 'step' else args
    for i, state in enumerate(descriptors):
        valid = type(state) is tuple and len(state) == 3
        m.action(f'input{i}.shape', valid, None if valid else 'INVALID_INPUT')
        for field, value, bits in zip(('a', 'b', 'k'), state, (64, 64, 32)):
            prefix = f'input{i}.{field}'
            m.action(prefix + '.type', type(value).__name__, None if type(value) is int else 'INVALID_INPUT')
            m.width(prefix + '.width', value, bits, 'INVALID_INPUT')
    if op == 'step':
        n = args[1]
        m.action('increment.type', type(n).__name__, None if type(n) is int else 'INVALID_INPUT')
        m.width('increment.width', n, 32, 'INVALID_INPUT')
    if op not in ('canonicalize', 'norm', 'sign'):
        for i, state in enumerate(descriptors):
            m.canonical(state, f'canonical{i}')
    left = descriptors[0]; a, b, k = left
    if op == 'norm':
        return m.width('norm.publication', m.norm(left), 128, 'NORM_OVERFLOW')
    if op == 'sign':
        return m.action('sign', ordering(a, b))
    if op == 'equality':
        return m.action('tuple.equality', descriptors[0] == descriptors[1])
    if op == 'same_k_sum':
        c, d, exponent = descriptors[1]
        m.action('equal.k', k == exponent, None if k == exponent else 'UNSUPPORTED_OPERATION')
        first = m.scalar('sum.a', a + c); second = m.scalar('sum.b', b + d)
        zero = m.action('sum.zero', first == second == 0)
        return m.final((0, 0, 0) if zero else m.normalize((first, second, k), 64))
    zero_tests = [m.action(f'zero{i}', state[0] == state[1] == 0)
                  for i, state in enumerate(descriptors)]
    if op == 'unit_inverse':
        if zero_tests[0]:
            from .schedule_arithmetic import Stop
            raise Stop('INVALID_DOMAIN')
        norm = m.norm(left)
        m.action('inverse.norm_one', norm == 1, None if norm == 1 else 'UNSUPPORTED_OPERATION')
    elif any(zero_tests):
        return m.final((0, 0, 0))
    if op == 'step':
        return m.final((a, b, m.exponent('step.exponent', k + n)))
    if op in ('conjugate', 'unit_inverse'):
        k = m.exponent('negate.exponent', -k)
        b = m.scalar('negate.b', -b)
    if op == 'multiply':
        k = m.exponent('multiply.exponent', k + descriptors[1][2])
        a, b = m.product(left, descriptors[1])
    return m.final(m.normalize((a, b, k), 64 if op == 'canonicalize' else 1))


def operation(fixture):
    op = fixture['operation']
    m = Replay(fixture['budget'])
    args = arguments(op, fixture['arguments'])
    return m.observation(lambda: perform(m, op, args), destination(fixture['initial_destination']))


def kernel(fixture):
    m = Replay(fixture['work_budget'])
    state = (*fixture['input_mantissa'], fixture['input_exponent'])
    return m.observation(lambda: m.normalize(state, fixture['adjustment_allowance']), None)
