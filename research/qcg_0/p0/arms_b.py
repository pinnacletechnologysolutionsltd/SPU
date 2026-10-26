"""Cell B arms (contract §5): B-COMP, stand-alone C1 (h1-h13), E-COMP / E-BEZ / E-TS (k1-k8); steps P16-P31."""
import poly
from arms import Arm
from events import Refusal
from ledger import lit
from prep import bern, derive_steps, pcomp, pder, pmul, trim

H = poly.horner


def p16(e, L):
    return trim(pder(e["phi"]))


class Base(Arm):
    """Common output: (psi_x, psi_y, psi_x', psi_y', s_signed, s_nonneg, S_inc) and the monotonicity flag ok = (phi' >= 0)."""
    cell = "B"

    def outputs(self, env):
        if not env["ok"]:
            raise Refusal("NONMONOTONE")        # whole-request refusal; the transaction rolls back
        o = [env[k].pair() for k in ("psx", "psy", "psxp", "psyp", "s", "s", "Sinc")]
        return {"values": o, "ok": env["ok"]}


class BComp(Base):
    name, retained = "B-COMP", ("X", "Y", "dx", "dy", "sg", "SS", "phi", "phip")

    def p_rows(self):
        return derive_steps()[:9] + [("P16", "phip", ("phi",), p16)]

    def q_rows(self, req):
        return [
            ("e1", "f", ("phi", "t"), lambda e, L: H(e["phi"], e["t"])), ("e2", "g", ("phip", "t"), lambda e, L: H(e["phip"], e["t"])),
            ("e3", "ok", ("g",), lambda e, L: e["g"].sgn() >= 0),
            ("e4", "psx", ("X", "f"), lambda e, L: H(e["X"], e["f"])), ("e5", "psy", ("Y", "f"), lambda e, L: H(e["Y"], e["f"])),
            ("e6", "q1", ("dx", "f"), lambda e, L: H(e["dx"], e["f"])), ("e7", "q2", ("dy", "f"), lambda e, L: H(e["dy"], e["f"])),
            ("e8", "q3", ("sg", "f"), lambda e, L: H(e["sg"], e["f"])),
            ("e9", "psxp", ("g", "q1"), lambda e, L: e["g"] * e["q1"]), ("e10", "psyp", ("g", "q2"), lambda e, L: e["g"] * e["q2"]),
            ("e11", "s", ("g", "q3"), lambda e, L: e["g"] * e["q3"]), ("e12", "Sinc", ("SS", "f"), lambda e, L: H(e["SS"], e["f"])),
        ]


class C1B(Base):
    name, retained = "C1", ("phi", "phip", "cx", "cy", "cSS")

    def p_rows(self):
        d = derive_steps()[:9]
        return d + [("P16", "phip", ("phi",), p16), ("P17", "cx", ("X", "phi"), lambda e, L: trim(pcomp(e["X"], e["phi"]))),
                    ("P18", "cy", ("Y", "phi"), lambda e, L: trim(pcomp(e["Y"], e["phi"]))),
                    ("P22", "cSS", ("SS", "phi"), lambda e, L: trim(pcomp(e["SS"], e["phi"])))]

    def prepare(self):   # X, Y, SS are scratch of preparation; only the retained names survive
        return super().prepare()

    def q_rows(self, req):
        one = lambda L: lit(1, L)
        return [
            ("h1", "f", ("phi", "t"), lambda e, L: H(e["phi"], e["t"])), ("h2", "g", ("phip", "t"), lambda e, L: H(e["phip"], e["t"])),
            ("h3", "ok", ("g",), lambda e, L: e["g"].sgn() >= 0), ("h4", "ff", ("f",), lambda e, L: e["f"] * e["f"]),
            ("h5", "w1", ("ff",), lambda e, L: one(L) - e["ff"]), ("h6", "psxp", ("g", "w1"), lambda e, L: e["g"] * e["w1"]),
            ("h7", "w2", ("g", "f"), lambda e, L: e["g"] * e["f"]), ("h8", "psyp", ("w2",), lambda e, L: e["w2"].twice()),
            ("h9", "w3", ("ff",), lambda e, L: one(L) + e["ff"]), ("h10", "s", ("g", "w3"), lambda e, L: e["g"] * e["w3"]),
            ("h11", "psx", ("cx", "t"), lambda e, L: H(e["cx"], e["t"])), ("h12", "psy", ("cy", "t"), lambda e, L: H(e["cy"], e["t"])),
            ("h13", "Sinc", ("cSS", "t"), lambda e, L: H(e["cSS"], e["t"])),
        ]


class EComp(Base):
    name = "E-COMP"
    retained = ("cx", "cy", "cdx", "cdy", "csg", "cSS", "phip")
    ev = staticmethod(poly.horner)

    def p_rows(self):
        c = lambda src: (lambda e, L: trim(pcomp(e[src], e["phi"])))
        m = lambda a: (lambda e, L: trim(pmul(e["phip"], e[a])))
        return derive_steps()[:9] + [
            ("P16", "phip", ("phi",), p16), ("P17", "cx", ("X", "phi"), c("X")), ("P18", "cy", ("Y", "phi"), c("Y")),
            ("P19", "cdxp", ("dx", "phi"), c("dx")), ("P20", "cdyp", ("dy", "phi"), c("dy")), ("P21", "csgp", ("sg", "phi"), c("sg")),
            ("P22", "cSS", ("SS", "phi"), c("SS")), ("P23", "cdx", ("phip", "cdxp"), m("cdxp")),
            ("P24", "cdy", ("phip", "cdyp"), m("cdyp")), ("P25", "csg", ("phip", "csgp"), m("csgp"))]

    def q_rows(self, req):
        ev = self.ev
        r = [("k1", "g", ("phip", "t"), lambda e, L: H(e["phip"], e["t"])), ("k2", "ok", ("g",), lambda e, L: e["g"].sgn() >= 0)]
        for i, (tgt, src) in enumerate((("psx", "cx"), ("psy", "cy"), ("psxp", "cdx"), ("psyp", "cdy"), ("s", "csg"), ("Sinc", "cSS"))):
            r.append(("k%d" % (i + 3), tgt, (src, "t"), (lambda src=src: lambda e, L: ev(e[src], e["t"]))()))
        return r


class ETS(EComp):
    name = "E-TS"
    ev = staticmethod(lambda p, t: poly.tshift(p, t)[0])


class EBez(EComp):
    name = "E-BEZ"
    retained = ("bcx", "bcy", "bcdx", "bcdy", "bcsg", "bcSS", "phip")
    ev = staticmethod(poly.decas)

    def p_rows(self):
        rows = super().p_rows()
        names = ("cx", "cy", "cdx", "cdy", "csg", "cSS")
        return rows + [("P%d" % (26 + i), "b" + n, (n,), (lambda n=n: lambda e, L: bern(e[n], n))()) for i, n in enumerate(names)]

    def q_rows(self, req):
        rows = super().q_rows(req)
        ren = {"cx": "bcx", "cy": "bcy", "cdx": "bcdx", "cdy": "bcdy", "csg": "bcsg", "cSS": "bcSS"}
        return [(lab, tgt, tuple(ren.get(x, x) for x in rd), (lambda f=fn, rd=rd: lambda e, L: f(dict(e, **{k: e[v] for k, v in ren.items() if v in e}), L))())
                for lab, tgt, rd, fn in rows]


ARMS_B = (BComp, C1B, EComp, EBez, ETS)
