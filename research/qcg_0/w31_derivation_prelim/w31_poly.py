"""Contract §5 primitives; one operation counter per outer primitive call."""
from math import comb
from w31_arithmetic import Q


def trim(a):
    while len(a) > 1 and a[-1].n == 0:
        a.pop()
    return a


class Program:
    def __init__(self, trace, prefix):
        self.trace, self.prefix, self.index = trace, prefix, 0

    def op(self, name, *args):
        self.index += 1
        return getattr(self.trace, name)(*args, f'{self.prefix}.{self.index}')

    def horner(self, a, t):
        v = a[-1]
        for x in reversed(a[:-1]):
            v = self.op('add', self.op('mul', v, t), x)
        return v

    def decas(self, a, t):
        a = list(a)
        for r in range(1, len(a)):
            for j in range(len(a)-r):
                diff = self.sub(a[j+1], a[j])
                a[j] = self.op('add', a[j], self.op('mul', t, diff))
        return a[0]

    def sub(self, x, y):
        return self.op('add', x, Q(-y.n, y.d))

    def tshift(self, a, t):
        a = list(a)
        for j in range(len(a)-1):
            for i in range(len(a)-2, j-1, -1):
                a[i] = self.op('add', a[i], self.op('mul', t, a[i+1]))
        return a

    def fdinit(self, a, delta):
        t, v = Q(0), []
        for k in range(len(a)):
            if k:
                t = self.op('add', t, delta)
            v.append(self.horner(a, t))
        out = [v[0]]
        for r in range(1, len(a)):
            for j in range(len(a)-r):
                v[j] = self.sub(v[j+1], v[j])
            out.append(v[0])
        return out

    def fdstep(self, a):
        a = list(a)
        for j in range(len(a)-1):
            a[j] = self.op('add', a[j], a[j+1])
        return a

    def pmul(self, a, b):
        out = [None] * (len(a)+len(b)-1)
        for i, x in enumerate(a):
            for j, y in enumerate(b):
                term = self.op('mul', x, y)
                out[i+j] = term if out[i+j] is None else self.op('add', out[i+j], term)
        return trim(out)

    def padd(self, a, b, subtract=False):
        out = []
        for i in range(max(len(a), len(b))):
            if i < min(len(a), len(b)):
                out.append(self.sub(a[i], b[i]) if subtract else self.op('add', a[i], b[i]))
            elif i < len(a):
                out.append(a[i])
            else:
                out.append(Q(-b[i].n, b[i].d) if subtract else b[i])
        return trim(out)

    def pder(self, a):
        return trim([self.op('mul', a[i], Q(i)) for i in range(1, len(a))] or [Q(0)])

    def pint(self, a):
        return trim([Q(0)] + [self.op('div', x, Q(i+1)) for i, x in enumerate(a)])

    def pscale2(self, a):
        return trim([self.op('shift2', x) for x in a])

    def pcomp(self, a, b):
        acc = [a[-1]]
        for x in reversed(a[:-1]):
            acc = self.pmul(acc, b)
            acc[0] = self.op('add', acc[0], x)
        return trim(acc)

    def bern(self, a, name=None):
        out, d = [], len(a)-1
        for j in range(d+1):
            v = None
            for i in range(j+1):
                w = Q(comb(j, i), comb(d, i))
                self.trace.import_q(w, f'{".".join(self.prefix.split(".")[:2])}.import.w.{name or self.prefix.split(".")[-1]}.{j}.{i}')
                term = self.op('mul', w, a[i])
                v = term if v is None else self.op('add', v, term)
            out.append(v)
        return out
