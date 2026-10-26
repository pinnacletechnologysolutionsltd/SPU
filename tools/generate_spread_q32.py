#!/usr/bin/env python3
"""Generate a 4096-entry Q(\u221A3) spread LUT with 32-bit P/Q per entry (packed 64-bit hex per line).
Writes hardware/common/rtl/gpu/rational_sine_4096_q32.mem
"""
import argparse
import math

SCALE32 = 2147483647
SQRT3 = math.sqrt(3.0)


def pack32(p,q):
    p32 = p & 0xffffffff
    q32 = q & 0xffffffff
    return (p32 << 32) | q32


def compute_spread(base_s, order=3):
    s = base_s
    if order == 1:
        return s
    s2 = 4.0*s*(1.0 - s)
    if order == 2:
        return s2
    s3 = s * (3.0 - 4.0*s)**2
    return s3


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--depth', type=int, default=4096)
    p.add_argument('--order', type=int, default=3)
    p.add_argument('--out', default='hardware/common/rtl/gpu/rational_sine_4096_q32.mem')
    args = p.parse_args()

    depth = args.depth
    order = args.order

    vals = [compute_spread(float(n)/depth, order) for n in range(depth)]

    packed = []
    recon = []
    for v in vals:
        qf = v / SQRT3
        q32 = int(round(qf * SCALE32))
        # clamp
        if q32 < -2**31: q32 = -2**31
        if q32 > 2**31-1: q32 = 2**31-1
        a_real = v - (q32 / SCALE32) * SQRT3
        p32 = int(round(a_real * SCALE32))
        if p32 < -2**31: p32 = -2**31
        if p32 > 2**31-1: p32 = 2**31-1
        packed.append(pack32(p32, q32))
        recon.append(p32/SCALE32 + q32/SCALE32 * SQRT3)

    with open(args.out,'w') as f:
        for w in packed:
            f.write('{:016x}\n'.format(w))

    # compute error stats
    max_err = 0.0; sum_err = 0.0; max_idx=0
    for i in range(depth):
        err = abs(recon[i] - vals[i])
        sum_err += err
        if err > max_err:
            max_err = err; max_idx = i
    print(f'Wrote {depth} entries to {args.out}; mean_err={sum_err/depth:.6e} max_err={max_err:.6e} at idx={max_idx}')

if __name__ == '__main__':
    main()
