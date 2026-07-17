#!/usr/bin/env python3
"""Validated SOM map files and dependency-free POSIX serial helpers."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import select
import termios
import time
from pathlib import Path
from typing import Iterator


MAP_FORMAT = "SPU_SOM_MAP_V1"
EXPECTED_NODES = 7
EXPECTED_FEATURES = 4
COEFFICIENT_BITS = 18
TRAINER_KIND = "deterministic-online-hex-som"
TRAINER_EPOCHS = 40
TRAINER_ORDER_SEED = 188
TRAINER_WINNER_SHIFT_SCHEDULE = [[0, 10, 3], [10, 25, 4], [25, 40, 5]]


class SomMapError(ValueError):
    """Raised when a SOM map violates the v1 artifact contract."""


def _canonical_payload(document: dict) -> bytes:
    payload = copy.deepcopy(document)
    payload.pop("map_sha256", None)
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        .encode("ascii")
    )


def compute_map_sha256(document: dict) -> str:
    return hashlib.sha256(_canonical_payload(document)).hexdigest()


def validate_map(document: dict, *, require_checksum: bool = True) -> dict:
    if not isinstance(document, dict):
        raise SomMapError("map root must be an object")
    if document.get("format") != MAP_FORMAT:
        raise SomMapError(f"format must be {MAP_FORMAT}")
    if document.get("node_count") != EXPECTED_NODES:
        raise SomMapError(f"node_count must be {EXPECTED_NODES}")
    if document.get("feature_count") != EXPECTED_FEATURES:
        raise SomMapError(f"feature_count must be {EXPECTED_FEATURES}")
    if document.get("coefficient_bits") != COEFFICIENT_BITS:
        raise SomMapError(f"coefficient_bits must be {COEFFICIENT_BITS}")
    if not isinstance(document.get("scale"), int) or document["scale"] <= 0:
        raise SomMapError("scale must be a positive integer")
    if not isinstance(document.get("model"), str) or not document["model"]:
        raise SomMapError("model must be a nonempty string")
    if not isinstance(document.get("dataset"), str) or not document["dataset"]:
        raise SomMapError("dataset must be a nonempty string")
    if (
        not isinstance(document.get("dataset_path"), str)
        or not document["dataset_path"]
    ):
        raise SomMapError("dataset_path must be a nonempty string")
    dataset_hash = document.get("dataset_sha256")
    if (
        not isinstance(dataset_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", dataset_hash) is None
    ):
        raise SomMapError("dataset_sha256 must be 64 lowercase hexadecimal digits")

    feature_names = document.get("feature_names")
    if (
        not isinstance(feature_names, list)
        or len(feature_names) != EXPECTED_FEATURES
        or any(not isinstance(name, str) or not name for name in feature_names)
        or len(set(feature_names)) != EXPECTED_FEATURES
    ):
        raise SomMapError(
            f"feature_names must contain {EXPECTED_FEATURES} distinct nonempty strings"
        )
    class_names = document.get("class_names")
    if (
        not isinstance(class_names, list)
        or not 1 <= len(class_names) <= EXPECTED_NODES
        or any(not isinstance(name, str) or not name for name in class_names)
        or len(set(class_names)) != len(class_names)
    ):
        raise SomMapError(
            f"class_names must contain 1..{EXPECTED_NODES} distinct nonempty strings"
        )

    trainer = document.get("trainer")
    if not isinstance(trainer, dict):
        raise SomMapError("trainer must be an object")
    pinned_trainer_fields = {
        "kind": TRAINER_KIND,
        "epochs": TRAINER_EPOCHS,
        "order": "sha256",
        "order_seed": TRAINER_ORDER_SEED,
        "initialization": "mean-nearest-then-farthest-first",
        "neighbor_epochs": 5,
        "neighbor_shift": 3,
        "winner_shift_schedule": TRAINER_WINNER_SHIFT_SCHEDULE,
    }
    for key, expected in pinned_trainer_fields.items():
        if trainer.get(key) != expected:
            raise SomMapError(f"trainer {key} must be {expected!r}")
    initial_indices = trainer.get("initial_sample_indices")
    if (
        not isinstance(initial_indices, list)
        or len(initial_indices) != EXPECTED_NODES
        or any(not isinstance(index, int) or index < 0 for index in initial_indices)
        or len(set(initial_indices)) != EXPECTED_NODES
    ):
        raise SomMapError(
            "trainer initial_sample_indices must contain "
            f"{EXPECTED_NODES} distinct non-negative integers"
        )

    limit_lo = -(1 << (COEFFICIENT_BITS - 1))
    limit_hi = (1 << (COEFFICIENT_BITS - 1)) - 1

    feature_weights = document.get("feature_weights")
    if (
        not isinstance(feature_weights, list)
        or len(feature_weights) != EXPECTED_FEATURES
    ):
        raise SomMapError(
            f"feature_weights must contain exactly {EXPECTED_FEATURES} entries"
        )
    for feature, value in enumerate(feature_weights):
        if not isinstance(value, dict) or set(value) != {"p", "q"}:
            raise SomMapError(
                f"feature weight {feature} must contain only p and q"
            )
        for component in ("p", "q"):
            coefficient = value[component]
            if not isinstance(coefficient, int):
                raise SomMapError(
                    f"feature weight {feature} {component} must be integer"
                )
            if not limit_lo <= coefficient <= limit_hi:
                raise SomMapError(
                    f"feature weight {feature} {component}={coefficient} "
                    f"is outside signed {COEFFICIENT_BITS}-bit range"
                )

    nodes = document.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != EXPECTED_NODES:
        raise SomMapError(f"nodes must contain exactly {EXPECTED_NODES} entries")

    seen_ids: set[int] = set()
    coefficient_count = 0
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise SomMapError(f"node {index} must be an object")
        node_id = node.get("id")
        if not isinstance(node_id, int) or not 0 <= node_id < EXPECTED_NODES:
            raise SomMapError(f"node {index} id must be in 0..{EXPECTED_NODES - 1}")
        if node_id in seen_ids:
            raise SomMapError(f"duplicate node id {node_id}")
        seen_ids.add(node_id)
        if (
            not isinstance(node.get("class_label"), int)
            or not 0 <= node["class_label"] < len(class_names)
        ):
            raise SomMapError(
                f"node {node_id} class_label must index class_names"
            )
        axial = node.get("axial")
        if (
            not isinstance(axial, list)
            or len(axial) != 2
            or not all(isinstance(value, int) for value in axial)
        ):
            raise SomMapError(f"node {node_id} axial must be two integers")
        weights = node.get("weights")
        if not isinstance(weights, list) or len(weights) != EXPECTED_FEATURES:
            raise SomMapError(
                f"node {node_id} must contain exactly {EXPECTED_FEATURES} weights"
            )
        for feature, value in enumerate(weights):
            if not isinstance(value, dict) or set(value) != {"p", "q"}:
                raise SomMapError(
                    f"node {node_id} feature {feature} must contain only p and q"
                )
            for component in ("p", "q"):
                coefficient = value[component]
                if not isinstance(coefficient, int):
                    raise SomMapError(
                        f"node {node_id} feature {feature} {component} must be integer"
                    )
                if not limit_lo <= coefficient <= limit_hi:
                    raise SomMapError(
                        f"node {node_id} feature {feature} {component}={coefficient} "
                        f"is outside signed {COEFFICIENT_BITS}-bit range"
                    )
            coefficient_count += 1

    if seen_ids != set(range(EXPECTED_NODES)):
        raise SomMapError("node ids must be exactly 0..6")
    if coefficient_count != EXPECTED_NODES * EXPECTED_FEATURES:
        raise SomMapError("map must contain exactly 28 prototype values")

    expected_hash = compute_map_sha256(document)
    stored_hash = document.get("map_sha256")
    if require_checksum and stored_hash != expected_hash:
        raise SomMapError(
            f"map_sha256 mismatch: stored={stored_hash!r}, expected={expected_hash}"
        )
    return document


def load_map(path: str | os.PathLike[str]) -> dict:
    path = Path(path)
    if path.suffix.lower() != ".json":
        raise SomMapError("SOM v1 maps must be JSON; executable Python maps are rejected")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SomMapError(f"cannot load {path}: {exc}") from exc
    return validate_map(document)


def write_map(path: str | os.PathLike[str], document: dict) -> None:
    document = copy.deepcopy(document)
    document["map_sha256"] = compute_map_sha256(document)
    validate_map(document)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def pack_surd(p: int, q: int, bits: int = COEFFICIENT_BITS) -> int:
    limit_lo = -(1 << (bits - 1))
    limit_hi = (1 << (bits - 1)) - 1
    if not limit_lo <= p <= limit_hi or not limit_lo <= q <= limit_hi:
        raise SomMapError(f"({p}, {q}) is outside signed {bits}-bit range")
    mask = (1 << bits) - 1
    return ((q & mask) << bits) | (p & mask)


def iter_weight_commands(document: dict) -> Iterator[str]:
    validate_map(document)
    for node in sorted(document["nodes"], key=lambda item: item["id"]):
        for feature, value in enumerate(node["weights"]):
            packed = pack_surd(value["p"], value["q"])
            yield f"somwrite {node['id']} {feature} 0x{packed:016X}"


def iter_label_commands(document: dict) -> Iterator[str]:
    validate_map(document)
    for node in sorted(document["nodes"], key=lambda item: item["id"]):
        yield f"somlabel {node['id']} {node['class_label']}"


def parse_result_response(response: str) -> tuple[int, int, int, int]:
    match = re.search(
        r"OK result done=(\d+) busy=(\d+) label=(\d+) raw=0x([0-9A-Fa-f]{2})",
        response,
    )
    if not match:
        raise RuntimeError(f"malformed result response: {response!r}")
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        int(match.group(4), 16),
    )


class PosixSerial:
    """Small 8N1 serial transport using only the Python standard library."""

    _BAUDS = {
        9600: termios.B9600,
        57600: termios.B57600,
        115200: termios.B115200,
        230400: termios.B230400,
    }

    def __init__(self, path: str, baud: int = 115200):
        if baud not in self._BAUDS:
            raise ValueError(f"unsupported baud rate {baud}")
        self.path = path
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CLOCAL | termios.CREAD | termios.CS8
        attrs[3] = 0
        attrs[4] = self._BAUDS[baud]
        attrs[5] = self._BAUDS[baud]
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self) -> "PosixSerial":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def drain(self, quiet_seconds: float = 0.05) -> bytes:
        data = bytearray()
        deadline = time.monotonic() + quiet_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            readable, _, _ = select.select([self.fd], [], [], remaining)
            if not readable:
                break
            chunk = os.read(self.fd, 4096)
            if chunk:
                data.extend(chunk)
                deadline = time.monotonic() + quiet_seconds
        return bytes(data)

    def write(self, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            _, writable, _ = select.select([], [self.fd], [], 1.0)
            if not writable:
                raise TimeoutError(f"timeout writing {self.path}")
            offset += os.write(self.fd, data[offset:])

    def read_exact(self, count: int, timeout: float) -> bytes:
        data = bytearray()
        deadline = time.monotonic() + timeout
        while len(data) < count:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"timeout reading {count} byte(s) from {self.path}; got {data.hex()}"
                )
            readable, _, _ = select.select([self.fd], [], [], remaining)
            if readable:
                data.extend(os.read(self.fd, count - len(data)))
        return bytes(data)

    def read_until(self, marker: bytes, timeout: float) -> bytes:
        data = bytearray()
        deadline = time.monotonic() + timeout
        while marker not in data:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"timeout waiting for {marker!r} from {self.path}: {data!r}"
                )
            readable, _, _ = select.select([self.fd], [], [], remaining)
            if readable:
                data.extend(os.read(self.fd, 4096))
        return bytes(data)


class DiagConsole:
    def __init__(self, serial_port: PosixSerial):
        self.serial = serial_port
        self.serial.drain(0.1)

    def command(self, command: str, timeout: float = 2.0) -> str:
        # The diagnostic firmware may emit a second idle prompt after a prior
        # command. Discard complete stale output before starting a transaction.
        self.serial.drain(0.01)
        self.serial.write((command + "\r\n").encode("ascii"))
        deadline = time.monotonic() + timeout
        response = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                decoded = response.decode("ascii", errors="replace")
                raise TimeoutError(f"{command}: incomplete response: {decoded!r}")
            response.extend(self.serial.read_until(b"> ", remaining))
            decoded = response.decode("ascii", errors="replace")
            if "ERR " in decoded:
                raise RuntimeError(f"{command}: {decoded.strip()}")
            if "OK " in decoded:
                return decoded
