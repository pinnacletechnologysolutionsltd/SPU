"""Independent exact oracle: multiplication via distributive basis products."""
from itertools import product

def multiply(x, y):
    # Basis products 1*1=1, 1*r=r, r*1=r, r*r=3.
    out = [0, 0]
    for i in range(2):
        for j in range(2):
            out[(i+j) % 2] += x[i]*y[j]*(3 if i+j == 2 else 1)
    return tuple(out)

def calculate(name, values):
    a,b,c,d = values
    x = (a,b)
    y = (a,-b) if name in ('F2','F4') else (c,d)
    first = multiply(x,y)
    return (first, multiply(first, (y[0], -y[1]))) if name == 'F3' else (first,)

def inputs(name):
    for a,b,c,d in product(range(-2,3), repeat=4):
        if name in ('F2','F4') and (c,d) != (a,-b):
            continue
        yield a,b,c,d

def extrema(values):
    return tuple((min(x[i] for x in values), max(x[i] for x in values)) for i in range(2))
