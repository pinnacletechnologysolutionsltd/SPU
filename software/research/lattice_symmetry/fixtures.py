"""Deterministic proposed comparison inputs; no pseudo-random corpus selection."""
from .roots import roots, member


def validate_case(case):
    if type(case) is not dict or case.get('system') not in ('D4', 'E8'):
        raise ValueError('CASE_SYSTEM')
    n = 4 if case['system'] == 'D4' else 8
    values, word = case.get('scaled_input'), case.get('generator_word')
    if type(values) not in (list, tuple) or len(values) != n or not member(values):
        raise ValueError('CASE_VECTOR')
    if type(word) not in (list, tuple) or any(type(i) is not int or not 0 <= i < n for i in word):
        raise ValueError('CASE_WORD')


def simple_roots(system):
    n = 4 if system == 'D4' else 8
    if n == 4:
        return ((2, -2, 0, 0), (0, 2, -2, 0), (0, 0, 2, -2), (0, 0, 2, 2))
    # Standard independent E8 simple-root convention, doubled coordinates.
    return ((1, -1, -1, -1, -1, -1, -1, 1), (2, 2, 0, 0, 0, 0, 0, 0),
            (-2, 2, 0, 0, 0, 0, 0, 0), (0, -2, 2, 0, 0, 0, 0, 0),
            (0, 0, -2, 2, 0, 0, 0, 0), (0, 0, 0, -2, 2, 0, 0, 0),
            (0, 0, 0, 0, -2, 2, 0, 0), (0, 0, 0, 0, 0, -2, 2, 0))


def workload_plan():
    result = []
    for system in ('D4', 'E8'):
        n = 4 if system == 'D4' else 8
        basis = simple_roots(system)
        first, last = roots(system)[0], roots(system)[-1]
        vectors = [tuple([0] * n), first, last, tuple(a + b for a, b in zip(first, basis[0])),
                   tuple(17 * v for v in first)]
        for length in (0, 1, 2, 8, 32, 128):
            word = tuple(i % n for i in range(length))
            for mode, sequence in (('forward', word), ('inverse_pair', word + tuple(reversed(word)))):
                for index, values in enumerate(vectors):
                    result.append(dict(id=f'{system}/{mode}/{length}/{index}', system=system,
                                       scaled_input=list(values), generator_word=list(sequence)))
    return dict(status='PREPARED_NOT_QUALIFIED', coordinate_scale=2,
                word_order='left-to-right application; accumulated matrix is left-composed',
                proposed_cases=result)
