`timescale 1ns / 1ps

// spu13_tang25k_som_sidecar_top_tb.v -- bit-banged SPI + UART regression for
// the real Tang 25K SOM-SIDECAR board top (hardware/boards/tang_primer_25k/
// spu13_tang25k_som_sidecar_top.v). This is the module the SOM-SIDECAR spin
// actually synthesizes (synth_gowin_25k_spu13_som_sidecar.ys) and the module
// the existing RP2350 diag firmware (spu_diag.c: somwrite/featwrite/classify)
// drives over J-something USB-CDC -- distinct from, and previously
// name-colliding with, hardware/rtl/core/spu13/spu_som_sidecar_top.v (an
// unrelated cfg-bus/QR-commit variant with its own testbench).
//
// Drives the DUT exactly the way spu_link_write_rplu_cfg()/cmd_result() in
// hardware/rp_common/spu_link.c and spu_diag.c do: cmd(0xA5) + 8 header
// bytes + 8 data bytes + 1 crc byte for writes (header built the same way
// as spu_rplu_header()), and a single dummy-byte full-duplex transfer for
// the SPI status read. Also decodes the bit-banged UART telemetry byte,
// which is the reliable path a first-hour user actually watches.
//
// Regression case for the node-id truncation fix: node 4 aliases with node
// 0 under a 2-bit-truncated node id (100b -> 00b), so classifying onto node
// 4 is the case that would have silently misreported as node 0 before the
// fix in spu13_tang25k_som_sidecar_top.v (bmu_best[1:0] -> bmu_best[2:0]).
//
// This TB is also what caught a second, more severe bug: spu_spi_cfg.v's
// 0xA5 command-byte detection compared hdr[63:56] to 8'hA5 one cycle before
// the 8th bit's shift-in took effect, so no 0xA5 write ever matched -- the
// entire write/classify path was silently dead, in simulation and on real
// silicon, until fixed (see spu_spi_cfg.v). Separately (not fixed here):
// the SPI status-read path (cmd_result() in spu_diag.c, a single 8-clock
// dummy-byte transfer) used to read back 0x00: the DUT can only shift the
// result after consuming the command byte. The host now clocks a second byte,
// and this regression checks both that readback and UART telemetry.

module spu13_tang25k_som_sidecar_top_tb;

    reg  sys_clk;
    reg  spi_cs_n;
    reg  spi_sck;
    reg  spi_mosi;
    wire spi_miso;
    wire uart_tx_telemetry;
    wire [2:0] led;

    spu13_tang25k_som_sidecar_top dut (
        .sys_clk(sys_clk),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .uart_tx_telemetry(uart_tx_telemetry),
        .led(led)
    );

    // 50 MHz system clock
    always #10 sys_clk = ~sys_clk;

    // SPI clock: 2 MHz-equivalent bit period, far slower than sys_clk so the
    // DUT's 2-stage synchronizer always resolves within one SCK half period.
    localparam SCK_HALF = 250;

    // 115200 baud, matches CLKS_PER_BIT = 50_000_000/115200 in the DUT.
    localparam BIT_PERIOD = 8680;

    integer pass_count = 0;
    integer fail_count = 0;

    // ---- byte-at-a-time full-duplex SPI, MSB first, mode 0 -------------
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
        input [63:0] v;
        input integer idx; // 0 = MSB byte .. 7 = LSB byte
        begin
            byte_of = v[(7 - idx) * 8 +: 8];
        end
    endfunction

    // ---- 0xA5 write: cmd + 8 header bytes + 8 data bytes + 1 crc byte --
    // header layout matches hardware/rp_common/spu_link.c:spu_rplu_header()
    task automatic spi_write_rplu(input [2:0] sel, input [3:0] material,
                                   input [9:0] addr, input [63:0] data);
        reg [63:0] header;
        reg [7:0]  rx;
        integer    i;
        begin
            header = {8'hA5, 5'd0, sel, material, addr, 34'd0};
            spi_cs_n = 1'b0;
            spi_xfer_byte(8'hA5, rx);
            for (i = 0; i < 8; i = i + 1)
                spi_xfer_byte(byte_of(header, i), rx);
            for (i = 0; i < 8; i = i + 1)
                spi_xfer_byte(byte_of(data, i), rx);
            spi_xfer_byte(8'h00, rx); // crc byte, ignored by the DUT
            #(SCK_HALF);
            spi_cs_n = 1'b1;
            #20; // one sys_clk, just enough for a clean CS pulse in the waveform
        end
    endtask

    // ---- status nibble read, mirrors spu_diag.c's cmd_result() --------
    task automatic spi_read_status(output [7:0] resp);
        reg [7:0] ignored;
        begin
            spi_cs_n = 1'b0;
            spi_xfer_byte(8'h01, ignored);
            spi_xfer_byte(8'h00, resp);
            #(SCK_HALF);
            spi_cs_n = 1'b1;
            #20;
        end
    endtask

    task automatic write_weight(input [2:0] node, input [1:0] feat, input [17:0] p);
        begin
            spi_write_rplu(3'd4, 4'd0, {node, feat}, {46'd0, p});
        end
    endtask

    task automatic write_feature(input [1:0] feat, input [17:0] p);
        begin
            spi_write_rplu(3'd5, 4'd0, {8'd0, feat}, {46'd0, p});
        end
    endtask

    // ---- UART RX: LSB-first 8N1, samples mid-bit ------------------------
    task automatic uart_rx_byte(output [7:0] data);
        integer i;
        begin
            @(negedge uart_tx_telemetry);
            #(BIT_PERIOD + BIT_PERIOD / 2);
            for (i = 0; i < 8; i = i + 1) begin
                data[i] = uart_tx_telemetry;
                #(BIT_PERIOD);
            end
        end
    endtask

    task automatic classify_and_check(input [2:0] expect_node, input [287:0] label_str);
        reg [7:0] tel;
        reg [7:0] status_resp;
        begin
            spi_write_rplu(3'd6, 4'd0, 10'd0, 64'd0); // classify
            uart_rx_byte(tel);
            spi_read_status(status_resp); // informational only, see header note
            if (tel[2:0] == expect_node) begin
                $display("PASS %0s: best_node=%0d (telemetry=0x%02X, status_read=0x%02X)",
                          label_str, tel[2:0], tel, status_resp);
                pass_count = pass_count + 1;
            end else begin
                $display("FAIL %0s: best_node=%0d, expected %0d (telemetry=0x%02X)",
                          label_str, tel[2:0], expect_node, tel);
                fail_count = fail_count + 1;
            end
            if (status_resp[7] && !status_resp[6] &&
                status_resp[5:4] == tel[4:3]) begin
                $display("PASS %0s: status valid/idle/label=0x%02X",
                         label_str, status_resp);
                pass_count = pass_count + 1;
            end else begin
                $display("FAIL %0s: bad status=0x%02X for telemetry=0x%02X",
                         label_str, status_resp, tel);
                fail_count = fail_count + 1;
            end
        end
    endtask

    initial begin
        sys_clk = 1'b0;
        spi_cs_n = 1'b1;
        spi_sck = 1'b0;
        spi_mosi = 1'b0;

        #6000; // clear the DUT's internal 255-cycle power-on reset

        // Node 0: feat0 = 2. Node 4: feat2 = 7. Node 6: feat3 = 4.
        // Nodes 4 and 6 are exactly the cases that would have aliased to
        // nodes 0 and 2 under the pre-fix 2-bit-truncated telemetry field.
        write_weight(3'd0, 2'd0, 18'd2);
        write_weight(3'd4, 2'd2, 18'd7);
        write_weight(3'd6, 2'd3, 18'd4);

        // --- Test 1: feature {2,0,0,0} -> node 0 ---
        write_feature(2'd0, 18'd2);
        write_feature(2'd1, 18'd0);
        write_feature(2'd2, 18'd0);
        write_feature(2'd3, 18'd0);
        classify_and_check(3'd0, "test1 node0");

        // --- Test 2: feature {0,0,7,0} -> node 4 (the alias-with-0 case) ---
        write_feature(2'd0, 18'd0);
        write_feature(2'd2, 18'd7);
        classify_and_check(3'd4, "test2 node4 (truncation regression)");

        // --- Test 3: feature {0,0,0,4} -> node 6 ---
        write_feature(2'd2, 18'd0);
        write_feature(2'd3, 18'd4);
        classify_and_check(3'd6, "test3 node6");

        if (fail_count == 0)
            $display("PASS: %0d checks passed", pass_count);
        else
            $display("FAIL: %0d passed, %0d failed", pass_count, fail_count);

        $finish;
    end

    // Safety timeout
    initial begin
        #3_000_000;
        $display("FAIL: testbench timeout");
        $finish;
    end

endmodule
