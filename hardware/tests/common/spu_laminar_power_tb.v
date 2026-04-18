// spu_laminar_power_tb.v — channel_stress → effective intensity clamping tests
`timescale 1ns/1ps

module spu_laminar_power_tb;

    localparam W = 32;

    reg        clk, rst_n;
    reg [7:0]  bloom_intensity, channel_stress;
    reg [W-1:0] reg_in;
    wire [W-1:0] reg_out;

    spu_laminar_power #(.WIDTH(W)) dut (
        .clk(clk), .rst_n(rst_n),
        .bloom_intensity(bloom_intensity),
        .channel_stress(channel_stress),
        .reg_in(reg_in),
        .reg_out(reg_out)
    );

    always #20.833 clk = ~clk;

    integer fail = 0;

    task check;
        input [W-1:0] expected;
        input [63:0]  tag;
        begin
            @(posedge clk); #1;
            if (reg_out === expected)
                $display("PASS %0s: out=%08h", tag, reg_out);
            else begin
                $display("FAIL %0s: expected %08h got %08h", tag, expected, reg_out);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        clk = 0; rst_n = 0;
        bloom_intensity = 8'hFF;
        channel_stress  = 8'h00;
        reg_in          = 32'h0000_1000;
        #200; rst_n = 1; #50;

        // T1: no stress, full bloom → 100% output
        bloom_intensity = 8'hFF; channel_stress = 8'h00;
        @(posedge clk); #1;
        check(32'h0000_1000, "T1_no_stress_full");

        // T2: mild stress (0x3F < 0x40) → no cap, full bloom still
        bloom_intensity = 8'hFF; channel_stress = 8'h3F;
        @(posedge clk); #1;
        check(32'h0000_1000, "T2_mild_stress_full");

        // T3: stress=0x40 → cap at 0xC0 (75%) → out = 0x1000 - 0x0400 = 0x0C00
        bloom_intensity = 8'hFF; channel_stress = 8'h40;
        @(posedge clk); #1;
        check(32'h0000_0C00, "T3_stress40_cap75");

        // T4: stress=0x80 → cap at 0x80 (50%) → out = 0x1000>>1 = 0x0800
        bloom_intensity = 8'hFF; channel_stress = 8'h80;
        @(posedge clk); #1;
        check(32'h0000_0800, "T4_stress80_cap50");

        // T5: stress=0xC0 → cap at 0x40 (25%) → out = 0x1000>>2 = 0x0400
        bloom_intensity = 8'hFF; channel_stress = 8'hC0;
        @(posedge clk); #1;
        check(32'h0000_0400, "T5_stress_C0_cap25");

        // T6: bloom lower than stress cap → bloom wins (not lifted)
        bloom_intensity = 8'h80; channel_stress = 8'h20;  // cap=0xFF, bloom=0x80 → 50%
        @(posedge clk); #1;
        check(32'h0000_0800, "T6_bloom_below_cap");

        // T7: bloom=0x20 (below 0x40), stress=0xC0 (cap=0x40) → bloom wins (25%)
        bloom_intensity = 8'h20; channel_stress = 8'hC0;
        @(posedge clk); #1;
        // eff_intensity=0x20 < 0x40 → c_0=1 → out=0
        check(32'h0000_0000, "T7_bloom_below_cap_zero");

        // T8: reset → all zeros
        rst_n = 0; @(posedge clk); #1;
        if (reg_out === 32'h0) $display("PASS T8_reset: out=0");
        else begin $display("FAIL T8_reset: got %08h", reg_out); fail = fail + 1; end
        rst_n = 1;

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

    initial #1000000 begin $display("FAIL (timeout)"); $finish; end

endmodule
