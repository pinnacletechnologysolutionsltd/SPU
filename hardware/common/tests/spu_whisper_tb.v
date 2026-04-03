`timescale 1ns/1ps

module spu_whisper_tb;

    reg clk;
    reg rst_n;

    // TX — current port names: trig_en, is_sync, surd_a, surd_b, pwi_out, tx_ready
    reg  [15:0] surd_a, surd_b;
    reg  trig_en;
    wire pwi_link;
    wire tx_ready;

    SPU_WHISPER_TX #(
        .K_FACTOR(1),
        .BIAS(16'd0)
    ) tx (
        .clk(clk), .rst_n(rst_n),
        .trig_en(trig_en), .is_sync(1'b0),
        .surd_a(surd_a), .surd_b(surd_b),
        .pwi_out(pwi_link), .tx_ready(tx_ready)
    );

    // RX — current port names: pwi_in, is_cal, surd_a, surd_b, rx_ready
    wire signed [15:0] rx_a, rx_b;
    wire rx_ready;

    SPU_WHISPER_RX #(
        .BIAS(16'd0)
    ) rx (
        .clk(clk), .rst_n(rst_n),
        .pwi_in(pwi_link), .is_cal(1'b0),
        .surd_a(rx_a), .surd_b(rx_b),
        .rx_ready(rx_ready)
    );

    always #40 clk = ~clk;

    integer timeout;
    task send_and_check;
        input [15:0] a_in, b_in;
        begin
            @(posedge clk);
            surd_a = a_in; surd_b = b_in; trig_en = 1;
            @(posedge clk);
            trig_en = 0;
            timeout = 0;
            while (!rx_ready && timeout < 5000000) begin
                @(posedge clk);
                timeout = timeout + 1;
            end
            if (!rx_ready) begin
                $display("FAIL: rx_ready timeout for a=%0d b=%0d", a_in, b_in);
            end else if (rx_a == $signed(a_in) && rx_b == $signed(b_in)) begin
                $display("PASS: a=%0d b=%0d → rx_a=%0d rx_b=%0d", a_in, b_in, rx_a, rx_b);
            end else begin
                $display("FAIL: a=%0d b=%0d mismatch rx_a=%0d rx_b=%0d", a_in, b_in, rx_a, rx_b);
            end
        end
    endtask

    initial begin
        $dumpfile("whisper_trace.vcd");
        $dumpvars(0, spu_whisper_tb);
        clk = 0; rst_n = 0; trig_en = 0; surd_a = 0; surd_b = 0;
        #200; rst_n = 1; #200;

        $display("--- Whisper PWI Loopback Test (BIAS=0, K=1) ---");
        send_and_check(16'd1,  16'd0);
        send_and_check(16'd0,  16'd1);
        send_and_check(16'd5,  16'd3);
        $display("--- Whisper Test Complete ---");

        #100;
        $finish;
    end

endmodule

