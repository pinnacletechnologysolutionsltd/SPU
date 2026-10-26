"""Directed aliases and terminal failures; no change to frozen tuple semantics."""
from software.tools.surd_cpu_encoding import encode_surd
from software.experiments.surd_cpu_stream import canonical, fits


def verification_cases(stream):
    m, u = 1 << 63, (1 << 64) - 1
    cases = (
        ('SADD', (3, -4, 5), (-2, 7, 11)),
        ('SSUB', (3, -4, 5), (-2, 7, 11)),
        ('SMUL', (3, -4, 5), (-2, 7, 11)),
        ('SADD', (m-1, 0, 2), (m-1, 0, 2)),
        ('SSUB', (-m, 0, 2), (m-2, 0, 2)),
        ('SMUL', (m//2, 0, m), (2, 0, 2)),
        ('SADD', (m-1, 0, 1), (1, 0, 1)),
        ('SSUB', (-m, 0, 1), (1, 0, 1)),
        ('SMUL', (-m, 0, 1), (-1, 0, 1)),
    )
    all_equal = (
        ('SADD', (3, -4, 5)), ('SSUB', (3, -4, 5)),
        ('SMUL', (3, -4, 5)), ('SADD', (m-1, 0, 2)),
        ('SMUL', (-m, -m, m)), ('SADD', (m-1, 0, 1)),
        ('SMUL', (-m, -m, 1)), ('SSUB', (m-1, -m, u)),
    )

    def seed():
        stream.reset()
        # Distinct initialized poison values plus an uninitialized S7.
        for i in range(7):
            stream.load(i, (17+i, -19-i, 23+i))

    def alias(op, x, y, equal):
        seed()
        stream.load(0, x)
        if not equal:
            stream.load(1, y)
        dst, rhs = (0, 0) if equal else (1, 1)
        from math import gcd
        a, b, d = x
        c, e, f = y
        if op == 'SMUL':
            raw = (a*c + 3*b*e, a*e + b*c, d*f)
        else:
            g = gcd(d, f)
            sign = 1 if op == 'SADD' else -1
            raw = (a*(f//g) + sign*c*(d//g),
                   b*(f//g) + sign*e*(d//g), d*(f//g))
        kind = 11 if fits(raw) else 12 if fits(canonical(raw)) else 13
        stream.command(op, [f'S{dst}', 'S0', f'S{rhs}'], kind=kind)
        stream.command('SSTAT', [])
        for i in range(7):
            stream.read_tuple(i)
        stream.command('SRD', ['S7', 0])

    for op, x, y in cases:
        alias(op, x, y, False)
    for op, x in all_equal:
        alias(op, x, x, True)
    for kind in (5, 6):
        for op in ('SADD', 'SNORM', 'SMUL'):
            seed()
            stream.load(0, (m//2, 0, m))
            stream.load(1, (2, 0, 2))
            args = ['S2', 'S0'] + ([] if op == 'SNORM' else ['S1'])
            stream.row(kind, encode_surd(op, args), code=3)
            stream.status = 3
            stream.command('SSTAT', [])
            for i in range(7):
                stream.read_tuple(i)
            # Same arithmetic succeeds after releasing injection, without reset.
            stream.command(op, args)
            stream.command('SSTAT', [])
            stream.read_tuple(2)
