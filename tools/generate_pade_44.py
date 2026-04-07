#!/usr/bin/env python3
"""Compute Padé [4/4] approximant for exp(-x) around 0 and write Q16.16 mem files.
Writes:
 - hardware/common/rtl/gpu/pade_num_4_4.mem (p0..p4, Q16.16 hex)
 - hardware/common/rtl/gpu/pade_den_4_4.mem (b0..b4, Q16.16 hex)
"""
from fractions import Fraction
from math import factorial

SCALE = 1 << 16

# Maclaurin coefficients for exp(-x): a_k = (-1)^k / k!
a = [Fraction(( -1)**k, factorial(k)) for k in range(9)]  # 0..8

n = 4
m = 4
# Solve for denominator coefficients b1..b4 (b0 = 1)
# Equations: sum_{j=1..m} b_j * a_{k-j} = -a_k  for k = n+1..n+m
# Build matrix A * b = rhs
A = [[0]*m for _ in range(m)]
rhs = [Fraction(0) for _ in range(m)]
for row_k in range(n+1, n+m+1):
    i = row_k - (n+1)
    rhs[i] = -a[row_k]
    for j in range(1, m+1):
        A[i][j-1] = a[row_k - j]

# Solve linear system using Gaussian elimination with fractions
# Augment matrix
aug = [ [Fraction(x) for x in Arow] + [rhsv] for Arow, rhsv in zip(A, rhs) ]
# elimination
for i in range(m):
    # pivot
    piv = aug[i][i]
    if piv == 0:
        # find non-zero pivot
        for k in range(i+1,m):
            if aug[k][i] != 0:
                aug[i], aug[k] = aug[k], aug[i]
                piv = aug[i][i]
                break
    # normalize
    for j in range(i, m+1):
        aug[i][j] /= piv
    # eliminate below
    for k in range(m):
        if k == i: continue
        factor = aug[k][i]
        if factor != 0:
            for j in range(i, m+1):
                aug[k][j] -= factor * aug[i][j]
# solution
b = [aug[i][m] for i in range(m)]
# assemble full b coefficients with b0 = 1
b_full = [Fraction(1)] + b

# compute numerator coefficients p0..p4: p_i = sum_{j=0..i} b_j * a_{i-j}
p = []
for i in range(n+1):
    s = Fraction(0)
    for j in range(0, i+1):
        s += b_full[j] * a[i - j]
    p.append(s)

# Convert to Q16.16
def frac_to_q16(frac):
    # round to nearest
    val = int((frac * SCALE).numerator // (frac * SCALE).denominator)
    # for rounding, compute float diff
    # better: use rounding by adding 0.5
    # but using Fraction trunc; adjust using float
    # simple approach: compute rounded = int(round(float(frac) * SCALE))
    rounded = int(round(float(frac) * SCALE))
    # clamp to signed 32-bit
    if rounded >= 2**31:
        rounded = 2**31 - 1
    if rounded < -2**31:
        rounded = -2**31
    return rounded

num_q = [frac_to_q16(v) for v in p]
den_q = [frac_to_q16(v) for v in b_full]

# write mem files as 8-hex per line
os_num = 'hardware/common/rtl/gpu/pade_num_4_4.mem'
os_den = 'hardware/common/rtl/gpu/pade_den_4_4.mem'
with open(os_num, 'w') as fn:
    for v in num_q:
        fn.write('{:08x}\n'.format(v & 0xffffffff))
with open(os_den, 'w') as fd:
    for v in den_q:
        fd.write('{:08x}\n'.format(v & 0xffffffff))

# print coefficients for logging
print('Numerator coefficients (p0..p4) as fractions:')
for v in p:
    print(v)
print('\nDenominator coefficients (b0..b4) as fractions:')
for v in b_full:
    print(v)
print('\nWrote', os_num, 'and', os_den)
