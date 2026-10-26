"""Prepared coordinate, rational-matrix and conventional deferred-word arms."""
from fractions import Fraction

from .accounting import bits, Work
from .fixtures import simple_roots, validate_case


def coordinate(values, alpha, work):
    dot = 0
    for a, b in zip(values, alpha):
        dot = work.operation('add', dot, work.operation('multiply', a, b))
    work.counts['remainder_check'] += 1
    if dot % 4:
        raise ValueError('NONINTEGRAL_REFLECTION')
    work.counts['exact_quotient'] += 1
    coefficient = work.watch(dot // 4)
    return tuple(work.operation('subtract', x, work.operation('multiply', coefficient, a))
                 for x, a in zip(values, alpha))


def matrix(alpha, work):
    a = tuple(Fraction(v, 2) for v in alpha)
    return tuple(tuple(work.operation('subtract', Fraction(int(i == j)),
                       work.operation('multiply', a[i], a[j])) for j in range(len(a)))
                 for i in range(len(a)))


def dot(row, column, work):
    result = Fraction(0)
    for a, b in zip(row, column):
        result = work.operation('add', result, work.operation('multiply', a, b))
    return result


def multiply(left, right, work):
    return tuple(tuple(dot(row, column, work) for column in zip(*right)) for row in left)


def run(case, arm):
    validate_case(case)
    values, word = tuple(case['scaled_input']), tuple(case['generator_word'])
    generators, work = simple_roots(case['system']), Work()
    n, construction, table_bits = len(values), 0, bits(generators)
    peak = bits(values) + table_bits
    for value in values:
        work.watch(value)
    if arm == 'coordinates':
        for token in word:
            values = coordinate(values, generators[token], work)
            peak = max(peak, bits(values) + table_bits)
    elif arm == 'generator_word':
        # Appending does no arithmetic, but all deferred work is charged on evaluation.
        work.counts['word_append'] += len(word)
        construction = 32 + len(word) * (n - 1).bit_length()
        peak += construction
        for token in word:
            values = coordinate(values, generators[token], work)
            peak = max(peak, bits(values) + table_bits + construction)
    elif arm == 'matrix':
        current = tuple(tuple(Fraction(int(i == j)) for j in range(n)) for i in range(n))
        table = tuple(matrix(a, work) for a in generators)
        table_bits = bits(table)
        for token in word:
            updated = multiply(table[token], current, work)
            peak = max(peak, bits(current) + bits(updated) + table_bits + bits(values))
            current = updated
        construction = bits(current)
        physical = tuple(Fraction(v, 2) for v in values)
        output = tuple(dot(row, physical, work) for row in current)
        if any((v * 2).denominator != 1 for v in output):
            raise ValueError('MATRIX_OUTPUT_SCALE')
        values = tuple(int(v * 2) for v in output)
        peak = max(peak, construction + table_bits + bits(output) + bits(physical))
    else:
        raise ValueError('COMPARISON_ARM')
    return dict(scaled_output=values, descriptor_bits=construction,
                root_table_bits=table_bits, peak_observed_array_bits=peak,
                accounting=work.report(), costs_scope='logical; excludes containers/pointers; not cycles')
