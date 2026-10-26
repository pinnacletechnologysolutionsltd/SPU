"""Exact Quadray/FCC coordinate oracle; validation precedes arithmetic."""


def integer_vector(value, length):
    """Accept only built-in containers/integers, in contract rejection order."""
    if type(value) not in (tuple, list):
        raise ValueError('CONTAINER_TYPE')
    if len(value) != length:
        raise ValueError('TUPLE_LENGTH')
    if any(type(coefficient) is not int for coefficient in value):
        raise ValueError('COEFFICIENT_TYPE')
    return tuple(value)


def quadray_image(value):
    """Return D(q)/2 for the ratified domain; never round invalid coordinates."""
    a, b, c, d = integer_vector(value, 4)
    if (a + b + c + d) % 4:
        raise ValueError('INVALID_FCC_PARITY')
    return ((a + b - c - d) // 2,
            (a - b + c - d) // 2,
            (a - b - c + d) // 2)


def inverse_lift(value):
    """Zero-sum lift of an integer FCC node, not an ISA encoding."""
    x, y, z = integer_vector(value, 3)
    if (x + y + z) % 2:
        raise ValueError('INVALID_FCC_PARITY')
    return ((x + y + z) // 2, (x - y - z) // 2,
            (-x + y - z) // 2, (-x - y + z) // 2)
