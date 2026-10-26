"""Basis-permutation action on exact Quadray tuples and directed ports."""
from .geometry import integer_vector, quadray_image


def basis_permutation(value):
    sigma = integer_vector(value, 4)
    if sorted(sigma) != [0, 1, 2, 3]:
        raise ValueError('INVALID_BASIS_PERMUTATION')
    return sigma


def permute_quadray(value, permutation):
    sigma = basis_permutation(permutation)
    q = integer_vector(value, 4)
    # Enforce the ratified input domain, including parity, before permutation.
    quadray_image(q)
    result = [0] * 4
    for old, new in enumerate(sigma):
        result[new] = q[old]
    return tuple(result)


def permute_port(value, permutation):
    sigma = basis_permutation(permutation)
    i, j = integer_vector(value, 2)
    if i not in range(4) or j not in range(4) or i == j:
        raise ValueError('INVALID_PORT')
    return sigma[i], sigma[j]
