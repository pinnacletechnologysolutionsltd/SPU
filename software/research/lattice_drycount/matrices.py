"""Dense rational matrix construction/composition, without zero shortcuts."""
from .arrays import matrix, vector, encode
from .exact import add, multiply


def identity(m, name, n):
    result = matrix(m, name, n)
    for i in m.loop(n):
        row = m.read(result, i)
        for j in m.loop(n):
            m.charge('equality_compare')
            m.write(row, j, (m.constant(int(i == j)), m.constant(1)))
    return result


def root_matrix(m, root, name):
    n = len(root)
    alpha = encode(m, root, name+'/alpha')
    result = matrix(m, name, n)
    for i in m.loop(n):
        row = m.read(result, i)
        for j in m.loop(n):
            m.charge('equality_compare')
            one = (m.constant(int(i == j)), m.constant(1))
            value = add(m, one, multiply(m, m.read(alpha, i), m.read(alpha, j)), True)
            m.write(row, j, value)
    m.release(name+'/alpha')
    return result


def compose(m, left, right, name):
    n = len(left)
    result = matrix(m, name, n)
    with m.frame(12, 4):
        for i in m.loop(n):
            row = m.read(result, i)
            for j in m.loop(n):
                value = (m.constant(0), m.constant(1))
                for k in m.loop(n):
                    x = m.read(m.read(left, i), k)
                    y = m.read(m.read(right, k), j)
                    value = add(m, value, multiply(m, x, y))
                m.write(row, j, value)
    return result


def evaluate(m, current, values, name):
    n = len(values)
    result = vector(m, name, n, 128)
    with m.frame(8, 4):
        for i in m.loop(n):
            value = (m.constant(0), m.constant(1))
            for j in m.loop(n):
                value = add(m, value, multiply(m, m.read(m.read(current, i), j), m.read(values, j)))
            m.write(result, i, value)
    return result
