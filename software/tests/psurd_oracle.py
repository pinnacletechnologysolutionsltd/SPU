"""Independent oracle for the EXPERIMENTAL programmable-surd profile (SPU-V03-SIM-0).

Written from docs/design/SPU_V03_CONTRACT_CANDIDATE.md (image revision 0x03) with Python big integers.
SRD (0x72) is retired: its encoder remains only to build negative tests.
It imports nothing from the C++ simulator. Also provides an encoder and the SIM-0 image envelope.
"""
import math, zlib

M64 = 1 << 64
I64 = lambda x: -(1 << 63) <= x < (1 << 63)
CAUSES = dict(HALT=0, BAD_ENCODING=1, INVALID=2, ENGINE_FAULT=3, BAD_TARGET=4, PC_OVERRUN=5, BUDGET=6)

# ---- encoder (draft §2 nibble layouts) ----
def W(op, r1=0, r2=0, p1a=0, low=0): return op << 56 | r1 << 48 | r2 << 40 | p1a << 24 | low
def SLI(d, s, p): return W(0x70, d, s) | (p & 0xFFFFFFFF) << 8
def SLD(d): return W(0x71, d)
def SRD(d, s): return W(0x72, d, s)
def AR(op, d, a, b): return W(op, d, a) | b << 24
SMUL = lambda d, a, b: AR(0x73, d, a, b)
SADD = lambda d, a, b: AR(0x74, d, a, b)
SSUB = lambda d, a, b: AR(0x75, d, a, b)
def SNORM(d, a): return W(0x76, d, a)
def SLIK(d, i): return W(0x78, d) | (i & 0xFFFFFFFF) << 8
def STST(a): return W(0x79, 0, a)
CC = dict(AL=0, EQ=1, NE=2, LT=3, GE=4, GT=5, LE=6, RF=7, NR=8, RS=9)
def BR(cc, t): return W(0x7A, CC[cc], 0, t)
HALT = 0x7B00000000000000
def LOAD(d, t):
    a, b, dd = (x % M64 for x in t)
    return [SLI(d, s, (v >> (32 * (s % 2))) & 0xFFFFFFFF) for s, v in enumerate((a, a, b, b, dd, dd))] + [SLD(d)]
def image(words, profile=0x01, rev=0x03, crc_delta=0, length=None):
    body = b''.join(w.to_bytes(8, 'big') for w in words)
    n = len(words) if length is None else length
    return b'SPUI' + bytes([profile, rev]) + n.to_bytes(2, 'little') + \
        ((zlib.crc32(body) + crc_delta) % 2**32).to_bytes(4, 'little') + body

# ---- semantics ----
def fit_or_norm(A, B, D):
    if I64(A) and I64(B) and 0 < D < M64: return (A, B, D)
    if A == 0 and B == 0: return (0, 0, 1)
    g = math.gcd(math.gcd(A, B), D)
    A, B, D = A // g, B // g, D // g
    return (A, B, D) if I64(A) and I64(B) and 0 < D < M64 else None
def mul(x, y): return fit_or_norm(x[0] * y[0] + 3 * x[1] * y[1], x[0] * y[1] + x[1] * y[0], x[2] * y[2])
def addsub(x, y, sgn):
    g = math.gcd(x[2], y[2]); u, v = y[2] // g, x[2] // g
    return fit_or_norm(x[0] * u + sgn * y[0] * v, x[1] * u + sgn * y[1] * v, x[2] * u)
def norm(x):
    if x[0] == 0 and x[1] == 0: return (0, 0, 1)
    g = math.gcd(math.gcd(x[0], x[1]), x[2]); return (x[0] // g, x[1] // g, x[2] // g)
def sign(x):   # sign of a + b*sqrt(3): exact via the sign of (a + b r)(a - b r) = a^2 - 3b^2 when needed
    a, b = x[0], x[1]
    if a == 0 and b == 0: return 0
    if a * b >= 0: return 1 if a + b > 0 else -1
    return (1 if a > 0 else -1) if a * a > 3 * b * b else (1 if b > 0 else -1)

def fields_ok(w):
    op, r1, r2 = w >> 56, (w >> 48) & 255, (w >> 40) & 255
    lo40, lo24, hi8, sb = w & (2**40 - 1), w & (2**24 - 1), (w >> 32) & 255, (w >> 24) & 255
    return {0x70: r1 < 8 and r2 < 6 and w & 255 == 0, 0x71: r1 < 8 and r2 == 0 and lo40 == 0,
            0x73: r1 < 8 and r2 < 8 and hi8 == 0 and sb < 8 and lo24 == 0,
            0x76: r1 < 8 and r2 < 8 and lo40 == 0, 0x78: r1 < 8 and r2 == 0 and w & 255 == 0,
            0x79: r1 == 0 and r2 < 8 and lo40 == 0, 0x7A: r1 <= 9 and r2 == 0 and lo24 == 0,
            0x7B: w == HALT}.get(0x73 if op in (0x74, 0x75) else op, False)

def run(words, budget):
    reg = [None] * 8; stage = {}; tgt = None; f = dict(Z=0, N=0, P=0, CV=0, R=0, RS=0)
    status = 0; pc = 0; n = 0; L = len(words)
    def end(c): return dict(cause=c, pc=pc, flags=f, status=status, retired=n, budget=budget, reg=reg)
    while True:
        if n == budget: return end('BUDGET')
        if pc >= L: return end('PC_OVERRUN')
        w = words[pc]
        if not fields_ok(w): return end('BAD_ENCODING')
        op, r1, r2, t, sb = w >> 56, (w >> 48) & 255, (w >> 40) & 255, (w >> 24) & 0xFFFF, (w >> 24) & 255
        nxt = pc + 1
        if op == 0x70:
            if stage and tgt != r1: return end('INVALID')
            tgt = r1; stage[r2] = (w >> 8) & 0xFFFFFFFF
        elif op == 0x71:
            if len(stage) != 6 or tgt != r1 or (stage[4] | stage[5]) == 0: return end('INVALID')
            v = [stage[2 * i] | stage[2 * i + 1] << 32 for i in range(3)]
            reg[r1] = (v[0] - M64 * (v[0] >> 63), v[1] - M64 * (v[1] >> 63), v[2]); stage = {}; tgt = None
        elif op in (0x73, 0x74, 0x75, 0x76):
            srcs = [r2] if op == 0x76 else [r2, sb]
            if any(reg[s] is None for s in srcs): return end('INVALID')
            r = {0x73: lambda: mul(reg[r2], reg[sb]), 0x74: lambda: addsub(reg[r2], reg[sb], 1),
                 0x75: lambda: addsub(reg[r2], reg[sb], -1), 0x76: lambda: norm(reg[r2])}[op]()
            f['R'] = int(r is None); f['RS'] |= f['R']; status = 2 if r is None else 0
            if r is not None: reg[r1] = r
        elif op == 0x78:
            i = (w >> 8) & 0xFFFFFFFF; reg[r1] = (i - (1 << 32) * (i >> 31), 0, 1)
        elif op == 0x79:
            if reg[r2] is None: return end('INVALID')
            s = sign(reg[r2]); f.update(Z=int(s == 0), N=int(s < 0), P=int(s > 0), CV=1)
        elif op == 0x7A:
            if t >= L: return end('BAD_TARGET')
            if 1 <= r1 <= 6 and not f['CV']: return end('INVALID')
            if [1, f['Z'], 1 - f['Z'], f['N'], 1 - f['N'], f['P'], 1 - f['P'], f['R'], 1 - f['R'], f['RS']][r1]: nxt = t
        elif op == 0x7B:
            n += 1; return end('HALT')
        n += 1; pc = nxt

def record(s):   # SIM-0 provisional layout of draft §8.3 (213 bytes)
    f = s['flags']
    b = bytes([0xA5, 3, 1, CAUSES[s['cause']], s['pc'] & 255, s['pc'] >> 8,
               f['Z'] | f['N'] << 1 | f['P'] << 2 | f['CV'] << 3 | f['R'] << 4 | f['RS'] << 5, s['status']])
    b += s['retired'].to_bytes(4, 'little') + s['budget'].to_bytes(4, 'little')
    b += bytes([sum(1 << i for i, r in enumerate(s['reg']) if r is not None)])
    for r in s['reg']: b += b''.join((x % M64).to_bytes(8, 'little') for x in (r or (0, 0, 0)))
    return b + zlib.crc32(b).to_bytes(4, 'little')
