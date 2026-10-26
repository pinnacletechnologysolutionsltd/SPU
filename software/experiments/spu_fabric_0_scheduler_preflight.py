"""Identity and completeness checks run before any campaign scheduling."""
from __future__ import annotations

import json
from pathlib import Path

from software.experiments.spu_fabric_0_scheduler_io import (
    PROFILES, ROOT, digest, load_profile,
)

MANIFEST = ROOT / "fixtures/spu_fabric_0/manifest.json"
TIMING = ROOT / "fixtures/spu_fabric_0/phase1b_timing_table.json"
SERVICE = ROOT / "fixtures/spu_fabric_0/phase1b_candidate_service_table.json"


def load_service_table() -> dict:
    table = json.loads(SERVICE.read_text(encoding="utf-8"))
    if table.get("schema") != "spu-fabric-0-candidate-service-v1":
        raise ValueError("unsupported candidate service table")
    checks = {
        "manifest_sha256": MANIFEST,
        "timing_table_sha256": TIMING,
        "schedule_draft_sha256": ROOT / "spu_strategy/contract_spu_fabric_0_phase1b_schedule_model_draft_2026-10-15.md",
        "schedule_acceptance_sha256": ROOT / "spu_strategy/contract_spu_fabric_0_phase1b_schedule_acceptance_2026-10-15.md",
        "scheduler_engine_sha256": ROOT / "software/experiments/spu_fabric_0_scheduler_engine.py",
        "scheduler_ops_sha256": ROOT / "software/experiments/spu_fabric_0_scheduler_ops.py",
        "scheduler_accept_sha256": ROOT / "software/experiments/spu_fabric_0_scheduler_accept.py",
        "scheduler_resources_sha256": ROOT / "software/experiments/spu_fabric_0_scheduler_resources.py",
        "scheduler_report_sha256": ROOT / "software/experiments/spu_fabric_0_scheduler_report.py",
        "scheduler_io_sha256": ROOT / "software/experiments/spu_fabric_0_scheduler_io.py",
    }
    for field, path in checks.items():
        if table.get(field) != digest(path):
            raise ValueError(f"candidate service table identity mismatch: {field}")
    return table


def preflight() -> dict:
    service = load_service_table()
    checked = {}
    for profile in PROFILES:
        records, refs = load_profile(MANIFEST, profile, TIMING)
        if service["operation_count"] != len(records):
            raise ValueError("candidate service table operation count mismatch")
        if service.get("client_constants", {}).get("d4_cycles") != 1:
            raise ValueError("D4 service convention mismatch")
        if service["operation_count"] != len(records):
            raise ValueError("candidate service table operation count mismatch")
        if service.get("client_constants", {}).get("d4_cycles") != 1:
            raise ValueError("D4 service convention mismatch")
        all_ids = {row["operation_id"] for row in records}
        non_d4 = {row["operation_id"] for row in records if row["client"] != "d4"}
        if len(all_ids) != len(records):
            raise ValueError(f"duplicate operation IDs in {profile}")
        if set(service["entries"]) != {"A", "B", "C"}:
            raise ValueError("candidate set mismatch")
        for candidate, entries in service["entries"].items():
            if set(entries) != non_d4 or any(type(v) is not int or v < 0 for v in entries.values()):
                raise ValueError(f"{candidate} candidate-service entries mismatch")
        if service["entries"]["A"] != {opid: refs["intrinsic"][opid] for opid in non_d4}:
            raise ValueError("Candidate A service table differs from intrinsic references")
        checked[profile] = {"trace_sha256": refs["trace_sha256"],
                            "operations": len(records), "unique_ids": len(all_ids)}
    return {"manifest_sha256": digest(MANIFEST), "timing_table_sha256": digest(TIMING),
            "service_table_sha256": digest(SERVICE), "profiles": checked}
