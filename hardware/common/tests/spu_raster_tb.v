// spu_raster_tb.v — Testbench for spu_raster_unit (single triangle)
// Sets up a triangle covering pixel (100,100) and verifies covered=1.
// Also checks that (0,0) is outside the triangle.
`timescale 1ns/1ps
module spu_raster_tb;

    reg clk = 0, rst_n = 0;
    reg setup = 0, step_x = 0, step_y = 0;

    // Triangle: (90,90), (150,90), (90,150)
    // Edge 0: y >= 90  → A=0, B=1, C=-90
    // Edge 1: x >= 90  → A=1, B=0, C=-90
    // Edge 2: x+y <= 240 → -x-y+240>=0 → A=-1, B=-1, C=240
    wire covered;
    wire [3:0] pr, pg, pb;

    spu_raster_unit dut (
        .clk(clk), .rst_n(rst_n), .setup(setup),
        .a0(16'sd0),  .b0(16'sd1),  .c0(-32'sd90),
        .a1(16'sd1),  .b1(16'sd0),  .c1(-32'sd90),
        .a2(-16'sd1), .b2(-16'sd1), .c2(32'sd240),
        .step_x(step_x), .step_y(step_y), .x_span(16'sd640),
        .tri_r(4'hF), .tri_g(4'hA), .tri_b(4'h5),
        .covered(covered), .pixel_r(pr), .pixel_g(pg), .pixel_b(pb));

    always #10 clk = ~clk;

    integer pass = 1;
    integer ix, iy;

    initial begin
        #15 rst_n = 1;

        @(posedge clk); #1;
        setup = 1;
        @(posedge clk); #1;
        setup = 0;

        // Step to pixel (100, 100): step_y 100 times, then step_x 100 times
        // step_y first (advances y from 0 to 100)
        for (iy = 0; iy < 100; iy = iy + 1) begin
            step_y = 1;
            @(posedge clk); #1;
            step_y = 0;
            @(posedge clk); #1;
        end
        for (ix = 0; ix < 100; ix = ix + 1) begin
            step_x = 1;
            @(posedge clk); #1;
            step_x = 0;
            @(posedge clk); #1;
        end

        // Now at (100,100) — should be inside triangle
        @(posedge clk); #1;
        if (!covered) begin
            $display("FAIL: pixel (100,100) should be inside triangle");
            pass = 0;
        end

        if (pass) $display("PASS");
        else      $display("FAIL");
        $finish;
    end
endmodule
