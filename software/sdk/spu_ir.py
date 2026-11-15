"""SPU-ECO-2 mathematical IR: an ordered, straight-line list of exact operations over Q(sqrt3). Target independent.

Knows nothing about registers, opcodes, encodings, image size or refusal: those belong to a backend.
The order in which operations are created IS the operation order; no backend or pass may reorder, merge or simplify.
Operations: const(a, b, d) = (a + b sqrt3)/d (kept exactly as given, not canonicalized), add, sub, mul, square
(recorded as mul(x, x)), and result(x). No parser, no inputs: a v0.3 backend needs every value bound to a constant.
exact() evaluates the mathematical value with unbounded rationals (exact mode); it models no machine limit."""
from fractions import Fraction as F

class IRError(Exception): pass

class Value:
    __slots__ = ('prog', 'idx')
    def __init__(self, prog, idx): self.prog, self.idx = prog, idx

class Program:
    def __init__(self): self.stmts, self.out = [], None      # stmt: ('const', (a, b, d)) | (op, i, j), op in add/sub/mul
    def _new(self, st): self.stmts.append(st); return Value(self, len(self.stmts) - 1)
    def _ref(self, v):
        if not isinstance(v, Value) or v.prog is not self: raise IRError('operand is not a value of this program')
        return v.idx
    def const(self, a, b=0, d=1):
        if not all(isinstance(x, int) for x in (a, b, d)): raise IRError('constants are integer tuples (a, b, d)')
        if d == 0: raise IRError('constant denominator is 0')
        return self._new(('const', (a, b, d)))
    def add(self, x, y): return self._new(('add', self._ref(x), self._ref(y)))
    def sub(self, x, y): return self._new(('sub', self._ref(x), self._ref(y)))
    def mul(self, x, y): return self._new(('mul', self._ref(x), self._ref(y)))
    def square(self, x): return self.mul(x, x)
    def result(self, x):
        if self.out is not None: raise IRError('result already selected')
        self.out = self._ref(x)

    def exact(self):
        """Exact mathematical value of the result as (p, q) Fractions meaning p + q sqrt3 (exact mode, no refusal)."""
        if self.out is None: raise IRError('no result selected')
        v = []
        for st in self.stmts:
            if st[0] == 'const': a, b, d = st[1]; v.append((F(a, d), F(b, d))); continue
            x, y = v[st[1]], v[st[2]]
            v.append({'add': lambda: (x[0] + y[0], x[1] + y[1]), 'sub': lambda: (x[0] - y[0], x[1] - y[1]),
                      'mul': lambda: (x[0] * y[0] + 3 * x[1] * y[1], x[0] * y[1] + x[1] * y[0])}[st[0]]())
        return v[self.out]
