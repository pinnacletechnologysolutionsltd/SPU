// spu_bresenham_tb.v — Testbench for spu_bresenham_raster
// Draws a simple line and checks quadrance + pixel positions.
`timescale 1ns/1ps
module spu_bresenham_tb;

    reg clk = 0, rst_n = 0;
    reg setup = 0, step = 0;
    reg [9:0] x0 = 0, y0 = 0, x1 = 3, y1 = 4;

    wire [9:0] px, py;
    wire       pixel_valid, done;
    wire [3:0] out_r, out_g, out_b;
    wire [19:0] quadrance;

    spu_bresenham_raster dut (
        .clk(clk), .rst_n(rst_n),
        .setup(setup), .step(step),
        .x0(x0), .y0(y0), .x1(x1), .y1(y1),
        .line_r(4'hF), .line_g(4'h8), .line_b(4'h0),
        .px(px), .py(py), .pixel_valid(pixel_valid),
        .out_r(out_r), .out_g(out_g), .out_b(out_b),
        .done(done), .quadrance(quadrance));

    always #10 clk = ~clk;

    integer pass = 1;
    integer steps_taken = 0;

    initial begin
        #15 rst_n = 1;

        // Setup: line (0,0) → (3,4), Q = 9+16 = 25
        @(posedge clk); #1;
        setup = 1;
        @(posedge clk); #1;
        setup = 0;

        // Check quadrance
        @(posedge clk); #1;
        if (quadrance !== 20'd25) begin
            $display("FAIL: quadrance=%0d expected 25", quadrance);
            pass = 0;
        end

        // Step until done or max steps
        while (!done && steps_taken < 20) begin
            step = 1;
            @(posedge clk); #1;
            step = 0;
            @(posedge clk); #1;
            steps_taken = steps_taken + 1;
        end

        if (!done) begin
            $display("FAIL: line did not complete in %0d steps", steps_taken);
            pass = 0;
        end

        if (pass) $display("PASS");
        else      $display("FAIL");
        $finish;
    end
endmodule
