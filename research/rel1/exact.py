"""Counted exact kernels shared by both REL-1 backends (declared shared dependency).

Scalars are Fraction or phy_r1 QF (Q(sqrt d)). `Ops` counts scalar mul/add/div at kernel
level; Python-object cost is not modelled. These counts are a model, not a measurement of
hardware cost.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from fractions import Fraction as Fr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phy_r1"))
from field import QF  # noqa: E402


class Ops(Counter):
    def total(self):
        return sum(self.values())


def zero(x):
    return x.is_zero() if isinstance(x, QF) else x == 0


def sign(x):
    return x.sign() if isinstance(x, QF) else (x > 0) - (x < 0)


def div(a, b):
    return (QF.of(a, b.d) if isinstance(b, QF) and not isinstance(a, QF) else a) / b


def dot(u, v, ops):
    acc = None
    for a, b in zip(u, v):
        if zero(a) or zero(b):
            continue
        ops["mul"] += 1
        t = a * b
        if acc is None:
            acc = t
        else:
            ops["add"] += 1
            acc = acc + t
    return Fr(0) if acc is None else acc


def matvec(H, v, ops):
    return [dot(row, v, ops) for row in H]


def nullspace(rows, ops):
    """Exact RREF; returns (basis of the nullspace, pivot columns)."""
    m = [list(r) for r in rows]
    ncol = len(m[0]) if m else 0
    piv, r = [], 0
    for c in range(ncol):
        k = next((i for i in range(r, len(m)) if not zero(m[i][c])), None)
        if k is None:
            continue
        m[r], m[k] = m[k], m[r]
        ops["div"] += 1
        inv = 1 / m[r][c] if not isinstance(m[r][c], QF) else m[r][c].inv()
        m[r] = [v * inv for v in m[r]]
        ops["mul"] += ncol
        for i in range(len(m)):
            if i != r and not zero(m[i][c]):
                f = m[i][c]
                ops["mul"] += ncol
                ops["add"] += ncol
                m[i] = [a - f * b for a, b in zip(m[i], m[r])]
        piv.append(c)
        r += 1
    basis = []
    for fc in (c for c in range(ncol) if c not in piv):
        v = [Fr(0)] * ncol
        v[fc] = Fr(1)
        for i, pc in enumerate(piv):
            v[pc] = -m[i][fc]
        basis.append(v)
    return basis, piv


def ldl(mat, ops):
    """Symmetric LDL^T with diagonal pivoting -> (rank, is_psd)."""
    a = [list(r) for r in mat]
    alive, rank, psd = list(range(len(a))), 0, True
    while alive:
        p = next((i for i in alive if not zero(a[i][i])), None)
        if p is None:
            if any(not zero(a[i][j]) for i in alive for j in alive):
                psd = False
                blk = [[a[i][j] for j in alive] for i in alive]
                rank += len(alive) - len(nullspace(blk, ops)[0])
            break
        if sign(a[p][p]) < 0:
            psd = False
        rank += 1
        alive.remove(p)
        for i in alive:
            if zero(a[i][p]):
                continue
            ops["div"] += 1
            f = div(a[i][p], a[p][p])
            for j in alive:
                if not zero(a[p][j]):
                    ops["mul"] += 1
                    ops["add"] += 1
                    a[i][j] = a[i][j] - f * a[p][j]
    return rank, psd
