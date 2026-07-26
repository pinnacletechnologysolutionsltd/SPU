`timescale 1ns / 1ps

// Historical v1 latency measurement for the RPLU v0.1 corrigendum.
//
// This bench is intentionally compiled against the untouched RTL at commit
// f1e4dbf06aa1163cc98005feb063ec8aae7c933a.  It measures rising-edge index
// difference from debug_start_accept to done (done_edge - accept_edge):
//
//   1. the leaf inverter with an uncontended parallel M31 multiplier; and
//   2. the historical RPLU2PADE sidecar's real shared-multiplier mux, with no
//      Padé request outstanding.
//
// The integrated case forces only the sidecar's existing Padé→inverter
// request boundary.  No historical RTL source is patched or instrumented.

module spu13_fp4_inverter_latency_tb;
    reg clk;
    reg rst_n;
    integer edge_index;

    // Leaf inverter.
    reg         leaf_start;
    reg  [31:0] leaf_z0, leaf_z1, leaf_z2, leaf_z3;
    wire [31:0] leaf_inv0, leaf_inv1, leaf_inv2, leaf_inv3;
    wire        leaf_done, leaf_busy, leaf_flags_v;
    wire        leaf_mult_start;
    wire [31:0] leaf_mult_a0, leaf_mult_a1, leaf_mult_a2, leaf_mult_a3;
    wire [31:0] leaf_mult_b0, leaf_mult_b1, leaf_mult_b2, leaf_mult_b3;
    wire [31:0] leaf_mult_r0, leaf_mult_r1, leaf_mult_r2, leaf_mult_r3;
    wire        leaf_mult_done, leaf_mult_busy;
    wire        leaf_debug_start_accept;

    // Integrated historical RPLU2PADE sidecar.  Its public inputs stay idle;
    // the force/release in run_integrated_case drives the existing internal
    // request boundary while preserving the real shared-multiplier datapath.
    reg         int_start;
    reg  [31:0] int_z0, int_z1, int_z2, int_z3;

    integer leaf_unit_latency;
    integer leaf_singular_latency;
    integer integrated_unit_latency;
    integer integrated_singular_latency;
    integer failures;
    reg [31:0] reference_inv0, reference_inv1, reference_inv2, reference_inv3;

    always #5 clk = ~clk;

    always @(posedge clk)
        edge_index <= edge_index + 1;

    spu13_fp4_inverter u_leaf_inverter (
        .clk(clk), .rst_n(rst_n), .start(leaf_start),
        .z0(leaf_z0), .z1(leaf_z1), .z2(leaf_z2), .z3(leaf_z3),
        .inv0(leaf_inv0), .inv1(leaf_inv1),
        .inv2(leaf_inv2), .inv3(leaf_inv3),
        .done(leaf_done), .busy(leaf_busy), .flags_v(leaf_flags_v),
        .mult_start(leaf_mult_start),
        .mult_a0(leaf_mult_a0), .mult_a1(leaf_mult_a1),
        .mult_a2(leaf_mult_a2), .mult_a3(leaf_mult_a3),
        .mult_b0(leaf_mult_b0), .mult_b1(leaf_mult_b1),
        .mult_b2(leaf_mult_b2), .mult_b3(leaf_mult_b3),
        .mult_r0(leaf_mult_r0), .mult_r1(leaf_mult_r1),
        .mult_r2(leaf_mult_r2), .mult_r3(leaf_mult_r3),
        .mult_done(leaf_mult_done), .mult_busy(leaf_mult_busy),
        .debug_state(), .debug_start_accept(leaf_debug_start_accept)
    );

    spu13_m31_multiplier u_leaf_multiplier (
        .clk(clk), .rst_n(rst_n), .start(leaf_mult_start),
        .a0(leaf_mult_a0), .a1(leaf_mult_a1),
        .a2(leaf_mult_a2), .a3(leaf_mult_a3),
        .b0(leaf_mult_b0), .b1(leaf_mult_b1),
        .b2(leaf_mult_b2), .b3(leaf_mult_b3),
        .r0(leaf_mult_r0), .r1(leaf_mult_r1),
        .r2(leaf_mult_r2), .r3(leaf_mult_r3),
        .done(leaf_mult_done), .busy(leaf_mult_busy), .rns_error()
    );

    spu13_rplu2_pade_sidecar u_integrated (
        .clk(clk), .rst_n(rst_n),
        .inst_valid(1'b0), .inst_word(64'd0),
        .inst_claimed(), .busy(), .error(),
        .cfg_wr_en(1'b0), .cfg_sel(3'd0),
        .cfg_addr(10'd0), .cfg_data(64'd0),
        .qr_commit_valid(), .qr_commit_lane(),
        .qr_commit_A(), .qr_commit_B(),
        .qr_commit_C(), .qr_commit_D(),
        .debug_status(), .debug_state()
    );

    task check_latency_class;
        input [8*12-1:0] path_name;
        input [8*16-1:0] class_name;
        input integer measured;
        inout integer expected;
        begin
            if (expected < 0)
                expected = measured;
            else if (measured != expected) begin
                failures = failures + 1;
                $display("FAIL class-variance path=%0s class=%0s expected=%0d got=%0d",
                         path_name, class_name, expected, measured);
            end
        end
    endtask

    task run_leaf_case;
        input [8*24-1:0] case_name;
        input              expect_singular;
        input [31:0]       z0, z1, z2, z3;
        integer accept_edge;
        integer done_edge;
        integer latency;
        begin
            @(negedge clk);
            leaf_z0 = z0; leaf_z1 = z1; leaf_z2 = z2; leaf_z3 = z3;
            leaf_start = 1'b1;
            #1;
            if (!leaf_debug_start_accept) begin
                failures = failures + 1;
                $display("FAIL no-accept-ready path=leaf case=%0s edge=%0d",
                         case_name, edge_index);
            end
            @(posedge clk); #1;
            accept_edge = edge_index;
            @(negedge clk);
            leaf_start = 1'b0;
            while (!leaf_done) begin
                @(posedge clk); #1;
            end
            done_edge = edge_index;
            latency = done_edge - accept_edge;
            if (leaf_flags_v !== expect_singular) begin
                failures = failures + 1;
                $display("FAIL flags path=leaf case=%0s expected=%0d got=%0d",
                         case_name, expect_singular, leaf_flags_v);
            end
            if (!expect_singular) begin
                reference_inv0 = leaf_inv0;
                reference_inv1 = leaf_inv1;
                reference_inv2 = leaf_inv2;
                reference_inv3 = leaf_inv3;
            end
            if (expect_singular)
                check_latency_class("leaf", "singular", latency,
                                    leaf_singular_latency);
            else
                check_latency_class("leaf", "unit", latency,
                                    leaf_unit_latency);
            $display("LATENCY path=leaf class=%0s case=%0s accept_edge=%0d done_edge=%0d delta=%0d flags_v=%0d",
                     expect_singular ? "singular" : "unit",
                     case_name, accept_edge, done_edge, latency, leaf_flags_v);
            @(posedge clk); #1;
        end
    endtask

    task run_integrated_case;
        input [8*24-1:0] case_name;
        input              expect_singular;
        input [31:0]       z0, z1, z2, z3;
        integer accept_edge;
        integer done_edge;
        integer latency;
        begin
            @(negedge clk);
            int_z0 = z0; int_z1 = z1; int_z2 = z2; int_z3 = z3;
            int_start = 1'b1;
            force u_integrated.inv_start = int_start;
            force u_integrated.inv_z0 = int_z0;
            force u_integrated.inv_z1 = int_z1;
            force u_integrated.inv_z2 = int_z2;
            force u_integrated.inv_z3 = int_z3;
            #1;
            if (!u_integrated.inv_debug_start_accept) begin
                failures = failures + 1;
                $display("FAIL no-accept-ready path=integrated case=%0s edge=%0d",
                         case_name, edge_index);
            end
            @(posedge clk); #1;
            accept_edge = edge_index;
            @(negedge clk);
            int_start = 1'b0;
            while (!u_integrated.inv_done) begin
                @(posedge clk); #1;
            end
            done_edge = edge_index;
            latency = done_edge - accept_edge;
            if (u_integrated.inv_flags_v !== expect_singular) begin
                failures = failures + 1;
                $display("FAIL flags path=integrated case=%0s expected=%0d got=%0d",
                         case_name, expect_singular,
                         u_integrated.inv_flags_v);
            end
            if (!expect_singular &&
                (u_integrated.inv_r0 !== reference_inv0 ||
                 u_integrated.inv_r1 !== reference_inv1 ||
                 u_integrated.inv_r2 !== reference_inv2 ||
                 u_integrated.inv_r3 !== reference_inv3)) begin
                failures = failures + 1;
                $display("FAIL result path=integrated case=%0s expected=%08x,%08x,%08x,%08x got=%08x,%08x,%08x,%08x",
                         case_name,
                         reference_inv0, reference_inv1,
                         reference_inv2, reference_inv3,
                         u_integrated.inv_r0, u_integrated.inv_r1,
                         u_integrated.inv_r2, u_integrated.inv_r3);
            end
            if (expect_singular)
                check_latency_class("integrated", "singular", latency,
                                    integrated_singular_latency);
            else
                check_latency_class("integrated", "unit", latency,
                                    integrated_unit_latency);
            $display("LATENCY path=integrated class=%0s case=%0s accept_edge=%0d done_edge=%0d delta=%0d flags_v=%0d",
                     expect_singular ? "singular" : "unit",
                     case_name, accept_edge, done_edge, latency,
                     u_integrated.inv_flags_v);
            @(posedge clk); #1;
            release u_integrated.inv_start;
            release u_integrated.inv_z0;
            release u_integrated.inv_z1;
            release u_integrated.inv_z2;
            release u_integrated.inv_z3;
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        edge_index = 0;
        leaf_start = 1'b0;
        leaf_z0 = 32'd0; leaf_z1 = 32'd0;
        leaf_z2 = 32'd0; leaf_z3 = 32'd0;
        int_start = 1'b0;
        int_z0 = 32'd0; int_z1 = 32'd0;
        int_z2 = 32'd0; int_z3 = 32'd0;
        leaf_unit_latency = -1;
        leaf_singular_latency = -1;
        integrated_unit_latency = -1;
        integrated_singular_latency = -1;
        failures = 0;
        reference_inv0 = 32'd0; reference_inv1 = 32'd0;
        reference_inv2 = 32'd0; reference_inv3 = 32'd0;

        repeat (4) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        $display("HISTORICAL_RTL_COMMIT f1e4dbf06aa1163cc98005feb063ec8aae7c933a");
        $display("CYCLE_CONVENTION done_rising_edge_index - debug_start_accept_rising_edge_index");
`ifdef SPU_LATENCY_SEQ
        $display("BACKEND spu13_m31_multiplier_seq.v fallback uncontended");
`else
        $display("BACKEND spu13_m31_multiplier.v parallel uncontended");
`endif

        run_leaf_case("identity", 1'b0, 32'd1, 32'd0, 32'd0, 32'd0);
        run_integrated_case("identity", 1'b0,
                            32'd1, 32'd0, 32'd0, 32'd0);
        run_leaf_case("scalar_two", 1'b0, 32'd2, 32'd0, 32'd0, 32'd0);
        run_integrated_case("scalar_two", 1'b0,
                            32'd2, 32'd0, 32'd0, 32'd0);
        run_leaf_case("pure_sqrt3", 1'b0, 32'd0, 32'd1, 32'd0, 32'd0);
        run_integrated_case("pure_sqrt3", 1'b0,
                            32'd0, 32'd1, 32'd0, 32'd0);
        run_leaf_case("mixed_unit", 1'b0,
                      32'd12345, 32'd67890, 32'd11111, 32'd22222);
        run_integrated_case("mixed_unit", 1'b0,
                            32'd12345, 32'd67890, 32'd11111, 32'd22222);
        run_leaf_case("zero", 1'b1, 32'd0, 32'd0, 32'd0, 32'd0);
        run_integrated_case("zero", 1'b1,
                            32'd0, 32'd0, 32'd0, 32'd0);
        run_leaf_case("nonzero_zero_divisor", 1'b1,
                      32'd753804466, 32'd0, 32'd0, 32'd1);
        run_integrated_case("nonzero_zero_divisor", 1'b1,
                            32'd753804466, 32'd0, 32'd0, 32'd1);

        $display("SUMMARY leaf_unit=%0d leaf_singular=%0d integrated_unit=%0d integrated_singular=%0d arbitration_delta_unit=%0d arbitration_delta_singular=%0d",
                 leaf_unit_latency, leaf_singular_latency,
                 integrated_unit_latency, integrated_singular_latency,
                 integrated_unit_latency - leaf_unit_latency,
                 integrated_singular_latency - leaf_singular_latency);
        if (failures == 0)
            $display("PASS historical_fp4_latency (%0d failures)", failures);
        else
            $display("FAIL historical_fp4_latency (%0d failures)", failures);
        $finish;
    end
endmodule
