"""Counted conventional D4 descriptor construction and final application."""
from ..lattice_comparison.d4 import GENERATORS
from .arrays import vector


def build(m, word):
    m.allocate('signed/table', 64+4*(32+12))
    for g in m.loop(4):
        for i in m.loop(4):
            m.charge('move', 2)
            m.charge('indexed_write', 2)
    m.stage = 'construction'
    m.allocate('signed/current', 32+12)
    current_name = 'signed/current'
    p, signs = [0]*4, [0]*4
    for i in m.loop(4):
        m.write(p, i, m.constant(i)); m.write(signs, i, m.constant(0))
    for t in m.loop(len(word)):
        left_p, left_b = m.read(GENERATORS, m.read(word, t))
        new_name = 'signed/state/'+str(t)
        m.allocate(new_name, 32+12)
        q, b = [0]*4, [0]*4
        for i in m.loop(4):
            index = m.read(left_p, i)
            m.write(q, i, m.read(p, index))
            m.write(b, i, m.op('xor', m.read(left_b, i), m.read(signs, index)))
        m.release(current_name)
        p, signs = q, b
        m.charge('move', 2)
        current_name = new_name
    return p, signs


def evaluate(m, descriptor, values):
    p, signs = descriptor
    result = vector(m, 'signed/output', 4)
    for i in m.loop(4):
        value = m.read(values, m.read(p, i))
        m.charge('zero_compare')
        if m.read(signs, i):
            value = m.op('negate', value)
        m.write(result, i, m.scalar(value, committed=True))
    return result
