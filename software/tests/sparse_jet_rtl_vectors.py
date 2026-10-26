"""Generate bounded, independent Cauchy expectations, never hand-edited fixtures."""

import random
from sparse_jet_reference import P, ZERO, dense, pairs
from sparse_jet_model import windows


def reference_tag(n, at, bt, mul):
    if mul:
        occupied = [i + j for i in range(at[0], at[1] + 1)
                    for j in range(bt[0], bt[1] + 1) if i + j <= n]
    else:
        occupied = [i for tag in (at, bt) for i in range(tag[0], tag[1] + 1)]
    return (min(occupied), max(occupied)) if occupied else (n + 1, 0)


def make_vectors(n):
    rng = random.Random(131110 + n)
    out = []
    for at in windows(n):
        for bt in windows(n):
            def operand(tag):
                return tuple(tuple(rng.randrange(P) for _ in range(4)) if tag[0] <= i <= tag[1]
                             else ZERO for i in range(n + 1))
            a, b = operand(at), operand(bt)
            out.extend((a, b, at, bt, mul) for mul in (True, False))
    basis = [tuple(int(i == j) for i in range(4)) for j in range(4)]
    s = pow(15, (P + 1) // 4, P)
    directed = [(x, y) for x in basis for y in basis]
    directed += [((P-1,)*4, (P-1,)*4), ((s,0,0,1), (s,0,0,P-1)), (ZERO, ZERO)]
    for x, y in directed:
        out.append(((x,) + (ZERO,)*n, (y,) + (ZERO,)*n, (0,n), (0,n), True))
    a = tuple((i+1, P-1, 2, 3) for i in range(n+1))
    out.append((a, tuple(tuple(-x % P for x in row) for row in a), (0,n), (0,n), False))
    return out


def write_vectors(path, n):
    vectors = make_vectors(n)
    with path.open("x") as stream:
        for a, b, at, bt, mul in vectors:
            expected = dense(a, b) if mul else tuple(tuple((x+y) % P for x,y in zip(u,v)) for u,v in zip(a,b))
            tag = reference_tag(n, at, bt, mul)
            count = len(pairs(n, at, bt)) if mul else 0
            stream.write(" ".join(map(str, (int(mul), *at, *bt, *tag, count))) + "\n")
            for u, v, row in zip(a, b, expected):
                for x,y,z in zip(u,v,row):
                    stream.write(f"{x:08x} {y:08x} {z:08x}\n")
    return len(vectors)
