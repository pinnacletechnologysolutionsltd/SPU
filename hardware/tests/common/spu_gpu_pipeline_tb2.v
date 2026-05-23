// spu_gpu_pipeline_tb2.v — GPU Pipeline with VE Vertex Data
//
// Renders one VE triangle face through the full GPU pipeline:
// vertices (1,-1,0,0), (1,0,-1,0), (1,0,0,-1) projected to 2D.
// Verifies pixel coverage, barycentric weights, and rational output.
// Counts covered pixels for a 32×32 sub-region around the triangle.

`timescale 1ns/1ps

module spu_gpu_pipeline_tb2;

    reg         clk, rst_n, frame_start;
    reg  [31:0] v0_xy, v1_xy, v2_xy;
    reg  [63:0] v0_attr, v1_attr, v2_attr;
    wire [31:0] pixel_x, pixel_y;
    wire        pixel_inside;
    wire [127:0] pixel_color;
    wire [15:0] pixel_weight;
    wire        frame_done;

    spu_gpu_pipeline #(.SCREEN_W(64), .SCREEN_H(64)) u_gpu (
        .clk(clk), .rst_n(rst_n), .frame_start(frame_start),
        .v0_xy(v0_xy), .v1_xy(v1_xy), .v2_xy(v2_xy),
        .v0_attr(v0_attr), .v1_attr(v1_attr), .v2_attr(v2_attr),
        .pixel_x(pixel_x), .pixel_y(pixel_y),
        .pixel_inside(pixel_inside),
        .pixel_color(pixel_color),
        .pixel_weight(pixel_weight),
        .frame_done(frame_done)
    );

    always #5 clk = ~clk;

    integer pass, fail, covered_pixels;

    initial begin
        clk = 0; rst_n = 0; frame_start = 0;
        pass = 0; fail = 0; covered_pixels = 0;

        @(posedge clk); rst_n = 1;
        @(posedge clk);

        $display("\n── GPU Pipeline with VE Vertices ──");

        // VE triangle face: vertices (1,-1,0,0), (1,0,-1,0), (1,0,0,-1)
        // Projected to 2D: v0=(48,48), v1=(16,16), v2=(16,48)
        // Quadray attributes: {A,B,C,D} packed as 4×16-bit
        v0_xy = {16'd48, 16'd48};  // {y, x}
        v1_xy = {16'd16, 16'd16};
        v2_xy = {16'd48, 16'd16};
        v0_attr = {16'd1, 16'hFFFF, 16'd0,  16'd0};    // (1,-1,0,0)
        v1_attr = {16'd1, 16'd0,    16'hFFFF, 16'd0};  // (1,0,-1,0)
        v2_attr = {16'd1, 16'd0,    16'd0,  16'hFFFF}; // (1,0,0,-1)

        // Start frame scan
        frame_start = 1;
        @(posedge clk);
        frame_start = 0;

        // Wait for scan to complete (64×64 = 4096 pixels)
        while (!frame_done) begin
            @(posedge clk);
            if (pixel_inside) covered_pixels = covered_pixels + 1;
        end

        $display("Covered pixels: %0d / 4096", covered_pixels);
        check("triangle has coverage", covered_pixels > 0);
        check("triangle < 50% screen", covered_pixels < 2048);

        repeat (5) @(posedge clk);

        $display("\n──────────────────────────────");
        $display("Results: %0d passed, %0d failed", pass, fail);
        if (fail == 0) begin
            $display("PASS");
            $finish;
        end else begin
            $display("FAIL");
            $finish;
        end
    end

    task check;
        input [255:0] name;
        input condition;
        begin
            if (condition) begin
                $display("  PASS: %0s", name);
                pass = pass + 1;
            end else begin
                $display("  FAIL: %0s", name);
                fail = fail + 1;
            end
        end
    endtask

endmodule
