"""Deterministic synthetic current-signature pipeline for SOM1 replay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from lib.cartesian_bridge import (
    quantize_feature_vector,
    widen_sensor_scalar_to_som18,
)
from lib.rational_som import BmuResult, RationalSurd, SomNode, find_bmu
from spu_host.som1 import SOM1Result, encode_som1_frame, parse_som1_frame


WINDOW_SAMPLES = 32
SAMPLE_HZ = 100
TRAIN_CASES_PER_CLASS = 12
REPLAY_CASES_PER_CLASS = 6
FEATURE_NAMES = (
    "mean_current_mA",
    "peak_to_peak_mA",
    "mean_abs_delta_mA",
    "mean_abs_deviation_mA",
)
CLASS_NAMES = ("bearing_drag", "normal", "stall")


@dataclass(frozen=True)
class ReplayEvidence:
    true_label: int
    features: tuple[int, ...]
    oracle: BmuResult
    frame: bytes
    parsed: SOM1Result


def round_ratio_half_even(numerator: int, denominator: int) -> int:
    """Round an integer ratio to nearest, ties to even, without floating point."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    magnitude = abs(numerator)
    quotient, remainder = divmod(magnitude, denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient & 1):
        quotient += 1
    return sign * quotient


def extract_current_features(samples_uA: Sequence[int]) -> tuple[int, ...]:
    """Extract four auditable integer-mA temporal features from one window."""
    if len(samples_uA) != WINDOW_SAMPLES:
        raise ValueError(f"current window must contain {WINDOW_SAMPLES} samples")
    if any(not isinstance(sample, int) for sample in samples_uA):
        raise TypeError("current samples must be integer microamps")

    count = len(samples_uA)
    total = sum(samples_uA)
    mean_mA = round_ratio_half_even(total, count * 1000)
    peak_to_peak_mA = round_ratio_half_even(
        max(samples_uA) - min(samples_uA), 1000
    )
    mean_abs_delta_mA = round_ratio_half_even(
        sum(abs(right - left) for left, right in zip(samples_uA, samples_uA[1:])),
        (count - 1) * 1000,
    )
    # Exact mean absolute deviation: |x_i - total/count| summed without first
    # rounding the mean. Multiplying each lane by count keeps the path integral.
    mean_abs_deviation_mA = round_ratio_half_even(
        sum(abs(count * sample - total) for sample in samples_uA),
        count * count * 1000,
    )
    return (
        mean_mA,
        peak_to_peak_mA,
        mean_abs_delta_mA,
        mean_abs_deviation_mA,
    )


def generate_current_window(class_name: str, case_index: int) -> tuple[int, ...]:
    """Generate a deterministic 320 ms current window in integer microamps."""
    if class_name not in CLASS_NAMES:
        raise ValueError(f"unknown current class {class_name!r}")
    if case_index < 0:
        raise ValueError("case_index must be non-negative")

    variant = (case_index % 7) - 3
    phase = case_index % 11
    samples: list[int] = []
    for index in range(WINDOW_SAMPLES):
        if class_name == "normal":
            ripple = (((index * 3 + phase) % 9) - 4) * 2500
            value = 420_000 + variant * 5_000 + ripple
        elif class_name == "bearing_drag":
            ripple = (((index * 5 + phase) % 11) - 5) * 9_000
            tooth = 25_000 if (index + phase) % 6 == 0 else 0
            value = 650_000 + variant * 8_000 + index * 1_100 + ripple + tooth
        else:
            ripple = (((index * 7 + phase) % 13) - 6) * 18_000
            pulse = 260_000 if (index + phase) % 8 in (0, 1) else 0
            value = 1_080_000 + variant * 12_000 + ripple + pulse
        samples.append(value)
    return tuple(samples)


def generated_feature_rows(
    *, first_case: int, cases_per_class: int
) -> tuple[tuple[tuple[int, ...], int], ...]:
    rows = []
    for label, class_name in enumerate(CLASS_NAMES):
        for case_index in range(first_case, first_case + cases_per_class):
            rows.append((extract_current_features(
                generate_current_window(class_name, case_index)
            ), label))
    return tuple(rows)


def feature_csv_bytes(
    *, first_case: int = 0, cases_per_class: int = TRAIN_CASES_PER_CLASS
) -> bytes:
    lines = [",".join((*FEATURE_NAMES, "state"))]
    for features, label in generated_feature_rows(
        first_case=first_case, cases_per_class=cases_per_class
    ):
        lines.append(",".join((*map(str, features), CLASS_NAMES[label])))
    return ("\n".join(lines) + "\n").encode("ascii")


def document_nodes(document: dict) -> tuple[list[SomNode], list[RationalSurd]]:
    nodes = [
        SomNode(
            node_id=node["id"],
            axial_q=node["axial"][0],
            axial_r=node["axial"][1],
            cluster_label=node["class_label"],
            weights=tuple(
                RationalSurd(value["p"], value["q"])
                for value in node["weights"]
            ),
        )
        for node in sorted(document["nodes"], key=lambda item: item["id"])
    ]
    feature_weights = [
        RationalSurd(value["p"], value["q"])
        for value in document["feature_weights"]
    ]
    return nodes, feature_weights


def bridge_feature_vector(features: Sequence[int]) -> tuple[RationalSurd, ...]:
    """Traverse Cartesian P16/Q16 quantization and explicit SOM18 widening."""
    if len(features) != len(FEATURE_NAMES):
        raise ValueError(f"feature vector must contain {len(FEATURE_NAMES)} values")
    quantized = quantize_feature_vector([float(value) for value in features], scale=1)
    if any(result.saturated for result in quantized):
        raise ValueError("temporal feature saturated at the Cartesian boundary")
    return tuple(widen_sensor_scalar_to_som18(result.value) for result in quantized)


def pack_quadrance(value: RationalSurd) -> int:
    if not 0 <= value.p <= 0xFFFFFFFF:
        raise ValueError("SOM1 quadrance P is outside unsigned 32-bit range")
    if not -(1 << 31) <= value.q < (1 << 31):
        raise ValueError("SOM1 quadrance Q is outside signed 32-bit range")
    return ((value.p & 0xFFFFFFFF) << 32) | (value.q & 0xFFFFFFFF)


def result_frame(result: BmuResult, generation: int) -> bytes:
    if not result.valid or not result.has_second:
        raise ValueError("SOM1 replay requires a valid winner and runner-up")
    flags = 0x01 | 0x04 | 0x10
    if result.ambiguous:
        flags |= 0x08
    evidence = SOM1Result(
        version=1,
        flags=flags,
        error=0,
        map_generation=1,
        result_generation=generation,
        winner=result.best_node_id,
        runner_up=result.second_node_id,
        label=result.cluster_label,
        best_q=pack_quadrance(result.best_q),
        second_q=pack_quadrance(result.second_q),
        confidence_gap=pack_quadrance(result.confidence_gap),
    )
    return encode_som1_frame(evidence)


def replay_current_windows(
    document: dict,
    rows: Iterable[tuple[Sequence[int], int]],
) -> tuple[ReplayEvidence, ...]:
    nodes, feature_weights = document_nodes(document)
    evidence = []
    for generation, (features, true_label) in enumerate(rows, 1):
        result = find_bmu(bridge_feature_vector(features), nodes, feature_weights)
        frame = result_frame(result, generation)
        evidence.append(
            ReplayEvidence(
                true_label=true_label,
                features=tuple(features),
                oracle=result,
                frame=frame,
                parsed=parse_som1_frame(frame),
            )
        )
    return tuple(evidence)
