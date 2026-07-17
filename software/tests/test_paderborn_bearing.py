#!/usr/bin/env python3
"""Truth gate for deterministic Paderborn current feature extraction."""

from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.paderborn_bearing import (  # noqa: E402
    CurrentRecording,
    PaderbornDataError,
    binary64_to_microamps,
    envelope100_features,
    fit_scaler,
    native_features,
    round_ratio_half_even,
)
from paderborn_benchmark import Sample, fit_centroids, fit_threshold, threshold_confusion  # noqa: E402


def main() -> None:
    checks = 0

    def check(name: str, condition: bool) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(name)

    check("half-even lower tie", round_ratio_half_even(1, 2) == 0)
    check("half-even upper tie", round_ratio_half_even(3, 2) == 2)
    check("half-even negative", round_ratio_half_even(-3, 2) == -2)
    check("binary64 amp boundary", binary64_to_microamps(1.25) == 1_250_000)
    check("binary64 negative boundary", binary64_to_microamps(-0.5) == -500_000)

    native_recording = CurrentRecording(
        "constant.mat", (1_000_000,) * 4096, (-500_000,) * 4096
    )
    native = native_features(native_recording)
    check("one native window", len(native) == 1)
    check("three-phase mean absolute", native[0][0] == 666_667)
    check("constant phase ranges", native[0][1:] == (0, 0, 0))

    # One 320 ms envelope window with a changing amplitude and reconstructed
    # third phase.  This pins the 64 kHz -> 100 Hz integer block boundary.
    phase_1 = tuple((index // 640) * 1_000 for index in range(20_480))
    phase_2 = tuple(-value // 2 for value in phase_1)
    envelope = envelope100_features(CurrentRecording("envelope.mat", phase_1, phase_2))
    check("one envelope window", len(envelope) == 1)
    check("envelope has four integer features", len(envelope[0]) == 4 and all(isinstance(v, int) for v in envelope[0]))
    check("envelope detects change", envelope[0][1] > 0 and envelope[0][2] > 0)

    scaler = fit_scaler(((0, 10, 20, 30), (100, 110, 120, 130)))
    transformed, clipped = scaler.transform((50, 60, 70, 80))
    check("training affine scale", transformed == (15_000,) * 4 and clipped == 0)
    transformed, clipped = scaler.transform((-1, 111, 70, 80))
    check("unseen range clipping", transformed[:2] == (0, 30_000) and clipped == 2)
    try:
        fit_scaler(((1, 1, 1, 1), (1, 2, 3, 4)))
    except PaderbornDataError:
        pass
    else:
        raise AssertionError("constant training feature accepted")
    checks += 1

    train = (
        Sample("train", "H", "h", 0, (1, 1, 1, 1), 0),
        Sample("train", "H", "h", 1, (2, 2, 2, 2), 0),
        Sample("train", "I", "i", 0, (10, 10, 10, 10), 1),
        Sample("train", "O", "o", 0, (12, 12, 12, 12), 2),
    )
    threshold = fit_threshold(train)
    check("threshold chooses first tied feature", threshold["feature_index"] == 0)
    check("threshold separates damage", threshold_confusion(train, threshold)["correct"] == 4)
    check("three centroids", fit_centroids(train) == ((2, 2, 2, 2), (10, 10, 10, 10), (12, 12, 12, 12)))

    print(f"PASS: Paderborn current pipeline ({checks} checks)")


if __name__ == "__main__":
    main()
