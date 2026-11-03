"""Bounded research model: architectural tuples and software-only norm facts."""
from fractions import Fraction

from software.experiments import surd_register_exact as ex


class Model:
    def __init__(self, width=64):
        self.width = width
        self.reg = [None] * 8
        self.version = [0] * 8
        self.bounds = [None] * 8
        self.equal = set()
        self.norm_equal = set()
        self.cache = {}
        self.stats = {"norm_evaluations": 0, "norm_reuses": 0,
                      "bookkeeping": 0, "proof_multiplications": 0}

    def _key(self, i):
        return (i, self.version[i])

    def _write(self, i, value):
        old = self._key(i)
        self.stats["bookkeeping"] += len(self.equal) + len(self.norm_equal) + 2
        self.equal = {p for p in self.equal if old not in p}
        self.norm_equal = {p for p in self.norm_equal if old not in p}
        self.cache.pop(old, None)
        self.version[i] += 1
        self.reg[i] = value
        self.bounds[i] = (abs(value.a), abs(value.b), value.d)

    def load(self, i, value):
        if not ex.valid(value, self.width):
            return "INVALID"
        self._write(i, value)
        return "OK"

    def multiply(self, dst, left, right):
        x, y = self.reg[left], self.reg[right]
        if x is None or y is None:
            return "INVALID"
        raw, _ = ex.raw("MUL", x, y)
        value = raw if ex.valid(raw, self.width) else ex.normalize(raw)
        if not ex.valid(value, self.width):
            return "OVERFLOW"
        self._write(dst, value)
        return "OK"

    def prove_equal(self, left, right):
        x, y = self.reg[left], self.reg[right]
        self.stats["bookkeeping"] += 1
        if x is None or y is None:
            return False
        self.stats["proof_multiplications"] += 4
        a_matches = x.a * y.d == y.a * x.d
        b_matches = x.b * y.d == y.b * x.d
        if not a_matches or not b_matches:
            return False
        pair = frozenset((self._key(left), self._key(right)))
        self.equal.add(pair)
        self.norm_equal.add(pair)
        return True

    def prove_norm_equal(self, left, right):
        x, y = self.reg[left], self.reg[right]
        self.stats["bookkeeping"] += 1
        if x is None or y is None:
            return False
        self.stats["proof_multiplications"] += 10
        lhs = (x.a*x.a - 3*x.b*x.b) * (y.d*y.d)
        rhs = (y.a*y.a - 3*y.b*y.b) * (x.d*x.d)
        if lhs != rhs:
            return False
        self.norm_equal.add(frozenset((self._key(left), self._key(right))))
        return True

    def prove_bounds(self, i, a_bound, b_bound, d_bound):
        self.stats["bookkeeping"] += 1
        r = self.reg[i]
        if r is None or any(type(x) is not int or x < 0 for x in (a_bound, b_bound, d_bound)):
            return False
        if abs(r.a) > a_bound or abs(r.b) > b_bound or r.d > d_bound:
            return False
        self.bounds[i] = (a_bound, b_bound, d_bound)
        return True

    def norm(self, i):
        r = self.reg[i]
        if r is None:
            raise ValueError("uninitialized")
        key = self._key(i)
        self.stats["bookkeeping"] += 1
        if key in self.cache:
            self.stats["norm_reuses"] += 1
            return self.cache[key]
        for pair in self.norm_equal:
            self.stats["bookkeeping"] += 1
            if key in pair:
                for candidate in pair:
                    if candidate in self.cache:
                        self.cache[key] = self.cache[candidate]
                        self.stats["norm_reuses"] += 1
                        return self.cache[key]
        self.stats["norm_evaluations"] += 1
        result = Fraction(r.a*r.a - 3*r.b*r.b, r.d*r.d)
        self.cache[key] = result
        return result
