"""Uniform adapters over the two implementations (relational.py, conventional.py)."""
from __future__ import annotations

from fractions import Fraction as Fr

import conventional as C
import relational as R
from field import QF


def _bits(values):
    n = b = 0
    for v in values:
        for r in ((v.a, v.b) if isinstance(v, QF) else (v,)):
            n += 1
            b += Fr(r).numerator.bit_length() + Fr(r).denominator.bit_length()
    return n, b


class Relational:
    name = "relational"

    @staticmethod
    def admit(d, ops, count): return R.admit(ops)

    @staticmethod
    def transform(s, M, d, ops, count): return R.transform(s, M, ops)

    move, compute, reuse, observe = (staticmethod(R.move), staticmethod(R.compute),
                                     staticmethod(R.reuse), staticmethod(R.observe))

    @staticmethod
    def size(s):
        vals = [s.M[a][b] for a in range(3) for b in range(a, 3)] if s.kind == "metric" else \
               [c for p in s.P for c in p]
        return _bits(vals)


class Conventional:
    name = "conventional"
    admit, move, compute, reuse, observe = (staticmethod(C.admit), staticmethod(C.move),
                                            staticmethod(C.compute), staticmethod(C.reuse),
                                            staticmethod(C.observe))

    @staticmethod
    def transform(s, M, d, ops, count): return C.transform(M, d, ops, count)

    @staticmethod
    def size(s): return _bits([c for p in s.x for c in p])
