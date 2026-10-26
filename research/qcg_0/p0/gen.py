"""Generator (U, V, h) with its exact observables and requests (contract §4 S4, §5 S5/S6). All arithmetic through ledgered Q."""
from events import Invalid, Refusal, result
from ledger import Q
from poly import horner
from prep import padd, pder, pint, pmul, pscale2, psub, trim


def qs(pairs, L, name):
    return [Q.imp(n, d, L, "%s.%d" % (name, i)) for i, (n, d) in enumerate(pairs)]


class Gen:
    """r' = h (U^2 - V^2, 2UV). `orient` is the retiming metadata: -1 for a reversed base traversal, else +1."""

    def __init__(self, U, V, h, x0, y0, L, orient=1):
        self.L, self.U, self.V, self.h, self.orient = L, U, V, h, orient
        UU, VV, UV = trim(pmul(U, U)), trim(pmul(V, V)), trim(pmul(U, V))
        self.wxp, self.g = trim(psub(UU, VV)), trim(padd(UU, VV))
        self.wyp = trim(pscale2(UV))
        self.dx, self.dy = trim(pmul(h, self.wxp)), trim(pmul(h, self.wyp))
        self.X, self.Y = trim(pint(self.dx)), trim(pint(self.dy))
        self.X[0], self.Y[0] = x0, y0
        self.S = trim(pint(trim(pmul(h, self.g))))
        self.U1, self.V1 = trim(pder(U)), trim(pder(V))
        self.hsgn = None

    def h_sign(self):
        """Constant sign of h on [0,1] when all coefficients agree (K tests); else None (not a single polynomial length)."""
        s = {c.sgn() for c in self.h if True}
        s.discard(0)
        return s.pop() if len(s) == 1 else (0 if not s else None)

    def request(self, kind, t, qid=0):
        L = self.L
        L.begin("Q", qid)
        try:
            out = self._req(kind, t)
            L.commit()
            return result("OK", None, None, out)
        except Refusal as e:
            L.rollback()
            return result("REFUSED", e.code, e.event)
        except Invalid as e:
            L.rollback()
            return result("INVALID", e.code, e.event)

    def _dir(self, t):
        u, v = horner(self.U, t), horner(self.V, t)
        uu, vv = u * u, v * v
        g = uu + vv
        return (uu - vv) / g, ((u * v).twice()) / g, g

    def _req(self, kind, t):
        H = horner
        if kind == "POSITION":
            return [H(self.X, t), H(self.Y, t)]
        if kind == "VELOCITY":
            hh = H(self.h, t)
            u, v = H(self.U, t), H(self.V, t)
            uu, vv = u * u, v * v
            return [hh * (uu - vv), hh * (u * v).twice()]
        if kind == "SPEED":
            hh, g = H(self.h, t), H(self.g, t)
            r = hh * g
            return [r if hh.sgn() >= 0 else -r]
        if kind == "SIGNED_RATE":
            return [H(self.h, t) * H(self.g, t)]
        if kind == "DIRECTION":
            return list(self._dir(t)[:2])
        if kind == "TANGENT":
            hh = H(self.h, t)
            s = hh.sgn()
            if s == 0:
                raise Refusal("NONREGULAR", self.L.event())
            dx, dy, _ = self._dir(t)
            return [dx, dy] if s > 0 else [-dx, -dy]
        if kind == "CURVATURE":
            hh = H(self.h, t)
            s = hh.sgn()
            if s == 0:
                raise Refusal("NONREGULAR", self.L.event())
            u, v, u1, v1 = H(self.U, t), H(self.V, t), H(self.U1, t), H(self.V1, t)
            g = u * u + v * v
            nk = (u * v1 - u1 * v).twice()
            r = hh * g
            den = (r if s > 0 else -r) * g
            return [nk, den, nk / den]
        if kind == "INTEGRAL":                      # representation-signed integral of h g from 0
            return [H(self.S, t)]
        if kind == "ACCUMULATED_LENGTH":            # accumulated length = sign(h) * S only when h has one constant sign
            s = self.h_sign()
            if s is None:
                raise Refusal("OUT_OF_DOMAIN", self.L.event())
            v = H(self.S, t)
            return [v if s >= 0 else -v]
        if kind == "BASE_ORIENTED":
            s = self.h_sign()
            if s is None:
                raise Refusal("OUT_OF_DOMAIN", self.L.event())
            v = H(self.S, t)
            v = v if s >= 0 else -v
            return [v if self.orient > 0 else -v]
        raise Invalid("MALFORMED", "request.%s" % kind)


def make(case, L, orient=1):
    p = case
    return Gen(qs(p["U"], L, "U"), qs(p["V"], L, "V"), qs(p["h"], L, "h"),
               Q.imp(*p["x"][0], L, "x0"), Q.imp(*p["y"][0], L, "y0"), L, orient)
