// spu_artery_tb.v (v2.1) — Direct SPU_ARTERY_FIFO protocol test
// Tests the Artery async FIFO bridge in isolation: write at 133 MHz, read at 61.44 kHz.
`timescale 1ns/1ps

module spu_artery_tb;

    reg  wr_clk, rd_clk;
    reg  wr_rst_n, rd_rst_n;
    reg  wr_en;
    reg  [63:0] wr_data;
    wire full, empty;
    wire [63:0] rd_data;
    reg  rd_en;

    SPU_ARTERY_FIFO uut (
        .wr_clk(wr_clk), .wr_rst_n(wr_rst_n), .wr_en(wr_en), .wr_data(wr_data), .full(full),
        .rd_clk(rd_clk), .rd_rst_n(rd_rst_n), .rd_en(rd_en), .rd_data(rd_data), .empty(empty)
    );

    always #3.76  wr_clk = ~wr_clk;  // ~133 MHz (RP2040 domain)
    always #8138  rd_clk = ~rd_clk;  // ~61.44 kHz (SPU heartbeat)

    integer ai;
    integer fail = 0;
    reg [63:0] expected [0:12];

    initial begin
        $dumpfile("artery_trace.vcd");
        $dumpvars(0, spu_artery_tb);

        wr_clk = 0; rd_clk = 0;
        wr_rst_n = 0; rd_rst_n = 0;
        wr_en = 0; rd_en = 0; wr_data = 0;
        #20000;
        wr_rst_n = 1; rd_rst_n = 1;
        #1000;

        $display("--- Artery Protocol Test Start ---");

        // ── T1: Burst-write 13 Chords at 133 MHz ─────────────────────
        $display("Ghost OS: Hydrating 13 Chords at 133 MHz...");
        // #1 after each posedge ensures wr_en/wr_data are set BETWEEN posedges
        // so the FIFO always block captures the new values at the NEXT posedge.
        for (ai = 0; ai < 13; ai = ai + 1) begin
            @(posedge wr_clk); #1;
            wr_en = 1;
            wr_data = 64'hA000 + ai;
            expected[ai] = 64'hA000 + ai;
        end
        @(posedge wr_clk); #1; wr_en = 0;

        if (!full)
            $display("  FIFO not full after 13 writes (depth > 13).");
        else
            $display("  FIFO full flag asserted as expected.");

        // ── T2: Read back at 61.44 kHz, verify data integrity ────────
        $display("SPU-13: Inhaling 13 Chords at 61.44 kHz...");
        // FWFT FIFO: rd_data combinatorially tracks rd_ptr.
        // Setting rd_en=1 must happen BETWEEN posedges (after #1) to avoid
        // a race where the always @(posedge rd_clk) block sees rd_en=1 during
        // what should be an idle cycle.
        repeat(2) @(posedge rd_clk); #1;
        for (ai = 0; ai < 13; ai = ai + 1) begin
            if (rd_data !== expected[ai]) begin
                $display("FAIL T2[%0d]: got %h exp %h", ai, rd_data, expected[ai]);
                fail = fail + 1;
            end
            @(posedge rd_clk); #1;     // idle: no rd_en; #1 clears posedge hazard
            rd_en = 1;                 // set between posedges — no race
            @(posedge rd_clk); #1;     // advance: rd_ptr++; #1 resolves NBA
            rd_en = 0;
        end

        if (fail == 0)
            $display("PASS: Artery Bridge bit-exact over 133 MHz → 61.44 kHz crossing.");
        else
            $display("FAIL: %0d chord(s) corrupted in transit.", fail);

        // ── T3: FIFO empty after draining ─────────────────────────────
        @(posedge rd_clk);
        if (empty)
            $display("PASS: FIFO empty after full drain.");
        else
            $display("FAIL: FIFO not empty after drain.");

        #100;
        $finish;
    end

endmodule
