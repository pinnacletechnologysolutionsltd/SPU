"""Deterministic canonical addressing for the rank-four root system D4."""

from software.research.lattice_comparison import d4


GROUP = tuple(sorted(d4.group()))
IDENTITY = d4.IDENTITY


def validate_vector(vector):
    if (type(vector) not in (tuple, list) or len(vector) != 4
            or any(type(value) is not int for value in vector)):
        raise ValueError("D4_VECTOR")
    return tuple(vector)


def inverse(element):
    """Return the two-sided inverse under d4.compose's action convention."""
    d4.validate(element)
    for candidate in GROUP:
        if (d4.compose(candidate, element) == IDENTITY
                and d4.compose(element, candidate) == IDENTITY):
            return candidate
    raise ValueError("D4_NO_INVERSE")


def canonicalize(vector):
    """Return (lexicographic orbit key, first sorted witness mapping to it)."""
    vector = validate_vector(vector)
    images = tuple((d4.act(element, vector), element) for element in GROUP)
    key = min(image for image, _ in images)
    witness = next(element for image, element in images if image == key)
    return key, witness


def orbit(vector):
    """Return distinct orbit vectors in deterministic lexicographic order."""
    vector = validate_vector(vector)
    return tuple(sorted({d4.act(element, vector) for element in GROUP}))
