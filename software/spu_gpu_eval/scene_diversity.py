"""Independent per-pixel oracle and collision analysis for the T1d suite."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from . import packet, reference
from .device_model import pixel_decision as device_decision, prepare_scene, render_rgb8
from .observer import extract_tile_features
from .scene import HEIGHT, WIDTH, Scene, parse_scene_bytes

HEADER = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
TASK_FIELDS = ("coverage", "covered_by", "winner", "rgb")
_COVERAGE = {"background": 0, "triangle0": 1, "triangle1": 2, "overlap": 3}


class SceneDiversityError(ValueError):
    """Raised when frozen suite or collision invariants fail."""


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("utf-8")


def _task(decision: dict[str, Any]) -> tuple[object, ...]:
    return (decision["coverage"], tuple(decision["covered_by"]), decision["winner"],
            tuple(decision["rgb"]))


def _signature(decision: dict[str, Any]) -> bytes:
    covered = sum(1 << item for item in decision["covered_by"])
    winner = 2 if decision["winner"] is None else decision["winner"]
    return bytes((_COVERAGE[decision["coverage"]], covered, winner, *decision["rgb"]))


def evaluate_scene(scene_id: str, raw: bytes, expected_samples: list[dict[str, Any]]) -> dict[str, Any]:
    scene = parse_scene_bytes(raw)
    packet_bytes = packet.compile_packet(scene)
    prepared = prepare_scene(packet_bytes)
    features = extract_tile_features(prepared)
    preview = HEADER + render_rgb8(prepared)
    samples = {(row["x"], row["y"]): row for row in expected_samples}
    if len(samples) != len(expected_samples):
        raise SceneDiversityError(f"{scene_id} has duplicate frozen sample coordinates")
    seen_samples: set[tuple[int, int]] = set()
    ideal_hash = hashlib.sha256()
    signatures = bytearray()
    disagreements = 0
    disagreement_rows = []
    sample_results = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            ideal = reference.pixel_decision(scene, x, y)
            device = device_decision(prepared, x, y)
            ideal_hash.update(canonical_json(ideal))
            signatures.extend(_signature(ideal))
            if _task(ideal) != _task(device):
                disagreements += 1
                disagreement_rows.append({"x": x, "y": y, "ideal": {field: ideal[field] for field in TASK_FIELDS},
                                          "device": {field: device[field] for field in TASK_FIELDS}})
            point = (x, y)
            if point in samples:
                expected = samples[point]
                for field in TASK_FIELDS:
                    if ideal[field] != expected["ideal"][field]:
                        raise SceneDiversityError(f"{scene_id} ideal sample mismatch at {point}: {field}")
                if ideal["depths"] != expected["ideal"]["depths"]:
                    raise SceneDiversityError(f"{scene_id} ideal rational-depth mismatch at {point}")
                if _task(device) != _task(expected["device"]):
                    raise SceneDiversityError(f"{scene_id} device sample mismatch at {point}")
                if [row["value"] for row in device["depths"]] != expected["device"]["depth_values"]:
                    raise SceneDiversityError(f"{scene_id} device depth sample mismatch at {point}")
                seen_samples.add(point)
                sample_results.append({"x": x, "y": y, "ideal": ideal, "device": device})
    if seen_samples != set(samples):
        raise SceneDiversityError(f"{scene_id} has an out-of-bounds or missing frozen sample")
    feature_doc = json.loads(features)
    if feature_doc["pixel_decisions"] != WIDTH * HEIGHT or len(feature_doc["tiles"]) != 1200:
        raise SceneDiversityError(f"{scene_id} observer output is incomplete")
    result = {"scene_id": scene_id, "input_sha256": hashlib.sha256(raw).hexdigest(),
              "feature_sha256": hashlib.sha256(features).hexdigest(),
              "device_preview_sha256": hashlib.sha256(preview).hexdigest(),
              "ideal_reference_map_sha256": ideal_hash.hexdigest(),
              "ideal_task_signature_sha256": hashlib.sha256(signatures).hexdigest(),
              "device_oracle_task_disagreement_pixels": disagreements,
              "device_oracle_task_disagreements": disagreement_rows,
              "pixel_decisions": WIDTH * HEIGHT, "tile_records": len(feature_doc["tiles"]),
              "samples": sample_results}
    return {"result": result, "features": features, "preview": preview,
            "packet": packet_bytes, "task_signatures": bytes(signatures)}


def collision_result(pair: dict[str, Any], left: dict[str, Any], right: dict[str, Any],
                     expected_differences: int) -> dict[str, Any]:
    equal = left["features"] == right["features"]
    differences = sum(left["task_signatures"][i:i + 6] != right["task_signatures"][i:i + 6]
                      for i in range(0, len(left["task_signatures"]), 6))
    if not equal or differences != expected_differences or differences == 0:
        raise SceneDiversityError("required observation collision or task-map difference failed")
    return {"scene_a": pair["a"], "scene_b": pair["b"], "kind": pair["kind"],
            "feature_payload_byte_equal": True,
            "ideal_task_differing_pixels": differences,
            "ideal_reference_map_sha256_a": left["result"]["ideal_reference_map_sha256"],
            "ideal_reference_map_sha256_b": right["result"]["ideal_reference_map_sha256"],
            "ideal_task_signature_sha256_a": left["result"]["ideal_task_signature_sha256"],
            "ideal_task_signature_sha256_b": right["result"]["ideal_task_signature_sha256"],
            "task_fields": list(TASK_FIELDS), "task_relevant_collision": True}
