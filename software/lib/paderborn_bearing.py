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
PERIODIC_WINDOW_SAMPLES = 12_800
CARRIER_HALF_PERIOD = 320
CARRIER_PERIOD = 640
SHAFT_PERIOD = 2_560
TIME_FEATURE_NAMES = (
    "mean_abs_current_uA",
    "peak_to_peak_uA",
    "mean_abs_delta_uA",
    "mean_abs_deviation_uA",
)
PERIODIC_FEATURE_NAMES = (
    "carrier_half_cycle_antiresidual_ppm",
    "carrier_cycle_residual_ppm",
    "shaft_cycle_residual_ppm",
    "carrier_envelope_deviation_ppm",
)
PROFILE_FEATURE_NAMES = {
    "native64k": TIME_FEATURE_NAMES,
    "envelope100": TIME_FEATURE_NAMES,
    "periodic64k": PERIODIC_FEATURE_NAMES,
}
FEATURE_NAMES = TIME_FEATURE_NAMES
PROFILES = tuple(PROFILE_FEATURE_NAMES)
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

    def project(
        self, features: Sequence[int], *, clamp: bool = True
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        """Apply the training affine map and return per-lane range direction.

        Direction is -1 below the training minimum, +1 above its maximum, and
        zero in range.  With ``clamp=False`` the affine result is intentionally
        allowed outside 0..limit for software-only domain-shift diagnosis.
        """
        if len(features) != len(self.minima):
            raise PaderbornDataError("feature vector has the wrong width")
        output: list[int] = []
        direction: list[int] = []
        for value, low, high in zip(features, self.minima, self.maxima):
            if high <= low:
                raise PaderbornDataError("feature scaler has an empty range")
            if value < low:
                direction.append(-1)
                projected = low if clamp else value
            elif value > high:
                direction.append(1)
                projected = high if clamp else value
            else:
                direction.append(0)
                projected = value
            output.append(round_ratio_half_even(
                (projected - low) * self.limit, high - low
            ))
        return tuple(output), tuple(direction)

    def transform(self, features: Sequence[int]) -> tuple[tuple[int, ...], int]:
        output, direction = self.project(features)
        return output, sum(item != 0 for item in direction)


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


def _lag_residual_ppm(phases: Sequence[Sequence[int]], lag: int, anti: bool) -> int:
    count = len(phases[0])
    amplitude = sum(abs(value) for phase in phases for value in phase)
    if amplitude == 0:
        raise PaderbornDataError("periodic feature window has zero current")
    if anti:
        residual = sum(
            abs(phase[index] + phase[index - lag])
            for phase in phases for index in range(lag, count)
        )
    else:
        residual = sum(
            abs(phase[index] - phase[index - lag])
            for phase in phases for index in range(lag, count)
        )
    # Both residual and amplitude have three equal phase lanes.  Their mean
    # ratio therefore reduces to this exact integer expression.
    return round_ratio_half_even(
        residual * count * 1_000_000, amplitude * (count - lag)
    )


def periodic_features(recording: CurrentRecording) -> tuple[tuple[int, ...], ...]:
    """Extract exact 100 Hz carrier/25 Hz shaft residuals as integer ppm."""
    result = []
    for start in range(0, len(recording.phase_1_uA) - PERIODIC_WINDOW_SAMPLES + 1,
                       PERIODIC_WINDOW_SAMPLES):
        end = start + PERIODIC_WINDOW_SAMPLES
        phases = _three_phases(
            recording.phase_1_uA[start:end], recording.phase_2_uA[start:end]
        )
        cycle_sums = []
        for cycle_start in range(0, PERIODIC_WINDOW_SAMPLES, CARRIER_PERIOD):
            cycle_end = cycle_start + CARRIER_PERIOD
            cycle_sums.append(sum(
                abs(phase[index])
                for phase in phases for index in range(cycle_start, cycle_end)
            ))
        cycle_total = sum(cycle_sums)
        cycle_count = len(cycle_sums)
        if cycle_total == 0:
            raise PaderbornDataError("periodic feature window has zero envelope")
        envelope_deviation = round_ratio_half_even(
            sum(abs(cycle_count * value - cycle_total) for value in cycle_sums)
            * 1_000_000,
            cycle_count * cycle_total,
        )
        result.append((
            _lag_residual_ppm(phases, CARRIER_HALF_PERIOD, True),
            _lag_residual_ppm(phases, CARRIER_PERIOD, False),
            _lag_residual_ppm(phases, SHAFT_PERIOD, False),
            envelope_deviation,
        ))
    return tuple(result)


def extract_features(
    recording: CurrentRecording, profile: str
) -> tuple[tuple[int, ...], ...]:
    if profile == "native64k":
        return native_features(recording)
    if profile == "envelope100":
        return envelope100_features(recording)
    if profile == "periodic64k":
        return periodic_features(recording)
    raise PaderbornDataError(f"unknown feature profile {profile!r}")


def fit_scaler(rows: Iterable[Sequence[int]]) -> FeatureScaler:
    rows = tuple(tuple(row) for row in rows)
    if not rows or any(len(row) != len(rows[0]) for row in rows) or len(rows[0]) != 4:
        raise PaderbornDataError("cannot fit scaler to empty or malformed rows")
    minima = tuple(min(row[index] for row in rows) for index in range(len(rows[0])))
    maxima = tuple(max(row[index] for row in rows) for index in range(len(rows[0])))
    if any(high <= low for low, high in zip(minima, maxima)):
        raise PaderbornDataError("training rows contain a constant feature")
    return FeatureScaler(minima, maxima)
