"""Source-backed operation records for the SPU-FABRIC-0 Phase 1A traces."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "software"), str(ROOT / "software/tests")]

from software.experiments.surd_wide_correctness_vectors import self_test, vectors
from test_d4_reflection_oracle import (
    ROOTS, check_case, reflect_formula, reflect_specialized,
)
from test_d4_reflection_rtl import cases as d4_cases
from test_spu4_som_edge_oracle import NODES, QUERIES
from lib.spu4_som_edge_oracle import find_bmu_edge


SOURCE_PATHS = (
    "software/experiments/surd_wide_correctness_vectors.py",
    "software/tests/test_surd_wide_rtl_vectors.py",
    "hardware/tests/math/surd_mul_normalizer_vectors_harness.v",
    "hardware/rtl/math/surd_smul_unit.v",
    "hardware/rtl/math/surd_normalize_unit.v",
    "hardware/rtl/math/surd_binary_gcd3.v",
    "hardware/rtl/math/surd_exact_quotient.v",
    "software/tests/test_d4_reflection_rtl.py",
    "software/tests/test_d4_reflection_oracle.py",
    "hardware/rtl/math/spu_d4_reflection_unit.v",
    "software/tests/test_spu4_som_edge_oracle.py",
    "software/lib/spu4_som_edge_oracle.py",
    "software/lib/rational_som.py",
    "hardware/rtl/core/spu4/spu4_som_edge.v",
    "hardware/tests/spu4/spu4_som_edge_full_chain_tb.v",
)


def surd_records(width: int):
    rows = list(vectors(width))
    if len(rows) != 327:
        raise ValueError(f"Surd W={width} source count changed: {len(rows)}")
    for row in rows:
        ex = row["expected"]
        yield {
            "operation_id": f"surd_w{width}:{row['name']}",
            "source_case_id": f"surd_w{width}:{row['name']}",
            "client": f"surd_w{width}", "operation": "surd_multiply",
            "operands": row["operands"],
            "initial_state": {"destination": row["initial_destination"]},
            "read_set": ["operands", "initial_state.destination"],
            "write_set": ["result", "status"], "predecessors": [],
            "expected": {
                "invalid": ex["invalid"], "overflow": ex["overflow"],
                "request_normalization": ex["request_normalization"],
                "raw": ex["raw"], "reduced": ex["reduced"],
                "result_defined": True, "result": ex["destination"],
            },
        }


def d4_records():
    expected_count = 288_132
    for ordinal, (vector, selector) in enumerate(d4_cases()):
        if ordinal < 262_144:
            group, base = "reduced4", ordinal // 4
        elif ordinal < 271_748:
            group, base = "boundary16", (ordinal - 262_144) // 4
        else:
            group, base = "seeded16", (ordinal - 271_748) // 4
        case_id = f"{group}:{base:05d}:root{selector}"
        formula = reflect_formula(vector, ROOTS[selector])
        invalid = any(value < -32768 or value > 32767 for value in formula)
        specialized, oracle_invalid = reflect_specialized(vector, selector, 16)
        if invalid != oracle_invalid or (not invalid and tuple(specialized) != formula):
            raise ValueError(f"D4 oracle disagreement at {case_id}")
        check_case(vector, selector, 4 if ordinal < 262_144 else 16)
        result = None if invalid else list(formula)
        yield {
            "operation_id": f"d4:{case_id}", "source_case_id": f"d4:{case_id}",
            "client": "d4", "operation": "d4_reflect_signed16",
            "operands": {"vector": list(vector), "selector": selector},
            "initial_state": None, "read_set": ["vector", "selector"],
            "write_set": ["result", "invalid"], "predecessors": [],
            "expected": {"invalid": invalid, "result_defined": not invalid,
                         "result": result},
        }
    if ordinal + 1 != expected_count:
        raise ValueError(f"D4 source count changed: {ordinal + 1}")


def som_records():
    for index, (label, features, expected_node, expected_q) in enumerate(QUERIES):
        got_node, got_q = find_bmu_edge(features, NODES)
        distances = [sum((x.p - w.p) ** 2 + 3 * (x.q - w.q) ** 2
                         for x, w in zip(features, node)) for node in NODES]
        manual = min(range(len(distances)), key=lambda i: (distances[i], i))
        if (got_node, got_q) != (expected_node, expected_q):
            raise ValueError(f"SOM oracle/fixture disagreement at query {index}")
        if (manual, distances[manual]) != (got_node, got_q):
            raise ValueError(f"SOM independent score disagreement at query {index}")
        pairs = lambda values: [[value.p, value.q] for value in values]
        case_id = f"som:query:{index:02d}"
        yield {
            "operation_id": case_id, "source_case_id": case_id,
            "client": "som", "operation": "som_bmu_4x4_w16",
            "operands": {"features": pairs(features)},
            "initial_state": {"weights": [pairs(node) for node in NODES]},
            "read_set": ["features", "weights"],
            "write_set": ["best_node", "best_quadrance"],
            "predecessors": [],
            "expected": {"invalid": False, "result_defined": True,
                         "result": {"best_node": got_node,
                                    "best_quadrance": got_q}},
            "source_label": label,
        }


def client_streams():
    all_surd = [row for width in (32, 64) for row in vectors(width)]
    if len(all_surd) != 654:
        raise ValueError(f"Surd source count changed: {len(all_surd)}")
    self_test(all_surd)
    return {
        "surd_w32": surd_records(32), "surd_w64": surd_records(64),
        "som": som_records(), "d4": d4_records(),
    }
