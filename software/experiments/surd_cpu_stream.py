"""CPU program writer and independent exact tuple expectations; never times Python."""
from fractions import Fraction
from math import gcd
from software.tools.surd_cpu_encoding import encode_surd

MASK = (1 << 64) - 1


def canonical(t):
    a, b, d = t
    g = gcd(gcd(abs(a), abs(b)), d)
    return a // g, b // g, d // g


def fits(t):
    return all(-(1 << 63) <= c < 1 << 63 for c in t[:2]) and 0 < t[2] <= MASK


class Stream:
    def __init__(self):
        self.lines = []
        self.group = -1
        self.reset()

    def row(self, kind, word=0, code=0, writes=0, t=(0, 0, 1), cache=-1, read=0, tag=0):
        a, b, d = t
        self.lines.append(f'{kind} {word:016x} {code} {writes} {a&MASK:016x} '
                          f'{b&MASK:016x} {d&MASK:016x} {cache} {read:08x} {self.group} {tag}')

    def reset(self):
        self.bank = [None] * 8
        self.staged = {}
        self.target = None
        self.status = 0
        self.cached = {}
        self.row(8)

    def command(self, mnemonic, args, cache=-1, tag=0, kind=1):
        word = encode_surd(mnemonic, list(map(str, args)))
        dst = int(args[0][1:]) if args and str(args[0]).startswith('S') else 0
        code, write, read, result = 0, 0, 0, (0, 0, 1)
        if mnemonic == 'SLI':
            if self.target is not None and self.target != dst:
                code = 1
            else:
                self.target = dst
                self.staged[int(args[1])] = self.cached[cache] if kind == 2 else int(args[2])
        elif mnemonic == 'SLD':
            if self.target == dst and len(self.staged) == 6:
                values = [self.staged[2*i] | self.staged[2*i+1] << 32 for i in range(3)]
                result = tuple(v - (1 << 64) if i < 2 and v >> 63 else v for i, v in enumerate(values))
                code = int(result[2] == 0)
                write = int(code == 0)
            else:
                code = 1
            self.target, self.staged = None, {}
        elif mnemonic == 'SRD':
            result = self.bank[dst]
            if result is None:
                code, result = 1, (0, 0, 1)
            else:
                index = int(args[1])
                read = ((result[index//2] & MASK) >> (32*(index & 1))) & 0xffffffff
                if cache >= 0:
                    self.cached[cache] = read
        elif mnemonic == 'SSTAT':
            code, read = self.status, self.status
        else:
            x = self.bank[int(args[1][1:])]
            y = self.bank[int(args[2][1:])] if len(args) == 3 else None
            if x is None or (len(args) == 3 and y is None):
                code = 1
            elif mnemonic == 'SNORM':
                result, write = canonical(x), 1
            else:
                a, b, d = x
                c, e, f = y
                if mnemonic == 'SMUL':
                    result = a*c + 3*b*e, a*e + b*c, d*f
                    real = Fraction(a,d)*Fraction(c,f) + 3*Fraction(b,d)*Fraction(e,f)
                    radical = Fraction(a,d)*Fraction(e,f) + Fraction(b,d)*Fraction(c,f)
                else:
                    g = gcd(d, f)
                    u, v = f//g, d//g
                    sign = 1 if mnemonic == 'SADD' else -1
                    result = a*u + sign*c*v, b*u + sign*e*v, d*u
                    real = Fraction(a,d) + sign*Fraction(c,f)
                    radical = Fraction(b,d) + sign*Fraction(e,f)
                if Fraction(result[0],result[2]) != real or Fraction(result[1],result[2]) != radical:
                    raise ValueError('independent component oracle disagreement')
                if not fits(result):
                    result = canonical(result)
                code, write = (0, 1) if fits(result) else (2, 0)
        if write:
            self.bank[dst] = result
        self.status = code
        self.row(kind, word, code, write, result, cache, read, tag)

    def load(self, dst, t=None, cached_joint=None, component=0):
        for i in range(6):
            payload = ((t[i//2] & MASK) >> (32*(i & 1))) & 0xffffffff if t else 0
            cache = cached_joint*18 + component*6 + i if cached_joint is not None else -1
            self.command('SLI', [f'S{dst}', i, payload], cache=cache, kind=2 if cache>=0 else 1)
        self.command('SLD', [f'S{dst}'])

    def read_tuple(self, src, cache_base=-1):
        for i in range(6):
            self.command('SRD', [f'S{src}', i], cache=cache_base+i if cache_base>=0 else -1)
