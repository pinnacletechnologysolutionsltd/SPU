#!/usr/bin/env python3
"""Reproduce, validate, and optionally run the Iris SOM v1 hardware demo."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.rational_som import RationalSurd, SomNode, find_bmu
from som_map import (
    DiagConsole,
    PosixSerial,
    compute_map_sha256,
    iter_weight_commands,
    load_map,
    pack_surd,
    parse_result_response,
    validate_map,
    write_map,
)


DATASET = REPO / "software" / "tests" / "data" / "iris.csv"
DEFAULT_MAP = REPO / "software" / "models" / "iris_som_v1.json"
LABEL_NAMES = ("setosa", "versicolor", "virginica")
LABEL_MAP = {
    "Iris-setosa": 0,
    "Iris-versicolor": 1,
    "Iris-virginica": 2,
}
AXIAL_COORDS = (
    (0, 0),
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)
HEX_DELTAS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
SCALE = 1000
EPOCHS = 40
ORDER_SEED = 188
NEIGHBOR_EPOCHS = 5
WINNER_SHIFT_SCHEDULE = ((0, 10, 3), (10, 25, 4), (25, 40, 5))
SIDECAR_RAW_LABELS = (0, 1, 1, 2, 2, 3, 3)


def parse_scaled_decimal(text: str, scale: int = SCALE) -> int:
    if scale != 1000:
        raise ValueError("the Iris v1 parser is pinned to scale=1000")
    sign = -1 if text.startswith("-") else 1
    text = text.lstrip("+-")
    whole, dot, fractional = text.partition(".")
    if not whole.isdigit() or (dot and not fractional.isdigit()):
        raise ValueError(f"invalid decimal {text!r}")
    thousandths = int((fractional + "000")[:3]) if dot else 0
    return sign * (int(whole) * scale + thousandths)


def load_iris(path: Path = DATASET) -> list[tuple[tuple[int, ...], int]]:
    samples: list[tuple[tuple[int, ...], int]] = []
    with path.open(newline="", encoding="ascii") as handle:
        for row in csv.reader(handle):
            if not row:
                continue
            if len(row) != 5 or row[4] not in LABEL_MAP:
                raise ValueError(f"malformed Iris row: {row!r}")
            samples.append(
                (tuple(parse_scaled_decimal(value) for value in row[:4]), LABEL_MAP[row[4]])
            )
    if len(samples) != 150:
        raise ValueError(f"Iris corpus must contain 150 samples, got {len(samples)}")
    return samples


def squared_distance(lhs: tuple[int, ...] | list[int], rhs: tuple[int, ...] | list[int]) -> int:
    return sum((a - b) * (a - b) for a, b in zip(lhs, rhs))


def _initial_indices(samples: list[tuple[tuple[int, ...], int]]) -> list[int]:
    features = [sample[0] for sample in samples]
    mean = tuple(sum(row[j] for row in features) // len(features) for j in range(4))
    indices = [min(range(len(features)), key=lambda i: (squared_distance(features[i], mean), i))]
    while len(indices) < 7:
        candidates = (i for i in range(len(features)) if i not in indices)
        indices.append(
            max(
                candidates,
                key=lambda i: (
                    min(squared_distance(features[i], features[k]) for k in indices),
                    -i,
                ),
            )
        )
    return indices


def _epoch_order(epoch: int, count: int) -> list[int]:
    return sorted(
        range(count),
        key=lambda index: hashlib.sha256(
            f"iris-som-v1:{ORDER_SEED}:{epoch}:{index}".encode("ascii")
        ).digest(),
    )


def _winner_shift(epoch: int) -> int:
    for first, last, shift in WINNER_SHIFT_SCHEDULE:
        if first <= epoch < last:
            return shift
    raise AssertionError(f"epoch {epoch} is outside the schedule")


def train_iris_map(
    samples: list[tuple[tuple[int, ...], int]]
) -> tuple[list[list[int]], list[int], list[int]]:
    features = [sample[0] for sample in samples]
    initial_indices = _initial_indices(samples)
    weights = [list(features[index]) for index in initial_indices]

    for epoch in range(EPOCHS):
        for sample_index in _epoch_order(epoch, len(samples)):
            feature = features[sample_index]
            winner = min(
                range(7), key=lambda node: (squared_distance(feature, weights[node]), node)
            )
            targets = [(winner, _winner_shift(epoch))]
            if epoch < NEIGHBOR_EPOCHS:
                q, r = AXIAL_COORDS[winner]
                for dq, dr in HEX_DELTAS:
                    coordinate = (q + dq, r + dr)
                    if coordinate in AXIAL_COORDS:
                        targets.append((AXIAL_COORDS.index(coordinate), 3))
            for node, shift in targets:
                for feature_index in range(4):
                    delta = feature[feature_index] - weights[node][feature_index]
                    weights[node][feature_index] += delta >> shift

    votes = [Counter() for _ in range(7)]
    assignments: list[int] = []
    for feature, true_label in samples:
        winner = min(
            range(7), key=lambda node: (squared_distance(feature, weights[node]), node)
        )
        assignments.append(winner)
        votes[winner][true_label] += 1
    labels = [
        min(counts, key=lambda label: (-counts[label], label))
        if counts
        else 0
        for counts in votes
    ]
    return weights, labels, initial_indices


def build_map_document(
    samples: list[tuple[tuple[int, ...], int]]
) -> dict:
    weights, labels, initial_indices = train_iris_map(samples)
    document = {
        "format": "SPU_SOM_MAP_V1",
        "model": "iris-som-v1",
        "dataset": "Fisher Iris, checked-in 150-sample corpus",
        "dataset_path": "software/tests/data/iris.csv",
        "dataset_sha256": hashlib.sha256(DATASET.read_bytes()).hexdigest(),
        "node_count": 7,
        "feature_count": 4,
        "coefficient_bits": 18,
        "scale": SCALE,
        "feature_names": [
            "sepal_length",
            "sepal_width",
            "petal_length",
            "petal_width",
        ],
        "feature_weights": [
            {"p": 1, "q": 0},
            {"p": 1, "q": 0},
            {"p": 1, "q": 0},
            {"p": 1, "q": 0},
        ],
        "class_names": list(LABEL_NAMES),
        "trainer": {
            "kind": "deterministic-online-hex-som",
            "epochs": EPOCHS,
            "order": "sha256",
            "order_seed": ORDER_SEED,
            "initialization": "mean-nearest-then-farthest-first",
            "initial_sample_indices": initial_indices,
            "neighbor_epochs": NEIGHBOR_EPOCHS,
            "neighbor_shift": 3,
            "winner_shift_schedule": [list(item) for item in WINNER_SHIFT_SCHEDULE],
        },
        "nodes": [
            {
                "id": node,
                "axial": list(AXIAL_COORDS[node]),
                "class_label": labels[node],
                "weights": [{"p": value, "q": 0} for value in weights[node]],
            }
            for node in range(7)
        ],
    }
    document["map_sha256"] = compute_map_sha256(document)
    validate_map(document)
    return document


def map_nodes(document: dict) -> list[SomNode]:
    return [
        SomNode(
            node_id=node["id"],
            axial_q=node["axial"][0],
            axial_r=node["axial"][1],
            cluster_label=node["class_label"],
            weights=tuple(
                RationalSurd(value["p"], value["q"]) for value in node["weights"]
            ),
        )
        for node in sorted(document["nodes"], key=lambda item: item["id"])
    ]


def evaluate(
    document: dict, samples: list[tuple[tuple[int, ...], int]]
) -> tuple[list[int], list[list[int]], int]:
    nodes = map_nodes(document)
    feature_weights = [
        RationalSurd(value["p"], value["q"])
        for value in document["feature_weights"]
    ]
    winners: list[int] = []
    confusion = [[0, 0, 0] for _ in range(3)]
    correct = 0
    for feature, true_label in samples:
        result = find_bmu(
            [RationalSurd(value, 0) for value in feature], nodes, feature_weights
        )
        winners.append(result.best_node_id)
        predicted = result.cluster_label
        confusion[true_label][predicted] += 1
        correct += predicted == true_label
    return winners, confusion, correct


def print_confusion(title: str, confusion: list[list[int]], correct: int) -> None:
    print(title)
    print("                 predicted")
    print("true             set  ver  vir")
    for label, row in zip(("setosa    ", "versicolor", "virginica "), confusion):
        print(f"{label}       {row[0]:3d}  {row[1]:3d}  {row[2]:3d}")
    print(f"accuracy: {correct}/150 ({correct / 1.5:.1f}%)")


def upload_map(console: DiagConsole, document: dict, *, progress: bool = True) -> None:
    commands = list(iter_weight_commands(document))
    if len(commands) != 28:
        raise AssertionError(f"expected 28 writes, got {len(commands)}")
    for index, command in enumerate(commands, 1):
        console.command(command)
        if progress and index % 7 == 0:
            print(f"  map upload: {index}/28 writes")


def run_hardware(
    document: dict,
    samples: list[tuple[tuple[int, ...], int]],
    expected_winners: list[int],
    console_path: str,
    uart_path: str,
) -> tuple[list[list[int]], int]:
    nodes_by_id = {node["id"]: node for node in document["nodes"]}
    confusion = [[0, 0, 0] for _ in range(3)]
    exact_winners = 0
    started = time.monotonic()
    with PosixSerial(console_path) as console_serial, PosixSerial(uart_path) as uart:
        console = DiagConsole(console_serial)
        print(f"Uploading {document['model']} to {console_path}...")
        upload_map(console, document)

        for index, ((feature, true_label), expected_node) in enumerate(
            zip(samples, expected_winners), 1
        ):
            for feature_index, value in enumerate(feature):
                packed = pack_surd(value, 0)
                console.command(f"featwrite {feature_index} 0x{packed:016X}")
            uart.drain(0.002)
            console.command("classify")
            telemetry = uart.read_exact(1, 1.0)[0]
            response = console.command("result")
            done, busy, raw_label, raw = parse_result_response(response)

            node = telemetry & 0x7
            uart_label = (telemetry >> 3) & 0x3
            if not done or busy or raw != (0x80 | (raw_label << 4)):
                raise RuntimeError(
                    f"sample {index}: invalid result state done={done} busy={busy} "
                    f"label={raw_label} raw=0x{raw:02X}"
                )
            if uart_label != raw_label or raw_label != SIDECAR_RAW_LABELS[node]:
                raise RuntimeError(
                    f"sample {index}: UART/SPI raw-label mismatch "
                    f"node={node} uart={uart_label} spi={raw_label}"
                )
            if node != expected_node:
                raise RuntimeError(
                    f"sample {index}: FPGA node {node}, oracle node {expected_node}"
                )

            predicted = nodes_by_id[node]["class_label"]
            confusion[true_label][predicted] += 1
            exact_winners += 1
            if index % 25 == 0:
                print(f"  corpus: {index}/150 exact winner matches")

    print(f"Hardware corpus elapsed: {time.monotonic() - started:.1f}s")
    return confusion, exact_winners


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=str(DEFAULT_MAP), help="checked SOM map JSON")
    parser.add_argument("--emit-map", metavar="PATH", help="write regenerated map JSON")
    parser.add_argument("--hardware", action="store_true", help="run the connected Tang")
    parser.add_argument("--console-port", default="/dev/ttyACM0")
    parser.add_argument("--uart-port", default="/dev/ttyUSB1")
    args = parser.parse_args()

    samples = load_iris()
    regenerated = build_map_document(samples)
    if args.emit_map:
        write_map(args.emit_map, regenerated)
        print(f"Wrote {args.emit_map}")

    checked = load_map(args.map)
    if checked != regenerated:
        print("ERROR: checked map does not match deterministic regeneration", file=sys.stderr)
        print(f"  checked:     {checked.get('map_sha256')}", file=sys.stderr)
        print(f"  regenerated: {regenerated.get('map_sha256')}", file=sys.stderr)
        return 1

    winners, confusion, correct = evaluate(checked, samples)
    if correct != 147 or confusion != [[50, 0, 0], [0, 48, 2], [0, 1, 49]]:
        print(f"ERROR: unexpected oracle result {correct}, {confusion}", file=sys.stderr)
        return 1

    print(f"Map SHA-256: {checked['map_sha256']}")
    print(f"Dataset SHA-256: {checked['dataset_sha256']}")
    print_confusion("Oracle confusion matrix", confusion, correct)

    if args.hardware:
        hw_confusion, exact = run_hardware(
            checked,
            samples,
            winners,
            args.console_port,
            args.uart_port,
        )
        print_confusion("FPGA confusion matrix", hw_confusion, sum(
            hw_confusion[i][i] for i in range(3)
        ))
        if hw_confusion != confusion or exact != 150:
            print("IRIS_SOM_V1: FAIL", file=sys.stderr)
            return 1
        print("IRIS_SOM_V1: PASS (150/150 FPGA winners bit-exact to oracle)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
