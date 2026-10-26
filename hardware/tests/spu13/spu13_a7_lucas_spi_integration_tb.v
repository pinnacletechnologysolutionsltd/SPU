`timescale 1ns / 1ps

// End-to-end regression for the Wukong LUCAS spin.  This deliberately drives
// the board top's physical SPI pins: B1 + CRC must cross spu_spi_slave, reach
// the Lucas sidecar, return through the top-level QR mux, and be observable via
// an AE response.  The four vectors are the rp2350_lucas_j11_smoke oracle.
//
// It also reads the AC status frame after each case, which pins the golden
// value of the chord-dispatch breadcrumbs the board top has always latched
// (spu_a7_top.v:409-451) and the slave has always published.  A healthy case
// leaves "5A <opcode> 13 00" -- opcode latched from spi_inst_valid, sidecar
// claim and commit both set, no error.  That frame is what the bench firmware
// already prints, so a silicon capture compares byte for byte.
module spu13_a7_lucas_spi_integration_tb;
    localparam integer SCK_HALF_NS = 40; // 100 MHz clk, 12.5 MHz SCK: ratio 8
    // Production sidecar uses MAC_CE_DIV=64.  This exceeds the standalone
    // bench's MAC_CE_DIV*2048 PINV guard without shortening the board-top
    // configuration for simulation.
    localparam integer SETTLE_CLKS = 150000;

    reg clk_100mhz = 1'b0;
    reg rst_n = 1'b0;
    reg spi_cs_n = 1'b1;
    reg spi_sck = 1'b0;
    reg spi_mosi = 1'b0;
    wire spi_miso;
    wire uart_tx;
    wire [3:0] hdmi_d_p, hdmi_d_n;
    wire hdmi_clk_p, hdmi_clk_n;
    wire i2s_bclk, i2s_lrclk, i2s_dout;
    wire [3:0] led_out;
    wire fault_led;

    reg [7:0] rx_buf [0:33];
    reg [7:0] status_buf [0:3];
    integer errors = 0;

    always #5 clk_100mhz = ~clk_100mhz;

    spu_a7_top #(
        .DEVICE("A7_100T"),
        .SPIN("LUCAS"),
        .A7_CLK_DIV_LOG2(0),
        .A7_UART_DIAG(0)
    ) dut (
        .clk_100mhz(clk_100mhz),
        .rst_n(rst_n),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .uart_tx(uart_tx),
        .hdmi_d_p(hdmi_d_p),
        .hdmi_d_n(hdmi_d_n),
        .hdmi_clk_p(hdmi_clk_p),
        .hdmi_clk_n(hdmi_clk_n),
        .i2s_bclk(i2s_bclk),
        .i2s_lrclk(i2s_lrclk),
        .i2s_dout(i2s_dout),
        .sensor_in(8'd0),
        .led_out(led_out),
        .fault_led(fault_led)
    );

    function automatic [7:0] crc8_byte;
        input [7:0] crc;
        input [7:0] byte_data;
        reg [7:0] state;
        integer bit_index;
        begin
            state = crc;
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                if (state[7] != byte_data[7-bit_index])
                    state = {state[6:0], 1'b0} ^ 8'h07;
                else
                    state = {state[6:0], 1'b0};
            end
            crc8_byte = state;
        end
    endfunction

    function automatic [7:0] chord_crc;
        input [63:0] word;
        reg [7:0] state;
        integer byte_index;
        begin
            state = crc8_byte(8'h00, 8'hB1);
            for (byte_index = 0; byte_index < 8; byte_index = byte_index + 1)
                state = crc8_byte(state, word[63-byte_index*8 -: 8]);
            chord_crc = state;
        end
    endfunction

    task automatic spi_xfer_byte;
        input [7:0] tx;
        output [7:0] rx;
        integer bit_index;
        begin
            rx = 8'h00;
            for (bit_index = 7; bit_index >= 0; bit_index = bit_index - 1) begin
                spi_mosi = tx[bit_index];
                #(SCK_HALF_NS);
                spi_sck = 1'b1;
                rx[bit_index] = spi_miso;
                #(SCK_HALF_NS);
                spi_sck = 1'b0;
            end
        end
    endtask

    task automatic spi_write_chord;
        input [63:0] word;
        reg [7:0] ignored;
        integer byte_index;
        begin
            spi_cs_n = 1'b0;
            #(2*SCK_HALF_NS);
            spi_xfer_byte(8'hB1, ignored);
            for (byte_index = 0; byte_index < 8; byte_index = byte_index + 1)
                spi_xfer_byte(word[63-byte_index*8 -: 8], ignored);
            spi_xfer_byte(chord_crc(word), ignored);
            #(2*SCK_HALF_NS);
            spi_cs_n = 1'b1;
            spi_mosi = 1'b0;
            repeat (SETTLE_CLKS) @(posedge clk_100mhz);
        end
    endtask

    task automatic spi_read_qr;
        reg [7:0] ignored;
        reg [7:0] value;
        integer byte_index;
        begin
            spi_cs_n = 1'b0;
            #(2*SCK_HALF_NS);
            spi_xfer_byte(8'hAE, ignored);
            for (byte_index = 0; byte_index < 34; byte_index = byte_index + 1) begin
                spi_xfer_byte(8'h00, value);
                rx_buf[byte_index] = value;
            end
            #(2*SCK_HALF_NS);
            spi_cs_n = 1'b1;
            repeat (32) @(posedge clk_100mhz);
        end
    endtask

    // CMD 0xAC status read, byte-for-byte what rp2350_lucas_j11_smoke's
    // print_status() emits.  On a LUCAS spin sidecar_status is 1, so the four
    // bytes carry the chord-dispatch breadcrumbs directly:
    //   [0] 0x5A                       — sidecar_status_hi literal
    //   [1] debug_last_spi_opcode      — latched on spi_inst_valid
    //   [2] {su3_state[2:0], ratio_valid, fifo_full, error, claim, commit}
    //   [3] {5'h0, boot_ready, crc_error_sticky, rplu_mode(busy)}
    // Byte 2 bit1 is debug_sidecar_claim_seen, bit0 debug_sidecar_commit_seen.
    task automatic spi_read_status;
        reg [7:0] ignored;
        reg [7:0] value;
        integer byte_index;
        begin
            spi_cs_n = 1'b0;
            #(2*SCK_HALF_NS);
            spi_xfer_byte(8'hAC, ignored);
            for (byte_index = 0; byte_index < 4; byte_index = byte_index + 1) begin
                spi_xfer_byte(8'h00, value);
                status_buf[byte_index] = value;
            end
            #(2*SCK_HALF_NS);
            spi_cs_n = 1'b1;
            repeat (32) @(posedge clk_100mhz);
        end
    endtask

    task automatic run_case;
        input [63:0] word;
        input [3:0] expected_lane;
        input [63:0] expected_a;
        input [8*16-1:0] label;
        reg [63:0] got_a, got_b, got_c, got_d;
        reg case_ok;
        reg status_ok;
        begin
            spi_write_chord(word);
            spi_read_qr();
            spi_read_status();
            got_a = {rx_buf[2],  rx_buf[3],  rx_buf[4],  rx_buf[5],
                     rx_buf[6],  rx_buf[7],  rx_buf[8],  rx_buf[9]};
            got_b = {rx_buf[10], rx_buf[11], rx_buf[12], rx_buf[13],
                     rx_buf[14], rx_buf[15], rx_buf[16], rx_buf[17]};
            got_c = {rx_buf[18], rx_buf[19], rx_buf[20], rx_buf[21],
                     rx_buf[22], rx_buf[23], rx_buf[24], rx_buf[25]};
            got_d = {rx_buf[26], rx_buf[27], rx_buf[28], rx_buf[29],
                     rx_buf[30], rx_buf[31], rx_buf[32], rx_buf[33]};
            case_ok = rx_buf[0] === 8'h01 &&
                      rx_buf[1][3:0] === expected_lane &&
                      got_a === expected_a && got_b === 64'd0 &&
                      got_c === 64'd0 && got_d === 64'd0;
            // A healthy dispatch leaves 0x5A <opcode> 0x13 in the status frame:
            // opcode latched from spi_inst_valid, claim and commit both sticky
            // high, error low.  This is the same frame the bench firmware
            // already prints, so a silicon capture is directly comparable.
            status_ok = status_buf[0] === 8'h5A &&
                        status_buf[1] === word[63:56] &&
                        status_buf[2][2] === 1'b0 &&
                        status_buf[2][1] === 1'b1 &&
                        status_buf[2][0] === 1'b1;
            if (!case_ok || !status_ok)
                errors = errors + 1;
            $display("case %0s %0s valid=%0d lane=%0d A=%016h",
                     label, case_ok ? "ok" : "bad",
                     rx_buf[0][0], rx_buf[1][3:0], got_a);
            $display("  status %0s raw=%02h %02h %02h %02h (IV/IW=%02h claim=%0d commit=%0d err=%0d)",
                     status_ok ? "ok" : "bad",
                     status_buf[0], status_buf[1], status_buf[2], status_buf[3],
                     status_buf[1], status_buf[2][1], status_buf[2][0],
                     status_buf[2][2]);
        end
    endtask

    initial begin
        repeat (16) @(posedge clk_100mhz);
        rst_n = 1'b1;
        // spu_a7_top debounces the reset pin: rst_n_int stays asserted until
        // rst_n has read high for 256 consecutive clk_100mhz cycles. Wait out
        // that release before driving SPI, or the first chord lands in reset.
        repeat (512) @(posedge clk_100mhz);

        run_case(64'hD0200C0500000000, 4'd2,
                 64'h0000000800000005, "PSCALE");
        run_case(64'hD1C00C0500000000, 4'd12,
                 64'h0000020400000008, "PCHIRAL");
        run_case(64'hD2300C0500807000, 4'd3,
                 64'h0000004200000029, "PMUL");
        run_case(64'hD3400C0500000000, 4'd4,
                 64'h0000000500000201, "PINV");

        if (errors == 0)
            $display("PASS");
        else
            $display("FAIL errors=%0d", errors);
        $finish;
    end

    initial begin
        #10_000_000;
        $display("FAIL timeout");
        $finish;
    end
endmodule
