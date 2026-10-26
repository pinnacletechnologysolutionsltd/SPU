"""Exact D4 word and signed-permutation operations for the retrieval audit."""

from fractions import Fraction

from test_d4_reflection_oracle import ROOTS, reflect_formula


SELECT = (0, 1)


def word_formula(vector, word):
    for root_index in word:
        vector = reflect_formula(vector, ROOTS[root_index])
    return vector


def signed_map(word):
    """Build a signed permutation from explicit swaps, separate from roots."""
    labels = (1, 2, 3, 4)
    for index in word:
        a, b, c, d = labels
        if index == 0:
            labels = (b, a, c, d)
        elif index == 1:
            labels = (a, c, b, d)
        elif index == 2:
            labels = (a, b, d, c)
        elif index == 3:
            labels = (a, b, -d, -c)
        else:
            raise AssertionError(f"invalid root index {index}")
    return tuple((abs(label) - 1, 1 if label > 0 else -1)
                 for label in labels)


def apply_map(vector, mapping):
    return tuple(sign * vector[source] for source, sign in mapping)


def inverse_map(mapping):
    inverse = [None] * 4
    for output, (source, sign) in enumerate(mapping):
        inverse[source] = (output, sign)
    return tuple(inverse)


def compose(left, right):
    """Return left after right, using output-coordinate mappings."""
    return tuple((right[source][0], sign * right[source][1])
                 for source, sign in left)


def pulled_mask(mapping):
    return tuple(sorted(mapping[output][0] for output in SELECT))


def squared_distance(left, right, coordinates):
    return sum((left[index] - right[index]) ** 2 for index in coordinates)


def rank(query, candidates, scorer):
    return tuple(sorted(candidates, key=lambda key: (scorer(query, key), key)))


def rational(value: Fraction):
    return {"numerator": value.numerator, "denominator": value.denominator}
