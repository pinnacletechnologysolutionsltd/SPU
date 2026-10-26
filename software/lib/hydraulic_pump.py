"""Exact 100 Hz motor-power features for the UCI hydraulic pump study."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


SAMPLE_HZ = 100
SAMPLES_PER_CYCLE = 6_000
WINDOW_SAMPLES = 32
WINDOWS_PER_CYCLE = 16
NORMALIZED_LIMIT = 30_000
CLASS_VALUES = (0, 1, 2)
CLASS_NAMES = ("no_leakage", "weak_leakage", "severe_leakage")
FEATURE_NAMES = (
    "mean_power_dW",
    "peak_to_peak_power_dW",
    "mean_abs_delta_power_dW",
    "mean_abs_deviation_power_dW",
)
FOLD_COUNT = 5
FOLD_SEED = "hydraulic-pump-v1"


class HydraulicDataError(ValueError):
    """Raised when hydraulic source data violates the frozen contract."""


@dataclass(frozen=True)
class HydraulicProfile:
    cooler: int
    valve: int
    pump: int
    accumulator: int
    stable_flag: int

    @property
    def nuisance_group(self) -> tuple[int, int, int]:
        return self.cooler, self.valve, self.accumulator


@dataclass(frozen=True)
class HydraulicWindow:
    cycle: int
    nuisance_group: tuple[int, int, int]
    window: int
    features: tuple[int, ...]
    label: int


@dataclass(frozen=True)
class FeatureScaler:
    minima: tuple[int, ...]
    maxima: tuple[int, ...]
    limit: int = NORMALIZED_LIMIT

    def project(
        self, features: Sequence[int], *, clamp: bool = True
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        if len(features) != len(self.minima):
            raise HydraulicDataError("feature vector has the wrong width")
        output: list[int] = []
        direction: list[int] = []
        for value, low, high in zip(features, self.minima, self.maxima):
            if high <= low:
                raise HydraulicDataError("feature scaler has an empty range")
            if value < low:
                direction.append(-1)
                source = low if clamp else value
            elif value > high:
                direction.append(1)
                source = high if clamp else value
            else:
                direction.append(0)
                source = value
            output.append(round_ratio_half_even(
                (source - low) * self.limit, high - low
            ))
        return tuple(output), tuple(direction)


def round_ratio_half_even(numerator: int, denominator: int) -> int:
    """Round an integer ratio to nearest, resolving exact ties to even."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient & 1):
        quotient += 1
    return sign * quotient


def parse_deciwatts(token: str) -> int:
    """Parse the source's integer/one-decimal watt tokens exactly."""
    value = token.strip()
    if not value:
        raise HydraulicDataError("empty EPS1 power token")
    sign = -1 if value.startswith("-") else 1
    value = value.lstrip("+-")
    whole, dot, fractional = value.partition(".")
    if not whole or not whole.isdigit() or value.count(".") > 1:
        raise HydraulicDataError(f"invalid EPS1 power token {token!r}")
    if dot and (not fractional or not fractional.isdigit()):
        raise HydraulicDataError(f"invalid EPS1 power token {token!r}")
    if len(fractional) > 1 and any(char != "0" for char in fractional[1:]):
        raise HydraulicDataError(
            f"EPS1 power token is not exactly representable in deciwatts: {token!r}"
        )
    tenth = int(fractional[:1] or "0")
    return sign * (int(whole) * 10 + tenth)


def parse_profile_line(line: str, cycle: int) -> HydraulicProfile:
    try:
        values = tuple(map(int, line.split()))
    except ValueError as exc:
        raise HydraulicDataError(f"cycle {cycle}: invalid profile row") from exc
    if len(values) != 5:
        raise HydraulicDataError(f"cycle {cycle}: profile row must have five values")
    profile = HydraulicProfile(*values)
    if profile.pump not in CLASS_VALUES:
        raise HydraulicDataError(f"cycle {cycle}: unknown pump label {profile.pump}")
    if profile.stable_flag not in (0, 1):
        raise HydraulicDataError(f"cycle {cycle}: invalid stable flag")
    return profile


def parse_power_line(line: str, cycle: int) -> tuple[int, ...]:
    tokens = line.split()
    if len(tokens) != SAMPLES_PER_CYCLE:
        raise HydraulicDataError(
            f"cycle {cycle}: EPS1 row has {len(tokens)} samples, "
            f"expected {SAMPLES_PER_CYCLE}"
        )
    return tuple(parse_deciwatts(token) for token in tokens)


def fixed_window_starts() -> tuple[int, ...]:
    span = SAMPLES_PER_CYCLE - WINDOW_SAMPLES
    return tuple(
        index * span // (WINDOWS_PER_CYCLE - 1)
        for index in range(WINDOWS_PER_CYCLE)
    )


def extract_power_features(samples_dW: Sequence[int]) -> tuple[int, ...]:
    if len(samples_dW) != WINDOW_SAMPLES:
        raise HydraulicDataError(
            f"power window must contain {WINDOW_SAMPLES} samples"
        )
    if any(not isinstance(value, int) for value in samples_dW):
        raise HydraulicDataError("power samples must be integers")
    count = len(samples_dW)
    total = sum(samples_dW)
    return (
        round_ratio_half_even(total, count),
        max(samples_dW) - min(samples_dW),
        round_ratio_half_even(
            sum(abs(right - left) for left, right in zip(samples_dW, samples_dW[1:])),
            count - 1,
        ),
        round_ratio_half_even(
            sum(abs(count * value - total) for value in samples_dW),
            count * count,
        ),
    )


def cycle_windows(
    cycle: int, profile: HydraulicProfile, samples_dW: Sequence[int]
) -> tuple[HydraulicWindow, ...]:
    if len(samples_dW) != SAMPLES_PER_CYCLE:
        raise HydraulicDataError(f"cycle {cycle}: wrong EPS1 sample count")
    return tuple(
        HydraulicWindow(
            cycle=cycle,
            nuisance_group=profile.nuisance_group,
            window=window,
            features=extract_power_features(samples_dW[start:start + WINDOW_SAMPLES]),
            label=profile.pump,
        )
        for window, start in enumerate(fixed_window_starts())
    )


def iter_stable_windows(
    eps1_path: str | Path, profile_path: str | Path
) -> Iterator[HydraulicWindow]:
    """Stream exact features without retaining the 87 MB source matrix."""
    eps1_path = Path(eps1_path)
    profile_path = Path(profile_path)
    with eps1_path.open("r", encoding="ascii") as eps_source, profile_path.open(
        "r", encoding="ascii"
    ) as profile_source:
        cycle = 0
        while True:
            eps_line = eps_source.readline()
            profile_line = profile_source.readline()
            if not eps_line and not profile_line:
                break
            if not eps_line or not profile_line:
                raise HydraulicDataError("EPS1/profile row counts differ")
            profile = parse_profile_line(profile_line, cycle)
            if profile.stable_flag == 0:
                samples = parse_power_line(eps_line, cycle)
                yield from cycle_windows(cycle, profile, samples)
            cycle += 1
    if cycle != 2_205:
        raise HydraulicDataError(f"source has {cycle} cycles, expected 2205")


def group_digest(group: tuple[int, int, int]) -> bytes:
    cooler, valve, accumulator = group
    return hashlib.sha256(
        f"{FOLD_SEED}:{cooler}:{valve}:{accumulator}".encode("ascii")
    ).digest()


def assign_group_folds(
    groups: Iterable[tuple[int, int, int]], fold_count: int = FOLD_COUNT
) -> dict[tuple[int, int, int], int]:
    unique = sorted(set(groups), key=lambda group: (group_digest(group), group))
    if len(unique) < fold_count:
        raise HydraulicDataError("not enough nuisance groups for the fold contract")
    return {group: index % fold_count for index, group in enumerate(unique)}


def fit_scaler(features: Iterable[Sequence[int]]) -> FeatureScaler:
    rows = tuple(tuple(row) for row in features)
    if not rows or any(len(row) != len(FEATURE_NAMES) for row in rows):
        raise HydraulicDataError("scaler requires nonempty four-feature rows")
    minima = tuple(min(row[index] for row in rows) for index in range(len(FEATURE_NAMES)))
    maxima = tuple(max(row[index] for row in rows) for index in range(len(FEATURE_NAMES)))
    if any(high <= low for low, high in zip(minima, maxima)):
        raise HydraulicDataError("training feature has no range")
    return FeatureScaler(minima, maxima)
