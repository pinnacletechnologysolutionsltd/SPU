"""Sequential PH family: PH (Horner on U,V,..), PHFD (forward-difference tables) = C1, and the C2 jet arm (contract §5)."""
import poly
from arms_seq import B_REQ, C_REQ, Seq
from ledger import lit
from prep import derive_steps

PB = ("U", "V", "U1", "V1", "X", "Y", "SS")


def coef(jet, i):
    """Jet coefficient i; beyond the jet's order (= degree) it is exactly zero (free read, no operation)."""
    return jet[i] if i < len(jet) else lit(0, jet[0].L)


class SeqPH(Seq):
    kind, name = "H", "PH"

    def get(self, e, p, k):
        if self.kind == "H":
            return poly.horner(e[p], e["t"])
        tab = e["f" + p]
        if k > 0:
            e["f" + p] = tab = poly.fdstep(list(tab))
        return tab[0]

    def p_rows(self):
        rows = derive_steps()[:11]
        if self.kind == "F":
            rows += [("FDINIT." + n, "f" + n, (n, "delta"), (lambda n=n: lambda e, L: poly.fdinit(e[n], e["delta"]))()) for n in PB]
        return rows

    @property
    def retained(self):
        return (tuple(("f" if self.kind == "F" else "") + n for n in PB)) + (("Sprev",) if self.tape == "S3" else ())

    @property
    def evolving(self):
        return self.retained if self.kind == "F" else ("Sprev",)

    def q_rows(self, k):
        g = lambda p: (lambda e, L: self.get(e, p, k))
        R = [("b1", "u", g("U")), ("b2", "v", g("V")), ("b3", "u1", g("U1")), ("b4", "v1", g("V1")),
             ("b5", "uu", lambda e, L: e["u"] * e["u"]), ("b6", "vv", lambda e, L: e["v"] * e["v"]),
             ("b7", "uv", lambda e, L: e["u"] * e["v"]), ("b8", "xp", lambda e, L: e["uu"] - e["vv"]),
             ("b9", "yp", lambda e, L: e["uv"].twice()), ("b10", "sig", lambda e, L: e["uu"] + e["vv"]),
             ("b11", "s2", lambda e, L: e["sig"] * e["sig"]), ("b12", "m1", lambda e, L: e["u"] * e["v1"]),
             ("b13", "m2", lambda e, L: e["u1"] * e["v"]), ("b14", "Np", lambda e, L: e["m1"] - e["m2"]),
             ("b15", "Nkv", lambda e, L: e["Np"].twice()), ("b16", "x", g("X")), ("b17", "y", g("Y")), ("b18", "S", g("SS")),
             ("b19", "ok", lambda e, L: e["sig"].sgn() != 0), ("b20", "Tx", lambda e, L: e["xp"] / e["sig"]),
             ("b21", "Ty", lambda e, L: e["yp"] / e["sig"]), ("b22", "inc", lambda e, L: e["S"] - e["Sprev"])]
        out = [(lab, tgt, (), fn) for lab, tgt, fn in R if lab in B_REQ[self.tape] and not (lab == "b22" and k == 0)]
        if self.tape == "S3":
            out.append(("keep", "Sprev", (), lambda e, L: e["S"]))
        return out


class SeqPHFD(SeqPH):
    kind, name = "F", "PHFD"


class SeqC1(SeqPHFD):
    name = "C1"


class SeqC2(Seq):
    kind, name = "J", "C2"
    JETS = {"c1": ("jU", "U"), "c2": ("jV", "V"), "c3": ("jX", "X"), "c4": ("jY", "Y"), "c5": ("jS", "SS")}

    def p_rows(self):
        return derive_steps()[:9]

    @property
    def retained(self):
        return ("U", "V", "X", "Y", "SS") + (("Sprev",) if self.tape == "S3" else ())

    @property
    def evolving(self):
        return self.retained

    def q_rows(self, k):
        req = C_REQ[self.tape]
        out = []
        if k > 0:                                         # shifts replace the retained jets; at k = 0 they are read unshifted
            for lab, (tgt, src) in self.JETS.items():
                if lab in req:
                    out.append((lab, src, (), (lambda src=src: lambda e, L: poly.tshift(e[src], e["h"]))()))
        proj = {"c6a": ("x", "y"), "c6b": ("x", "xp", "y", "yp", "sig"), "c6": ("x", "xp", "y", "yp", "S", "sig", "U", "U1", "V", "V1")}
        src = {"x": ("X", 0), "xp": ("X", 1), "y": ("Y", 0), "yp": ("Y", 1), "S": ("SS", 0), "sig": ("SS", 1),
               "U": ("U", 0), "U1": ("U", 1), "V": ("V", 0), "V1": ("V", 1)}
        for lab in ("c6a", "c6b", "c6"):
            if lab in req:
                out.append((lab, "v", (), (lambda lab=lab: lambda e, L: {n: coef(e[src[n][0]], src[n][1]) for n in proj[lab]})()))
        v = lambda n: (lambda e, L: e["v"][n])
        more = [("c7", "s2", lambda e, L: e["v"]["sig"] * e["v"]["sig"]), ("c8", "m1", lambda e, L: e["v"]["U"] * e["v"]["V1"]),
                ("c9", "m2", lambda e, L: e["v"]["U1"] * e["v"]["V"]), ("c10", "Np", lambda e, L: e["m1"] - e["m2"]),
                ("c11", "Nkv", lambda e, L: e["Np"].twice()), ("c12", "ok", lambda e, L: e["v"]["sig"].sgn() != 0),
                ("c13", "Tx", lambda e, L: e["v"]["xp"] / e["v"]["sig"]), ("c14", "Ty", lambda e, L: e["v"]["yp"] / e["v"]["sig"]),
                ("c15", "inc", lambda e, L: e["v"]["S"] - e["Sprev"])]
        out += [(lab, tgt, (), fn) for lab, tgt, fn in more if lab in req and not (lab == "c15" and k == 0)]
        if self.tape == "S3":
            out.append(("keep", "Sprev", (), lambda e, L: e["v"]["S"]))
        return out

    def outputs(self, env):
        w = dict(env["v"], **{k: env[k] for k in ("s2", "Nkv", "Tx", "Ty", "inc") if k in env})
        names = {"S1": ("x", "y"), "S2": ("x", "y", "xp", "yp", "sig", "Tx", "Ty"),
                 "S3": ("x", "y", "xp", "yp", "sig", "Tx", "Ty", "Nkv", "s2")}[self.tape]
        o = {"values": [w[n].pair() for n in names]}
        if "inc" in w:
            o["inc_prev"] = w["inc"].pair()
        return o
