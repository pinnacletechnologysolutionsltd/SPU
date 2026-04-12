#!/usr/bin/env python3
"""Generate Padé [4/4] coefficients in Q32 and improved Q16 rounding.
Outputs:
 - hardware/common/rtl/gpu/pade_num_4_4_q32.mem (64-bit hex per line)
 - hardware/common/rtl/gpu/pade_den_4_4_q32.mem (64-bit hex per line)
 - hardware/common/rtl/gpu/pade_num_4_4.mem (Q16.16 improved rounding)
 - hardware/common/rtl/gpu/pade_den_4_4.mem (Q16.16 improved rounding)
"""
from math import factorial
from fractions import Fraction

# Maclaurin coefficients for exp(-x): a_k = (-1)^k / k!
a = [Fraction(( -1)**k, factorial(k)) for k in range(9)]  # 0..8
n = 4
m = 4
# Build system for denominator b1..b4
A = [[Fraction(0)]*m for _ in range(m)]
rhs = [Fraction(0)]*m
for row_k in range(n+1, n+m+1):
    i = row_k - (n+1)
    rhs[i] = -a[row_k]
    for j in range(1, m+1):
        A[i][j-1] = a[row_k - j]
# solve via fractions Gaussian elimination
aug = [ [Arow[j] for j in range(m)] + [rhsv] for Arow, rhsv in zip(A, rhs)]
for i in range(m):
    # pivot
    piv = aug[i][i]
    if piv == 0:
        for k in range(i+1,m):
            if aug[k][i] != 0:
                aug[i], aug[k] = aug[k], aug[i]
                piv = aug[i][i]
                break
    # normalize
    for j in range(i, m+1):
        aug[i][j] /= piv
    # eliminate others
    for k in range(m):
        if k == i: continue
        factor = aug[k][i]
        if factor != 0:
            for j in range(i, m+1):
                aug[k][j] -= factor * aug[i][j]
b = [aug[i][m] for i in range(m)]
b_full = [Fraction(1)] + b
# numerator p_i
p = []
for i in range(n+1):
    s = Fraction(0)
    for j in range(0, i+1):
        s += b_full[j] * a[i - j]
    p.append(s)

# scale and write Q32 (signed 64-bit) and Q16 (signed 32-bit) mems
SCALE16 = 1 << 16
SCALE32 = 1 << 32

def frac_to_signed_int(frac, scale):
    # round to nearest
    val = float(frac) * scale
    rounded = int(round(val))
    # clamp to signed width
    if scale == SCALE32:
        maxv = 2**63 - 1
        minv = -2**63
    else:
        maxv = 2**31 - 1
        minv = -2**31
    if rounded > maxv: rounded = maxv
    if rounded < minv: rounded = minv
    return rounded

num_q32 = [frac_to_signed_int(v, SCALE32) for v in p]
den_q32 = [frac_to_signed_int(v, SCALE32) for v in b_full]
num_q16 = [frac_to_signed_int(v, SCALE16) for v in p]
den_q16 = [frac_to_signed_int(v, SCALE16) for v in b_full]

with open('hardware/common/rtl/gpu/pade_num_4_4_q32.mem','w') as f:
    for v in num_q32:
        # 64-bit hex
        f.write('{:016x}\n'.format(v & 0xffffffffffffffff))
with open('hardware/common/rtl/gpu/pade_den_4_4_q32.mem','w') as f:
    for v in den_q32:
        f.write('{:016x}\n'.format(v & 0xffffffffffffffff))
with open('hardware/common/rtl/gpu/pade_num_4_4.mem','w') as f:
    for v in num_q16:
        f.write('{:08x}\n'.format(v & 0xffffffff))
with open('hardware/common/rtl/gpu/pade_den_4_4.mem','w') as f:
    for v in den_q16:
        f.write('{:08x}\n'.format(v & 0xffffffff))

print('Wrote Q32 and improved Q16 Padé mem files')
print('Numerator (fractions):', p)
print('Denominator (fractions):', b_full)
