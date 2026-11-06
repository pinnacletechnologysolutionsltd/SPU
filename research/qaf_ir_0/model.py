"""Research IR: immutable origin, mathematical form, sampled bounds and constraints.

Annotations are supplied hypotheses, not validated target semantics or optimizer authority.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from research.qaf_expr_graph_0.model import Node, normal, eval_graph


def freeze_poly(poly):
    return tuple(sorted((key, Fraction(value)) for key,value in poly.items()))


def structural_dependencies(node):
    if node.op in ('x','y'): return frozenset([node.op])
    return frozenset().union(*(structural_dependencies(arg) for arg in node.args if isinstance(arg,Node)))


def mathematical_dependencies(form):
    dependencies=set()
    for poly in form:
        for exp,_ in poly:
            if exp[0] or exp[1]: dependencies.add('x')
            if exp[2] or exp[3]: dependencies.add('y')
    return frozenset(dependencies)


def width(n):
    n=int(n)
    return (n if n >= 0 else ~n).bit_length()+1


@dataclass(frozen=True)
class Constraint:
    observer: str       # mathematical, final, strict, or unknown
    arithmetic: str     # exact, toy-signed64, or unknown
    status: str         # unobserved, observable, or unknown
    events: str         # unobserved, observable, or unknown

    def __post_init__(self):
        for value,allowed in ((self.observer,('mathematical','final','strict','unknown')),
                              (self.arithmetic,('exact','toy-signed64','unknown')),
                              (self.status,('unobserved','observable','unknown')),
                              (self.events,('unobserved','observable','unknown'))):
            if value not in allowed: raise ValueError('unknown constraint value')


@dataclass(frozen=True)
class BoundEvidence:
    domain: tuple
    samples: int
    bounds: tuple
    max_signed_bits: tuple
    kind: str


@dataclass(frozen=True)
class Record:
    origin: Node
    canonical: tuple
    syntax_deps: frozenset
    value_deps: frozenset
    constraint: Constraint
    bounds: BoundEvidence | None


def build(node, constraint, domain=None):
    polys=normal(node)
    form=tuple(freeze_poly(p) for p in polys)
    evidence = None
    if domain is not None:
        data=sampled_bounds(node,domain)
        evidence=BoundEvidence(tuple(tuple(pair) for pair in data['domain']),data['samples'],
                               data['bounds'],data['max_signed_bits'],data['kind'])
    return Record(node, form, structural_dependencies(node),
                  mathematical_dependencies(form), constraint, evidence)


def sampled_bounds(node, domain):
    """Enumerate bounded integer box; report witnesses, not a symbolic proof."""
    if len(domain)!=4 or any(type(v) is not int for pair in domain for v in pair):
        raise ValueError('four integer ranges required')
    if any(lo > hi for lo,hi in domain): raise ValueError('invalid range')
    count=1
    for lo,hi in domain: count*=hi-lo+1
    if count>625: raise ValueError('fixture cap exceeded')
    results=[]
    for a,b,c,d in product(*(range(lo,hi+1) for lo,hi in domain)):
        out=eval_graph(node,{'x':(a,b),'y':(c,d)})
        if any(v.denominator != 1 for v in out):
            raise ValueError('integer-coefficient outputs required')
        results.append(tuple(int(v) for v in out))
    return {'domain':domain,'samples':count,
            'bounds':tuple((min(v[i] for v in results),max(v[i] for v in results)) for i in (0,1)),
            'max_signed_bits':tuple(max(width(v[i]) for v in results) for i in (0,1)),
            'kind':'enumerated exact extrema for independent integer box'}


def compare(left,right):
    """Report meaning and provenance, never grant a machine rewrite."""
    if left.constraint != right.constraint: return {'mathematical_equal':left.canonical==right.canonical,'rewrite':'UNKNOWN_CONSTRAINT_MISMATCH'}
    return {'mathematical_equal':left.canonical==right.canonical,
            'same_origin':left.origin==right.origin,
            'rewrite':'NOT_DECIDED'}
