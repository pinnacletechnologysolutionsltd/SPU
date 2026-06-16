"""
rational_som.py — exact rational/quadrance SOM reference model.

This is the software oracle for the first SPU-13 SOM/multicluster pass:
weighted quadrance BMU selection, stable tie-breaking, confidence-gap
calculation, and Nguyen-style cluster label reduction.

The arithmetic is restricted to Q(sqrt(3)) integer pairs. No float, no sqrt,
and no division are used in the BMU hot path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RationalSurd:
    """Element p + q*sqrt(3), represented as integer coefficients."""

    p: int = 0
    q: int = 0

    def __add__(self, other: "RationalSurd") -> "RationalSurd":
        return RationalSurd(self.p + other.p, self.q + other.q)

    def __sub__(self, other: "RationalSurd") -> "RationalSurd":
        return RationalSurd(self.p - other.p, self.q - other.q)

    def __mul__(self, other: "RationalSurd") -> "RationalSurd":
        return RationalSurd(
            self.p * other.p + 3 * self.q * other.q,
            self.p * other.q + self.q * other.p,
        )

    def square(self) -> "RationalSurd":
        return self * self

    def is_zero(self) -> bool:
        return self.p == 0 and self.q == 0


RS_ZERO = RationalSurd(0, 0)


def rs_lt(lhs: RationalSurd, rhs: RationalSurd) -> bool:
    """Return true when lhs < rhs, using integer-only Q(sqrt(3)) ordering."""

    da = lhs.p - rhs.p
    db = lhs.q - rhs.q
    if da == 0 and db == 0:
        return False
    if da <= 0 and db <= 0:
        return True
    if da >= 0 and db >= 0:
        return False

    da2 = da * da
    db2 = db * db
    if da < 0 and db > 0:
        return da2 > 3 * db2
    return da2 < 3 * db2


def rs_le(lhs: RationalSurd, rhs: RationalSurd) -> bool:
    return lhs == rhs or rs_lt(lhs, rhs)


@dataclass(frozen=True)
class SomNode:
    node_id: int
    axial_q: int
    axial_r: int
    cluster_label: int
    weights: tuple[RationalSurd, ...]
    valid: bool = True


@dataclass(frozen=True)
class BmuResult:
    valid: bool
    best_node_id: int
    second_node_id: int
    cluster_label: int
    best_q: RationalSurd
    second_q: RationalSurd
    confidence_gap: RationalSurd
    has_second: bool

    @property
    def ambiguous(self) -> bool:
        return self.has_second and self.confidence_gap.is_zero()


HEX_AXIAL_DELTAS: tuple[tuple[int, int], ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


def hex_neighbors(axial_q: int, axial_r: int) -> tuple[tuple[int, int], ...]:
    return tuple((axial_q + dq, axial_r + dr) for dq, dr in HEX_AXIAL_DELTAS)


def weighted_quadrance(
    features: Sequence[RationalSurd],
    node_weights: Sequence[RationalSurd],
    feature_weights: Sequence[RationalSurd],
) -> RationalSurd:
    """Compute sum_j r_j * (x_j - w_ij)^2."""

    if len(features) != len(node_weights) or len(features) != len(feature_weights):
        raise ValueError("feature, node, and weight vectors must have equal length")

    total = RS_ZERO
    for x_j, w_ij, r_j in zip(features, node_weights, feature_weights):
        delta = x_j - w_ij
        total = total + r_j * delta.square()
    return total


def _candidate_better(
    cand_q: RationalSurd,
    cand_id: int,
    ref_q: RationalSurd,
    ref_id: int,
    has_ref: bool,
) -> bool:
    if not has_ref:
        return True
    if rs_lt(cand_q, ref_q):
        return True
    return cand_q == ref_q and cand_id < ref_id


def find_bmu(
    features: Sequence[RationalSurd],
    nodes: Iterable[SomNode],
    feature_weights: Sequence[RationalSurd],
) -> BmuResult:
    """Find the best and second-best matching units with stable tie-breaking."""

    have_best = False
    have_second = False
    best_id = -1
    second_id = -1
    best_label = 0
    best_q = RS_ZERO
    second_q = RS_ZERO

    for node in nodes:
        if not node.valid:
            continue
        q_i = weighted_quadrance(features, node.weights, feature_weights)
        if _candidate_better(q_i, node.node_id, best_q, best_id, have_best):
            if have_best:
                second_id = best_id
                second_q = best_q
                have_second = True
            best_id = node.node_id
            best_q = q_i
            best_label = node.cluster_label
            have_best = True
        elif _candidate_better(q_i, node.node_id, second_q, second_id, have_second):
            second_id = node.node_id
            second_q = q_i
            have_second = True

    if not have_best:
        return BmuResult(False, -1, -1, 0, RS_ZERO, RS_ZERO, RS_ZERO, False)

    gap = second_q - best_q if have_second else RS_ZERO
    return BmuResult(
        True,
        best_id,
        second_id,
        best_label,
        best_q,
        second_q,
        gap,
        have_second,
    )


def classify(
    result: BmuResult,
    ambiguity_threshold: RationalSurd = RS_ZERO,
) -> tuple[int, bool]:
    """Return cluster label and ambiguity flag from a BMU result."""

    if not result.valid:
        raise ValueError("cannot classify without a valid BMU")
    ambiguous = result.has_second and rs_le(result.confidence_gap, ambiguity_threshold)
    return result.cluster_label, ambiguous


def rs(p: int, q: int = 0) -> RationalSurd:
    return RationalSurd(p, q)


def tiny_hex_fixture() -> tuple[list[SomNode], list[RationalSurd]]:
    """Seven-node fixture shared by Python and C++ tests."""

    feature_weights = [rs(1), rs(2), rs(1), rs(1)]
    nodes = [
        SomNode(0, 0, 0, 0, (rs(0), rs(0), rs(0), rs(0))),
        SomNode(1, 1, 0, 1, (rs(2), rs(0), rs(0), rs(0))),
        SomNode(2, 1, -1, 1, (rs(0), rs(2), rs(0), rs(0))),
        SomNode(3, 0, -1, 2, (rs(0), rs(0), rs(2), rs(0))),
        SomNode(4, -1, 0, 2, (rs(-2), rs(0), rs(0), rs(0))),
        SomNode(5, -1, 1, 3, (rs(0), rs(-2), rs(0), rs(0))),
        SomNode(6, 0, 1, 3, (rs(0), rs(0), rs(-2), rs(1, 1))),
    ]
    return nodes, feature_weights
