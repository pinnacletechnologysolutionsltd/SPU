"""Fixed-width arrays, matrix rows and owned lifetimes for the diagnostic model."""


def vector(m, name, count, width=64):
    m.allocate(name, 64+count*width)
    return [None]*count


def matrix(m, name, n):
    # Matrix header/count/shape plus individually owned row headers/counts.
    m.allocate(name, 128+n*(64+n*128))
    return [[None]*n for _ in range(n)]


def row_copy(m, source, target):
    for i in m.loop(len(source)):
        m.write(target, i, m.read(source, i))
    return target


def encode(m, source, name, surd=False):
    from .exact import normalize
    result = vector(m, name, len(source), 192 if surd else 128)
    for i in m.loop(len(source)):
        value = m.read(source, i)
        pair = (value, m.constant(0), m.constant(2)) if surd else (value, m.constant(2))
        m.write(result, i, normalize(m, pair))
    return result


def decode(m, source, name):
    from .exact import quotient
    result = vector(m, name, len(source))
    for i in m.loop(len(source)):
        value = m.read(source, i)
        if len(value) == 3:
            m.test(m.read(value, 1) == 0, 'SURD_NONRATIONAL', 'zero_compare')
        x = quotient(m, m.op('multiply', m.read(value, 0), m.constant(2)), m.read(value, len(value)-1))
        m.write(result, i, m.scalar(x, committed=True))
    return result
