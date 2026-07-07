#!/usr/bin/env python3
"""
Trace equivalence test for SPU-13 SOM BMU RTL against the software oracle.

Replays the two built-in seven-node fixture scenarios from test_rational_som.py
through the Verilog spu_som_bmu + spu_cluster_reduce pipeline and asserts
bit-exact match on best_node_id, second_node_id, cluster_label, best_q,
second_q, confidence_gap, has_second, and ambiguity flag.

Usage:
  python3 software/tests/test_som_bmu_rtl_trace.py

Requirements: iverilog + vvp, rational_som oracle.
"""

import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software"))

from lib import rational_som
from lib.rational_som import (
    RationalSurd as Rs,
    SomNode,
    find_bmu,
    classify,
    rs,
    tiny_hex_fixture,
)


WIDTH = 32
SURD_W = 2 * WIDTH
NUM_FEATURES = 4


# ── RTL hex encoding ──────────────────────────────────────────────────

def surd_to_hex(r: Rs) -> str:
    """Encode a BMU output RationalSurd as {p[31:0], q[31:0]}."""
    a32 = r.p & 0xFFFFFFFF
    b32 = r.q & 0xFFFFFFFF
    return f"64'h{a32:08X}{b32:08X}"


def features_to_hex(feats: list[Rs]) -> str:
    """Encode feature vector as flat concat {f3, f2, f1, f0}, each {b,a}."""
    # MSB first: f3, f2, f1, f0
    parts = []
    for f in reversed(feats):
        parts.append(f"64'h{f.q & 0xFFFFFFFF:08X}{f.p & 0xFFFFFFFF:08X}")
    return "{" + ", ".join(parts) + "}"


# ── Expected output computation ───────────────────────────────────────

def compute_expected(features: list[Rs], nodes, feature_weights: list[Rs]):
    """Run software oracle and return expected BMU + classify outputs."""
    result = find_bmu(features, nodes, feature_weights)
    label, ambiguous = classify(result)
    return {
        "valid": result.valid,
        "best_node_id": result.best_node_id,
        "second_node_id": result.second_node_id if result.has_second else 0xFFFF,
        "cluster_label": result.cluster_label,
        "best_q": surd_to_hex(result.best_q),
        "second_q": surd_to_hex(result.second_q),
        "confidence_gap": surd_to_hex(result.confidence_gap),
        "has_second": result.has_second,
        "ambiguous": ambiguous,
    }


# ── Verilog testbench ─────────────────────────────────────────────────

TB_HEADER = """// Auto-generated expected values for SOM BMU trace test
"""

TB_BODY = r"""
`timescale 1ns/1ps

module spu_som_bmu_trace_tb;

    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    // --- BMU signals ---
    reg  start;
    wire done;
    reg  [255:0] features;
    reg  [255:0] feature_weights;
    wire bmu_valid;
    wire [15:0] best_node_id, second_node_id, cluster_label_in;
    wire [63:0] best_q, second_q, confidence_gap_in;
    wire has_second;

    reg  [2:0] train_addr = 0;

    spu_som_bmu #(.NUM_FEATURES(4), .MAX_NODES(7), .WIDTH(32)) u_bmu (
        .clk(clk), .rst_n(rst_n),
        .start(start), .done(done),
        .features(features),
        .feature_weights(feature_weights),
        .bmu_valid(bmu_valid),
        .best_node_id(best_node_id),
        .second_node_id(second_node_id),
        .cluster_label(cluster_label_in),
        .best_q(best_q),
        .second_q(second_q),
        .confidence_gap(confidence_gap_in),
        .has_second(has_second),
        .train_we(1'b0),
        .train_addr(train_addr),
        .train_be(4'b0000),
        .train_wdata(256'b0),
        .train_rdata(),
        .axiomatic_level(2'b00),
        .axiomatic_fault(),
        .fault_type(),
        .fault_count()
    );

    // --- Cluster reduce ---
    wire classify_valid;
    wire [15:0] label;
    wire [63:0] confidence_gap;
    wire ambiguous;

    spu_cluster_reduce #(.WIDTH(32)) u_reduce (
        .clk(clk), .rst_n(rst_n),
        .bmu_valid(bmu_valid),
        .best_node_id(best_node_id),
        .cluster_label_in(cluster_label_in),
        .best_q(best_q),
        .second_q(second_q),
        .confidence_gap_in(confidence_gap_in),
        .has_second(has_second),
        .ambiguity_threshold(64'd0),
        .classify_valid(classify_valid),
        .label(label),
        .confidence_gap(confidence_gap),
        .ambiguous(ambiguous)
    );

    integer fail_count;
    integer test_idx;

    task run_test;
        input [255:0] feat_vec;
        input [255:0] fw_vec;
        input [15:0]  exp_best_id;
        input [15:0]  exp_sec_id;
        input [15:0]  exp_label;
        input [63:0]  exp_best_q;
        input [63:0]  exp_sec_q;
        input [63:0]  exp_gap;
        input         exp_has_sec;
        input         exp_ambig;
        begin
            features <= feat_vec;
            feature_weights <= fw_vec;
            start <= 1;
            @(posedge clk);
            start <= 0;
            wait(done);
            #1;

            $display("--- Test %0d ---", test_idx);
            test_idx = test_idx + 1;

            if (bmu_valid !== 1) begin
                $display("  FAIL: bmu_valid = 0");
                fail_count = fail_count + 1;
            end

            if (best_node_id !== exp_best_id) begin
                $display("  FAIL: best_node_id: got %0d, expected %0d",
                         best_node_id, exp_best_id);
                fail_count = fail_count + 1;
            end else $display("  PASS: best_node_id = %0d", best_node_id);

            if (second_node_id !== exp_sec_id) begin
                $display("  FAIL: second_node_id: got %0d, expected %0d",
                         second_node_id, exp_sec_id);
                fail_count = fail_count + 1;
            end else $display("  PASS: second_node_id = %0d", second_node_id);

            if (cluster_label_in !== exp_label) begin
                $display("  FAIL: cluster_label: got %0d, expected %0d",
                         cluster_label_in, exp_label);
                fail_count = fail_count + 1;
            end else $display("  PASS: cluster_label = %0d", cluster_label_in);

            if (best_q !== exp_best_q) begin
                $display("  FAIL: best_q: got %h, expected %h", best_q, exp_best_q);
                fail_count = fail_count + 1;
            end else $display("  PASS: best_q = %h", best_q);

            if (second_q !== exp_sec_q) begin
                $display("  FAIL: second_q: got %h, expected %h", second_q, exp_sec_q);
                fail_count = fail_count + 1;
            end else $display("  PASS: second_q = %h", second_q);

            if (confidence_gap_in !== exp_gap) begin
                $display("  FAIL: confidence_gap: got %h, expected %h",
                         confidence_gap_in, exp_gap);
                fail_count = fail_count + 1;
            end else $display("  PASS: confidence_gap = %h", confidence_gap_in);

            if (has_second !== exp_has_sec) begin
                $display("  FAIL: has_second: got %b, expected %b",
                         has_second, exp_has_sec);
                fail_count = fail_count + 1;
            end else $display("  PASS: has_second = %b", has_second);

            if (ambiguous !== exp_ambig) begin
                $display("  FAIL: ambiguous: got %b, expected %b",
                         ambiguous, exp_ambig);
                fail_count = fail_count + 1;
            end else $display("  PASS: ambiguous = %b", ambiguous);

            #40;
        end
    endtask

    initial begin
        $dumpfile("build/spu_som_bmu_trace_tb.vcd");
        $dumpvars(0, spu_som_bmu_trace_tb);

        fail_count = 0;
        test_idx = 0;

        #20 rst_n = 1;
        #20;

        // ── Test scenarios (populated by Python) ──────────────────────

`SCENARIOS

        if (fail_count == 0)
            $display("ALL CHECKS PASSED");
        else
            $display("FAILED: %0d mismatches", fail_count);

        #200;
        $finish;
    end

endmodule
"""


# ── Main ──────────────────────────────────────────────────────────────

def main() -> int:
    nodes, f_weights = tiny_hex_fixture()
    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)

    # Test scenario 1: Integer BMU
    feats_1 = [rs(2), rs(1), rs(0), rs(0)]
    exp_1 = compute_expected(feats_1, nodes, f_weights)

    # Test scenario 2: Surd BMU
    feats_2 = [rs(0), rs(0), rs(-2), rs(2, 1)]
    exp_2 = compute_expected(feats_2, nodes, f_weights)

    # Test scenario 3: Stable tie-breaking (all-zero features, all-zero weights)
    fw_3 = [rs(1)]
    nodes_3 = [
        SomNode(5, 0, 0, 9, (rs(0),)),
        SomNode(1, 1, 0, 7, (rs(0),)),
        SomNode(3, 0, 1, 8, (rs(0),)),
    ]
    feats_3 = [rs(0)]
    exp_3 = compute_expected(feats_3, nodes_3, fw_3)

    # Test scenario 4: Invalid node should be skipped
    fw_4 = [rs(1)]
    nodes_4 = [
        SomNode(0, 0, 0, 1, (rs(0),), valid=False),
        SomNode(1, 1, 0, 2, (rs(3),)),
    ]
    feats_4 = [rs(0)]
    exp_4 = compute_expected(feats_4, nodes_4, fw_4)

    print("Expected outputs from software oracle:")
    for label, exp in [("Integer BMU", exp_1), ("Surd BMU", exp_2),
                        ("Tie-breaking", exp_3), ("Skip invalid", exp_4)]:
        print(f"  {label}: best={exp['best_node_id']} sec={exp['second_node_id']} "
              f"label={exp['cluster_label']} best_q={exp['best_q']} "
              f"gap={exp['confidence_gap']} has_sec={exp['has_second']} "
              f"ambig={exp['ambiguous']}")

    # Generate Verilog header
    header_path = build_dir / "som_trace_expected.vh"
    header_lines = [TB_HEADER]
    header_path.write_text("\n".join(header_lines) + "\n")

    # Build testbench body with scenarios
    scenarios = []

    # For scenarios 1-2: use built-in 7-node fixture
    for i, (feats, fw, exp) in enumerate(
        [(feats_1, f_weights, exp_1), (feats_2, f_weights, exp_2)]
    ):
        scenarios.append(
            f"        // Scenario {i+1}\n"
            f"        run_test({features_to_hex(feats)},\n"
            f"                 {features_to_hex(fw)},\n"
            f"                 16'd{exp['best_node_id']}, 16'd{exp['second_node_id']},\n"
            f"                 16'd{exp['cluster_label']},\n"
            f"                 {exp['best_q']},\n"
            f"                 {exp['second_q']},\n"
            f"                 {exp['confidence_gap']},\n"
            f"                 1'b{1 if exp['has_second'] else 0},\n"
            f"                 1'b{1 if exp['ambiguous'] else 0});\n"
        )

    # Note: scenarios 3-4 need custom node ROM (different node counts/features)
    # These are covered by the software oracle tests; for RTL trace we
    # verify scenarios 1-2 that exercise the 7-node fixture

    tb_content = TB_BODY.replace("`SCENARIOS", "\n".join(scenarios))

    tb_path = build_dir / "spu_som_bmu_trace_tb.v"
    # First write the header include
    full_tb = f'`include "{header_path}"\n' + tb_content
    tb_path.write_text(full_tb)

    # Find source files
    srcs = [
        REPO / "hardware/rtl/core/spu13/spu_quadrance_accum.v",
        REPO / "hardware/rtl/core/spu13/spu_som_bmu.v",
        REPO / "hardware/rtl/core/spu13/spu_cluster_reduce.v",
        REPO / "hardware/rtl/common/prim/surd_multiplier.v",
        tb_path,
    ]

    missing = [s for s in srcs if not s.exists()]
    if missing:
        print(f"ERROR: missing source files: {missing}")
        return 1

    # Compile
    vvp_path = build_dir / "spu_som_bmu_trace_tb.vvp"
    compile_cmd = [
        "iverilog", "-g2012",
        "-o", str(vvp_path),
        "-I", str(REPO / "hardware/rtl/common/prim"),
        "-y", str(REPO / "hardware/rtl/common/prim"),
        "-y", str(REPO / "hardware/rtl/core/spu13"),
        str(tb_path),
    ]
    print(f"\nCompile: {' '.join(compile_cmd)}")
    cr = subprocess.run(compile_cmd, capture_output=True, text=True, cwd=str(REPO))
    if cr.returncode != 0:
        print(f"COMPILE ERROR:\n{cr.stderr}")
        return 1

    # Run
    print(f"Run: vvp {vvp_path}")
    rr = subprocess.run(["vvp", str(vvp_path)], capture_output=True, text=True,
                        cwd=str(REPO), timeout=60)
    print(rr.stdout)
    if rr.stderr:
        print(rr.stderr, file=sys.stderr)

    if "ALL CHECKS PASSED" in rr.stdout:
        print("\nSOM BMU RTL TRACE: PASS")
        return 0
    else:
        print("\nSOM BMU RTL TRACE: FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
