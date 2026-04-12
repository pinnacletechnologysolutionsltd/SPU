// spu_bresenham_killer.v — Rational line / Quadrance-conic rasterizer
// Draws a line from (x0,y0)→(x1,y1) using integer-only Bresenham.
// Also outputs the Quadrance Q = Δx² + Δy² (never irrational).
// Iterates one step per clock; asserts pixel_valid when on the line.
// No floating point. CC0 1.0 Universal.

module spu_bresenham_raster (
    input  wire        clk,
    input  wire        rst_n,

    // Setup
    input  wire        setup,      // pulse: load new line endpoints
    input  wire [9:0]  x0, y0,
    input  wire [9:0]  x1, y1,
    input  wire [3:0]  line_r,
    input  wire [3:0]  line_g,
    input  wire [3:0]  line_b,

    // Advance one step along the line
    input  wire        step,

    // Current pixel
    output reg  [9:0]  px,
    output reg  [9:0]  py,
    output reg         pixel_valid,
    output reg  [3:0]  out_r,
    output reg  [3:0]  out_g,
    output reg  [3:0]  out_b,
    output reg         done,        // asserted when (px,py)==(x1,y1)

    // Quadrance of this line segment (Δx² + Δy²)
    output reg  [19:0] quadrance
);

    reg [9:0] dx_abs, dy_abs;
    reg       sx, sy;          // step directions (0=+1, 1=-1)
    reg       steep;           // |dy|>|dx|: drive on y axis
    reg signed [10:0] err;

    reg  [9:0] x1_lat, y1_lat;

    // Combinational helpers for quadrance and initial error (Verilog-2001 compatible)
    wire [9:0] ddx;
    assign ddx = (x1 >= x0) ? (x1 - x0) : (x0 - x1);
    wire [9:0] ddy;
    assign ddy = (y1 >= y0) ? (y1 - y0) : (y0 - y1);
    wire [9:0] dx_in;
    assign dx_in = ddx, dy_in = ddy;
    wire       steep_in;
    assign steep_in = (dy_in > dx_in);

    // Combinational next-step values (for done detection without latency)
    wire [9:0] next_py_s = sy ? py - 10'd1 : py + 10'd1;  // steep path
    wire [9:0] next_px_f = sx ? px - 10'd1 : px + 10'd1;  // flat path
    wire signed [10:0] err1_s = err - $signed({1'b0, dx_abs}); // steep err after major step
    wire signed [10:0] err1_f = err - $signed({1'b0, dy_abs}); // flat  err after major step
    wire       do_minor_s = (err1_s < 11'sd0);  // need X step in steep mode
    wire       do_minor_f = (err1_f < 11'sd0);  // need Y step in flat mode
    wire [9:0] next_px_s;
    assign next_px_s = do_minor_s ? (sx ? px-10'd1 : px+10'd1) : px;
    wire [9:0] next_py_f;
    assign next_py_f = do_minor_f ? (sy ? py-10'd1 : py+10'd1) : py;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pixel_valid <= 1'b0;
            done        <= 1'b0;
            px          <= 10'd0;
            py          <= 10'd0;
            quadrance   <= 20'd0;
        end else if (setup) begin
            dx_abs <= dx_in;
            dy_abs <= dy_in;
            sx     <= (x1 >= x0) ? 1'b0 : 1'b1;
            sy     <= (y1 >= y0) ? 1'b0 : 1'b1;
            steep  <= steep_in;
            px          <= x0;
            py          <= y0;
            x1_lat      <= x1;
            y1_lat      <= y1;
            done        <= (x0 == x1) && (y0 == y1);
            pixel_valid <= 1'b1;
            out_r       <= line_r;
            out_g       <= line_g;
            out_b       <= line_b;
            quadrance   <= (dx_in * dx_in) + (dy_in * dy_in);
            // Initialise Bresenham error: start at major/2 for centering
            err <= steep_in ?
                $signed({1'b0, dy_in}) >>> 1 :
                $signed({1'b0, dx_in}) >>> 1;
        end else if (step && pixel_valid && !done) begin
            if (steep) begin
                py  <= next_py_s;
                px  <= next_px_s;
                err <= do_minor_s ? err1_s + $signed({1'b0, dy_abs}) : err1_s;
                done <= (next_px_s == x1_lat) && (next_py_s == y1_lat);
            end else begin
                px  <= next_px_f;
                py  <= next_py_f;
                err <= do_minor_f ? err1_f + $signed({1'b0, dx_abs}) : err1_f;
                done <= (next_px_f == x1_lat) && (next_py_f == y1_lat);
            end
        end else if (done) begin
            pixel_valid <= 1'b0;
        end
    end

endmodule
