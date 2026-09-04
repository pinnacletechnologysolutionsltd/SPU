// spu_video_pattern.v — 640x480 test pattern: eight colour bars plus a
// vertically-scrolling marker line.
//
// The scrolling line matters for bring-up: colour bars alone cannot
// distinguish a live link from a frozen one, because a stuck framebuffer and
// a working one look identical. A line that moves every frame proves the
// pixel clock, the frame counter, and the sync generator are all running.
//
// Bar boundaries are integer comparisons at multiples of 80 (640 = 8 x 80).
// No division. CC0 1.0 Universal.

module spu_video_pattern (
    input  wire        clk_pixel,
    input  wire        rst_n,
    input  wire [9:0]  x,
    input  wire [9:0]  y,
    input  wire        vsync,      // active low
    output reg  [7:0]  r,
    output reg  [7:0]  g,
    output reg  [7:0]  b
);

    // ── Frame counter, advanced on each vsync falling edge ───────────────
    reg        vsync_d;
    reg [8:0]  frame;
    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            vsync_d <= 1'b1;
            frame   <= 9'd0;
        end else begin
            vsync_d <= vsync;
            if (vsync_d && !vsync) frame <= frame + 9'd1;
        end
    end

    // Marker sweeps 0..479 as the frame counter advances.
    wire [9:0] marker_y = {1'b0, frame};
    wire       on_marker = (y >= marker_y) && (y < marker_y + 10'd4);

    // ── Eight colour bars, 80 px each ────────────────────────────────────
    reg [2:0] bar;
    always @* begin
        if      (x < 10'd80)  bar = 3'd0;
        else if (x < 10'd160) bar = 3'd1;
        else if (x < 10'd240) bar = 3'd2;
        else if (x < 10'd320) bar = 3'd3;
        else if (x < 10'd400) bar = 3'd4;
        else if (x < 10'd480) bar = 3'd5;
        else if (x < 10'd560) bar = 3'd6;
        else                  bar = 3'd7;
    end

    always @(posedge clk_pixel or negedge rst_n) begin
        if (!rst_n) begin
            r <= 8'd0; g <= 8'd0; b <= 8'd0;
        end else if (on_marker) begin
            r <= 8'hFF; g <= 8'h00; b <= 8'h00;   // red sweep line
        end else begin
            // white, yellow, cyan, green, magenta, red, blue, black
            r <= (bar == 3'd0 || bar == 3'd1 || bar == 3'd4 || bar == 3'd5)
                 ? 8'hFF : 8'h00;
            g <= (bar == 3'd0 || bar == 3'd1 || bar == 3'd2 || bar == 3'd3)
                 ? 8'hFF : 8'h00;
            b <= (bar == 3'd0 || bar == 3'd2 || bar == 3'd4 || bar == 3'd6)
                 ? 8'hFF : 8'h00;
        end
    end

endmodule
