"""Isolated immutable-outcome execution; no caller state writes."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from . import arithmetic, comparator, normalize, validation
from .budget import InvariantError, Meter, Refusal, fits


@dataclass(frozen=True)
class Outcome:
    status: str
    result: object
    destination: object
    charged_units: int
    adjustments: int
    events: tuple
    next_action: object
    primitive_counts: Mapping


def _outcome(meter, status, result, destination):
    return Outcome(status, result, destination, meter.used, meter.adjustments,
                   tuple(MappingProxyType(dict(event)) for event in meter.events),
                   meter.next_action, MappingProxyType(dict(meter.primitive_counts)))


def _calculate(operation, arguments, meter):
    descriptors = validation.validate(operation, arguments, meter)
    if operation not in ('canonicalize', 'norm', 'sign'):
        for i, descriptor in enumerate(descriptors):
            validation.canonical(descriptor, f'canonical{i}', meter)
    a, b, k = descriptors[0]
    if operation == 'norm':
        value = arithmetic.norm(descriptors[0], meter)
        return meter.width('norm.publication', value, 128, 'NORM_OVERFLOW')
    if operation == 'sign':
        return meter.action('sign', lambda: comparator.sign(a, b, meter.primitive_counts))
    if operation == 'equality':
        return meter.action('tuple.equality', lambda: descriptors[0] == descriptors[1])
    if operation == 'same_k_sum':
        c, d, m = descriptors[1]
        meter.test('equal.k', lambda: k == m, 'UNSUPPORTED_OPERATION')
        first = meter.scalar('sum.a', lambda: a + c)
        second = meter.scalar('sum.b', lambda: b + d)
        zero = meter.test('sum.zero', lambda: first == second == 0)
        state = (0, 0, 0) if zero else normalize.normalize((first, second, k), meter)
        return arithmetic.publish(state, meter)
    zero = []
    for i, descriptor in enumerate(descriptors):
        zero.append(meter.test(f'zero{i}', lambda: descriptor[0] == descriptor[1] == 0))
    if operation == 'unit_inverse':
        if zero[0]:
            raise Refusal('INVALID_DOMAIN')
        value = arithmetic.norm(descriptors[0], meter)
        meter.test('inverse.norm_one', lambda: value == 1, 'UNSUPPORTED_OPERATION')
    elif any(zero):
        return arithmetic.publish((0, 0, 0), meter)
    if operation == 'step':
        exponent = meter.exponent('step.exponent', lambda: k + arguments[1])
        return arithmetic.publish((a, b, exponent), meter)
    if operation in ('conjugate', 'unit_inverse'):
        exponent = meter.exponent('negate.exponent', lambda: -k)
        second = meter.scalar('negate.b', lambda: -b, kind='negate')
        state = (a, second, exponent)
    elif operation == 'multiply':
        c, d, m = descriptors[1]
        exponent = meter.exponent('multiply.exponent', lambda: k + m)
        first, second = arithmetic.products(a, b, c, d, meter)
        state = (first, second, exponent)
    else:
        state = (a, b, k)
    general = operation == 'canonicalize'
    state = normalize.normalize(state, meter, 64 if general else 1, not general)
    return arithmetic.publish(state, meter)


def execute(operation, arguments, destination, budget=4096):
    meter = Meter(budget)
    try:
        result = _calculate(operation, arguments, meter)
    except Refusal as failure:
        return _outcome(meter, str(failure), None, destination)
    target = destination if operation in ('norm', 'sign', 'equality') else result
    return _outcome(meter, 'OK', result, target)


def run_kernel(mantissa, k, budget=4096, allowance=64):
    if (type(mantissa) is not tuple or len(mantissa) != 2 or
            any(type(v) is not int or not fits(v, 136) for v in mantissa) or
            mantissa == (0, 0) or
            type(k) is not int or not fits(k, 32) or
            type(allowance) is not int or not 0 <= allowance <= 64):
        raise InvariantError('invalid internal diagnostic preconditions')
    meter = Meter(budget)
    try:
        result = normalize.normalize((*mantissa, k), meter, allowance)
    except Refusal as failure:
        return _outcome(meter, str(failure), None, None)
    return _outcome(meter, 'OK', result, None)
