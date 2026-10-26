"""Oracle O2: an independent route to the same observables. No power-coefficient expansion of x, y, S: they are exact
5-point Boole quadrature of the hodograph evaluated pointwise from (U, V) (exact for degree <= 5). Stdlib only."""
from fractions import Fraction as F

W = (F(7), F(32), F(12), F(32), F(7))


def ev(c, t):
    r = F(0)
    for x in reversed(c):
        r = r * t + x
    return r


def quad(fun, t):
    """integral of fun over [0, t] by Boole's rule: exact for polynomial integrands of degree <= 5."""
    return t * sum(w * fun(t * F(k, 4)) for k, w in enumerate(W)) / 90


def parts(U, V, s):
    u, v = ev(U, s), ev(V, s)
    return u * u - v * v, 2 * u * v, u * u + v * v


def cell_a(U, V, t):
    U, V = [F(*p) for p in U], [F(*p) for p in V]
    s = parts(U, V, t)[2]
    u1 = [i * U[i] for i in range(1, len(U))] or [F(0)]
    v1 = [i * V[i] for i in range(1, len(V))] or [F(0)]
    nk = 2 * (ev(U, t) * ev(v1, t) - ev(u1, t) * ev(V, t))
    return [quad(lambda s_: parts(U, V, s_)[0], t), quad(lambda s_: parts(U, V, s_)[1], t), parts(U, V, t)[0],
            parts(U, V, t)[1], s * s, s, quad(lambda s_: parts(U, V, s_)[2], t), nk, s * s]


def cell_b(U, V, phi, t):
    U, V, phi = [F(*p) for p in U], [F(*p) for p in V], [F(*p) for p in phi]
    f = ev(phi, t)
    g = ev([i * phi[i] for i in range(1, len(phi))], t)
    a = lambda s_, k: parts(U, V, s_)[k]       # noqa: E731
    return [quad(lambda s_: a(s_, 0), f), quad(lambda s_: a(s_, 1), f), g * a(f, 0), g * a(f, 1), g * a(f, 2), g * a(f, 2),
            quad(lambda s_: a(s_, 2), f)]
