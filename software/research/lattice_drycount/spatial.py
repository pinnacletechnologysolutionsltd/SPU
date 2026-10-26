"""Immediate and deferred-coordinate evaluation and explicit-denominator Surds."""
from .arrays import vector
from .exact import quotient, add, multiply


def reflect(m, values, root, name, surd=False):
    n = len(values)
    out = vector(m, name, n, 192 if surd else 64)
    with m.frame(12, 4):
        coefficient = (m.constant(0), m.constant(0), m.constant(1)) if surd else m.constant(0)
        for i in m.loop(n):
            x, a = m.read(values, i), m.read(root, i)
            coefficient = add(m, coefficient, multiply(m, x, a)) if surd else m.op('add', coefficient, m.op('multiply', x, a))
        if not surd:
            coefficient = quotient(m, coefficient, m.constant(4))
        for i in m.loop(n):
            x, a = m.read(values, i), m.read(root, i)
            value = add(m, x, multiply(m, coefficient, a), True) if surd else m.scalar(
                m.op('subtract', x, m.op('multiply', coefficient, a)), committed=True)
            m.write(out, i, value)
    return out


def evaluate(m, values, roots, word, initial_name, surd=False):
    name = initial_name
    for t in m.loop(len(word)):
        token = m.read(word, t)
        new = 'state/'+str(t)
        values = reflect(m, values, m.read(roots, token), new, surd)
        m.release(name)
        name = new
    return values, name
