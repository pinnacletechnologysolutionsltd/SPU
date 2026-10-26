// One-cycle, pixel-aligned register boundary after final color selection.
// CC0 1.0 Universal.

module spu_pixel_output_register (
    input wire clk_pixel,
    input wire rst_n,
    input wire [3:0] rgb_r_in,
    input wire [3:0] rgb_g_in,
    input wire [3:0] rgb_b_in,
    input wire hsync_in,
    input wire vsync_in,
    input wire active_in,
    output reg [3:0] rgb_r_out,
    output reg [3:0] rgb_g_out,
    output reg [3:0] rgb_b_out,
    output reg hsync_out,
    output reg vsync_out,
    output reg active_out
);
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            rgb_r_out <= 4'd0;
            rgb_g_out <= 4'd0;
            rgb_b_out <= 4'd0;
            hsync_out <= 1'b0;
            vsync_out <= 1'b0;
            active_out <= 1'b0;
        end else begin
            rgb_r_out <= rgb_r_in;
            rgb_g_out <= rgb_g_in;
            rgb_b_out <= rgb_b_in;
            hsync_out <= hsync_in;
            vsync_out <= vsync_in;
            active_out <= active_in;
        end
    end
endmodule
