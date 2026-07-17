#!/usr/bin/env python3
"""Reproduce, validate, and optionally run the Iris SOM v1 hardware demo."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.rational_som import RationalSurd, SomNode, find_bmu
from spu_host.som1 import parse_som1_frame
from som_map import (
    DiagConsole,
    PosixSerial,
    iter_label_commands,
    iter_weight_commands,
    load_map,
    pack_surd,
    parse_result_response,
    write_map,
)
from som_trainer import (
    DEFAULT_SCALE as SCALE,
    build_map_document as build_som_map_document,
    parse_scaled_decimal,
    train_map,
)


DATASET = REPO / "software" / "tests" / "data" / "iris.csv"
DEFAULT_MAP = REPO / "software" / "models" / "iris_som_v1.json"
LABEL_NAMES = ("setosa", "versicolor", "virginica")
LABEL_MAP = {
    "Iris-setosa": 0,
    "Iris-versicolor": 1,
    "Iris-virginica": 2,
}
SIDECAR_RAW_LABELS = (0, 1, 1, 2, 2, 3, 3)


def pack_result_surd(value: RationalSurd) -> int:
    return ((value.p & 0xFFFFFFFF) << 32) | (value.q & 0xFFFFFFFF)


def parse_som1_console_response(response: str):
    match = re.search(r"OK som1 raw=([0-9A-Fa-f ]+)", response)
    if not match:
        raise RuntimeError(f"malformed SOM1 console response: {response!r}")
    return parse_som1_frame(bytes.fromhex(match.group(1)))


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


def train_iris_map(
    samples: list[tuple[tuple[int, ...], int]]
) -> tuple[list[list[int]], list[int], list[int]]:
    return train_map(samples, model="iris-som-v1")


def build_map_document(
    samples: list[tuple[tuple[int, ...], int]]
) -> dict:
    return build_som_map_document(
        samples,
        model="iris-som-v1",
        dataset="Fisher Iris, checked-in 150-sample corpus",
        dataset_path="software/tests/data/iris.csv",
        dataset_sha256=hashlib.sha256(DATASET.read_bytes()).hexdigest(),
        scale=SCALE,
        feature_names=[
            "sepal_length",
            "sepal_width",
            "petal_length",
            "petal_width",
        ],
        class_names=LABEL_NAMES,
    )


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
    commands = list(iter_weight_commands(document)) + list(iter_label_commands(document))
    if len(commands) != 35:
        raise AssertionError(f"expected 35 writes, got {len(commands)}")
    for index, command in enumerate(commands, 1):
        console.command(command)
        if progress and index % 7 == 0:
            print(f"  map upload: {index}/35 writes")


def run_hardware(
    document: dict,
    samples: list[tuple[tuple[int, ...], int]],
    expected_winners: list[int],
    console_path: str,
    uart_path: str | None,
) -> tuple[list[list[int]], int]:
    nodes_by_id = {node["id"]: node for node in document["nodes"]}
    nodes = map_nodes(document)
    feature_weights = [
        RationalSurd(value["p"], value["q"])
        for value in document["feature_weights"]
    ]
    confusion = [[0, 0, 0] for _ in range(3)]
    exact_winners = 0
    active_map_generation = None
    last_result_generation = None
    started = time.monotonic()
    uart_context = PosixSerial(uart_path) if uart_path else nullcontext(None)
    with PosixSerial(console_path) as console_serial, uart_context as uart:
        console = DiagConsole(console_serial)
        print(f"Uploading {document['model']} to {console_path}...")
        upload_map(console, document)

        for index, ((feature, true_label), expected_node) in enumerate(
            zip(samples, expected_winners), 1
        ):
            for feature_index, value in enumerate(feature):
                packed = pack_surd(value, 0)
                console.command(f"featwrite {feature_index} 0x{packed:016X}")
            if uart is not None:
                uart.drain(0.002)
            console.command("classify")
            telemetry = uart.read_exact(1, 1.0)[0] if uart is not None else None
            response = console.command("result")
            done, busy, raw_label, raw = parse_result_response(response)
            som1 = parse_som1_console_response(console.command("som1"))

            oracle = find_bmu(
                [RationalSurd(value, 0) for value in feature],
                nodes,
                feature_weights,
            )

            node = som1.winner
            if not done or busy or raw != (0x80 | (raw_label << 4)):
                raise RuntimeError(
                    f"sample {index}: invalid result state done={done} busy={busy} "
                    f"label={raw_label} raw=0x{raw:02X}"
                )
            if raw_label != SIDECAR_RAW_LABELS[node]:
                raise RuntimeError(
                    f"sample {index}: SPI compact/SOM1 raw-label mismatch "
                    f"node={node} spi={raw_label}"
                )
            if telemetry is not None:
                uart_node = telemetry & 0x7
                uart_label = (telemetry >> 3) & 0x3
                if uart_node != node or uart_label != raw_label:
                    raise RuntimeError(
                        f"sample {index}: UART/SPI result mismatch "
                        f"uart_node={uart_node} som1_node={node} "
                        f"uart_label={uart_label} spi_label={raw_label}"
                    )
            if node != expected_node:
                raise RuntimeError(
                    f"sample {index}: FPGA node {node}, oracle node {expected_node}"
                )
            if not (som1.valid and not som1.busy and som1.has_second and
                    som1.map_valid and som1.error == 0):
                raise RuntimeError(f"sample {index}: invalid SOM1 flags {som1}")
            if (som1.winner != oracle.best_node_id or
                    som1.runner_up != oracle.second_node_id or
                    som1.label != oracle.cluster_label or
                    som1.best_q != pack_result_surd(oracle.best_q) or
                    som1.second_q != pack_result_surd(oracle.second_q) or
                    som1.confidence_gap != pack_result_surd(oracle.confidence_gap) or
                    som1.ambiguous != oracle.ambiguous):
                raise RuntimeError(
                    f"sample {index}: SOM1 evidence differs from oracle: {som1}"
                )
            if active_map_generation is None:
                active_map_generation = som1.map_generation
                if active_map_generation == 0:
                    raise RuntimeError("SOM1 map generation did not advance after upload")
            elif som1.map_generation != active_map_generation:
                raise RuntimeError(
                    f"sample {index}: map generation changed during corpus"
                )
            if last_result_generation is not None and som1.result_generation != (
                (last_result_generation + 1) & 0xFFFFFFFF
            ):
                raise RuntimeError(
                    f"sample {index}: non-consecutive result generation"
                )
            last_result_generation = som1.result_generation

            predicted = nodes_by_id[node]["class_label"]
            confusion[true_label][predicted] += 1
            exact_winners += 1
            if index % 25 == 0:
                print(f"  corpus: {index}/150 exact SOM1 evidence matches")

    print(f"Hardware corpus elapsed: {time.monotonic() - started:.1f}s")
    return confusion, exact_winners


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=str(DEFAULT_MAP), help="checked SOM map JSON")
    parser.add_argument("--emit-map", metavar="PATH", help="write regenerated map JSON")
    parser.add_argument("--hardware", action="store_true", help="run the connected SOM sidecar")
    parser.add_argument("--console-port", default="/dev/ttyACM0")
    parser.add_argument("--uart-port", default="/dev/ttyUSB1")
    parser.add_argument(
        "--no-uart",
        action="store_true",
        help="skip optional legacy UART telemetry; validate SPI compact and SOM1 results",
    )
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
            None if args.no_uart else args.uart_port,
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
