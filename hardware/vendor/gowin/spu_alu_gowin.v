// spu_alu_gowin.v — Gowin-native parallel SPU ALU
// Replaces spu_unified_alu_tdm.v (iCE40 SB_MAC16 TDM placeholder)
//
// Architecture: Fully parallel — all 4 axes computed simultaneously.
// Each axis requires 4 × MULT18X18 = 16 DSPs total for SPU-4.
// SPU-13 (13-axis) uses 52 DSPs — fits GW2A-18 (48+2) with 4 TDM passes
// for the last axis; fits GW5A-25 (28 DSPs) with 2 TDM passes (7 lanes/pass).
//
// Davis Gasket: ∑(A+B+C+D) == 0 check using pure LUT adder (3 LUTs).
// The ALU54D on GW2A can absorb this into the P_out accumulation for free
// — but we keep it simple and portable here.
//
// Latency (from ce pulse to valid):
//   GW1N / SIM : 2 clocks
//   GW2A / GW5A: 3 clocks  (extra pipe stage in MULT18X18D / ALU54D)
//
// DEVICE parameter flows through to gowin_mult18 and spu_surd_mul_gowin.
// Set in top-level: spu_tang_top.v or spu_nano_top.v.
//
// CC0 1.0 Universal.

// Depends on: gowin_mult18.v, spu_surd_mul_gowin.v, spu_janus_mirror.v (compile together)

module spu_alu_gowin #(
    parameter DEVICE    = "GW5A",  // "GW1N" | "GW2A" | "GW5A" | "SIM"
    parameter N_AXES    = 4,       // 4 for SPU-4; 13 requires external TDM wrapper
    parameter WIDTH     = 16       // P/Q component width (always 16 for our ISA)
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        ce,          // start computation this cycle

    // Opcode (from Lithic-L ISA v1.2)
    input  wire [4:0]  opcode,

    // Input manifold: N_AXES × 2 × 16-bit = N_AXES × 32-bit surd values
    // Packed: axis[k] = {P[15:0], Q[15:0]}
    input  wire [N_AXES*32-1:0] manifold_in,

    // Rotor coefficients for QROT / JITTER (single surd applied to all axes)
    input  wire signed [WIDTH-1:0] rotor_P, rotor_Q,

    // Output manifold
    output reg  [N_AXES*32-1:0] manifold_out,

    // Davis gasket: sum of all rational parts == 0 for Laminar state
    output wire        davis_ok,    // 1 = Laminar (∑P == 0 mod tolerance)
    output wire        davis_fault, // 1 = Cubic Leak detected

    // Janus snap: Q(√3) conjugate polarity check on axis-0 result
    // Valid 2 cycles after valid rises (registered in spu_janus_mirror)
    output wire        janus_laminar, // K = P²−3Q² > 0  — positive rational cone
    output wire        janus_null,    // K == 0           — zero / cubic leak
    output wire        janus_shadow,  // K < 0            — shadow polarity

    output reg         valid        // output stable
);

    // ── Opcode decode ─────────────────────────────────────────────────────
    localparam OP_PASS  = 5'h00;  // identity / NOP
    localparam OP_QROT  = 5'h01;  // multiply each axis by rotor (P,Q) via spu_surd_mul_gowin
    localparam OP_SADD  = 5'h02;  // scalar add: axis_P += rotor_P
    localparam OP_SNORM = 5'h03;  // normalise: >>>16 (used after QROT chain)
    localparam OP_JITTER= 5'h04;  // 60° Jitterbug permutation: (a,b,c,d)→(c,a,b,d), d anchored
    // Further opcodes (PELL etc.) dispatch to dedicated modules upstream

    // ── Unpack manifold_in into per-axis P/Q ─────────────────────────────
    wire signed [WIDTH-1:0] ax_P [0:N_AXES-1];
    wire signed [WIDTH-1:0] ax_Q [0:N_AXES-1];

    genvar k;
    generate
        for (k = 0; k < N_AXES; k = k + 1) begin : gen_unpack
            assign ax_P[k] = manifold_in[k*32 +: 16];
            assign ax_Q[k] = manifold_in[k*32+16 +: 16];
        end
    endgenerate

    // ── Per-axis surd multiplier instances ────────────────────────────────
    // Each instance uses 4 × MULT18X18 DSP slices.
    wire signed [31:0] mul_P_out [0:N_AXES-1];
    wire signed [31:0] mul_Q_out [0:N_AXES-1];
    wire               mul_valid [0:N_AXES-1];

    generate
        for (k = 0; k < N_AXES; k = k + 1) begin : gen_mul
            spu_surd_mul_gowin #(.DEVICE(DEVICE)) u_mul (
                .clk  (clk),
                .rst_n(rst_n),
                .ce   (ce & (opcode == OP_QROT)),
                .P1   (ax_P[k]),    .Q1(ax_Q[k]),
                .P2   (rotor_P),    .Q2(rotor_Q),
                .P_out(mul_P_out[k]),
                .Q_out(mul_Q_out[k]),
                .valid(mul_valid[k])
            );
        end
    endgenerate

    // ── Davis Gasket: ∑ rational parts (P) == 0 ──────────────────────────
    // Quadray constraint: A+B+C+D = 0 in canonical form.
    // We check sum of P components across all axes.
    // Tolerance: allow ±1 LSB per axis (rounding noise from >>>16).
    reg signed [WIDTH+4:0] p_sum;   // N_AXES×16-bit, needs log2(N_AXES) extra bits
    integer                j;

    always @(*) begin
        p_sum = 0;
        for (j = 0; j < N_AXES; j = j + 1)
            p_sum = p_sum + ax_P[j];
    end

    localparam signed [WIDTH+4:0] GASKET_TOL = N_AXES;  // ±1 LSB per axis
    assign davis_ok    = (p_sum <= GASKET_TOL) && (p_sum >= -GASKET_TOL);
    assign davis_fault = ~davis_ok;

    // ── Janus Mirror: Q(√3) conjugate + quadrance snap on axis-0 ─────────
    // Monitors axis-0 of the output manifold for polarity classification.
    // Feeds from manifold_out so it reflects the registered ALU result.
    wire [WIDTH*2-1:0] janus_shadow_out;
    wire signed [WIDTH*2-1:0] janus_quadrance;

    spu_janus_mirror #(.WIDTH(WIDTH)) u_janus (
        .clk         (clk),
        .rst_n       (rst_n),
        .surd_in     (manifold_out[WIDTH*2-1:0]),   // axis-0: {P,Q}
        .shadow_out  (janus_shadow_out),
        .quadrance_out(janus_quadrance),
        .snap_laminar(janus_laminar),
        .snap_null   (janus_null),
        .snap_shadow (janus_shadow)
    );

    // ── Output mux: route result based on opcode ──────────────────────────
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            manifold_out <= {N_AXES*32{1'b0}};
            valid        <= 1'b0;
        end else begin
            valid <= 1'b0;

            case (opcode)
                // QROT: output from multipliers (valid fires when mul_valid[0] rises)
                OP_QROT: begin
                    if (mul_valid[0]) begin
                        for (i = 0; i < N_AXES; i = i + 1) begin
                            manifold_out[i*32     +: 16] <= mul_P_out[i][15:0];
                            manifold_out[i*32+16  +: 16] <= mul_Q_out[i][15:0];
                        end
                        valid <= 1'b1;
                    end
                end

                // SADD: add rotor_P to every axis P component (1 cycle, LUT only)
                OP_SADD: begin
                    if (ce) begin
                        for (i = 0; i < N_AXES; i = i + 1) begin
                            manifold_out[i*32    +: 16] <= ax_P[i] + rotor_P;
                            manifold_out[i*32+16 +: 16] <= ax_Q[i];
                        end
                        valid <= 1'b1;
                    end
                end

                // JITTER: 60° IVM Jitterbug permutation (pure wire swap, 1 cycle)
                // Axis mapping (N_AXES == 4): a→b, b→c, c→a, d anchored.
                // For N_AXES != 4 axes rotate cyclically over axes 0..N_AXES-2; last anchored.
                OP_JITTER: begin
                    if (ce) begin
                        // Axis 0 ← Axis 2 (was C)
                        manifold_out[0*32 +: 32] <= manifold_in[2*32 +: 32];
                        // Axis 1 ← Axis 0 (was A)
                        manifold_out[1*32 +: 32] <= manifold_in[0*32 +: 32];
                        // Axis 2 ← Axis 1 (was B)
                        manifold_out[2*32 +: 32] <= manifold_in[1*32 +: 32];
                        // Axes 3..N_AXES-1: anchored (pass through)
                        for (i = 3; i < N_AXES; i = i + 1)
                            manifold_out[i*32 +: 32] <= manifold_in[i*32 +: 32];
                        valid <= 1'b1;
                    end
                end

                // PASS / default: output == input (identity / NOP)
                default: begin
                    if (ce) begin
                        manifold_out <= manifold_in;
                        valid        <= 1'b1;
                    end
                end
            endcase
        end
    end

endmodule
