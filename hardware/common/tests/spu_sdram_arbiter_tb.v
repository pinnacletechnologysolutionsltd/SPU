// spu_sdram_arbiter_tb.v — Testbench for spu_sdram_arbiter (v1.0)
// CC0 1.0 Universal.
//
// Tests:
//   1. Core 0 request → granted, bank bit 23 = 0
//   2. Core 1 request (core 0 idle) → granted, bank bit 23 = 1
//   3. Simultaneous requests → core 0 wins
//   4. Done routing: only granted core sees burst_done
//   5. c1_mem_ready suppressed while core 0 is requesting

`timescale 1ns/1ps
`include "spu_arch_defines.vh"

module spu_sdram_arbiter_tb;

    reg clk, rst_n;
    initial begin clk = 0; rst_n = 0; #12 rst_n = 1; end
    always #5 clk = ~clk;

    // Core 0 drives
    reg  c0_rd, c0_wr;
    reg  [`MEM_ADDR_WIDTH-1:0] c0_addr;
    reg  [`MANIFOLD_WIDTH-1:0] c0_wdat;

    // Core 1 drives
    reg  c1_rd, c1_wr;
    reg  [`MEM_ADDR_WIDTH-1:0] c1_addr;
    reg  [`MANIFOLD_WIDTH-1:0] c1_wdat;

    // SDRAM controller responses
    reg  sdram_ready, sdram_done;
    reg  [`MANIFOLD_WIDTH-1:0] sdram_rdat;

    // DUT outputs
    wire c0_ready, c0_done;
    wire [`MANIFOLD_WIDTH-1:0] c0_rdat;
    wire c1_ready, c1_done;
    wire [`MANIFOLD_WIDTH-1:0] c1_rdat;
    wire sdram_brd, sdram_bwr;
    wire [`MEM_ADDR_WIDTH-1:0] sdram_addr_out;
    wire [`MANIFOLD_WIDTH-1:0] sdram_wdat_out;

    spu_sdram_arbiter u_arb (
        .clk                    (clk),
        .rst_n                  (rst_n),
        .c0_mem_ready           (c0_ready),
        .c0_mem_burst_rd        (c0_rd),
        .c0_mem_burst_wr        (c0_wr),
        .c0_mem_addr            (c0_addr),
        .c0_mem_rd_manifold     (c0_rdat),
        .c0_mem_wr_manifold     (c0_wdat),
        .c0_mem_burst_done      (c0_done),
        .c1_mem_ready           (c1_ready),
        .c1_mem_burst_rd        (c1_rd),
        .c1_mem_burst_wr        (c1_wr),
        .c1_mem_addr            (c1_addr),
        .c1_mem_rd_manifold     (c1_rdat),
        .c1_mem_wr_manifold     (c1_wdat),
        .c1_mem_burst_done      (c1_done),
        .sdram_mem_ready        (sdram_ready),
        .sdram_mem_burst_rd     (sdram_brd),
        .sdram_mem_burst_wr     (sdram_bwr),
        .sdram_mem_addr         (sdram_addr_out),
        .sdram_mem_rd_manifold  (sdram_rdat),
        .sdram_mem_wr_manifold  (sdram_wdat_out),
        .sdram_mem_burst_done   (sdram_done)
    );

    integer fail = 0;

    task check;
        input cond;
        input [63:0] tag;
        begin
            if (!cond) begin
                $display("FAIL tag=%0d", tag);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        c0_rd = 0; c0_wr = 0; c0_addr = 0; c0_wdat = 0;
        c1_rd = 0; c1_wr = 0; c1_addr = 0; c1_wdat = 0;
        sdram_ready = 0; sdram_done = 0; sdram_rdat = 0;
        @(posedge rst_n); @(posedge clk); #1;

        // ── Test 1: Core 0 burst read ─────────────────────────────── //
        sdram_ready = 1;
        c0_addr = 24'h001234; // bank bits [23:22]=0 already
        @(posedge clk); #1;
        c0_rd = 1;
        @(posedge clk); #1;  // grant registers core 0
        // sdram_burst_rd should now forward c0_rd
        check(sdram_brd == 1, 1);
        check(sdram_bwr == 0, 2);
        // Bank bit 23 must be 0
        check(sdram_addr_out[`MEM_ADDR_WIDTH-1] == 1'b0, 3);
        // Core 1 must NOT see ready (core 0 requesting)
        check(c1_ready == 0, 4);
        // Simulate SDRAM busy
        sdram_ready = 0;
        @(posedge clk); #1;
        // Simulate burst complete
        sdram_done = 1;
        @(posedge clk); #1;
        // c0_done should fire, c1_done must not
        check(c0_done == 1, 5);
        check(c1_done == 0, 6);
        sdram_done = 0;
        c0_rd = 0;
        sdram_ready = 1;
        @(posedge clk); #1;

        // ── Test 2: Core 1 burst read when core 0 idle ───────────── //
        c1_addr = 24'h005678;
        @(posedge clk); #1;
        c1_rd = 1;
        @(posedge clk); #1;  // grant registers core 1
        check(sdram_brd == 1, 10);
        check(sdram_bwr == 0, 11);
        // Bank bit 23 must be 1 (core 1 → banks 2-3)
        check(sdram_addr_out[`MEM_ADDR_WIDTH-1] == 1'b1, 12);
        sdram_ready = 0;
        @(posedge clk); #1;
        sdram_done = 1;
        @(posedge clk); #1;
        check(c1_done == 1, 13);
        check(c0_done == 0, 14);
        sdram_done = 0;
        c1_rd = 0;
        sdram_ready = 1;
        @(posedge clk); #1;

        // ── Test 3: Simultaneous requests → core 0 wins ──────────── //
        c0_rd = 1; c0_addr = 24'h000000;
        c1_rd = 1; c1_addr = 24'h000000;
        @(posedge clk); #1;  // both registered, grant evaluates c0 first
        @(posedge clk); #1;  // grant=0 now (c0 priority), sdram_burst_rd from c0
        check(sdram_brd == 1, 20);
        // Bank must be 0 (core 0 win)
        check(sdram_addr_out[`MEM_ADDR_WIDTH-1] == 1'b0, 21);
        // c1_ready suppressed while c0 requesting
        check(c1_ready == 0, 22);
        sdram_ready = 0;
        @(posedge clk); #1;
        sdram_done = 1;
        @(posedge clk); #1;
        // Only core 0 sees done
        check(c0_done == 1, 23);
        check(c1_done == 0, 24);
        sdram_done = 0;
        c0_rd = 0;
        sdram_ready = 1;
        // Core 1 still requesting — should win now
        @(posedge clk); #1;
        @(posedge clk); #1;  // grant switches to 1
        check(sdram_brd == 1, 25);
        check(sdram_addr_out[`MEM_ADDR_WIDTH-1] == 1'b1, 26);
        sdram_ready = 0;
        @(posedge clk); #1;
        sdram_done = 1;
        @(posedge clk); #1;
        check(c1_done == 1, 27);
        check(c0_done == 0, 28);
        sdram_done = 0;
        c1_rd = 0;
        sdram_ready = 1;
        @(posedge clk); #2;

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d errors)", fail);
        $finish;
    end

    initial #5000 begin $display("FAIL (timeout)"); $finish; end

endmodule
