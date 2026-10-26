"""Bounded W-bit register semantics, policies, failures and operation counts."""
from math import gcd
from . import surd_register_exact as ex

POLICIES = ('EAGER', 'FIT_RESCUE', 'BOUNDARY')


def _steps(a, b):
    n = 0
    while b: a, b, n = b, a % b, n+1
    return n


def _fits(r, w): return isinstance(r, ex.R) and ex.valid(r, w)


def _counts(op, x, y, trace, names):
    c = trace['counts']; c['operations'][op] = c['operations'].get(op, 0)+1
    def product(a, b):
        if a == 1 or b == 1: c['factor_one_shortcuts'] += 1
        else: c['integer_products'] += 1
        c['product_operand_widths'].append([ex.sw(a), ex.sw(b)])
    if op in ('ADD','SUB'):
        g=gcd(x.d,y.d); c['gcd_calls']+=1; c['gcd_steps']+=_steps(x.d,y.d)
        u,v=y.d//g,x.d//g; c['exact_quotients']+=2
        for a in (x.a,x.b): product(a,u)
        for a in (y.a,y.b): product(a,v)
        product(x.d,u); c['additions']+=2
        c['alignment_operations']+=int(x.d!=y.d)
    elif op=='MUL':
        for a,b in ((x.a,y.a),(x.b,y.b),(x.a,y.b),(x.b,y.a),(x.d,y.d)): product(a,b)
        c['constant_operations']+=1; c['additions']+=2
    elif op in ('NEG','CONJ'): c['additions']+=1
    elif op=='EQ':
        for a,b in ((x.a,y.d),(y.a,x.d),(x.b,y.d),(y.b,x.d)): product(a,b)
        c['additions']+=2
    elif op=='NORM':
        g=gcd(gcd(abs(x.a),abs(x.b)),x.d); c['gcd_calls']+=2
        c['gcd_steps']+=_steps(abs(x.a),abs(x.b))+_steps(g,x.d)
        c['exact_quotients']+=3
    for name,value in names.items(): trace['named_intermediates'][name]=ex.widths(ex.R(value,0,1))['a']


def new_trace():
    return {'counts':{'operations':{},'gcd_calls':0,'gcd_steps':0,'exact_quotients':0,
        'integer_products':0,'product_operand_widths':[],'additions':0,'constant_operations':0,
        'factor_one_shortcuts':0,'alignment_operations':0,'fallback_attempts':0,
        'reentry_count':0},'named_intermediates':{}}


def load(destination, value, w):
    if not _fits(value,w):
        return {'status':'INVALID_INPUT','operation':'LOAD','destination':destination}
    return {'status':'OK','operation':'LOAD','destination':value}


def execute(op, x, y=None, w=64, policy='EAGER', trace=None, limits=None):
    t=trace if trace is not None else new_trace()
    needs_y=op in ('ADD','SUB','MUL','EQ')
    if (policy not in POLICIES or not _fits(x,w) or
            (needs_y and (y is None or not _fits(y,w)))):
        return {'status':'INVALID_INPUT','operation':op,'result':None,'required_widths':{}}
    result, mids=ex.raw(op,x,y)
    if isinstance(result,bool): _counts(op,x,y,t,mids); return {'status':'OK','operation':op,'result':result,'required_widths':{}}
    _counts(op,x,y,t,mids)
    unsigned={'d','den_product','dd','gcd','u','v','quot_d'}
    req={k:(ex.uw(v) if k in unsigned else ex.sw(v)) for k,v in mids.items()}
    lim=ex.intermediate_limits(op,w)
    if limits: lim.update(limits)
    overflow=[]
    for name,bits in req.items():
        role=('den_product' if name in ('den_product','dd') else
              'accumulator' if name in ('a','b','acc_a','acc_b') else
              'neg' if name.startswith(('neg_','conj_')) else
              'cross_product' if name in ('a1d2','a2d1','b1d2','b2d1') else
              'magnitude' if name=='gcd' else
              'quotient' if name.startswith('quot_') else 'product')
        if bits>lim.get(role, 10000): overflow.append(name)
    # Full exact intermediates are checked before normalization or destination fit.
    final_req=ex.widths(result)
    if overflow:
        return {'status':'INTERMEDIATE_OVERFLOW','operation':op,'result':None,
                'required_widths':{'result':final_req,'intermediates':req,'overflowing':overflow}}
    candidate=result
    if op!='NORM' and result.a==0 and result.b==0:
        candidate=_normalize(result,t)
    elif op!='NORM' and policy=='EAGER': candidate=_normalize(result,t)
    if not _fits(candidate,w) and policy=='FIT_RESCUE' and op!='NORM': candidate=_normalize(result,t)
    if _fits(candidate,w): return {'status':'OK','operation':op,'result':candidate,'required_widths':{'result':final_req}}
    return {'status':'DESTINATION_OVERFLOW','operation':op,'result':None,
            'required_widths':{'result':ex.widths(candidate),'raw_result':final_req}}


def execute_with_fallback(op, x, y=None, w=64, policy='EAGER', trace=None, limits=None):
    narrow=execute(op,x,y,w,policy,trace,limits)
    if narrow['status']=='OK': return {'narrow':narrow,'fallback':None,'resident':True}
    if narrow['status']=='INVALID_INPUT': return {'narrow':narrow,'fallback':None,'resident':False}
    wide, mids=ex.raw(op,x,y)
    if isinstance(wide,ex.R):
        if op=='NORM' or policy=='EAGER' or (policy=='FIT_RESCUE' and not _fits(wide,w)):
            wide=_normalize(wide,trace if trace is not None else new_trace())
        resident=_fits(wide,w)
    else: resident=True
    if trace is not None:
        trace['counts']['fallback_attempts']+=1
        trace['counts']['reentry_count']+=int(resident)
    return {'narrow':narrow,'fallback':{'executed':True,'result':wide,
        'reentry_eligible':resident,'wide_value_resident':resident,'named_intermediates':mids},
        'resident':resident}


def _normalize(value, trace):
    g=gcd(gcd(abs(value.a),abs(value.b)),value.d)
    c=trace['counts']; c['gcd_calls']+=2
    c['gcd_steps']+=_steps(abs(value.a),abs(value.b))+_steps(g,value.d)
    c['exact_quotients']+=3
    return ex.R(0,0,1) if value.a==value.b==0 else ex.R(value.a//g,value.b//g,value.d//g)
