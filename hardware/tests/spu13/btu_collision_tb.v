`timescale 1ns / 1ps

// btu_collision_tb.v — Stress-test the BTU collision resolver
//
// Exercises multi-saddle scenarios through spu_btu_collision_resolver:
//   A) Single node activation → direct dispatch
//   B) Two simultaneous activations → priority queue + bubble stall
//   C) Three simultaneous activations → serial dispatch
//   D) Zero activation → idle, no stall

module btu_collision_tb;

    reg clk, rst_n;
    reg [63:0] activation;
    wire pipeline_stall;
    wire [5:0] selected_k;
    wire bus_valid;

    spu_btu_collision_resolver uut (
        .clk(clk), .rst_n(rst_n),
        .neuron_activation_lines(activation),
        .pipeline_stall(pipeline_stall),
        .selected_row_k(selected_k),
        .bus_valid(bus_valid)
    );

    always #5 clk = ~clk;

    integer test_pass, test_total;
    task check;
        input ok;
        input [255:0] msg;
        begin
            test_total = test_total + 1;
            if (ok) test_pass = test_pass + 1;
            else $display("FAIL: %0s", msg);
        end
    endtask

    initial begin
        clk = 0; rst_n = 0;
        test_pass = 0; test_total = 0;
        activation = 64'd0;
        #20 rst_n = 1; #10;

        // ── Scenario A: Single node (bit 3) ───────────────────────
        activation = 64'd1 << 3;  // bit 3 only
        #10;  // one cycle
        check(bus_valid && selected_k == 6'd3 && !pipeline_stall, "A: single node dispatch");
        activation = 64'd0; #20;  // drain

        // ── Scenario B: Two nodes (bits 7 and 15) ─────────────────
        activation = (64'd1 << 7) | (64'd1 << 15);
        #10;  // cycle 1: lowest (bit 7) dispatched, bit 15 queued
        check(bus_valid && selected_k == 6'd7 && pipeline_stall, "B1: two-node cycle1 lowest");
        #10;  // cycle 2: bit 15 dispatched from queue
        check(bus_valid && selected_k == 6'd15 && !pipeline_stall, "B2: two-node cycle2 queued");
        activation = 64'd0; #20;

        // ── Scenario C: Three nodes (bits 0, 33, 63) ──────────────
        activation = 64'd1 | (64'd1 << 33) | (64'd1 << 63);
        #10;  // cycle 1: bit 0 (lowest)
        check(bus_valid && selected_k == 6'd0 && pipeline_stall, "C1: three-node cycle1 bit0");
        #10;  // cycle 2: bit 33
        check(bus_valid && selected_k == 6'd33 && pipeline_stall, "C2: three-node cycle2 bit33");
        #10;  // cycle 3: bit 63
        check(bus_valid && selected_k == 6'd63 && !pipeline_stall, "C3: three-node cycle3 bit63");
        activation = 64'd0; #20;

        // ── Scenario D: Zero activation ───────────────────────────
        activation = 64'd0;
        #10;
        check(!bus_valid && !pipeline_stall, "D: zero activation idle");
        #10;

        if (test_pass == test_total)
            $display("PASS: btu_collision_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: btu_collision_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
