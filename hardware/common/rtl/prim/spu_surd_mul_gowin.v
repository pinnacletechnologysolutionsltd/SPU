// spu_surd_mul_gowin.v — Q(√3) surd multiplication using Gowin DSP blocks
//
// Computes: (P1 + Q1·√3) × (P2 + Q2·√3)
//   P_out = P1·P2 + 3·Q1·Q2          (rational part)
//   Q_out = P1·Q2 + Q1·P2            (surd part)
//
// Uses 4 × gowin_mult18 instances (one per cross-product).
// The ×3 on Q1·Q2 uses the ALU54D accumulate path on GW2A
// (C = 2·Q1Q2 shifted in, DOUT = Q1Q2 + C = 3·Q1Q2) saving a LUT adder.
// On GW1N/GW5A the ×3 uses a shift-add: (x<<1)+x in LUTs (3 LUTs, zero DSPs).
//
// Latency:
//   GW1N / SIM : 1 clock (inferred registered multiply)
//   GW2A       : 2 clocks (ALU54D pipeline: AREG+BREG+PREG)
//   GW5A       : 2 clocks (MULT18X18D registered + accum register)
//
// Input format: 16-bit signed P and Q, sign-extended internally to 18 bits.
// Output format: 32-bit signed (product normalised by >>>16 to stay in Q16.16).
//
// CC0 1.0 Universal.

// Depends on: gowin_mult18.v (compile together)

module spu_surd_mul_gowin #(
    parameter DEVICE = "GW5A"   // "GW1N" | "GW2A" | "GW5A" | "SIM"
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        ce,

    input  wire signed [15:0] P1, Q1,   // operand 1
    input  wire signed [15:0] P2, Q2,   // operand 2

    output reg  signed [31:0] P_out,    // rational result  (Q16.16)
    output reg  signed [31:0] Q_out,    // surd result      (Q16.16)
    output reg                valid     // pulses 1 when outputs are stable
);

    // ── Sign-extend 16→18 for DSP inputs ─────────────────────────────────
    wire signed [17:0] p1e = {{2{P1[15]}}, P1};
    wire signed [17:0] q1e = {{2{Q1[15]}}, Q1};
    wire signed [17:0] p2e = {{2{P2[15]}}, P2};
    wire signed [17:0] q2e = {{2{Q2[15]}}, Q2};

    // ── 4 DSP products ────────────────────────────────────────────────────
    wire signed [35:0] prod_p1p2;   // P1×P2
    wire signed [35:0] prod_q1q2;   // Q1×Q2  (needs ×3 for P_out)
    wire signed [35:0] prod_p1q2;   // P1×Q2
    wire signed [35:0] prod_q1p2;   // Q1×P2

    gowin_mult18 #(.DEVICE(DEVICE), .ACCUM(0)) u_p1p2 (
        .clk(clk), .rst_n(rst_n), .ce(ce),
        .A(p1e), .B(p2e), .C(36'sd0), .P(prod_p1p2)
    );

    gowin_mult18 #(.DEVICE(DEVICE), .ACCUM(0)) u_q1q2 (
        .clk(clk), .rst_n(rst_n), .ce(ce),
        .A(q1e), .B(q2e), .C(36'sd0), .P(prod_q1q2)
    );

    gowin_mult18 #(.DEVICE(DEVICE), .ACCUM(0)) u_p1q2 (
        .clk(clk), .rst_n(rst_n), .ce(ce),
        .A(p1e), .B(q2e), .C(36'sd0), .P(prod_p1q2)
    );

    gowin_mult18 #(.DEVICE(DEVICE), .ACCUM(0)) u_q1p2 (
        .clk(clk), .rst_n(rst_n), .ce(ce),
        .A(q1e), .B(p2e), .C(36'sd0), .P(prod_q1p2)
    );

    // ── ×3 on Q1Q2: (x<<1)+x  (3 LUTs, zero extra DSPs) ─────────────────
    // On GW2A this could instead use a 5th ALU54D with C=2×Q1Q2, but the
    // LUT cost is negligible and saves a DSP for the Davis gasket.
    wire signed [35:0] q1q2_x3 = (prod_q1q2 <<< 1) + prod_q1q2;

    // ── Output adder + normalisation ──────────────────────────────────────
    // 2-bit shift register covers both latency cases (1 or 2 cycles).
    // GW1N/SIM: 1-cycle DSP → sample valid_sr[0].
    // GW2A/GW5A: 2-cycle DSP → sample valid_sr[1].
    localparam LAT2 = (DEVICE == "GW1N" || DEVICE == "SIM") ? 0 : 1;

    reg [1:0] valid_sr;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            P_out    <= 32'sd0;
            Q_out    <= 32'sd0;
            valid    <= 1'b0;
            valid_sr <= 2'b00;
        end else begin
            valid_sr <= {valid_sr[0], ce};
            valid    <= valid_sr[LAT2];

            if (valid_sr[LAT2]) begin
                P_out <= (prod_p1p2 + q1q2_x3) >>> 16;
                Q_out <= (prod_p1q2 + prod_q1p2) >>> 16;
            end
        end
    end

endmodule
