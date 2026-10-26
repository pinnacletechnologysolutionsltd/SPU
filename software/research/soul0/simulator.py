"""Inspectable sample-by-sample replay of the frozen Soul-0 fixture."""

from __future__ import annotations

import hashlib

from .counted import CountedRollingMean, CountedSoul0, CountedStateless, as_reference_soul
from .heldout_experiment import PHASE_ORDER, _validate_transient_envelopes, load_frozen_inputs


class FrozenSoul0Simulator:
    """Replay the immutable fixture and expose each model decision as a row."""

    def __init__(self) -> None:
        self.fixture, self.fixture_hash, self.manifest_hash = load_frozen_inputs()
        _validate_transient_envelopes(self.fixture)
        training = self.fixture["training"]
        center = sum(training) // len(training)
        threshold = self.fixture["threshold"]
        self.stateless = CountedStateless(center, threshold)
        self.rolling = CountedRollingMean(training, threshold, window=8)
        self.soul = CountedSoul0([(center, len(training))], threshold=threshold, capacity=3)

    @staticmethod
    def _label(alert: bool) -> str:
        return "ALERT" if alert else "ok"

    def run(self) -> dict:
        rows: list[dict] = []
        restored = None
        checkpoint = b""
        totals = {
            name: {phase: {"healthy_alerts": 0, "fault_detected": 0} for phase in PHASE_ORDER}
            for name in ("stateless", "rolling_mean", "soul0")
        }
        for phase_name in PHASE_ORDER:
            phase = self.fixture["phases"][phase_name]
            if phase_name == "regime_a_return":
                checkpoint = as_reference_soul(self.soul).to_bytes()
                restored = CountedSoul0.from_bytes(checkpoint)
            for index, value in enumerate(phase["values"]):
                fault = index == phase["fault_index"]
                stateless_alert, stateless_ops = self.stateless.observe(value)
                rolling_alert, rolling_ops = self.rolling.observe(value)
                soul_alert, soul_ops = self.soul.observe(value)
                restored_alert = None if restored is None else restored.observe(value)[0]
                if restored_alert is not None and restored_alert != soul_alert:
                    raise RuntimeError("restored Soul-0 decision differs from uninterrupted replay")
                alerts = {
                    "stateless": stateless_alert,
                    "rolling_mean": rolling_alert,
                    "soul0": soul_alert,
                }
                ops = {"stateless": stateless_ops, "rolling_mean": rolling_ops, "soul0": soul_ops}
                for name, alert in alerts.items():
                    key = "fault_detected" if fault else "healthy_alerts"
                    totals[name][phase_name][key] += int(alert)
                profiles = ",".join(f"{p.center}:{p.count}" for p in self.soul.profiles)
                rows.append({
                    "phase": phase_name,
                    "tick": index,
                    "sensor": value,
                    "event": "OUT_OF_RANGE(+140)" if fault else "normal",
                    "alerts": alerts,
                    "operations": ops,
                    "profiles": profiles,
                    "restored_soul0": restored_alert,
                })
        final_checkpoint = as_reference_soul(self.soul).to_bytes()
        recovery = CountedSoul0([(180, 2)], threshold=self.fixture["threshold"], capacity=3)
        recovery_alerts = 0
        recovery_values = [
            self.fixture["phases"]["regime_b"]["nominal_center"]
            + self.fixture["noise_cycle"][index % len(self.fixture["noise_cycle"])]
            for index in range(16)
        ]
        for value in recovery_values:
            alert, _ = recovery.observe(value)
            recovery_alerts += int(alert)
        recovery_center = recovery.profiles[0].center
        return {
            "fixture_sha256": self.fixture_hash,
            "manifest_sha256": self.manifest_hash,
            "rows": rows,
            "totals": totals,
            "checkpoint_bytes": len(checkpoint),
            "checkpoint_sha256": hashlib.sha256(checkpoint).hexdigest(),
            "checkpoint_replay_matches": restored is not None and final_checkpoint == as_reference_soul(restored).to_bytes(),
            "soul0_final_checkpoint_sha256": hashlib.sha256(final_checkpoint).hexdigest(),
            "recovery_regression": {
                "initial_center": 180,
                "initial_count": 2,
                "final_center": recovery_center,
                "target_center": 200,
                "center_error": abs(recovery_center - 200),
                "recovery_succeeded": abs(recovery_center - 200) <= 5,
                "healthy_alerts": recovery_alerts,
                "profile_count": len(recovery.profiles),
            },
            "scope": "synthetic out-of-range transient detection; cross-regime lookalikes not evaluated",
        }
