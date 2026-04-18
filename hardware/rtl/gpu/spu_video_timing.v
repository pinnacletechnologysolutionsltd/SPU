// spu_video_timing.v — Video sync/pixel counter for 640×480@60Hz
// Outputs (x, y) counters, hsync, vsync, active each pixel clock.
// All arithmetic is integer. No floating point.
// CC0 1.0 Universal.

module spu_video_timing #(
    parameter H_ACTIVE = 640,
    parameter H_FP     = 16,
    parameter H_SYNC   = 96,
    parameter H_BP     = 48,
    // H_TOTAL = 800
    parameter V_ACTIVE = 480,
    parameter V_FP     = 10,
    parameter V_SYNC   = 2,
    parameter V_BP     = 33
    // V_TOTAL = 525
)(
    input  wire        clk,
    input  wire        rst_n,
    output reg  [9:0]  x,
    output reg  [9:0]  y,
    output wire        hsync,
    output wire        vsync,
    output wire        active
);

    localparam H_TOTAL = H_ACTIVE + H_FP + H_SYNC + H_BP; // 800
    localparam V_TOTAL = V_ACTIVE + V_FP + V_SYNC + V_BP; // 525

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x <= 10'd0;
            y <= 10'd0;
        end else if (x == H_TOTAL - 1) begin
            x <= 10'd0;
            y <= (y == V_TOTAL - 1) ? 10'd0 : y + 10'd1;
        end else
            x <= x + 10'd1;
    end

    assign hsync  = ~((x >= H_ACTIVE + H_FP) && (x < H_ACTIVE + H_FP + H_SYNC));
    assign vsync  = ~((y >= V_ACTIVE + V_FP) && (y < V_ACTIVE + V_FP + V_SYNC));
    assign active = (x < H_ACTIVE) && (y < V_ACTIVE);

endmodule
