import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction as F
import eisenstein as Z
from eisenstein import E, EPH
import oracle


def cart_oracle(c, t0):
    """Independent route: Cartesian Q(sqrt3) generators A=Re(zeta), B=Im(zeta) through oracle.curve_facts."""
    A = [E.cart(z)[0] for z in c.zeta]
    B = [E.cart(z)[1] for z in c.zeta]
    h = [(F(x), F(0)) for x in c.h]
    w0 = c.W[0].cart()
    return oracle.curve_facts(A, B, h, w0[0], w0[1], (F(t0), F(0)))


def main():
    z = [E(1, 2), E(-1, 1), E(F(1, 2), 0)]
    c = EPH(z, w0=E(1, 1))
    # identity N(zeta^2)=N(zeta)^2 on a grid, and N == Euclidean |.|^2 of the Cartesian image
    n = 0
    for a in range(-4, 5):
        for b in range(-4, 5):
            u = E(a, b)
            assert (u * u).norm() == u.norm() ** 2
            (px, _), (_, qy) = u.cart()
            assert px * px + 3 * qy * qy == u.norm()  # sqrt3 part: (b/2*r3)^2 = 3 b^2/4
            n += 1
    print(f"IDENTITY: N(z^2)=N(z)^2 and N(z)=|cart(z)|^2 exact on {n} lattice points")
    for t0 in (F(0), F(1, 3), F(2, 5), F(-3, 7)):
        f = cart_oracle(c, t0)
        for name, fn in (("PH", lambda: Z.eph_eval(c, t0)), ("poly", lambda: Z.poly_eval(c, t0))):
            o = fn()
            (px, py) = o["P"].cart()
            assert (px, py) == f["P"], (name, "P")
            assert o["T"].cart() == f["T"]
            assert o["Q"] == f["Q"][0] and f["Q"][1] == 0
            assert o["speed2"] == f["speed2"][0] and f["speed2"][1] == 0
            assert o["dQ"] == f["dQ"][0] and f["dQ"][1] == 0
    print("CROSS-CHECK: Eisenstein-route outputs == Cartesian Q(sqrt3) oracle route at 4 points (P,T,speed2,Q,dQ)")
    t0 = F(2, 5)
    for name, fn in (("PH", Z.eph_eval), ("poly_horner", Z.poly_eval)):
        Z.C.clear()
        fn(c, t0)
        print("Eisenstein", name, dict(Z.C))
    print("degrees: zeta", len(c.zeta) - 1, "curve", len(c.W) - 1)
    print("speed polynomial is RATIONAL here (h*N(zeta) in Q[t]); Cartesian Euclidean PH over Q(sqrt3) needs surd arithmetic")


if __name__ == "__main__":
    main()
