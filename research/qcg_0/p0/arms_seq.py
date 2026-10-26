"""Sequential tapes S1-S3 (contract §5): arms Horner, Bezier, TS, FD, PH, PHFD (= C1), C2; t_k = k/16, h = 1/16."""
from math import gcd
import poly
from arms import Arm
from prep import bern, derive_steps

PN = ("X", "Y", "dx", "dy", "sg", "SS", "Nk")
A_REQ = {"S1": ("a1", "a2"), "S2": ("a1", "a2", "a3", "a4", "a5", "a9", "a10", "a11"),
         "S3": tuple("a%d" % i for i in range(1, 13))}
B_REQ = {"S1": ("b16", "b17"), "S2": ("b1", "b2", "b5", "b6", "b7", "b8", "b9", "b10", "b16", "b17", "b19", "b20", "b21"),
         "S3": tuple("b%d" % i for i in range(1, 23))}
C_REQ = {"S1": ("c3", "c4", "c6a"), "S2": ("c3", "c4", "c5", "c6b", "c12", "c13", "c14"),
         "S3": tuple(["c1", "c2", "c3", "c4", "c5", "c6"] + ["c%d" % i for i in range(7, 16)])}


def kq(k):
    g = gcd(k, 16)
    return (k // g, 16 // g)


class Seq(Arm):
    kind = "H"                       # H Horner, Z Bezier, T Taylor shift, F forward differences
    name = "Horner"
    tape = "S1"

    def __init__(self, profile, source, tape):
        super().__init__(profile, dict(source, delta=[(1, 16)]))
        self.tape = tape

    def import_source(self, env):
        super().import_source(env)
        env["delta"] = env["delta"][0]

    # evaluator over the retained representation; `k` is the sample index
    def get(self, e, p, k):
        kd = self.kind
        if kd == "H":
            return poly.horner(e[p], e["t"])
        if kd == "Z":
            return poly.decas(e["b" + p], e["t"])
        if kd == "T":
            if k == 0:
                return e[p][0]
            e[p] = poly.tshift(e[p], e["h"])
            return e[p][0]
        tab = e["f" + p]
        if k > 0:
            e["f" + p] = tab = poly.fdstep(list(tab))
        return tab[0]

    def extra_env(self, env, L):
        from ledger import Q
        env["h"] = Q.imp(1, 16, L, "h")

    def p_rows(self):
        rows = derive_steps()
        if self.kind == "Z":
            rows += [("BERN." + n, "b" + n, (n,), (lambda n=n: lambda e, L: bern(e[n], n))()) for n in PN]
        if self.kind == "F":
            rows += [("FDINIT." + n, "f" + n, (n, "delta"), (lambda n=n: lambda e, L: poly.fdinit(e[n], e["delta"]))()) for n in PN]
        return rows

    @property
    def retained(self):
        pre = {"H": "", "Z": "b", "T": "", "F": "f"}[self.kind]
        return tuple(pre + n for n in PN) + (("Sprev",) if self.tape == "S3" else ())

    @property
    def evolving(self):
        return self.retained if self.kind in "TF" else ("Sprev",)

    def q_rows(self, req):
        k = req
        g = lambda p: (lambda e, L: self.get(e, p, k))
        R = [("a1", "x", g("X")), ("a2", "y", g("Y")), ("a3", "xp", g("dx")), ("a4", "yp", g("dy")), ("a5", "sig", g("sg")),
             ("a6", "S", g("SS")), ("a7", "Nkv", g("Nk")), ("a8", "s2", lambda e, L: e["sig"] * e["sig"]),
             ("a9", "ok", lambda e, L: e["sig"].sgn() != 0), ("a10", "Tx", lambda e, L: e["xp"] / e["sig"]),
             ("a11", "Ty", lambda e, L: e["yp"] / e["sig"]), ("a12", "inc", lambda e, L: e["S"] - e["Sprev"])]
        out = []
        for lab, tgt, fn in R:
            if lab not in A_REQ[self.tape]:
                continue
            if lab == "a12":
                if k == 0:
                    continue
            out.append((lab, tgt, (), fn))
        if self.tape == "S3":
            out.append(("keep", "Sprev", (), lambda e, L: e["S"]))   # bookkeeping: next sample's Sprev (no operation)
        return out

    def outputs(self, env):
        names = {"S1": ("x", "y"), "S2": ("x", "y", "xp", "yp", "sig", "Tx", "Ty"),
                 "S3": ("x", "y", "xp", "yp", "sig", "Tx", "Ty", "Nkv", "s2")}[self.tape]
        o = {"values": [env[n].pair() for n in names]}
        if "inc" in env:
            o["inc_prev"] = env["inc"].pair()
        return o

    def run_tape(self, rows=17):
        """Frozen tape of `rows` requests from the post-preparation snapshot. Contract §3 gives every request exactly one status and
        leaves committed state untouched by a refusal, but defines no recovery for an evolving tape: a request whose retained inputs
        (stepped tables/jets, or S3's previous sample) were not advanced by the refused sample would run off the k/16 grid. Such
        requests are not issued and are recorded as NOT_ISSUED (not a contract status); state-independent requests proceed."""
        res, stale = [], False
        snap = self.snapshot()
        for k in range(rows):
            if stale:
                res.append({"status": "NOT_ISSUED", "code": "STATE_DEPENDENT_AFTER_REFUSAL", "event": None, "outputs": None})
                continue
            res.append(self.request(k, kq(k), k))
            if res[-1]["status"] != "OK" and set(self.evolving) & set(self.retained):
                stale = True
        self.restore(snap)
        return res

    def request(self, qid, tpair, req="BUNDLE"):
        return super().request(qid, tpair, req)


def make(kind, name, tape_cls_extra=None):
    return type(name, (Seq,), {"kind": kind, "name": name})


SeqH, SeqZ, SeqT, SeqF = make("H", "Horner"), make("Z", "Bezier"), make("T", "TS"), make("F", "FD")
