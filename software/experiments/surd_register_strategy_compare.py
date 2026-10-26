"""Isolated cross-cancel/adaptive variants over the accepted S0 workload."""
from fractions import Fraction
from types import SimpleNamespace
from software.experiments import surd_register_exact as ex
from software.experiments import surd_register_model as model
from software.experiments import surd_register_s0_runner as s0


def value(r):
    return Fraction(r.a, r.d), Fraction(r.b, r.d)


def oracle(op, x, y):
    a, b = value(x); c, d = value(y)
    if op == 'ADD': return a+c, b+d
    if op == 'SUB': return a-c, b-d
    if op == 'MUL': return a*c+3*b*d, a*d+b*c
    raise ValueError(op)


def counted_gcd(*values):
    value=abs(values[0]); steps=0
    for other in values[1:]:
        other=abs(other)
        while other: value,other=other,value%other; steps+=1
    return value,steps


def run_variant(data, variant):
    original_raw, original_execute, original_s0_model = ex.raw, model.execute, s0.model
    cost = {'cross_cancel_gcd_calls':0,'cross_cancel_gcd_steps':0,
            'cross_cancel_exact_divisions':0,'cross_cancel_applied':0,
            'adaptive_checks':0,'adaptive_normalizations':0}
    statuses={}

    def raw(op,x,y=None):
        if op!='MUL' or variant not in ('cross_cancel','combined'):
            return original_raw(op,x,y)
        cost['cross_cancel_gcd_calls']+=2
        cx,st1=counted_gcd(x.d,abs(y.a),abs(y.b)); cy,st2=counted_gcd(y.d,abs(x.a),abs(x.b))
        cost['cross_cancel_gcd_steps']+=st1+st2
        if cx>1 or cy>1: cost['cross_cancel_applied']+=1
        if cx>1 or cy>1:
            x=ex.R(x.a//cy,x.b//cy,x.d//cx)
            y=ex.R(y.a//cx,y.b//cx,y.d//cy)
            cost['cross_cancel_exact_divisions']+=3*int(cx>1)+3*int(cy>1)
        return original_raw(op,x,y)

    def execute(op,x,y=None,w=64,policy='EAGER',trace=None,limits=None):
        out=original_execute(op,x,y,w,policy,trace,limits)
        if out['status']=='INVALID_INPUT':
            raise ValueError(f'invalid narrow input rejected before fallback: {op} W={w}')
        bucket=statuses.setdefault(op,{})
        bucket[out['status']]=bucket.get(out['status'],0)+1
        if variant not in ('adaptive','combined') or policy!='FIT_RESCUE' or out['status']!='OK' or op=='NORM':
            return out
        widths=out['required_widths'].get('result',{})
        cost['adaptive_checks']+=1
        if (widths and max(widths.values())>=w-1 and max(widths.values())<=w and
                (out['result'].a!=0 or out['result'].b!=0)):
            out=dict(out); out['result']=model._normalize(out['result'],trace)
            cost['adaptive_normalizations']+=1
        return out

    try:
        ex.raw=raw; model.execute=execute
        # Filter S0's policy loop without narrowing model.POLICIES: its
        # boundary NORM calls still require BOUNDARY to remain valid.
        s0.model=SimpleNamespace(POLICIES=('FIT_RESCUE',))
        chains,checks=s0.retained(data)
        return {'chains':chains,'correctness':checks,'technique_cost':cost,
                'narrow_execution_statuses':statuses}
    finally:
        ex.raw=original_raw; model.execute=original_execute; s0.model=original_s0_model


def synthetic(variant):
    cases=((ex.R(7,5,12),ex.R(9,-3,18)),
           (ex.R(12,6,30),ex.R(-15,9,45)),
           (ex.R(1,1,3),ex.R(-1,1,3)),
           (ex.R(0,0,17),ex.R(5,-2,7)))
    rows=[]; original_raw,original_execute=ex.raw,model.execute
    cost={'cross_cancel_gcd_calls':0,'cross_cancel_gcd_steps':0,
          'cross_cancel_exact_divisions':0,'cross_cancel_applied':0,
          'adaptive_checks':0,'adaptive_normalizations':0}
    def raw(op,x,y=None):
        if op!='MUL' or variant not in ('cross_cancel','combined'): return original_raw(op,x,y)
        cost['cross_cancel_gcd_calls']+=2
        cx,st1=counted_gcd(x.d,abs(y.a),abs(y.b)); cy,st2=counted_gcd(y.d,abs(x.a),abs(x.b))
        cost['cross_cancel_gcd_steps']+=st1+st2
        cost['cross_cancel_applied']+=int(cx>1 or cy>1)
        if cx>1 or cy>1:
            x=ex.R(x.a//cy,x.b//cy,x.d//cx)
            y=ex.R(y.a//cx,y.b//cx,y.d//cy)
            cost['cross_cancel_exact_divisions']+=3*int(cx>1)+3*int(cy>1)
        return original_raw(op,x,y)
    def execute(op,x,y=None,w=64,policy='EAGER',trace=None,limits=None):
        out=original_execute(op,x,y,w,policy,trace,limits)
        widths=out.get('required_widths',{}).get('result',{})
        if variant in ('adaptive','combined') and policy=='FIT_RESCUE' and out['status']=='OK' and widths:
            cost['adaptive_checks']+=1
            r=out['result']
            if max(widths.values())>=w-1 and max(widths.values())<=w and (r.a or r.b):
                out=dict(out); out['result']=model._normalize(r,trace); cost['adaptive_normalizations']+=1
        return out
    try:
        ex.raw=raw; model.execute=execute
        for w in (16,32,64):
            for x,y in cases:
                for op in ('ADD','MUL'):
                    trace=model.new_trace(); out=execute(op,x,y,w,'FIT_RESCUE',trace)
                    exact=oracle(op,x,y)
                    exact_match=out['status']=='OK' and value(out['result'])==exact
                    rows.append({'width':w,'operation':op,'x':x.__dict__,'y':y.__dict__,
                                 'status':out['status'],'exact_match':exact_match,
                                 'required_widths':out.get('required_widths',{}),
                                 'trace':trace})
        return {'cases':rows,'correct':all(r['exact_match'] for r in rows),'technique_cost':cost}
    finally:
        ex.raw=original_raw; model.execute=original_execute


def boundary(variant):
    """Two-multiply boundary chains: one cancelable, one coprime control."""
    cost={'cross_cancel_gcd_calls':0,'cross_cancel_gcd_steps':0,
          'cross_cancel_exact_divisions':0,'cross_cancel_applied':0,
          'adaptive_checks':0,'adaptive_normalizations':0,
          'adaptive_gcd_calls':0,'adaptive_gcd_steps':0,'adaptive_exact_divisions':0,
          'narrow_attempts':0,'narrow_failures':0,'wide_fallbacks':0,
          'wide_reentries':0,'nonresident_wide_results':0,
          'wide_gcd_calls':0,'wide_gcd_steps':0,'wide_exact_divisions':0}
    rows=[]
    for w in (16,32,64):
        q=(1<<(w-3))-1
        for case,yr in (('cancelable',ex.R(q,0,3)),('coprime_control',ex.R(q+1,0,3))):
            start=ex.R(1,0,q); state=start; exact=value(start)
            for stage in (1,2):
                x,y=state,yr
                if variant in ('cross_cancel','combined'):
                    cost['cross_cancel_gcd_calls']+=2
                    cx,st1=counted_gcd(x.d,abs(y.a),abs(y.b))
                    cy,st2=counted_gcd(y.d,abs(x.a),abs(x.b))
                    cost['cross_cancel_gcd_steps']+=st1+st2
                    cost['cross_cancel_applied']+=int(cx>1 or cy>1)
                    if cx>1 or cy>1:
                        x=ex.R(x.a//cy,x.b//cy,x.d//cx)
                        y=ex.R(y.a//cx,y.b//cx,y.d//cy)
                        cost['cross_cancel_exact_divisions']+=3*int(cx>1)+3*int(cy>1)
                raw,mids=ex.raw('MUL',x,y)
                raw_widths=ex.widths(raw)
                a,b=exact; c,d=value(yr)
                next_exact=(a*c+3*b*d,a*d+b*c)
                math_match=value(raw)==next_exact
                candidate=raw
                if variant in ('adaptive','combined') and (raw.a or raw.b):
                    cost['adaptive_checks']+=1
                    if max(raw_widths.values())>=w-1:
                        g1,s1=counted_gcd(abs(raw.a),abs(raw.b))
                        g,s2=counted_gcd(g1,raw.d)
                        cost['adaptive_gcd_calls']+=2
                        cost['adaptive_gcd_steps']+=s1+s2
                        cost['adaptive_exact_divisions']+=3
                        candidate=ex.R(raw.a//g,raw.b//g,raw.d//g)
                        cost['adaptive_normalizations']+=1
                status='OK' if ex.valid(candidate,w) else 'DESTINATION_OVERFLOW'
                cost['narrow_attempts']+=1
                if status!='OK':
                    cost['narrow_failures']+=1; cost['wide_fallbacks']+=1
                    g1,s1=counted_gcd(abs(candidate.a),abs(candidate.b))
                    g,s2=counted_gcd(g1,candidate.d)
                    cost['wide_gcd_calls']+=2; cost['wide_gcd_steps']+=s1+s2
                    cost['wide_exact_divisions']+=3
                    wide=ex.normalize(candidate)
                    reentry=ex.valid(wide,w)
                    cost['wide_reentries']+=int(reentry)
                    cost['nonresident_wide_results']+=int(not reentry)
                    state=wide
                else: state=candidate
                exact=next_exact
                rows.append({'width':w,'case':case,'stage':stage,
                    'input_widths':{'left':ex.widths(x),'right':ex.widths(y)},
                    'raw_result_widths':raw_widths,'committed_widths':ex.widths(candidate),
                    'raw_intermediate_widths':{k:(ex.uw(v) if k in ('dd','denominator') else ex.sw(v)) for k,v in mids.items()},
                    'status':status,'exact_match':math_match and value(state)==exact})
                if status!='OK': break
    return {'operations':rows,'exact':all(x['exact_match'] for x in rows),'cost':cost}
