"""Named preparation falsifiers with retained first counterexamples."""
from fractions import Fraction
from .checker import check_roots, need
from .linear import rank, apply, compose
from .mapping import constrained_block_basis, restore_blocks
from . import reference
from .roots import roots, reflect
from .fixtures import validate_case


def qualify():
    report = []

    def reject(name, reason, operation, exception=AssertionError):
        try:
            operation()
        except exception as error:
            detail = error.args
            actual = detail[0][0] if type(detail[0]) is tuple else detail[0]
            need(actual == reason, 'UNEXPECTED_CONTROL_REASON', name, reason, actual)
            report.append(dict(control=name, reason=actual, first_counterexample=detail))
        else:
            raise AssertionError(('CONTROL_ESCAPED', name))

    data = list(roots('D4'))
    reject('missing_root', 'ROOT_COUNT', lambda: check_roots('D4', data[:-1]))
    reject('duplicate_root', 'DUPLICATE_ROOT', lambda: check_roots('D4', [data[1]] + data[1:]))
    reject('wrong_norm', 'SCALED_ROOT_NORM', lambda: check_roots('D4', [(4, 0, 0, 0)] + data[1:]))
    reject('odd_coordinate', 'LATTICE_MEMBERSHIP', lambda: check_roots('D4', [(1, 0, 0, 0)] + data[1:]))
    reject('boolean', 'ROOT_INTEGER_TYPE', lambda: check_roots('D4', [(True, 0, 0, 0)] + data[1:]))
    e8 = list(roots('E8'))
    reject('half_root_parity', 'LATTICE_MEMBERSHIP', lambda: check_roots('E8', [(-1, 1, 1, 1, 1, 1, 1, 1)] + e8[1:]))
    reject('rank_six_as_e8', 'RANK_EIGHT_REQUIRED', lambda: need(rank(constrained_block_basis()) == 8,
            'RANK_EIGHT_REQUIRED', rank(constrained_block_basis())))
    reject('scaled_root_wrong_norm', 'INVALID_ROOT', lambda: reflect(data[0], tuple(v // 2 for v in data[0])), ValueError)
    reject('invalid_vector', 'OUTSIDE_LATTICE', lambda: reflect((1, 0, 0, 0), data[0]), ValueError)
    reject('block_fraction_loss', 'BLOCK_DIVISIBILITY', lambda: restore_blocks((((1, -1, 0, 0), 0), ((0, 0, 0, 0), 0))), ValueError)
    a, b = [tuple(Fraction(v, 2) for v in row) for row in ((2, -2, 0, 0), (0, 2, -2, 0))]
    x = (1, -1, 0, 0)
    expected = reference.reflect(reference.reflect(x, a), b)
    wrong = apply(compose(reference.matrix(a), reference.matrix(b)), x)
    reject('reversed_composition', 'COMPOSITION_ORDER', lambda: need(wrong == expected, 'COMPOSITION_ORDER', wrong, expected))
    reject('noninvolutive', 'REFLECTION_INVOLUTION', lambda: need(tuple(4 * v for v in x) == x,
           'REFLECTION_INVOLUTION', x, tuple(4 * v for v in x)))
    for token in (True, -1, 4):
        case = dict(system='D4', scaled_input=[2, -2, 0, 0], generator_word=[token])
        reject(f'invalid_generator_{token}', 'CASE_WORD', lambda: validate_case(case), ValueError)
    return report
