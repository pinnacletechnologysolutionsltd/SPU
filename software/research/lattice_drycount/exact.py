"""Schoolbook rational/Surd operators with explicit, counted Euclid normalization."""
from contextlib import contextmanager


def quotient(m, a, b):
    m.test(b != 0, 'ZERO_DENOMINATOR', 'zero_compare')
    m.test(m.op('remainder', a, b) == 0, 'INEXACT_QUOTIENT', 'zero_compare')
    return m.op('quotient', a, b)


def gcd(m, a, b):
    with m.frame(4, 2):
        a, b = m.op('absolute', a), m.op('absolute', b)
        while True:
            m.charge('zero_compare')
            if b == 0:
                return a
            a, b = b, m.op('remainder', a, b)
            m.charge('move', 2)


def normalize(m, values):
    with m.frame(8, 4):
        d = values[-1]
        m.test(d != 0, 'ZERO_DENOMINATOR', 'zero_compare')
        m.charge('sign_compare')
        if d < 0:
            values = tuple(m.op('negate', v) for v in values)
        common = m.constant(0)
        # Rational gcd(a,d); Surd gcd(gcd(a,b),d), without an extra gcd(0,a).
        common = gcd(m, values[0], values[1])
        if len(values) == 3:
            common = gcd(m, common, values[2])
        result = []
        for i in m.loop(len(values)):
            value = quotient(m, m.read(values, i), common)
            result.append(m.scalar(value, committed=True))
            m.charge('indexed_write')
        m.test(result[-1] > 0, 'DENOMINATOR_RANGE', 'sign_compare')
        return tuple(result)


def add(m, x, y, subtract=False):
    with m.frame(12, 4):
        for i in m.loop(len(x)):
            m.read(x, i); m.read(y, i)
        operation = 'subtract' if subtract else 'add'
        if len(x) == 2:
            a, d = x; c, f = y
            return normalize(m, (m.op(operation, m.op('multiply', a, f), m.op('multiply', c, d)),
                                 m.op('multiply', d, f)))
        a, b, d = x; c, e, f = y
        # Contracted Surd subtraction: negate both coefficients, then add.
        if subtract:
            c, e = m.op('negate', c), m.op('negate', e)
        return normalize(m, (m.op('add', m.op('multiply', a, f), m.op('multiply', c, d)),
                             m.op('add', m.op('multiply', b, f), m.op('multiply', e, d)),
                             m.op('multiply', d, f)))


def multiply(m, x, y):
    with m.frame(12, 4):
        for i in m.loop(len(x)):
            m.read(x, i); m.read(y, i)
        if len(x) == 2:
            a, d = x; c, f = y
            return normalize(m, (m.op('multiply', a, c), m.op('multiply', d, f)))
        a, b, d = x; c, e, f = y
        return normalize(m, (m.op('add', m.op('multiply', a, c),
                                 m.op('multiply', m.constant(3), m.op('multiply', b, e))),
                             m.op('add', m.op('multiply', a, e), m.op('multiply', b, c)),
                             m.op('multiply', d, f)))
