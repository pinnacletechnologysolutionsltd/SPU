// spu_psram_dual_tb.v — Testbench: spu_psram_dual
// Verifies bank routing, init sequencing, and burst signalling.
// Both chips init in parallel; requests route to the correct bank.

`timescale 1ns/1ps

module spu_psram_dual_tb;

    reg         clk   = 0;
    reg         reset = 1;

    // Manifold bus
    reg  [23:0]  mem_addr;
    reg          mem_burst_rd, mem_burst_wr;
    reg          mem_rd_en, mem_wr_en;
    reg  [15:0]  mem_wr_data;
    reg  [831:0] mem_wr_manifold;

    wire         mem_ready, mem_burst_done, mem_init_done;
    wire [831:0] mem_rd_manifold;
    wire [15:0]  mem_rd_data;

    // PSRAM pin stubs (let controller drive; float when controller releases)
    wire         psram0_ce_n, psram0_clk;
    wire [3:0]   psram0_dq;
    wire         psram1_ce_n, psram1_clk;
    wire [3:0]   psram1_dq;

    spu_psram_dual u_dut (
        .clk              (clk),
        .reset            (reset),
        .mem_addr         (mem_addr),
        .mem_ready        (mem_ready),
        .mem_burst_rd     (mem_burst_rd),
        .mem_burst_wr     (mem_burst_wr),
        .mem_rd_manifold  (mem_rd_manifold),
        .mem_wr_manifold  (mem_wr_manifold),
        .mem_burst_done   (mem_burst_done),
        .mem_init_done    (mem_init_done),
        .mem_rd_en        (mem_rd_en),
        .mem_wr_en        (mem_wr_en),
        .mem_wr_data      (mem_wr_data),
        .mem_rd_data      (mem_rd_data),
        .psram0_ce_n      (psram0_ce_n),
        .psram0_clk       (psram0_clk),
        .psram0_dq        (psram0_dq),
        .psram1_ce_n      (psram1_ce_n),
        .psram1_clk       (psram1_clk),
        .psram1_dq        (psram1_dq)
    );

    always #20 clk = ~clk;  // 25 MHz

    // Defaults
    initial begin
        mem_addr        = 24'h0;
        mem_burst_rd    = 0;
        mem_burst_wr    = 0;
        mem_rd_en       = 0;
        mem_wr_en       = 0;
        mem_wr_data     = 16'h0;
        mem_wr_manifold = 832'h0;
    end

    integer pass_count = 0;
    integer fail_count = 0;

    task check;
        input condition;
        input [159:0] test_name;  // 20 chars
        begin
            if (condition) begin
                pass_count = pass_count + 1;
            end else begin
                $display("FAIL: %s", test_name);
                fail_count = fail_count + 1;
            end
        end
    endtask

    initial begin
        // ---------------------------------------------------------------- //
        // T1: Both chips held in reset — mem_init_done must be 0           //
        // ---------------------------------------------------------------- //
        @(posedge clk);
        check(!mem_init_done, "T1: init_done=0 during reset");

        // Release reset
        @(posedge clk); reset = 0;

        // ---------------------------------------------------------------- //
        // T2: Bank 0 address (addr[23]=0) → only psram0 CE asserted        //
        // ---------------------------------------------------------------- //
        // During init the controllers drive CE on their own, but once done
        // we test that a burst_rd to bank 0 does NOT activate bank 1 CE.
        // Wait for both chips to complete init sequence (~2400 + cmds clocks)
        repeat(3000) @(posedge clk);
        check(mem_init_done, "T2: both chips init_done after power-up");

        // ---------------------------------------------------------------- //
        // T3: Bank select routing — addr[23]=0 routes to psram0            //
        // ---------------------------------------------------------------- //
        mem_addr = 24'h000080;  // bank 0, addr 0x000080
        @(posedge clk);
        // psram1_ce_n should remain high (deselected) while burst to bank 0
        mem_burst_rd = 1;
        @(posedge clk);
        mem_burst_rd = 0;
        // After issuing the request, psram1 CE should stay high
        @(posedge clk);
        check(psram1_ce_n === 1'b1, "T3: bank1 CE inactive for bank0 addr");

        // Wait for burst to complete or timeout
        repeat(500) @(posedge clk);

        // ---------------------------------------------------------------- //
        // T4: Bank select routing — addr[23]=1 routes to psram1            //
        // ---------------------------------------------------------------- //
        mem_addr = 24'h800080;  // bank 1, addr 0x000080 within bank
        @(posedge clk);
        mem_burst_rd = 1;
        @(posedge clk);
        mem_burst_rd = 0;
        @(posedge clk);
        check(psram0_ce_n === 1'b1, "T4: bank0 CE inactive for bank1 addr");

        repeat(500) @(posedge clk);

        // ---------------------------------------------------------------- //
        // T5: mem_ready de-asserts during a burst (ready goes low)         //
        // ---------------------------------------------------------------- //
        mem_addr = 24'h000100;
        @(posedge clk);
        mem_burst_wr = 1;
        mem_wr_manifold = {832{1'b1}};
        @(posedge clk);  // controller samples burst_wr, schedules ready=0
        @(posedge clk);  // ready is now registered-low
        // After issuing write, ready should deassert
        check(!mem_ready, "T5: ready low on write");
        mem_burst_wr = 0;
        mem_wr_manifold = 832'h0;

        repeat(500) @(posedge clk);

        // ---------------------------------------------------------------- //
        // Report                                                            //
        // ---------------------------------------------------------------- //
        if (fail_count == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail_count);

        $finish;
    end

    // Safety timeout
    initial begin
        #5000000;
        $display("FAIL (timeout)");
        $finish;
    end

endmodule
