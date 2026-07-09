// spu4_dissonance_whisper_tb.v — Testbench: spu4_core dissonance + whisper v1
// integration (the gap flagged in the 2026-07-09 handover: spu4_core wires a
// real dissonance computation and a real spu_whisper_v1_emitter instance,
// but no testbench asserted the VALUES were correct — spu4_autonomy_tb.v
// only wires dissonance to a dangling wire and never touches whisper_tx).
//
// Drives spu4_core in slave mode (mode_autonomous=0) with B_in=C_in=D_in=0,
// which forces the circulant ALU's B'/C'/D' outputs to exactly zero
// regardless of F/G/H (each term is a product with a zero operand), so
// A_out settles to exactly A_in once bloom_intensity reaches full scale.
// That sidesteps the ALU's internal Q8.8/phi-fold arithmetic entirely and
// gives a fully hand-computable oracle: dissonance = saturating |A_in|.
//
// For each test vector this checks:
//   1. dissonance == oracle_dissonance(A_in) directly on the core's output.
//   2. The whisper v1 frame broadcasting that dissonance decodes cleanly
//      (no frame_err) with node_id=1 (hardcoded in spu4_core), flags=000
//      (sentinel_mode=0), and the SAME dissonance value carried through.
//
// Oracle-driven: expected dissonance computed from A_in directly, never
// re-derived from the RTL's internal gasket_sum_ext/abs_sum logic.

`timescale 1ns/1ps

module spu4_dissonance_whisper_tb;

    reg clk, reset;
    reg prog_en;
    reg [3:0]  prog_addr;
    reg [15:0] prog_data;
    reg        mode_autonomous;
    reg [15:0] A_in, B_in, C_in, D_in;
    reg [15:0] F_rat, G_rat, H_rat;

    wire [15:0] A_out, B_out, C_out, D_out;
    wire        bloom_complete;
    wire [7:0]  dissonance;
    wire        whisper_tx;
    wire        spi_cs_n, spi_sck, spi_mosi;
    wire [7:0]  bus_addr;
    wire        bus_wen, bus_ren;
    wire        psram_ce_n, psram_clk;
    wire [3:0]  psram_dq;

    spu4_core dut (
        .clk(clk), .reset(reset),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck), .spi_mosi(spi_mosi), .spi_miso(1'b0),
        .piranha_pulse(1'b0), .sentinel_mode(1'b0),
        .prog_en_aux(prog_en), .prog_addr_aux(prog_addr), .prog_data_aux(prog_data),
        .mode_autonomous(mode_autonomous),
        .A_in(A_in), .B_in(B_in), .C_in(C_in), .D_in(D_in),
        .F_rat(F_rat), .G_rat(G_rat), .H_rat(H_rat),
        .bus_addr(bus_addr), .bus_wen(bus_wen), .bus_ren(bus_ren), .bus_ready(1'b0),
        .psram_ce_n(psram_ce_n), .psram_clk(psram_clk), .psram_dq(psram_dq),
        .A_out(A_out), .B_out(B_out), .C_out(C_out), .D_out(D_out),
        .bloom_complete(bloom_complete),
        .dissonance(dissonance),
        .whisper_tx(whisper_tx)
    );

    // Decode the coherence-plane frame. Must match spu4_core's internal
    // (hardcoded) WHISPER_CLK_HZ/WHISPER_BAUD exactly, or bit timing
    // desyncs and every frame reads as garbage.
    wire [3:0] rx_node_id;
    wire [2:0] rx_flags;
    wire [7:0] rx_dissonance;
    wire [7:0] rx_som_label;   // frame field named "seq" in the listener port
    wire       rx_valid, rx_err, rx_incoherent;

    spu_whisper_v1_listener #(
        .CLK_HZ(50000000), .BAUD(115200), .PERIOD_CYCLES(8333)
    ) u_listener (
        .clk(clk), .rst_n(!reset), .rx(whisper_tx),
        .node_id(rx_node_id), .flags(rx_flags),
        .dissonance(rx_dissonance), .seq(rx_som_label),
        .frame_valid(rx_valid), .frame_err(rx_err), .incoherent(rx_incoherent)
    );

    always #10 clk = ~clk;   // 50 MHz, matching spu4_core's whisper timing

    integer fail;

    // ── Oracle: dissonance[7:0] = min(|A_in + 0 + 0 + 0|, 255) ───────
    // Independent of the RTL's gasket_sum_ext/abs_sum implementation.
    function [7:0] oracle_dissonance;
        input signed [15:0] a;
        reg [16:0] mag;
        begin
            mag = (a < 0) ? (-a) : a;
            oracle_dissonance = (mag > 17'd255) ? 8'hFF : mag[7:0];
        end
    endfunction

    task check_dissonance;
        input [127:0] msg;
        reg [7:0] expected;
        begin
            expected = oracle_dissonance(A_in);
            if (dissonance !== expected) begin
                $display("FAIL: %0s dissonance got=%h exp=%h (A_in=%h)",
                          msg, dissonance, expected, A_in);
                fail = fail + 1;
            end
        end
    endtask

    // Wait for the next whisper frame (or time out), then check its fields
    // against the CURRENT A_in-derived oracle.
    task check_next_frame;
        input [127:0] msg;
        reg [7:0] expected;
        integer   cycles;
        begin
            expected = oracle_dissonance(A_in);
            cycles = 0;
            while (!rx_valid && cycles < 300000) begin
                @(posedge clk);
                cycles = cycles + 1;
            end
            if (!rx_valid) begin
                $display("FAIL: %0s timeout — no whisper frame in 300K cycles", msg);
                fail = fail + 1;
            end else begin
                if (rx_err) begin
                    $display("FAIL: %0s frame_err asserted on received frame", msg);
                    fail = fail + 1;
                end
                if (rx_node_id !== 4'h1) begin
                    $display("FAIL: %0s node_id got=%h exp=1", msg, rx_node_id);
                    fail = fail + 1;
                end
                if (rx_flags !== 3'b000) begin
                    $display("FAIL: %0s flags got=%b exp=000 (sentinel_mode=0)", msg, rx_flags);
                    fail = fail + 1;
                end
                if (rx_dissonance !== expected) begin
                    $display("FAIL: %0s frame dissonance got=%h exp=%h", msg, rx_dissonance, expected);
                    fail = fail + 1;
                end
                @(posedge clk);   // drain the pulse before the next wait
            end
        end
    endtask

    // ── Global watchdog ───────────────────────────────────────────────
    initial begin
        repeat (3000000) @(posedge clk);
        $display("FAIL: global watchdog timeout");
        $finish;
    end

    initial begin
        clk = 0; reset = 1; fail = 0;
        prog_en = 0; prog_addr = 0; prog_data = 0;
        mode_autonomous = 0;
        A_in = 16'h0032; B_in = 16'h0000; C_in = 16'h0000; D_in = 16'h0000;
        F_rat = 16'h0050; G_rat = 16'h00B5; H_rat = 16'h0050;

        #200;
        reset = 0;

        // bloom_intensity ramps to full scale (~19,000 cycles observed);
        // wait extra cycles beyond bloom_complete for the continuously-
        // running slave-mode ALU to complete a pass at full intensity
        // (2000 cycles was empirically sufficient — one ALU pass is far
        // shorter than that).
        wait (bloom_complete);
        repeat (2000) @(posedge clk);

        // Full whisper-frame decode (each wait is a real ~90-110K cycle
        // UART transmission at the core's hardcoded 50MHz/115200 baud) is
        // checked on the normal and saturating vectors only, to stay under
        // the test harness's wall-clock budget. Every vector still gets
        // the fast, direct dissonance check.

        // ── Test 1: positive, non-saturating ──────────────────────────
        $display("── Test 1: A_in=50, dissonance=50 ──");
        check_dissonance("T1 direct");
        check_next_frame("T1 whisper");

        // ── Test 2: negative, non-saturating (exercises abs-of-negative) ──
        $display("── Test 2: A_in=-50, dissonance=50 ──");
        A_in = 16'hFFCE;   // -50 two's complement
        repeat (3000) @(posedge clk);
        check_dissonance("T2 direct");

        // ── Test 3: saturating (|A_in| > 255) ─────────────────────────
        $display("── Test 3: A_in=512, dissonance saturates to 0xFF ──");
        A_in = 16'h0200;   // 512
        repeat (3000) @(posedge clk);
        check_dissonance("T3 direct");
        check_next_frame("T3 whisper");

        // ── Test 4: zero — fully laminar ──────────────────────────────
        $display("── Test 4: A_in=0, dissonance=0 ──");
        A_in = 16'h0000;
        repeat (3000) @(posedge clk);
        check_dissonance("T4 direct");

        // ── Report ─────────────────────────────────────────────────────
        if (fail == 0)
            $display("\nPASS");
        else
            $display("\nFAIL (%0d failures)", fail);
        $finish;
    end

endmodule
