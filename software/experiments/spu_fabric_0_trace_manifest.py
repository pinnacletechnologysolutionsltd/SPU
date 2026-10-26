"""Versioned candidate, arrival, queue, and source manifest for FABRIC-0."""

from __future__ import annotations

CLIENTS = ("surd_w32", "surd_w64", "som", "d4")


def candidate_profiles():
    return {
        "A": {"surd_lanes": 5, "d4": "dedicated",
              "som": "4-node x 4-feature dedicated BMU"},
        "B": {"shared_product_lanes": 1, "shared_add_accumulate": True,
              "surd_normalization": "dedicated", "som_compare_tie": "dedicated",
              "d4": "dedicated"},
        "C": {"shared_product_lanes": 2, "shared_add_accumulate": False,
              "surd_normalization": "dedicated",
              "som_accumulate_compare_tie": "dedicated", "d4": "dedicated"},
    }


def build_manifest(source_map, traces, python_version, zlib_version):
    return {
        "schema": "spu-fabric-0-trace-manifest-v2",
        "parent_contract": "contract_spu_fabric_0_2026-10-15.md",
        "phase1a_contract": "contract_spu_fabric_0_phase1a_2026-10-15.md",
        "generator_version": "1.1.0",
        "generator_sha256": source_map["tools/prepare_spu_fabric_0_traces.py"],
        "data_module_sha256": source_map[
            "software/experiments/spu_fabric_0_trace_data.py"],
        "io_module_sha256": source_map[
            "software/experiments/spu_fabric_0_trace_io.py"],
        "manifest_module_sha256": source_map[
            "software/experiments/spu_fabric_0_trace_manifest.py"],
        "source_sha256": source_map, "python_version": python_version,
        "zlib_version": zlib_version,
        "candidate_profiles": candidate_profiles(),
        "arrival_policy": {
            "client_order": list(CLIENTS), "isolated_interval_cycles": 1,
            "burst_interval_cycles": 1, "steady_period_cycles": 8,
            "steady_and_burst_synthetic": True,
            "workload_class": "THROUGHPUT_ORIENTED",
            "deadline_cycles": "NOT SPECIFIED",
        },
        "queues": {"external_ingress_entries_per_client": 4,
                   "candidate_internal_entries": {"A": 0, "B": 0, "C": 0}},
        "arbitration": {
            "A": "direct independent-unit dispatch; no global arbiter",
            "B": "product lane and shared add/accumulate each arbitrate "
                 "work-conserving round-robin: surd_w32,surd_w64,som",
            "C": "product lanes use work-conserving round-robin; select up "
                 "to two ready clients per cycle",
            "initial_pointer": "surd_w32",
            "D4": "dedicated path; not in shared-product arbitration",
        },
        "service_operation_counts": {
            "surd_multiply_products": 5,
            "som_products": "2 squares per feature x 4 features x 4 nodes",
            "d4_reflection_operations": 1,
            "candidate_service_cycle_latency": "NOT SPECIFIED; Phase 1B contract",
        },
        "source_case_counts": {"surd_w32": 327, "surd_w64": 327,
                               "d4": 288_132, "som": 8},
        "source_case_parameters": {
            "surd": {"widths": [32, 64], "named": 17, "edge": 54,
                     "seeded": 256, "seed_formula": "0x53555244 + width"},
            "d4": {"reduced_vectors": 65_536, "reduced_components": "-8..7",
                   "boundary_vectors": 2_401,
                   "boundary_values": [-32768, -32767, -1, 0, 1, 32766, 32767],
                   "seeded_vectors": 4_096, "seed": "0xD4_2026",
                   "selectors_per_vector": 4, "hardware_width": 16},
            "som": {"nodes": 4, "features": 4, "width": 16,
                    "queries": 8, "tie_rule": "strict less-than; lowest index wins"},
        },
        "traces": traces,
    }
