// SPU Unified TDM-ALU (v2.0)
// Objective: A resource-folded, stability-guarded, instruction-driven ALU.
// Architecture: TDM-Folded (1-DSP) with integrated Davis Law Gaskets.
// Functionality: Q(sqrt3) Arithmetic, Pell Orbit ROT, Active Inference.
//
// Opcodes:
//   OP_NOP = 3'b000  — pass A_in to A_out unchanged
//   OP_ROT = 3'b001  — Q(sqrt3) rotation: (A+B√3) × (F_rat+F_surd√3)
//   OP_ADD = 3'b010  — Q(sqrt3) add: A_out=A+C, B_out=B+D
//   OP_INF = 3'b011  — Active Inference (predictive coding)
//
// ROT TDM schedule (6 clocks: IDLE → S1..S4 → FINISH):
//   IDLE     : latch A,B,Ra,Rb; set DSP ← A*Ra; assert rot_en
//   ROT_S1   : capture prod_aa = A*Ra; DSP ← B*Rb
//   ROT_S2   : capture prod_bb = B*Rb; DSP ← A*Rb
//   ROT_S3   : capture prod_ab = A*Rb; DSP ← B*Ra
//   ROT_S4   : capture prod_ba = B*Ra
//   ROT_FIN  : A'=prod_aa - 3*prod_bb; B'=prod_ab + prod_ba; Q12 shift; done
//
//   A' = A*Ra - 3*B*Rb  (P²-3Q²=1 norm preserved if rotor is Pell unit)
//   B' = A*Rb + B*Ra
//   Q12 shift: input data Q12×Q12 → Q24; extract bits[27:12] → Q12
//
// rot_en/rot_axis: one-cycle pulse in IDLE on OP_ROT start.
//   External vault advances step counter on this pulse.

module spu_unified_alu_tdm #(
    parameter BIT_WIDTH = 32,
    parameter DEVICE    = "SIM"  // "SIM"/"GW1N"/"GW2A" => inferred; "ICE40" => SB_MAC16
)(
    input  wire clk,
    input  wire reset,
    
    // Instruction Interface
    input  wire        start,
    input  wire [2:0]  opcode,
    input  wire [31:0] A_in, B_in, C_in, D_in,
    input  wire [31:0] F_rat, F_surd,    // Rotor {Ra,Rb} in Q12 (from vault)
    input  wire [31:0] G_rat, G_surd,
    input  wire [31:0] H_rat, H_surd,
    
    // Vault interface — pulse rot_en for one cycle when ROT starts
    input  wire [3:0]  rot_axis_in,      // which axis to rotate (0-12)
    output reg         rot_en,           // 1-cycle pulse → vault.rot_en
    output reg  [3:0]  rot_axis_out,     // passthrough → vault.axis_id
    
    // Adaptive Metabolism
    input  wire [31:0] adaptive_tau_q,
    
    // Backward compatibility ports
    input wire sync_alert,
    input wire rst_n,
    input wire [31:0] operand_A,
    input wire [31:0] operand_B,
    output wire led_status,
    output wire [17:0] result_18,
    
    // Outputs
    output reg  [31:0] A_out, B_out, C_out, D_out,
    output reg         done,
    output wire        davis_violation,
    output wire        is_dissonant
);

    // Opcode constants
    localparam OP_NOP = 3'b000;
    localparam OP_ROT = 3'b001;
    localparam OP_ADD = 3'b010;
    localparam OP_INF = 3'b011;

    // --- 1. The Single Shared Multiplier (TDM Core) ---
    reg  [15:0] mult_a, mult_b;
    wire [31:0] prod;

    generate
        if (DEVICE == "ICE40") begin : g_ice40_mul
            SB_MAC16 #(
                .NEG_TRIGGER(1'b0),
                .C_REG(1'b0)
            ) u_dsp_mul (
                .A    (mult_a),
                .B    (mult_b),
                .C    (16'h0),
                .D    (16'h0),
                .CLK  (clk),
                .CE   (1'b1),
                .IRSTTOP(reset),
                .IRSTBOT(reset),
                .O    (prod)
            );
        end else begin : g_sim_mul
            reg [31:0] prod_r;
            always @(posedge clk) begin
                if (reset) prod_r <= 32'h0;
                else prod_r <= $signed(mult_a) * $signed(mult_b);
            end
            assign prod = prod_r;
        end
    endgenerate
    
    // TDM State Machine
    reg [3:0] state;
    localparam IDLE       = 4'd0;
    localparam ROT_S1     = 4'd1;   // prod = A*Ra; DSP ← B*Rb
    localparam ROT_S2     = 4'd2;   // prod = B*Rb; DSP ← A*Rb
    localparam ROT_S3     = 4'd3;   // prod = A*Rb; DSP ← B*Ra
    localparam ROT_S4     = 4'd7;   // prod = B*Ra; all 4 products latched
    localparam ROT_FINISH = 4'd8;   // compute A', B'; assert done
    localparam DAVIS_CHK  = 4'd4;
    localparam INF_CHK    = 4'd5;
    localparam FINISH     = 4'd6;

    // --- 2. The Davis Law Gasket (Stability Guard) ---
    reg [31:0] q_accum;
    assign davis_violation = (q_accum > adaptive_tau_q);

    reg [127:0] prior_state;
    
    // --- 3.1. LFSR Dither Generator ---
    reg [15:0] lfsr;
    always @(posedge clk or posedge reset) begin
        if (reset) lfsr <= 16'hACE1;
        else lfsr <= {lfsr[14:0], lfsr[15] ^ lfsr[13] ^ lfsr[12] ^ lfsr[10]};
    end
    wire [31:0] err_dither = {31'b0, lfsr[0]};

    wire [31:0] raw_err = (A_in > prior_state[31:0]) ? (A_in - prior_state[31:0]) : (prior_state[31:0] - A_in);
    wire [31:0] err_sum  = raw_err + err_dither;
    assign is_dissonant  = (err_sum > 32'h00001000);

    // --- 3.5. Divergence Watchdog ---
    reg [4:0] watchdog_cnt;

    // --- ROT intermediate product registers ---
    reg signed [31:0] prod_aa, prod_bb, prod_ab, prod_ba;
    reg signed [31:0] rot_nA_r, rot_nB_r;  // blocking intermediates for ROT_FINISH
    reg [15:0] rot_A, rot_B, rot_Ra, rot_Rb;

    // --- 4. ALU Execution Logic ---
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state        <= IDLE;
            rot_en       <= 1'b0;
            rot_axis_out <= 4'b0;
            A_out <= 0; B_out <= 0; C_out <= 0; D_out <= 0;
            q_accum      <= 0;
            done         <= 0;
            prior_state  <= 0;
            watchdog_cnt <= 0;
            prod_aa <= 0; prod_bb <= 0; prod_ab <= 0; prod_ba <= 0;
            rot_A <= 0; rot_B <= 0; rot_Ra <= 0; rot_Rb <= 0;
            mult_a <= 0; mult_b <= 0;
        end else begin
            rot_en <= 1'b0; // default de-assert
            done   <= 1'b0;

            case (state)
                IDLE: begin
                    if (start) begin
                        case (opcode)
                            OP_ROT: begin
                                rot_A        <= A_in[15:0];
                                rot_B        <= B_in[15:0];
                                rot_Ra       <= F_rat[15:0];
                                rot_Rb       <= F_surd[15:0];
                                mult_a       <= A_in[15:0];
                                mult_b       <= F_rat[15:0]; // DSP ← A*Ra
                                rot_en       <= 1'b1;        // advance vault
                                rot_axis_out <= rot_axis_in;
                                state        <= ROT_S1;
                            end
                            OP_ADD: begin
                                A_out <= A_in + C_in;
                                B_out <= B_in + D_in;
                                done  <= 1'b1;
                                state <= IDLE;
                            end
                            OP_INF: begin
                                mult_a <= A_in[15:0];
                                mult_b <= A_in[15:0];
                                state  <= DAVIS_CHK;
                            end
                            default: begin // OP_NOP
                                A_out <= A_in;
                                done  <= 1'b1;
                            end
                        endcase
                    end
                end

                // ── ROT path: TDM Q(√3) multiply ─────────────────────────
                // DSP: prod_r is captured ONE cycle AFTER mult_a/b are set.
                // Schedule:
                //   IDLE      : mult ← A, Ra  (DSP starts A*Ra)
                //   ROT_S1    : prod=garbage   mult ← B, Rb  (start B*Rb)
                //   ROT_S2    : prod=A*Ra→aa   mult ← A, Rb  (start A*Rb)
                //   ROT_S3    : prod=B*Rb→bb   mult ← B, Ra  (start B*Ra)
                //   ROT_S4    : prod=A*Rb→ab   (no new mult; B*Ra already in flight)
                //   ROT_FINISH: prod=B*Ra→ba   compute A',B'; done

                ROT_S1: begin
                    // prod = garbage (prev cycle); set up B*Rb
                    mult_a <= rot_B;
                    mult_b <= rot_Rb;
                    state  <= ROT_S2;
                end

                ROT_S2: begin
                    prod_aa <= $signed(prod); // A*Ra ✓
                    mult_a  <= rot_A;
                    mult_b  <= rot_Rb; // DSP ← A*Rb
                    state   <= ROT_S3;
                end

                ROT_S3: begin
                    prod_bb <= $signed(prod); // B*Rb ✓
                    mult_a  <= rot_B;
                    mult_b  <= rot_Ra; // DSP ← B*Ra
                    state   <= ROT_S4;
                end

                ROT_S4: begin
                    prod_ab <= $signed(prod); // A*Rb ✓
                    // B*Ra already in flight from ROT_S3 mult setup
                    state   <= ROT_FINISH;
                end

                ROT_FINISH: begin
                    prod_ba <= $signed(prod); // B*Ra ✓
                    // A' = A*Ra + 3*B*Rb  (Q(√3): (a+b√3)(c+d√3) = ac+3bd + (ad+bc)√3)
                    // B' = A*Rb + B*Ra
                    // Q12 shift: take [27:12] of Q24 product → Q12
                    rot_nA_r = $signed(prod_aa) + ($signed(prod_bb) + ($signed(prod_bb) <<< 1));
                    rot_nB_r = $signed(prod_ab) + $signed(prod);  // prod = B*Ra (not yet latched)
                    A_out <= {16'b0, rot_nA_r[27:12]};
                    B_out <= {16'b0, rot_nB_r[27:12]};
                    done  <= 1'b1;
                    state <= IDLE;
                end

                // ── INF/Davis path ────────────────────────────────────────
                DAVIS_CHK: begin
                    q_accum <= prod;
                    state   <= INF_CHK;
                end

                INF_CHK: begin
                    if (is_dissonant || watchdog_cnt > 5'd15) begin
                        A_out        <= A_in;
                        watchdog_cnt <= 0;
                    end else begin
                        A_out        <= prior_state[31:0];
                        watchdog_cnt <= watchdog_cnt + 1'b1;
                    end
                    state <= FINISH;
                end

                FINISH: begin
                    prior_state <= {D_out, C_out, B_out, A_out};
                    done  <= 1'b1;
                    state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

    assign led_status = davis_violation ^ is_dissonant ^ A_out[0];
    assign result_18  = A_out[17:0];

endmodule
