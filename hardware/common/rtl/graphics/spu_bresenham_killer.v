// SPU-13 Bresenham-Killer: Rational Lattice Traversal (v2.0)
//
// ALGORITHM: 4-axis proportional error accumulation (L∞-normalised DDA).
//
// This is the integer hardware analog of the Metal drawEdge() closest-point
// parametric projection used in the SovereignKernel / DQFA kernels:
//
//   Metal:    t = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0)
//   Hardware: L∞ step count + per-axis Bresenham error register
//
// The key invariant: all 4 axes arrive at their target in exactly max_steps
// pulses.  No axis runs ahead and stops — the traversal is a geometrically
// straight line in Quadray space.  This eliminates the "knot" (bend) produced
// by the v1.0 axis-independent ±1 DDA.
//
// Display paths (downstream of this module):
//   60° native  → HAL_Native_Hex.v  (Quadray coords map directly to IVM pixels)
//   90° Cartesian → spu_hal_cartesian.v projects to (x,y) then rasterizer draws
//                   a soft disk per point (smoothstep analog of drawEdge SDF)
//
// Phase-locked to the 61.44 kHz Piranha Pulse; one output point per pulse.

module spu_bresenham_killer (
    input  wire        clk,
    input  wire        reset,
    input  wire        pulse_61k,
    input  wire        start,

    // Line endpoints — signed 16-bit Quadray lattice coordinates
    input  wire signed [15:0] q_a_start, q_b_start, q_c_start, q_d_start,
    input  wire signed [15:0] q_a_end,   q_b_end,   q_c_end,   q_d_end,

    // Current lattice point — valid for one clock when valid=1
    output reg  signed [15:0] out_a, out_b, out_c, out_d,
    output reg                valid,   // high for exactly one clk per step
    output reg                busy,
    output reg                done
);

    // -----------------------------------------------------------------------
    // State machine
    // -----------------------------------------------------------------------
    localparam S_IDLE = 2'd0, S_INIT = 2'd1, S_STEP = 2'd2, S_DONE = 2'd3;
    reg [1:0] state;

    // Signed deltas (latched at INIT)
    reg signed [15:0] da, db, dc, dd;

    // Absolute deltas (for error accumulation — always positive)
    reg [15:0] abs_da, abs_db, abs_dc, abs_dd;

    // L∞ step count: dominant axis magnitude determines total pulses
    reg [15:0] max_steps;

    // Bresenham error registers — each accumulates its axis's abs_delta per step.
    // Biased to max_steps/2 so the first step is centred (proper rounding, no drift).
    reg [15:0] err_a, err_b, err_c, err_d;

    // Remaining steps counter
    reg [15:0] steps_left;

    // -----------------------------------------------------------------------
    // Combinatorial: absolute delta and L∞ norm from current inputs
    // (used only during the INIT cycle to avoid multi-cycle latency)
    // -----------------------------------------------------------------------
    wire [15:0] c_abs_da = ($signed(q_a_end) >= $signed(q_a_start)) ?
                           (q_a_end - q_a_start) : (q_a_start - q_a_end);
    wire [15:0] c_abs_db = ($signed(q_b_end) >= $signed(q_b_start)) ?
                           (q_b_end - q_b_start) : (q_b_start - q_b_end);
    wire [15:0] c_abs_dc = ($signed(q_c_end) >= $signed(q_c_start)) ?
                           (q_c_end - q_c_start) : (q_c_start - q_c_end);
    wire [15:0] c_abs_dd = ($signed(q_d_end) >= $signed(q_d_start)) ?
                           (q_d_end - q_d_start) : (q_d_start - q_d_end);

    wire [15:0] max_ab   = (c_abs_da > c_abs_db) ? c_abs_da : c_abs_db;
    wire [15:0] max_cd   = (c_abs_dc > c_abs_dd) ? c_abs_dc : c_abs_dd;
    wire [15:0] c_max    = (max_ab   > max_cd)   ? max_ab   : max_cd;

    // -----------------------------------------------------------------------
    // Main state machine
    // -----------------------------------------------------------------------
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state  <= S_IDLE;
            out_a  <= 0; out_b  <= 0; out_c  <= 0; out_d  <= 0;
            da     <= 0; db     <= 0; dc     <= 0; dd     <= 0;
            abs_da <= 0; abs_db <= 0; abs_dc <= 0; abs_dd <= 0;
            max_steps  <= 0; steps_left <= 0;
            err_a <= 0; err_b <= 0; err_c <= 0; err_d <= 0;
            valid  <= 0; busy   <= 0; done   <= 0;

        end else begin
            valid <= 0; // default — only raised for one clock per step

            case (state)

            S_IDLE: begin
                done <= 0;
                if (start) begin
                    // Latch start position and deltas
                    out_a <= q_a_start; out_b <= q_b_start;
                    out_c <= q_c_start; out_d <= q_d_start;
                    da    <= $signed(q_a_end) - $signed(q_a_start);
                    db    <= $signed(q_b_end) - $signed(q_b_start);
                    dc    <= $signed(q_c_end) - $signed(q_c_start);
                    dd    <= $signed(q_d_end) - $signed(q_d_start);
                    abs_da <= c_abs_da; abs_db <= c_abs_db;
                    abs_dc <= c_abs_dc; abs_dd <= c_abs_dd;
                    max_steps  <= c_max;
                    steps_left <= c_max;
                    // Bias = max_steps/2 — centres rounding, no systematic drift
                    err_a <= c_max >> 1; err_b <= c_max >> 1;
                    err_c <= c_max >> 1; err_d <= c_max >> 1;
                    busy  <= 1;
                    state <= S_INIT;
                end
            end

            // INIT: emit the start point, then begin stepping on first pulse
            S_INIT: begin
                if (pulse_61k) begin
                    valid <= 1;  // emit start point
                    if (max_steps == 0) begin
                        // Degenerate: start == end — nothing to traverse
                        busy  <= 0; done  <= 1;
                        state <= S_DONE;
                    end else begin
                        state <= S_STEP;
                    end
                end
            end

            S_STEP: begin
                if (pulse_61k) begin
                    // --- Bresenham error accumulation per axis ---
                    // Each axis advances only when its accumulated sub-step
                    // crosses the max_steps threshold.  This is the integer
                    // exact analog of:  t = dot(pa,ba) / dot(ba,ba)

                    // Axis A
                    if (err_a + abs_da >= max_steps) begin
                        out_a <= out_a + (da > 0 ? 1 : -1);
                        err_a <= err_a + abs_da - max_steps;
                    end else begin
                        err_a <= err_a + abs_da;
                    end

                    // Axis B
                    if (err_b + abs_db >= max_steps) begin
                        out_b <= out_b + (db > 0 ? 1 : -1);
                        err_b <= err_b + abs_db - max_steps;
                    end else begin
                        err_b <= err_b + abs_db;
                    end

                    // Axis C
                    if (err_c + abs_dc >= max_steps) begin
                        out_c <= out_c + (dc > 0 ? 1 : -1);
                        err_c <= err_c + abs_dc - max_steps;
                    end else begin
                        err_c <= err_c + abs_dc;
                    end

                    // Axis D
                    if (err_d + abs_dd >= max_steps) begin
                        out_d <= out_d + (dd > 0 ? 1 : -1);
                        err_d <= err_d + abs_dd - max_steps;
                    end else begin
                        err_d <= err_d + abs_dd;
                    end

                    valid <= 1;
                    steps_left <= steps_left - 1;

                    if (steps_left == 1) begin
                        busy  <= 0; done  <= 1;
                        state <= S_DONE;
                    end
                end
            end

            S_DONE: begin
                done  <= 0;
                state <= S_IDLE;
            end

            endcase
        end
    end

endmodule
