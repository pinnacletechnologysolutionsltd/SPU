// spu4_sentinel.v (v1.3 - 2-stage pipeline for timing closure)
// Objective: Autonomous Tetrahedral Rotation Stress Test.
// Standard: Strictly Rational Q(sqrt3) SQR Rotors.
// Verification: Janus Parity must hold within 4 LSB over 1,000 heartbeats.
//
// Pipeline: Stage-0 (heartbeat): rotation multiply → pipe registers
//           Stage-1 (heartbeat+1): quadrance, drift check, output register
// Two-stage split cuts the ~38 ns combinatorial logic depth in half,
// bringing the critical path within 12 MHz on iCE40UP5K.

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

    // ── Stage-0 pipeline registers (capture rotation result) ─────────────
    // Filled on the heartbeat cycle; stage-1 reads them one cycle later.
    reg signed [15:0] p_A, p_B, p_C, p_D;
    reg               p_valid;         // stage-1 enable
    reg               p_seeding;       // marks this as the seed-capture beat
    reg               p_henosis;       // Henosis fired in this beat

    wire signed [15:0] B_s;
    assign B_s = $signed(B_out);
    wire signed [15:0] C_s;
    assign C_s = $signed(C_out);
    wire signed [15:0] D_s;
    assign D_s = $signed(D_out);

    // Henosis fold operates on stage-0 rotation result (cuts path: no quadrance needed)
    wire signed [47:0] nB_full;
    assign nB_full = ($signed(F) * B_s) + ($signed(H) * C_s) + ($signed(G) * D_s);
    wire signed [47:0] nC_full;
    assign nC_full = ($signed(G) * B_s) + ($signed(F) * C_s) + ($signed(H) * D_s);
    wire signed [47:0] nD_full;
    assign nD_full = ($signed(H) * B_s) + ($signed(G) * C_s) + ($signed(F) * D_s);

    wire signed [15:0] nA;
    assign nA = $signed(A_out);
    wire signed [15:0] nB;
    assign nB = nB_full[27:12];
    wire signed [15:0] nC;
    assign nC = nC_full[27:12];
    wire signed [15:0] nD;
    assign nD = nD_full[27:12];

    // ── Stage-1 combinatorial (from pipeline registers) ───────────────────
    wire signed [31:0] p_A2;
    assign p_A2 = $signed(p_A) * $signed(p_A);
    wire signed [31:0] p_B2;
    assign p_B2 = $signed(p_B) * $signed(p_B);
    wire signed [31:0] p_C2;
    assign p_C2 = $signed(p_C) * $signed(p_C);
    wire signed [31:0] p_D2;
    assign p_D2 = $signed(p_D) * $signed(p_D);
    wire [31:0] p_Q;
    assign p_Q = p_A2 + p_B2 + p_C2 + p_D2;

    wire signed [31:0] qd;
    assign qd = $signed(p_Q) - $signed(quadrance_seed);
    wire drift_ok;
    assign drift_ok = (qd >= -4) && (qd <= 4);

    // Henosis threshold check (stage-1: uses registered pipe values)
    wire p_henosis_needed;
    assign p_henosis_needed = seeded && (p_Q > (quadrance_seed << 1));
    wire signed [15:0] B_lam;
    assign B_lam = p_henosis_needed ? ($signed(p_B) >>> 1) : p_B;
    wire signed [15:0] C_lam;
    assign C_lam = p_henosis_needed ? ($signed(p_C) >>> 1) : p_C;
    wire signed [15:0] D_lam;
    assign D_lam = p_henosis_needed ? ($signed(p_D) >>> 1) : p_D;

    assign janus_stable  = !seeded || drift_ok;
    assign test_pass     = (heartbeat_count == 10'd1000) && janus_stable;
    assign henosis_pulse = p_valid && p_henosis_needed;

    // ── Stage-0 register: fill pipeline on heartbeat ──────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p_A       <= 16'h0; p_B <= 16'h0;
            p_C       <= 16'h0; p_D <= 16'h0;
            p_valid   <= 1'b0;
            p_seeding <= 1'b0;
            p_henosis <= 1'b0;
        end else begin
            p_valid   <= 1'b0;
            p_seeding <= 1'b0;
            if (heartbeat && heartbeat_count <= 10'd1000) begin
                if (!seeded) begin
                    p_A       <= A_seed; p_B <= B_seed;
                    p_C       <= C_seed; p_D <= D_seed;
                    p_seeding <= 1'b1;
                end else begin
                    p_A <= nA; p_B <= nB;
                    p_C <= nC; p_D <= nD;
                end
                p_valid   <= 1'b1;
                p_henosis <= 1'b0;
            end
        end
    end

    // ── Stage-1 register: commit outputs one cycle after heartbeat ────────
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
        end else if (p_valid) begin
            if (p_seeding) begin
                A_out          <= p_A; B_out <= p_B;
                C_out          <= p_C; D_out <= p_D;
                quadrance_seed <= p_Q;
                seeded         <= 1'b1;
            end else begin
                A_out           <= p_A;
                B_out           <= B_lam;
                C_out           <= C_lam;
                D_out           <= D_lam;
                quadrance       <= p_Q;
                heartbeat_count <= heartbeat_count + 1;
            end
        end
    end


endmodule
