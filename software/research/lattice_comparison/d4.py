"""Conventional W(D4) even signed permutations, independent of reflection code."""
from itertools import permutations, product

IDENTITY = ((0, 1, 2, 3), (0, 0, 0, 0))
GENERATORS = (
    ((1, 0, 2, 3), (0, 0, 0, 0)),
    ((0, 2, 1, 3), (0, 0, 0, 0)),
    ((0, 1, 3, 2), (0, 0, 0, 0)),
    ((0, 1, 3, 2), (0, 0, 1, 1)),
)


def validate(value):
    if type(value) not in (tuple, list) or len(value) != 2:
        raise ValueError('D4_DESCRIPTOR')
    p, b = value
    if (type(p) not in (tuple, list) or type(b) not in (tuple, list)
            or len(p) != 4 or len(b) != 4
            or any(type(i) is not int for i in (*p, *b))
            or sorted(p) != [0, 1, 2, 3]
            or any(i not in (0, 1) for i in b) or sum(b) % 2):
        raise ValueError('D4_DESCRIPTOR')


def compose(left, right):
    """Action convention: apply right first, then left."""
    validate(left)
    validate(right)
    lp, lb = left
    rp, rb = right
    return (tuple(rp[lp[i]] for i in range(4)),
            tuple(lb[i] ^ rb[lp[i]] for i in range(4)))


def descriptor(word):
    if type(word) not in (tuple, list):
        raise ValueError('D4_WORD')
    result = IDENTITY
    for token in word:
        if type(token) is not int or not 0 <= token < 4:
            raise ValueError('D4_WORD')
        result = compose(GENERATORS[token], result)
    return result


def act(value, vector):
    validate(value)
    if (type(vector) not in (tuple, list) or len(vector) != 4
            or any(type(i) is not int for i in vector)):
        raise ValueError('D4_VECTOR')
    p, b = value
    return tuple(-vector[p[i]] if b[i] else vector[p[i]] for i in range(4))


def pack(value):
    """12 meaningful bits: four 2-bit indices followed by four sign bits."""
    validate(value)
    p, b = value
    return sum(p[i] << (2 * i) for i in range(4)) | sum(b[i] << (8 + i) for i in range(4))


def unpack(payload):
    if type(payload) is not int or not 0 <= payload < 4096:
        raise ValueError('D4_PAYLOAD')
    result = (tuple((payload >> (2 * i)) & 3 for i in range(4)),
              tuple((payload >> (8 + i)) & 1 for i in range(4)))
    validate(result)
    return result


def group():
    return tuple((p, b) for p in permutations(range(4))
                 for b in product((0, 1), repeat=4) if sum(b) % 2 == 0)
