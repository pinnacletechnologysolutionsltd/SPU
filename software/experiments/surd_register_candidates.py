"""Fixed-scale and shared-denominator storage models for S0 accounting."""
from dataclasses import dataclass
from math import gcd, lcm
from . import surd_register_exact as ex


@dataclass(frozen=True)
class FixedScale:
    scale: int

    def load(self, value):
        a,b,d=value.a,value.b,value.d
        if d<=0 or self.scale%d: return {'status':'INVALID_INPUT','value':None,'reason':'LOAD_NOT_DIVISIBLE'}
        return {'status':'OK','value':(a*(self.scale//d),b*(self.scale//d)),
                'counts':{'conversions':1,'exact_quotients':2,'logical_bits':None}}

    def apply(self, op, x, y=None):
        s=self.scale; counts={'integer_products':0,'exact_quotients':0,'divisibility_checks':0}
        if op in ('ADD','SUB'):
            sign=1 if op=='ADD' else -1; out=(x[0]+sign*y[0],x[1]+sign*y[1])
        elif op=='MUL':
            terms=(x[0]*y[0],3*x[1]*y[1],x[0]*y[1],x[1]*y[0]); counts['integer_products']=4
            n=(terms[0]+terms[1],terms[2]+terms[3]); counts['constant_operations']=1
            counts['divisibility_checks']=2
            if any(v%s for v in n): return {'status':'DESTINATION_OVERFLOW','value':None,'reason':'FIXED_SCALE_NOT_DIVISIBLE','counts':counts}
            out=(n[0]//s,n[1]//s); counts['exact_quotients']=2
        elif op=='NEG': out=(-x[0],-x[1])
        elif op=='CONJ': out=(x[0],-x[1])
        elif op=='NORM':
            r=ex.normalize(ex.R(x[0],x[1],s)); load=self.load(r)
            if load['status']!='OK': return {'status':'DESTINATION_OVERFLOW','value':None,'reason':'NORMALIZED_VALUE_OFF_SCALE'}
            out=load['value']; counts['gcd_calls']=2; counts['exact_quotients']=3
        else: raise ValueError(op)
        return {'status':'OK','value':out,'denominator':s,'counts':counts}


@dataclass
class SharedBlock:
    values: tuple
    scale: int
    counts: dict
    lane_width: int = 64

    @classmethod
    def load(cls, values):
        scale=1
        for r in values:
            if r.d<=0: raise ValueError('invalid denominator')
            scale=lcm(scale,r.d)
        aligned=tuple((r.a*(scale//r.d),r.b*(scale//r.d)) for r in values)
        return cls(aligned,scale,{'scale_alignment_multiplications':2*sum(r.d!=scale for r in values),
                                  'block_scale_updates':1,'fallbacks':int(scale>=(1<<64))})

    @property
    def logical_bits(self): return 2*len(self.values)*self.lane_width+self.lane_width

    @property
    def resident(self):
        lim=1<<(self.lane_width-1)
        return (0<self.scale<(1<<self.lane_width) and
                all(-lim<=a<lim and -lim<=b<lim for a,b in self.values))

    def apply_pairs(self, op, pairs):
        raw=[]
        for i,j in pairs:
            x=ex.R(*self.values[i],self.scale); y=ex.R(*self.values[j],self.scale)
            r,_=ex.raw(op,x,y)
            if isinstance(r,bool): raise ValueError('Boolean cannot enter shared block')
            raw.append(r)
        scale=1
        for r in raw: scale=lcm(scale,r.d)
        values=tuple((r.a*(scale//r.d),r.b*(scale//r.d)) for r in raw)
        self.counts['scale_alignment_multiplications']+=2*sum(r.d!=scale for r in raw)
        self.counts['block_scale_updates']+=int(scale!=self.scale); self.values=values; self.scale=scale
        self.counts['fallbacks']+=int(not self.resident)
        return self

    def materialize(self): return tuple(ex.normalize(ex.R(a,b,self.scale)) for a,b in self.values)
