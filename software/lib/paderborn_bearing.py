"""Deterministic current-only features for the Paderborn bearing corpus.

The source MAT files contain calibrated binary64 phase-current samples.  This
module crosses that boundary once, by exact rational round-to-nearest-even into
integer microamps.  Every subsequent feature operation is integer-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from lib.matlab_v5 import MatlabV5Error, NumericArray, load_matlab_v5


CURRENT_NAMES = ("phase_current_1", "phase_current_2")
SOURCE_SAMPLE_HZ = 64_000
NATIVE_WINDOW_SAMPLES = 4_096
ENVELOPE_BLOCK_SAMPLES = 640
ENVELOPE_WINDOW_SAMPLES = 32
FEATURE_NAMES = (
    "mean_abs_current_uA",
    "peak_to_peak_uA",
    "mean_abs_delta_uA",
    "mean_abs_deviation_uA",
)
PROFILES = ("native64k", "envelope100")
NORMALIZED_LIMIT = 30_000


class PaderbornDataError(ValueError):
    """Raised when a recording violates the pinned import contract."""


@dataclass(frozen=True)
class CurrentRecording:
    source: str
    phase_1_uA: tuple[int, ...]
    phase_2_uA: tuple[int, ...]


@dataclass(frozen=True)
class FeatureScaler:
    minima: tuple[int, ...]
    maxima: tuple[int, ...]
    limit: int = NORMALIZED_LIMIT

    def transform(self, features: Sequence[int]) -> tuple[tuple[int, ...], int]:
        if len(features) != len(FEATURE_NAMES):
            raise PaderbornDataError("feature vector has the wrong width")
        output: list[int] = []
        clipped = 0
        for value, low, high in zip(features, self.minima, self.maxima):
            if high <= low:
                raise PaderbornDataError("feature scaler has an empty range")
            if value < low:
                value = low
                clipped += 1
            elif value > high:
                value = high
                clipped += 1
            output.append(round_ratio_half_even((value - low) * self.limit, high - low))
        return tuple(output), clipped


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


def binary64_to_microamps(value: float) -> int:
    """Convert a calibrated ampere sample to microamps without float arithmetic."""
    numerator, denominator = value.as_integer_ratio()
    return round_ratio_half_even(numerator * 1_000_000, denominator)


def _root_record(path: Path) -> dict:
    variables = load_matlab_v5(path)
    if len(variables) != 1:
        raise PaderbornDataError(f"{path.name}: expected exactly one root variable")
    root = next(iter(variables.values()))
    if not isinstance(root, dict) or not isinstance(root.get("Y"), list):
        raise PaderbornDataError(f"{path.name}: missing Paderborn Y signal table")
    return root


def load_current_recording(path: str | Path) -> CurrentRecording:
    """Load the two named phase currents and quantize them to integer microamps."""
    path = Path(path)
    try:
        root = _root_record(path)
    except MatlabV5Error as exc:
        raise PaderbornDataError(f"{path.name}: {exc}") from exc
    signals = {}
    for signal in root["Y"]:
        if not isinstance(signal, dict):
            continue
        name = signal.get("Name")
        if name not in CURRENT_NAMES:
            continue
        if signal.get("Raster") != "HostService":
            raise PaderbornDataError(f"{path.name}: {name} has an unexpected raster")
        data = signal.get("Data")
        if not isinstance(data, NumericArray):
            raise PaderbornDataError(f"{path.name}: {name} is not numeric")
        signals[name] = tuple(binary64_to_microamps(value) for value in data.values)
    if set(signals) != set(CURRENT_NAMES):
        raise PaderbornDataError(f"{path.name}: phase-current channels are missing")
    first, second = (signals[name] for name in CURRENT_NAMES)
    if len(first) != len(second) or len(first) < NATIVE_WINDOW_SAMPLES:
        raise PaderbornDataError(f"{path.name}: phase-current lengths are invalid")
    # Files contain both endpoints of the four-second interval.  Pin the signal
    # to complete seconds so the duplicate/final endpoint never enters a window.
    sample_count = (len(first) // SOURCE_SAMPLE_HZ) * SOURCE_SAMPLE_HZ
    return CurrentRecording(path.name, first[:sample_count], second[:sample_count])


def _three_phases(
    phase_1: Sequence[int], phase_2: Sequence[int]
) -> tuple[Sequence[int], Sequence[int], tuple[int, ...]]:
    return phase_1, phase_2, tuple(-(a + b) for a, b in zip(phase_1, phase_2))


def _phase_features(phase_1: Sequence[int], phase_2: Sequence[int]) -> tuple[int, ...]:
    phases = _three_phases(phase_1, phase_2)
    count = len(phase_1)
    lanes = count * 3
    mean_abs = round_ratio_half_even(sum(abs(v) for phase in phases for v in phase), lanes)
    peak_to_peak = round_ratio_half_even(
        sum(max(phase) - min(phase) for phase in phases), 3
    )
    mean_abs_delta = round_ratio_half_even(
        sum(
            abs(right - left)
            for phase in phases
            for left, right in zip(phase, phase[1:])
        ),
        3 * (count - 1),
    )
    # Preserve each phase's exact mean as total/count; do not round it first.
    deviation_numerator = 0
    for phase in phases:
        total = sum(phase)
        deviation_numerator += sum(abs(count * value - total) for value in phase)
    mean_abs_deviation = round_ratio_half_even(deviation_numerator, 3 * count * count)
    return mean_abs, peak_to_peak, mean_abs_delta, mean_abs_deviation


def native_features(recording: CurrentRecording) -> tuple[tuple[int, ...], ...]:
    """Produce non-overlapping 64 kHz three-phase feature windows."""
    result = []
    for start in range(0, len(recording.phase_1_uA) - NATIVE_WINDOW_SAMPLES + 1,
                       NATIVE_WINDOW_SAMPLES):
        end = start + NATIVE_WINDOW_SAMPLES
        result.append(_phase_features(
            recording.phase_1_uA[start:end], recording.phase_2_uA[start:end]
        ))
    return tuple(result)


def envelope100_features(recording: CurrentRecording) -> tuple[tuple[int, ...], ...]:
    """Produce 100 Hz current-envelope windows using exact 640-sample blocks."""
    phases = _three_phases(recording.phase_1_uA, recording.phase_2_uA)
    envelope = []
    for start in range(0, len(recording.phase_1_uA) - ENVELOPE_BLOCK_SAMPLES + 1,
                       ENVELOPE_BLOCK_SAMPLES):
        end = start + ENVELOPE_BLOCK_SAMPLES
        envelope.append(round_ratio_half_even(
            sum(abs(phase[index]) for phase in phases for index in range(start, end)),
            3 * ENVELOPE_BLOCK_SAMPLES,
        ))
    result = []
    for start in range(0, len(envelope) - ENVELOPE_WINDOW_SAMPLES + 1,
                       ENVELOPE_WINDOW_SAMPLES):
        window = envelope[start:start + ENVELOPE_WINDOW_SAMPLES]
        total = sum(window)
        count = len(window)
        result.append((
            round_ratio_half_even(total, count),
            max(window) - min(window),
            round_ratio_half_even(
                sum(abs(right - left) for left, right in zip(window, window[1:])),
                count - 1,
            ),
            round_ratio_half_even(
                sum(abs(count * value - total) for value in window), count * count
            ),
        ))
    return tuple(result)


def extract_features(
    recording: CurrentRecording, profile: str
) -> tuple[tuple[int, ...], ...]:
    if profile == "native64k":
        return native_features(recording)
    if profile == "envelope100":
        return envelope100_features(recording)
    raise PaderbornDataError(f"unknown feature profile {profile!r}")


def fit_scaler(rows: Iterable[Sequence[int]]) -> FeatureScaler:
    rows = tuple(tuple(row) for row in rows)
    if not rows or any(len(row) != len(FEATURE_NAMES) for row in rows):
        raise PaderbornDataError("cannot fit scaler to empty or malformed rows")
    minima = tuple(min(row[index] for row in rows) for index in range(len(FEATURE_NAMES)))
    maxima = tuple(max(row[index] for row in rows) for index in range(len(FEATURE_NAMES)))
    if any(high <= low for low, high in zip(minima, maxima)):
        raise PaderbornDataError("training rows contain a constant feature")
    return FeatureScaler(minima, maxima)
