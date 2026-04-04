// spu_whisper_bridge_tb.v — testbench for spu_whisper_bridge
// Verifies 4-byte UART packet: [0xAA, hi, lo, hi^lo]
`timescale 1ns/1ps

module spu_whisper_bridge_tb;

    reg        clk, rst_n;
    reg [12:0] whisper_frame;
    reg        strike_pulse;
    wire [7:0] uart_tx_byte;
    wire       uart_tx_en;

    spu_whisper_bridge dut (
        .clk(clk), .rst_n(rst_n),
        .whisper_frame(whisper_frame),
        .strike_pulse(strike_pulse),
        .uart_tx_byte(uart_tx_byte),
        .uart_tx_en(uart_tx_en)
    );

    initial clk = 0;
    always #20.833 clk = ~clk;  // 24 MHz

    reg [7:0] bytes_rx [0:3];
    integer   byte_cnt;
    integer   pass_count, fail_count;

    // Collect bytes as uart_tx_en fires
    always @(posedge clk) begin
        if (uart_tx_en && byte_cnt < 4) begin
            bytes_rx[byte_cnt] = uart_tx_byte;
            byte_cnt = byte_cnt + 1;
        end
    end

    task send_frame;
        input [12:0] frame;
        begin
            byte_cnt      = 0;
            whisper_frame = frame;
            @(posedge clk); #1;
            strike_pulse = 1;
            @(posedge clk); #1;
            strike_pulse = 0;
            // Wait enough cycles for all 4 bytes (4×2 cycles = 8 + margin)
            repeat(20) @(posedge clk);
        end
    endtask

    initial begin
        rst_n = 0; strike_pulse = 0; whisper_frame = 13'h0;
        pass_count = 0; fail_count = 0;
        #200; rst_n = 1; #100;

        // --- T1: frame = 13'h1A5C → hi=5'h0D lo=8'h5C ---
        //   byte0 = 0xAA
        //   byte1 = {3'b0, 5'h0D} = 0x0D
        //   byte2 = 0x5C
        //   byte3 = 0x0D ^ 0x5C = 0x51
        send_frame(13'h0D5C);

        if (bytes_rx[0] === 8'hAA && bytes_rx[1] === 8'h0D &&
            bytes_rx[2] === 8'h5C && bytes_rx[3] === 8'h51) begin
            $display("T1 PASS: packet [AA,0D,5C,51] correct");
            pass_count = pass_count + 1;
        end else begin
            $display("T1 FAIL: got [%02h,%02h,%02h,%02h] expected [AA,0D,5C,51]",
                bytes_rx[0], bytes_rx[1], bytes_rx[2], bytes_rx[3]);
            fail_count = fail_count + 1;
        end

        // --- T2: frame = 13'h1FFF → hi=5'h1F lo=8'hFF ---
        //   byte1 = 0x1F, byte2 = 0xFF, byte3 = 0x1F^0xFF = 0xE0
        send_frame(13'h1FFF);

        if (bytes_rx[0] === 8'hAA && bytes_rx[1] === 8'h1F &&
            bytes_rx[2] === 8'hFF && bytes_rx[3] === 8'hE0) begin
            $display("T2 PASS: packet [AA,1F,FF,E0] correct");
            pass_count = pass_count + 1;
        end else begin
            $display("T2 FAIL: got [%02h,%02h,%02h,%02h] expected [AA,1F,FF,E0]",
                bytes_rx[0], bytes_rx[1], bytes_rx[2], bytes_rx[3]);
            fail_count = fail_count + 1;
        end

        // --- T3: all-zero frame ---
        //   byte1=0x00 byte2=0x00 byte3=0x00
        send_frame(13'h0000);

        if (bytes_rx[0] === 8'hAA && bytes_rx[1] === 8'h00 &&
            bytes_rx[2] === 8'h00 && bytes_rx[3] === 8'h00) begin
            $display("T3 PASS: zero frame correct");
            pass_count = pass_count + 1;
        end else begin
            $display("T3 FAIL: got [%02h,%02h,%02h,%02h]",
                bytes_rx[0], bytes_rx[1], bytes_rx[2], bytes_rx[3]);
            fail_count = fail_count + 1;
        end

        if (fail_count == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail_count);

        $finish;
    end

    initial #500000 begin $display("FAIL (timeout)"); $finish; end

endmodule
