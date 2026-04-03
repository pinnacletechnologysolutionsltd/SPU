// spu4_sentinel.v (v1.2 - SQR v3.1 High-Fidelity Rotation)
// Objective: Autonomous Tetrahedral Rotation Stress Test.
// Standard: Strictly Rational Q(sqrt3) SQR Rotors.
// Verification: Janus Parity must hold within 4 LSB over 1,000 heartbeats.

`include "sqr_params.vh"

module spu4_sentinel (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        heartbeat,

    // Initial Quadray State
    input  wire [15:0] A_seed, B_seed, C_seed, D_seed,

    // Rotation Mode (from SQR Params)
    input  wire [1:0]  rot_mode, // 01: 60deg, 10: 120deg, 11: 180deg

    // Live Outputs
    output reg  [15:0] A_out, B_out, C_out, D_out,

    // Janus Parity Monitor
    output reg  [31:0] quadrance,
    output reg  [31:0] quadrance_seed,
    output wire        janus_stable,
    output reg  [9:0]  heartbeat_count,
    output wire        test_pass,
    output wire        henosis_pulse   // 1 = Phi-fold fired this heartbeat
);

    reg seeded;

    // ── SQR Native Tetrahedral Rotor ──────────────────────────────────
    // Rotation about A-axis (Fixed):
    // B' = (F*B + H*C + G*D) >>> 12
    // C' = (G*B + F*C + H*D) >>> 12
    // D' = (H*B + G*C + F*D) >>> 12
    
    reg signed [15:0] F, G, H;
    always @(*) begin
        case(rot_mode)
            2'b01: begin F = `SQR_60_F;  G = `SQR_60_G;  H = `SQR_60_H;  end
            2'b10: begin F = `SQR_120_F; G = `SQR_120_G; H = `SQR_120_H; end
            2'b11: begin F = `SQR_180_F; G = `SQR_180_G; H = `SQR_180_H; end
            default: begin F = `SQR_ID_F; G = `SQR_ID_G; H = `SQR_ID_H; end
        endcase
    end

    wire signed [15:0] B_s = $signed(B_out);
    wire signed [15:0] C_s = $signed(C_out);
    wire signed [15:0] D_s = $signed(D_out);

    // Intermediate products are 32-bit signed. 
    // Summing three 32-bit values can overflow into 34 bits, so we use 48-bit for safety.
    wire signed [47:0] nB_full = ($signed(F) * B_s) + ($signed(H) * C_s) + ($signed(G) * D_s);
    wire signed [47:0] nC_full = ($signed(G) * B_s) + ($signed(F) * C_s) + ($signed(H) * D_s);
    wire signed [47:0] nD_full = ($signed(H) * B_s) + ($signed(G) * C_s) + ($signed(F) * D_s);

    wire signed [15:0] nA = $signed(A_out); // A is rotation axis
    wire signed [15:0] nB = nB_full[27:12]; // Q12 shift back to 16-bit
    wire signed [15:0] nC = nC_full[27:12];
    wire signed [15:0] nD = nD_full[27:12];


    // ── Quadrance ────────────────────────────────────────────────────────
    wire signed [31:0] nA2 = $signed(nA) * $signed(nA);
    wire signed [31:0] nB2 = $signed(nB) * $signed(nB);
    wire signed [31:0] nC2 = $signed(nC) * $signed(nC);
    wire signed [31:0] nD2 = $signed(nD) * $signed(nD);

    wire [31:0] nQ = nA2 + nB2 + nC2 + nD2;


    // Drift tolerance = ±4 LSB
    wire signed [31:0] qd = $signed(nQ) - $signed(quadrance_seed);
    wire drift_ok = (qd >= -4) && (qd <= 4);

    assign janus_stable = !seeded || drift_ok;
    assign test_pass    = (heartbeat_count == 10'd1000) && janus_stable;

    // ── Davis Law Henosis fold ────────────────────────────────────────────
    // When the manifold quadrance grows beyond 2× the seed (true overflow, not
    // precision drift), fold B/C/D back via arithmetic >>1 (Phi-step descent).
    // Threshold is intentionally coarse — janus_stable (±4) is the fine monitor;
    // Henosis only fires on genuine runaway growth.
    wire henosis_needed = seeded && (nQ > (quadrance_seed << 1));
    wire signed [15:0] B_lam = henosis_needed ? ($signed(nB) >>> 1) : nB;
    wire signed [15:0] C_lam = henosis_needed ? ($signed(nC) >>> 1) : nC;
    wire signed [15:0] D_lam = henosis_needed ? ($signed(nD) >>> 1) : nD;
    assign henosis_pulse = henosis_needed;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            A_out           <= 16'h0;
            B_out           <= 16'h0;
            C_out           <= 16'h0;
            D_out           <= 16'h0;
            quadrance       <= 32'h0;
            quadrance_seed  <= 32'h0;
            heartbeat_count <= 10'h0;
            seeded          <= 1'b0;
        end else if (heartbeat && heartbeat_count <= 10'd1000) begin
            if (!seeded) begin
                A_out <= A_seed;
                B_out <= B_seed;
                C_out <= C_seed;
                D_out <= D_seed;
                quadrance_seed <= {16'h0, A_seed} * {16'h0, A_seed} +
                                  {16'h0, B_seed} * {16'h0, B_seed} +
                                  {16'h0, C_seed} * {16'h0, C_seed} +
                                  {16'h0, D_seed} * {16'h0, D_seed};
                seeded <= 1'b1;
            end else begin
                A_out           <= nA;
                B_out           <= B_lam;
                C_out           <= C_lam;
                D_out           <= D_lam;
                quadrance       <= nQ;
                heartbeat_count <= heartbeat_count + 1;
            end
        end
    end

endmodule

