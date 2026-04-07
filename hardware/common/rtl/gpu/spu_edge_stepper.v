// spu_edge_stepper.v — Incremental triangle edge function stepper
// Computes A*x + B*y + C for three triangle edges using only additions.
// Operates in the Q(√3) integer domain — all operands are integers.
// Setup: loads (A, B, C) coefficients and initialises accumulators.
// Per-pixel: steps accumulators by +A (x advance) or +B (y advance).
// CC0 1.0 Universal.

module spu_edge_stepper (
    input  wire        clk,
    input  wire        rst_n,

    // Setup — load triangle edge coefficients
    input  wire        setup,         // pulse: latch A/B/C for current triangle
    input  wire signed [15:0] coef_a, // ΔF/Δx
    input  wire signed [15:0] coef_b, // ΔF/Δy
    input  wire signed [31:0] coef_c, // F at (x0, y0)

    // Scan control
    input  wire        step_x,        // advance one pixel right
    input  wire        step_y,        // advance one scanline (resets x)
    input  wire signed [15:0] x_span, // x span at start of scanline (for row-reset)

    // Output
    output wire        inside          // 1 when edge function >= 0 (pixel is inside)
);

    reg signed [31:0] f;       // current edge function value
    reg signed [31:0] f_row;   // edge function at start of current scanline

    reg signed [15:0] a_r, b_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            f     <= 32'sd0;
            f_row <= 32'sd0;
            a_r   <= 16'sd0;
            b_r   <= 16'sd0;
        end else if (setup) begin
            a_r   <= coef_a;
            b_r   <= coef_b;
            f     <= coef_c;
            f_row <= coef_c;
        end else if (step_y) begin
            // New scanline: rewind x to left edge, advance row by B
            f_row <= f_row + {{16{b_r[15]}}, b_r};
            f     <= f_row + {{16{b_r[15]}}, b_r};
        end else if (step_x) begin
            f <= f + {{16{a_r[15]}}, a_r};
        end
    end

    assign inside = !f[31]; // MSB=0 → F >= 0

endmodule
