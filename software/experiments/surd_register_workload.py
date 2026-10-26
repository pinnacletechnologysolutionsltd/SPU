"""Retained robotics adapter and independent Fraction component-pair oracle."""
from fractions import Fraction
from math import gcd
from . import surd_register_exact as ex
from . import surd_register_model as model


def from_q3(q):
    d=q.p.denominator*q.q.denominator//gcd(q.p.denominator,q.q.denominator)
    return ex.R(q.p.numerator*(d//q.p.denominator),q.q.numerator*(d//q.q.denominator),d)


def to_q3(r, ref): return ref.Q3(Fraction(r.a,r.d),Fraction(r.b,r.d))


def oracle_add(x,y,sign=1): return x[0]+sign*y[0],x[1]+sign*y[1]
def oracle_mul(x,y): return x[0]*y[0]+3*x[1]*y[1],x[0]*y[1]+x[1]*y[0]


def oracle_rotate(v,j):
    a,b,c,d=v; f,g,h=j
    return (a,oracle_add(oracle_add(oracle_mul(f,b),oracle_mul(h,c)),oracle_mul(g,d)),
            oracle_add(oracle_add(oracle_mul(g,b),oracle_mul(f,c)),oracle_mul(h,d)),
            oracle_add(oracle_add(oracle_mul(h,b),oracle_mul(g,c)),oracle_mul(f,d)))


def oracle_joint(r):
    f,g,h=r
    return (oracle_add(oracle_mul(f,f),oracle_mul(g,h),-1),
            oracle_add(oracle_mul(h,h),oracle_mul(f,g),-1),
            oracle_add(oracle_mul(g,g),oracle_mul(f,h),-1))


def oracle_chain(v,joints):
    forward=tuple((x.p,x.q) for x in v.components())
    js=tuple(tuple((x.p,x.q) for x in (j.f,j.g,j.h)) for j in joints)
    end=forward
    for j in js: end=oracle_rotate(end,j)
    back=end
    for j in reversed(js): back=oracle_rotate(back,oracle_joint(j))
    return end,back


def _step(op,x,y,w,policy,stats):
    out=model.execute(op,x,y,w,policy,stats['trace'])
    stats['operations']+=1
    if out['status']=='OK': return out['result']
    if out['status']=='INVALID_INPUT' and isinstance(x,ex.R) and (y is None or isinstance(y,ex.R)):
        structurally_valid=lambda r: (type(r.a) is int and type(r.b) is int and type(r.d) is int and r.d>0)
        if structurally_valid(x) and (y is None or structurally_valid(y)):
            stats['fallbacks']+=1
            stats['wide_continuations']+=1
            stats['trace']['counts']['fallback_attempts']+=1
            raw,_=ex.raw(op,x,y)
            if isinstance(raw,ex.R):
                if op=='NORM' or policy=='EAGER' or (policy=='FIT_RESCUE' and not ex.valid(raw,w)): raw=ex.normalize(raw)
                if ex.valid(raw,w):
                    stats['reentries']+=1; stats['trace']['counts']['reentry_count']+=1
                else: stats['nonresident_results']+=1
            return raw
    stats['status_counts'][out['status']]=stats['status_counts'].get(out['status'],0)+1
    if out['status']=='INVALID_INPUT': return None
    stats['fallbacks']+=1
    stats['trace']['counts']['fallback_attempts']+=1
    raw,_=ex.raw(op,x,y)
    if isinstance(raw,ex.R):
        if op=='NORM' or policy=='EAGER' or (policy=='FIT_RESCUE' and not ex.valid(raw,w)): raw=ex.normalize(raw)
        if ex.valid(raw,w):
            stats['reentries']+=1; stats['trace']['counts']['reentry_count']+=1
        else: stats['nonresident_results']+=1
    return raw


def _rotate(state,joint,w,policy,stats):
    a,b,c,d=state; f,g,h=joint
    def mul(x,y): return _step('MUL',x,y,w,policy,stats)
    def add(x,y): return _step('ADD',x,y,w,policy,stats)
    def sub(x,y): return _step('SUB',x,y,w,policy,stats)
    return (a,add(add(mul(f,b),mul(h,c)),mul(g,d)),
            add(add(mul(g,b),mul(f,c)),mul(h,d)),
            add(add(mul(h,b),mul(g,c)),mul(f,d)))


def _norm_state(state,w,stats):
    out=[]
    for r in state:
        v=model.execute('NORM',r,w=w,policy='BOUNDARY',trace=stats['trace'])
        stats['operations']+=1
        if v['status']=='OK': out.append(v['result'])
        else:
            stats['fallbacks']+=1
            stats['trace']['counts']['fallback_attempts']+=1
            normalized=ex.normalize(r)
            if ex.valid(normalized,w):
                stats['reentries']+=1; stats['trace']['counts']['reentry_count']+=1
            else: stats['nonresident_results']+=1
            out.append(normalized)
    return tuple(out)


def bounded_chain(vector,joints,w,policy):
    stats={'operations':0,'fallbacks':0,'reentries':0,'nonresident_results':0,
           'wide_continuations':0,'status_counts':{},'boundary_norms':0,
           'trace':model.new_trace()}
    state=tuple(from_q3(x) for x in vector.components())
    js=tuple(tuple(from_q3(x) for x in (j.f,j.g,j.h)) for j in joints)
    inv=[]
    for f,g,h in js:
        inv.append((_step('SUB',_step('MUL',f,f,w,policy,stats),_step('MUL',g,h,w,policy,stats),w,policy,stats),
                    _step('SUB',_step('MUL',h,h,w,policy,stats),_step('MUL',f,g,w,policy,stats),w,policy,stats),
                    _step('SUB',_step('MUL',g,g,w,policy,stats),_step('MUL',f,h,w,policy,stats),w,policy,stats)))
    forward=state
    for j in js:
        forward=_rotate(forward,j,w,policy,stats)
        forward=_norm_state(forward,w,stats); stats['boundary_norms']+=3
    recovered=forward
    for j in reversed(inv):
        recovered=_rotate(recovered,j,w,policy,stats)
        recovered=_norm_state(recovered,w,stats); stats['boundary_norms']+=3
    return (forward,recovered),stats


def oracle_quadray(pair,ref): return ref.QuadrayQ(*(ref.Q3(p,q) for p,q in pair))


def bounded_quadray(state,ref): return ref.QuadrayQ(*(to_q3(r,ref) for r in state))
