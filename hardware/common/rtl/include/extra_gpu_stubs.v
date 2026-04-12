// extra_gpu_stubs.v — minimal GPU stubs for triage
// NOTE: Temporary triage-only stubs; replace with real GPU RTL later.

module spu_raster_unit (
    input wire clk,
    input wire rst_n,
    input wire setup,
    input wire signed [15:0] a0, b0,
    input wire signed [31:0] c0,
    input wire signed [15:0] a1, b1,
    input wire signed [31:0] c1,
    input wire signed [15:0] a2, b2,
    input wire signed [31:0] c2,
    input wire step_x,
    input wire step_y,
    input wire signed [15:0] x_span,
    input wire [3:0] tri_r, tri_g, tri_b,
    output reg covered,
    output reg [3:0] pixel_r, pixel_g, pixel_b
);
    reg signed [31:0] x;
    reg signed [31:0] y;
    initial begin
        x = 0; y = 0; covered = 1'b0; pixel_r = 4'd0; pixel_g = 4'd0; pixel_b = 4'd0;
    end
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x <= 0; y <= 0;
        end else begin
            if (setup) begin x <= 0; y <= 0; end
            else begin
                if (step_x) x <= x + 1;
                if (step_y) y <= y + 1;
            end
        end
    end
    wire signed [63:0] e0 = $signed(a0) * $signed(x) + $signed(b0) * $signed(y) + $signed(c0);
    wire signed [63:0] e1 = $signed(a1) * $signed(x) + $signed(b1) * $signed(y) + $signed(c1);
    wire signed [63:0] e2 = $signed(a2) * $signed(x) + $signed(b2) * $signed(y) + $signed(c2);
    always @(*) begin
        covered = (e0 >= 0) && (e1 >= 0) && (e2 >= 0);
        if (covered) begin
            pixel_r = tri_r; pixel_g = tri_g; pixel_b = tri_b;
        end else begin
            pixel_r = 4'd0; pixel_g = 4'd0; pixel_b = 4'd0;
        end
    end
endmodule

module spu_bresenham_raster (
    input wire clk,
    input wire rst_n,
    input wire setup,
    input wire step,
    input wire [9:0] x0, y0, x1, y1,
    input wire [3:0] line_r, line_g, line_b,
    output reg [9:0] px, py,
    output reg pixel_valid,
    output reg [3:0] out_r, out_g, out_b,
    output reg done,
    output reg [19:0] quadrance
);
    wire signed [31:0] dx = $signed({1'b0,x1}) - $signed({1'b0,x0});
    wire signed [31:0] dy = $signed({1'b0,y1}) - $signed({1'b0,y0});
    wire [31:0] sqx = dx * dx;
    wire [31:0] sqy = dy * dy;
    always @(*) begin
        quadrance = sqx + sqy;
    end
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            done <= 1'b0; pixel_valid <= 1'b0; px <= 10'd0; py <= 10'd0; out_r <= 4'd0; out_g <= 4'd0; out_b <= 4'd0;
        end else begin
            if (setup) begin
                done <= 1'b1;
                pixel_valid <= 1'b0;
            end
            if (step) begin
                // simple handshake: emit first endpoint as a pixel then mark valid=1 then low
                px <= x0; py <= y0; pixel_valid <= 1'b1; out_r <= line_r; out_g <= line_g; out_b <= line_b;
            end else begin
                pixel_valid <= 1'b0;
            end
        end
    end
endmodule
