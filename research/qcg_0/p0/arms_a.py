"""Cell A arms (contract §5): B-Horner, B-Bezier, B-TS, B-PH, C1 (= B-PH), C2, and B-FD (NOT_APPLICABLE)."""
import poly
from arms import Arm
from events import result
from prep import bern, derive_steps

PN = ("X", "Y", "dx", "dy", "sg", "SS", "Nk")        # the seven retained polynomials of the all-cached arms


def eval_rows(ev, keys):
    """a1-a9 with the evaluator `ev(poly, t)` substituted for HORNER (DECAS / TSHIFT for the other arms)."""
    k = dict(zip(PN, keys))
    rows = [("a%d" % (i + 1), n, (k[p], "t"), (lambda p=p: lambda e, L: ev(e[k[p]], e["t"]))())
            for i, (n, p) in enumerate((("x", "X"), ("y", "Y"), ("xp", "dx"), ("yp", "dy"), ("sig", "sg"), ("S", "SS"), ("Nkv", "Nk")))]
    rows.append(("a8", "s2", ("sig",), lambda e, L: e["sig"] * e["sig"]))
    rows.append(("a9", "ok", ("sig",), lambda e, L: e["sig"].sgn() != 0))
    return rows


def pairs(env, order):
    return [env[k].pair() for k in order]


class Horner(Arm):
    name, retained = "B-Horner", PN

    def p_rows(self):
        return derive_steps()

    def q_rows(self, req):
        return eval_rows(poly.horner, PN)

    def outputs(self, env):
        o = pairs(env, ("x", "y", "xp", "yp", "s2", "sig", "S", "Nkv", "s2"))
        return {"values": o, "ok": env["ok"]}


class TS(Horner):
    name = "B-TS"

    def q_rows(self, req):
        return eval_rows(lambda p, t: poly.tshift(p, t)[0], PN)


class Bezier(Horner):
    name = "B-Bezier"
    retained = tuple("b" + n for n in PN)

    def p_rows(self):
        return derive_steps() + [("BERN." + n, "b" + n, (n,), (lambda n=n: lambda e, L: bern(e[n], n))()) for n in PN]

    def q_rows(self, req):
        return eval_rows(poly.decas, self.retained)


class PH(Arm):
    name, retained = "B-PH", ("U", "V", "U1", "V1", "X", "Y", "SS")

    def p_rows(self):
        return derive_steps()[:11]

    def q_rows(self, req):
        H = poly.horner
        return [
            ("b1", "u", ("U", "t"), lambda e, L: H(e["U"], e["t"])), ("b2", "v", ("V", "t"), lambda e, L: H(e["V"], e["t"])),
            ("b3", "u1", ("U1", "t"), lambda e, L: H(e["U1"], e["t"])), ("b4", "v1", ("V1", "t"), lambda e, L: H(e["V1"], e["t"])),
            ("b5", "uu", ("u",), lambda e, L: e["u"] * e["u"]), ("b6", "vv", ("v",), lambda e, L: e["v"] * e["v"]),
            ("b7", "uv", ("u", "v"), lambda e, L: e["u"] * e["v"]), ("b8", "xp", ("uu", "vv"), lambda e, L: e["uu"] - e["vv"]),
            ("b9", "yp", ("uv",), lambda e, L: e["uv"].twice()), ("b10", "sig", ("uu", "vv"), lambda e, L: e["uu"] + e["vv"]),
            ("b11", "s2", ("sig",), lambda e, L: e["sig"] * e["sig"]), ("b12", "m1", ("u", "v1"), lambda e, L: e["u"] * e["v1"]),
            ("b13", "m2", ("u1", "v"), lambda e, L: e["u1"] * e["v"]), ("b14", "Np", ("m1", "m2"), lambda e, L: e["m1"] - e["m2"]),
            ("b15", "Nkv", ("Np",), lambda e, L: e["Np"].twice()), ("b16", "x", ("X", "t"), lambda e, L: H(e["X"], e["t"])),
            ("b17", "y", ("Y", "t"), lambda e, L: H(e["Y"], e["t"])), ("b18", "S", ("SS", "t"), lambda e, L: H(e["SS"], e["t"])),
            ("b19", "ok", ("sig",), lambda e, L: e["sig"].sgn() != 0),
        ]

    def outputs(self, env):
        return Horner.outputs(self, env)


class C1(PH):
    name = "C1"


class C2(Arm):
    name, retained = "C2", ("U", "V", "X", "Y", "SS")

    def p_rows(self):
        return derive_steps()[:9]

    def q_rows(self, req):
        T = poly.tshift

        def proj(e, L):
            jU, jV, jX, jY, jS = e["jU"], e["jV"], e["jX"], e["jY"], e["jS"]
            return {"x": jX[0], "xp": jX[1], "y": jY[0], "yp": jY[1], "S": jS[0], "sig": jS[1],
                    "U": jU[0], "U1": jU[1], "V": jV[0], "V1": jV[1]}
        return [
            ("c1", "jU", ("U", "t"), lambda e, L: T(e["U"], e["t"])), ("c2", "jV", ("V", "t"), lambda e, L: T(e["V"], e["t"])),
            ("c3", "jX", ("X", "t"), lambda e, L: T(e["X"], e["t"])), ("c4", "jY", ("Y", "t"), lambda e, L: T(e["Y"], e["t"])),
            ("c5", "jS", ("SS", "t"), lambda e, L: T(e["SS"], e["t"])),
            ("c6", "v", ("jU", "jV", "jX", "jY", "jS"), proj),
            ("c7", "s2", ("v",), lambda e, L: e["v"]["sig"] * e["v"]["sig"]),
            ("c8", "m1", ("v",), lambda e, L: e["v"]["U"] * e["v"]["V1"]), ("c9", "m2", ("v",), lambda e, L: e["v"]["U1"] * e["v"]["V"]),
            ("c10", "Np", ("m1", "m2"), lambda e, L: e["m1"] - e["m2"]), ("c11", "Nkv", ("Np",), lambda e, L: e["Np"].twice()),
            ("c12", "ok", ("v",), lambda e, L: e["v"]["sig"].sgn() != 0),
        ]

    def outputs(self, env):
        v = env["v"]
        env = dict(env, x=v["x"], xp=v["xp"], y=v["y"], yp=v["yp"], S=v["S"], sig=v["sig"])
        return Horner.outputs(self, env)


class FD(Arm):
    """Random-access Cell A: forward differencing has no meaning; NOT_APPLICABLE, nothing charged (owner D-2)."""
    name = "B-FD"

    def prepare(self):
        return None

    def request(self, qid, tpair, req="BUNDLE"):
        return result("NOT_APPLICABLE")


ARMS = (Horner, Bezier, TS, PH, C1, C2, FD)
