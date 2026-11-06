"""Exact mathematical expression DAG and quadratic-polynomial normal form.

A mathematical model only: no machine state, instruction execution or refusals.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import product

# Polynomials: exponent tuple (xa, xb, ya, yb) -> rational coefficient.
ZERO = (0, 0, 0, 0)


def const(value):
    value = Fraction(value)
    return {ZERO: value} if value else {}


def variable(index):
    e = [0] * 4
    e[index] = 1
    return {tuple(e): Fraction(1)}


def add(p, q):
    out = dict(p)
    for e, v in q.items():
        out[e] = out.get(e, 0) + v
        if out[e] == 0:
            del out[e]
    return out


def scale(p, k):
    return {e: v*k for e, v in p.items() if v*k}


def mul(p, q):
    out = {}
    for a, av in p.items():
        for b, bv in q.items():
            key = tuple(x+y for x, y in zip(a, b))
            out[key] = out.get(key, 0) + av*bv
    return {e: v for e, v in out.items() if v}


def surd_mul(x, y):
    a, b = x
    c, d = y
    return add(mul(a, c), scale(mul(b, d), 3)), add(mul(a, d), mul(b, c))


@dataclass(frozen=True)
class Node:
    op: str
    args: tuple = ()


def normal(node, memo=None):
    """Canonical expanded polynomials. Memoization is keyed by immutable nodes."""
    if memo is None:
        memo = {}
    if node in memo:
        return memo[node]
    if node.op == 'x':
        value = variable(0), variable(1)
    elif node.op == 'y':
        value = variable(2), variable(3)
    elif node.op == 'const':
        value = const(node.args[0]), const(node.args[1])
    elif node.op == 'add':
        a, b = (normal(n, memo) for n in node.args)
        value = add(a[0], b[0]), add(a[1], b[1])
    elif node.op == 'mul':
        value = surd_mul(*(normal(n, memo) for n in node.args))
    elif node.op == 'conj':
        a, b = normal(node.args[0], memo)
        value = a, scale(b, -1)
    elif node.op == 'norm':
        a, b = normal(node.args[0], memo)
        value = add(mul(a, a), scale(mul(b, b), -3)), {}
    else:
        raise ValueError('unsupported node: '+node.op)
    memo[node] = value
    return value


def eval_graph(node, values):
    """Direct concrete evaluator, independent of polynomial normalization."""
    if node.op in ('x', 'y'):
        return tuple(Fraction(v) for v in values[node.op])
    if node.op == 'const':
        return tuple(Fraction(v) for v in node.args)
    if node.op == 'conj':
        a, b = eval_graph(node.args[0], values)
        return a, -b
    if node.op == 'norm':
        a, b = eval_graph(node.args[0], values)
        return a*a-3*b*b, Fraction(0)
    a, b = eval_graph(node.args[0], values)
    c, d = eval_graph(node.args[1], values)
    if node.op == 'mul':
        return a*c+3*b*d, a*d+b*c
    if node.op == 'add':
        return a+c, b+d
    raise ValueError('unsupported node: '+node.op)


def eval_poly(pair, values):
    terms = tuple(map(Fraction, values['x'] + values['y']))
    def evaluate(poly):
        return sum((v * product_term(e, terms) for e, v in poly.items()), Fraction(0))
    return tuple(evaluate(poly) for poly in pair)


def product_term(exponents, values):
    result = Fraction(1)
    for value, exponent in zip(values, exponents):
        result *= value ** exponent
    return result


def nodes(root):
    """Count unique graph nodes by immutable structural identity."""
    seen = set()
    def walk(n):
        if n in seen:
            return
        seen.add(n)
        for v in n.args:
            if isinstance(v, Node):
                walk(v)
    walk(root)
    return seen


def exact_box(root, bounds):
    """Enumerated integer-coefficient bounds, not a general symbolic bound proof."""
    result = []
    for vals in product(*(range(lo, hi+1) for lo, hi in bounds)):
        result.append(eval_graph(root, {'x': vals[:2], 'y': vals[2:]}))
    return tuple((min(v[i] for v in result), max(v[i] for v in result)) for i in (0, 1))


X, Y = Node('x'), Node('y')
U, V = Node('const', (2, 1)), Node('const', (2, -1))
CANCEL = Node('mul', (Node('mul', (X, U)), V))
CONJ_PRODUCT = Node('mul', (X, Node('conj', (X,))))
NORM_X = Node('norm', (X,))
FACTOR_ORIGINAL = Node('mul', (Node('mul', (X, Y)), Node('conj', (Y,))))
FACTOR = Node('mul', (X, Node('norm', (Y,))))
