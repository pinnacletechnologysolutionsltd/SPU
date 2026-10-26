"""Small exact integer maps with known W(D4)-equivariance contracts."""


def _vector(x):
    if (type(x) not in (tuple, list) or len(x) != 4
            or any(type(value) is not int for value in x)):
        raise ValueError("D4_NL_VECTOR")
    return tuple(x)


def identity(x):
    return _vector(x)


def invariant_norm2(x):
    x = _vector(x)
    return sum(value * value for value in x)


def radial(x):
    x = _vector(x)
    scale = 1 + invariant_norm2(x)
    return tuple(scale * value for value in x)


def cubic_coupled(x):
    x = _vector(x)
    squares = tuple(value * value for value in x)
    norm2 = sum(squares)
    return tuple(value + value * square + value * norm2
                 for value, square in zip(x, squares))


def odd_threshold(x, threshold=2):
    x = _vector(x)
    if type(threshold) is not int or threshold < 0:
        raise ValueError("D4_NL_THRESHOLD")
    out = []
    for value in x:
        magnitude = max(abs(value) - threshold, 0)
        out.append(-magnitude if value < 0 else magnitude if value > 0 else 0)
    return tuple(out)


def signed_bits(max_magnitude):
    if type(max_magnitude) is not int or max_magnitude < 0:
        raise ValueError("D4_NL_MAGNITUDE")
    return max_magnitude.bit_length() + 1


def width_report(bound=4):
    if type(bound) is not int or bound < 0:
        raise ValueError("D4_NL_BOUND")
    norm2 = 4 * bound * bound
    radial_max = bound * (1 + norm2)
    cube_max = bound ** 3
    coupled_max = bound * norm2
    cubic_max = bound + cube_max + coupled_max
    threshold_max = max(bound - 2, 0)
    return {
        "coordinate_input_signed_bits": signed_bits(bound),
        "norm2_unsigned_bits": norm2.bit_length(),
        "radial_scale_unsigned_bits": (1 + norm2).bit_length(),
        "radial_output_signed_bits": signed_bits(radial_max),
        "cubic_term_signed_bits": signed_bits(cube_max),
        "coupled_product_signed_bits": signed_bits(coupled_max),
        "cubic_output_signed_bits": signed_bits(cubic_max),
        "odd_threshold_output_signed_bits": signed_bits(threshold_max),
        "max_magnitudes": {
            "norm2": norm2, "radial_output": radial_max,
            "cubic_term": cube_max, "coupled_product": coupled_max,
            "cubic_output": cubic_max, "odd_threshold_output": threshold_max,
        },
    }


def primitive_counts():
    """Source-level arithmetic events per vector; excludes validation/control."""
    return {
        "identity": {"copies": 4},
        "group_action": {"coordinate_permutations": 4, "conditional_signs": 4},
        "radial": {"multiplications": 8, "additions": 4},
        "cubic_coupled": {"multiplications": 12, "additions": 11},
        "odd_threshold": {"absolute_values": 4, "comparisons": 12,
                           "subtractions": 4, "selections": 12,
                           "sign_applications": 4},
        "counting_note": "source-level primitive counts; not weighted cost, runtime, or hardware estimates",
    }
