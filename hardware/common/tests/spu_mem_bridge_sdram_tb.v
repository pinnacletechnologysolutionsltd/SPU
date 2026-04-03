// spu_mem_bridge_sdram_tb.v
// Tests spu_mem_bridge_sdram with a behavioral W9825G6KH-6 SDRAM model.
// Cases:
//   1. Init sequence: mem_ready asserts after JEDEC power-up
//   2. Burst write: 52 words written, mem_burst_done fires
//   3. Burst read: 52 words read back, data matches written pattern
//   4. Back-to-back: second write-read cycle works without reset

`timescale 1ns/1ps

module spu_mem_bridge_sdram_tb;

    // -------------------------------------------------------------------------
    // Clock (50 MHz = 20 ns period)
    // -------------------------------------------------------------------------
    reg clk = 0;
    always #10 clk = ~clk;

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

    wire         sdram_clk, sdram_cke, sdram_cs_n;
    wire         sdram_ras_n, sdram_cas_n, sdram_we_n;
    wire [1:0]   sdram_ba;
    wire [12:0]  sdram_addr_pin;
    wire [15:0]  sdram_dq;

    // -------------------------------------------------------------------------
    // DUT — T_INIT=8 so init finishes in ~20 cycles for simulation
    // -------------------------------------------------------------------------
    spu_mem_bridge_sdram #(.T_INIT(8)) dut (
        .clk             (clk),
        .reset           (reset),
        .mem_ready       (mem_ready),
        .mem_burst_rd    (mem_burst_rd),
        .mem_burst_wr    (mem_burst_wr),
        .mem_addr        (mem_addr),
        .mem_rd_manifold (mem_rd_manifold),
        .mem_wr_manifold (mem_wr_manifold),
        .mem_burst_done  (mem_burst_done),
        .sdram_clk       (sdram_clk),
        .sdram_cke       (sdram_cke),
        .sdram_cs_n      (sdram_cs_n),
        .sdram_ras_n     (sdram_ras_n),
        .sdram_cas_n     (sdram_cas_n),
        .sdram_we_n      (sdram_we_n),
        .sdram_ba        (sdram_ba),
        .sdram_addr      (sdram_addr_pin),
        .sdram_dq        (sdram_dq)
    );

    // -------------------------------------------------------------------------
    // Behavioral SDRAM model
    //
    // DQ output is COMBINATORIAL from the pipeline stage register so that
    // data is visible to the DUT in the SAME cycle the pipeline stage fires.
    // This matches real SDRAM behaviour: output data is valid on the rising
    // edge CAS_LAT cycles after the READ command.
    // -------------------------------------------------------------------------
    reg  [15:0] sdram_mem [0:63];   // 64-word scratch (covers one 52-word burst)

    // 3-stage CAS pipeline (registered per rising edge)
    reg [5:0]  cas_col   [0:2];
    reg        cas_valid [0:2];

    wire [2:0] sdram_cmd = {sdram_ras_n, sdram_cas_n, sdram_we_n};
    localparam MCMD_READ  = 3'b101;
    localparam MCMD_WRITE = 3'b100;

    integer k;
    initial begin
        for (k = 0; k < 3; k = k + 1) begin cas_col[k] = 0; cas_valid[k] = 0; end
        for (k = 0; k < 64; k = k + 1) sdram_mem[k] = 0;
    end

    always @(posedge sdram_clk) begin
        // Shift pipeline (oldest stage = [2])
        cas_col[2]   <= cas_col[1];   cas_valid[2] <= cas_valid[1];
        cas_col[1]   <= cas_col[0];   cas_valid[1] <= cas_valid[0];
        cas_col[0]   <= 6'd0;         cas_valid[0] <= 1'b0;

        if (!sdram_cs_n) begin
            if (sdram_cmd == MCMD_READ) begin
                cas_col[0]   <= sdram_addr_pin[5:0];
                cas_valid[0] <= 1'b1;
            end
            if (sdram_cmd == MCMD_WRITE)
                sdram_mem[sdram_addr_pin[5:0]] <= sdram_dq;
        end
    end

    // Combinatorial DQ output: drives bus in the same cycle the pipeline fires.
    // The DUT samples sdram_dq on the posedge CAS_LAT cycles after READ.
    reg  [15:0] dq_out;
    reg          dq_en;
    assign sdram_dq = dq_en ? dq_out : 16'hzzzz;

    always @(*) begin
        if (cas_valid[2]) begin
            dq_out = sdram_mem[cas_col[2]];
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
        $display("spu_mem_bridge_sdram Testbench");
        $display("============================================================");

        @(posedge clk); @(posedge clk); @(posedge clk);
        reset = 0;

        // -----------------------------------------------------------------
        // Case 1: Init sequence — mem_ready asserts after JEDEC power-up
        // -----------------------------------------------------------------
        $display("--- Case 1: Init complete ---");
        wait(mem_ready == 1'b1);
        @(posedge clk); #1;
        if (mem_ready === 1'b1) pass("sdram-bridge: mem_ready after init");
        else                     fail("sdram-bridge: mem_ready after init", 0, 1);

        // -----------------------------------------------------------------
        // Case 2: Burst write — 52 words, pattern word[i] = 0xA000 + i
        // -----------------------------------------------------------------
        $display("--- Case 2: Burst write ---");
        for (i = 0; i < 52; i = i + 1)
            mem_wr_manifold[i*16 +: 16] = 16'hA000 + i;
        mem_addr = 24'h000000;
        @(posedge clk); #1;
        mem_burst_wr = 1;
        @(posedge clk); #1;
        mem_burst_wr = 0;
        wait(mem_burst_done == 1'b1);
        @(posedge clk); #1;   // one cycle after done: should be de-asserted

        if (mem_burst_done === 1'b0) pass("sdram-bridge: burst_done 1-cycle pulse");
        else                          fail("sdram-bridge: burst_done 1-cycle pulse", 1, 0);

        if (sdram_mem[0]  === 16'hA000) pass("sdram-bridge: write word[0]  = 0xA000");
        else                             fail("sdram-bridge: write word[0]  = 0xA000",
                                              {48'd0, sdram_mem[0]},  64'hA000);
        if (sdram_mem[51] === 16'hA033) pass("sdram-bridge: write word[51] = 0xA033");
        else                             fail("sdram-bridge: write word[51] = 0xA033",
                                              {48'd0, sdram_mem[51]}, 64'hA033);

        // -----------------------------------------------------------------
        // Case 3: Burst read — read back written pattern
        // -----------------------------------------------------------------
        $display("--- Case 3: Burst read ---");
        mem_addr = 24'h000000;
        @(posedge clk); #1;
        mem_burst_rd = 1;
        @(posedge clk); #1;
        mem_burst_rd = 0;
        wait(mem_burst_done == 1'b1);
        @(posedge clk); #1;

        if (mem_rd_manifold[15:0]    === 16'hA000) pass("sdram-bridge: read word[0]  = 0xA000");
        else                                         fail("sdram-bridge: read word[0]  = 0xA000",
                                                           {48'd0, mem_rd_manifold[15:0]}, 64'hA000);
        if (mem_rd_manifold[831:816] === 16'hA033) pass("sdram-bridge: read word[51] = 0xA033");
        else                                         fail("sdram-bridge: read word[51] = 0xA033",
                                                           {48'd0, mem_rd_manifold[831:816]}, 64'hA033);
        begin : full_check
            reg match;
            match = 1;
            for (i = 0; i < 52; i = i + 1)
                if (mem_rd_manifold[i*16 +: 16] !== (16'hA000 + i)) match = 0;
            if (match) pass("sdram-bridge: all 52 words match write pattern");
            else        fail("sdram-bridge: all 52 words match write pattern", 0, 1);
        end

        // -----------------------------------------------------------------
        // Case 4: Back-to-back cycle (no reset)
        // -----------------------------------------------------------------
        $display("--- Case 4: Back-to-back cycle ---");
        for (i = 0; i < 52; i = i + 1)
            mem_wr_manifold[i*16 +: 16] = 16'hB000 + i;
        mem_addr = 24'h000000;
        @(posedge clk); #1;
        mem_burst_wr = 1;
        @(posedge clk); #1;
        mem_burst_wr = 0;
        wait(mem_burst_done == 1'b1);
        @(posedge clk); #1;
        mem_burst_rd = 1;
        @(posedge clk); #1;
        mem_burst_rd = 0;
        wait(mem_burst_done == 1'b1);
        @(posedge clk); #1;

        if (mem_rd_manifold[15:0] === 16'hB000) pass("sdram-bridge: back-to-back word[0] = 0xB000");
        else                                      fail("sdram-bridge: back-to-back word[0] = 0xB000",
                                                        {48'd0, mem_rd_manifold[15:0]}, 64'hB000);
        if (mem_rd_manifold[815:800] === 16'hB033) pass("sdram-bridge: back-to-back word[50] = 0xB033... wait");
        // Word 51: bits [831:816]
        if (mem_rd_manifold[831:816] === 16'hB033) pass("sdram-bridge: back-to-back word[51] = 0xB033");
        else                                         fail("sdram-bridge: back-to-back word[51] = 0xB033",
                                                           {48'd0, mem_rd_manifold[831:816]}, 64'hB033);

        // -----------------------------------------------------------------
        $display("============================================================");
        $display("Result: %0d/%0d passed %s",
                  pass_count, pass_count+fail_count,
                  (fail_count == 0) ? "PASS" : "FAIL");
        $display("============================================================");
        $finish;
    end

    initial begin #500000; $display("TIMEOUT"); $finish; end

endmodule
