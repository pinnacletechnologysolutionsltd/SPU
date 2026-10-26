#!/usr/bin/env python3
"""Print an inspectable replay of the frozen Soul-0 research fixture."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.research.soul0.simulator import FrozenSoul0Simulator


def main() -> int:
    replay = FrozenSoul0Simulator().run()
    print("Soul-0 frozen replay | synthetic software model")
    print(f"fixture sha256: {replay['fixture_sha256']}")
    print("phase           tick sensor event              stateless rolling soul0 restored profiles")
    for row in replay["rows"]:
        alerts = row["alerts"]
        restored = "-" if row["restored_soul0"] is None else FrozenSoul0Simulator._label(row["restored_soul0"])
        print(
            f"{row['phase']:<15} {row['tick']:>4} {row['sensor']:>6} "
            f"{row['event']:<18} {FrozenSoul0Simulator._label(alerts['stateless']):<8} "
            f"{FrozenSoul0Simulator._label(alerts['rolling_mean']):<8} "
            f"{FrozenSoul0Simulator._label(alerts['soul0']):<8} {restored:<8} {row['profiles']}"
        )
    print(f"checkpoint bytes after C: {replay['checkpoint_bytes']}")
    print(f"checkpoint sha256 after C: {replay['checkpoint_sha256']}")
    print(f"restored replay identical: {replay['checkpoint_replay_matches']}")
    recovery = replay["recovery_regression"]
    print(
        "seeded profile regression: "
        f"{recovery['initial_center']} (count {recovery['initial_count']}) -> "
        f"{recovery['final_center']} vs target {recovery['target_center']} "
        f"(error {recovery['center_error']}, recovery={recovery['recovery_succeeded']})"
    )
    print(f"scope: {replay['scope']}")
    return 0 if replay["checkpoint_replay_matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
