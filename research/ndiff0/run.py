"""NDIFF-0 Euclidean probe: python3 -I -B run.py  (host-only, stdlib, exact arithmetic)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction as F
from field import *
from curve import *
import cost, oracle

GATE = ("ADVANTAGE iff PH rational mul < every baseline's AND PH (rat mul + rat add) <= that baseline's, "
        "on the common output set, repeated evaluation; else NO COST ADVANTAGE DEMONSTRATED")
SAMPLES = [S3(0), S3(F(1, 3)), S3(F(1, 2)), S3(F(2, 5)), S3(F(1, 4), F(1, 4)), S3(F(-1, 3), F(1, 5))]


def pr(p):
    return (p.p, p.q)


def main():
    print("MODEL: surd mul=4mR+2aR+1kR, add=2aR, kmul=2kR (field.py)")
    print("GATE :", GATE)
    c = sample_curve()
    a_o, b_o, h_o = oracle.pairs(c.a), oracle.pairs(c.b), oracle.pairs(c.h)
    x0, y0 = pr(c.X[0]), pr(c.Y[0])
    res = {"degrees": {"X": len(c.X) - 1, "hodograph": len(c.xp) - 1, "sigma": len(c.sigma) - 1}}
    # correctness: every strategy vs independent oracle
    ok = 0
    for t0 in SAMPLES:
        f = oracle.curve_facts(a_o, b_o, h_o, x0, y0, pr(t0))
        for order in (1, 2):
            for name, fn in cost.STRATEGIES.items():
                out = fn(c, t0, order)
                exp = {"P": f["P"], "T": f["T"], "speed2": f["speed2"], "Q": f["Q"], "dQ": f["dQ"]}
                if order == 2:
                    exp["P2"] = f["P2"]
                for k, v in exp.items():
                    got = tuple(pr(z) for z in out[k]) if isinstance(out[k], tuple) else pr(out[k])
                    want = tuple(v) if isinstance(out[k], tuple) else v
                    assert got == want, (name, k, order, t0, got, want)
                    ok += 1
                if name == "PH":  # sigma^2 == speed2 and sigma == oracle-derived sqrt check
                    assert pr(out["sigma"] * out["sigma"]) == f["speed2"]
                    ok += 1
    print(f"CORRECTNESS: {ok} comparisons vs binomial-shift oracle, 3 strategies x 6 points x orders 1,2: all exact")
    # construction
    reset()
    c2 = sample_curve()
    cons = snapshot()
    reset()
    _ = (pder(c2.X), pder(c2.Y))
    base_extra = snapshot()
    res["construction"] = {"shared_generators_to_X_Y": cons, "baseline_extra_derivative_polys": base_extra, "PH_extra": "none (a,b stored)"}
    res["denominators"] = {"X": denominators(c.X), "Y": denominators(c.Y), "hodograph_x": denominators(c.xp)}
    res["bits"] = {"generators": pbits(c.a + c.b), "hodograph": pbits(c.xp + c.yp), "position": pbits(c.X + c.Y), "sigma": pbits(c.sigma)}
    # evaluation counts
    ev = {}
    for order in (1, 2):
        row = {}
        for name, fn in cost.STRATEGIES.items():
            outs = [cost.run_counted(fn, c, t, order) for t in SAMPLES]
            counts = {json.dumps(s, sort_keys=True) for _, s in outs}
            assert len(counts) == 1, "op counts must be data independent"
            row[name] = {**outs[0][1], "max_out_bits(num,den)": max(cost.out_bits(o) for o, _ in outs)}
        ev[f"order{order}"] = row
    res["eval"] = ev
    print(json.dumps(res, default=str, indent=1))
    for order in ("order1", "order2"):
        ph, others = ev[order]["PH"], [ev[order]["poly_horner"], ev[order]["jet_horner"]]
        wins = cost.gate(ph, others)
        print(order, "GATE ->", "ADVANTAGE" if wins else "NO COST ADVANTAGE DEMONSTRATED")


if __name__ == "__main__":
    main()
