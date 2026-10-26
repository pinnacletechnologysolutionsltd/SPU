"""Exact Fibonacci braid arithmetic in the fifth cyclotomic ring.

This module is the characteristic-zero oracle for the proposed cyclotomic
tranche.  It deliberately starts with the integral (non-orthonormal) gauge

    F = [[phi^-1, 1], [phi^-1, -phi^-1]]

whose entries and the Fibonacci R phases all lie in Z[zeta_5].  The ordinary
Euclidean inner product is not valid in this gauge; the preserved metric is
diag(1, phi).  Keeping that distinction explicit prevents an integral basis
change from being mistaken for non-unitary physics.

The modular image is a separate type.  Mapping characteristic-zero results
into F_p[x]/Phi_5(x) is a ring homomorphism, not an assertion that modular
residues are unbounded complex amplitudes.  For prime p != 5, Phi_5 is
irreducible exactly when p == 2 or 3 (mod 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Sequence


M31 = (1 << 31) - 1
OBJECT_ONE = "1"
OBJECT_TAU = "tau"
OBJECTS = (OBJECT_ONE, OBJECT_TAU)


class CyclotomicDomain(Enum):
    """Runtime-visible algebraic domain; cross-domain arithmetic is rejected."""

    CHARACTERISTIC_ZERO_RING = "Z[zeta_5]"
    MODULAR_FIELD = "F_p[x]/Phi_5 (irreducible degree-4 field)"
    MODULAR_QUOTIENT_RING = "F_p[x]/Phi_5 (reducible quotient ring)"


def _phi5_reduce(coefficients: Sequence[int]) -> tuple[int, int, int, int]:
    """Reduce an integer polynomial modulo x^4+x^3+x^2+x+1."""

    work = list(coefficients)
    if len(work) < 4:
        work.extend([0] * (4 - len(work)))
    for degree in range(len(work) - 1, 3, -1):
        coefficient = work[degree]
        if coefficient == 0:
            continue
        work[degree] = 0
        # x^degree = -(x^(degree-1)+...+x^(degree-4)).
        for offset in range(1, 5):
            work[degree - offset] -= coefficient
    return tuple(work[:4])


def _phi5_mul_coefficients(
    left: Sequence[int], right: Sequence[int]
) -> tuple[int, int, int, int]:
    convolution = [0] * 7
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            convolution[i + j] += a * b
    return _phi5_reduce(convolution)


@dataclass(frozen=True)
class Zeta5:
    """An algebraic integer c0+c1*zeta+...+c3*zeta^3 in Z[zeta_5]."""

    coefficients: tuple[int, int, int, int]

    def __init__(self, c0: int = 0, c1: int = 0, c2: int = 0, c3: int = 0):
        object.__setattr__(
            self,
            "coefficients",
            (int(c0), int(c1), int(c2), int(c3)),
        )

    @staticmethod
    def coerce(value: int | "Zeta5") -> "Zeta5":
        if isinstance(value, Zeta5):
            return value
        if isinstance(value, int):
            return Zeta5(value)
        return NotImplemented

    def __add__(self, other: int | "Zeta5") -> "Zeta5":
        other = self.coerce(other)
        if other is NotImplemented:
            return NotImplemented
        return Zeta5(*(a + b for a, b in zip(self.coefficients, other.coefficients)))

    __radd__ = __add__

    def __neg__(self) -> "Zeta5":
        return Zeta5(*(-value for value in self.coefficients))

    def __sub__(self, other: int | "Zeta5") -> "Zeta5":
        other = self.coerce(other)
        if other is NotImplemented:
            return NotImplemented
        return self + (-other)

    def __rsub__(self, other: int | "Zeta5") -> "Zeta5":
        other = self.coerce(other)
        if other is NotImplemented:
            return NotImplemented
        return other - self

    def __mul__(self, other: int | "Zeta5") -> "Zeta5":
        other = self.coerce(other)
        if other is NotImplemented:
            return NotImplemented
        return Zeta5(*_phi5_mul_coefficients(self.coefficients, other.coefficients))

    __rmul__ = __mul__

    def __pow__(self, exponent: int) -> "Zeta5":
        if exponent < 0:
            raise ValueError("negative powers require an explicitly proven unit inverse")
        result = ZETA5_ONE
        base = self
        while exponent:
            if exponent & 1:
                result = result * base
            base = base * base
            exponent >>= 1
        return result

    @property
    def domain(self) -> CyclotomicDomain:
        return CyclotomicDomain.CHARACTERISTIC_ZERO_RING

    def multiply_by_zeta(self) -> "Zeta5":
        """Dedicated root multiply: shift plus broadcast-subtract.

        In the canonical four-lane basis,

            (a0,a1,a2,a3)*zeta = (-a3,a0-a3,a1-a3,a2-a3).

        This is the operation whose hardware cost differs materially from a
        general rank-4 convolution.
        """

        a0, a1, a2, a3 = self.coefficients
        return Zeta5(-a3, a0 - a3, a1 - a3, a2 - a3)

    def automorphism(self, exponent: int) -> "Zeta5":
        """Apply zeta -> zeta^exponent for exponent in (Z/5Z)^*."""

        exponent %= 5
        if exponent not in (1, 2, 3, 4):
            raise ValueError("a fifth-cyclotomic automorphism exponent must be 1..4")
        image = ZETA5_ZETA ** exponent
        power = ZETA5_ONE
        result = ZETA5_ZERO
        for coefficient in self.coefficients:
            result += coefficient * power
            power *= image
        return result

    def conjugate(self) -> "Zeta5":
        """Complex conjugation: zeta -> zeta^-1 = zeta^4."""

        return self.automorphism(4)

    def trace(self) -> int:
        value = sum((self.automorphism(k) for k in (1, 2, 3, 4)), ZETA5_ZERO)
        return value.as_integer()

    def norm(self) -> int:
        value = ZETA5_ONE
        for exponent in (1, 2, 3, 4):
            value *= self.automorphism(exponent)
        return value.as_integer()

    def as_integer(self) -> int:
        c0, c1, c2, c3 = self.coefficients
        if (c1, c2, c3) != (0, 0, 0):
            raise ValueError(f"cyclotomic element is not rational-integer: {self}")
        return c0

    def max_coefficient_bits(self) -> int:
        return max((abs(value).bit_length() for value in self.coefficients), default=0)

    def reduce_mod(self, modulus: int) -> "Zeta5Mod":
        return Zeta5Mod(self.coefficients, modulus)

    def __repr__(self) -> str:
        return f"Zeta5{self.coefficients}"


ZETA5_ZERO = Zeta5(0)
ZETA5_ONE = Zeta5(1)
ZETA5_ZETA = Zeta5(0, 1)


@dataclass(frozen=True)
class Zeta5Mod:
    """An element of F_p[x]/Phi_5, kept distinct from Z[zeta_5]."""

    coefficients: tuple[int, int, int, int]
    modulus: int

    def __init__(self, coefficients: Sequence[int], modulus: int):
        if modulus <= 1:
            raise ValueError("modulus must be greater than one")
        reduced = _phi5_reduce(tuple(int(value) for value in coefficients))
        object.__setattr__(self, "coefficients", tuple(value % modulus for value in reduced))
        object.__setattr__(self, "modulus", int(modulus))

    def _coerce(self, value: int | "Zeta5Mod") -> "Zeta5Mod":
        if isinstance(value, int):
            return Zeta5Mod((value, 0, 0, 0), self.modulus)
        if isinstance(value, Zeta5Mod) and value.modulus == self.modulus:
            return value
        raise TypeError("modular cyclotomic operands must have the same modulus")

    def __add__(self, other: int | "Zeta5Mod") -> "Zeta5Mod":
        other = self._coerce(other)
        return Zeta5Mod(
            tuple(a + b for a, b in zip(self.coefficients, other.coefficients)),
            self.modulus,
        )

    __radd__ = __add__

    def __neg__(self) -> "Zeta5Mod":
        return Zeta5Mod(tuple(-value for value in self.coefficients), self.modulus)

    def __sub__(self, other: int | "Zeta5Mod") -> "Zeta5Mod":
        return self + (-self._coerce(other))

    def __rsub__(self, other: int | "Zeta5Mod") -> "Zeta5Mod":
        return self._coerce(other) - self

    def __mul__(self, other: int | "Zeta5Mod") -> "Zeta5Mod":
        other = self._coerce(other)
        return Zeta5Mod(
            _phi5_mul_coefficients(self.coefficients, other.coefficients),
            self.modulus,
        )

    __rmul__ = __mul__

    def __pow__(self, exponent: int) -> "Zeta5Mod":
        if exponent < 0:
            raise ValueError("use inverse() for negative modular powers")
        result = Zeta5Mod((1, 0, 0, 0), self.modulus)
        base = self
        while exponent:
            if exponent & 1:
                result = result * base
            base = base * base
            exponent >>= 1
        return result

    @property
    def domain(self) -> CyclotomicDomain:
        if phi5_irreducible_over_prime(self.modulus):
            return CyclotomicDomain.MODULAR_FIELD
        return CyclotomicDomain.MODULAR_QUOTIENT_RING

    def multiply_by_zeta(self) -> "Zeta5Mod":
        a0, a1, a2, a3 = self.coefficients
        return Zeta5Mod((-a3, a0 - a3, a1 - a3, a2 - a3), self.modulus)

    def automorphism(self, exponent: int) -> "Zeta5Mod":
        exponent %= 5
        if exponent not in (1, 2, 3, 4):
            raise ValueError("a fifth-cyclotomic automorphism exponent must be 1..4")
        zeta = Zeta5Mod((0, 1, 0, 0), self.modulus)
        image = zeta ** exponent
        power = Zeta5Mod((1, 0, 0, 0), self.modulus)
        result = Zeta5Mod((0, 0, 0, 0), self.modulus)
        for coefficient in self.coefficients:
            result += coefficient * power
            power *= image
        return result

    def conjugate(self) -> "Zeta5Mod":
        return self.automorphism(4)

    def norm(self) -> int:
        value = Zeta5Mod((1, 0, 0, 0), self.modulus)
        for exponent in (1, 2, 3, 4):
            value *= self.automorphism(exponent)
        return value.as_scalar()

    def as_scalar(self) -> int:
        c0, c1, c2, c3 = self.coefficients
        if (c1, c2, c3) != (0, 0, 0):
            raise ValueError(f"modular cyclotomic element is not scalar: {self}")
        return c0

    def inverse(self) -> "Zeta5Mod":
        if not phi5_irreducible_over_prime(self.modulus):
            raise ValueError("inverse() requires prime p with Phi_5 irreducible")
        if self == Zeta5Mod((0, 0, 0, 0), self.modulus):
            raise ZeroDivisionError("zero has no inverse")
        return self ** (self.modulus**4 - 2)

    def __repr__(self) -> str:
        return f"Zeta5Mod{self.coefficients}@{self.modulus}"


def phi5_irreducible_over_prime(prime: int) -> bool:
    """Return the cyclotomic irreducibility criterion, assuming prime input."""

    return prime != 5 and prime % 5 in (2, 3)


def phi5_roots_mod_prime(prime: int) -> list[int]:
    """Enumerate roots of Phi_5 over a small prime field (diagnostic only)."""

    return [
        value
        for value in range(prime)
        if (value**4 + value**3 + value**2 + value + 1) % prime == 0
    ]


def split_zero_divisor_pair(prime: int, root: int | None = None) -> tuple[Zeta5Mod, Zeta5Mod]:
    """Construct nonzero factors whose product is zero when Phi_5 has a root."""

    if root is None:
        roots = phi5_roots_mod_prime(prime)
        if not roots:
            raise ValueError(f"Phi_5 has no scalar root modulo {prime}")
        root = roots[0]
    if (root**4 + root**3 + root**2 + root + 1) % prime != 0:
        raise ValueError(f"{root} is not a root of Phi_5 modulo {prime}")

    # Synthetic division of x^4+x^3+x^2+x+1 by x-root.  ``high`` stores
    # the quotient from x^3 down to its constant term.
    high = [1]
    for coefficient in (1, 1, 1):
        high.append((coefficient + root * high[-1]) % prime)
    quotient_low = tuple(reversed(high))
    return (
        Zeta5Mod((-root, 1, 0, 0), prime),
        Zeta5Mod(quotient_low, prime),
    )


Matrix = tuple[tuple[object, ...], ...]


def matrix_identity(size: int, one: object) -> Matrix:
    zero = one * 0
    return tuple(
        tuple(one if row == column else zero for column in range(size))
        for row in range(size)
    )


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("incompatible matrix dimensions")
    zero = left[0][0] * 0
    return tuple(
        tuple(
            sum(
                (left[row][index] * right[index][column] for index in range(len(right))),
                zero,
            )
            for column in range(len(right[0]))
        )
        for row in range(len(left))
    )


def matrix_dagger(matrix: Matrix) -> Matrix:
    return tuple(
        tuple(matrix[row][column].conjugate() for row in range(len(matrix)))
        for column in range(len(matrix[0]))
    )


def matrix_inverse_unit_1_or_2(matrix: Matrix) -> Matrix:
    """Invert the one- and two-dimensional integral associators used here."""

    if len(matrix) == 1 and len(matrix[0]) == 1:
        value = matrix[0][0]
        if value == ZETA5_ONE:
            return matrix
        if value == -ZETA5_ONE:
            return ((-ZETA5_ONE,),)
        raise ValueError(f"non-unit scalar associator: {value}")
    if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
        raise ValueError("only 1x1 and 2x2 integral matrices are supported")
    a, b = matrix[0]
    c, d = matrix[1]
    determinant = a * d - b * c
    if determinant == ZETA5_ONE:
        sign = 1
    elif determinant == -ZETA5_ONE:
        sign = -1
    else:
        raise ValueError(f"associator determinant is not +/-1: {determinant}")
    return (
        (sign * d, sign * -b),
        (sign * -c, sign * a),
    )


def matrix_reduce_mod(matrix: Matrix, modulus: int) -> Matrix:
    return tuple(
        tuple(value.reduce_mod(modulus) for value in row)
        for row in matrix
    )


def matrix_max_coefficient_bits(matrix: Matrix) -> int:
    return max(value.max_coefficient_bits() for row in matrix for value in row)


# phi^-1 = zeta+zeta^-1, phi = 1+phi^-1.
PHI_INVERSE = ZETA5_ZETA + (ZETA5_ZETA ** 4)
PHI = ZETA5_ONE + PHI_INVERSE

FIBONACCI_F: Matrix = (
    (PHI_INVERSE, ZETA5_ONE),
    (PHI_INVERSE, -PHI_INVERSE),
)
FIBONACCI_R: Matrix = (
    (ZETA5_ZETA ** 3, ZETA5_ZERO),
    (ZETA5_ZERO, -(ZETA5_ZETA ** 4)),
)
FIBONACCI_METRIC: Matrix = (
    (ZETA5_ONE, ZETA5_ZERO),
    (ZETA5_ZERO, PHI),
)
FIBONACCI_IDENTITY = matrix_identity(2, ZETA5_ONE)
FIBONACCI_R_INVERSE: Matrix = matrix_dagger(FIBONACCI_R)
FIBONACCI_SIGMA1 = FIBONACCI_R
FIBONACCI_SIGMA2 = matrix_multiply(
    matrix_multiply(FIBONACCI_F, FIBONACCI_R), FIBONACCI_F
)
FIBONACCI_SIGMA1_INVERSE = FIBONACCI_R_INVERSE
FIBONACCI_SIGMA2_INVERSE = matrix_multiply(
    matrix_multiply(FIBONACCI_F, FIBONACCI_R_INVERSE), FIBONACCI_F
)


def fusion(left: str, right: str) -> tuple[str, ...]:
    if left not in OBJECTS or right not in OBJECTS:
        raise ValueError(f"unknown Fibonacci object: {left}, {right}")
    if left == OBJECT_ONE:
        return (right,)
    if right == OBJECT_ONE:
        return (left,)
    return (OBJECT_ONE, OBJECT_TAU)


def f_symbol(
    a: str,
    b: str,
    c: str,
    total: str,
    left_channel: str,
    right_channel: str,
) -> Zeta5:
    """Multiplicity-free Fibonacci F symbol in the integral gauge."""

    admissible = (
        left_channel in fusion(a, b)
        and total in fusion(left_channel, c)
        and right_channel in fusion(b, c)
        and total in fusion(a, right_channel)
    )
    if not admissible:
        return ZETA5_ZERO
    if (a, b, c, total) == (
        OBJECT_TAU,
        OBJECT_TAU,
        OBJECT_TAU,
        OBJECT_TAU,
    ):
        index = {OBJECT_ONE: 0, OBJECT_TAU: 1}
        return FIBONACCI_F[index[left_channel]][index[right_channel]]
    return ZETA5_ONE


def r_symbol(a: str, b: str, output: str) -> Zeta5:
    """Multiplicity-free Fibonacci R symbol in the same gauge."""

    if output not in fusion(a, b):
        return ZETA5_ZERO
    if a == OBJECT_ONE or b == OBJECT_ONE:
        return ZETA5_ONE
    if output == OBJECT_ONE:
        return FIBONACCI_R[0][0]
    return FIBONACCI_R[1][1]


def left_basis(a: str, b: str, c: str, total: str) -> tuple[str, ...]:
    return tuple(channel for channel in fusion(a, b) if total in fusion(channel, c))


def right_basis(a: str, b: str, c: str, total: str) -> tuple[str, ...]:
    return tuple(channel for channel in fusion(b, c) if total in fusion(a, channel))


def associator_matrix(a: str, b: str, c: str, total: str) -> Matrix:
    """Map ((a b) c) coefficients to (a (b c)) coefficients."""

    source = left_basis(a, b, c, total)
    destination = right_basis(a, b, c, total)
    return tuple(
        tuple(f_symbol(a, b, c, total, left, right) for left in source)
        for right in destination
    )


def _transition_matrix(
    source: Sequence[object],
    destination: Sequence[object],
    coefficient: Callable[[object, object], Zeta5],
) -> Matrix:
    return tuple(
        tuple(coefficient(src, dst) for src in source)
        for dst in destination
    )


def pentagon_report() -> tuple[int, list[tuple[str, str, str, str, str]]]:
    """Return (admissible sectors checked, failures) for the Pentagon."""

    failures: list[tuple[str, str, str, str, str]] = []
    checked = 0
    for a in OBJECTS:
        for b in OBJECTS:
            for c in OBJECTS:
                for d in OBJECTS:
                    for total in OBJECTS:
                        p0 = tuple(
                            (x, y)
                            for x in fusion(a, b)
                            for y in fusion(x, c)
                            if total in fusion(y, d)
                        )
                        if not p0:
                            continue
                        checked += 1
                        p1 = tuple(
                            (u, y)
                            for u in fusion(b, c)
                            for y in fusion(a, u)
                            if total in fusion(y, d)
                        )
                        p2 = tuple(
                            (u, v)
                            for u in fusion(b, c)
                            for v in fusion(u, d)
                            if total in fusion(a, v)
                        )
                        p3 = tuple(
                            (w, v)
                            for w in fusion(c, d)
                            for v in fusion(b, w)
                            if total in fusion(a, v)
                        )
                        p4 = tuple(
                            (x, w)
                            for x in fusion(a, b)
                            for w in fusion(c, d)
                            if total in fusion(x, w)
                        )
                        if not (len(p0) == len(p1) == len(p2) == len(p3) == len(p4)):
                            failures.append((a, b, c, d, total))
                            continue

                        t01 = _transition_matrix(
                            p0,
                            p1,
                            lambda src, dst: (
                                f_symbol(a, b, c, src[1], src[0], dst[0])
                                if src[1] == dst[1]
                                else ZETA5_ZERO
                            ),
                        )
                        t12 = _transition_matrix(
                            p1,
                            p2,
                            lambda src, dst: (
                                f_symbol(a, src[0], d, total, src[1], dst[1])
                                if src[0] == dst[0]
                                else ZETA5_ZERO
                            ),
                        )
                        t23 = _transition_matrix(
                            p2,
                            p3,
                            lambda src, dst: (
                                f_symbol(b, c, d, src[1], src[0], dst[0])
                                if src[1] == dst[1]
                                else ZETA5_ZERO
                            ),
                        )
                        t04 = _transition_matrix(
                            p0,
                            p4,
                            lambda src, dst: (
                                f_symbol(src[0], c, d, total, src[1], dst[1])
                                if src[0] == dst[0]
                                else ZETA5_ZERO
                            ),
                        )
                        t43 = _transition_matrix(
                            p4,
                            p3,
                            lambda src, dst: (
                                f_symbol(a, b, src[1], total, src[0], dst[1])
                                if src[1] == dst[0]
                                else ZETA5_ZERO
                            ),
                        )
                        long_path = matrix_multiply(t23, matrix_multiply(t12, t01))
                        short_path = matrix_multiply(t43, t04)
                        if long_path != short_path:
                            failures.append((a, b, c, d, total))
    return checked, failures


def pentagon_failures() -> list[tuple[str, str, str, str, str]]:
    """Enumerate the complete Fibonacci Pentagon coherence failures."""

    return pentagon_report()[1]


def _diagonal_label_map(
    source: Sequence[str],
    destination: Sequence[str],
    value: Callable[[str], Zeta5],
) -> Matrix:
    return tuple(
        tuple(value(src) if src == dst else ZETA5_ZERO for src in source)
        for dst in destination
    )


def hexagon_report() -> tuple[int, list[tuple[str, str, str, str, str]]]:
    """Return (identities checked, failures) for both Hexagon paths."""

    failures: list[tuple[str, str, str, str, str]] = []
    checked = 0
    for a in OBJECTS:
        for b in OBJECTS:
            for c in OBJECTS:
                for total in OBJECTS:
                    source = left_basis(a, b, c, total)
                    if not source:
                        continue
                    checked += 2

                    # First hexagon: braid a across b tensor c.
                    a_abc = associator_matrix(a, b, c, total)
                    right_abc = right_basis(a, b, c, total)
                    target_bca = left_basis(b, c, a, total)
                    outer_a_bc = _diagonal_label_map(
                        right_abc,
                        target_bca,
                        lambda channel: r_symbol(a, channel, total),
                    )
                    direct_one = matrix_multiply(outer_a_bc, a_abc)

                    left_bac = left_basis(b, a, c, total)
                    braid_ab = _diagonal_label_map(
                        source,
                        left_bac,
                        lambda channel: r_symbol(a, b, channel),
                    )
                    a_bac = associator_matrix(b, a, c, total)
                    right_bac = right_basis(b, a, c, total)
                    right_bca = right_basis(b, c, a, total)
                    braid_ac_inner = _diagonal_label_map(
                        right_bac,
                        right_bca,
                        lambda channel: r_symbol(a, c, channel),
                    )
                    a_bca_inverse = matrix_inverse_unit_1_or_2(
                        associator_matrix(b, c, a, total)
                    )
                    split_one = matrix_multiply(
                        a_bca_inverse,
                        matrix_multiply(
                            braid_ac_inner,
                            matrix_multiply(a_bac, braid_ab),
                        ),
                    )
                    if direct_one != split_one:
                        failures.append(("left", a, b, c, total))

                    # Second hexagon: braid a tensor b across c.
                    target_cab = right_basis(c, a, b, total)
                    outer_ab_c = _diagonal_label_map(
                        source,
                        target_cab,
                        lambda channel: r_symbol(channel, c, total),
                    )
                    direct_two = outer_ab_c

                    right_acb = right_basis(a, c, b, total)
                    braid_bc_inner = _diagonal_label_map(
                        right_abc,
                        right_acb,
                        lambda channel: r_symbol(b, c, channel),
                    )
                    a_acb_inverse = matrix_inverse_unit_1_or_2(
                        associator_matrix(a, c, b, total)
                    )
                    left_acb = left_basis(a, c, b, total)
                    left_cab = left_basis(c, a, b, total)
                    braid_ac = _diagonal_label_map(
                        left_acb,
                        left_cab,
                        lambda channel: r_symbol(a, c, channel),
                    )
                    a_cab = associator_matrix(c, a, b, total)
                    split_two = matrix_multiply(
                        a_cab,
                        matrix_multiply(
                            braid_ac,
                            matrix_multiply(
                                a_acb_inverse,
                                matrix_multiply(braid_bc_inner, a_abc),
                            ),
                        ),
                    )
                    if direct_two != split_two:
                        failures.append(("right", a, b, c, total))
    return checked, failures


def hexagon_failures() -> list[tuple[str, str, str, str, str]]:
    """Enumerate both braided Fibonacci Hexagon coherence failures."""

    return hexagon_report()[1]


def braid_generator(index: int) -> Matrix:
    generators = {
        1: FIBONACCI_SIGMA1,
        2: FIBONACCI_SIGMA2,
        -1: FIBONACCI_SIGMA1_INVERSE,
        -2: FIBONACCI_SIGMA2_INVERSE,
    }
    try:
        return generators[index]
    except KeyError as exc:
        raise ValueError(f"unsupported three-anyon braid generator: {index}") from exc


def evaluate_braid_word(word: Iterable[int]) -> Matrix:
    result = FIBONACCI_IDENTITY
    for generator in word:
        result = matrix_multiply(braid_generator(generator), result)
    return result


def evaluate_braid_word_mod(word: Iterable[int], modulus: int) -> Matrix:
    identity = matrix_reduce_mod(FIBONACCI_IDENTITY, modulus)
    generators = {
        index: matrix_reduce_mod(braid_generator(index), modulus)
        for index in (1, 2, -1, -2)
    }
    result = identity
    for generator in word:
        try:
            result = matrix_multiply(generators[generator], result)
        except KeyError as exc:
            raise ValueError(f"unsupported three-anyon braid generator: {generator}") from exc
    return result


STRUCTURED_PATTERNS = {
    "sigma1": (1,),
    "sigma2": (2,),
    "alternating": (1, 2),
    "inverse_alternating": (1, -2),
    "commutator": (1, 2, -1, -2),
}

# Three of the structured patterns generate finite cyclic subgroups -- sigma1
# and sigma2 both have order 10, and their product has order 15 -- so their
# coefficients cannot grow however long the word gets.  Growth evidence has to
# come from the generic stream, and a single sample per length is too thin to
# state a bound from.  Five independent streams per length instead.
GENERIC_STREAMS = 5


def _lcg_word(seed: int, length: int) -> tuple[int, ...]:
    """Fixed LCG: deterministic without depending on Python's PRNG version."""

    state = seed & 0xFFFFFFFF
    choices = (1, 2, -1, -2)
    word = []
    for _ in range(length):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        word.append(choices[(state >> 30) & 3])
    return tuple(word)


def is_generic_label(label: str) -> bool:
    """True for the pseudo-random stream words, false for structured ones."""

    return label.startswith("lcg")


def deterministic_braid_corpus(max_length: int = 100) -> dict[str, tuple[int, ...]]:
    """A reproducible corpus containing periodic, cancelling, and mixed words."""

    if max_length < 1:
        raise ValueError("max_length must be positive")
    lengths = sorted({1, 2, 3, 5, 8, 13, 21, 34, 55, max_length})
    corpus: dict[str, tuple[int, ...]] = {}
    for length in lengths:
        for label, pattern in STRUCTURED_PATTERNS.items():
            corpus[f"{label}_{length}"] = tuple(
                pattern[index % len(pattern)] for index in range(length)
            )
        for stream in range(GENERIC_STREAMS):
            seed = (0x5F3759DF ^ length) + 0x9E3779B9 * stream
            corpus[f"lcg{stream}_{length}"] = _lcg_word(seed, length)
    return corpus


def braid_growth_profile(max_length: int = 100) -> dict[str, int]:
    profile: dict[str, int] = {}
    for label, word in deterministic_braid_corpus(max_length).items():
        profile[label] = matrix_max_coefficient_bits(evaluate_braid_word(word))
    return profile


def signed_storage_bits(value: int) -> int:
    """Minimum two's-complement width that holds ``value``.

    ``Zeta5.max_coefficient_bits`` reports ``abs(v).bit_length()`` -- a
    *magnitude* width that excludes the sign.  Storage needs one more bit,
    except at the exact negative boundary where ``-2**(w-1)`` still fits in
    ``w``.  Computing it rather than adding one keeps the two quantities from
    being conflated in a resource claim.
    """

    width = 1
    while not -(1 << (width - 1)) <= value <= (1 << (width - 1)) - 1:
        width += 1
    return width


def braid_storage_bits_by_class(max_length: int = 100) -> dict[str, int]:
    """Minimum signed storage width per word class over the corpus."""

    worst = {"structured": 1, "generic": 1}
    for label, word in deterministic_braid_corpus(max_length).items():
        key = "generic" if is_generic_label(label) else "structured"
        for row in evaluate_braid_word(word):
            for value in row:
                for coefficient in value.coefficients:
                    width = signed_storage_bits(coefficient)
                    if width > worst[key]:
                        worst[key] = width
    return worst


def braid_growth_by_class(max_length: int = 100) -> dict[str, int]:
    """Report structured-word and generic-word growth separately.

    The structured families include finite-order words whose coefficients
    never grow.  A single maximum over the whole corpus would attribute the
    stated bound to words that cannot contribute to it, so the two classes are
    reported apart.
    """

    profile = braid_growth_profile(max_length)
    generic = [bits for label, bits in profile.items() if is_generic_label(label)]
    structured = [
        bits for label, bits in profile.items() if not is_generic_label(label)
    ]
    return {"generic": max(generic), "structured": max(structured)}


def braid_word_order(word: Sequence[int], cap: int = 64) -> int | None:
    """Order of a repeated braid word, or None if it exceeds ``cap``.

    Recorded so the growth corpus cannot silently become inert: a pattern with
    a finite order contributes no growth evidence at any length.
    """

    matrix = evaluate_braid_word(word)
    power = FIBONACCI_IDENTITY
    for exponent in range(1, cap + 1):
        power = matrix_multiply(matrix, power)
        if power == FIBONACCI_IDENTITY:
            return exponent
    return None


def structured_pattern_orders(cap: int = 64) -> dict[str, int | None]:
    """Order of each structured generating pattern."""

    return {
        label: braid_word_order(pattern, cap)
        for label, pattern in STRUCTURED_PATTERNS.items()
    }
