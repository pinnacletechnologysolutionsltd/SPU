`timescale 1ns/1ps

module spu_t1d_board_reset_tb;
    reg sys_clk = 1'b0;
    reg rst_n = 1'b0;
    reg uart_rx = 1'b1;
    wire vga_r, vga_g, vga_b, vga_hsync, vga_vsync;
    integer failures = 0;

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

    initial begin
        repeat (4) @(posedge sys_clk);
        check(!dut.rst_n_db && !dut.pix_rst_n, "asserted reset is held");

        rst_n = 1'b1;
        repeat (65536) @(posedge sys_clk);
        repeat (8) @(posedge sys_clk);
        #1;

        check(dut.rst_n_db && dut.pix_rst_n,
              "physical reset deasserts after debounce and pixel sync");
        check(dut.u_gpu.u_scene_loader.active_scene === 504'b0,
              "prepared top active scene is clear after reset");
        check(dut.u_gpu.u_scene_loader.candidate_scene === 504'b0,
              "prepared top candidate scene is clear after reset");
        check(dut.u_gpu.u_scene_loader.active_bank === 1'b0,
              "prepared top selects bank zero after reset");
        check(!dut.u_gpu.u_scene_loader.receiving &&
              !dut.u_gpu.u_scene_loader.commit_pending,
              "prepared top loader is idle after reset");
        check(!dut.u_gpu.armed0 && !dut.u_gpu.armed1,
              "prepared renderer remains unarmed after reset");
        check(!dut.u_gpu.scene_commit_pending && !dut.u_gpu.activate_scene,
              "prepared top has no pending activation after reset");
        check(vga_r === 1'b0 && vga_g === 1'b0 && vga_b === 1'b0,
              "prepared top default display is black");
        check(vga_hsync !== 1'bx && vga_vsync !== 1'bx,
              "prepared top emits defined VGA sync levels");
        check(dut.scene_rx_valid === 1'b0,
              "T1d idle UART path has no scene byte valid");

        rst_n = 1'b0;
        repeat (65536) @(posedge sys_clk);
        repeat (8) @(posedge sys_clk);
        #1;
        check(!dut.rst_n_db && !dut.pix_rst_n,
              "physical reset reasserts after the symmetric debounce window");
        check(dut.u_gpu.u_scene_loader.active_scene === 504'b0 &&
              dut.u_gpu.u_scene_loader.candidate_scene === 504'b0 &&
              dut.u_gpu.u_scene_loader.active_bank === 1'b0 &&
              !dut.u_gpu.u_scene_loader.receiving &&
              !dut.u_gpu.u_scene_loader.commit_pending,
              "physical reassertion restores the loader reset state");

        if (failures == 0)
            $display("PASS: T1d board reset/default-state integration");
        else
            $display("FAIL: T1d board reset failures=%0d", failures);
        $finish;
    end
endmodule
