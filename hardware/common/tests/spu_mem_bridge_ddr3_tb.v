// spu_mem_bridge_ddr3_tb.v
// Tests spu_mem_bridge_ddr3 with a behavioural DDR3 memory model.
// Cases:
//   1. Init sequence: mem_ready asserts after DDR3 power-up
//   2. Burst write: 52 words written, mem_burst_done fires
//   3. Burst read: 52 words read back, data matches written pattern
//   4. Back-to-back: second write-read cycle works without reset
//
// Timing model (matches spu_mem_bridge_sdram_tb.v pattern):
//   CAS_LAT=5: 5-stage pipeline in TB, combinatorial DQ output.
//   Effective read offset = CAS_LAT+1 = 6 (matches DUT's WR_OFFSET).
//
// CC0 1.0 Universal.

`include "spu_arch_defines.vh"
`timescale 1ns/1ps

module spu_mem_bridge_ddr3_tb;

    // -------------------------------------------------------------------------
    // Clock (24 MHz = 41.667 ns period)
    // -------------------------------------------------------------------------
    reg clk   = 0;
    always #20.833 clk = ~clk;

    integer pass_count = 0;
    integer fail_count = 0;
    integer i;

    task pass; input [127:0] name;
        begin $display("  PASS  %0s", name); pass_count = pass_count + 1; end
    endtask
    task fail; input [127:0] name; input [63:0] got; input [63:0] exp;
        begin $display("  FAIL  %0s  got=%h exp=%h", name, got, exp); fail_count = fail_count + 1; end
    endtask

    // -------------------------------------------------------------------------
    // DUT ports
    // -------------------------------------------------------------------------
    reg          reset        = 1;
    reg          mem_burst_rd = 0;
    reg          mem_burst_wr = 0;
    reg  [23:0]  mem_addr     = 24'h000000;
    reg  [831:0] mem_wr_manifold = 0;
    wire [831:0] mem_rd_manifold;
    wire         mem_ready;
    wire         mem_burst_done;

    wire         ddr3_ck_p;
    wire         ddr3_ck_n;
    wire         ddr3_cke;
    wire         ddr3_cs_n;
    wire         ddr3_ras_n;
    wire         ddr3_cas_n;
    wire         ddr3_we_n;
    wire         ddr3_odt;
    wire         ddr3_reset_n;
    wire [2:0]   ddr3_ba;
    wire [13:0]  ddr3_addr_w;
    wire [15:0]  ddr3_dq;
    wire [1:0]   ddr3_dqs_p;
    wire [1:0]   ddr3_dqs_n;
    wire [1:0]   ddr3_dm;

    // -------------------------------------------------------------------------
    // DUT — short timing parameters for simulation
    // -------------------------------------------------------------------------
    spu_mem_bridge_ddr3 #(
        .T_RESET_CYCLES (8),
        .T_INIT_CKE     (8),
        .T_TXPR         (4),
        .T_MRD          (4),
        .T_MOD          (4),
        .T_ZQINIT       (8),
        .T_REFI         (1000)   // large interval — no refresh fires during short TB
    ) dut (
        .clk             (clk),
        .reset           (reset),
        .mem_ready       (mem_ready),
        .mem_burst_rd    (mem_burst_rd),
        .mem_burst_wr    (mem_burst_wr),
        .mem_addr        (mem_addr),
        .mem_rd_manifold (mem_rd_manifold),
        .mem_wr_manifold (mem_wr_manifold),
        .mem_burst_done  (mem_burst_done),
        .ddr3_ck_p       (ddr3_ck_p),
        .ddr3_ck_n       (ddr3_ck_n),
        .ddr3_cke        (ddr3_cke),
        .ddr3_cs_n       (ddr3_cs_n),
        .ddr3_ras_n      (ddr3_ras_n),
        .ddr3_cas_n      (ddr3_cas_n),
        .ddr3_we_n       (ddr3_we_n),
        .ddr3_odt        (ddr3_odt),
        .ddr3_reset_n    (ddr3_reset_n),
        .ddr3_ba         (ddr3_ba),
        .ddr3_addr       (ddr3_addr_w),
        .ddr3_dq         (ddr3_dq),
        .ddr3_dqs_p      (ddr3_dqs_p),
        .ddr3_dqs_n      (ddr3_dqs_n),
        .ddr3_dm         (ddr3_dm)
    );

    // -------------------------------------------------------------------------
    // Behavioural DDR3 memory model
    //
    // DQ output is COMBINATORIAL from the pipeline stage register so that
    // data is visible to the DUT in the same cycle the pipeline stage fires.
    // This matches the SDRAM TB pattern; effective read offset = CAS_LAT+1=6.
    //
    // Write capture: DUT drives ddr3_dq (dq_en=1) when issuing CMD_WRITE.
    // Due to NBA timing the command and data are both visible to the TB model
    // one posedge after the DUT issues the command.
    // -------------------------------------------------------------------------
    localparam CAS_LAT   = 5;
    localparam BURST_LEN = `MANIFOLD_WIDTH / 16;  // 52

    reg [15:0] ddr3_mem [0:127];  // 128-word scratch space

    // CAS_LAT-stage pipeline (index 0 = newest, index CAS_LAT-1 = oldest)
    reg [8:0]  cas_col   [0:CAS_LAT-1];
    reg        cas_valid [0:CAS_LAT-1];

    wire [3:0] ddr3_cmd4 = {ddr3_cs_n, ddr3_ras_n, ddr3_cas_n, ddr3_we_n};
    localparam CMD4_READ  = 4'b0101;
    localparam CMD4_WRITE = 4'b0100;

    integer k;
    initial begin
        for (k = 0; k < CAS_LAT; k = k + 1) begin
            cas_col[k]   = 0;
            cas_valid[k] = 0;
        end
        for (k = 0; k < 128; k = k + 1) ddr3_mem[k] = 0;
    end

    always @(posedge ddr3_ck_p) begin : ddr3_model
        integer p;
        // Shift pipeline: oldest stage = [CAS_LAT-1]
        for (p = CAS_LAT-1; p > 0; p = p - 1) begin
            cas_col[p]   <= cas_col[p-1];
            cas_valid[p] <= cas_valid[p-1];
        end
        cas_col[0]   <= 9'd0;
        cas_valid[0] <= 1'b0;

        if (!ddr3_cs_n) begin
            if (ddr3_cmd4 == CMD4_READ) begin
                cas_col[0]   <= ddr3_addr_w[8:0];
                cas_valid[0] <= 1'b1;
            end
            if (ddr3_cmd4 == CMD4_WRITE)
                ddr3_mem[ddr3_addr_w[8:0]] <= ddr3_dq;
        end
    end

    // Combinatorial DQ output: drives bus as soon as pipeline fires
    reg  [15:0] dq_out;
    reg          dq_en;
    assign ddr3_dq = dq_en ? dq_out : 16'hzzzz;

    always @(*) begin
        if (cas_valid[CAS_LAT-1]) begin
            dq_out = ddr3_mem[cas_col[CAS_LAT-1]];
            dq_en  = 1;
        end else begin
            dq_out = 16'h0;
            dq_en  = 0;
        end
    end

    // -------------------------------------------------------------------------
    // Test stimulus
    // -------------------------------------------------------------------------
    initial begin
        $display("============================================================");
        $display("spu_mem_bridge_ddr3 Testbench");
        $display("============================================================");

        @(posedge clk); @(posedge clk); @(posedge clk);
        reset = 0;

        // -----------------------------------------------------------------
        // Case 1: Init sequence — mem_ready asserts after DDR3 power-up
        // -----------------------------------------------------------------
        $display("--- Case 1: Init complete ---");
        wait (mem_ready == 1'b1);
        @(posedge clk); #1;
        if (mem_ready === 1'b1) pass("ddr3-bridge: mem_ready after init");
        else                     fail("ddr3-bridge: mem_ready after init", 0, 1);

        // -----------------------------------------------------------------
        // Case 2: Burst write — 52 words, pattern word[i] = 0xA000 + i
        // -----------------------------------------------------------------
        $display("--- Case 2: Burst write ---");
        for (i = 0; i < BURST_LEN; i = i + 1)
            mem_wr_manifold[i*16 +: 16] = 16'hA000 + i;
        mem_addr = 24'h000000;
        @(posedge clk); #1;
        mem_burst_wr = 1;
        @(posedge clk); #1;
        mem_burst_wr = 0;
        wait (mem_burst_done == 1'b1);
        @(posedge clk); #1;

        if (mem_burst_done === 1'b0) pass("ddr3-bridge: burst_done 1-cycle pulse");
        else                          fail("ddr3-bridge: burst_done 1-cycle pulse", 1, 0);

        if (ddr3_mem[0]  === 16'hA000) pass("ddr3-bridge: write word[0]  = 0xA000");
        else                            fail("ddr3-bridge: write word[0]  = 0xA000",
                                             {48'd0, ddr3_mem[0]}, 64'hA000);
        if (ddr3_mem[51] === 16'hA033) pass("ddr3-bridge: write word[51] = 0xA033");
        else                            fail("ddr3-bridge: write word[51] = 0xA033",
                                             {48'd0, ddr3_mem[51]}, 64'hA033);

        // -----------------------------------------------------------------
        // Case 3: Burst read — read back the written pattern
        // -----------------------------------------------------------------
        $display("--- Case 3: Burst read ---");
        mem_addr = 24'h000000;
        @(posedge clk); #1;
        mem_burst_rd = 1;
        @(posedge clk); #1;
        mem_burst_rd = 0;
        wait (mem_burst_done == 1'b1);
        @(posedge clk); #1;

        if (mem_rd_manifold[15:0]    === 16'hA000) pass("ddr3-bridge: read word[0]  = 0xA000");
        else                                         fail("ddr3-bridge: read word[0]  = 0xA000",
                                                          {48'd0, mem_rd_manifold[15:0]}, 64'hA000);
        if (mem_rd_manifold[831:816] === 16'hA033) pass("ddr3-bridge: read word[51] = 0xA033");
        else                                         fail("ddr3-bridge: read word[51] = 0xA033",
                                                          {48'd0, mem_rd_manifold[831:816]}, 64'hA033);
        begin : full_check
            reg match;
            match = 1;
            for (i = 0; i < BURST_LEN; i = i + 1)
                if (mem_rd_manifold[i*16 +: 16] !== (16'hA000 + i)) match = 0;
            if (match) pass("ddr3-bridge: all 52 words match write pattern");
            else        fail("ddr3-bridge: all 52 words match write pattern", 0, 1);
        end

        // -----------------------------------------------------------------
        // Case 4: Back-to-back (no reset)
        // -----------------------------------------------------------------
        $display("--- Case 4: Back-to-back cycle ---");
        for (i = 0; i < BURST_LEN; i = i + 1)
            mem_wr_manifold[i*16 +: 16] = 16'hB000 + i;
        mem_addr = 24'h000000;
        @(posedge clk); #1;
        mem_burst_wr = 1;
        @(posedge clk); #1;
        mem_burst_wr = 0;
        wait (mem_burst_done == 1'b1);
        @(posedge clk); #1;
        mem_burst_rd = 1;
        @(posedge clk); #1;
        mem_burst_rd = 0;
        wait (mem_burst_done == 1'b1);
        @(posedge clk); #1;

        if (mem_rd_manifold[15:0]    === 16'hB000) pass("ddr3-bridge: back-to-back word[0]  = 0xB000");
        else                                         fail("ddr3-bridge: back-to-back word[0]  = 0xB000",
                                                          {48'd0, mem_rd_manifold[15:0]}, 64'hB000);
        if (mem_rd_manifold[831:816] === 16'hB033) pass("ddr3-bridge: back-to-back word[51] = 0xB033");
        else                                         fail("ddr3-bridge: back-to-back word[51] = 0xB033",
                                                          {48'd0, mem_rd_manifold[831:816]}, 64'hB033);

        // -----------------------------------------------------------------
        $display("============================================================");
        $display("Result: %0d/%0d passed %s",
                  pass_count, pass_count+fail_count,
                  (fail_count == 0) ? "PASS" : "FAIL");
        $display("============================================================");
        $finish;
    end

    initial begin #5_000_000; $display("FAIL: timeout"); $finish; end

endmodule
