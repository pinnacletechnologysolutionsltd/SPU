// Sovereign GPU Pipeline Testbench (v1.1)
// Objective: Basic verification of vertex-to-display flow.

`timescale 1ns/1ps

`include "spu_hal_interface.vh"

module gpu_pipeline_tb;

    // Parameters for the DUT
    parameter RES_X = 16; // Small resolution for quick simulation
    parameter RES_Y = 16;

    // Clock and Reset
    reg clk = 0;
    reg reset = 0;
    always #5 clk = ~clk; // 100 MHz clock

    // Signals for DUT
    wire        v_valid;
    wire [63:0] v0_abcd, v1_abcd, v2_abcd, v0_attr, v1_attr, v2_attr;
    wire        spi_cs_n, spi_sck, spi_mosi, spi_dc;
    wire        display_ready;

    // Vertex Coordinate Definitions (as 16-bit values)
    wire [15:0] v0_x = 10;
    wire [15:0] v0_y = 10;
    wire [15:0] v1_x = RES_X - 10; // 6
    wire [15:0] v1_y = 10;
    wire [15:0] v2_x = RES_X / 2;   // 8
    wire [15:0] v2_y = RES_Y - 10; // 6

    // Instantiate the Sovereign GPU Top
    spu_gpu_top #(
        .RES_X(RES_X),
        .RES_Y(RES_Y)
    ) u_gpu_top (
        .clk(clk), .reset(reset),
        
        // Vertex Interface (Sample Data for a simple triangle)
        // Quadray format: {y[31:0], x[31:0]}
        // Y_part (32 bits): {16'b0, y_val[15:0]}
        // X_part (32 bits): {16'b0, x_val[15:0]}
        // Quadray = {Y_part, X_part}
        .v0_abcd({ {16'b0, v0_y}, {16'b0, v0_x} }), 
        .v0_attr(64'hFFFF0000_00000000), // Example: Red color (RGBA)
        
        .v1_abcd({ {16'b0, v1_y}, {16'b0, v1_x} }), 
        .v1_attr(64'h00FF0000_00000000), // Example: Green color
        
        .v2_abcd({ {16'b0, v2_y}, {16'b0, v2_x} }), 
        .v2_attr(64'h0000FF00_00000000), // Example: Blue color

        // Display Interface
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck), .spi_mosi(spi_mosi), .spi_dc(spi_dc),
        .display_ready(display_ready)
    );

    // --- Monitoring ---
    initial begin
        $monitor("Time=%t | clk=%b reset=%b | pix_in=%b | l0=%h l1=%h l2=%h | frag_E=%h | spi_mosi=%b | disp_ready=%b", 
                 $time, clk, reset,
                 u_gpu_top.pixel_inside,
                 u_gpu_top.l0, u_gpu_top.l1, u_gpu_top.l2,
                 u_gpu_top.fragment_energy,
                 u_gpu_top.spi_mosi,
                 display_ready);
        
        reset = 1;
        #20; // Hold reset for 20ns
        reset = 0;
        #100; // Wait for some clock cycles after reset
        #1100; // Run simulation for 1.1us to ensure full cycle

        $display("--- Simulation Finished ---");
        $finish;
    end

endmodule
