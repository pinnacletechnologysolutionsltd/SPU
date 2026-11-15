"""SPU-ECO-5 geometry layer above spu_ir.Program: points, quadrance, orientation, triple-quad, Python operators.

A Num wraps one IR value, so `+`, `-`, `*` and `**2` create exactly one IR operation each, in Python evaluation order.
Nothing is rewritten, reordered or simplified, and arithmetic refusal is not hidden: a program that refuses reports it
(see spu_v03_backend.predict). Integers are coerced to constants at the point of use. `**` accepts only 2 (an explicit
product fixes the operation order); `-x` is `0 - x` (one constant and one SSUB, which can refuse for -2^63).
Operation order of the library functions is part of their definition (documented in GEOMETRY_GUIDE.md)."""
from collections import namedtuple
from spu_ir import Program, IRError
import spu_v03_backend as B

Point = namedtuple('Point', 'x y')
Compiled = namedtuple('Compiled', 'asm image words instructions prediction exact')

class Num:
    def __init__(self, g, v): self.g, self.v = g, v
    def _co(self, o):
        if isinstance(o, Num):
            if o.g is not self.g: raise IRError('operands belong to different Geometry programs')
            return o
        if isinstance(o, int) and not isinstance(o, bool): return self.g.const(o)
        raise IRError(f'cannot use {type(o).__name__} as an operand; use an int, a tuple through Geometry.const, or a Num')
    def _op(self, name, a, b): return Num(self.g, getattr(self.g.prog, name)(a.v, b.v))
    def __add__(self, o): return self._op('add', self, self._co(o))
    def __radd__(self, o): return self._op('add', self._co(o), self)
    def __sub__(self, o): return self._op('sub', self, self._co(o))
    def __rsub__(self, o): return self._op('sub', self._co(o), self)
    def __mul__(self, o): return self._op('mul', self, self._co(o))
    def __rmul__(self, o): return self._op('mul', self._co(o), self)
    def __neg__(self): return self._op('sub', self._co(0), self)
    def __pow__(self, n):
        if n != 2 or isinstance(n, bool): raise IRError('only **2 is supported; write explicit products to fix the operation order')
        return Num(self.g, self.g.prog.square(self.v))

class Geometry:
    """One program over Q(sqrt3). Values are (a + b*sqrt3)/d, given as an int or an (a, b, d) tuple."""
    def __init__(self): self.prog = Program()
    def const(self, a, b=0, d=1):
        if isinstance(a, tuple): a, b, d = a
        return Num(self, self.prog.const(a, b, d))
    def point(self, x, y):                                    # coordinates are created in the order x, y
        mk = lambda c: c if isinstance(c, Num) else self.const(c)
        return Point(mk(x), mk(y))
    def result(self, x): self.prog.result(x.v)
    def compile(self):
        asm, img, words, ins, rout = B.compile_v03(self.prog)
        return Compiled(asm, img, len(words), ins, B.predict(ins, rout), self.prog.exact())

def quadrance(a, b):                                          # sub dx, sub dy, square dx, square dy, add
    dx, dy = b.x - a.x, b.y - a.y
    return dx ** 2 + dy ** 2

def orientation(a, b, c):                                     # (B-A) x (C-A): bx-ax, cx-ax, by-ay, cy-ay, then u*v - w*z
    ux, vx, uy, vy = b.x - a.x, c.x - a.x, b.y - a.y, c.y - a.y
    return ux * vy - uy * vx

def triple_quad(q1, q2, q3):                                  # (Q1+Q2+Q3)^2 - 2(Q1^2+Q2^2+Q3^2); the constant 2 is created after s
    s = (q1 + q2) + q3
    t = (q1 ** 2 + q2 ** 2) + q3 ** 2
    return s ** 2 - 2 * t

def triple_quad_points(a, b, c): return triple_quad(quadrance(a, b), quadrance(b, c), quadrance(c, a))
