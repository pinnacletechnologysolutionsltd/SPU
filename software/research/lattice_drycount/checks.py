"""Independent formula and reference gates for every dry-count row."""
from fractions import Fraction
from ..lattice_symmetry.reference import reflect
from ..lattice_symmetry.fixtures import simple_roots


def expected(case):
    values = tuple(Fraction(v, 2) for v in case['scaled_input'])
    basis = simple_roots(case['system'])
    for token in case['generator_word']:
        values = reflect(values, tuple(Fraction(v, 2) for v in basis[token]))
    scaled = tuple(2*v for v in values)
    assert all(v.denominator == 1 for v in scaled), 'REFERENCE_SCALE'
    return tuple(int(v) for v in scaled)


def inspect(case, row):
    assert row['output'] == expected(case), 'REFERENCE_OUTPUT'
    n, length = len(case['scaled_input']), len(case['generator_word'])
    assert row['work'] == sum(row['counts'].values()), 'COUNT_SUM'
    assert row['work'] == sum(sum(v.values()) for v in row['stages'].values()), 'STAGE_SUM'
    arm = row['arm']
    if arm in ('coordinates', 'generator_word') and length:
        stage = row['stages']['construction' if arm == 'coordinates' else 'evaluation']
        assert stage['multiply'] == 2*n*length, 'COORDINATE_MULTIPLY_COUNT'
        assert stage['quotient'] == length, 'COORDINATE_QUOTIENT_COUNT'
    elif arm == 'matrix' and length:
        stage = row['stages']['construction']
        assert stage['multiply'] == 5*n**3*length, 'MATRIX_MULTIPLY_COUNT'
        assert stage['quotient'] == 4*n**3*length, 'MATRIX_NORMALIZATION_COUNT'
        assert sum(stage.values()) >= 40*n**3*length, 'MATRIX_LOWER_BOUND'
    elif arm == 'surd' and length:
        stage = row['stages']['evaluation']
        assert stage['multiply'] == 22*n*length, 'SURD_MULTIPLY_COUNT'
        assert stage['quotient'] == 12*n*length, 'SURD_NORMALIZATION_COUNT'
    assert row['retained_live_bits'] == 64+n*64, 'RETAINED_OUTPUT'
    return 'DRY_COUNT_ROW_CHECK_PASS'
