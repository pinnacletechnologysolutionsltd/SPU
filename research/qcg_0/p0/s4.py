"""S4 capability task (contract §4 P-1 references): retimed traversals against the supplemental dyadic and random rows."""
from account import Ledger
from events import P4096
from gen import make
from ledger import Q
import refs


def pr(x):
    return [x.n, x.d]


def status(r):
    return "OK" if r["status"] == "OK" else "REFUSED(%s)" % r["code"]


def s4(profile=P4096):
    """Supplemental P-1 rows: 4 representations x 17 dyadic rows, plus the 16 registered random points of the h-composite case."""
    cases = refs.load("P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json")["cases"]
    bad, ledgers, n = [], {}, 0
    for name, c in cases.items():
        L = Ledger(profile, name)
        g = make(c["polynomials"], L, -1 if "rev" in name else 1)
        for i, r in enumerate(c["dyadic_S4_rows"]):
            t, q = Q.imp(*r["parameter"], L, "t"), i

            def ask(kind):
                return g.request(kind, t, q)

            def eq(a, b, what):
                nonlocal n
                n += 1
                if a != b:
                    bad.append((name, i, what))
            eq([pr(v) for v in ask("POSITION")["outputs"]], r["position"], "position")
            eq([pr(v) for v in ask("VELOCITY")["outputs"]], r["velocity"], "velocity")
            eq(pr(ask("SPEED")["outputs"][0]), r["nonnegative_speed"], "speed")
            eq(pr(ask("SIGNED_RATE")["outputs"][0]), r["signed_progression_rate"], "rate")
            eq([pr(v) for v in ask("DIRECTION")["outputs"]], r["continued_direction"], "direction")
            for kind in ("TANGENT", "CURVATURE"):
                res = ask(kind)
                eq(status(res), r["requests"][kind], kind + ".status")
                if res["status"] == "OK" and kind == "TANGENT":
                    eq([pr(v) for v in res["outputs"]], r["unit_tangent"], "tangent")
                if res["status"] == "OK" and kind == "CURVATURE":
                    o = res["outputs"]
                    eq([pr(o[0]), pr(o[1])], r["curvature_pair"], "curvature_pair")
                    eq(pr(o[2]), r["signed_curvature"], "signed_curvature")
            eq(pr(ask("INTEGRAL")["outputs"][0]), r["representation_signed_integral"], "integral")
            eq(pr(ask("ACCUMULATED_LENGTH")["outputs"][0]), r["accumulated_length_increment"], "accumulated")
            eq(pr(ask("BASE_ORIENTED")["outputs"][0]), r["base_oriented_length_increment"], "base_oriented")
        for i, r in enumerate(c.get("registered_random_tape_rows") or []):
            t = Q.imp(*r["parameter"], L, "t")
            n += 1
            if [pr(v) for v in g.request("POSITION", t, 100 + i)["outputs"]] != r["position"]:
                bad.append((name, "random%d" % i, "position"))
        ledgers[name] = L.total()
    return {"checks": n, "mismatches": bad, "ledgers": ledgers}
