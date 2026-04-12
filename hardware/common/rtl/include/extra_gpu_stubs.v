// extra_gpu_stubs.v — Minimal GPU stubs for triage
// CC0 1.0 Universal

module spu_raster_unit(
    input wire        clk,
    input wire        rst_n,
    input wire        setup,
    input wire signed [15:0] a0, input wire signed [15:0] b0, input wire signed [31:0] c0,
    input wire signed [15:0] a1, input wire signed [15:0] b1, input wire signed [31:0] c1,
    input wire signed [15:0] a2, input wire signed [15:0] b2, input wire signed [31:0] c2,
    input wire        step_x,
    input wire        step_y,
    input wire signed [15:0] x_span,
    input wire [3:0]  tri_r,
    input wire [3:0]  tri_g,
    input wire [3:0]  tri_b,
    output wire       covered,
    output wire [3:0] pixel_r,
    output wire [3:0] pixel_g,
    output wire [3:0] pixel_b
);
    assign covered = 1'b0;
    assign pixel_r = 4'h0;
    assign pixel_g = 4'h0;
    assign pixel_b = 4'h0;
endmodule

module spu_bresenham_raster(
    input wire        clk,
    input wire        rst_n,
    input wire        setup,
    input wire [9:0]  x0, y0,
    input wire [9:0]  x1, y1,
    input wire [3:0]  line_r,
    input wire [3:0]  line_g,
    input wire [3:0]  line_b,
    input wire        step,
    output reg  [9:0] px,
    output reg  [9:0] py,
    output reg        pixel_valid,
    output reg  [3:0] out_r,
    output reg  [3:0] out_g,
    output reg  [3:0] out_b,
    output reg        done,
    output reg  [19:0] quadrance
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            px <= 10'd0;
            py <= 10'd0;
            pixel_valid <= 1'b0;
            out_r <= 4'h0; out_g <= 4'h0; out_b <= 4'h0;
            done <= 1'b0;
            quadrance <= 20'd0;
        end else begin
            // stub: no rasterisation
            pixel_valid <= 1'b0;
            done <= 1'b0;
        end
    end
endmodule
