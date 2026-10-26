"""Scene tree and the four layouts. Every layout is a bijection between
existing cell identities (a, b, l) and record slots; padding slots map to None.

Address overhead per access (defined before any result, from this code):
  key ops   axial 0; morton 33 (two 5-step magic spreads + 2 subs + or);
            gbt 11*l + 23*(K - l) (pre-division per level, then per digit:
            residue 9, lookup 1, subtract 2, divide 11); tiled 12 (no table)
  index     dense layouts (axial, morton, gbt) rank a sorted key array:
            ceil(log2 N) compares and 8 bytes/record; tiled uses padding instead
"""
from __future__ import annotations

from math import ceil, log2

import gbt
import spec
from algebra import e_mul, e_norm

UNITS = gbt.DIGITS[1:]


def build_tree():
    nodes, kids = [], {}
    stack = [(0, 0, spec.K)]
    while stack:
        c = stack.pop()
        nodes.append(c)
        a, b, l = c
        if l > 0 and (l == spec.K or
                      e_norm((a - spec.FOCUS[0], b - spec.FOCUS[1])) <= spec.REFINE_C * 7 ** l):
            kids[c] = gbt.children(c)
            stack.extend(reversed(kids[c]))
    return nodes, kids


class Scene:
    def __init__(self):
        self.nodes, self.kids = build_tree()
        self.node_set = set(self.nodes)
        self.leaves = [c for c in self.nodes if c not in self.kids]
        self.size = {}
        for c in sorted(self.nodes, key=lambda c: c[2]):        # leaves first
            self.size[c] = 1 + sum(self.size[k] for k in self.kids.get(c, []))
        self.addr = {c: gbt.address(c, spec.K) for c in self.nodes}

    def neighbour(self, c, u):
        a, b, l = c
        s = e_mul(u, gbt.pi_pow(l))
        return (a + s[0], b + s[1], l)

    def preorder(self):
        out = []

        def walk(c):
            out.append(c)
            for k in self.kids.get(c, []):
                walk(k)
        walk((0, 0, spec.K))
        return out


def _spread16(x):
    x &= 0xFFFF
    for s, m in ((8, 0x00FF00FF), (4, 0x0F0F0F0F), (2, 0x33333333), (1, 0x55555555)):
        x = (x | (x << s)) & m
    return x


def make_layout(scene, name):
    """Return (slot_of: dict cell->slot, cell_at: list slot->cell|None, key_ops, index_ops, index_bytes)."""
    n = len(scene.nodes)
    amin = min(c[0] for c in scene.nodes)
    bmin = min(c[1] for c in scene.nodes)
    if name == "axial":
        order = sorted(scene.nodes, key=lambda c: (c[2], c[1], c[0]))
    elif name == "morton":
        order = sorted(scene.nodes, key=lambda c: (c[2], _spread16(c[0] - amin)
                                                   | (_spread16(c[1] - bmin) << 1)))
    elif name == "gbt":
        order = scene.preorder()
    elif name == "tiled":
        return _tiled(scene)
    else:
        raise ValueError(name)
    slot_of = {c: i for i, c in enumerate(order)}
    key_ops = {"axial": lambda c: 0, "morton": lambda c: 33,
               "gbt": lambda c: 11 * c[2] + 23 * (spec.K - c[2])}[name]
    return slot_of, list(order), key_ops, ceil(log2(n)), 8 * n


def _tiled(scene):
    cell_at, slot_of = [], {}
    for l in sorted({c[2] for c in scene.nodes}):
        cs = [c for c in scene.nodes if c[2] == l]
        a0, b0 = min(c[0] for c in cs), min(c[1] for c in cs)
        w = (max(c[0] for c in cs) - a0) // 2 + 1
        h = (max(c[1] for c in cs) - b0) // 2 + 1
        base = len(cell_at)
        cell_at.extend([None] * (w * h * 4))
        for c in cs:
            da, db = c[0] - a0, c[1] - b0
            s = base + ((db >> 1) * w + (da >> 1)) * 4 + (db & 1) * 2 + (da & 1)
            cell_at[s] = c
            slot_of[c] = s
    return slot_of, cell_at, (lambda c: 12), 0, 0
