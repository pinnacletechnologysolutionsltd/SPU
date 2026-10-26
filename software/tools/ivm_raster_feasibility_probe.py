#!/usr/bin/env python3
"""Bounded Rung-4 mathematical probe; not a GPU implementation or RTL oracle.

Run: python3 software/tools/ivm_raster_feasibility_probe.py
Integer axial determinants are checked against Fraction ray crossings in a
different affine chart. Projection uses an explicit tetrahedral embedding.
No display-quality, timing, synthesis or physical claims follow from this.
"""
from fractions import Fraction as F
from itertools import product
import random


def project(q):
    a, b, c, d = q
    return 2*b-c-d, -b+2*c-d, 3*a-b-c-d  # u=U/3, v=V/3


def edge(p, q):
    x, y = p
    u, v = q
    return y-v, u-x, x*v-y*u


def value(e, p):
    return e[0]*p[0] + e[1]*p[1] + e[2]


def edges(t):
    return [edge(t[1], t[2]), edge(t[2], t[0]), edge(t[0], t[1])]


def oriented(t, z):
    if value(edge(t[0], t[1]), t[2]) < 0:
        return [t[0], t[2], t[1]], [z[0], z[2], z[1]]
    return t, z


def covered(t, p):
    # Symbolic sample perturbation (+epsilon, +epsilon**2).
    return all(value(e, p) > 0 or
               (value(e, p) == 0 and (e[0] > 0 or
                (e[0] == 0 and e[1] > 0))) for e in edges(t))


def reference_coverage(t, p):
    # Different chart X=2u+v,Y=v; exact ray crossings, not edge predicates.
    eps = F(1, 10**6)  # sufficient for this bounded integer test population
    u, v = F(p[0])+eps, F(p[1])+eps*eps
    x, y = 2*u+v, v
    verts = [(2*a+b, b) for a, b in t]
    inside = False
    for (a, b), (c, d) in zip(verts, verts[1:]+verts[:1]):
        if (b > y) != (d > y):
            if x < a + (y-b)*F(c-a, d-b):
                inside = not inside
    return inside


def plane_reference(t, z):
    # Fraction Gaussian elimination in the other chart, independent of edges.
    m = [[F(2*u+v), F(v), F(1), F(h)] for (u, v), h in zip(t, z)]
    for col in range(3):
        pivot = next(i for i in range(col, 3) if m[i][col])
        m[col], m[pivot] = m[pivot], m[col]
        divisor = m[col][col]
        m[col] = [x/divisor for x in m[col]]
        for i in range(3):
            if i != col:
                scale = m[i][col]
                m[i] = [x-scale*y for x, y in zip(m[i], m[col])]
    a, b, c = [m[i][3] for i in range(3)]
    return lambda p: a*(2*p[0]+p[1])+b*p[1]+c


def numerator(t, z):
    ee = edges(t)
    return tuple(sum(h*e[j] for h, e in zip(z, ee)) for j in range(3)), sum(e[2] for e in ee)


def main():
    projection_count = 0
    for a, b, c in product(range(-3, 4), repeat=3):
        d = -a-b-c
        q = a, b, c, d
        U, V, h = project(q)
        xyz = (a+b-c-d, a-b+c-d, a-b-c+d)
        # E1=(2,0,-2), E2=(0,2,-2), normal=(1,1,1).
        reconstructed = (F(2*U+h, 3), F(2*V+h, 3), F(-2*U-2*V+h, 3))
        assert reconstructed == xyz
        assert project(tuple(x+7 for x in q)) == (U, V, h)
        assert h == 4*a
        projection_count += 1
    # A zero-sum integer world point need not project to integer axial sites.
    assert project((1, 0, 0, -1)) == (1, 1, 4)
    rng = random.Random(4602026)
    samples = [(3*u, 3*v) for u, v in product(range(-4, 5), repeat=2)]
    triangles = []
    while len(triangles) < 100:
        projected = []
        for _ in range(3):
            abc = [rng.randint(-4, 4) for _ in range(3)]
            projected.append(project((*abc, -sum(abc))))
        t = [(U, V) for U, V, h in projected]
        if value(edge(t[0], t[1]), t[2]) == 0:
            continue
        triangles.append(oriented(t, [h for U, V, h in projected]))
    for t, z in triangles:
        n, D = numerator(t, z)
        ref = plane_reference(t, z)
        for p in samples:
            assert covered(t, p) == reference_coverage(t, p)
            assert F(value(n, p), D) == ref(p)
    pair_count = 0
    for (t0, z0), (t1, z1) in zip(triangles[::2], triangles[1::2]):
        n0, d0 = numerator(t0, z0)
        n1, d1 = numerator(t1, z1)
        H = tuple(d1*a-d0*b for a, b in zip(n0, n1))
        r0, r1 = plane_reference(t0, z0), plane_reference(t1, z1)
        for v in range(-4, 5):
            acc = value(H, (-12, 3*v))
            for u in range(-4, 5):
                assert (acc <= 0) == (r0((3*u, 3*v)) <= r1((3*u, 3*v)))
                acc += 3*H[0]
                pair_count += 1
    t0, t1 = [(0, 0), (4, 0), (4, 4)], [(0, 0), (4, 4), (0, 4)]
    assert all(covered(t0, p)+covered(t1, p) == 1 for p in product(range(1, 4), repeat=2))
    inclusive_faults = sum(all(value(e, p) >= 0 for e in edges(t0)) and
                           all(value(e, p) >= 0 for e in edges(t1)) for p in [(1, 1), (2, 2), (3, 3)])
    assert inclusive_faults == 3  # negative control: all-inclusive double ownership
    depths = []
    for size in (7, 8):
        t, z = [(0, 0), (size, 0), (0, size)], [0, 12, 0]
        for (u, v), h in zip(t, z):
            k = h//12
            assert project((3*k, u-k, v-k, -k-u-v)) == (3*u, 3*v, h)
        depths.append(plane_reference(t, z)((1, 1)))
    assert depths == [F(12, 7), F(3, 2)]
    assert not depths[0] <= depths[1] and int(depths[0]) <= int(depths[1])
    print(f'PASS: {projection_count} exact Quadray projections + gauge controls')
    print(f'PASS: {len(triangles)*len(samples)} coverage and rational-depth comparisons')
    print(f'PASS: {pair_count} add-only exact pair-depth comparisons')
    print(f'PASS: shared-edge ownership; inclusive mutation gives {inclusive_faults} double hits')
    print(f'COUNTEREXAMPLE: integer IVM vertices give depths {depths}; integer truncation selects wrong winner')


if __name__ == '__main__':
    main()
