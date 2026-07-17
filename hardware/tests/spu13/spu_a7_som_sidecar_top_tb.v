`timescale 1ns / 1ps

// Board-wrapper regression for the Artix SOM-SIDECAR.  The comprehensive
// functional regression remains spu13_tang25k_som_sidecar_top_tb.v; this test
// proves the Artix wrapper preserves the external SPI and UART paths while
// reading a complete CRC-checked SOM1 frame from the shared implementation.

module spu_a7_som_sidecar_top_tb;
    reg  sys_clk = 1'b0;
    reg  spi_cs_n = 1'b1;
    reg  spi_sck = 1'b0;
    reg  spi_mosi = 1'b0;
    wire spi_miso;
    wire uart_tx;

    spu_a7_som_sidecar_top dut (
        .sys_clk(sys_clk),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .uart_tx(uart_tx)
    );

    always #10 sys_clk = ~sys_clk; // 50 MHz

    localparam SCK_HALF = 250;
    localparam BIT_PERIOD = 8680;

    task automatic spi_xfer_byte(input [7:0] tx, output [7:0] rx);
        integer i;
        begin
            for (i = 7; i >= 0; i = i - 1) begin
                spi_mosi = tx[i];
                #(SCK_HALF);
                spi_sck = 1'b1;
                rx[i] = spi_miso;
                #(SCK_HALF);
                spi_sck = 1'b0;
            end
        end
    endtask

    function [7:0] byte_of;
        input [63:0] value;
        input integer index;
        begin
            byte_of = value[(7-index)*8 +: 8];
        end
    endfunction

    task automatic spi_write_cfg(
        input [2:0] sel,
        input [9:0] addr,
        input [63:0] data
    );
        reg [63:0] header;
        reg [7:0] rx;
        integer i;
        begin
            header = {8'hA5, 5'd0, sel, 4'd0, addr, 34'd0};
            spi_cs_n = 1'b0;
            spi_xfer_byte(8'hA5, rx);
            for (i = 0; i < 8; i = i + 1)
                spi_xfer_byte(byte_of(header, i), rx);
            for (i = 0; i < 8; i = i + 1)
                spi_xfer_byte(byte_of(data, i), rx);
            spi_xfer_byte(8'h00, rx);
            #(SCK_HALF);
            spi_cs_n = 1'b1;
            #20;
        end
    endtask

    task automatic write_feature(input [1:0] feature, input [17:0] value);
        begin
            spi_write_cfg(3'd5, {8'd0, feature}, {46'd0, value});
        end
    endtask

    task automatic read_som1(output [415:0] frame);
        reg [7:0] ignored;
        reg [7:0] value;
        integer i;
        begin
            spi_cs_n = 1'b0;
            spi_xfer_byte(8'h02, ignored);
            for (i = 0; i < 52; i = i + 1) begin
                spi_xfer_byte(8'h00, value);
                frame[(51-i)*8 +: 8] = value;
            end
            #(SCK_HALF);
            spi_cs_n = 1'b1;
            #20;
        end
    endtask

    task automatic uart_rx_byte(output [7:0] value);
        integer i;
        begin
            @(negedge uart_tx);
            #(BIT_PERIOD + BIT_PERIOD/2);
            for (i = 0; i < 8; i = i + 1) begin
                value[i] = uart_tx;
                #(BIT_PERIOD);
            end
        end
    endtask

    function [31:0] crc32_byte;
        input [31:0] crc;
        input [7:0] data;
        reg [31:0] state;
        integer bit_index;
        begin
            state = crc ^ data;
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1)
                state = state[0] ? ((state >> 1) ^ 32'hEDB88320) :
                                   (state >> 1);
            crc32_byte = state;
        end
    endfunction

    function [31:0] frame_crc;
        input [415:0] frame;
        reg [31:0] state;
        integer i;
        begin
            state = 32'hFFFFFFFF;
            for (i = 0; i < 48; i = i + 1)
                state = crc32_byte(state, frame[(51-i)*8 +: 8]);
            frame_crc = ~state;
        end
    endfunction

    reg [7:0] telemetry;
    reg [415:0] som1;

    initial begin
        #6000; // internal power-on reset

        // Built-in map: input feature 0 = 2 selects node 1 exactly; node 0
        // is runner-up at quadrance 4.  Other features remain zero.
        write_feature(2'd0, 18'd2);
        write_feature(2'd1, 18'd0);
        write_feature(2'd2, 18'd0);
        write_feature(2'd3, 18'd0);
        spi_write_cfg(3'd6, 10'd0, 64'd0);
        uart_rx_byte(telemetry);
        wait (dut.u_sidecar.som1_frame_ready);
        read_som1(som1);

        if (telemetry !== 8'h09) begin
            $display("FAIL: Artix wrapper UART got %02X, expected 09", telemetry);
            $finish;
        end
        if (som1[415:384] !== 32'h534F4D31 ||
            som1[383:376] !== 8'd1 || som1[375:368] !== 8'd52 ||
            som1[367:360] !== 8'h15 || som1[359:352] !== 8'd0 ||
            som1[351:320] !== 32'd0 || som1[319:288] !== 32'd1 ||
            som1[287:272] !== 16'd1 || som1[271:256] !== 16'd0 ||
            som1[255:240] !== 16'd1 || som1[239:224] !== 16'd0 ||
            som1[223:160] !== 64'd0 ||
            som1[159:96] !== {32'd4, 32'd0} ||
            som1[95:32] !== {32'd4, 32'd0} ||
            som1[31:0] !== frame_crc(som1)) begin
            $display("FAIL: Artix wrapper SOM1 frame %0104X", som1);
            $finish;
        end

        $display("PASS: Artix wrapper preserved SPI, UART, and SOM1 frame");
        $finish;
    end

    initial begin
        #2_000_000;
        $display("FAIL: Artix SOM-SIDECAR wrapper timeout");
        $finish;
    end
endmodule
