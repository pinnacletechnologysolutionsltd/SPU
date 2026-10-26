"""Five literal Cell B Q programs, independent random-access requests."""
from w31_arithmetic import Q, Refusal
from w31_poly import Program


def evaluate(trace, arm, state, t, k):
    family = 'e' if arm == 'B-COMP' else 'h' if arm == 'C1' else 'k'
    def prog(step):
        return Program(trace,f'{arm}.Q.q{k:02d}.{family}{step}')
    def op(step, method, *args):
        return prog(step).op(method,*args)
    def value(step, name, at=t):
        p = prog(step)
        if arm == 'E-BEZ' and name != 'phi1':
            return p.decas(state[name],at)
        if arm == 'E-TS' and name != 'phi1':
            return p.tshift(state[name],at)[0]
        return p.horner(state[name],at)
    def ok(step,g):
        if op(step,'sign',g) < 0:
            raise Refusal(f'{arm}.Q.q{k:02d}.{family}{step}.1','NONMONOTONE')
    if family == 'e':
        f,g = value(1,'phi'),value(2,'phi1')
        ok(3,g)
        x,y = value(4,'X',f),value(5,'Y',f)
        q1,q2,q3 = value(6,'dx',f),value(7,'dy',f),value(8,'sg',f)
        dx,dy,s = op(9,'mul',g,q1),op(10,'mul',g,q2),op(11,'mul',g,q3)
        S = value(12,'SS',f)
    elif family == 'h':
        f,g = value(1,'phi'),value(2,'phi1')
        ok(3,g)
        ff = op(4,'mul',f,f)
        w1 = prog(5).sub(Q(1),ff)
        dx = op(6,'mul',g,w1)
        w2 = op(7,'mul',g,f)
        dy = op(8,'shift2',w2)
        w3 = op(9,'add',Q(1),ff)
        s = op(10,'mul',g,w3)
        x,y,S = value(11,'cx'),value(12,'cy'),value(13,'cSS')
    else:
        g = value(1,'phi1')
        ok(2,g)
        x,y,dx,dy,s,S = [value(i,name) for i,name in enumerate(('cx','cy','cdx','cdy','csg','cSS'),3)]
    return dict(x=x,y=y,dx=dx,dy=dy,s_signed=s,s_nonneg=s,S_inc=S,ok=True)
