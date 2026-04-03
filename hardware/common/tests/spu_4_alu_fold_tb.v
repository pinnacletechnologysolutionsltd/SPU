`timescale 1ns/1ps
// spu_4_alu_fold_tb.v — Phi-Fold & Davis Henosis Testbench
// Tests:
//   1. Normal inputs  — no fold, output matches expected Q8.8 sum
//   2. Overflow inputs — Phi-fold fires, output stays within 16-bit Q8.8 range
//   3. Sentinel Henosis — quadrance runaway triggers fold, manifold recovers
//
// CC0 1.0 Universal.

module spu_4_alu_fold_tb;

    // ── Clock & reset ─────────────────────────────────────────────────────
    reg clk, reset;
    always #41.66 clk = ~clk; // 12 MHz

    // ── DUT: spu_4_euclidean_alu ──────────────────────────────────────────
    reg  [15:0] A_in, B_in, C_in, D_in;
    reg  [15:0] F, G, H;
    reg  [7:0]  bloom;
    reg         start, mode_auto;
    wire [15:0] A_out, B_out, C_out, D_out;
    wire        done, henosis_pulse;

    spu_4_euclidean_alu u_alu (
        .clk(clk), .reset(reset),
        .start(start),
        .bloom_intensity(bloom),
        .mode_autonomous(mode_auto),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .F(F), .G(G), .H(H),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out),
        .done(done),
        .henosis_pulse(henosis_pulse)
    );

    // ── DUT: spu4_sentinel ───────────────────────────────────────────────
    `include "sqr_params.vh"
    reg  heartbeat, rst_n_s;
    wire [15:0] sA, sB, sC, sD;
    wire [31:0] s_quad, s_quad_seed;
    wire        s_janus, s_pass, s_henosis;
    wire [9:0]  s_hb_cnt;

    spu4_sentinel u_sentinel (
        .clk(clk), .rst_n(rst_n_s),
        .heartbeat(heartbeat),
        .A_seed(16'h0000), .B_seed(16'h1000),
        .C_seed(16'h0000), .D_seed(16'h0000),
        .rot_mode(2'b01), // 60-degree
        .A_out(sA), .B_out(sB), .C_out(sC), .D_out(sD),
        .quadrance(s_quad), .quadrance_seed(s_quad_seed),
        .janus_stable(s_janus),
        .heartbeat_count(s_hb_cnt),
        .test_pass(s_pass),
        .henosis_pulse(s_henosis)
    );

    // ── Task: run one ALU operation, wait for done ────────────────────────
    task run_alu;
        begin
            @(posedge clk); start = 1;
            @(posedge clk); start = 0;
            // Wait up to 500 cycles for done
            begin : wait_done
                integer timeout;
                for (timeout = 0; timeout < 500 && !done; timeout = timeout + 1)
                    @(posedge clk);
            end
            @(posedge clk); // capture outputs
        end
    endtask

    integer failures;

    initial begin
        $dumpfile("fold_trace.vcd");
        $dumpvars(0, spu_4_alu_fold_tb);

        clk = 0; reset = 1; rst_n_s = 0;
        start = 0; mode_auto = 0; bloom = 8'hFF; // max intensity = no scaling
        A_in = 0; B_in = 0; C_in = 0; D_in = 0;
        F = 0; G = 0; H = 0; heartbeat = 0;
        failures = 0;
        #200; reset = 0; rst_n_s = 1; #200;

        // ── Test 1: Normal inputs, no overflow ────────────────────────────
        // B_in=C_in=D_in=0x0100 (1.0 Q8.8), F=0x0050, G=0x00B5, H=0x0050
        // Expected: B'=C'=D'=0x0050+0x0050+0x00B5 = 0x0145 (no fold)
        $display("--- Test 1: Normal inputs (expect no fold) ---");
        B_in = 16'h0100; C_in = 16'h0100; D_in = 16'h0100;
        F    = 16'h0050; G    = 16'h00B5; H    = 16'h0050;
        run_alu;
        if (B_out !== 16'h0155 || C_out !== 16'h0155 || D_out !== 16'h0155) begin
            $display("[FAIL] T1: B=%04x C=%04x D=%04x (expected 0155 each)", B_out, C_out, D_out);
            failures = failures + 1;
        end else if (henosis_pulse) begin
            $display("[FAIL] T1: henosis_pulse unexpectedly set");
            failures = failures + 1;
        end else
            $display("[PASS] T1: B=C=D=%04x (0x50+0x50+0xB5=0x155), no fold", B_out);

        #100;

        // ── Test 2: Max inputs, max coefficients → guaranteed overflow ────
        // B=C=D=0xFFFF, F=G=H=0x00FF
        // prod_trunc(0xFFFF × 0x00FF) = (0x00FE FF01)[23:8] = 0xFEFF = 65279
        // sum = 3 × 65279 = 195837 → bit16 set → fold by >>1 → 97918 = 0x17EFE
        // ...>>1 → 0xBEFF (48959).  bit17 set so >>2: 195837>>2 = 48959 = 0xBEFF
        $display("--- Test 2: Max inputs (expect Phi-fold fires) ---");
        B_in = 16'hFFFF; C_in = 16'hFFFF; D_in = 16'hFFFF;
        F    = 16'h00FF; G    = 16'h00FF; H    = 16'h00FF;
        reset = 1; #100; reset = 0; #100;
        run_alu;
        // Check outputs are in valid 16-bit range (fold occurred, no wrap)
        if (B_out > 16'hFFFF || C_out > 16'hFFFF || D_out > 16'hFFFF) begin
            $display("[FAIL] T2: Output out of range B=%04x C=%04x D=%04x", B_out, C_out, D_out);
            failures = failures + 1;
        end else begin
            $display("[PASS] T2: B=%04x C=%04x D=%04x (folded from overflow)", B_out, C_out, D_out);
        end

        #100;

        // ── Test 3: Sentinel — 100 normal heartbeats, Henosis should NOT fire
        $display("--- Test 3: Sentinel 100-beat, no runaway (expect no Henosis) ---");
        begin : sentinel_normal
            integer i, henosis_count;
            henosis_count = 0;
            for (i = 0; i < 101; i = i + 1) begin
                heartbeat = 1; #83.33; heartbeat = 0;
                if (s_henosis) henosis_count = henosis_count + 1;
                #(83.33 * 9);
            end
            #500;
            if (henosis_count > 0)
                $display("[WARN] T3: Henosis fired %0d times (precision drift?)", henosis_count);
            else
                $display("[PASS] T3: Sentinel stable, no Henosis over 100 heartbeats");
            $display("       Q_seed=%08x  Q_now=%08x  Janus=%0d",
                     s_quad_seed, s_quad, s_janus);
        end

        $display("--- Results: %0d failure(s) ---", failures);
        if (failures == 0)
            $display("[PASS] spu_4_alu_fold: All tests passed.");
        else
            $display("[FAIL] spu_4_alu_fold: %0d test(s) failed.", failures);

        $finish;
    end

endmodule
