// spu_gpu_pipeline.v — Quadray GPU Pipeline (v1.0)
// Chains: rasterizer → fragment pipe → display output.
// Takes 3 projected VE vertices + Quadray attributes, iterates
// over a pixel grid, and outputs spread-weighted rational colors.
//
// Integration: instantiate alongside spu13_core, feed vertices
// from QR regfile (qrf_dbg_A/B/C/D or dedicated output port).
// Clocked at pixel rate for scan-out.
//
// CC0 1.0 Universal.

module spu_gpu_pipeline #(
    parameter SCREEN_W = 240,
    parameter SCREEN_H = 240
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         frame_start,     // start of frame pulse

    // Vertex inputs (3 projected vertices per triangle)
    // Format: {y[15:0], x[15:0]} for rasterizer compatibility
    input  wire [31:0]  v0_xy, v1_xy, v2_xy,
    // Quadray attributes per vertex: {A[15:0], B[15:0], C[15:0], D[15:0]}
    input  wire [63:0]  v0_attr, v1_attr, v2_attr,

    // Pixel scan-out
    output reg  [31:0]  pixel_x,
    output reg  [31:0]  pixel_y,
    output wire         pixel_inside,
    output wire [127:0] pixel_color,     // 4×32-bit rational RGBA
    output wire [15:0]  pixel_weight,    // denominator
    output wire         frame_done
);

    // ── Rasterizer ───────────────────────────────────────────────────
    wire [31:0] lambda0, lambda1, lambda2;
    wire [15:0] pixel_z;

    spu_rasterizer u_rast (
        .clk(clk), .reset(!rst_n),
        .v0_abcd({16'd0, v0_xy[31:16], 16'd0, v0_xy[15:0]}),
        .v1_abcd({16'd0, v1_xy[31:16], 16'd0, v1_xy[15:0]}),
        .v2_abcd({16'd0, v2_xy[31:16], 16'd0, v2_xy[15:0]}),
        .v0_z(16'd0), .v1_z(16'd0), .v2_z(16'd0),
        .pixel_x(pixel_x), .pixel_y(pixel_y),
        .pixel_inside(pixel_inside),
        .lambda0(lambda0), .lambda1(lambda1), .lambda2(lambda2),
        .pixel_z(pixel_z)
    );

    // ── Fragment Pipe ────────────────────────────────────────────────
    spu_fragment_pipe u_frag (
        .clk(clk), .rst_n(rst_n),
        .pixel_inside(pixel_inside),
        .w0_n(lambda0[31:16]), .w1_n(lambda1[31:16]), .w2_n(lambda2[31:16]),
        .v0_attr(v0_attr), .v1_attr(v1_attr), .v2_attr(v2_attr),
        .pixel_energy_n(pixel_color),
        .pixel_w_total(pixel_weight)
    );

    // ── Pixel Counter / Scan-Out ────────────────────────────────────
    reg scanning;
    reg frame_done_r;

    assign frame_done = frame_done_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pixel_x <= 0;
            pixel_y <= 0;
            scanning <= 0;
            frame_done_r <= 0;
        end else begin
            frame_done_r <= 0;
            if (frame_start) begin
                pixel_x <= 0;
                pixel_y <= 0;
                scanning <= 1;
            end else if (scanning) begin
                if (pixel_x < SCREEN_W - 1) begin
                    pixel_x <= pixel_x + 1;
                end else begin
                    pixel_x <= 0;
                    if (pixel_y < SCREEN_H - 1) begin
                        pixel_y <= pixel_y + 1;
                    end else begin
                        pixel_y <= 0;
                        scanning <= 0;
                        frame_done_r <= 1;  // pulse for one cycle
                    end
                end
            end
        end
    end

endmodule
