`timescale 1ns/1ps

module spu_whisper_tb;

    reg clk;
    reg rst_n;
    
    // 1. SPU_WHISPER_TX (Transmitter)
    reg [15:0] tx_surd_a, tx_surd_b;
    reg trig_en;
    wire pwi_link;
    wire tx_ready;

    SPU_WHISPER_TX #(
        .K_FACTOR(1),
        .BIAS(16'd0)
    ) tx (
        .clk(clk), .rst_n(rst_n),
        .trig_en(trig_en), .is_sync(1'b0), .surd_a(tx_surd_a), .surd_b(tx_surd_b),
        .pwi_out(pwi_link), .tx_ready(tx_ready)
    );

    // 2. SPU_WHISPER_RX (Receiver)
    wire [15:0] rx_surd_a, rx_surd_b;
    wire rx_ready;

    SPU_WHISPER_RX #(
        .BIAS(16'd0)
    ) rx (
        .clk(clk), .rst_n(rst_n),
        .pwi_in(pwi_link), .is_cal(1'b0),
        .surd_a(rx_surd_a), .surd_b(rx_surd_b),
        .rx_ready(rx_ready)
    );

    // 3. Clock Generation
    always #41.67 clk = ~clk; // 12 MHz iCE40 Clock

    // 4. Test Sequence
    initial begin
        $dumpfile("whisper_trace.vcd");
        $dumpvars(0, spu_whisper_tb);

        clk = 0; rst_n = 0;
        tx_surd_a = 0; tx_surd_b = 0;
        trig_en = 0;
        #100;
        rst_n = 1;
        #100;

        $display("--- Whisper Protocol 181/104 Loopback Stress Test (BIAS=0) ---");
        
        // Test Case 1: a=1, b=0 (Rational Unit Step)
        @(posedge clk);
        tx_surd_a = 16'd1; tx_surd_b = 16'd0;
        trig_en = 1;
        @(posedge clk);
        trig_en = 0;

        begin : wait1 integer t1; for (t1=0; t1<5000000 && !rx_ready; t1=t1+1) @(posedge clk); end
        $display("Test Case 1 (a=1, b=0): RX_a=%d, RX_b=%d", rx_surd_a, rx_surd_b);
        if (rx_surd_a == 1 && rx_surd_b == 0) begin
             $display("PASS: Rational Unit Step reconstructed.");
        end else begin
             $display("FAIL: Reconstruction mismatch.");
        end

        // Test Case 2: a=0, b=1 (Surd Unit Step)
        #1000;
        @(posedge clk);
        tx_surd_a = 16'd0; tx_surd_b = 16'd1;
        trig_en = 1;
        @(posedge clk);
        trig_en = 0;

        begin : wait2 integer t2; for (t2=0; t2<5000000 && !rx_ready; t2=t2+1) @(posedge clk); end
        $display("Test Case 2 (a=0, b=1): RX_a=%d, RX_b=%d", rx_surd_a, rx_surd_b);
        if (rx_surd_a == 0 && rx_surd_b == 1) begin
             $display("PASS: Surd Unit Step reconstructed.");
        end else begin
             $display("FAIL: Reconstruction mismatch.");
        end

        // Test Case 3: Mixed Compound Step (a=47, b=13)
        #5000;
        @(posedge clk);
        tx_surd_a = 16'd47; tx_surd_b = 16'd13;
        trig_en = 1;
        @(posedge clk);
        trig_en = 0;

        begin : wait3 integer t3; for (t3=0; t3<5000000 && !rx_ready; t3=t3+1) @(posedge clk); end
        $display("Test Case 3 (a=47, b=13): RX_a=%d, RX_b=%d", rx_surd_a, rx_surd_b);
        if (rx_surd_a == 47 && rx_surd_b == 13) begin
             $display("PASS: Compound Step reconstructed.");
        end else begin
             $display("FAIL: Reconstruction mismatch.");
        end

        #1000;
        $finish;
    end

endmodule
