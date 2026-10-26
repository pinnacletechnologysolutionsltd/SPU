"""Software-only explicit-denominator Surd bridge; never imports or changes CPU RTL."""
from fractions import Fraction
from math import gcd

from .accounting import bits, Work
from .fixtures import simple_roots, validate_case


def normalize(a, b, d, work):
    if d <= 0:
        raise ValueError('SURD_DENOMINATOR')
    work.counts['gcd_calls'] += 2
    common = gcd(gcd(abs(a), abs(b)), d)
    work.counts['exact_quotient'] += 3
    for v in (a, b, d):
        work.watch(v)
    return a // common, b // common, d // common


def add(left, right, work, subtract=False):
    a, b, d = left; c, e, f = right
    operation = 'subtract' if subtract else 'add'
    product = lambda x, y: work.operation('multiply', x, y)
    return normalize(work.operation(operation, product(a, f), product(c, d)),
                     work.operation(operation, product(b, f), product(e, d)), product(d, f), work)


def multiply(left, right, work):
    a, b, d = left; c, e, f = right
    product = lambda x, y: work.operation('multiply', x, y)
    return normalize(work.operation('add', product(a, c), product(3, product(b, e))),
                     work.operation('add', product(a, e), product(b, c)), product(d, f), work)


def run(case):
    validate_case(case)
    work = Work()
    encode = lambda row: tuple((Fraction(v, 2).numerator, 0, Fraction(v, 2).denominator) for v in row)
    values = encode(case['scaled_input'])
    table = tuple(encode(row) for row in simple_roots(case['system']))
    peak = bits(values) + bits(table)
    work.counts['coordinate_encode'] += len(values) + sum(map(len, table))
    for token in case['generator_word']:
        root, coefficient = table[token], (0, 0, 1)
        for x, a in zip(values, root):
            coefficient = add(coefficient, multiply(x, a, work), work)
        updated = tuple(add(x, multiply(coefficient, a, work), work, True) for x, a in zip(values, root))
        peak = max(peak, bits(values) + bits(updated) + bits(table) + bits(coefficient))
        values = updated
    work.counts['coordinate_decode'] += len(values)
    if any(b or (2 * a) % d for a, b, d in values):
        raise ValueError('SURD_OUTPUT_SCALE')
    work.counts['exact_quotient'] += len(values)
    return dict(scaled_output=tuple(2 * a // d for a, b, d in values), descriptor_bits=0,
                root_table_bits=bits(table), peak_observed_array_bits=peak,
                accounting=work.report(), costs_scope='B=0 rational subspace; software Surd bridge; no AOR-S1')
