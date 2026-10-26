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

        // ═══════════════════════════════════════════════════════════
        // Scenario E: 5-way collision — verify serial dispatch and
        //             stall clears only on last element
        // ═══════════════════════════════════════════════════════════
        activation = (64'd1 << 3) | (64'd1 << 12) | (64'd1 << 25) | (64'd1 << 40) | (64'd1 << 63);
        #10;
        check(bus_valid && selected_k == 6'd3 && pipeline_stall, "E1: 5-way cycle1 bit3");
        #10;
        check(bus_valid && selected_k == 6'd12 && pipeline_stall, "E2: 5-way cycle2 bit12");
        #10;
        check(bus_valid && selected_k == 6'd25 && pipeline_stall, "E3: 5-way cycle3 bit25");
        #10;
        check(bus_valid && selected_k == 6'd40 && pipeline_stall, "E4: 5-way cycle4 bit40");
        #10;
        check(bus_valid && selected_k == 6'd63 && !pipeline_stall, "E5: 5-way cycle5 bit63 done");
        activation = 64'd0; #20;

        // ═══════════════════════════════════════════════════════════
        // Scenario F: Single node at boundaries (bit 0, bit 63)
        // ═══════════════════════════════════════════════════════════
        activation = 64'd1;  // bit 0
        #10;
        check(bus_valid && selected_k == 6'd0 && !pipeline_stall, "F1: boundary bit0");
        activation = 64'd0; #20;

        activation = (64'd1 << 63);  // bit 63
        #10;
        check(bus_valid && selected_k == 6'd63 && !pipeline_stall, "F2: boundary bit63");
        activation = 64'd0; #20;

        // ═══════════════════════════════════════════════════════════
        // Scenario G: Back-to-back collisions — rapid-fire dispatch
        // Dispatch a collision, drain, then immediately dispatch another
        // ═══════════════════════════════════════════════════════════
        // Burst 1: 2-way
        activation = (64'd1 << 5) | (64'd1 << 17);
        #10;
        check(bus_valid && selected_k == 6'd5 && pipeline_stall, "G1: burst1 cycle1 bit5");
        #10;
        check(bus_valid && selected_k == 6'd17 && !pipeline_stall, "G2: burst1 cycle2 bit17 done");
        activation = 64'd0; #10;

        // Burst 2: 4-way immediately after
        activation = (64'd1 << 1) | (64'd1 << 8) | (64'd1 << 22) | (64'd1 << 44);
        #10;
        check(bus_valid && selected_k == 6'd1 && pipeline_stall, "G3: burst2 cycle1 bit1");
        #10;
        check(bus_valid && selected_k == 6'd8 && pipeline_stall, "G4: burst2 cycle2 bit8");
        #10;
        check(bus_valid && selected_k == 6'd22 && pipeline_stall, "G5: burst2 cycle3 bit22");
        #10;
        check(bus_valid && selected_k == 6'd44 && !pipeline_stall, "G6: burst2 cycle4 bit44 done");
        activation = 64'd0; #20;

        if (test_pass == test_total)
            $display("PASS: btu_collision_tb (%0d/%0d)", test_pass, test_total);
        else
            $display("FAIL: btu_collision_tb (%0d/%0d)", test_pass, test_total);
        $finish;
    end

endmodule
