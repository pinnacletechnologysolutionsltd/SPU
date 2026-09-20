`timescale 1ns/1ps

// D1 simulation: the real T1d UART/loader/GPU top with diagnostic TX enabled.
// The test deliberately repeats the identical transaction after warm reset and
// decodes the independent 16-byte diagnostic records from diag_tx.

`ifdef GPU_T1D_DIAG
module spu_t1d_repeatability_diag_tb;
    localparam integer BIT_CYCLES = 217;
    localparam [503:0] SCENE =
        504'h0e10019002bc0f000043620ffb0fe34ffffb820fe2001cc000000000230000001900e1002bc00f00043620fe20fe34ffffb820ffb001cc0000000002300000;

    reg sys_clk = 1'b0;
    reg rst_n = 1'b0;
    reg uart_rx = 1'b1;
    wire diag_tx;
    wire vga_r, vga_g, vga_b, vga_hsync, vga_vsync;
    integer failures = 0;
    integer start_phase = 0;
    integer reset_phase = 0;
    integer i;

    always #10 sys_clk = ~sys_clk;

    spu_a7_gpu_vga_top #(
        .PREPARED_SCENE(1),
        .COST_STIMULUS(0)
    ) dut (
        .sys_clk(sys_clk), .rst_n(rst_n), .uart_rx(uart_rx),
        .vga_r(vga_r), .vga_g(vga_g), .vga_b(vga_b),
        .vga_hsync(vga_hsync), .vga_vsync(vga_vsync),
        .diag_tx(diag_tx)
    );

    task check(input condition, input [8*120-1:0] label);
        begin
            if (condition !== 1'b1) begin
                failures = failures + 1;
                $display("FAIL: %0s", label);
            end
        end
    endtask

    task tick_pixel(input integer count);
        integer n;
        begin
            for (n = 0; n < count; n = n + 1)
                @(posedge dut.clk_pixel);
        end
    endtask

    task send_byte(input [7:0] value);
        integer bit_index;
        begin
            uart_rx = 1'b0;
            tick_pixel(BIT_CYCLES);
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                uart_rx = value[bit_index];
                tick_pixel(BIT_CYCLES);
            end
            uart_rx = 1'b1;
            tick_pixel(BIT_CYCLES);
        end
    endtask

    task send_scene;
        integer byte_index;
        begin
            tick_pixel(start_phase);
            send_byte(8'hA5);
            for (byte_index = 0; byte_index < 63; byte_index = byte_index + 1)
                send_byte(SCENE[byte_index*8 +: 8]);
        end
    endtask

    task board_reset;
        begin
            rst_n = 1'b0;
            uart_rx = 1'b1;
            repeat (65536) @(posedge sys_clk);
            wait (dut.pix_rst_n === 1'b0);
            rst_n = 1'b1;
            wait (dut.pix_rst_n === 1'b1);
            tick_pixel(reset_phase);
        end
    endtask

    task read_record(output reg [127:0] record);
        integer bit_index;
        integer byte_index;
        integer data_bit;
        begin
            record = 128'd0;
            wait (dut.u_diag_uart_tx.busy === 1'b1);
            tick_pixel(BIT_CYCLES / 2);
            for (bit_index = 0; bit_index < 160; bit_index = bit_index + 1) begin
                if ((bit_index % 10) == 0 || (bit_index % 10) == 9)
                    check(((bit_index % 10) == 0) ? (diag_tx === 1'b0) :
                          (diag_tx === 1'b1),
                          "diagnostic UART start/stop bit is valid");
                else begin
                    byte_index = bit_index / 10;
                    data_bit = (bit_index % 10) - 1;
                    record[byte_index*8 + data_bit] = diag_tx;
                end
                if (bit_index != 159)
                    tick_pixel(BIT_CYCLES);
            end
            wait (dut.u_diag_uart_tx.busy === 1'b0);
        end
    endtask

    task check_ready_record(input [127:0] record);
        begin
            check(record[7:0] === 8'hD7, "READY magic");
            check(record[15:8] === 8'h01, "READY version");
            check(record[23:16] === 8'h01, "READY record type");
            check(record[31:24] === 8'h00, "READY sequence");
            check(record[39:32] === 8'h01, "READY flags");
            check(record[47:40] === 8'h00, "READY accepted count");
            check(record[63:48] === 16'h0000, "READY payload CRC");
            check(record[71:64] === 8'h00, "READY active bank");
            check(record[79:72] === 8'h01, "READY terminal reason");
            check(record[103:96] === 8'h01, "READY state");
            check(record[119:112] === 8'h2F, "READY record CRC8");
            check(record[127:120] === 8'h7E, "READY terminal marker");
        end
    endtask

    task check_transaction_record(input [127:0] record);
        begin
            check(record[7:0] === 8'hD7, "transaction magic");
            check(record[15:8] === 8'h01, "transaction version");
            check(record[23:16] === 8'h02, "transaction record type");
            check(record[31:24] === 8'h01, "transaction sequence");
            check(record[39:32] === 8'h7B, "transaction flags");
            check(record[47:40] === 8'h3F, "transaction accepted count");
            check(record[63:48] === 16'h7920, "transaction payload CRC");
            check(record[71:64] === 8'h01, "transaction active bank");
            check(record[79:72] === 8'h02, "transaction activation reason");
            check(record[95:80] === 16'h0000, "transaction frame wait");
            check(record[103:96] === 8'h01, "transaction ready state");
            check(record[119:112] === 8'h7B, "transaction record CRC8");
            check(record[127:120] === 8'h7E, "transaction terminal marker");
        end
    endtask

    reg [127:0] ready_record;
    reg [127:0] transaction_record;

    initial begin
        if (!$value$plusargs("START_PHASE=%d", start_phase)) start_phase = 0;
        if (!$value$plusargs("RESET_PHASE=%d", reset_phase)) reset_phase = 0;

        board_reset();
        read_record(ready_record);
        check_ready_record(ready_record);
        send_scene();
        read_record(transaction_record);
        check_transaction_record(transaction_record);
        check(dut.u_gpu.u_scene_loader.active_scene === SCENE,
              "first diagnostic transaction activates the frozen scene");
        check(!dut.u_gpu.u_scene_loader.commit_pending,
              "first diagnostic transaction clears commit pending");

        board_reset();
        read_record(ready_record);
        check_ready_record(ready_record);
        send_scene();
        read_record(transaction_record);
        check_transaction_record(transaction_record);
        check(dut.u_gpu.u_scene_loader.active_scene === SCENE,
              "reset/re-arm transaction activates the frozen scene");
        check(vga_r !== 1'bx && vga_g !== 1'bx && vga_b !== 1'bx,
              "diagnostic instrumentation leaves VGA outputs defined");

        if (failures == 0)
            $display("PASS: T1d repeatability diagnostic D1");
        else
            $display("FAIL: T1d repeatability diagnostic failures=%0d", failures);
        $finish;
    end
endmodule
`else
module spu_t1d_repeatability_diag_tb;
    initial begin
        $display("SKIP: T1d repeatability diagnostic requires GPU_T1D_DIAG");
        $finish;
    end
endmodule
`endif
