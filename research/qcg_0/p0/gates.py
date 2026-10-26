"""Pareto evaluation (contract §2): lexicographic comparator, guard set G*, trigger set Tr, TRADE-OFF, ledger equality."""
GUARD = ("M", "A", "S", "D", "K", "G_calls", "G_bits", "W_bits", "W_peak_red", "W_peak_raw", "T_ret_peak")
TRIGGER = ("M", "A", "D", "K", "T_ret_peak", "W_peak_red")
ORDER = TRIGGER                                   # comparator key: (M, A, D, K, T_ret_peak, W_peak_red)


def eligible(arms):
    """arms: {id: {"total": ledger total view, "all_ok": bool, "role": "conventional" | "candidate" | ...}}"""
    return sorted(a for a, v in arms.items() if v["role"] == "conventional" and v["all_ok"])


def comparator(arms):
    """Lexicographically smallest eligible arm on ORDER; ties broken by ascending ASCII arm id. None if none eligible."""
    ids = eligible(arms)
    return min(ids, key=lambda a: tuple(arms[a]["total"][c] for c in ORDER) + (a,)) if ids else None


def virtual_best(arms):
    ids = eligible(arms)
    return {c: min(arms[a]["total"][c] for a in ids) for c in GUARD} if ids else None


def evaluate(arms, cand):
    """Candidate vs the comparator: guards (all <=), triggers (>= 20% reduction, integer test 5*c <= 4*b, b > 0), TRADE-OFF."""
    comp = comparator(arms)
    if comp is None or not arms[cand]["all_ok"]:
        return {"comparator": comp, "candidate": cand, "verdict": "NOT_EVALUABLE"}
    c, b = arms[cand]["total"], arms[comp]["total"]
    guard = {k: c[k] <= b[k] for k in GUARD}
    trig = {k: b[k] > 0 and 5 * c[k] <= 4 * b[k] for k in TRIGGER}
    tradeoff = c["T_ret_peak"] < b["T_ret_peak"] and (c["M"] > b["M"] or c["A"] > b["A"])
    sig = all(guard.values()) and any(trig.values())
    return {"comparator": comp, "candidate": cand, "guard": guard, "trigger": trig, "tradeoff": tradeoff,
            "signal": sig, "verdict": "SIGNAL" if sig else ("TRADE-OFF" if tradeoff else "NO_SIGNAL")}


def ledgers_equal(a, b):
    """EQ-1 / EQ-2: every category and phase identical (cumulative P, Q and peaks)."""
    return a.cum == b.cum and a.pk == b.pk


def dominates(a, b):
    """a dominates b on the full registered cost vector (GUARD categories): all <=, at least one <."""
    return all(a[k] <= b[k] for k in GUARD) and any(a[k] < b[k] for k in GUARD)


def frontier(arms):
    """Reporting only: nondominated eligible conventional arms (ASCII order). Mutually equal vectors are all kept.
    Does not influence the comparator, guards, triggers or any verdict."""
    ids = eligible(arms)
    return [a for a in ids if not any(dominates(arms[b]["total"], arms[a]["total"]) for b in ids if b != a)]
