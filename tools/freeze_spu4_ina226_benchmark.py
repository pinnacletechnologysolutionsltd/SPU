#!/usr/bin/env python3
"""Reconstruct owner-authorised failed models; never promote or tune them."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "software")]
import ina226_capture_pipeline as pipeline

EXPECTED = "3a801cd9f54ef36328cb9f07fc0e2ffa676eccd859e8f7012ad3f5fb0ea53bc1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def freeze(output):
    manifest_path = ROOT / "build/ina226_capture/manifest.json"
    manifest = pipeline.load_manifest(manifest_path)
    captured = {}
    original = pipeline.spu4_trainer.train_nodes

    def record(samples, *, model, **kwargs):
        result = original(samples, model=model, **kwargs)
        require(model not in captured, "duplicate model")
        weights, labels, _ = result
        captured[model] = (weights, list(labels))
        return result

    # Observe the existing execution, not a substituted trainer or oracle.
    pipeline.spu4_trainer.train_nodes = record
    try:
        with tempfile.TemporaryDirectory(prefix="spu4-reconstruct-") as tmp:
            result = pipeline.run_study(manifest, manifest_path, Path(tmp))
    finally:
        pipeline.spu4_trainer.train_nodes = original
    result_bytes = pipeline.canonical_json_bytes(result)
    require(hashlib.sha256(result_bytes).hexdigest() == EXPECTED,
            "historical result did not reproduce: STOP")
    require(not result["gates"]["spu4_som_edge_hardware_replay_eligible"],
            "failed application gate changed")
    require(len(captured) == 5, "expected five reconstructed models")

    windows = pipeline.manifest_windows(manifest, manifest_path)
    sources = {}
    raw = {}
    for session in manifest["sessions"]:
        archived = ROOT / "docs/bench_captures/2026-09-03-ina226-som" / (
            session["session_id"] + ".csv")
        require(hashlib.sha256(archived.read_bytes()).hexdigest() ==
                session["csv_sha256"], "archived capture hash mismatch")
        sources[str(archived.relative_to(ROOT))] = session["csv_sha256"]
        with archived.open() as stream:
            raw[session["session_id"]] = [int(r["current_uA"])
                                           for r in csv.DictReader(stream)][:128]
    folds = []
    for i, previous in enumerate(result["folds"]):
        weights, labels = captured[f"spu4-som-edge-ina226-v1-fold-{i}"]
        require(all(w.q == 0 and 0 <= w.p <= 30000 for node in weights for w in node),
                "model outside approved Q=0 domain")
        require(labels == previous["spu4_som_edge_diagnostics"]["node_majority_labels"],
                "node labels changed")
        scaler = pipeline.fit_scaler(w.features for w in windows if w.fold != i)
        cases = []
        for row, features, directions in pipeline.normalized_rows(
                tuple(w for w in windows if w.fold == i), scaler):
            best, distance = pipeline.find_bmu_edge(
                tuple(pipeline.RationalSurd(v, 0) for v in features), weights)
            cases.append(dict(session=row.session_id, window=row.window,
                              truth=row.label, raw_uA=raw[row.session_id][
                                  row.window * 32:(row.window + 1) * 32],
                              features=list(row.features), scaled=list(features),
                              clamp=list(directions), best=best, distance=distance,
                              label=labels[best]))
        folds.append(dict(fold=i, weights_p=[[w.p for w in node] for node in weights],
                          labels=labels, scaler=previous["scaler"], cases=cases))
    paths = [manifest_path, pipeline.DEFAULT_CONTRACT, Path(__file__)]
    # Pin all imported local Python sources, including transitive oracle dependencies.
    paths += [Path(m.__file__) for m in tuple(sys.modules.values())
              if getattr(m, "__file__", None) and
              str(m.__file__).startswith(str(ROOT)) and str(m.__file__).endswith(".py")]
    for path in paths:
        sources[str(path.resolve().relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    artifact = dict(format="SPU4_INA226_PERFORMANCE_FREEZE_V1",
                    provenance="deterministically reconstructed; historical weight bytes unavailable",
                    original_result_sha256=EXPECTED, hardware_replay_eligible=False,
                    performance_only_owner_authorized=True, sources=sources, folds=folds)
    encoded = pipeline.canonical_json_bytes(artifact)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Refuse to replace any earlier freeze, including after code changes.
    with output.open("xb") as stream:
        stream.write(encoded)
    print(f"PASS: five folds, 120 windows; original result {EXPECTED}")
    print(f"freeze SHA256 {hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    freeze(parser.parse_args().output)
