// spu4_som_flash_loader_tb.v -- flash-to-weight-register hydration, checked
// end to end against a mock SPI flash and a real spu4_som_edge.
//
// Mock flash SPI slave technique lifted from
// hardware/tests/peripherals/tb_spu_flash_bridge.v (already proven): drive
// MISO on negedge SCLK from a small byte memory once CS is asserted, timed
// off a running bit counter (CMD 8b + ADDR 24b = 32 bits before data starts).
//
// This is the executable form of the flash image layout documented in
// spu4_som_flash_loader.v's header: node-major, feature-ascending, each
// feature as P_hi P_lo Q_hi Q_lo.

`timescale 1ns / 1ps

module spu4_som_flash_loader_tb;

    localparam integer NUM_FEATURES = 4;   // the INA226 capture contract's value
    localparam integer WIDTH        = 16;
    localparam integer FEATURE_W    = 2 * WIDTH;
    localparam integer NODE_W       = NUM_FEATURES * FEATURE_W;
    localparam integer TOTAL_BYTES  = 4 * NUM_FEATURES * (FEATURE_W / 8);

    reg clk = 0, rst_n = 0, start = 0;
    wire busy, done;
    wire weight_we;
    wire [1:0] weight_node;
    wire [NODE_W-1:0] weight_data;
    wire flash_sclk, flash_cs_n, flash_mosi;
    reg  flash_miso = 0;

    spu4_som_flash_loader #(
        .NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .busy(busy), .done(done),
        .weight_we(weight_we), .weight_node(weight_node), .weight_data(weight_data),
        .flash_sclk(flash_sclk), .flash_cs_n(flash_cs_n),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    // Real consumer downstream, so this test exercises the actual interface
    // contract rather than just the loader's own idea of correctness.
    wire som_done;
    wire [1:0] best_node;
    wire [31:0] best_quadrance;
    reg som_start = 0;
    reg [NODE_W-1:0] features = 0;

    spu4_som_edge #(
        .NUM_FEATURES(NUM_FEATURES), .WIDTH(WIDTH)
    ) som (
        .clk(clk), .rst_n(rst_n),
        .start(som_start), .done(som_done),
        .features(features),
        .weight_we(weight_we), .weight_node(weight_node), .weight_data(weight_data),
        .bmu_valid(), .best_node(best_node), .best_quadrance(best_quadrance)
    );

    always #10 clk = ~clk;

    integer pass = 0, fail = 0;
    task ok;  input [1023:0] m; begin $display("PASS: %0s", m); pass = pass + 1; end endtask
    task bad; input [1023:0] m; begin $display("FAIL: %0s", m); fail = fail + 1; end endtask

    // ── Mock flash: node-major, feature-ascending, P_hi P_lo Q_hi Q_lo ───
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
                spi_mem[idx]   = exp_p[n][f][15:8]; idx = idx + 1;
                spi_mem[idx]   = exp_p[n][f][7:0];  idx = idx + 1;
                spi_mem[idx]   = exp_q[n][f][15:8]; idx = idx + 1;
                spi_mem[idx]   = exp_q[n][f][7:0];  idx = idx + 1;
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

    // Expected node word, built with the SAME convention spu4_som_edge uses
    // internally: feature 0 occupies the low FEATURE_W bits, each feature is
    // {P, Q} with P in the upper 16 bits.
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

    // ── Capture every weight_we pulse the loader issues ──────────────────
    integer we_count;
    reg [1:0] we_node_seen [0:3];
    reg [NODE_W-1:0] we_data_seen [0:3];
    always @(posedge clk) begin
        if (weight_we) begin
            we_node_seen[we_count] = weight_node;
            we_data_seen[we_count] = weight_data;
            we_count = we_count + 1;
        end
    end

    initial begin
        we_count = 0;
        #100 rst_n = 1;
        repeat(4) @(posedge clk);

        // ── G1: idle before start ─────────────────────────────────────
        if (busy !== 1'b0 || done !== 1'b0)
            bad("loader must be idle (busy=0, done=0) before start");
        else
            ok("loader idle before start");

        @(posedge clk); start = 1; @(posedge clk); start = 0;

        // Wait for hydration to finish. TOTAL_BYTES*~16 clocks of SPI bit
        // time plus FSM overhead; generous bound, this is a correctness
        // check not a latency one.
        begin : wait_done
            integer timeout;
            timeout = 0;
            while (!done && timeout < 20000) begin
                @(posedge clk);
                timeout = timeout + 1;
            end
            if (!done) bad("loader never asserted done");
            else       ok("loader asserted done");
        end

        if (we_count !== 4)
            bad("expected exactly 4 weight_we pulses, one per node");
        else
            ok("exactly 4 weight_we pulses observed");

        // ── Order and content of each weight_we pulse ────────────────
        for (n = 0; n < 4; n = n + 1) begin
            if (we_count > n) begin
                if (we_node_seen[n] !== n[1:0])
                    bad("weight_we pulse out of order -- wrong node index");
                else
                    ok("weight_we pulse in order for its node");

                if (we_data_seen[n] !== expected_node_word(n))
                    bad("weight_data mismatch against the flash image for a node");
                else
                    ok("weight_data matches the flash image bit-for-bit for a node");
            end
        end

        if (busy !== 1'b0)
            bad("busy must clear once done");
        else
            ok("busy clears once done");

        // ── End-to-end: BMU picks the exact node whose features match ──
        // Node 2's trained weights, fed back in as the input feature
        // vector, must win with quadrance 0 -- this is the real payoff of
        // the hydration path, not just that bytes moved correctly.
        features = expected_node_word(2);
        @(posedge clk); som_start = 1; @(posedge clk); som_start = 0;
        begin : wait_som
            integer timeout;
            timeout = 0;
            while (!som_done && timeout < 100) begin
                @(posedge clk);
                timeout = timeout + 1;
            end
            if (!som_done) bad("spu4_som_edge never completed after hydration");
            else           ok("spu4_som_edge completed after hydration");
        end

        if (best_node !== 2'd2)
            bad("BMU did not select the exact-match node after flash hydration");
        else
            ok("BMU selects the exact-match node after flash hydration");

        if (best_quadrance !== 32'd0)
            bad("BMU quadrance nonzero for an exact feature/weight match");
        else
            ok("BMU quadrance is exactly 0 for the exact-match node");

        $display("%0d checks, %0d passed, %0d failed", pass + fail, pass, fail);
        if (fail == 0) $display("PASS");
        else            $display("FAIL");
        $finish;
    end

    initial begin
        #2_000_000;
        $display("FAIL: timeout");
        $display("FAIL");
        $finish;
    end

endmodule
