"""spu4_som_edge_oracle.py — exact oracle for the SPU-4 edge SOM classifier.

hardware/rtl/core/spu4/spu4_som_edge.v implements a DIFFERENT quadrance from
the SPU-13 seven-node hex SOM in rational_som.py. That module's
`weighted_quadrance`/`find_bmu` compute a genuine Q(sqrt(3)) field square
(delta * delta, via RationalSurd.__mul__), producing a surd with both P and Q
components, then order candidates with the full surd relation `rs_lt`.

spu4_som_edge.v does not do that. Per feature it computes the plain integer
quadratic form Q = dp*dp + 3*dq*dq (a scalar, not a surd — see the module's
own header comment), sums that scalar across features, and picks the winner
with a strict `<` scalar comparison, so equal quadrances keep the
earliest-scanned (lowest index) node. Reusing rational_som.py's find_bmu here
would silently check a different mathematical object — this module is the
bit-exact match for what the RTL actually computes, built on the same
RationalSurd representation.
"""
from __future__ import annotations

from typing import Sequence

from .rational_som import RationalSurd


def feature_quadrance_scalar(x: RationalSurd, w: RationalSurd) -> int:
    """dp*dp + 3*dq*dq for a single feature — spu4_som_edge.v's per-feature term."""

    dp = x.p - w.p
    dq = x.q - w.q
    return dp * dp + 3 * dq * dq


def node_quadrance(features: Sequence[RationalSurd], weights: Sequence[RationalSurd]) -> int:
    """Sum of feature_quadrance_scalar across features — one node's total quadrance."""

    if len(features) != len(weights):
        raise ValueError("features and weights must have equal length")
    return sum(feature_quadrance_scalar(x, w) for x, w in zip(features, weights))


def find_bmu_edge(
    features: Sequence[RationalSurd],
    nodes: Sequence[Sequence[RationalSurd]],
) -> tuple[int, int]:
    """Return (best_node, best_quadrance), matching spu4_som_edge.v's scan FSM
    exactly: node 0..N-1 in order, strict `<` beats the running best, so an
    exact tie keeps the lower index (the RTL never revisits an earlier node)."""

    if not nodes:
        raise ValueError("at least one node is required")
    best_node = 0
    best_q = node_quadrance(features, nodes[0])
    for idx in range(1, len(nodes)):
        q = node_quadrance(features, nodes[idx])
        if q < best_q:
            best_node = idx
            best_q = q
    return best_node, best_q
