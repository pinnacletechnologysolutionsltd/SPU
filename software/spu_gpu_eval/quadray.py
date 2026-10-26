"""Exact Quadray geometry and the explicit T1d screen projection boundary."""

from __future__ import annotations

from fractions import Fraction
from itertools import permutations

from .scene import HEIGHT, WIDTH, Scene, Triangle, Vertex


Point4 = tuple[Fraction, Fraction, Fraction, Fraction]
Point3 = tuple[Fraction, Fraction, Fraction]
TETRA_BASIS: tuple[Point3, ...] = (
    (Fraction(1), Fraction(1), Fraction(1)),
    (Fraction(1), Fraction(-1), Fraction(-1)),
    (Fraction(-1), Fraction(1), Fraction(-1)),
    (Fraction(-1), Fraction(-1), Fraction(1)),
)
DEMO_POINTS: tuple[Point4, ...] = tuple(
    tuple(Fraction(int(i == j)) for i in range(4)) for j in range(4)
)
DEMO_FACES = ((0, 1, 2), (0, 3, 2))
VIEW_MATRIX = (
    (Fraction(1, 9), Fraction(8, 9), Fraction(4, 9)),
    (Fraction(8, 9), Fraction(1, 9), Fraction(-4, 9)),
    (Fraction(-4, 9), Fraction(4, 9), Fraction(-7, 9)),
)
ALL_PERMUTATIONS = tuple(permutations(range(4)))


def point4(values) -> Point4:
    if len(values) != 4:
        raise ValueError("a Quadray point has four components")
    return tuple(Fraction(value) for value in values)


def zero_sum(q: Point4) -> Point4:
    mean = sum(q, Fraction(0)) / 4
    return tuple(value - mean for value in q)


def quadray_to_cartesian(q: Point4) -> Point3:
    a, b, c, d = zero_sum(q)
    return (a + b - c - d, a - b + c - d, a - b - c + d)


def quadrance(q: Point4) -> Fraction:
    return sum(((q[i] - q[j]) ** 2 for i in range(4) for j in range(i + 1, 4)),
               Fraction(0))


def distance_squared(p: Point4, q: Point4) -> Fraction:
    return quadrance(tuple(a - b for a, b in zip(p, q)))


def active_permutation(q: Point4, permutation: tuple[int, int, int, int]) -> Point4:
    if sorted(permutation) != [0, 1, 2, 3]:
        raise ValueError("component map must be a permutation of 0..3")
    result = [Fraction(0)] * 4
    for source, target in enumerate(permutation):
        result[target] = q[source]
    return tuple(result)


def permutation_sign(permutation: tuple[int, int, int, int]) -> int:
    inversions = sum(permutation[i] > permutation[j]
                     for i in range(4) for j in range(i + 1, 4))
    return -1 if inversions & 1 else 1


def determinant3(matrix: tuple[Point3, Point3, Point3]) -> Fraction:
    a, b, c = matrix
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0]))


def spatial_determinant_sign(permutation: tuple[int, int, int, int]) -> int:
    images = [quadray_to_cartesian(active_permutation(point4(tuple(int(i == j) for i in range(4))), permutation))
              for j in range(3)]
    original = [TETRA_BASIS[j] for j in range(3)]
    ratio = determinant3(tuple(images)) / determinant3(tuple(original))
    if ratio not in (Fraction(-1), Fraction(1)):
        raise AssertionError(f"component permutation did not induce an isometry: det={ratio}")
    return int(ratio)


def matrix_apply(matrix, point):
    return tuple(sum((coefficient * value for coefficient, value in zip(row, point)),
                     Fraction(0)) for row in matrix)


def round_fraction_even(value: Fraction) -> int:
    quotient, remainder = divmod(value.numerator, value.denominator)
    twice = 2 * remainder
    if twice < value.denominator:
        return quotient
    if twice > value.denominator:
        return quotient + 1
    return quotient if quotient % 2 == 0 else quotient + 1


def project_to_t1d(q: Point4, *, scale: int = 80, depth_scale: int = 1000) -> Vertex:
    """Orthographic exact conversion; quantization is ties-to-even at pixel edge."""
    xyz = quadray_to_cartesian(q)
    u, v, depth = matrix_apply(VIEW_MATRIX, xyz)
    sx = Fraction(WIDTH - 1, 2) + scale * u
    sy = Fraction(HEIGHT - 1, 2) - scale * v
    sz = 32768 + depth_scale * depth
    x, y, z = round_fraction_even(sx), round_fraction_even(sy), round_fraction_even(sz)
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT and 0 <= z <= 65535):
        raise ValueError(f"projected Quadray point outside T1d range: {(x, y, z)}")
    return Vertex(x, y, z)


def make_demo_scene() -> Scene:
    return make_permuted_demo_scene((0, 1, 2, 3))


def make_permuted_demo_scene(permutation: tuple[int, int, int, int]) -> Scene:
    """Build the frozen two-face tetrahedron view after an exact S4 map."""
    projected = tuple(
        project_to_t1d(active_permutation(point, permutation))
        for point in DEMO_POINTS
    )
    colors = ((15, 2, 1), (1, 8, 15))
    triangles = tuple(
        Triangle(tuple(projected[i] for i in face), color)
        for face, color in zip(DEMO_FACES, colors)
    )
    return Scene(triangles)
