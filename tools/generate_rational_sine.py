#!/usr/bin/env python3
"""Generate a 4096-entry rational-surd ROM for a "rational sine" waveform.
Writes a 32-bit-per-line hex file (32-bit words) where upper 16 bits = signed P (rational part, Q15 fixed-point), lower 16 bits = signed Q (surd part, Q15 fixed-point, currently 0).
Usage: python3 tools/generate_rational_sine.py --depth 4096 --out hardware/common/rtl/gpu/rational_sine_4096.mem
"""
import argparse
import math

def to_word(p16, q16=0):
    return ((p16 & 0xffff) << 16) | (q16 & 0xffff)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--depth', type=int, default=4096)
    p.add_argument('--out', required=True)
    args = p.parse_args()

    depth = args.depth
    out = args.out

    lines = []
    for n in range(depth):
        # sample sin wave: sin(2*pi*n/N)
        theta = 2.0 * math.pi * n / depth
        val = math.sin(theta)  # in [-1,1]
        # convert to Q15 signed
        p16 = int(round(val * 32767.0))
        q16 = 0
        word = to_word(p16, q16)
        lines.append('{:08x}'.format(word))

    with open(out, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote {depth} entries to {out}')

if __name__ == '__main__':
    main()
