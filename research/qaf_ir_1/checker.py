"""Small independent checker for selected QAF-IR-0 claims.

No imports from the producer/normalizer. Input objects are ordinary Python,
not authenticated certificates or an untrusted-data security boundary.
"""
from fractions import Fraction
from itertools import product

ZERO=(0,0,0,0)


def _add(a,b):
    d=dict(a)
    for k,v in b.items():
        d[k]=d.get(k,Fraction(0))+v
        if not d[k]: del d[k]
    return d


def _scale(p,k):
    return {e:v*k for e,v in p.items() if v*k}


def _mul(a,b):
    out={}
    for i,x in a.items():
        for j,y in b.items():
            k=tuple(n+m for n,m in zip(i,j))
            out[k]=out.get(k,Fraction(0))+x*y
    return {k:v for k,v in out.items() if v}


def _variable(i):
    exponents=[0]*4
    exponents[i]=1
    return {tuple(exponents):Fraction(1)}


def analyze(node, depth=0):
    """Recompute formal polynomial and syntactic deps by separate traversal."""
    if depth > 32: raise ValueError('depth cap')
    op,args=node.op,node.args
    if op in ('x','y') and args == ():
        i=0 if op=='x' else 2
        return (_variable(i),_variable(i+1)),frozenset((op,))
    if op=='const' and len(args)==2:
        def c(x):
            if type(x) not in (int,Fraction): raise ValueError('non-rational constant')
            x=Fraction(x); return {ZERO:x} if x else {}
        return (c(args[0]),c(args[1])),frozenset()
    if op in ('conj','norm') and len(args)==1:
        (a,b),deps=analyze(args[0],depth+1)
        if op=='conj': return (a,_scale(b,-1)),deps
        return (_add(_mul(a,a),_scale(_mul(b,b),-3)),{}),deps
    if op in ('add','mul') and len(args)==2:
        (a,b),da=analyze(args[0],depth+1)
        (c,d),db=analyze(args[1],depth+1)
        if op=='add': return (_add(a,c),_add(b,d)),da|db
        return (_add(_mul(a,c),_scale(_mul(b,d),3)),_add(_mul(a,d),_mul(b,c))),da|db
    raise ValueError('unsupported expression')


def canonical(form):
    return tuple(tuple(sorted(p.items())) for p in form)


def direct(node, inputs, depth=0):
    """Numerical evaluator independent of producer and this file's polynomial path."""
    if depth > 32: raise ValueError('depth cap')
    op,args=node.op,node.args
    if op in ('x','y') and not args: return inputs[op]
    if op=='const' and len(args)==2: return tuple(Fraction(v) for v in args)
    if op in ('conj','norm') and len(args)==1:
        a,b=direct(args[0],inputs,depth+1)
        return (a,-b) if op=='conj' else (a*a-3*b*b,Fraction(0))
    if op in ('add','mul') and len(args)==2:
        a,b=direct(args[0],inputs,depth+1); c,d=direct(args[1],inputs,depth+1)
        return (a+c,b+d) if op=='add' else (a*c+3*b*d,a*d+b*c)
    raise ValueError('unsupported expression')


def check_bounds(node, evidence):
    """Exhaust finite independent integer rectangle, compare exact extrema and widths."""
    domain=evidence.domain
    if len(domain)!=4 or any(len(p)!=2 or any(type(x) is not int for x in p) or p[0]>p[1] for p in domain): raise ValueError('invalid domain')
    n=1
    for lo,hi in domain: n*=hi-lo+1
    if n>625: raise ValueError('domain cap')
    points=[]
    for a,b,c,d in product(*(range(lo,hi+1) for lo,hi in domain)):
        x=direct(node,{'x':(Fraction(a),Fraction(b)),'y':(Fraction(c),Fraction(d))})
        if any(v.denominator!=1 for v in x): raise ValueError('fractional output unsupported')
        points.append(tuple(int(v) for v in x))
    extrema=tuple((min(p[i] for p in points),max(p[i] for p in points)) for i in (0,1))
    def width(v): return (v if v>=0 else -v-1).bit_length()+1
    widths=tuple(max(width(p[i]) for p in points) for i in (0,1))
    return (evidence.samples==n and evidence.bounds==extrema and evidence.max_signed_bits==widths and evidence.kind=='enumerated exact extrema for independent integer box')


def check(record, expected_origin=None, expected_domain=None):
    """Return checked mathematical claims separately from unverified effects."""
    try:
        form,deps=analyze(record.origin)
        value_deps=frozenset(name for name,indices in [('x',(0,1)),('y',(2,3))]
                             if any(e[indices[0]] or e[indices[1]] for p in form for e in p))
        if expected_origin is None:
            return {'claims':'UNKNOWN_ORIGIN_SCOPE','execution_assumptions':'UNVERIFIED','rewrite_eligibility':'UNKNOWN'}
        if record.origin != expected_origin:
            return {'claims':'FAIL_ORIGIN_MISMATCH','execution_assumptions':'UNVERIFIED','rewrite_eligibility':'UNKNOWN'}
        if record.bounds is None:
            bounds='NOT_SUPPLIED'
        elif expected_domain is None:
            bounds='UNKNOWN_DOMAIN_SCOPE'
        elif record.bounds.domain != expected_domain:
            bounds='FAIL_DOMAIN_MISMATCH'
        else:
            bounds='PASS' if check_bounds(record.origin,record.bounds) else 'FAIL'
        return {'normal_form':'PASS' if record.canonical==canonical(form) else 'FAIL',
                'structural_dependencies':'PASS' if record.syntax_deps==deps else 'FAIL',
                'mathematical_dependencies':'PASS' if record.value_deps==value_deps else 'FAIL',
                'bounds':bounds,
                'execution_assumptions':'UNVERIFIED', 'rewrite_eligibility':'UNKNOWN'}
    except (ValueError,TypeError,AttributeError,RecursionError):
        return {'claims':'UNKNOWN_UNSUPPORTED','execution_assumptions':'UNVERIFIED','rewrite_eligibility':'UNKNOWN'}


def check_equal(left,right,expected_left=None,expected_right=None):
    """Ignore supplied forms, compare recomputed formal polynomial pairs."""
    try:
        if expected_left is None or expected_right is None: return 'UNKNOWN_ORIGIN_SCOPE'
        if left.origin != expected_left or right.origin != expected_right: return 'FAIL_ORIGIN_MISMATCH'
        a,_=analyze(left.origin); b,_=analyze(right.origin)
        return 'PASS_EQUAL_FORM' if canonical(a)==canonical(b) else 'FAIL_NOT_EQUAL_FORM'
    except (ValueError,TypeError,AttributeError,RecursionError):
        return 'UNKNOWN_UNSUPPORTED'
