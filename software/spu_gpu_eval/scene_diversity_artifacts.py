"""Frozen-input checks and atomic publication for scene-diversity results."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .scene import PROFILE
from .scene_diversity import (SceneDiversityError, canonical_json, collision_result,
                              evaluate_scene)
from .scene_diversity_publish import publish

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "examples/gpu/scene_diversity/manifest.json"
REFERENCE = ROOT / "fixtures/gpu_scene_diversity_reference.json"
SOURCE_LOCK = ROOT / "fixtures/gpu_scene_diversity_source_lock.json"
OUTPUT = ROOT / "build/gpu_evaluation/scene_diversity_01"
SOURCES = ("software/spu_gpu_eval/scene.py", "software/spu_gpu_eval/packet.py",
           "software/spu_gpu_eval/reference.py", "software/spu_gpu_eval/device_model.py",
           "software/spu_gpu_eval/observer.py", "software/spu_gpu_eval/scene_diversity.py",
           "software/spu_gpu_eval/scene_diversity_artifacts.py",
           "software/spu_gpu_eval/scene_diversity_publish.py",
           "software/spu_gpu_eval/cli.py", "software/tests/test_gpu_scene_diversity.py")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _frozen_sources() -> dict[str, str]:
    lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    expected = lock.get("source_sha256")
    if lock.get("format") != "gpu_scene_diversity_source_lock_v1" or set(expected or {}) != set(SOURCES):
        raise SceneDiversityError("source hash lock does not match the evaluator source set")
    actual = {name: _hash((ROOT / name).read_bytes()) for name in SOURCES}
    if actual != expected:
        raise SceneDiversityError("a frozen evaluator source hash does not match the lock")
    return actual


def _evaluate(suite_raw: bytes, reference_raw: bytes) -> tuple[dict[str, bytes], dict[str, Any]]:
    suite, reference = json.loads(suite_raw), json.loads(reference_raw)
    if suite.get("format") != "spu_gpu_scene_diversity_suite_v1" or suite.get("profile") != PROFILE:
        raise SceneDiversityError("unsupported scene-diversity suite")
    if suite.get("reference_fixture") != "fixtures/gpu_scene_diversity_reference.json":
        raise SceneDiversityError("suite names an unexpected reference fixture")
    if reference.get("format") != "gpu_scene_diversity_reference_v1":
        raise SceneDiversityError("unsupported scene-diversity reference")
    if reference.get("task_fields") != ["coverage", "covered_by", "winner", "rgb"]:
        raise SceneDiversityError("reference task fields disagree with the frozen task contract")
    entries = suite.get("scenes", [])
    if {item["id"] for item in entries} != set(reference.get("scenes", {})):
        raise SceneDiversityError("suite scene IDs disagree with frozen references")
    role_set = {item["role"] for item in entries}
    required_roles = {"collision-pair-a", "collision-pair-b", "overlap-depth-order-0",
                      "overlap-depth-order-1", "equal-depth-tie", "shared-color-control"}
    if role_set != required_roles:
        raise SceneDiversityError("suite does not contain the frozen diversity roles")
    outputs: dict[str, dict[str, Any]] = {}
    artifacts: dict[str, bytes] = {}
    for entry in entries:
        scene_id, path = entry["id"], ROOT / entry["path"]
        raw = path.read_bytes()
        expected_hash = entry.get("sha256")
        if not expected_hash or _hash(raw) != expected_hash:
            raise SceneDiversityError(f"frozen scene hash mismatch: {scene_id}")
        result = evaluate_scene(scene_id, raw, reference["scenes"][scene_id])
        outputs[scene_id] = result
        prefix = f"scenes/{scene_id}/"
        artifacts[prefix + "scene_packet.bin"] = result["packet"]
        artifacts[prefix + "device_preview.ppm"] = result["preview"]
        artifacts[prefix + "tile_features.json"] = result["features"]
        artifacts[prefix + "ideal_reference_map.sha256"] = (
            result["result"]["ideal_reference_map_sha256"] + "\n").encode("ascii")
        artifacts[prefix + "report.json"] = canonical_json(result["result"])
    collision_fixtures = { (item["a"], item["b"]): item for item in reference["collision_pairs"] }
    if set(collision_fixtures) != {(item["a"], item["b"]) for item in suite["collision_pairs"]}:
        raise SceneDiversityError("suite and reference collision declarations differ")
    collision_reports = []
    for pair in suite["collision_pairs"]:
        frozen = collision_fixtures.get((pair["a"], pair["b"]))
        if frozen is None or frozen["kind"] != pair["kind"]:
            raise SceneDiversityError("collision declaration is absent from independent fixture")
        collision_reports.append(collision_result(pair, outputs[pair["a"]], outputs[pair["b"]],
                                                  frozen["expected_task_differing_pixels"]))
    if suite.get("optional_same_rgb_pair") is not None:
        raise SceneDiversityError("optional pair is not implemented in this contract version")
    artifacts["collision_report.json"] = canonical_json({"pairs": collision_reports})
    report = {"format": "gpu_scene_diversity_result_v1", "profile": PROFILE,
              "scene_count": len(outputs), "scenes": [outputs[key]["result"] for key in outputs],
              "collision_pairs": collision_reports, "optional_same_rgb_pair": None,
              "verdicts": {"fixtures_valid": True, "finite_width_observed": True,
                           "task_relevant_collision_demonstrated": True,
                           "som_or_compression_advantage": "NOT_EVALUATED"}}
    artifacts["report.json"] = canonical_json(report)
    return artifacts, report


def write_scene_diversity(suite_path: str | Path = SUITE,
                         out_dir: str | Path = OUTPUT) -> Path:
    suite_target = Path(suite_path)
    if not suite_target.is_absolute():
        suite_target = ROOT / suite_target
    if Path(os.path.abspath(suite_target)) != SUITE:
        raise SceneDiversityError(f"suite must be the frozen manifest {SUITE}")
    target = Path(out_dir)
    if not target.is_absolute():
        target = ROOT / target
    target = Path(os.path.abspath(target))
    if target != OUTPUT:
        raise SceneDiversityError(f"output must be the frozen destination {OUTPUT}")
    if target.exists() or target.is_symlink():
        raise SceneDiversityError(f"output path already exists: {target}")
    suite_raw, reference_raw = SUITE.read_bytes(), REFERENCE.read_bytes()
    suite = json.loads(suite_raw)
    if _hash(reference_raw) != suite.get("reference_fixture_sha256"):
        raise SceneDiversityError("frozen independent-reference fixture hash mismatch")
    suite_doc = json.loads(suite_raw)
    sources = _frozen_sources()
    fixture_hashes = {item["path"]: _hash((ROOT / item["path"]).read_bytes())
                      for item in suite_doc["scenes"]}
    fixture_hashes["examples/gpu/scene_diversity/manifest.json"] = _hash(suite_raw)
    fixture_hashes["fixtures/gpu_scene_diversity_reference.json"] = _hash(reference_raw)
    fixture_hashes["fixtures/gpu_scene_diversity_source_lock.json"] = _hash(SOURCE_LOCK.read_bytes())
    artifact_bytes, report = _evaluate(suite_raw, reference_raw)
    if _frozen_sources() != sources:
        raise SceneDiversityError("source changed while the suite was being evaluated")
    for name, value in fixture_hashes.items():
        if _hash((ROOT / name).read_bytes()) != value:
            raise SceneDiversityError("frozen fixture changed while the suite was being evaluated")
    manifest = {"format": "gpu_scene_diversity_manifest_v1", "profile": PROFILE,
                "suite_sha256": _hash(suite_raw), "source_sha256": sources,
                "fixture_sha256": fixture_hashes,
                "artifacts_sha256": {name: _hash(content) for name, content in artifact_bytes.items()},
                "scene_count": report["scene_count"], "device_model": True,
                "physical_observation": False}
    artifact_bytes["manifest.json"] = canonical_json(manifest)
    return publish(target, artifact_bytes)
