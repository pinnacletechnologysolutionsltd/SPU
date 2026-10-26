"""Atomic exact paired-rotation macro with source snapshots and alias rules."""
# The macro is software semantics only. Both outputs are formed from the same
# two snapshots; no destination is committed until both fit the selected lanes.
# Its denominator is the shared aligned scale doubled by the half-turn factor.
# BOUNDARY treats this macro result as a named boundary and canonicalizes both
# output triples together. FIT_RESCUE retries only a destination fit failure.
# A width failure in the formula intermediates is always reported first.
# Denominators remain positive, including when operands have unequal scales.
# Rejected calls return the original register mapping by value.
# A wide mathematical result can still be an architectural destination fault.
from math import gcd
from . import surd_register_exact as ex


def rotate_pair(registers, src_x, src_y, dst_x, dst_y, w, policy):
    before=dict(registers)
    if dst_x==dst_y or src_x not in before or src_y not in before:
        return {'status':'INVALID_INPUT','registers':before,'operation':'ROTATE_PAIR'}
    x,y=before[src_x],before[src_y]  # snapshot permits source/destination aliasing
    if not ex.valid(x,w) or not ex.valid(y,w):
        return {'status':'INVALID_INPUT','registers':before,'operation':'ROTATE_PAIR'}
    g=gcd(x.d,y.d); u=y.d//g; v=x.d//g; d=x.d*u
    rawx=ex.R(x.a*u-3*y.b*v,x.b*u-y.a*v,2*d)
    rawy=ex.R(3*x.b*u+y.a*v,x.a*u+y.b*v,2*d)
    mids={'x_a_left':x.a*u,'x_a_right':3*y.b*v,'x_b_left':x.b*u,
          'x_b_right':y.a*v,'y_b_left':3*x.b*u,'y_b_right':y.a*v,
          'y_a_left':x.a*u,'y_a_right':y.b*v,'denominator':2*d}
    widths={k:(ex.uw(v) if k=='denominator' else ex.sw(v)) for k,v in mids.items()}
    limits={'x_a':2*w+2,'x_b':2*w+2,'y_a':2*w+2,'y_b':2*w+2,
            'denominator':2*w+1,'product':2*w+1}
    checks=((rawx.a,'x_a'),(rawx.b,'x_b'),(rawy.a,'y_a'),(rawy.b,'y_b'),(rawx.d,'denominator'))
    required={k:ex.uw(v) if k=='denominator' else ex.sw(v) for k,v in
              (('x_a',rawx.a),('x_b',rawx.b),('y_a',rawy.a),('y_b',rawy.b),('denominator',rawx.d))}
    product_overflow=[k for k,v in mids.items() if k!='denominator' and ex.sw(v)>limits['product']]
    if product_overflow or any(required[k]>limits[k] for _,k in checks):
        return {'status':'INTERMEDIATE_OVERFLOW','registers':before,'operation':'ROTATE_PAIR',
                'required_widths':{'intermediates':widths,'results':required,'overflowing':product_overflow}}
    if policy not in ('EAGER','FIT_RESCUE','BOUNDARY'):
        return {'status':'INVALID_INPUT','registers':before,'operation':'ROTATE_PAIR'}
    candidates=(ex.normalize(rawx),ex.normalize(rawy)) if policy=='EAGER' else (rawx,rawy)
    if policy=='FIT_RESCUE':
        candidates=tuple(ex.normalize(r) if not ex.valid(r,w) else r for r in candidates)
    if not all(ex.valid(r,w) for r in candidates):
        return {'status':'DESTINATION_OVERFLOW','registers':before,'operation':'ROTATE_PAIR',
                'required_widths':{'x':ex.widths(candidates[0]),'y':ex.widths(candidates[1])}}
    if policy=='BOUNDARY': candidates=tuple(ex.normalize(r) for r in candidates)
    after=dict(before); after[dst_x],after[dst_y]=candidates
    return {'status':'OK','registers':after,'operation':'ROTATE_PAIR',
            'counts':{'gcd_calls':1,'scale_quotients':2,'alignment_multiplications':4,
                      'constant_multiplications':2,'additions':4,'boundary_normalizations':2}}
