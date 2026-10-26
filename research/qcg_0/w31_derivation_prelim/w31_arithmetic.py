"""Independent QCG-0 W31 arithmetic foundation.

Written solely against Revision 3.2.2 sections 2-3 and 5 in the handoff.
Not the candidate; not a complete stage-table interpreter.
No use of research/qcg_0/p0/ or any candidate results.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import gcd
from fractions import Fraction

RAW_MAX = 63
RED_MAX = 31

def bits(x: int) -> int:
    return max(1, abs(x).bit_length())

@dataclass(frozen=True)
class Q:
    n: int
    d: int = 1
    def __post_init__(self):
        if self.d == 0:
            raise ZeroDivisionError('invalid rational import')
        g = gcd(self.n, self.d)
        n, d = self.n // g, self.d // g
        if d < 0:
            n, d = -n, -d
        object.__setattr__(self, 'n', n)
        object.__setattr__(self, 'd', d)
    def value(self):
        return Fraction(self.n, self.d)

class Refusal(Exception):
    def __init__(self, event: str, code='ARITH_LIMIT'):
        super().__init__(f'{code}: {event}')
        self.event, self.code = event, code

class Invalid(Exception):
    def __init__(self, event: str, code='DIV_ZERO'):
        super().__init__(f'{code}: {event}')
        self.event, self.code = event, code

class Trace:
    """§3 ordered sub-checks; context/step supplied by a future arm interpreter."""
    def __init__(self, profile='W31'):
        if profile != 'W31':
            raise ValueError('this independent foundation only supports W31')
        self.events = []
        self.counts = dict(M=0, A=0, S=0, D=0, K=0, G_calls=0, G_bits=0, W_bits=0, W_peak_raw=0, W_peak_red=0, M2=0)
    def _raw(self, value, name):
        self.counts['W_peak_raw'] = max(self.counts['W_peak_raw'], bits(value))
        if bits(value) > RAW_MAX:
            raise Refusal(name)
    def _reduced(self, q, name):
        self.counts['W_peak_red'] = max(self.counts['W_peak_red'], bits(q.n), bits(q.d))
        if bits(q.n) > RED_MAX: raise Refusal(name+'.e1')
        if bits(q.d) > RED_MAX: raise Refusal(name+'.e2')
    def import_q(self, q, event):
        self.counts['W_peak_red'] = max(self.counts['W_peak_red'], bits(q.n), bits(q.d))
        if bits(q.n) > RED_MAX or bits(q.d) > RED_MAX:
            raise Refusal(event)
        return q
    def _finish(self, n, d, event, category):
        q=Q(n,d)
        self.counts['G_calls'] += 1
        self.counts['G_bits'] += max(bits(n), bits(d))
        self._reduced(q,event)
        self.events.append((event, category, q.n, q.d))
        return q
    def mul(self, x, y, event):
        self.counts['M'] += 1
        self.counts['W_bits'] += bits(x.n)*bits(y.n)+bits(x.d)*bits(y.d)
        self.counts['M2'] += int(abs(y.n) & (abs(y.n)-1) == 0 and y.n != 0 and y.d & (y.d-1) == 0)
        n=x.n*y.n; self._raw(n,event+'.r1')
        d=x.d*y.d; self._raw(d,event+'.r2')
        return self._finish(n,d,event,'M')
    def add(self,x,y,event,subtract=False):
        self.counts['A'] += 1
        self.counts['W_bits'] += bits(x.n)*bits(y.d)+bits(y.n)*bits(x.d)+bits(x.d)*bits(y.d)
        r1=x.n*y.d; self._raw(r1,event+'.r1')
        r2=y.n*x.d; self._raw(r2,event+'.r2')
        n=r1-r2 if subtract else r1+r2; self._raw(n,event+'.r3')
        d=x.d*y.d; self._raw(d,event+'.r4')
        return self._finish(n,d,event,'A')
    def div(self,x,y,event):
        self.counts['D'] += 1
        if y.n == 0: raise Invalid(event)
        self.counts['W_bits'] += bits(x.n)*bits(y.d)+bits(x.d)*bits(y.n)
        n=x.n*y.d; self._raw(n,event+'.r1')
        d=x.d*y.n; self._raw(d,event+'.r2')
        return self._finish(n,d,event,'D')
    def shift2(self,x,event,divide=False):
        self.counts['S'] += 1
        if divide:
            n,d=(x.n//2,x.d) if x.n%2==0 else (x.n,x.d*2)
        else:
            n,d=(x.n,x.d//2) if x.d%2==0 else (x.n*2,x.d)
        q=Q(n,d)
        self._reduced(q,event)
        self.events.append((event,'S',q.n,q.d))
        return q
    def compare(self,x,y,event):
        self.counts['K'] += 1
        self.counts['W_bits'] += bits(x.n)*bits(y.d)+bits(y.n)*bits(x.d)
        l=x.n*y.d; self._raw(l,event+'.r1')
        r=y.n*x.d; self._raw(r,event+'.r2')
        self.events.append((event,'K',None,None))
        return (l>r)-(l<r)
    def sign(self,x,event):
        self.counts['K'] += 1
        self.events.append((event,'K',None,None))
        return (x.n>0)-(x.n<0)

if __name__ == '__main__':
    # Unit checks ONLY; not a W31 stage derivation and not a campaign attempt.
    t=Trace()
    a=Q(2**30,3); b=Q(5,2**10)
    assert t.mul(a,b,'unit.M').value()==a.value()*b.value()
    assert t.div(Q(15,7),Q(3,5),'unit.D').value()==Fraction(25,7)
    assert t.add(Q(2,7),Q(3,5),'unit.A').value()==Fraction(31,35)
    assert t.add(Q(2,7),Q(3,5),'unit.Sub',True).value()==Fraction(-11,35)
    assert t.shift2(Q(3,2),'unit.S').value()==3
    assert t.shift2(Q(3,2),'unit.Shalf',True).value()==Fraction(3,4)
    assert t.sign(Q(-2),'unit.K')==-1
    assert t.compare(a,b,'unit.Cmp')==1
    try:
        t.mul(Q(2**30), Q(2), 'unit.Refusal')
        raise AssertionError('missing refusal')
    except Refusal as ex:
        assert ex.event=='unit.Refusal.e1'
    try:
        t.div(Q(1),Q(0),'unit.Zero')
        raise AssertionError('missing invalid')
    except Invalid as ex:
        assert ex.code=='DIV_ZERO'
    print('Independent arithmetic foundation: 10 unit checks PASS; no stage derivation')
