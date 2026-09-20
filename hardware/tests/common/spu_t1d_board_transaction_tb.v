`timescale 1ns/1ps

module spu_t1d_board_transaction_tb;
    localparam integer BIT_NS = 8680; // 217 pixel clocks at 25 MHz
    localparam [503:0] SCENE =
        504'h0e10019002bc0f000043620ffb0fe34ffffb820fe2001cc000000000230000001900e1002bc00f00043620fe20fe34ffffb820ffb001cc0000000002300000;

    reg sys_clk = 1'b0;
    reg rst_n = 1'b0;
    reg uart_rx = 1'b1;
    wire vga_r, vga_g, vga_b, vga_hsync, vga_vsync;
    integer failures = 0;
    integer i;

    always #10 sys_clk = ~sys_clk;

    spu_a7_gpu_vga_top #(
        .PREPARED_SCENE(1),
        .COST_STIMULUS(0)
    ) dut (
        .sys_clk(sys_clk), .rst_n(rst_n), .uart_rx(uart_rx),
        .vga_r(vga_r), .vga_g(vga_g), .vga_b(vga_b),
        .vga_hsync(vga_hsync), .vga_vsync(vga_vsync)
    );

    task check(input condition, input [8*96-1:0] label);
        begin
            if (condition !== 1'b1) begin
                failures = failures + 1;
                $display("FAIL: %0s", label);
            end
        end
    endtask

    task send_byte(input [7:0] value);
        integer bit_index;
        begin
            uart_rx = 1'b0;
            #(BIT_NS);
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                uart_rx = value[bit_index];
                #(BIT_NS);
            end
            uart_rx = 1'b1;
            #(BIT_NS);
        end
    endtask

    initial begin
        repeat (4) @(posedge sys_clk);
        rst_n = 1'b1;
        repeat (65536) @(posedge sys_clk);
        repeat (8) @(posedge sys_clk);
        #1;

        send_byte(8'hA5);
        for (i = 0; i < 63; i = i + 1)
            send_byte(SCENE[i*8 +: 8]);

        #1;
        check(dut.u_gpu.u_scene_loader.candidate_scene === SCENE,
              "board top reconstructs the exact 504-bit candidate");
        check(dut.u_gpu.u_scene_loader.active_bank === 1'b0,
              "complete packet does not change active bank mid-frame");
        check(dut.u_gpu.u_scene_loader.commit_pending,
              "complete packet creates one pending activation");
        check(!dut.u_gpu.activate_scene,
              "complete packet does not activate away from frame_start");

        @(posedge dut.u_gpu.frame_start);
        #1;
        check(dut.u_gpu.u_scene_loader.active_bank === 1'b0,
              "active bank is unchanged before frame_start clock edge");
        check(dut.u_gpu.activate_scene,
              "activation is asserted at internal frame_start boundary");
        @(posedge dut.u_gpu.clk_pixel);
        #1;
        check(dut.u_gpu.u_scene_loader.active_bank === 1'b1,
              "prepared scene activates on internal frame_start");
        check(dut.u_gpu.u_scene_loader.active_scene === SCENE,
              "active bank contains the exact frozen scene");
        check(!dut.u_gpu.u_scene_loader.commit_pending,
              "frame-boundary activation clears pending state");

        if (failures == 0)
            $display("PASS: T1d board transaction and frame activation");
        else
            $display("FAIL: T1d board transaction failures=%0d", failures);
        $finish;
    end
endmodule
