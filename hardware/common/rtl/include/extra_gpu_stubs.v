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

