#!/usr/bin/env python3
"""Generate exp LUT: exp(-x) samples over x in [0, XMAX], Q16.16 per entry, 256 entries."""
import math
XMAX = 4.0
N = 256
SCALE = 1 << 16
OUT = 'hardware/common/rtl/gpu/exp_lut_256.mem'
with open(OUT,'w') as f:
    for i in range(N):
        x = XMAX * i / (N-1)
        val = math.exp(-x)
        q = int(round(val * SCALE))
        if q < 0: q = 0
        if q > 0xffffffff: q = 0xffffffff
        f.write('{:08x}\n'.format(q & 0xffffffff))
print('Wrote', OUT)
