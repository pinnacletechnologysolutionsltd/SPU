"""Set-associative fast-tier model with five replacement policies (see spec.py)."""
from __future__ import annotations

import spec

POLICIES = ("lru", "lfu", "structural", "adaptive", "belady")


def line_weights(cell_at, size):
    """S(line) = sum of subtree sizes of the records in the line (padding = 0)."""
    w = []
    for i in range(0, len(cell_at), spec.PER_LINE):
        w.append(sum(size[c] for c in cell_at[i:i + spec.PER_LINE] if c is not None))
    return w


def _next_use(lines):
    nxt, last = [0] * len(lines), {}
    for i in range(len(lines) - 1, -1, -1):
        nxt[i] = last.get(lines[i], float("inf"))
        last[lines[i]] = i
    return nxt


def simulate(slots, policy, weights):
    lines = [s // spec.PER_LINE for s in slots]
    nxt = _next_use(lines) if policy == "belady" else None
    sets = [dict() for _ in range(spec.SETS)]      # line -> entry
    hits = misses = 0
    util = []
    for t, (ln, slot) in enumerate(zip(lines, slots)):
        st = sets[ln % spec.SETS]
        e = st.get(ln)
        if e is not None:
            hits += 1
            e["last"], e["count"] = t, e["count"] + 1
        else:
            misses += 1
            if len(st) == spec.WAYS:
                victim = _victim(st, policy, weights)
                util.append(len(st[victim]["touched"]) / spec.PER_LINE)
                del st[victim]
            e = st[ln] = {"last": t, "count": 1, "touched": set()}
        e["touched"].add(slot)
        if nxt is not None:
            e["next"] = nxt[t]
    util += [len(e["touched"]) / spec.PER_LINE for st in sets for e in st.values()]
    return {"hits": hits, "misses": misses, "accesses": len(slots),
            "utilisation": sum(util) / len(util) if util else 0.0}


def _victim(st, policy, weights):
    def lru(ln):
        return st[ln]["last"]
    if policy == "lru":
        return min(st, key=lru)
    if policy == "lfu":
        return min(st, key=lambda ln: (st[ln]["count"], lru(ln)))
    if policy == "structural":
        return min(st, key=lambda ln: (weights[ln], lru(ln)))
    if policy == "adaptive":
        return min(st, key=lambda ln: (weights[ln] + spec.ALPHA * st[ln]["count"], lru(ln)))
    if policy == "belady":
        return min(st, key=lambda ln: (-st[ln]["next"], ln))
    raise ValueError(policy)
