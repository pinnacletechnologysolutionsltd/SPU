"""Deterministic comparator vector set for NUM-SOM-2 (no dependence on the Python random module)."""
M = 1 << 32
EDGE = [-2**31, -2**31 + 1, -65536, -2, -1, 0, 1, 2, 65536, 2**31 - 2, 2**31 - 1]


class Xorshift64:
    def __init__(self, seed):
        self.s = seed

    def next(self):
        s = self.s
        s ^= (s << 13) & (2**64 - 1)
        s ^= s >> 7
        s ^= (s << 17) & (2**64 - 1)
        self.s = s
        return s

    def below(self, n):
        return self.next() % n


def clamp(x):
    return max(-2**31, min(2**31 - 1, x))


def vectors():
    """34,641 (lhs, rhs) pairs: all edge-combination pairs (14,641) plus 20,000 pseudo-random pairs."""
    combos = [(p, q) for p in EDGE for q in EDGE]
    out = [(a, b) for a in combos for b in combos]
    rng = Xorshift64(0x2026102700000001)

    def comp():
        k = rng.below(10)
        if k < 4:
            return rng.below(M) - 2**31
        if k < 8:
            return rng.below(2001) - 1000
        return clamp(EDGE[rng.below(len(EDGE))] + rng.below(7) - 3)

    for _ in range(20000):
        out.append(((comp(), comp()), (comp(), comp())))
    return out


def hex_lines(vecs):
    enc = lambda p, q: ((p & (M - 1)) << 32) | (q & (M - 1))
    return ["%016x%016x" % (enc(*a), enc(*b)) for a, b in vecs]
