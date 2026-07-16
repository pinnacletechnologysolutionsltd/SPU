#!/usr/bin/env python3
"""Truth-gate tests for the reproducible seven-node Iris SOM artifact."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from iris_som_demo import DEFAULT_MAP, build_map_document, evaluate, load_iris
from som_map import (
    SomMapError,
    iter_weight_commands,
    load_map,
    pack_surd,
    parse_result_response,
    validate_map,
)


checks = 0


def check(name: str, condition: bool) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(name)


def rejects(document: dict, phrase: str) -> None:
    try:
        validate_map(document)
    except SomMapError as exc:
        check(f"rejects {phrase}", phrase in str(exc))
    else:
        raise AssertionError(f"did not reject {phrase}")


def main() -> None:
    samples = load_iris()
    generated_a = build_map_document(samples)
    generated_b = build_map_document(samples)
    checked = load_map(DEFAULT_MAP)

    check("150 checked-in Iris samples", len(samples) == 150)
    check("deterministic regeneration", generated_a == generated_b)
    check("checked map equals regeneration", checked == generated_a)
    commands = list(iter_weight_commands(checked))
    check("exactly 28 prototype writes", len(commands) == 28)
    check("hex writes are explicitly prefixed", all(" 0x" in command for command in commands))

    winners, confusion, correct = evaluate(checked, samples)
    check("150 oracle winners", len(winners) == 150)
    check("98.0% accuracy", correct == 147)
    check("confusion matrix", confusion == [[50, 0, 0], [0, 48, 2], [0, 1, 49]])
    check("all seven nodes used", set(winners) == set(range(7)))
    check("negative coefficient packing", pack_surd(-1, 0) == 0x3FFFF)
    check("positive q packing", pack_surd(0, 1) == (1 << 18))
    check(
        "result parser",
        parse_result_response("OK result done=1 busy=0 label=3 raw=0xB0\r\n> ")
        == (1, 0, 3, 0xB0),
    )

    missing = copy.deepcopy(checked)
    missing["nodes"].pop()
    rejects(missing, "exactly 7")

    out_of_range = copy.deepcopy(checked)
    out_of_range["nodes"][0]["weights"][0]["p"] = 1 << 17
    rejects(out_of_range, "outside signed 18-bit range")

    missing_metric = copy.deepcopy(checked)
    missing_metric.pop("feature_weights")
    rejects(missing_metric, "feature_weights")

    bad_checksum = copy.deepcopy(checked)
    bad_checksum["model"] = "tampered"
    rejects(bad_checksum, "map_sha256 mismatch")

    print(f"PASS: Iris SOM v1 reproducibility ({checks} checks)")


if __name__ == "__main__":
    main()
