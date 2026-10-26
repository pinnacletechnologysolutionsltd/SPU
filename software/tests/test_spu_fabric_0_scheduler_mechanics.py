"""Hand-calculated mechanics fixtures; never loads the frozen campaign."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from software.experiments.spu_fabric_0_scheduler_engine import simulate


def d4(index: int, cycle: int = 0) -> dict:
    return {"operation_id": f"d4:test:{index}", "client": "d4",
            "operation": "d4_reflect_signed16", "client_order": index,
            "offered_cycle": cycle, "operands": {"vector": [index, 0, 0, 0], "selector": 0},
            "expected": {"invalid": False, "result_defined": True,
                         "result": [index, 0, 0, 0]}}


def surd(width: int, index: int = 0, cycle: int = 0,
         normalize: bool = False) -> dict:
    return {"operation_id": f"surd_w{width}:test:{index}", "client": f"surd_w{width}",
            "operation": "surd_multiply", "client_order": index,
            "offered_cycle": cycle, "operands": [1, 0, 1, 1, 0, 1],
            "expected": {"invalid": False, "request_normalization": normalize,
                         "result_defined": True, "result": [1, 0, 1]}}


def som(cycle: int = 0) -> dict:
    return {"operation_id": "som:test:0", "client": "som", "operation": "som_bmu_4x4_w16",
            "client_order": 0, "offered_cycle": cycle,
            "operands": {"features": [[[0, 0]] * 4]},
            "expected": {"invalid": False, "result_defined": True,
                         "result": {"best_node": 0, "best_quadrance": 0}}}


def test_d4_same_edge_replacement_is_one_cycle_interval():
    rows = [d4(0, 0), d4(1, 1)]
    result = simulate("A", "mechanics", rows, {row["operation_id"]: 1 for row in rows})
    assert result["completed_operations"] == 2
    assert result["clients"]["d4"]["max_response_cycles"] == 2
    assert result["clients"]["d4"]["completed_throughput_per_cycle"] == 0.5


def test_shared_lane_contention_and_hybrid_two_lane_issue():
    rows = [surd(32), surd(64), som(), d4(0)]
    intrinsic = {row["operation_id"]: 1 for row in rows}
    shared = simulate("B", "mechanics", rows, intrinsic)
    hybrid = simulate("C", "mechanics", rows, intrinsic)
    assert shared["completed_operations"] == 4
    assert shared["resources"]["surd_w64_product_arbitration_stall_cycles"] > 0
    assert hybrid["resources"]["product_lane_0_busy_cycles"] > 0
    assert hybrid["resources"]["product_lane_1_busy_cycles"] > 0
    assert hybrid["resources"]["surd_w32_reducer_busy_cycles"] == 1
    assert hybrid["resources"]["surd_w64_reducer_busy_cycles"] == 1


def test_ingress_saturation_counts_backpressure_and_drains():
    rows = [surd(32, index=i, cycle=i) for i in range(8)]
    result = simulate("A", "mechanics", rows,
                      {row["operation_id"]: 343 for row in rows}, max_cycles=5000)
    assert result["completed_operations"] == 8
    assert result["clients"]["surd_w32"]["accepted"] == 8
    assert result["clients"]["surd_w32"]["backpressure_cycles"] > 0
    assert result["ingress"]["surd_w32"]["max_occupancy"] == 4


def test_normalization_delay_is_included_in_response_latency():
    row = surd(32, normalize=True)
    result = simulate("A", "mechanics", [row], {row["operation_id"]: 107})
    # Offered at edge 0, enqueued there, accepted edge 1, completes edge 108.
    assert result["clients"]["surd_w32"]["max_response_cycles"] == 108
    assert result["completed_operations"] == 1


def test_isolated_candidate_service_cycles_match_hand_derived_dags():
    row = surd(32)
    intrinsic = {row["operation_id"]: 1}
    b = simulate("B", "mechanics", [row], intrinsic, include_operation_rows=True)
    c = simulate("C", "mechanics", [row], intrinsic, include_operation_rows=True)
    assert b["operation_rows"][row["operation_id"]]["service_cycles"] == 5
    assert c["operation_rows"][row["operation_id"]]["service_cycles"] == 6


def test_normalized_candidate_service_keeps_candidate_specific_compute_cost():
    row = surd(32, normalize=True)
    intrinsic = {row["operation_id"]: 107}
    b = simulate("B", "mechanics", [row], intrinsic, include_operation_rows=True)
    c = simulate("C", "mechanics", [row], intrinsic, include_operation_rows=True)
    assert b["operation_rows"][row["operation_id"]]["service_cycles"] == 111
    assert c["operation_rows"][row["operation_id"]]["service_cycles"] == 112


def test_d4_completion_is_independent_of_long_arithmetic_client():
    rows = [surd(32, normalize=True), som(), d4(0)]
    intrinsic = {rows[0]["operation_id"]: 107,
                 rows[1]["operation_id"]: 4,
                 rows[2]["operation_id"]: 1}
    result = simulate("B", "mechanics", rows, intrinsic)
    assert result["completed_operations"] == 3
    assert result["clients"]["d4"]["max_response_cycles"] < result["clients"]["surd_w32"]["max_response_cycles"]


if __name__ == "__main__":
    for test in (test_d4_same_edge_replacement_is_one_cycle_interval,
                 test_shared_lane_contention_and_hybrid_two_lane_issue,
                 test_ingress_saturation_counts_backpressure_and_drains,
                 test_normalization_delay_is_included_in_response_latency,
                 test_isolated_candidate_service_cycles_match_hand_derived_dags,
                 test_normalized_candidate_service_keeps_candidate_specific_compute_cost,
                 test_d4_completion_is_independent_of_long_arithmetic_client):
        test()
    print("SPU-FABRIC-0 scheduler mechanics: PASS (7 cases)")
