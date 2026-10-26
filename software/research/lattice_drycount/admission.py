"""Shared fixture admission and input ownership; same scope for all five arms."""
from .arrays import vector, row_copy


def lattice(m, values, system):
    n = 4 if system == 'D4' else 8
    m.test(len(values) == n, 'VECTOR_SHAPE', 'shape_compare')
    total, parity = m.constant(0), None
    with m.frame(8, 4):
        for i in m.loop(n):
            v = m.scalar(m.read(values, i), committed=True)
            p = m.op('remainder', v, m.constant(2))
            if parity is None:
                parity = p
                m.charge('move')
            m.test(p == parity, 'LATTICE_PARITY')
            total = m.op('add', total, v)
        if system == 'D4':
            m.test(parity == 0, 'D4_PARITY', 'zero_compare')
        m.test(m.op('remainder', total, m.constant(4)) == 0, 'LATTICE_SUM', 'zero_compare')


def admit(m, case, arm):
    m.test(type(case) is dict, 'CASE_TYPE', 'type_check')
    m.charge('indexed_read', 3)
    system, values, word = case['system'], case['scaled_input'], case['generator_word']
    m.test(system in ('D4', 'E8'), 'SYSTEM')
    m.test(arm in ('coordinates', 'matrix', 'generator_word', 'surd', 'signed'), 'ARM')
    m.test(arm != 'signed' or system == 'D4', 'NOT_APPLICABLE')
    n = 4 if system == 'D4' else 8
    m.test(type(values) in (list, tuple) and type(word) in (list, tuple), 'INPUT_SHAPE', 'type_check')
    lattice(m, values, system)
    m.test(len(word) <= 256, 'WORD_LIMIT', 'range_compare')
    for i in m.loop(len(word)):
        token = m.read(word, i)
        m.test(type(token) is int, 'TOKEN_TYPE', 'type_check')
        m.test(0 <= token < n, 'TOKEN_RANGE', 'range_compare')
    m.allocate('constants', 64+16*64)
    m.allocate('profile', 32+5*32)
    x = row_copy(m, values, vector(m, 'input/vector', n))
    w = row_copy(m, word, vector(m, 'input/word', len(word), 2 if n == 4 else 3))
    return system, x, w
