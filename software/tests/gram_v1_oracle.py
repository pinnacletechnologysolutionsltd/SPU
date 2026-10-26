"""Independent gram_v1 SPREAD oracle: plain (p, q) integer pairs over Q(sqrt3).

Shared by test_gram_v1_spread.py and test_gram_v1_spread_cpp.py; imports nothing from the VMs.
research/sim_cap1_spread/GRAM_V1_CONTRACT_FROZEN.md section 1.
"""


def smul(x, y):
    return (x[0] * y[0] + 3 * x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def sadd(x, y):
    return (x[0] + y[0], x[1] + y[1])


def bilinear(x, y):
    """B(x, y) = 4*sum(x_i y_i) - (sum x_i)(sum y_i); x, y: four (p, q) pairs."""
    dot, sx, sy = (0, 0), (0, 0), (0, 0)
    for a, b in zip(x, y):
        dot, sx, sy = sadd(dot, smul(a, b)), sadd(sx, a), sadd(sy, b)
    t = smul(sx, sy)
    return (4 * dot[0] - t[0], 4 * dot[1] - t[1])


def oracle(v, w):
    """((Np, Nq), (Dp, Dq)) unreduced, or None when B(v,v) or B(w,w) is zero."""
    bvv, bww, bvw = bilinear(v, v), bilinear(w, w), bilinear(v, w)
    if bvv == (0, 0) or bww == (0, 0):
        return None
    den = smul(bvv, bww)
    sq = smul(bvw, bvw)
    return (den[0] - sq[0], den[1] - sq[1]), den
