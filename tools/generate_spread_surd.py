#!/usr/bin/env python3
"""Generate a 4096-entry Q(\u221A3) Spread LUT using spread polynomials.
Writes a 32-bit-per-line hex file where upper 16 bits = signed P (Q15 fixed-point), lower 16 bits = signed Q (Q15 fixed-point).
Representation: value ~= P/scale + Q/scale * sqrt(3)

Sampling:
 - base s = n/depth (fractional phase in [0,1))
 - s1 = s
 - s2 = 4*s*(1-s)
 - s3 = s*(3-4*s)**2

Use --order {1,2,3} to select which polynomial to use (default 2).
"""
import argparse
import math

SCALE = 32767
SQRT3 = math.sqrt(3.0)


def best_pq_for_value(v, scale=SCALE):
    # initial guess for q: project onto sqrt(3) basis
    qf = v / SQRT3
    q_int = int(round(qf * scale))
    best = None
    for dq in (-2, -1, 0, 1, 2):
        q = q_int + dq
        a_real = v - (q / scale) * SQRT3
        p = int(round(a_real * scale))
        # clamp to signed 16-bit
        if p < -32768: p = -32768
        if p > 32767: p = 32767
        if q < -32768: q = -32768
        if q > 32767: q = 32767
        recon = p/scale + q/scale * SQRT3
        err = abs(recon - v)
        if best is None or err < best[0]:
            best = (err, p, q)
    return best[1], best[2]


def to_word(p16, q16):
    return ((p16 & 0xffff) << 16) | (q16 & 0xffff)


def compute_spread(base_s, order=2):
    s = base_s
    if order == 1:
        return s
    s2 = 4.0*s*(1.0 - s)
    if order == 2:
        return s2
    # order == 3
    s3 = s * (3.0 - 4.0*s)**2
    return s3


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--depth', type=int, default=4096)
    p.add_argument('--out', required=True)
    p.add_argument('--order', type=int, choices=[1,2,3], default=2,
                   help='Spread polynomial order: 1=s, 2=4s(1-s), 3=s(3-4s)^2')
    args = p.parse_args()

    depth = args.depth
    out = args.out
    order = args.order

    lines = []
    for n in range(depth):
        base_s = float(n) / float(depth)
        v = compute_spread(base_s, order=order)
        p16, q16 = best_pq_for_value(v)
        word = to_word(p16, q16)
        lines.append('{:08x}'.format(word))

    with open(out, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote {depth} spread(order={order}) entries to {out}')

if __name__ == '__main__':
    main()
