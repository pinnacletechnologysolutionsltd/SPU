#!/usr/bin/env python3
"""Generate spread LUT and improved correction table (32-bit P/Q) sampled at segment starts and interpolated using idx = i * corr_size / depth.
This version samples residual at segment START indices (not centers) to better match interpolation mapping.
"""
import argparse
import math

SCALE16 = 32767
SCALE32 = 2147483647
SQRT3 = math.sqrt(3.0)


def best_pq_for_value(v, scale=SCALE16):
    qf = v / SQRT3
    q_int = int(round(qf * scale))
    best = None
    for dq in (-3, -2, -1, 0, 1, 2, 3):
        q = q_int + dq
        a_real = v - (q / scale) * SQRT3
        p = int(round(a_real * scale))
        # clamp
        if p < -32768: p = -32768
        if p > 32767: p = 32767
        if q < -32768: q = -32768
        if q > 32767: q = 32767
        recon = p/scale + q/scale * SQRT3
        err = abs(recon - v)
        if best is None or err < best[0]:
            best = (err, p, q)
    return best[1], best[2]


def pack16(p,q):
    return ((p & 0xffff) << 16) | (q & 0xffff)


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
    p.add_argument('--corr-size', type=int, default=256)
    args = p.parse_args()

    depth = args.depth
    order = args.order
    corr_size = args.corr_size

    vals = [compute_spread(float(n)/depth, order) for n in range(depth)]

    # encode main ROM (16-bit)
    main_packed = []
    main_recon = []
    for v in vals:
        # reuse best_pq_for_value from earlier but duplicate for clarity
        qf = v / SQRT3
        q_int = int(round(qf * SCALE16))
        best = None
        for dq in (-3, -2, -1, 0, 1, 2, 3):
            q = q_int + dq
            a_real = v - (q / SCALE16) * SQRT3
            p = int(round(a_real * SCALE16))
            if p < -32768: p = -32768
            if p > 32767: p = 32767
            if q < -32768: q = -32768
            if q > 32767: q = 32767
            recon = p/SCALE16 + q/SCALE16 * SQRT3
            err = abs(recon - v)
            if best is None or err < best[0]:
                best = (err, p, q)
        p16,q16 = best[1], best[2]
        main_packed.append(pack16(p16,q16))
        main_recon.append(p16/SCALE16 + q16/SCALE16 * SQRT3)

    with open('hardware/common/rtl/gpu/rational_sine_4096.mem','w') as f:
        for w in main_packed:
            f.write('{:08x}\n'.format(w))

    residuals = [vals[i] - main_recon[i] for i in range(depth)]

    # Build correction table sampled at segment START indices
    corr_packed = []
    corr_recon = []
    starts = []
    for c in range(corr_size):
        start = (c * depth) // corr_size
        starts.append(start)
        r = residuals[start]
        # encode r into 32-bit signed P/Q (Q31)
        qf = r / SQRT3
        q32_guess = int(round(qf * SCALE32))
        best = None
        for dq in range(-10,11):
            q32 = q32_guess + dq
            a_real = r - (q32 / SCALE32) * SQRT3
            p32 = int(round(a_real * SCALE32))
            if p32 < -2**31: p32 = -2**31
            if p32 > 2**31-1: p32 = 2**31-1
            if q32 < -2**31: q32 = -2**31
            if q32 > 2**31-1: q32 = 2**31-1
            recon = p32/SCALE32 + q32/SCALE32 * SQRT3
            err = abs(recon - r)
            if best is None or err < best[0]:
                best = (err, p32, q32)
        p32,q32 = best[1], best[2]
        corr_packed.append(pack32(p32,q32))
        corr_recon.append(p32/SCALE32 + q32/SCALE32 * SQRT3)

    with open('hardware/common/rtl/gpu/rational_sine_4096_corr256_q32_start.mem','w') as f:
        for w in corr_packed:
            f.write('{:016x}\n'.format(w))

    # Interpolate using idx = i * corr_size / depth
    def interp(idx_f):
        m = corr_size
        if m == 1: return corr_recon[0]
        lo = int(math.floor(idx_f))
        hi = min(lo+1, m-1)
        t = idx_f - lo
        return corr_recon[lo]*(1-t) + corr_recon[hi]*t

    max_before=0.0; sum_before=0.0
    max_after=0.0; sum_after=0.0
    ib=None; ia=None
    for i in range(depth):
        errb = abs(residuals[i])
        sum_before += errb
        if errb > max_before: max_before = errb; ib = i
        idx_f = i * corr_size / depth
        corrv = interp(idx_f)
        erra = abs(residuals[i] - corrv)
        sum_after += erra
        if erra > max_after: max_after = erra; ia = i

    print(f'main ROM written and corr ROM written (corr_size={corr_size})')
    print(f'Error before: mean={sum_before/depth:.6e} max={max_before:.6e} at idx={ib}')
    print(f'Error after : mean={sum_after/depth:.6e} max={max_after:.6e} at idx={ia}')

    print('\nSample entries (idx,orig,recon,resid,corr_interp,resid_after):')
    for i in range(16):
        orig = vals[i]
        reconv = main_recon[i]
        resid = residuals[i]
        idx_f = i * corr_size / depth
        corrv = interp(idx_f)
        print(i, f'{orig:.10f}', f'{reconv:.10f}', f'{resid:.10e}', f'{corrv:.10e}', f'{(resid - corrv):.10e}')

if __name__ == '__main__':
    main()
