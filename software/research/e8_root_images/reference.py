"""Independent rational reflection/matrix reference; no descriptor/table update imports."""
from fractions import Fraction
from ..lattice_symmetry.reference import roots, reflect, matrix
from ..lattice_symmetry.fixtures import simple_roots
from ..lattice_symmetry.linear import compose, apply


def word_matrix(word):
    result = tuple(tuple(Fraction(i == j) for j in range(8)) for i in range(8))
    basis = tuple(tuple(Fraction(v,2) for v in row) for row in simple_roots('E8'))
    for j in word:
        result = compose(matrix(basis[j]),result)
    return result


def word_apply(word, scaled_vector):
    result = tuple(Fraction(v,2) for v in scaled_vector)
    basis = tuple(tuple(Fraction(v,2) for v in row) for row in simple_roots('E8'))
    for j in word:
        result = reflect(result,basis[j])
    return tuple(2*v for v in result)


def check_context(ctx):
    from ..lattice_comparison.review import determinant
    expected = tuple(sorted(tuple(int(2*v) for v in row) for row in roots('E8')))
    if expected != ctx.roots:
        raise ValueError('ROOT_REFERENCE')
    basis = tuple(tuple(Fraction(v,2) for v in row) for row in ctx.basis)
    gram = tuple(tuple(sum(a*b for a,b in zip(x,y)) for y in basis) for x in basis)
    if gram != ctx.gram or determinant(ctx.gram) != 1:
        raise ValueError('GRAM_REFERENCE')
    scaled = tuple(tuple(ctx.basis[j][i] for j in range(8)) for i in range(8))
    det = determinant(scaled)
    if abs(det) != 256:
        raise ValueError('BASIS_DETERMINANT')
    # Cofactor inversion is independent of the candidate's Gauss-Jordan routine.
    inverse_basis = tuple(tuple(Fraction((-1)**(i+j)*determinant(
        tuple(tuple(scaled[r][c] for c in range(8) if c != i)
              for r in range(8) if r != j)),det) for j in range(8)) for i in range(8))
    if inverse_basis != ctx.inverse_basis:
        raise ValueError('INVERSE_BASIS_REFERENCE')
    for i,x in enumerate(expected):
        coordinates = tuple(sum(a*b for a,b in zip(row,x)) for row in inverse_basis)
        if coordinates != ctx.coefficients[i] or any(v.denominator != 1 for v in coordinates):
            raise ValueError('ROOT_COEFFICIENT_REFERENCE')
    positive = tuple(i for i,c in enumerate(ctx.coefficients) if all(v >= 0 for v in c) and any(c))
    if positive != ctx.positive_ids or len(positive) != 120:
        raise ValueError('POSITIVE_ROOT_REFERENCE')
    if len(ctx.reflections) != 8 or any(len(row) != 240 for row in ctx.reflections):
        raise ValueError('TABLE_SHAPE')
    for j,row in enumerate(ctx.reflections):
        if any(type(i) is not int or not 0 <= i < 240 for i in row):
            raise ValueError('TABLE_INDEX')
        for i,x in enumerate(expected):
            reflected = reflect(tuple(Fraction(v,2) for v in x),basis[j])
            if tuple(2*v for v in reflected) != ctx.roots[row[i]]:
                raise ValueError('TABLE_REFERENCE')
            if row[row[i]] != i:
                raise ValueError('TABLE_INVOLUTION')
    return dict(roots=240, reflection_entries=1920, gram_determinant=1,
                status='INDEPENDENT_ALGORITHM_CHECK_PASS', reviewer_signoff='PENDING')
