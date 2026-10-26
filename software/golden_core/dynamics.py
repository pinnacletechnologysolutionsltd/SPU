"""Bounded exact trajectories and canonical measurements for Golden Core."""

import hashlib
import json
from fractions import Fraction

from .exact import Q5, ZERO
from .oriented_edge_turns import OrientedEdgeTurns


def trajectory(initial: tuple[Q5, ...], turns: OrientedEdgeTurns,
               left_weight: Q5, right_weight: Q5, steps: int) -> tuple[tuple[Q5, ...], ...]:
    """Return states x_0 through x_steps under the exact weighted turn law."""
    if steps < 0:
        raise ValueError("step count must be nonnegative")
    if len(initial) != len(turns.directed_edges):
        raise ValueError("initial state must match the directed-edge domain")
    states = [tuple(initial)]
    for _ in range(steps):
        states.append(turns.weighted(states[-1], left_weight, right_weight))
    return tuple(states)


def state_sum(state: tuple[Q5, ...]) -> Q5:
    return sum(state, ZERO)


def coefficient_max_bit_length(state: tuple[Q5, ...]) -> int:
    """Maximum numerator/denominator bit length in canonical Q(sqrt(5)) pairs."""
    return max((abs(value).bit_length()
                for item in state
                for coefficient in (item.a, item.b)
                for value in (coefficient.numerator, coefficient.denominator)),
               default=0)


def turn_channel_imbalance(state: tuple[Q5, ...], seed_edge_index: int,
                           turns: OrientedEdgeTurns) -> Q5:
    """Signed amplitude difference at the seed's left and right output edges."""
    left_channel = turns.left_image[seed_edge_index]
    right_channel = turns.right_image[seed_edge_index]
    return state[left_channel] - state[right_channel]


def canonical_state(state: tuple[Q5, ...]) -> list[list[int]]:
    """Encode each Q(sqrt(5)) coefficient as [a_num,a_den,b_num,b_den]."""
    def rational(value: Fraction) -> tuple[int, int]:
        return value.numerator, value.denominator
    return [[*rational(value.a), *rational(value.b)] for value in state]


def state_sha256(state: tuple[Q5, ...]) -> str:
    encoded = json.dumps(canonical_state(state), separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()
