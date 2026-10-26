"""Exact fixed-scale and shared-scale models for a Surd robotics chain."""
import math
from fractions import Fraction
from lib import rational_robotics as ref

class FixedScaleUnrepresentable(ArithmeticError):
    pass

def signed_width(value):
    return (value.bit_length() if value >= 0 else (~value).bit_length()) + 1

def observe(stats, role, *values):
    stats[role] = max(stats.get(role, 1), *(signed_width(v) for v in values))
    if role in ('product', 'accumulator'):
        counts = stats.setdefault('wide_fallback_events', {16: 0, 32: 0, 64: 0})
        for bits in counts:
            counts[bits] += int(any(signed_width(v) > bits for v in values))

def encode_pair(value, scale):
    p, q = value.p * scale, value.q * scale
    if p.denominator != 1 or q.denominator != 1:
        raise FixedScaleUnrepresentable('input not representable at fixed scale')
    return int(p), int(q)

def pair_mul(x, y):
    a, b = x
    c, e = y
    return a*c + 3*b*e, a*e + b*c

def pair_add(x, y):
    return x[0]+y[0], x[1]+y[1]

def fixed_mac3(x, f, y, g, z, h, scale, stats):
    products = (pair_mul(x, f), pair_mul(y, g), pair_mul(z, h))
    raw = products[0][0]+products[1][0]+products[2][0], products[0][1]+products[1][1]+products[2][1]
    observe(stats, 'product', *(v for p in products for v in p))
    observe(stats, 'accumulator', *raw)
    if raw[0] % scale or raw[1] % scale:
        raise FixedScaleUnrepresentable('MAC result needs a different denominator')
    return raw[0]//scale, raw[1]//scale

def fixed_msub(x, y, u, v, scale, stats):
    p, q = pair_mul(x, y), pair_mul(u, v)
    raw = p[0]-q[0], p[1]-q[1]
    observe(stats, 'product', *p, *q)
    observe(stats, 'accumulator', *raw)
    if raw[0] % scale or raw[1] % scale:
        raise FixedScaleUnrepresentable('MSUB result needs a different denominator')
    return raw[0]//scale, raw[1]//scale

def fixed_inverse(joint, scale, stats):
    f, g, h = joint
    return (fixed_msub(f, f, g, h, scale, stats),
            fixed_msub(h, h, f, g, scale, stats),
            fixed_msub(g, g, f, h, scale, stats))

def fixed_rotate(state, joint, scale, stats):
    a, b, c, d = state
    f, g, h = joint
    return (a,
            fixed_mac3(b, f, c, h, d, g, scale, stats),
            fixed_mac3(b, g, c, f, d, h, scale, stats),
            fixed_mac3(b, h, c, g, d, f, scale, stats))

def shared_inverse(joint, stats):
    f, g, h = joint
    raw = (pair_mul(f, f), pair_mul(g, h), pair_mul(h, h),
           pair_mul(f, g), pair_mul(g, g), pair_mul(f, h))
    observe(stats, 'product', *(v for p in raw for v in p))
    out = (raw[0][0]-raw[1][0], raw[0][1]-raw[1][1],
           raw[2][0]-raw[3][0], raw[2][1]-raw[3][1],
           raw[4][0]-raw[5][0], raw[4][1]-raw[5][1])
    observe(stats, 'accumulator', *out)
    return ((out[0], out[1]), (out[2], out[3]), (out[4], out[5]))

def shared_rotate(state, joint, scale, stats):
    a, b, c, d = state
    f, g, h = joint
    terms = ((b, f), (c, h), (d, g), (b, g), (c, f), (d, h),
             (b, h), (c, g), (d, f))
    products = tuple(pair_mul(x, y) for x, y in terms)
    observe(stats, 'product', *(v for p in products for v in p))
    outputs = (tuple(x*scale for x in a),
        tuple(sum(products[i][k] for i in (0,1,2)) for k in (0,1)),
        tuple(sum(products[i][k] for i in (3,4,5)) for k in (0,1)),
        tuple(sum(products[i][k] for i in (6,7,8)) for k in (0,1)))
    observe(stats, 'accumulator', *(v for p in outputs for v in p))
    return outputs

def materialize_pairs(values, scale):
    return ref.QuadrayQ(*(ref.Q3(Fraction(a, scale), Fraction(b, scale)) for a,b in values))

def width_trace(values, denominator, stats, phase, index):
    flat = [v for pair in values for v in pair] + [denominator]
    observe(stats, 'state', *flat)
    stats.setdefault('steps', []).append({'phase': phase, 'joint_index': index,
                                          'state_max_signed_bits': max(map(signed_width, flat))})

def block_scale(values):
    return math.lcm(*(den for value in values
                      for den in (value.p.denominator, value.q.denominator)))

def run_fixed(vector, joints, scale, stats):
    state = tuple(encode_pair(x, scale) for x in vector.components())
    prepared = tuple(tuple(encode_pair(x, scale) for x in (j.f, j.g, j.h)) for j in joints)
    observe(stats, 'input', *(v for pair in state for v in pair),
            *(v for joint in prepared for pair in joint for v in pair), scale)
    inverses = tuple(fixed_inverse(j, scale, stats) for j in prepared)
    forward = state
    for i, joint in enumerate(prepared):
        forward = fixed_rotate(forward, joint, scale, stats)
        width_trace(forward, scale, stats, 'forward', i)
    recovered = forward
    for i in range(len(inverses)-1, -1, -1):
        recovered = fixed_rotate(recovered, inverses[i], scale, stats)
        width_trace(recovered, scale, stats, 'recovery', i)
    observe(stats, 'output', *(v for pair in (*forward, *recovered) for v in pair), scale)
    return materialize_pairs(forward, scale), materialize_pairs(recovered, scale)

def run_shared(vector, joints, stats):
    scale = block_scale(vector.components())
    state = tuple(encode_pair(x, scale) for x in vector.components())
    prepared = []
    inverses = []
    for joint in joints:
        joint_scale = block_scale((joint.f, joint.g, joint.h))
        encoded = tuple(encode_pair(x, joint_scale) for x in (joint.f, joint.g, joint.h))
        prepared.append((encoded, joint_scale))
        inverses.append((shared_inverse(encoded, stats), joint_scale*joint_scale))
    observe(stats, 'input', *(v for pair in state for v in pair), scale)
    forward, forward_scale = state, scale
    for i, (joint, joint_scale) in enumerate(prepared):
        forward = shared_rotate(forward, joint, joint_scale, stats)
        forward_scale *= joint_scale
        width_trace(forward, forward_scale, stats, 'forward', i)
    recovered, recovered_scale = forward, forward_scale
    for i in range(len(inverses)-1, -1, -1):
        joint, inverse_scale = inverses[i]
        recovered = shared_rotate(recovered, joint, inverse_scale, stats)
        recovered_scale *= inverse_scale
        width_trace(recovered, recovered_scale, stats, 'recovery', i)
    observe(stats, 'output', *(v for pair in (*forward, *recovered) for v in pair),
            forward_scale, recovered_scale)
    return (materialize_pairs(forward, forward_scale),
            materialize_pairs(recovered, recovered_scale))
