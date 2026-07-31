// spu_spi_slave_ratio_tb.v — measures the maximum safe SCK:fabric-clock ratio
//
// spu_spi_slave treats SCK as data: it is sampled by the fabric clock through a
// 3-deep shift register (sck_r), with edge detection on sck_r[2:1]. That makes
// the maximum usable SCK a function of the *routed* fabric clock, not a fixed
// protocol constant. docs/SOUTHBRIDGE_SPI_PROTOCOL.md historically quoted a flat
// "~5 MHz max"; this bench measures the real divisor so that figure can be
// stated as a ratio instead.
//
// Method: hold the fabric clock fixed, sweep the SCK period as an integer
// multiple N of the fabric clock period, and issue a 0xAC status read whose
// expected 4-byte response is known exactly. Each N is retried at several
// sub-clock phase offsets, because an integer ratio that happens to align
// favourably can pass while the same ratio fails on real, drifting hardware.
// An N only passes if it passes at EVERY phase offset.
`timescale 1ns/1ps

module spu_spi_slave_ratio_tb;

    // Fabric clock: 20 ns period (50 MHz). Only the ratio matters; the absolute
    // frequency is arbitrary and results are reported as a divisor.
    localparam real CLK_PERIOD = 20.0;

    reg clk = 0;
    always #(CLK_PERIOD/2.0) clk = ~clk;

    reg rst_n;
    reg spi_cs_n, spi_sck, spi_mosi;
    wire spi_miso;

    // Stimulus chosen so the 0xAC response is fully determined.
    reg [15:0] laminar_index;
    reg        boot_ready;

    wire        rplu_cfg_wr_en;
    wire [2:0]  rplu_cfg_sel;
    wire [7:0]  rplu_cfg_material;
    wire [9:0]  rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;
    wire        inst_valid;
    wire [63:0] inst_word;

    spu_spi_slave dut (
        .clk(clk), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(832'd0),
        .satellite_snaps(4'd0),
        .is_janus_point(1'b0),
        .dissonance(16'd0),
        .scale_table(52'd0), .scale_overflow(13'd0),
        .qr_commit_valid(1'b0),
        .qr_commit_lane(4'd0),
        .qr_commit_A(64'd0), .qr_commit_B(64'd0),
        .qr_commit_C(64'd0), .qr_commit_D(64'd0),
        .hex_valid(1'b0), .hex_q(16'd0), .hex_r(16'd0),
        .rplu_ratio_res(3'sd0), .rplu_ratio_valid(1'b0),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .inst_valid(inst_valid),
        .inst_word(inst_word),
        .fifo_full(1'b0),
        .laminar_index(laminar_index),
        .turbulence(1'b0),
        .rplu_mode(1'b0),
        .boot_ready(boot_ready),
        .sentinel_telemetry(512'd0)
    );

    // SCK half-period for the ratio currently under test.
    real sck_half;

    // Mode 0 byte transfer: MOSI presented while SCK low, MISO sampled by the
    // master at the SCK rising edge. This is what an RP2350 SPI master does, so
    // a failure here is a failure the bench firmware would actually see.
    task spi_byte;
        input  [7:0] tx;
        output [7:0] rx;
        integer i;
        begin
            rx = 8'h00;
            for (i = 7; i >= 0; i = i - 1) begin
                spi_mosi = tx[i];
                #(sck_half);
                spi_sck = 1;
                rx[i] = spi_miso;   // master samples on the rising edge
                #(sck_half);
                spi_sck = 0;
            end
        end
    endtask

    reg [7:0] rx0, rx1, rx2, rx3, dummy;

    // One 0xAC status read. Returns the four response bytes.
    task read_status;
        begin
            spi_cs_n = 0;
            #(sck_half * 4.0);
            spi_byte(8'hAC, dummy);
            spi_byte(8'h00, rx0);
            spi_byte(8'h00, rx1);
            spi_byte(8'h00, rx2);
            spi_byte(8'h00, rx3);
            #(sck_half * 4.0);
            spi_cs_n = 1;
            #(CLK_PERIOD * 20.0);
        end
    endtask

    // Expected 0xAC response for the stimulus above:
    //   byte0/1 = laminar_index big-endian
    //   byte2   = {ratio[2:0], ratio_valid, fifo_full, turbulence, janus, snap} = 0
    //   byte3   = {5'h0, boot_ready, crc_error_sticky, rplu_mode}
    function expected_ok;
        input [7:0] b0, b1, b2, b3;
        begin
            expected_ok = (b0 == laminar_index[15:8]) &&
                          (b1 == laminar_index[7:0])  &&
                          (b2 == 8'h00)               &&
                          (b3 == {5'h0, boot_ready, 1'b0, 1'b0});
        end
    endfunction

    integer n;              // ratio under test: SCK period = n * CLK_PERIOD
    integer p;              // phase offset index
    integer phase_fails;
    integer min_pass_n;
    integer pass_count, fail_count;
    real    phase_step;

    initial begin
        rst_n         = 0;
        spi_cs_n      = 1;
        spi_sck       = 0;
        spi_mosi      = 0;
        laminar_index = 16'hBEEF;
        boot_ready    = 1'b1;
        pass_count    = 0;
        fail_count    = 0;
        min_pass_n    = 0;

        repeat (8) @(posedge clk);
        rst_n = 1;
        repeat (8) @(posedge clk);

        $display("SPI slave SCK:fabric-clock ratio sweep");
        $display("fabric clock period = %0.1f ns", CLK_PERIOD);
        $display("");
        // Sweep rows are labelled "ok"/"over" rather than PASS/FAIL: the bench
        // *expects* low ratios to fail, and run_all_tests.py treats any "FAIL"
        // substring anywhere in the output as a failed testbench. Only the
        // overall verdict at the end may use those tokens.
        $display("  N   SCK period    result   (N = fabric_clk / sck_freq)");
        $display("  --  -----------   ------");

        // Sweep from generous down to marginal. Report the smallest N that
        // survives every phase offset.
        for (n = 16; n >= 2; n = n - 1) begin
            sck_half    = (CLK_PERIOD * n) / 2.0;
            phase_fails = 0;

            // Four sub-clock phase offsets across one fabric clock period.
            for (p = 0; p < 4; p = p + 1) begin
                phase_step = (CLK_PERIOD * p) / 4.0;
                #(phase_step);
                read_status;
                if (!expected_ok(rx0, rx1, rx2, rx3))
                    phase_fails = phase_fails + 1;
            end

            if (phase_fails == 0) begin
                $display("  %2d  %6.1f ns     ok", n, CLK_PERIOD * n);
                // The summary bound below assumes the sweep is monotonic: every
                // ratio above the bound passes, every ratio below it fails. If
                // that ever stops holding, "smallest passing N" is not a safe
                // operating limit and must not be reported as one.
                if (fail_count != 0) begin
                    $display("FAIL — non-monotonic sweep: N=%0d passed after a lower-ratio failure; bound is not a safe limit", n);
                    $finish;
                end
                min_pass_n = n;   // smallest N seen passing so far
                pass_count = pass_count + 1;
            end else begin
                $display("  %2d  %6.1f ns     over  (%0d/4 phase offsets bad)",
                         n, CLK_PERIOD * n, phase_fails);
                fail_count = fail_count + 1;
            end
        end

        $display("");
        if (min_pass_n == 0) begin
            $display("FAIL — no ratio in the swept range worked; bench is broken");
            $finish;
        end

        $display("Minimum safe divisor: SCK <= fabric_clk / %0d", min_pass_n);
        $display("");
        // Wukong A7-100T spin classes. The board oscillator is 50 MHz (the
        // clk_100mhz port name is a misnomer); A7_FREQ is a nextpnr timing
        // constraint and does NOT divide the clock -- A7_CLK_DIV_LOG2 does.
        $display("Wukong A7-100T ceilings (50 MHz oscillator):");
        $display("  coreless spins, A7_CLK_DIV_LOG2=0  -> clk_fast 50.00 MHz  -> SCK <= %0.2f MHz",
                 50.0 / min_pass_n);
        $display("  core spins,     A7_CLK_DIV_LOG2=6  -> clk_fast %0.2f kHz -> SCK <= %0.0f kHz",
                 50.0e3 / 64.0, (50.0e3 / 64.0) / min_pass_n);
        $display("");

        // The bench is only meaningful if it observed BOTH outcomes. If every
        // ratio passed, the sweep never reached the failure edge and the
        // measured bound would be an artifact of the chosen range.
        if (fail_count == 0) begin
            $display("FAIL — sweep never reached a failing ratio; bound not bracketed");
            $finish;
        end
        if (pass_count == 0) begin
            $display("FAIL — sweep never reached a passing ratio");
            $finish;
        end

        $display("PASS — bound bracketed: %0d ratios passed, %0d failed",
                 pass_count, fail_count);
        $finish;
    end

    // Watchdog: the runner times out at 15 s, so fail loudly and early instead.
    initial begin
        #50_000_000;
        $display("FAIL — timeout");
        $finish;
    end

endmodule
