`timescale 1ns/1ps

module spu_t1d_uart_loader_tb;
    localparam integer BIT_CYCLES = 217;
    localparam [503:0] SCENE =
        504'hbbb8b5b2afaca9a6a3a09d9a9794918e8b8885827f7c797673706d6a6764615e5b5855524f4c494643403d3a3734312e2b2825221f1c191613100d0a070401;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg uart_rx = 1'b1;
    reg frame_start = 1'b0;
    wire [7:0] rx_byte;
    wire rx_valid;
    wire frame_err;
    wire [503:0] active_scene;
    wire [503:0] candidate_scene;
    wire commit_pending;
    integer failures = 0;
    integer i;

    always #20 clk = ~clk;

    spu_uart_rx #(.CLK_HZ(25_000_000), .BAUD(115200)) u_rx (
        .clk(clk), .rst_n(rst_n), .rx(uart_rx),
        .data(rx_byte), .valid(rx_valid), .frame_err(frame_err));

    spu_scene_loader u_loader (
        .clk(clk), .rst_n(rst_n), .rx_byte(rx_byte), .rx_valid(rx_valid),
        .activate_raw_bank(frame_start), .active_scene(active_scene),
        .candidate_scene(candidate_scene), .commit_pending(commit_pending));

    task tick(input integer count);
        integer n;
        begin
            for (n = 0; n < count; n = n + 1) @(posedge clk);
        end
    endtask

    task send_byte(input [7:0] value);
        integer bit_index;
        begin
            uart_rx = 1'b0;
            tick(BIT_CYCLES);
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                uart_rx = value[bit_index];
                tick(BIT_CYCLES);
            end
            uart_rx = 1'b1;
            tick(BIT_CYCLES);
        end
    endtask

    task send_byte_phase(input [7:0] value, input integer phase_ns);
        integer bit_index;
        begin
            #(phase_ns);
            uart_rx = 1'b0;
            tick(BIT_CYCLES);
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                uart_rx = value[bit_index];
                tick(BIT_CYCLES);
            end
            uart_rx = 1'b1;
            tick(BIT_CYCLES);
        end
    endtask

    task reset_dut;
        begin
            rst_n = 1'b0;
            uart_rx = 1'b1;
            frame_start = 1'b0;
            tick(4);
            rst_n = 1'b1;
            tick(4);
        end
    endtask

    task send_scene_phase(input integer phase_ns);
        integer byte_index;
        begin
            send_byte_phase(8'hA5, phase_ns);
            for (byte_index = 0; byte_index < 63; byte_index = byte_index + 1)
                send_byte_phase(SCENE[byte_index*8 +: 8], 0);
        end
    endtask

    task check(input condition, input [8*96-1:0] label);
        begin
            if (condition !== 1'b1) begin
                failures = failures + 1;
                $display("FAIL: %0s", label);
            end
        end
    endtask

    initial begin
        reset_dut();
        check(active_scene === 504'b0, "reset active scene is clear");
        check(!commit_pending, "reset has no pending activation");

        // A packet stopped at each required accepted-byte boundary remains
        // incomplete and cannot request activation.
        send_byte(8'hA5);
        check(!commit_pending, "start byte alone cannot commit");
        send_byte(SCENE[0 +: 8]);
        check(!commit_pending, "one payload byte cannot commit");
        reset_dut();
        check(!commit_pending && active_scene === 504'b0,
              "early reset during reception clears loader state");
        send_byte(8'hA5);
        for (i = 1; i < 32; i = i + 1)
            send_byte(SCENE[i*8 +: 8]);
        check(!commit_pending, "33 wire bytes cannot commit");
        for (i = 32; i < 62; i = i + 1)
            send_byte(SCENE[i*8 +: 8]);
        check(!commit_pending, "63 wire bytes cannot commit");
        check(active_scene === 504'b0, "incomplete packet leaves active scene clear");

        // Reset during a partial packet clears receive state and staged data.
        reset_dut();
        check(!commit_pending && active_scene === 504'b0,
              "reset during partial packet clears loader state");

        // Exercise the complete frozen packet at four sub-clock start phases.
        send_scene_phase(0);
        check(candidate_scene === SCENE, "phase 0 packet reconstructs scene");
        check(commit_pending, "phase 0 packet commits");
        reset_dut();
        send_scene_phase(10);
        check(candidate_scene === SCENE, "phase 10ns packet reconstructs scene");
        check(commit_pending, "phase 10ns packet commits");
        reset_dut();
        send_scene_phase(20);
        check(candidate_scene === SCENE, "phase 20ns packet reconstructs scene");
        check(commit_pending, "phase 20ns packet commits");
        reset_dut();
        send_scene_phase(30);
        check(candidate_scene === SCENE, "phase 30ns packet reconstructs scene");
        check(commit_pending, "phase 30ns packet commits");
        check(active_scene === 504'b0, "pending scene remains inactive");

        // Activation is only accepted at the loader's qualified boundary.
        frame_start = 1'b1;
        @(posedge clk);
        frame_start = 1'b0;
        tick(4);
        check(active_scene === SCENE, "activation occurs only at frame boundary");
        check(!commit_pending, "activation clears pending state");
        check(!frame_err, "frozen waveform has no framing errors");

        // Reset during the final payload window also prevents activation.
        reset_dut();
        send_byte(8'hA5);
        for (i = 0; i < 62; i = i + 1)
            send_byte(SCENE[i*8 +: 8]);
        rst_n = 1'b0;
        #1;
        check(!commit_pending && active_scene === 504'b0,
              "reset before final payload prevents activation");
        rst_n = 1'b1;
        tick(4);

        if (failures == 0)
            $display("PASS: T1d UART waveform-to-loader integration");
        else
            $display("FAIL: T1d UART integration failures=%0d", failures);
        $finish;
    end
endmodule
