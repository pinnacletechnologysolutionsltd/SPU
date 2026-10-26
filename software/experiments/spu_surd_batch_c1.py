"""C1 exact software candidates; production robotics and C0 remain unchanged."""
import math
from fractions import Fraction
from software.experiments import spu_lossless_cpu_c0 as c0


def signed_width(v):
    return (v.bit_length() if v >= 0 else (~v).bit_length()) + 1


class Trace:
    def __init__(self, width=None):
        self.width = width
        self.counts = dict(add=0, multiply=0, conjugate=0, divide=0,
                           gcd=0, lcm=0, integer_division=0, fallback=0)
        self.widths = dict(input=1, product=1, accumulator=1, output=1)

    def observe(self, role, *values):
        self.widths[role] = max(self.widths[role], *(signed_width(v) for v in values))
        return self.width is not None and any(signed_width(v) > self.width for v in values)


class Algebra:
    def __init__(self, eager=True, trace=None):
        self.eager, self.trace = eager, trace

    def count(self, key, amount=1):
        if self.trace:
            self.trace.counts[key] += amount

    def observe(self, role, *values):
        return self.trace.observe(role, *values) if self.trace else False

    def canonical(self, x):
        a, b, d = x
        if d == 0:
            raise ZeroDivisionError('zero denominator')
        if d < 0:
            a, b, d = -a, -b, -d
        self.count('gcd', 2)
        g = math.gcd(math.gcd(abs(a), abs(b)), d)
        self.count('integer_division', 3)
        return a // g, b // g, d // g

    def finish(self, x, overflow):
        if overflow:
            self.count('fallback')  # all expressions already evaluated in exact wide integers
        self.observe('output', *x)
        return self.canonical(x) if self.eager else x

    def add(self, x, y):
        a, b, d = x
        c, e, f = y
        self.count('add')
        self.count('lcm'); self.count('gcd'); self.count('integer_division', 3)
        L = math.lcm(d, f)
        u, v = L // d, L // f
        products = (a*u, c*v, b*u, e*v)
        out = products[0] + products[1], products[2] + products[3], L
        overflow = self.observe('product', *products)
        overflow = self.observe('accumulator', *out) or overflow
        return self.finish(out, overflow)

    def multiply(self, x, y):
        a, b, d = x
        c, e, f = y
        self.count('multiply')
        products = a*c, b*e, 3*b*e, a*e, b*c, d*f
        out = products[0] + products[2], products[3] + products[4], products[5]
        overflow = self.observe('product', *products)
        overflow = self.observe('accumulator', *out) or overflow
        return self.finish(out, overflow)

    def conjugate(self, x):
        self.count('conjugate')
        return self.finish((x[0], -x[1], x[2]), self.observe('accumulator', -x[1]))

    def divide(self, x, y):
        self.count('divide')
        a, b, d = y
        norm = a*a - 3*b*b
        self.observe('product', a*a, b*b, 3*b*b)
        self.observe('accumulator', norm)
        if not norm:
            raise ZeroDivisionError('zero norm')
        z = self.multiply(x, self.conjugate(y))
        return self.canonical((z[0]*d*d, z[1]*d*d, z[2]*norm))


def triples(inputs):
    vector, joint = inputs
    result = []
    for x in (*vector.components(), joint.f, joint.g, joint.h):
        d = math.lcm(x.p.denominator, x.q.denominator)
        result.append((x.p.numerator*(d//x.p.denominator),
                       x.q.numerator*(d//x.q.denominator), d))
    return tuple(result)


def shared_block(values):
    d = math.lcm(*(x[2] for x in values))
    return tuple((a*(d//f), b*(d//f), d) for a, b, f in values)


def materialize(values):
    return tuple((Fraction(a, d), Fraction(b, d)) for a, b, d in values)


def kernel(values, eager=True, trace=None):
    op = Algebra(eager, trace)
    if trace:
        trace.observe('input', *(v for x in values for v in x))
    a, b, c, d, f, g, h = values
    def rotate(v, j):
        A, B, C, D = v
        F, G, H = j
        return (A, op.add(op.add(op.multiply(F, B), op.multiply(H, C)), op.multiply(G, D)),
                op.add(op.add(op.multiply(G, B), op.multiply(F, C)), op.multiply(H, D)),
                op.add(op.add(op.multiply(H, B), op.multiply(G, C)), op.multiply(F, D)))
    forward = rotate((a, b, c, d), (f, g, h))
    def subtract(x, y):
        return op.add(x, (-y[0], -y[1], y[2]))
    inverse = (subtract(op.multiply(f, f), op.multiply(g, h)),
               subtract(op.multiply(h, h), op.multiply(f, g)),
               subtract(op.multiply(g, g), op.multiply(f, h)))
    recovered = rotate(forward, inverse)
    return tuple(op.canonical(x) for x in (*forward, *recovered))


def batch_aos(batch, eager=True, trace=None):
    return tuple(materialize(kernel(row, eager, trace)) for row in batch)


def to_soa(batch):
    return tuple(tuple(row[i] for row in batch) for i in range(7))


def batch_soa(columns, eager=True, trace=None):
    return batch_aos(tuple(zip(*columns)), eager, trace)
