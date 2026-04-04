// spu_whisper_stress_tb.v — variance accumulator + channel_stress tests
// Drives PWI pulses directly (no TX) to control exact widths.
// Tests:
//   T1: calibration pulse — sets k_width_ref, variance_acc resets
//   T2: 4 on-time pulses — channel_stress stays low
//   T3: 6 noisy pulses (±20% deviation) — channel_stress rises
//   T4: 8 clean pulses after noise — channel_stress decays
`timescale 1ns/1ps

module spu_whisper_stress_tb;

    // 24 MHz clock → ~41.67 ns period
    reg clk, rst_n;
    always #20.833 clk = ~clk;

    // Use BIAS=0 so pulse widths are small and predictable
    // With K=1, BIAS=0: N_REF = 1*104 + 0*181 = 104 cycles
    localparam [15:0] BIAS = 16'd0;
    localparam        DEV_SHIFT = 4;
    localparam [31:0] N_REF = 104;  // k_width_ref after calibration

    wire signed [15:0] surd_a, surd_b;
    wire               rx_ready;
    wire [7:0]         channel_stress;
    wire               variance_alert;

    reg pwi_in;
    reg is_cal;

    SPU_WHISPER_RX #(.BIAS(BIAS), .DEV_SHIFT(DEV_SHIFT)) dut (
        .clk(clk), .rst_n(rst_n),
        .pwi_in(pwi_in), .is_cal(is_cal),
        .surd_a(surd_a), .surd_b(surd_b), .rx_ready(rx_ready),
        .channel_stress(channel_stress), .variance_alert(variance_alert)
    );

    integer i, fail = 0;

    // Send a PWI pulse of exactly `width` clock cycles
    task send_pulse;
        input [31:0] width;
        input        cal;
        integer      j;
        begin
            is_cal  = cal;
            pwi_in  = 1'b1;
            for (j = 0; j < width; j = j + 1) @(posedge clk);
            pwi_in  = 1'b0;
            @(posedge clk);  // SOLVE fires here
            @(posedge clk);  // outputs registered
            is_cal  = 1'b0;
        end
    endtask

    initial begin
        clk = 0; rst_n = 0; pwi_in = 0; is_cal = 0;
        #200; rst_n = 1; #100;

        // --- T1: Calibration pulse (width = N_REF = 104) ---
        send_pulse(N_REF, 1'b1);
        // After cal: variance_acc should be 0, channel_stress = 0
        if (channel_stress === 8'h00) begin
            $display("T1 PASS: calibration clears variance (stress=%0d)", channel_stress);
        end else begin
            $display("T1 FAIL: expected stress=0 after cal, got %0d", channel_stress);
            fail = fail + 1;
        end

        // --- T2: 4 on-time pulses (zero deviation) ---
        for (i = 0; i < 4; i = i + 1) send_pulse(N_REF, 1'b0);
        if (channel_stress === 8'h00) begin
            $display("T2 PASS: clean pulses keep stress=0 (stress=%0d)", channel_stress);
        end else begin
            $display("T2 FAIL: expected stress=0 after clean pulses, got %0d", channel_stress);
            fail = fail + 1;
        end

        // --- T3: 8 noisy pulses (+20 cycles deviation = ~19% of N_REF=104) ---
        for (i = 0; i < 8; i = i + 1) send_pulse(N_REF + 20, 1'b0);
        // Each pulse: dev_raw=20, IIR accumulates — stress should be nonzero
        if (channel_stress > 8'h00) begin
            $display("T3 PASS: noisy pulses raised stress to %0d", channel_stress);
        end else begin
            $display("T3 FAIL: expected stress>0 after noisy pulses, got %0d", channel_stress);
            fail = fail + 1;
        end

        // --- T4: 16 clean pulses — stress should decay significantly ---
        begin : decay_check
            reg [7:0] stress_before;
            stress_before = channel_stress;
            for (i = 0; i < 16; i = i + 1) send_pulse(N_REF, 1'b0);
            if (channel_stress < stress_before) begin
                $display("T4 PASS: stress decayed from %0d to %0d after clean burst",
                    stress_before, channel_stress);
            end else begin
                $display("T4 FAIL: stress did not decay (was %0d, now %0d)",
                    stress_before, channel_stress);
                fail = fail + 1;
            end
        end

        // --- T5: variance_alert should NOT be set on moderate noise ---
        if (variance_alert === 1'b0) begin
            $display("T5 PASS: variance_alert not set on moderate noise");
        end else begin
            $display("T5 FAIL: variance_alert spuriously set");
            fail = fail + 1;
        end

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

    initial #50000000 begin $display("FAIL (timeout)"); $finish; end

endmodule
