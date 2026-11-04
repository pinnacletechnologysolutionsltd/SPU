"""Purpose-built interval and sparse-polynomial arithmetic for four variables."""
from itertools import product

ZERO = (0, 0, 0, 0)
COUNTS = {}

def count(key, n=1):
    COUNTS[key] = COUNTS.get(key, 0) + n

def addi(x, y):
    count('interval_add')
    return x[0] + y[0], x[1] + y[1]

def muli(x, y):
    count('interval_mul')
    p = [a*b for a in x for b in y]
    return min(p), max(p)

def negi(x):
    return -x[1], -x[0]

def imul(x, y):
    a, b = x
    c, d = y
    return addi(muli(a, c), muli((3, 3), muli(b, d))), addi(muli(a, d), muli(b, c))

def conji(x):
    return x[0], negi(x[1])

def const(n):
    return {ZERO: n} if n else {}

def var(i):
    e = [0]*4
    e[i] = 1
    return {tuple(e): 1}

def padd(p, q):
    out = dict(p)
    for k, v in q.items():
        count('poly_coefficient_add')
        out[k] = out.get(k, 0) + v
        if not out[k]:
            del out[k]
    return out

def pneg(p):
    return {k: -v for k, v in p.items()}

def pmul(p, q):
    out = {}
    for a, x in p.items():
        for b, y in q.items():
            count('poly_term_mul')
            count('poly_coefficient_add')
            k = tuple(i+j for i, j in zip(a, b))
            out[k] = out.get(k, 0) + x*y
    return {k:v for k,v in out.items() if v}

def smul(x, y):
    a,b=x; c,d=y
    return padd(pmul(a,c), pmul(const(3), pmul(b,d))), padd(pmul(a,d), pmul(b,c))

def sconj(x):
    return x[0], pneg(x[1])

def peval(p, values):
    return sum(coef * product_power(values, exponents) for exponents, coef in p.items())

def product_power(values, exponents):
    v = 1
    for x, n in zip(values, exponents):
        v *= x**n
    return v

def pbound(p, box):
    total = (0,0)
    for exponents, coefficient in p.items():
        term = (coefficient, coefficient)
        for (lo, hi), n in zip(box, exponents):
            if not n:
                continue
            if n % 2 == 0:
                power = (0 if lo <= 0 <= hi else min(lo**n, hi**n), max(lo**n, hi**n))
            else:
                power = (lo**n, hi**n)
            term = muli(term, power)
        total = addi(total, term)
    return total

def polynomials(name):
    a,b,c,d = map(var, range(4))
    x = a,b
    y = c,d
    if name == 'F2':
        y = sconj(x)
    if name == 'F4':
        y = sconj(x)
    z = smul(x,y)
    return smul(z, sconj(y)) if name == 'F3' else z

def intervals(name, box):
    a,b,c,d = box
    x = a,b
    y = (a, negi(b)) if name == 'F2' else (c,d)
    z = imul(x,y)
    return imul(z, conji(y)) if name == 'F3' else z

def norm_bounds(box):
    a,b,c,d = box
    # square range, with zero inside these domains
    sq = lambda q: (0 if q[0] <= 0 <= q[1] else min(q[0]**2,q[1]**2), max(q[0]**2,q[1]**2))
    n = addi(sq(c), negi(muli((3,3),sq(d))))
    return muli(a,n), muli(b,n)

def width(n):
    return (n if n >= 0 else ~n).bit_length()+1
