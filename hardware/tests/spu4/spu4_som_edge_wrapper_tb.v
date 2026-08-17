// spu4_som_edge_wrapper_tb.v -- the SPU-4 SOM edge-node contract, asserted
//
// Same mock-flash technique as spu4_som_flash_loader_tb.v (itself lifted
// from tb_spu_flash_bridge.v): drive MISO on negedge SCLK from a small byte
// memory once CS is asserted. This file exercises the wrapper as a
// customer would -- boot, then classify -- not the loader in isolation.

`timescale 1ns / 1ps

module spu4_som_edge_wrapper_tb;

    localparam integer NUM_FEATURES = 4;
    localparam integer WIDTH        = 16;
    localparam integer FEATURE_W    = 2 * WIDTH;
    localparam integer NODE_W       = NUM_FEATURES * FEATURE_W;
    localparam integer TOTAL_BYTES  = 4 * NUM_FEATURES * (FEATURE_W / 8);

    reg clk = 0, rst_n = 0, start = 0;
    reg [NODE_W-1:0] features = 0;
    wire busy, done;
    wire [1:0] best_node;
    wire [31:0] best_quadrance;
    wire [7:0] status;
    wire [15:0] id;
    wire flash_sclk, flash_cs_n, flash_mosi;
    reg  flash_miso = 0;

    spu4_som_edge_wrapper #(
        .NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)
    ) dut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .busy(busy), .done(done),
        .features(features),
        .best_node(best_node), .best_quadrance(best_quadrance),
        .status(status), .id(id),
        .flash_sclk(flash_sclk), .flash_cs_n(flash_cs_n),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    always #10 clk = ~clk;

    integer pass = 0, fail = 0;
    task ok;  input [1023:0] m; begin $display("PASS: %0s", m); pass = pass + 1; end endtask
    task bad; input [1023:0] m; begin $display("FAIL: %0s", m); fail = fail + 1; end endtask

    // ── Mock flash: same layout as spu4_som_flash_loader_tb.v ────────────
    reg [7:0] spi_mem [0:TOTAL_BYTES-1];
    reg [15:0] exp_p [0:3][0:NUM_FEATURES-1];
    reg [15:0] exp_q [0:3][0:NUM_FEATURES-1];

    integer n, f, idx;
    initial begin
        idx = 0;
        for (n = 0; n < 4; n = n + 1) begin
            for (f = 0; f < NUM_FEATURES; f = f + 1) begin
                exp_p[n][f] = 16'h1000 + (n << 8) + (f << 4) + 16'h1;
                exp_q[n][f] = 16'h2000 + (n << 8) + (f << 4) + 16'h2;
                spi_mem[idx] = exp_p[n][f][15:8]; idx = idx + 1;
                spi_mem[idx] = exp_p[n][f][7:0];  idx = idx + 1;
                spi_mem[idx] = exp_q[n][f][15:8]; idx = idx + 1;
                spi_mem[idx] = exp_q[n][f][7:0];  idx = idx + 1;
            end
        end
    end

    integer total_bits, sbn, sbyt;
    always @(negedge flash_cs_n) total_bits = 0;
    always @(negedge flash_sclk) begin
        if (!flash_cs_n) begin
            total_bits = total_bits + 1;
            if (total_bits >= 32) begin
                idx  = total_bits - 32;
                sbn  = idx % 8;
                sbyt = idx / 8;
                flash_miso = (sbyt < TOTAL_BYTES) ? spi_mem[sbyt][7-sbn] : 1'b0;
            end
        end
    end

    function [NODE_W-1:0] expected_node_word;
        input integer node;
        integer ff;
        reg [NODE_W-1:0] acc;
        begin
            acc = {NODE_W{1'b0}};
            for (ff = 0; ff < NUM_FEATURES; ff = ff + 1)
                acc = acc | ({{(NODE_W-FEATURE_W){1'b0}}, exp_p[node][ff], exp_q[node][ff]} << (ff * FEATURE_W));
            expected_node_word = acc;
        end
    endfunction

    initial begin
        // ── G1: outputs driven at reset, before anything has run ──────
        // 4 clocks of margin past the 2-clock reset synchroniser -- same
        // G6 lesson as spu4_customer_wrapper.v. Checking any sooner would
        // catch the DUT still internally held in reset, not actually
        // exercising the boot state.
        #100 rst_n = 1; repeat (4) @(posedge clk);
        if (^{busy, done, best_node, best_quadrance, status, id} === 1'bx)
            bad("G1 undriven/unknown output at reset release");
        else
            ok("G1 all outputs driven at reset release");

        // ── id is a fixed constant, present immediately ────────────────
        // ABI_MAJOR=1, ABI_MINOR=0, WRAPPER_ID=2, reserved=0.
        if (id === 16'h1020) ok("id reads the documented v1.0 wrapper-2 constant");
        else                 bad("id does not match the documented bitfield");

        // ── Boot: busy from reset, hydrated once loader completes ──────
        if (busy !== 1'b1 || status[2] !== 1'b0)
            bad("wrapper must be busy (booting), not yet hydrated, right after reset");
        else
            ok("wrapper busy and un-hydrated immediately after reset");

        // ── A start during boot is ignored and reported ────────────────
        // #1 after the sampling edge is load-bearing, not cosmetic -- same
        // reason spu4_customer_wrapper_tb.v's launch task has one: without
        // it, this read can race the NBA update to status.start_ignored and
        // sample the pre-edge (stale) value.
        start <= 1; @(posedge clk); start <= 0; #1;
        if (status[3] !== 1'b1)
            bad("status.start_ignored must report a start during boot hydration");
        else
            ok("start during boot hydration reported via status.start_ignored");

        begin : wait_hydrated
            integer t;
            t = 0;
            while (!status[2] && t < 20000) begin @(posedge clk); t = t + 1; end
            if (!status[2]) bad("wrapper never hydrated");
            else            ok("wrapper hydrated after boot");
        end

        if (busy !== 1'b0)
            bad("busy must clear once hydration completes and no classification is running");
        else
            ok("busy clears after hydration, before any classification");

        // ── Classify: node 2's exact trained weights must win, Q=0 ─────
        features = expected_node_word(2);
        @(posedge clk); start <= 1; @(posedge clk); start <= 0; #1;
        if (status[3] !== 1'b0)
            bad("status.start_ignored must have cleared on a clean accepted start");
        else
            ok("status.start_ignored clears on a clean accepted start");

        begin : wait_done
            integer t;
            t = 0;
            while (!done && t < 200) begin @(posedge clk); t = t + 1; end
            if (!done) bad("wrapper never completed a classification");
            else       ok("wrapper completed a classification");
        end

        if (best_node !== 2'd2)
            bad("wrapper did not select the exact-match node");
        else
            ok("wrapper selects the exact-match node");

        if (best_quadrance !== 32'd0)
            bad("wrapper quadrance nonzero for an exact match");
        else
            ok("wrapper quadrance is exactly 0 for an exact match");

        // ── G4: results held stable, done stays asserted, until next start
        begin : hold_check
            reg [1:0] hn; reg [31:0] hq;
            hn = best_node; hq = best_quadrance;
            repeat (20) @(posedge clk);
            if (best_node !== hn || best_quadrance !== hq || done !== 1'b1)
                bad("G4 results/done must hold stable while idle");
            else
                ok("G4 results and done held stable while idle");
        end

        // ── start during a classification in flight is ignored+reported ─
        features = expected_node_word(1);
        @(posedge clk); start <= 1; @(posedge clk); start <= 0;
        // Corrupt the feature register mid-flight and re-assert start.
        features = expected_node_word(3);
        @(posedge clk);
        if (!busy) bad("setup: expected busy immediately after accepted start");
        start <= 1; @(posedge clk); start <= 0;
        begin : wait_done2
            integer t;
            t = 0;
            while (!done && t < 200) begin @(posedge clk); t = t + 1; end
        end
        if (best_node !== 2'd1)
            bad("start during busy corrupted the in-flight classification");
        else
            ok("start during busy did not disturb the classification in flight");
        if (status[3] !== 1'b1)
            bad("status.start_ignored did not report a start during busy");
        else
            ok("status.start_ignored reports a start during busy");

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else            $display("FAIL");
        $finish;
    end

    initial begin
        #3_000_000;
        $display("FAIL: timeout");
        $display("FAIL");
        $finish;
    end

endmodule
