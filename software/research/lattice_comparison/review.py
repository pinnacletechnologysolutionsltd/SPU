"""Algorithmic review witnesses; not an independent human/agent sign-off."""
from fractions import Fraction
from .d4 import GENERATORS, act, group
from ..lattice_symmetry.fixtures import simple_roots, workload_plan
from ..lattice_symmetry.mapping import e8_to_blocks, restore_blocks
from ..lattice_symmetry.reference import roots as reference_roots
from ..lattice_symmetry.roots import roots


def determinant(matrix):
    """Bareiss elimination, independent of the preparation's Fraction rank routine."""
    a = [list(row) for row in matrix]
    previous, sign = 1, 1
    for k in range(len(a) - 1):
        pivot = next((i for i in range(k, len(a)) if a[i][k]), None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k], a[pivot], sign = a[pivot], a[k], -sign
        for i in range(k + 1, len(a)):
            for j in range(k + 1, len(a)):
                numerator = a[k][k] * a[i][j] - a[i][k] * a[k][j]
                if numerator % previous:
                    raise AssertionError('BAREISS_INEXACT')
                a[i][j] = numerator // previous
        previous = a[k][k]
        for i in range(k + 1, len(a)):
            a[i][k] = 0
    return sign * a[-1][-1]


def witnesses():
    findings = {}
    for system, expected_count, expected_det in (('D4', 24, 4), ('E8', 240, 1)):
        candidate = roots(system)
        independent = reference_roots(system)
        assert len(candidate) == expected_count
        assert {tuple(Fraction(v, 2) for v in x) for x in candidate} == set(independent)
        basis = simple_roots(system)
        gram = [[sum(a*b for a, b in zip(x, y)) // 4 for y in basis] for x in basis]
        assert determinant(gram) == expected_det
        assert all(gram[i][i] == 2 for i in range(len(basis)))
        assert all(gram[i][j] in (-1, 0) for i in range(len(basis)) for j in range(i))
        findings[system] = dict(roots=len(candidate), gram=gram, determinant=expected_det)
    # Transitivity on descriptors: closure under the four generators, starting at identity.
    from .d4 import IDENTITY, compose
    reached, frontier = {IDENTITY}, [IDENTITY]
    while frontier:
        value = frontier.pop()
        for generator in GENERATORS:
            nxt = compose(generator, value)
            if nxt not in reached:
                reached.add(nxt)
                frontier.append(nxt)
    assert reached == set(group())
    for value in group():
        assert all(act(value, x) in roots('D4') for x in roots('D4'))
    # A non-root E8 lattice witness, with both retained sums nonzero.
    x = (3, 1, 1, 1, 1, 1, 1, 3)
    blocks = e8_to_blocks(x)
    metric = sum(Fraction(sum(v*v for v in q), 64) + Fraction(t*t, 16) for q, t in blocks)
    assert restore_blocks(blocks) == x
    assert metric == sum(Fraction(v*v, 4) for v in x) == 6
    plan = workload_plan()['proposed_cases']
    assert len(plan) == 120 and len({case['id'] for case in plan}) == 120
    assert max(len(case['generator_word']) for case in plan) == 256
    findings.update(status='PREPARATION_REVIEW_WITNESSES_PASS', descriptor_group=192,
                    descriptor_root_actions=4608, block_metric_witness=str(metric),
                    prepared_cases=120, comparative_cases_executed=0,
                    independent_reviewer_signoff='PENDING; same preparer, separate algorithms')
    return findings
