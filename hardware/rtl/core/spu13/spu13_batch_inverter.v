`timescale 1ns / 1ps

// spu13_batch_inverter.v — Montgomery batch inversion for batched Padé evals
//
// Collapses k tower inversions to 1 tower + 3(k-1) A31 multiplies using
// Montgomery's prefix-product/unwind trick:
//
//   prefix[0] = d[0]
//   prefix[i] = prefix[i-1] * d[i]           [k-1 mults]
//   total_inv = tower_inv(prefix[k-1])        [1 tower, ~76 cycles]
//   acc = total_inv
//   for i = k-1 down to 0:
//       inv[i] = acc * prefix[i-1]            [k-1 mults]
//       acc    = acc * d[i]                   [k-1 mults]
//
// Zero-divisor check: norm(prefix[k-1]) == 0  iff some factor is singular
// (multiplicative into F_p). On hit: per-element norm probe (2 mults each,
// stages A+B only, no Fermat) isolates offending lanes; unit lanes still
// emerge bit-exact.
//
// Interface: denominators arrive sequentially (valid/last handshake);
// inverses stream out sequentially (valid per lane + per-lane singular flag).

module spu13_batch_inverter #(
    parameter MAX_BATCH = 16
) (
    input  wire         clk,
    input  wire         rst_n,

    // ── Input stream ────────────────────────────────────────────────
    input  wire         start,
    input  wire [3:0]   batch_size,       // k (1..MAX_BATCH)
    input  wire [31:0]  d0, d1, d2, d3,   // A31 denominator
    input  wire         d_valid,
    input  wire         d_last,

    // ── Output stream ───────────────────────────────────────────────
    output reg  [31:0]  inv0, inv1, inv2, inv3,
    output reg          inv_valid,
    output reg          inv_singular,      // per-lane FLAGS.V
    output reg          done,
    output reg          busy,

    // ── Debug ───────────────────────────────────────────────────────
    output wire [3:0]   debug_state
);

    localparam [31:0] P = 32'h7FFFFFFF;

    // ── State machine ───────────────────────────────────────────────
    localparam S_IDLE         = 4'd0;
    localparam S_LOAD         = 4'd1;
    localparam S_PREFIX_REQ   = 4'd2;
    localparam S_PREFIX_WAIT  = 4'd3;
    localparam S_TOWER_REQ    = 4'd4;
    localparam S_TOWER_WAIT   = 4'd5;
    localparam S_NORM_PROBE_A = 4'd7;
    localparam S_NORM_PROBE_B = 4'd8;
    localparam S_UNIT_TOWER   = 4'd9;   // per-element tower for unit lanes
    localparam S_UNWIND_SETUP = 4'd10;
    localparam S_UNWIND_MUL_A = 4'd11;
    localparam S_UNWIND_MUL_B = 4'd12;
    localparam S_OUTPUT       = 4'd13;
    localparam S_DONE         = 4'd14;

    (* keep, fsm_encoding = "none" *) reg [3:0] state;
    assign debug_state = state;

    // ── Denominator and prefix storage ──────────────────────────────
    reg [31:0] dens [0:MAX_BATCH-1][0:3];     // d[0..k-1]
    reg [31:0] prefix [0:MAX_BATCH-1][0:3];   // prefix[i] = d[0]*...*d[i]
    reg [31:0] singular_mask [0:MAX_BATCH-1]; // 1 if lane is singular
    reg [31:0] invs [0:MAX_BATCH-1][0:3];     // result array

    reg [3:0]  k;           // batch size
    reg [3:0]  idx;         // current index (0..k-1)
    reg [3:0]  load_idx;    // index during LOAD
    reg [3:0]  output_idx;  // index during OUTPUT
    reg [3:0]  probe_idx;   // index during NORM_PROBE
    reg        has_singular; // set if any lane is singular
    reg [3:0]  n_units;     // count of unit lanes for re-batch
    reg [3:0]  unit_idx [0:MAX_BATCH-1]; // indices of unit lanes
    reg [3:0]  unit_tower_idx;  // index into unit_idx[] for per-element towers

    // ── Multiplier for prefix/unwind (instance A) ───────────────────
    reg         mult_a_start;
    reg  [31:0] mult_a_a0, mult_a_a1, mult_a_a2, mult_a_a3;
    reg  [31:0] mult_a_b0, mult_a_b1, mult_a_b2, mult_a_b3;
    wire [31:0] mult_a_r0, mult_a_r1, mult_a_r2, mult_a_r3;
    wire        mult_a_done;
    wire        mult_a_busy;

    spu13_m31_multiplier u_mult_a (
        .clk  (clk),
        .rst_n(rst_n),
        .start(mult_a_start),
        .a0(mult_a_a0), .a1(mult_a_a1), .a2(mult_a_a2), .a3(mult_a_a3),
        .b0(mult_a_b0), .b1(mult_a_b1), .b2(mult_a_b2), .b3(mult_a_b3),
        .r0(mult_a_r0), .r1(mult_a_r1), .r2(mult_a_r2), .r3(mult_a_r3),
        .done(mult_a_done),
        .busy(mult_a_busy),
        .rns_error()
    );

    // ── Tower inverter ──────────────────────────────────────────────
    reg         tower_start;
    reg  [31:0] tower_z0, tower_z1, tower_z2, tower_z3;
    wire [31:0] tower_inv0, tower_inv1, tower_inv2, tower_inv3;
    wire        tower_done;
    wire        tower_busy;
    wire        tower_flags_v;

    // Tower's dedicated multiplier (instance B)
    wire        mult_b_start;
    wire [31:0] mult_b_a0, mult_b_a1, mult_b_a2, mult_b_a3;
    wire [31:0] mult_b_b0, mult_b_b1, mult_b_b2, mult_b_b3;
    wire [31:0] mult_b_r0, mult_b_r1, mult_b_r2, mult_b_r3;
    wire        mult_b_done;
    wire        mult_b_busy;

    spu13_m31_multiplier u_mult_b (
        .clk  (clk),
        .rst_n(rst_n),
        .start(mult_b_start),
        .a0(mult_b_a0), .a1(mult_b_a1), .a2(mult_b_a2), .a3(mult_b_a3),
        .b0(mult_b_b0), .b1(mult_b_b1), .b2(mult_b_b2), .b3(mult_b_b3),
        .r0(mult_b_r0), .r1(mult_b_r1), .r2(mult_b_r2), .r3(mult_b_r3),
        .done(mult_b_done),
        .busy(mult_b_busy),
        .rns_error()
    );

    spu13_fp4_inverter u_tower (
        .clk  (clk),
        .rst_n(rst_n),
        .start(tower_start),
        .z0(tower_z0), .z1(tower_z1), .z2(tower_z2), .z3(tower_z3),
        .inv0(tower_inv0), .inv1(tower_inv1),
        .inv2(tower_inv2), .inv3(tower_inv3),
        .done(tower_done),
        .busy(tower_busy),
        .flags_v(tower_flags_v),
        .mult_start(mult_b_start),
        .mult_a0(mult_b_a0), .mult_a1(mult_b_a1),
        .mult_a2(mult_b_a2), .mult_a3(mult_b_a3),
        .mult_b0(mult_b_b0), .mult_b1(mult_b_b1),
        .mult_b2(mult_b_b2), .mult_b3(mult_b_b3),
        .mult_r0(mult_b_r0), .mult_r1(mult_b_r1),
        .mult_r2(mult_b_r2), .mult_r3(mult_b_r3),
        .mult_done(mult_b_done),
        .mult_busy(mult_b_busy),
        .debug_state(),
        .debug_start_accept()
    );

    // ── Scalar norm probe for zero-divisor isolation ────────────────
    // Returns 1 if norm(z) == 0 (i.e., z is zero or a zero divisor).
    // Uses the shared mult_a for Stage A (Z * Z_conj) then Stage B
    // (W * W_conj -> scalar N) — 2 multiplies per element.
    reg [31:0] probe_z0, probe_z1, probe_z2, probe_z3;
    reg [31:0] probe_w0, probe_w1, probe_w2, probe_w3; // Stage A result
    reg        probe_zero;  // set when norm == 0

    function [31:0] m31_neg;
        input [31:0] x;
        begin
            m31_neg = (x == 32'd0) ? 32'd0 : (P - x);
        end
    endfunction

    // ── Accumulator for unwind ──────────────────────────────────────
    reg [31:0] acc0, acc1, acc2, acc3;

    // ── Sequential FSM ──────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= S_IDLE;
            done         <= 1'b0;
            busy         <= 1'b0;
            inv_valid    <= 1'b0;
            inv_singular <= 1'b0;
            mult_a_start <= 1'b0;
            tower_start  <= 1'b0;
            k            <= 4'd0;
            idx          <= 4'd0;
            load_idx     <= 4'd0;
            output_idx   <= 4'd0;
            probe_idx    <= 4'd0;
            has_singular <= 1'b0;
            probe_zero   <= 1'b0;
            n_units      <= 4'd0;
            unit_tower_idx <= 4'd0;
        end else begin
            done         <= 1'b0;
            inv_valid    <= 1'b0;
            mult_a_start <= 1'b0;
            tower_start  <= 1'b0;

            case (state)
                // ── IDLE: wait for start ────────────────────────────
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        busy      <= 1'b1;
                        k         <= batch_size;
                        load_idx  <= 4'd0;
                        has_singular <= 1'b0;
                        n_units   <= 4'd0;
                        unit_tower_idx <= 4'd0;
                        // Clear result array from previous batch
                        invs[0][0] <= 32'd0; invs[0][1] <= 32'd0;
                        invs[0][2] <= 32'd0; invs[0][3] <= 32'd0;
                        invs[1][0] <= 32'd0; invs[1][1] <= 32'd0;
                        invs[1][2] <= 32'd0; invs[1][3] <= 32'd0;
                        invs[2][0] <= 32'd0; invs[2][1] <= 32'd0;
                        invs[2][2] <= 32'd0; invs[2][3] <= 32'd0;
                        invs[3][0] <= 32'd0; invs[3][1] <= 32'd0;
                        invs[3][2] <= 32'd0; invs[3][3] <= 32'd0;
                        state     <= S_LOAD;
                    end
                end

                // ── LOAD: accept k denominators ─────────────────────
                S_LOAD: begin
                    if (d_valid) begin
                        dens[load_idx][0] <= d0;
                        dens[load_idx][1] <= d1;
                        dens[load_idx][2] <= d2;
                        dens[load_idx][3] <= d3;
                        singular_mask[load_idx] <= 1'b0;
                        if (d_last) begin
                            if (k == 4'd1) begin
                                tower_z0 <= d0; tower_z1 <= d1;
                                tower_z2 <= d2; tower_z3 <= d3;
                                tower_start <= 1'b1;
                                state <= S_TOWER_WAIT;
                            end else begin
                                // Seed prefix[0] from dens[0] (stored earlier)
                                idx      <= 4'd1;
                                prefix[0][0] <= dens[0][0];
                                prefix[0][1] <= dens[0][1];
                                prefix[0][2] <= dens[0][2];
                                prefix[0][3] <= dens[0][3];
                                // Transition to PREFIX_REQ to allow dens[1] to settle
                                state <= S_PREFIX_REQ;
                            end
                        end else begin
                            load_idx <= load_idx + 1;
                        end
                    end
                end

                // ── PREFIX_REQ: request next prefix multiply ────────
                S_PREFIX_REQ: begin
                    mult_a_a0 <= prefix[idx-1][0];
                    mult_a_a1 <= prefix[idx-1][1];
                    mult_a_a2 <= prefix[idx-1][2];
                    mult_a_a3 <= prefix[idx-1][3];
                    mult_a_b0 <= dens[idx][0];
                    mult_a_b1 <= dens[idx][1];
                    mult_a_b2 <= dens[idx][2];
                    mult_a_b3 <= dens[idx][3];
                    mult_a_start <= 1'b1;
                    state <= S_PREFIX_WAIT;
                end

                // ── PREFIX_WAIT: latch result, iterate or continue ──
                S_PREFIX_WAIT: begin
                    if (mult_a_done && !mult_a_start) begin
                        prefix[idx][0] <= mult_a_r0;
                        prefix[idx][1] <= mult_a_r1;
                        prefix[idx][2] <= mult_a_r2;
                        prefix[idx][3] <= mult_a_r3;
                        if (idx == k - 1) begin
                            // Done: start tower on prefix[k-1]
                            tower_z0 <= mult_a_r0;
                            tower_z1 <= mult_a_r1;
                            tower_z2 <= mult_a_r2;
                            tower_z3 <= mult_a_r3;
                            tower_start <= 1'b1;
                            state <= S_TOWER_WAIT;
                        end else begin
                            idx <= idx + 1;
                            state <= S_PREFIX_REQ;
                        end
                    end
                end

                // ── TOWER_REQ: start tower (unused, reserved for v2) ──
                S_TOWER_REQ: begin
                    state <= S_IDLE;
                end

                // ── TOWER_WAIT: wait for tower completion ────────────
                S_TOWER_WAIT: begin
                    if (tower_done) begin
                        if (tower_flags_v) begin
                            // At least one singular factor
                            has_singular <= 1'b1;
                            probe_idx    <= 4'd0;
                            // Start norm probe on dens[0]
                            probe_z0 <= dens[0][0];
                            probe_z1 <= dens[0][1];
                            probe_z2 <= dens[0][2];
                            probe_z3 <= dens[0][3];
                            // Stage A: Z * Z_conj (conj flips √5, √15)
                            mult_a_a0 <= dens[0][0];
                            mult_a_a1 <= dens[0][1];
                            mult_a_a2 <= dens[0][2];
                            mult_a_a3 <= dens[0][3];
                            mult_a_b0 <= dens[0][0];
                            mult_a_b1 <= dens[0][1];
                            mult_a_b2 <= m31_neg(dens[0][2]);
                            mult_a_b3 <= m31_neg(dens[0][3]);
                            mult_a_start <= 1'b1;
                            state <= S_NORM_PROBE_A;
                        end else begin
                            // All unit: latch total_inv and start unwind
                            acc0 <= tower_inv0;
                            acc1 <= tower_inv1;
                            acc2 <= tower_inv2;
                            acc3 <= tower_inv3;
                            idx  <= k - 1;  // start from last element
                            state <= S_UNWIND_SETUP;
                        end
                    end
                end

                // ── NORM_PROBE_A: latch Stage A result, start Stage B
                S_NORM_PROBE_A: begin
                    if (mult_a_done && !mult_a_start) begin
                        probe_w0 <= mult_a_r0;
                        probe_w1 <= mult_a_r1;
                        probe_w2 <= mult_a_r2;
                        probe_w3 <= mult_a_r3;
                        // Stage B: W * W_conj_3 -> scalar N
                        // W_conj w.r.t. √3: (w0, -w1, 0, 0)
                        mult_a_a0 <= mult_a_r0;
                        mult_a_a1 <= mult_a_r1;
                        mult_a_a2 <= mult_a_r2;
                        mult_a_a3 <= mult_a_r3;
                        mult_a_b0 <= mult_a_r0;
                        mult_a_b1 <= m31_neg(mult_a_r1);
                        mult_a_b2 <= 32'd0;
                        mult_a_b3 <= 32'd0;
                        mult_a_start <= 1'b1;
                        state <= S_NORM_PROBE_B;
                    end
                end

                // ── NORM_PROBE_B: check N, classify lane, iterate ───
                S_NORM_PROBE_B: begin
                    if (mult_a_done && !mult_a_start) begin
                        if (mult_a_r0 == 32'd0) begin
                            singular_mask[probe_idx] <= 1'b1;
                            has_singular <= 1'b1;
                        end else begin
                            unit_idx[n_units] <= probe_idx;
                            n_units <= n_units + 1;
                        end
                        if (probe_idx == k - 1) begin
                            // Done probing. If any unit lanes, run
                            // per-element towers on them.
                            if (n_units > 0) begin
                                unit_tower_idx <= 4'd0;
                                // Start tower on first unit lane
                                tower_z0 <= dens[unit_idx[0]][0];
                                tower_z1 <= dens[unit_idx[0]][1];
                                tower_z2 <= dens[unit_idx[0]][2];
                                tower_z3 <= dens[unit_idx[0]][3];
                                tower_start <= 1'b1;
                                state <= S_UNIT_TOWER;
                            end else begin
                                output_idx <= 4'd0;
                                state <= S_OUTPUT;
                            end
                        end else begin
                            probe_idx <= probe_idx + 1;
                            mult_a_a0 <= dens[probe_idx + 1][0];
                            mult_a_a1 <= dens[probe_idx + 1][1];
                            mult_a_a2 <= dens[probe_idx + 1][2];
                            mult_a_a3 <= dens[probe_idx + 1][3];
                            mult_a_b0 <= dens[probe_idx + 1][0];
                            mult_a_b1 <= dens[probe_idx + 1][1];
                            mult_a_b2 <= m31_neg(dens[probe_idx + 1][2]);
                            mult_a_b3 <= m31_neg(dens[probe_idx + 1][3]);
                            mult_a_start <= 1'b1;
                            state <= S_NORM_PROBE_A;
                        end
                    end
                end

                // ── UNIT_TOWER: per-element tower for unit lanes ──────
                S_UNIT_TOWER: begin
                    if (tower_done) begin
                        if (!tower_flags_v) begin
                            invs[unit_idx[unit_tower_idx]][0] <= tower_inv0;
                            invs[unit_idx[unit_tower_idx]][1] <= tower_inv1;
                            invs[unit_idx[unit_tower_idx]][2] <= tower_inv2;
                            invs[unit_idx[unit_tower_idx]][3] <= tower_inv3;
                        end
                        // else: unit was misclassified; leave invs=0,
                        // singular_mask already set by probe.
                        if (unit_tower_idx < n_units - 1) begin
                            unit_tower_idx <= unit_tower_idx + 1;
                            tower_z0 <= dens[unit_idx[unit_tower_idx + 1]][0];
                            tower_z1 <= dens[unit_idx[unit_tower_idx + 1]][1];
                            tower_z2 <= dens[unit_idx[unit_tower_idx + 1]][2];
                            tower_z3 <= dens[unit_idx[unit_tower_idx + 1]][3];
                            tower_start <= 1'b1;
                        end else begin
                            output_idx <= 4'd0;
                            state <= S_OUTPUT;
                        end
                    end
                end

                // ── UNWIND_SETUP: start first unwind multiply ────────
                S_UNWIND_SETUP: begin
                    if (idx == 4'd0) begin
                        // k == 1: acc already holds the inverse
                        invs[0][0] <= acc0;
                        invs[0][1] <= acc1;
                        invs[0][2] <= acc2;
                        invs[0][3] <= acc3;
                        output_idx <= 4'd0;
                        state <= S_OUTPUT;
                    end else begin
                        // inv[idx] = acc * prefix[idx-1]
                        mult_a_a0 <= acc0;
                        mult_a_a1 <= acc1;
                        mult_a_a2 <= acc2;
                        mult_a_a3 <= acc3;
                        mult_a_b0 <= prefix[idx-1][0];
                        mult_a_b1 <= prefix[idx-1][1];
                        mult_a_b2 <= prefix[idx-1][2];
                        mult_a_b3 <= prefix[idx-1][3];
                        mult_a_start <= 1'b1;
                        state <= S_UNWIND_MUL_A;
                    end
                end

                // ── UNWIND_MUL_A: latch inv[idx], start acc update ───
                S_UNWIND_MUL_A: begin
                    if (mult_a_done && !mult_a_start) begin
                        invs[idx][0] <= mult_a_r0;
                        invs[idx][1] <= mult_a_r1;
                        invs[idx][2] <= mult_a_r2;
                        invs[idx][3] <= mult_a_r3;
                        // acc = acc * d[idx]
                        mult_a_a0 <= acc0;
                        mult_a_a1 <= acc1;
                        mult_a_a2 <= acc2;
                        mult_a_a3 <= acc3;
                        mult_a_b0 <= dens[idx][0];
                        mult_a_b1 <= dens[idx][1];
                        mult_a_b2 <= dens[idx][2];
                        mult_a_b3 <= dens[idx][3];
                        mult_a_start <= 1'b1;
                        state <= S_UNWIND_MUL_B;
                    end
                end

                // ── UNWIND_MUL_B: latch new acc, iterate or output ───
                S_UNWIND_MUL_B: begin
                    if (mult_a_done && !mult_a_start) begin
                        acc0 <= mult_a_r0;
                        acc1 <= mult_a_r1;
                        acc2 <= mult_a_r2;
                        acc3 <= mult_a_r3;
                        if (idx == 4'd1) begin
                            // Last element: inv[0] = new acc
                            invs[0][0] <= mult_a_r0;
                            invs[0][1] <= mult_a_r1;
                            invs[0][2] <= mult_a_r2;
                            invs[0][3] <= mult_a_r3;
                            output_idx <= 4'd0;
                            state <= S_OUTPUT;
                        end else begin
                            idx <= idx - 1;
                            state <= S_UNWIND_SETUP;
                        end
                    end
                end

                // ── OUTPUT: stream results one per cycle ─────────────
                S_OUTPUT: begin
                    inv0        <= invs[output_idx][0];
                    inv1        <= invs[output_idx][1];
                    inv2        <= invs[output_idx][2];
                    inv3        <= invs[output_idx][3];
                    inv_singular <= singular_mask[output_idx];
                    inv_valid    <= 1'b1;
                    if (output_idx == k - 1) begin
                        state <= S_DONE;
                    end else begin
                        output_idx <= output_idx + 1;
                    end
                end

                // ── DONE ─────────────────────────────────────────────
                S_DONE: begin
                    done <= 1'b1;
                    busy <= 1'b0;
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
