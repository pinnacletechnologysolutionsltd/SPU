"""SDK-0 decoder for the v0.3 result record (contract §11, 213 bytes, provisional format). Validates before use."""
import zlib
from fractions import Fraction

CAUSES = ['HALT', 'BAD_ENCODING', 'INVALID', 'ENGINE_FAULT', 'BAD_TARGET', 'PC_OVERRUN', 'BUDGET']
FLAGS = ['Z', 'N', 'P', 'CV', 'R', 'RS']

def value_str(a, b, d):
    """(a + b*sqrt3)/d in lowest terms, e.g. '3√3', '-1/2 + √3/2', '0'."""
    if a == 0 and b == 0: return '0'
    x, y = Fraction(a, d), Fraction(b, d); parts = []
    if x: parts.append(str(x))
    if y:
        c = '' if abs(y.numerator) == 1 else str(abs(y.numerator))
        t = f'{c}√3' + (f'/{y.denominator}' if y.denominator != 1 else '')
        parts.append(('-' if y < 0 else '') + t if not parts else ('- ' if y < 0 else '+ ') + t)
    return ' '.join(parts)

def decode(rec):
    if len(rec) != 213: raise ValueError(f'record is {len(rec)} bytes, expected 213')
    if zlib.crc32(rec[:209]) != int.from_bytes(rec[209:213], 'little'): raise ValueError('record CRC mismatch')
    if rec[0] != 0xA5 or rec[1] != 0x03 or rec[2] != 0x01: raise ValueError('not a programmable-surd version 3 record')
    if rec[3] > 6 or rec[7] not in (0, 2) or rec[6] & 0xC0: raise ValueError('record field out of range')
    mask = rec[16]; regs = []
    for i in range(8):
        f = [int.from_bytes(rec[17 + 24 * i + 8 * k:25 + 24 * i + 8 * k], 'little', signed=k < 2) for k in range(3)]
        init = bool(mask >> i & 1)
        regs.append(dict(reg=f'S{i}', initialized=init, a=f[0], b=f[1], d=f[2],
                         value=value_str(*f) if init else None))
    return dict(cause=CAUSES[rec[3]], pc=int.from_bytes(rec[4:6], 'little'),
                flags={n: rec[6] >> k & 1 for k, n in enumerate(FLAGS)}, status='OVERFLOW' if rec[7] == 2 else 'OK',
                retired=int.from_bytes(rec[8:12], 'little'), budget=int.from_bytes(rec[12:16], 'little'), registers=regs)

def same_value(reg, expect):
    """Exact value equality of a decoded register with an expected [a, b, d] (representation may differ)."""
    a, b, d = expect
    return reg['initialized'] and Fraction(reg['a'], reg['d']) == Fraction(a, d) and Fraction(reg['b'], reg['d']) == Fraction(b, d)

def text(r):
    out = [f"cause {r['cause']}  pc {r['pc']}  retired {r['retired']}/{r['budget']}  status {r['status']}  "
           + ' '.join(f'{k}={v}' for k, v in r['flags'].items())]
    for g in r['registers']:
        out.append(f"  {g['reg']}  " + (f"({g['a']}, {g['b']}, {g['d']})  = {g['value']}" if g['initialized'] else 'uninitialized'))
    return '\n'.join(out)
