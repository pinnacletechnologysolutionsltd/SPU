// spu_spi_slave_tb.v — testbench for spu_spi_slave
// Tests CMD 0xA0 (32-byte manifold burst) and CMD 0xAC (4-byte status)
`timescale 1ns/1ps

module spu_spi_slave_tb;

    reg        clk, rst_n;
    reg        spi_cs_n, spi_sck, spi_mosi;
    wire       spi_miso;

    // RPLU CFG outputs (observed only in advanced tests)
    wire       rplu_cfg_wr_en;
    wire [2:0] rplu_cfg_sel;
    wire [7:0] rplu_cfg_material;
    wire [9:0] rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;

    // Drive a known manifold: axis0 P=16'h1234 Q=16'h0056,
    //                         axis1 P=16'hABCD Q=16'h0078, rest 0
    reg [831:0] manifold_state;
    reg [3:0]   satellite_snaps;
    reg         is_janus_point;
    reg [15:0]  dissonance;
    // Testbench hooks for RPLU comparator (tie-off)
    reg signed [2:0] tb_rplu_ratio_res = 3'sd0;
    reg              tb_rplu_ratio_valid = 1'b0;

    spu_spi_slave dut (
        .clk(clk), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(manifold_state),
        .satellite_snaps(satellite_snaps),
        .is_janus_point(is_janus_point),
        .dissonance(dissonance),
        .scale_table(52'd0), .scale_overflow(13'd0),
        .rplu_ratio_res(tb_rplu_ratio_res), .rplu_ratio_valid(tb_rplu_ratio_valid),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .fifo_full(1'b0),
        .laminar_index(dissonance),
        .turbulence(1'b0),
        .rplu_mode(1'b0),
        .sentinel_telemetry(512'd0)
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
    reg        seen_cfg_wr;
    reg [2:0]  seen_cfg_sel;
    reg [7:0]  seen_cfg_material;
    reg [9:0]  seen_cfg_addr;
    reg [63:0] seen_cfg_data;

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

    task spi_u64_send;
        input [63:0] word;
        integer b;
        reg [7:0] dummy;
        begin
            for (b = 7; b >= 0; b = b - 1)
                spi_byte_send(word[b*8 +: 8], dummy);
        end
    endtask

    task spi_rplu_write;
        input [63:0] header;
        input [63:0] data;
        reg [7:0] dummy;
        begin
            spi_cs_n = 0;
            #500;
            spi_byte_send(8'hA5, dummy);
            spi_u64_send(header);
            spi_u64_send(data);
            #500;
            spi_cs_n = 1;
            #2000;
        end
    endtask

    function [63:0] rplu_header;
        input [2:0] sel;
        input [3:0] material;
        input [9:0] addr;
        begin
            rplu_header = 64'd0;
            rplu_header[63:56] = 8'hA5;
            rplu_header[50:48] = sel;
            rplu_header[47:44] = material;
            rplu_header[43:34] = addr;
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            seen_cfg_wr <= 1'b0;
            seen_cfg_sel <= 3'd0;
            seen_cfg_material <= 8'd0;
            seen_cfg_addr <= 10'd0;
            seen_cfg_data <= 64'd0;
        end else if (rplu_cfg_wr_en) begin
            seen_cfg_wr <= 1'b1;
            seen_cfg_sel <= rplu_cfg_sel;
            seen_cfg_material <= rplu_cfg_material;
            seen_cfg_addr <= rplu_cfg_addr;
            seen_cfg_data <= rplu_cfg_data;
        end
    end

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

        // --- T2: CMD 0xAC — 4-byte status ---
        spi_transaction(8'hAC, 4);

        // laminar_index=0xBEEF; flags bit1=janus=1, bit0=snaps[0]=0 -> 0x02; rplu_mode=0
        if (rx_buf[0] === 8'hBE && rx_buf[1] === 8'hEF &&
            rx_buf[2] === 8'h02 && rx_buf[3] === 8'h00) begin
            $display("T2 PASS: status bytes correct (laminar=BEEF flags=02 mode=00)");
            pass_count = pass_count + 1;
        end else begin
            $display("T2 FAIL: [%02h,%02h,%02h,%02h] expected BE,EF,02,00",
                rx_buf[0], rx_buf[1], rx_buf[2], rx_buf[3]);
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

        // --- T4: CMD 0xA5 RPLU write with material ID 7 ---
        seen_cfg_wr = 1'b0;
        spi_rplu_write(rplu_header(3'd5, 4'd7, 10'h123), 64'h1122_3344_5566_7788);
        if (seen_cfg_wr &&
            seen_cfg_sel === 3'd5 &&
            seen_cfg_material === 8'd7 &&
            seen_cfg_addr === 10'h123 &&
            seen_cfg_data === 64'h1122_3344_5566_7788) begin
            $display("T4 PASS: RPLU material 7 config decoded");
            pass_count = pass_count + 1;
        end else begin
            $display("T4 FAIL: wr=%b sel=%0d material=%0d addr=%h data=%h",
                seen_cfg_wr, seen_cfg_sel, seen_cfg_material, seen_cfg_addr, seen_cfg_data);
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
