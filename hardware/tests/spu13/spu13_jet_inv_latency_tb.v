`timescale 1ns / 1ps

// Historical RPLU v0.1 jet-inverse latency measurement.
// Compile against untouched f1e4dbf RTL.  Latency is the difference between
// the rising edge accepting start in jet_inv's idle state and the rising edge
// on which done asserts.

module spu13_jet_inv_latency_tb;
    reg clk;
    reg rst_n;
    reg start;
    integer edge_index;
    integer failures;
    integer unit_latency;
    integer direct_zero_latency;
    integer tower_singular_latency;

    reg [31:0] c0_z0, c0_z1, c0_z2, c0_z3;
    reg [31:0] c1_z0, c1_z1, c1_z2, c1_z3;
    reg [31:0] c2_z0, c2_z1, c2_z2, c2_z3;
    wire [31:0] m0_z0, m0_z1, m0_z2, m0_z3;
    wire [31:0] m1_z0, m1_z1, m1_z2, m1_z3;
    wire [31:0] m2_z0, m2_z1, m2_z2, m2_z3;
    wire done, busy, err_zero_divisor;

    wire inv_start;
    wire [31:0] inv_z0, inv_z1, inv_z2, inv_z3;
    wire [31:0] inv_r0, inv_r1, inv_r2, inv_r3;
    wire inv_done, inv_busy, inv_flags_v;

    wire tower_mult_start;
    wire [31:0] tower_mult_a0, tower_mult_a1, tower_mult_a2, tower_mult_a3;
    wire [31:0] tower_mult_b0, tower_mult_b1, tower_mult_b2, tower_mult_b3;
    wire jet_mult_start;
    wire [31:0] jet_mult_a0, jet_mult_a1, jet_mult_a2, jet_mult_a3;
    wire [31:0] jet_mult_b0, jet_mult_b1, jet_mult_b2, jet_mult_b3;
    wire [31:0] mult_r0, mult_r1, mult_r2, mult_r3;
    wire mult_done, mult_busy;

    wire mult_start = tower_mult_start ? tower_mult_start : jet_mult_start;
    wire [31:0] mult_a0 = tower_mult_start ? tower_mult_a0 : jet_mult_a0;
    wire [31:0] mult_a1 = tower_mult_start ? tower_mult_a1 : jet_mult_a1;
    wire [31:0] mult_a2 = tower_mult_start ? tower_mult_a2 : jet_mult_a2;
    wire [31:0] mult_a3 = tower_mult_start ? tower_mult_a3 : jet_mult_a3;
    wire [31:0] mult_b0 = tower_mult_start ? tower_mult_b0 : jet_mult_b0;
    wire [31:0] mult_b1 = tower_mult_start ? tower_mult_b1 : jet_mult_b1;
    wire [31:0] mult_b2 = tower_mult_start ? tower_mult_b2 : jet_mult_b2;
    wire [31:0] mult_b3 = tower_mult_start ? tower_mult_b3 : jet_mult_b3;

    always #5 clk = ~clk;
    always @(posedge clk)
        edge_index <= edge_index + 1;

    spu13_jet_inv u_jet (
        .clk(clk), .rst_n(rst_n), .start(start),
        .c0_z0(c0_z0), .c0_z1(c0_z1), .c0_z2(c0_z2), .c0_z3(c0_z3),
        .c1_z0(c1_z0), .c1_z1(c1_z1), .c1_z2(c1_z2), .c1_z3(c1_z3),
        .c2_z0(c2_z0), .c2_z1(c2_z1), .c2_z2(c2_z2), .c2_z3(c2_z3),
        .m0_z0(m0_z0), .m0_z1(m0_z1), .m0_z2(m0_z2), .m0_z3(m0_z3),
        .m1_z0(m1_z0), .m1_z1(m1_z1), .m1_z2(m1_z2), .m1_z3(m1_z3),
        .m2_z0(m2_z0), .m2_z1(m2_z1), .m2_z2(m2_z2), .m2_z3(m2_z3),
        .done(done), .busy(busy), .err_zero_divisor(err_zero_divisor),
        .inv_start(inv_start),
        .inv_z0(inv_z0), .inv_z1(inv_z1), .inv_z2(inv_z2), .inv_z3(inv_z3),
        .inv_r0(inv_r0), .inv_r1(inv_r1), .inv_r2(inv_r2), .inv_r3(inv_r3),
        .inv_done(inv_done), .inv_busy(inv_busy), .inv_flags_v(inv_flags_v),
        .mult_start(jet_mult_start),
        .mult_a0(jet_mult_a0), .mult_a1(jet_mult_a1),
        .mult_a2(jet_mult_a2), .mult_a3(jet_mult_a3),
        .mult_b0(jet_mult_b0), .mult_b1(jet_mult_b1),
        .mult_b2(jet_mult_b2), .mult_b3(jet_mult_b3),
        .mult_r0(mult_r0), .mult_r1(mult_r1),
        .mult_r2(mult_r2), .mult_r3(mult_r3), .mult_done(mult_done)
    );

    spu13_fp4_inverter u_tower (
        .clk(clk), .rst_n(rst_n), .start(inv_start),
        .z0(inv_z0), .z1(inv_z1), .z2(inv_z2), .z3(inv_z3),
        .inv0(inv_r0), .inv1(inv_r1), .inv2(inv_r2), .inv3(inv_r3),
        .done(inv_done), .busy(inv_busy), .flags_v(inv_flags_v),
        .mult_start(tower_mult_start),
        .mult_a0(tower_mult_a0), .mult_a1(tower_mult_a1),
        .mult_a2(tower_mult_a2), .mult_a3(tower_mult_a3),
        .mult_b0(tower_mult_b0), .mult_b1(tower_mult_b1),
        .mult_b2(tower_mult_b2), .mult_b3(tower_mult_b3),
        .mult_r0(mult_r0), .mult_r1(mult_r1),
        .mult_r2(mult_r2), .mult_r3(mult_r3),
        .mult_done(mult_done), .mult_busy(mult_busy),
        .debug_state(), .debug_start_accept()
    );

    spu13_m31_multiplier u_multiplier (
        .clk(clk), .rst_n(rst_n), .start(mult_start),
        .a0(mult_a0), .a1(mult_a1), .a2(mult_a2), .a3(mult_a3),
        .b0(mult_b0), .b1(mult_b1), .b2(mult_b2), .b3(mult_b3),
        .r0(mult_r0), .r1(mult_r1), .r2(mult_r2), .r3(mult_r3),
        .done(mult_done), .busy(mult_busy), .rns_error()
    );

    task check_class;
        input [8*16-1:0] class_name;
        input integer measured;
        inout integer expected;
        begin
            if (expected < 0)
                expected = measured;
            else if (measured != expected) begin
                failures = failures + 1;
                $display("FAIL class-variance class=%0s expected=%0d got=%0d",
                         class_name, expected, measured);
            end
        end
    endtask

    task run_case;
        input [8*24-1:0] case_name;
        input [1:0] outcome_class; // 0=unit, 1=direct zero, 2=tower singular
        input [31:0] a0,a1,a2,a3, b0,b1,b2,b3, d0,d1,d2,d3;
        integer accept_edge;
        integer done_edge;
        integer latency;
        begin
            @(negedge clk);
            c0_z0=a0; c0_z1=a1; c0_z2=a2; c0_z3=a3;
            c1_z0=b0; c1_z1=b1; c1_z2=b2; c1_z3=b3;
            c2_z0=d0; c2_z1=d1; c2_z2=d2; c2_z3=d3;
            start = 1'b1;
            #1;
            if (busy) begin
                failures = failures + 1;
                $display("FAIL no-accept-ready case=%0s edge=%0d", case_name,
                         edge_index);
            end
            @(posedge clk); #1;
            accept_edge = edge_index;
            @(negedge clk);
            start = 1'b0;
            while (!done) begin
                @(posedge clk); #1;
            end
            done_edge = edge_index;
            latency = done_edge - accept_edge;

            if ((outcome_class == 0 && err_zero_divisor) ||
                (outcome_class != 0 && !err_zero_divisor)) begin
                failures = failures + 1;
                $display("FAIL flags case=%0s class=%0d err=%0d", case_name,
                         outcome_class, err_zero_divisor);
            end
            case (outcome_class)
                0: check_class("unit", latency, unit_latency);
                1: check_class("direct_zero", latency, direct_zero_latency);
                2: check_class("tower_singular", latency,
                               tower_singular_latency);
            endcase
            $display("JET_LATENCY class=%0s case=%0s accept_edge=%0d done_edge=%0d delta=%0d error=%0d",
                     outcome_class == 0 ? "unit" :
                     (outcome_class == 1 ? "direct_zero" : "tower_singular"),
                     case_name, accept_edge, done_edge, latency,
                     err_zero_divisor);
            @(posedge clk); #1;
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        start = 1'b0;
        edge_index = 0;
        failures = 0;
        unit_latency = -1;
        direct_zero_latency = -1;
        tower_singular_latency = -1;
        c0_z0=0; c0_z1=0; c0_z2=0; c0_z3=0;
        c1_z0=0; c1_z1=0; c1_z2=0; c1_z3=0;
        c2_z0=0; c2_z1=0; c2_z2=0; c2_z3=0;

        repeat (4) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        $display("HISTORICAL_RTL_COMMIT f1e4dbf06aa1163cc98005feb063ec8aae7c933a");
        $display("CYCLE_CONVENTION done_rising_edge_index - accepted_start_rising_edge_index");
        $display("BACKEND parallel shared spu13_m31_multiplier.v uncontended");

        run_case("scalar_five", 0,
                 5,0,0,0, 0,0,0,0, 0,0,0,0);
        run_case("scalar_jet", 0,
                 5,0,0,0, 3,0,0,0, 2,0,0,0);
        run_case("scalar_three", 0,
                 3,0,0,0, 1,0,0,0, 1,0,0,0);
        run_case("direct_zero", 1,
                 0,0,0,0, 1,0,0,0, 0,0,0,0);
        run_case("nonzero_zero_divisor", 2,
                 32'd753804466,0,0,1, 0,0,0,0, 0,0,0,0);

        $display("SUMMARY jet_unit=%0d jet_direct_zero=%0d jet_tower_singular=%0d tower_unit=83 wrapper_shadow_overhead=%0d",
                 unit_latency, direct_zero_latency, tower_singular_latency,
                 unit_latency - 83);
        if (failures == 0)
            $display("PASS historical_jet_inv_latency (%0d failures)", failures);
        else
            $display("FAIL historical_jet_inv_latency (%0d failures)", failures);
        $finish;
    end
endmodule
