"""Canonical serialization, provenance, and manifest helpers for FABRIC-0."""

from __future__ import annotations

import gzip
import hashlib
import heapq
import json
from collections import Counter
from pathlib import Path
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments import spu_fabric_0_trace_data as data

CLIENTS = ("surd_w32", "surd_w64", "som", "d4")
EXPECTED_COUNT = 327 + 327 + 8 + 288_132
SOURCE_LOCK = "spu_strategy/spu_fabric_0_phase1a_repair2_sources_2026-10-15.sha256"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=False) + "\n").encode("utf-8")


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def source_hashes(extra_paths=()):
    names = list(data.SOURCE_PATHS) + [
        "software/experiments/spu_fabric_0_trace_data.py",
        "software/experiments/spu_fabric_0_trace_io.py",
        "software/experiments/spu_fabric_0_trace_manifest.py",
        "tools/prepare_spu_fabric_0_traces.py",
        "spu_strategy/contract_spu_fabric_0_2026-10-15.md",
        "spu_strategy/contract_spu_fabric_0_phase1a_2026-10-15.md",
        "spu_strategy/contract_spu_fabric_0_phase1a_repair_2026-10-15.md",
        "spu_strategy/contract_spu_fabric_0_phase1a_repair2_2026-10-15.md",
    ] + list(extra_paths)
    locked = {}
    for line in (ROOT / SOURCE_LOCK).read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        locked[name] = digest
    if set(locked) != set(names):
        raise ValueError("frozen source lock path set does not match generator")
    actual = {name: file_hash(ROOT / name) for name in names}
    if actual != locked:
        changed = sorted(name for name in names if actual[name] != locked[name])
        raise ValueError(f"frozen source hash mismatch: {changed}")
    actual[SOURCE_LOCK] = file_hash(ROOT / SOURCE_LOCK)
    return actual


def write_source_spools(directory):
    """Run source/oracle generation once and stage immutable canonical rows."""
    streams = data.client_streams()
    directory = Path(directory)
    directory.mkdir()
    wanted = {"surd_w32": 327, "surd_w64": 327, "som": 8, "d4": 288_132}
    counts = {}
    for client in CLIENTS:
        count = 0
        with (directory / f"{client}.jsonl").open("xb") as output:
            for record in streams[client]:
                if record["client"] != client:
                    raise ValueError(f"source row has wrong client: {client}")
                expected_line = canonical(digest_expected(record)).decode("utf-8")
                output.write(canonical({"record": record,
                                        "expected_digest": expected_line}))
                count += 1
        if count != wanted[client]:
            raise ValueError(f"{client} source count {count} != {wanted[client]}")
        counts[client] = count
    return counts


def profiled_records(profile, source_directory):
    source_directory = Path(source_directory)
    if profile == "isolated":
        cycle = 0
        for client in CLIENTS:
            with (source_directory / f"{client}.jsonl").open("rb") as source:
                for order, line in enumerate(source):
                    row = json.loads(line)
                    yield cycle, client, order, row["record"], row["expected_digest"]
                    cycle += 1
        return
    interval = 1 if profile == "burst_synthetic" else 8
    iterators = []
    for rank, client in enumerate(CLIENTS):
        def events(client=client, rank=rank):
            with (source_directory / f"{client}.jsonl").open("rb") as source:
                for order, line in enumerate(source):
                    row = json.loads(line)
                    yield (order * interval, rank, order, client, row["record"],
                           row["expected_digest"])
        iterators.append(events())
    for cycle, _rank, order, client, record, expected_line in heapq.merge(*iterators):
        yield cycle, client, order, record, expected_line


def digest_expected(record):
    expected = dict(record["expected"])
    if expected.get("result_defined") is False:
        expected.pop("result", None)
    return {"operation_id": record["operation_id"], "expected": expected}


def write_trace(path, profile, source_directory):
    trace_hash = hashlib.sha256()
    oracle_hash = hashlib.sha256()
    count = 0
    last_order = {client: -1 for client in CLIENTS}
    client_counts = Counter()
    last_cycle = -1
    with Path(path).open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0,
                           compresslevel=1) as compressed:
            for cycle, client, order, source_record, expected_line in profiled_records(
                    profile, source_directory):
                if cycle < last_cycle or order <= last_order[client]:
                    raise ValueError("trace order is not deterministic/source ordered")
                last_cycle, last_order[client] = cycle, order
                record = dict(source_record)
                record.update(profile=profile, client_order=order,
                              offered_cycle=cycle)
                line = canonical(record)
                compressed.write(line)
                trace_hash.update(line)
                oracle_hash.update(expected_line.encode("utf-8"))
                count += 1
                client_counts[client] += 1
    if count != EXPECTED_COUNT:
        raise ValueError(f"{profile} count {count} != {EXPECTED_COUNT}")
    wanted = {"surd_w32": 327, "surd_w64": 327, "som": 8, "d4": 288_132}
    if dict(client_counts) != wanted:
        raise ValueError(f"{profile} client counts mismatch: {dict(client_counts)}")
    summary = {"path": str(Path(path).relative_to(Path(path).parents[1])),
               "count": count, "sha256": file_hash(path),
               "client_counts": dict(client_counts),
               "canonical_stream_sha256": trace_hash.hexdigest(),
               "expected_digest_sha256": oracle_hash.hexdigest()}
    verify_trace(path, profile, summary)
    return summary


def verify_trace(path, _profile, summary):
    trace_hash = hashlib.sha256()
    count = 0
    with gzip.open(path, "rb") as stream:
        for line in stream:
            if not line.endswith(b"\n"):
                raise ValueError("trace has a truncated canonical record")
            trace_hash.update(line)
            count += 1
    if count != EXPECTED_COUNT or count != summary["count"]:
        raise ValueError(f"trace readback count mismatch: {count}")
    if (trace_hash.hexdigest() != summary["canonical_stream_sha256"] or
            file_hash(path) != summary["sha256"]):
        raise ValueError("trace readback digest mismatch")


