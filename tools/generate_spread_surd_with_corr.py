#!/usr/bin/env python3
"""Generate a spread LUT and a small correction table.
Outputs:
 - main ROM: hardware/common/rtl/gpu/rational_sine_4096.mem
 - correction ROM: hardware/common/rtl/gpu/rational_sine_4096_corr256.mem (if --corr-size provided)

Algorithm:
 - sample spread polynomial (order 1/2/3) at depth points
 - encode each value into Q(\u221A3) basis with signed 16-bit P/Q (Q15 fixed point)
 - compute residuals (true - recon)
 - for corr_size entries, sample residual at segment center and encode as P/Q into corr mem
 - compute errors before/after applying linear interpolation of correction table
"""
import argparse
import math

SCALE = 32767
SQRT3 = math.sqrt(3.0)


def best_pq_for_value(v, scale=SCALE):
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


def to_word(p16, q16):
    return ((p16 & 0xffff) << 16) | (q16 & 0xffff)


def compute_spread(base_s, order=2):
    s = base_s
    if order == 1:
        return s
    s2 = 4.0*s*(1.0 - s)
    if order == 2:
        return s2
    s3 = s * (3.0 - 4.0*s)**2
    return s3


def encode_list(vals, scale=SCALE):
    packed = []
    recon_list = []
    for v in vals:
        p16, q16 = best_pq_for_value(v, scale)
        packed.append(to_word(p16, q16))
        recon_list.append(p16/scale + q16/scale * SQRT3)
    return packed, recon_list


def write_mem(path, packed):
    with open(path, 'w') as f:
        for w in packed:
            f.write('{:08x}\n'.format(w))


def interp_corr(corr_vals, idx_f):
    # corr_vals is list length M, idx_f in [0,M)
    m = len(corr_vals)
    if m == 0:
        return 0.0
    if m == 1:
        return corr_vals[0]
    lo = int(math.floor(idx_f))
    hi = min(lo+1, m-1)
    t = idx_f - lo
    return corr_vals[lo] * (1.0 - t) + corr_vals[hi] * t


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--depth', type=int, default=4096)
    p.add_argument('--out', default='hardware/common/rtl/gpu/rational_sine_4096.mem')
    p.add_argument('--order', type=int, choices=[1,2,3], default=3)
    p.add_argument('--corr-size', type=int, default=256)
    p.add_argument('--corr-out', default='hardware/common/rtl/gpu/rational_sine_4096_corr256.mem')
    args = p.parse_args()

    depth = args.depth
    order = args.order
    corr_size = args.corr_size

    vals = []
    for n in range(depth):
        base_s = float(n) / float(depth)
        v = compute_spread(base_s, order=order)
        vals.append(v)

    packed, recon = encode_list(vals)
    write_mem(args.out, packed)

    # compute residuals
    residuals = [vals[i] - recon[i] for i in range(depth)]

    # build correction table: sample residual at segment centers
    corr_vals = []
    for c in range(corr_size):
        # center of segment
        start = (c * depth) // corr_size
        end = ((c+1) * depth) // corr_size
        if end <= start:
            idx = start
        else:
            idx = (start + end) // 2
        corr_vals.append(residuals[idx])

    # encode corr_vals
    corr_packed, corr_recon = encode_list(corr_vals)
    write_mem(args.corr_out, corr_packed)

    # compute error stats before and after applying interpolated correction
    max_err_before = 0.0
    sum_err_before = 0.0
    max_err_after = 0.0
    sum_err_after = 0.0
    for i in range(depth):
        err_before = abs(residuals[i])
        sum_err_before += err_before
        if err_before > max_err_before:
            max_err_before = err_before
            idx_before = i
        # interpolate correction
        idx_f = (i + 0.5) * corr_size / depth
        corr_interp = interp_corr(corr_recon, idx_f)
        err_after = abs(residuals[i] - corr_interp)
        sum_err_after += err_after
        if err_after > max_err_after:
            max_err_after = err_after
            idx_after = i

    mean_before = sum_err_before / depth
    mean_after = sum_err_after / depth

    print(f'Wrote main ROM {args.out} and correction ROM {args.corr_out} (corr_size={corr_size})')
    print(f'Error before: mean={mean_before:.6e} max={max_err_before:.6e} at idx={idx_before}')
    print(f'Error after : mean={mean_after:.6e} max={max_err_after:.6e} at idx={idx_after}')

    # print some sample entries
    print('\nSample entries (idx, original, recon, residual, corr_interp, residual_after):')
    for i in range(16):
        base_s = i / depth
        orig = vals[i]
        r = recon[i]
        resid = residuals[i]
        idx_f = (i + 0.5) * corr_size / depth
        corr_interp = interp_corr(corr_recon, idx_f)
        print(i, f'{orig:.10f}', f'{r:.10f}', f'{resid:.10e}', f'{corr_interp:.10e}', f'{(resid - corr_interp):.10e}')

if __name__ == '__main__':
    main()
