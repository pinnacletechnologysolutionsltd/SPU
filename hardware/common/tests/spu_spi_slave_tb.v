// spu_spi_slave_tb.v — testbench for spu_spi_slave
// Tests CMD 0xA0 (32-byte manifold burst) and CMD 0xAC (3-byte status)
`timescale 1ns/1ps

module spu_spi_slave_tb;

    reg        clk, rst_n;
    reg        spi_cs_n, spi_sck, spi_mosi;
    wire       spi_miso;

    // Drive a known manifold: axis0 P=16'h1234 Q=16'h0056,
    //                         axis1 P=16'hABCD Q=16'h0078, rest 0
    reg [831:0] manifold_state;
    reg [3:0]   satellite_snaps;
    reg         is_janus_point;
    reg [15:0]  dissonance;

    spu_spi_slave dut (
        .clk(clk), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(manifold_state),
        .satellite_snaps(satellite_snaps),
        .is_janus_point(is_janus_point),
        .dissonance(dissonance)
    );

    // 24 MHz system clock
    initial clk = 0;
    always #20.833 clk = ~clk;  // ~24 MHz

    // SPI clock ~2 MHz — period 500 ns → half 250 ns
    task spi_byte_send;
        input [7:0] cmd;
        output [7:0] recv;
        integer i;
        begin
            recv = 8'h00;
            for (i = 7; i >= 0; i = i - 1) begin
                spi_mosi = cmd[i];
                #250;
                spi_sck = 1;
                recv[i] = spi_miso;
                #250;
                spi_sck = 0;
            end
        end
    endtask

    // SPI transaction: assert CS, send cmd, receive n_bytes
    reg [7:0] rx_buf [0:31];
    integer   pass_count, fail_count;

    task spi_transaction;
        input [7:0]  cmd;
        input integer n_bytes;
        integer b;
        reg [7:0] dummy;
        begin
            spi_cs_n = 0;
            #500;  // setup
            spi_byte_send(cmd, dummy);  // send command
            for (b = 0; b < n_bytes; b = b + 1)
                spi_byte_send(8'h00, rx_buf[b]);
            #500;
            spi_cs_n = 1;
            #1000;
        end
    endtask

    initial begin
        // Initialise
        spi_cs_n = 1; spi_sck = 0; spi_mosi = 0;
        rst_n = 0;
        pass_count = 0; fail_count = 0;

        // Drive manifold: axis0 P=0x1234 Q=0x0056, axis1 P=0xABCD Q=0x0078
        manifold_state = 832'h0;
        manifold_state[31:16] = 16'h1234;   // axis0 P
        manifold_state[15:0]  = 16'h0056;   // axis0 Q
        manifold_state[63:48] = 16'hABCD;   // axis1 P
        manifold_state[47:32] = 16'h0078;   // axis1 Q
        satellite_snaps  = 4'b1010;
        is_janus_point   = 1'b1;
        dissonance       = 16'hBEEF;

        #200;
        rst_n = 1;
        #500;

        // --- T1: CMD 0xA0 — 32-byte manifold burst ---
        spi_transaction(8'hA0, 32);

        // Axis 0: bytes 0-7 → P=0x1234 Q=0x0056
        if (rx_buf[0] === 8'h12 && rx_buf[1] === 8'h34 &&
            rx_buf[2] === 8'h00 && rx_buf[3] === 8'h00 &&
            rx_buf[4] === 8'h00 && rx_buf[5] === 8'h56 &&
            rx_buf[6] === 8'h00 && rx_buf[7] === 8'h00) begin
            $display("T1a PASS: axis0 bytes correct");
            pass_count = pass_count + 1;
        end else begin
            $display("T1a FAIL: axis0 P=[%02h,%02h] Q=[%02h,%02h] expected 12,34,00,56",
                rx_buf[0], rx_buf[1], rx_buf[4], rx_buf[5]);
            fail_count = fail_count + 1;
        end

        // Axis 1: bytes 8-15 → P=0xABCD Q=0x0078
        if (rx_buf[8]  === 8'hAB && rx_buf[9]  === 8'hCD &&
            rx_buf[12] === 8'h00 && rx_buf[13] === 8'h78) begin
            $display("T1b PASS: axis1 bytes correct");
            pass_count = pass_count + 1;
        end else begin
            $display("T1b FAIL: axis1 P=[%02h,%02h] Q=[%02h,%02h]",
                rx_buf[8], rx_buf[9], rx_buf[12], rx_buf[13]);
            fail_count = fail_count + 1;
        end

        // --- T2: CMD 0xAC — 3-byte status ---
        spi_transaction(8'hAC, 3);

        // dissonance=0xBEEF → bytes 0,1=BE,EF; flags bit1=janus=1, bit0=snaps[0]=0 → 0x02
        if (rx_buf[0] === 8'hBE && rx_buf[1] === 8'hEF && rx_buf[2] === 8'h02) begin
            $display("T2 PASS: status bytes correct (dis=BEEF flags=02)");
            pass_count = pass_count + 1;
        end else begin
            $display("T2 FAIL: [%02h,%02h,%02h] expected BE,EF,02",
                rx_buf[0], rx_buf[1], rx_buf[2]);
            fail_count = fail_count + 1;
        end

        // --- T3: unknown command --- 
        spi_transaction(8'hFF, 1);
        if (rx_buf[0] === 8'h00) begin
            $display("T3 PASS: unknown cmd returns 0x00");
            pass_count = pass_count + 1;
        end else begin
            $display("T3 FAIL: expected 0x00 got %02h", rx_buf[0]);
            fail_count = fail_count + 1;
        end

        if (fail_count == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail_count);

        $finish;
    end

    // Timeout
    initial #5000000 begin $display("FAIL (timeout)"); $finish; end

endmodule
