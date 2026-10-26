"""End-to-end host cost paths for ordinary, rescued, and fallback Surd chains."""
from fractions import Fraction
from math import gcd
from software.experiments import surd_register_exact as ex

STRATEGIES=('explicit_fit_rescue','cross_cancel_fit_rescue',
            'separate_normalization_rescue','combined')


def cases(width):
    q=(1<<(width-3))-1
    return {
      'ordinary':(ex.R(3,1,7),ex.R(2,-1,5)),
      'rescued':(ex.R(1,0,q),ex.R(q,0,3)),
      'unavoidable_fallback':(ex.R(1,0,q),ex.R(q+1,0,3))}


def val(r): return Fraction(r.a,r.d),Fraction(r.b,r.d)


def pair_mul(x,y):
    a,b=x; c,d=y
    return a*c+3*b*d,a*d+b*c


def gcd_work(*values):
    g=abs(values[0]); steps=0
    for other in values[1:]:
        other=abs(other)
        while other: g,other=other,g%other; steps+=1
    return g,steps


def cancel(x,y,stats):
    cx=gcd(x.d,abs(y.a),abs(y.b))
    cy=gcd(y.d,abs(x.a),abs(x.b))
    if stats is not None:
        _,sx=gcd_work(x.d,abs(y.a),abs(y.b))
        _,sy=gcd_work(y.d,abs(x.a),abs(x.b))
        stats['cross_cancel_gcd_calls']+=2; stats['cross_cancel_gcd_steps']+=sx+sy
    if cx>1 or cy>1:
        if stats is not None:
            stats['cross_cancel_applied']+=1
            stats['cross_cancel_exact_divisions']+=3*int(cx>1)+3*int(cy>1)
        x=ex.R(x.a//cy,x.b//cy,x.d//cx)
        y=ex.R(y.a//cx,y.b//cx,y.d//cy)
    return x,y


def normalize(r,stats=None,wide=False):
    if stats is not None:
        g1,s1=gcd_work(abs(r.a),abs(r.b)); g,s2=gcd_work(g1,r.d)
        prefix='wide_' if wide else 'normalizer_'
        stats[prefix+'gcd_calls']+=2; stats[prefix+'gcd_steps']+=s1+s2
        stats[prefix+'exact_divisions']+=3
    return ex.normalize(r)


def fresh_counts():
    return {k:0 for k in ('narrow_attempts','narrow_failures','intermediate_failures',
      'normalizer_calls','normalization_rescues','wide_fallbacks','wide_reentries',
      'nonresident_wide_results','cross_cancel_gcd_calls','cross_cancel_gcd_steps',
      'cross_cancel_exact_divisions','cross_cancel_applied','normalizer_gcd_calls',
      'normalizer_gcd_steps','normalizer_exact_divisions','wide_gcd_calls',
      'wide_gcd_steps','wide_exact_divisions','adaptive_checks',
      'peak_raw_result_bits','peak_raw_intermediate_bits')}


def execute_chain(x,y,width,strategy,stats=None,verify=False):
    # Invalid loads stop the candidate. They are never converted into fallbacks.
    if not ex.valid(x,width) or not ex.valid(y,width):
        raise ValueError(f'invalid register input at W={width}: {x!r}, {y!r}')
    state=x; exact=val(x) if verify else None
    for _ in range(2):
        if not ex.valid(state,width):
            raise ValueError(f'nonresident value used as a narrow input at W={width}')
        if stats is not None: stats['narrow_attempts']+=1
        left,right=state,y
        if strategy in ('cross_cancel_fit_rescue','combined'):
            left,right=cancel(left,right,stats)
        raw,mids=ex.raw('MUL',left,right)
        if verify:
            exact=pair_mul(exact,val(y))
            if val(raw)!=exact: raise AssertionError('candidate changed exact value')
        intermediate_overflow=any(
            (ex.uw(v) if key=='dd' else ex.sw(v))>ex.intermediate_limits('MUL',width).get(
                'den_product' if key=='dd' else 'product' if key in ('aa','bb','three_bb','ab','ba') else 'accumulator',10**9)
            for key,v in mids.items())
        raw_fits=ex.valid(raw,width)
        if stats is not None:
            stats['intermediate_failures']+=int(intermediate_overflow)
            stats['narrow_failures']+=int(intermediate_overflow or not raw_fits)
            stats['peak_raw_result_bits']=max(stats['peak_raw_result_bits'],*ex.widths(raw).values())
            for key,value in mids.items():
                bits=ex.uw(value) if key=='dd' else ex.sw(value)
                stats['peak_raw_intermediate_bits']=max(stats['peak_raw_intermediate_bits'],bits)
        candidate=raw
        do_normalize=False
        if strategy in ('explicit_fit_rescue','cross_cancel_fit_rescue'):
            do_normalize=intermediate_overflow or not raw_fits
        else:
            if stats is not None: stats['adaptive_checks']+=1
            near=max(ex.widths(raw).values())>=width-1
            do_normalize=intermediate_overflow or not raw_fits or near
        if do_normalize:
            if stats is not None: stats['normalizer_calls']+=1
            candidate=normalize(raw,stats)
            if stats is not None:
                stats['normalization_rescues']+=int(not raw_fits and ex.valid(candidate,width))
        if ex.valid(candidate,width):
            state=candidate
            continue
        # A failed normalization takes the exact software fallback from the
        # original source operands, then attempts canonical re-entry.
        if stats is not None: stats['wide_fallbacks']+=1
        wide_raw,_=ex.raw('MUL',state,y)
        wide=normalize(wide_raw,stats,wide=True)
        resident=ex.valid(wide,width)
        if stats is not None:
            stats['wide_reentries']+=int(resident)
            stats['nonresident_wide_results']+=int(not resident)
        state=wide
    return state


def measure_case(width,name,x,y,strategy,trials=5,repetitions=2000,warmups=100):
    import statistics,time
    expected=val(x)
    for _ in range(2): expected=pair_mul(expected,val(y))
    counts=fresh_counts()
    actual=execute_chain(x,y,width,strategy,counts,verify=True)
    if val(actual)!=expected: raise AssertionError('untimed exact check failed')
    for _ in range(warmups): execute_chain(x,y,width,strategy)
    samples=[]
    for _ in range(trials):
        begin=time.perf_counter_ns()
        for _ in range(repetitions): execute_chain(x,y,width,strategy)
        samples.append(time.perf_counter_ns()-begin)
    return {'case':name,'width':width,'strategy':strategy,'exact':True,
      'counts_per_chain':counts,'trial_ns':samples,
      'median_ns_per_chain':statistics.median(samples)/repetitions,
      'median_ns_per_multiply':statistics.median(samples)/(2*repetitions),
      'trials':trials,'repetitions_per_trial':repetitions,'warmup_chains':warmups,
      'timed_scope':'prepared R inputs; two exact MUL steps including width checks, normalization and fallback handling'}
