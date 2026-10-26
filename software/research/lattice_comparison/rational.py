"""Explicit schoolbook exact rational primitives; count Euclid work, not CPython."""
from .limits import Refusal


def op(meter, name, a, b):
    meter.integer(a)
    meter.integer(b)
    meter.charge(name)
    if name == 'add':
        value = a + b
    elif name == 'subtract':
        value = a - b
    elif name == 'multiply':
        value = a * b
    else:
        raise Refusal('OPERATION_INVALID')
    return meter.integer(value)


def quotient(meter, a, b):
    meter.integer(a)
    meter.integer(b)
    meter.charge('zero_compare')
    if b == 0:
        raise Refusal('ZERO_DENOMINATOR')
    meter.charge('remainder')
    meter.charge('zero_compare')
    if a % b:
        raise Refusal('INEXACT_QUOTIENT')
    meter.charge('quotient')
    return meter.integer(a // b)


def gcd(meter, a, b):
    meter.integer(a)
    meter.integer(b)
    meter.charge('absolute', 2)
    a, b = meter.integer(abs(a)), meter.integer(abs(b))
    while True:
        meter.charge('zero_compare')
        if b == 0:
            return a
        meter.charge('remainder')
        a, b = b, meter.integer(a % b)
        meter.charge('move', 2)


def normalize(meter, a, d):
    meter.integer(a)
    meter.integer(d)
    meter.charge('zero_compare')
    if d == 0:
        raise Refusal('ZERO_DENOMINATOR')
    meter.charge('sign_compare')
    if d < 0:
        meter.charge('negate', 2)
        a, d = meter.integer(-a), meter.integer(-d)
    common = gcd(meter, a, d)
    result = quotient(meter, a, common), quotient(meter, d, common)
    meter.integer(result[0], committed=True)
    meter.integer(result[1], committed=True)
    return result


def add(meter, left, right):
    a, d = left
    b, e = right
    return normalize(meter, op(meter, 'add', op(meter, 'multiply', a, e),
                               op(meter, 'multiply', b, d)), op(meter, 'multiply', d, e))


def multiply(meter, left, right):
    a, d = left
    b, e = right
    return normalize(meter, op(meter, 'multiply', a, b), op(meter, 'multiply', d, e))
