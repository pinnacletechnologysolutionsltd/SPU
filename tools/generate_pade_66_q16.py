#!/usr/bin/env python3
from fractions import Fraction
from math import factorial

m = 6
# series coefficients s_n = 1/n!
s = [Fraction(1, factorial(n)) for n in range(0, 2*m+1)]

# build linear system for d1..dm using equations for n = m+1 .. 2m
# sum_{j=1..m} d_j * s[n-j] = -s[n]
M = [[Fraction(0,1) for _ in range(m)] for _ in range(m)]
b = [Fraction(0,1) for _ in range(m)]
for row, n in enumerate(range(m+1, 2*m+1)):
    for col in range(m):
        j = col + 1
        M[row][col] = s[n - j]
    b[row] = -s[n]

# augment and solve via Gaussian elimination with Fraction
# M_aug is m x (m+1)
M_aug = [row[:] + [bval] for row, bval in zip(M, b)]

# Gaussian elimination
for i in range(m):
    pivot = None
    for r in range(i, m):
        if M_aug[r][i] != 0:
            pivot = r
            break
    if pivot is None:
        raise Exception('Singular matrix')
    if pivot != i:
        M_aug[i], M_aug[pivot] = M_aug[pivot], M_aug[i]
    pv = M_aug[i][i]
    # normalize pivot row
    M_aug[i] = [val / pv for val in M_aug[i]]
    # eliminate other rows
    for r in range(m):
        if r == i:
            continue
        factor = M_aug[r][i]
        if factor != 0:
            M_aug[r] = [M_aug[r][c] - factor * M_aug[i][c] for c in range(m+1)]

# solution d1..dm
d = [M_aug[i][-1] for i in range(m)]

# build full denominator coefficients d0..dm with d0 = 1
d_all = [Fraction(1,1)] + d

# numerator coefficients n_k = sum_{j=0..k} d_j * s[k-j]
nn = []
for k in range(m+1):
    val = Fraction(0,1)
    for j in range(k+1):
        val += d_all[j] * s[k-j]
    nn.append(val)

# helper to convert Fraction to Q16 int with rounding
def to_q16(frac):
    scale = 1 << 16
    val = frac * scale
    num = val.numerator
    den = val.denominator
    if num >= 0:
        q = num // den
        if (num % den) * 2 >= den:
            q += 1
    else:
        # negative rounding
        q = -(((-num) // den))
        if ((-num) % den) * 2 >= den:
            q -= 1
    # fit into signed 32-bit two's complement representation
    q32 = q & 0xFFFFFFFF
    return q, q32

# write mem files in hardware/common/rtl/accel
num_q16 = [to_q16(v)[0] for v in nn]
den_q16 = [to_q16(v)[0] for v in d_all]

num_q16_hex = [format(x & 0xFFFFFFFF, '08x') for x in num_q16]
den_q16_hex = [format(x & 0xFFFFFFFF, '08x') for x in den_q16]

num_path = '/home/john/projects/hardware/SPU/hardware/common/rtl/accel/pade6_num_q16.mem'
den_path = '/home/john/projects/hardware/SPU/hardware/common/rtl/accel/pade6_den_q16.mem'
with open(num_path, 'w') as f:
    for h in num_q16_hex:
        f.write(h + '\n')
with open(den_path, 'w') as f:
    for h in den_q16_hex:
        f.write(h + '\n')

print('Padé(6,6) coefficients (rational):')
for i, v in enumerate(nn):
    print(f'num[{i}] = {v}')
for i, v in enumerate(d_all):
    print(f'den[{i}] = {v}')

print('\nPadé(6,6) Q16 (decimal):')
print('num_q16 =', num_q16)
print('den_q16 =', den_q16)
print('\nWrote mem files:')
print(num_path)
print(den_path)
