"""Strict ingestion contract for the INA226 coarse-monitor experiment."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from lib.som_current_monitor import (
    FEATURE_NAMES,
    WINDOW_SAMPLES,
    extract_current_features,
    round_ratio_half_even,
)


CONTRACT_FORMAT = "SPU_INA226_COARSE_MONITOR_V1"
MANIFEST_FORMAT = "SPU_INA226_CAPTURE_MANIFEST_V1"
CLASS_NAMES = ("normal", "elevated_load", "current_limited_stall")
CSV_COLUMNS = (
    "host_iso",
    "probe",
    "phase",
    "t_ms",
    "bus_mV",
    "shunt_uV",
    "current_uA",
)
CAPTURE_BLOCKS = 10
FOLD_COUNT = 5
SESSIONS_PER_CLASS = 10
WINDOWS_PER_SESSION = 4
ACCEPTED_ROWS = WINDOW_SAMPLES * WINDOWS_PER_SESSION
NORMALIZED_LIMIT = 30_000
MEASUREMENT_HEADROOM_MA = 750


class CaptureDataError(ValueError):
    """Raised when a capture or manifest violates the frozen contract."""


@dataclass(frozen=True)
class CaptureSample:
    host_iso: str
    t_ms: int
    bus_mV: int
    shunt_uV: int
    current_uA: int


@dataclass(frozen=True)
class CaptureWindow:
    session_id: str
    block: int
    fold: int
    window: int
    features: tuple[int, ...]
    label: int


@dataclass(frozen=True)
class FeatureScaler:
    minima: tuple[int, ...]
    maxima: tuple[int, ...]
    limit: int = NORMALIZED_LIMIT

    def project(
        self, features: Sequence[int], *, clamp: bool = True
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        if len(features) != len(FEATURE_NAMES):
            raise CaptureDataError("feature vector has the wrong width")
        output: list[int] = []
        directions: list[int] = []
        for value, low, high in zip(features, self.minima, self.maxima):
            if high <= low:
                raise CaptureDataError("training feature has no range")
            if value < low:
                directions.append(-1)
                source = low if clamp else value
            elif value > high:
                directions.append(1)
                source = high if clamp else value
            else:
                directions.append(0)
                source = value
            output.append(round_ratio_half_even(
                (source - low) * self.limit, high - low
            ))
        return tuple(output), tuple(directions)


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_json_bytes(document: dict) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def expected_class_order(block: int) -> tuple[str, ...]:
    if not 0 <= block < CAPTURE_BLOCKS:
        raise CaptureDataError(f"capture block {block} is outside 0..9")
    offset = block % len(CLASS_NAMES)
    return CLASS_NAMES[offset:] + CLASS_NAMES[:offset]


def build_manifest(
    *,
    contract_path: str | Path,
    nominal_bus_mV: int,
    probe: str,
    actuator_model: str,
    actuator_continuous_current_mA: int,
    supply_current_limit_mA: int,
) -> dict:
    contract_path = Path(contract_path)
    if nominal_bus_mV <= 0:
        raise CaptureDataError("nominal bus voltage must be positive")
    if not probe or not actuator_model:
        raise CaptureDataError("probe and actuator model must be nonempty")
    if actuator_continuous_current_mA <= 0 or supply_current_limit_mA <= 0:
        raise CaptureDataError("current ratings must be positive")
    if supply_current_limit_mA > actuator_continuous_current_mA:
        raise CaptureDataError("supply limit exceeds actuator continuous-current rating")
    if supply_current_limit_mA > MEASUREMENT_HEADROOM_MA:
        raise CaptureDataError("supply limit exceeds INA226/R100 measurement headroom")

    sessions = []
    for block in range(CAPTURE_BLOCKS):
        for order, class_name in enumerate(expected_class_order(block)):
            session_id = f"b{block:02d}-{class_name}"
            sessions.append({
                "session_id": session_id,
                "block": block,
                "order": order,
                "class_name": class_name,
                "csv_path": f"captures/{session_id}.csv",
                "csv_sha256": None,
            })
    return {
        "format": MANIFEST_FORMAT,
        "contract": {
            "format": CONTRACT_FORMAT,
            "path": "software/datasets/ina226_coarse_monitor_v1.json",
            "sha256": sha256_file(contract_path),
        },
        "sensor": {
            "logger": "ina226_logger v1",
            "address": "0x40",
            "sample_hz": 100,
            "rshunt_mohm": 100,
        },
        "bench": {
            "probe": probe,
            "actuator_model": actuator_model,
            "actuator_continuous_current_mA": actuator_continuous_current_mA,
            "supply_current_limit_mA": supply_current_limit_mA,
            "nominal_bus_mV": nominal_bus_mV,
        },
        "sessions": sessions,
    }


def load_manifest(path: str | Path) -> dict:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureDataError(f"cannot load capture manifest: {exc}") from exc
    validate_manifest(document)
    return document


def validate_manifest(document: dict) -> None:
    if document.get("format") != MANIFEST_FORMAT:
        raise CaptureDataError("capture manifest format mismatch")
    contract = document.get("contract", {})
    if contract.get("format") != CONTRACT_FORMAT:
        raise CaptureDataError("capture contract format mismatch")
    if contract.get("path") != "software/datasets/ina226_coarse_monitor_v1.json":
        raise CaptureDataError("capture contract path mismatch")
    digest = contract.get("sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        raise CaptureDataError("capture contract SHA-256 is invalid")
    sensor = document.get("sensor", {})
    expected_sensor = {
        "logger": "ina226_logger v1",
        "address": "0x40",
        "sample_hz": 100,
        "rshunt_mohm": 100,
    }
    if sensor != expected_sensor:
        raise CaptureDataError("sensor metadata differs from frozen INA226/R100 contract")
    bench = document.get("bench", {})
    required_bench = (
        "probe",
        "actuator_model",
        "actuator_continuous_current_mA",
        "supply_current_limit_mA",
        "nominal_bus_mV",
    )
    if any(key not in bench for key in required_bench):
        raise CaptureDataError("capture manifest has incomplete bench metadata")
    if not bench["probe"] or not bench["actuator_model"]:
        raise CaptureDataError("probe and actuator model must be nonempty")
    if not isinstance(bench["nominal_bus_mV"], int) or bench["nominal_bus_mV"] <= 0:
        raise CaptureDataError("nominal bus voltage must be a positive integer")
    rating = bench["actuator_continuous_current_mA"]
    limit = bench["supply_current_limit_mA"]
    if (
        not isinstance(rating, int)
        or not isinstance(limit, int)
        or not 0 < limit <= rating
        or limit > MEASUREMENT_HEADROOM_MA
    ):
        raise CaptureDataError("supply current limit violates the frozen safety boundary")

    sessions = document.get("sessions")
    if not isinstance(sessions, list) or len(sessions) != CAPTURE_BLOCKS * 3:
        raise CaptureDataError("capture manifest must contain exactly 30 sessions")
    expected = []
    for block in range(CAPTURE_BLOCKS):
        for order, class_name in enumerate(expected_class_order(block)):
            expected.append((block, order, class_name))
    actual = [(item.get("block"), item.get("order"), item.get("class_name"))
              for item in sessions]
    if actual != expected:
        raise CaptureDataError("sessions do not follow the frozen block/class order")
    ids = [item.get("session_id") for item in sessions]
    paths = [item.get("csv_path") for item in sessions]
    if any(not isinstance(value, str) or not value for value in (*ids, *paths)):
        raise CaptureDataError("session ids and CSV paths must be nonempty strings")
    if len(set(ids)) != len(ids) or len(set(paths)) != len(paths):
        raise CaptureDataError("session ids and CSV paths must be unique")
    for item in sessions:
        digest = item.get("csv_sha256")
        if digest is not None and (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise CaptureDataError("session CSV SHA-256 must be lowercase hex or null")


def seal_manifest(document: dict, manifest_path: str | Path) -> dict:
    validate_manifest(document)
    root = Path(manifest_path).resolve().parent
    sealed = json.loads(json.dumps(document))
    for item in sealed["sessions"]:
        path = (root / item["csv_path"]).resolve()
        item["csv_sha256"] = sha256_file(path)
    validate_manifest(sealed)
    return sealed


def _parse_int(token: str, row_number: int, column: str) -> int:
    try:
        return int(token)
    except ValueError as exc:
        raise CaptureDataError(
            f"row {row_number}: {column} must be an integer"
        ) from exc


def parse_capture_csv(
    path: str | Path,
    *,
    class_name: str,
    probe: str,
    nominal_bus_mV: int,
    rshunt_mohm: int = 100,
) -> tuple[CaptureSample, ...]:
    path = Path(path)
    try:
        text = path.read_text(encoding="ascii")
    except (OSError, UnicodeDecodeError) as exc:
        raise CaptureDataError(f"cannot read {path}: {exc}") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != CSV_COLUMNS:
        raise CaptureDataError(f"{path}: CSV header differs from frozen schema")
    samples: list[CaptureSample] = []
    previous_t: int | None = None
    for row_number, row in enumerate(reader, 2):
        if None in row or any(row[column] is None for column in CSV_COLUMNS):
            raise CaptureDataError(f"{path}: row {row_number} has the wrong width")
        if row["probe"] != probe:
            raise CaptureDataError(f"{path}: row {row_number} has the wrong probe")
        if row["phase"] != class_name:
            raise CaptureDataError(f"{path}: row {row_number} has the wrong phase")
        try:
            datetime.fromisoformat(row["host_iso"])
        except ValueError as exc:
            raise CaptureDataError(
                f"{path}: row {row_number} has an invalid host timestamp"
            ) from exc
        t_ms = _parse_int(row["t_ms"], row_number, "t_ms")
        bus_mV = _parse_int(row["bus_mV"], row_number, "bus_mV")
        shunt_uV = _parse_int(row["shunt_uV"], row_number, "shunt_uV")
        current_uA = _parse_int(row["current_uA"], row_number, "current_uA")
        if previous_t is not None:
            interval = t_ms - previous_t
            if not 8 <= interval <= 12:
                raise CaptureDataError(
                    f"{path}: row {row_number} cadence interval {interval} ms"
                )
        previous_t = t_ms
        if abs(shunt_uV * 1000 - current_uA * rshunt_mohm) > 500:
            raise CaptureDataError(f"{path}: row {row_number} violates shunt scaling")
        if abs(shunt_uV) > 75_000:
            raise CaptureDataError(f"{path}: row {row_number} exceeds shunt headroom")
        tolerance = nominal_bus_mV * 50_000 // 1_000_000
        if not nominal_bus_mV - tolerance <= bus_mV <= nominal_bus_mV + tolerance:
            raise CaptureDataError(f"{path}: row {row_number} bus voltage out of range")
        samples.append(CaptureSample(
            host_iso=row["host_iso"],
            t_ms=t_ms,
            bus_mV=bus_mV,
            shunt_uV=shunt_uV,
            current_uA=current_uA,
        ))
    if len(samples) < ACCEPTED_ROWS:
        raise CaptureDataError(
            f"{path}: {len(samples)} rows, need at least {ACCEPTED_ROWS}"
        )
    return tuple(samples[:ACCEPTED_ROWS])


def manifest_windows(
    document: dict, manifest_path: str | Path
) -> tuple[CaptureWindow, ...]:
    validate_manifest(document)
    root = Path(manifest_path).resolve().parent
    bench = document["bench"]
    windows: list[CaptureWindow] = []
    for item in document["sessions"]:
        path = (root / item["csv_path"]).resolve()
        expected_sha = item["csv_sha256"]
        if expected_sha is None:
            raise CaptureDataError(f"session {item['session_id']} is not SHA-256 sealed")
        if sha256_file(path) != expected_sha:
            raise CaptureDataError(f"session {item['session_id']} SHA-256 mismatch")
        samples = parse_capture_csv(
            path,
            class_name=item["class_name"],
            probe=bench["probe"],
            nominal_bus_mV=bench["nominal_bus_mV"],
        )
        label = CLASS_NAMES.index(item["class_name"])
        for window in range(WINDOWS_PER_SESSION):
            start = window * WINDOW_SAMPLES
            current = tuple(
                sample.current_uA for sample in samples[start:start + WINDOW_SAMPLES]
            )
            windows.append(CaptureWindow(
                session_id=item["session_id"],
                block=item["block"],
                fold=item["block"] % FOLD_COUNT,
                window=window,
                features=extract_current_features(current),
                label=label,
            ))
    return tuple(windows)


def fit_scaler(features: Iterable[Sequence[int]]) -> FeatureScaler:
    rows = tuple(tuple(row) for row in features)
    if not rows or any(len(row) != len(FEATURE_NAMES) for row in rows):
        raise CaptureDataError("scaler requires nonempty four-feature rows")
    minima = tuple(min(row[index] for row in rows) for index in range(4))
    maxima = tuple(max(row[index] for row in rows) for index in range(4))
    if any(high <= low for low, high in zip(minima, maxima)):
        raise CaptureDataError("training feature has no range")
    return FeatureScaler(minima, maxima)


def feature_csv_bytes(windows: Iterable[CaptureWindow]) -> bytes:
    lines = [",".join(("session_id", "block", "fold", "window", *FEATURE_NAMES, "state"))]
    for row in windows:
        lines.append(",".join((
            row.session_id,
            str(row.block),
            str(row.fold),
            str(row.window),
            *map(str, row.features),
            CLASS_NAMES[row.label],
        )))
    return ("\n".join(lines) + "\n").encode("ascii")
