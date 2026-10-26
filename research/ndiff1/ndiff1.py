"""NDIFF-1: composition cost of POLY / PRIM / GEN / GEN_REBUILD.  python3 -I -B ndiff1.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rep import *
import rep
from composed import comp_eval
import cost, oracle
from fractions import Fraction as F
from math import lcm
from curve import sample_curve

H, R = S3(F(1, 2)), S3(0, F(1, 2))
ROT = {"r30": (R, H), "r60": (H, R), "r90": (ZERO, ONE)}
SC = {"s3": S3(3), "sr3": S3(0, 1), "s2": S3(2)}
CHAINS = {
    "A rot60": [("rot", "r60")],
    "B rot30": [("rot", "r30")],
    "C scale3": [("scale", "s3")],
    "D scale r3": [("scale", "sr3")],
    "E t2": [("t2", None)],
    "F rot30,scale r3": [("rot", "r30"), ("scale", "sr3")],
    "G t2,rot30": [("t2", None), ("rot", "r30")],
    "H rot30,scale r3,t2": [("rot", "r30"), ("scale", "sr3"), ("t2", None)],
    "I t2,rot30,t2,scale r3": [("t2", None), ("rot", "r30"), ("t2", None), ("scale", "sr3")],
    "J rot60,scale3,rot60,scale3": [("rot", "r60"), ("scale", "s3"), ("rot", "r60"), ("scale", "s3")],
    "K rot30 x4": [("rot", "r30")] * 4,
}
KINDS = ["POLY", "PRIM", "GEN", "GEN_REBUILD", "COMP_POLY", "COMP_PH"]
T0 = S3(F(2, 5), F(1, 7))
GATE0 = "ORIGINAL: GEN total < materialised POLY total at N=100 and representable throughout"
GATE = "REVISED (control added after first results): GEN total < min(all other strategies incl. composed-at-evaluation) at N=100"


def arg(op, name):
    return ROT[name] if op == "rot" else SC[name] if op == "scale" else None


def facts(chain, t, base):
    if not chain:
        a, b, h = (oracle.pairs(base.a), oracle.pairs(base.b), oracle.pairs(base.h))
        f = oracle.curve_facts(a, b, h, (base.X[0].p, base.X[0].q), (base.Y[0].p, base.Y[0].q), t)
        return f["P"], f["T"]
    op, nm = chain[-1]
    if op == "t2":
        P, T = facts(chain[:-1], oracle.mul(t, t), base)
        k = oracle.mul((F(2), F(0)), t)
        return P, (oracle.mul(T[0], k), oracle.mul(T[1], k))
    sc = lambda v, k: oracle.mul(v, k)
    P, T = facts(chain[:-1], t, base)
    if op == "scale":
        k = (SC[nm].p, SC[nm].q)
        return (sc(P[0], k), sc(P[1], k)), (sc(T[0], k), sc(T[1], k))
    c, s = ((ROT[nm][0].p, ROT[nm][0].q), (ROT[nm][1].p, ROT[nm][1].q))
    neg = lambda u: (-u[0], -u[1])
    rot = lambda V: (oracle.add(sc(V[0], c), neg(sc(V[1], s))), oracle.add(sc(V[0], s), sc(V[1], c)))
    return rot(P), rot(T)


def check(out, chain, base):
    P, T = facts(chain, (T0.p, T0.q), base)
    pr = lambda z: (z.p, z.q)
    q = oracle.add(oracle.mul(P[0], P[0]), oracle.mul(P[1], P[1]))
    s2 = oracle.add(oracle.mul(T[0], T[0]), oracle.mul(T[1], T[1]))
    d = oracle.add(oracle.mul(P[0], T[0]), oracle.mul(P[1], T[1]))
    assert (pr(out["P"][0]), pr(out["P"][1])) == P and (pr(out["T"][0]), pr(out["T"][1])) == T
    assert pr(out["Q"]) == q and pr(out["speed2"]) == s2 and pr(out["dQ"]) == (2 * d[0], 2 * d[1])
    if "sigma" in out:
        assert pr(out["sigma"] * out["sigma"]) == s2


def metrics(r):
    polys = [r.X, r.Y] + ([r.a, r.b, r.h] if r.a else [])
    dens = [c.p.denominator for p in (r.X, r.Y) for c in p] + [c.q.denominator for p in (r.X, r.Y) for c in p]
    return {"deg_pos": len(r.X) - 1, "coef_bits(num,den)": max(pbits(p) for p in polys), "lcm_den_bits": lcm(*dens).bit_length(),
            "stored": sum(len(p) for p in polys)}


def run_chain(chain, base):
    res = {}
    for kind in KINDS:
        if kind.startswith("COMP"):
            continue
        r, fail = rep.from_ph(base, kind), None
        field.reset()
        try:
            for op, nm in chain:
                r = rep.step(r, op, arg(op, nm))
        except rep.Unrepresentable as e:
            fail = str(e)
        if fail:
            res[kind] = {"unrepresentable": fail}
            continue
        m = field.snapshot()
        ev = cost.ph_eval if kind != "POLY" else cost.poly_eval
        out, e = cost.run_counted(lambda c, t, o: ev(c, t, o), r, T0, 1)
        check(out, chain, base)
        w = lambda s: s["rat_mul"] + s["rat_add"]
        res[kind] = {"maint": w(m), "maint_mul": m["rat_mul"], "eval": w(e), "eval_mul": e["rat_mul"], **metrics(r)}
    for nm, ev in (("COMP_POLY", cost.poly_eval), ("COMP_PH", cost.ph_eval)):
        field.reset()
        out = comp_eval(base, chain, ev, T0, arg)
        e = field.snapshot()
        check(out, chain, base)
        res[nm] = {"maint": 0, "maint_mul": 0, "eval": e["rat_mul"] + e["rat_add"], "eval_mul": e["rat_mul"], "deg_pos": len(base.X) - 1,
                   "coef_bits(num,den)": (0, 0), "lcm_den_bits": 0, "stored": len(base.X) * 2 + (0 if nm == "COMP_POLY" else len(base.a) * 2 + 1)}
    return res


def best(res, n):
    tot = {k: v["maint"] + n * v["eval"] for k, v in res.items() if "unrepresentable" not in v}
    return min(tot, key=tot.get), tot


def main():
    base = sample_curve()
    print("GATE0:", GATE0, "\nGATE :", GATE, "\nunits: rational mul+add (model in rep.py/field.py)")
    tally = {n: {} for n in (1, 10, 100)}
    for name, chain in CHAINS.items():
        res = run_chain(chain, base)
        print(f"\n{name}")
        p = res["POLY"]
        for kind in KINDS:
            x = res[kind]
            if "unrepresentable" in x:
                print(f"  {kind:12s} UNREPRESENTABLE: {x['unrepresentable']}")
                continue
            tot = lambda n: x["maint"] + n * x["eval"]
            cross = ""
            if kind != "POLY":
                if x["eval"] < p["eval"] and x["maint"] > p["maint"]:
                    cross = f"N*={(x['maint'] - p['maint']) / (p['eval'] - x['eval']):.1f}"
                elif x["eval"] < p["eval"]:
                    cross = "cheaper at every N"
                else:
                    cross = "never (eval not cheaper)"
            print(f"  {kind:12s} maint {x['maint']:5d} eval {x['eval']:4d} total@N=1/10/100: {tot(1)}/{tot(10)}/{tot(100)} "
                  f"deg {x['deg_pos']:2d} bits {x['coef_bits(num,den)']} lcm {x['lcm_den_bits']:3d}b stored {x['stored']:3d} {cross}")
        for n in (1, 10, 100):
            b, tot = best(res, n)
            tally[n][name] = b
            g0 = "GEN<POLY" if tot["GEN"] < tot["POLY"] else "GEN>=POLY"
            g1 = "GEN best" if b == "GEN" else f"best={b}"
            print(f"  N={n:<3d} {g0:10s} {g1}")
    summary(tally)


def summary(tally):
    for n, d in tally.items():
        cnt = {}
        for b in d.values():
            cnt[b] = cnt.get(b, 0) + 1
        print(f"best strategy count over {len(d)} chains at N={n}: {dict(sorted(cnt.items()))}")


if __name__ == "__main__":
    main()
