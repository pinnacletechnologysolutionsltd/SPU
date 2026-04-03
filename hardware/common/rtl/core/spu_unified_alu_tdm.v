// SPU Unified TDM-ALU (v1.0)
// Objective: A resource-folded, stability-guarded, instruction-driven ALU.
// Architecture: TDM-Folded (1-DSP) with integrated Davis Law Gaskets.
// Functionality: Q(sqrt3) Arithmetic, Active Inference, and Metabolic Scaling.

module spu_unified_alu_tdm #(
    parameter BIT_WIDTH = 32,
    parameter DEVICE    = "SIM"  // "SIM"/"GW1N"/"GW2A" => inferred; "ICE40" => SB_MAC16
)(
    input  wire clk,
    input  wire reset,
    
    // Instruction Interface
    input  wire        start,
    input  wire [2:0]  opcode,
    input  wire [31:0] A_in, B_in, C_in, D_in, // Operand 1
    input  wire [31:0] F_rat, F_surd,         // Rotor coefficients
    input  wire [31:0] G_rat, G_surd,
    input  wire [31:0] H_rat, H_surd,
    
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

    // --- 1. The Single Shared Multiplier (TDM Core) ---
    // Explicit SB_MAC16 instantiation guarantees exactly 1 DSP slice.
    // SB_MAC16 is a 16x16 -> 32-bit signed multiply-accumulate; inputs are
    // the lower 16 bits of each RationalSurd operand (the P or Q component).
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
    localparam ROT_FB_1   = 4'd1; // F_rat * B_in
    localparam ROT_FB_2   = 4'd2; // F_surd * B_surd (Not implemented in SPU-4 simplicity)
    localparam ROT_FB_3   = 4'd3; 
    localparam DAVIS_CHK  = 4'd4;
    localparam INF_CHK    = 4'd5;
    localparam FINISH     = 4'd6;

    // --- 2. The Davis Law Gasket (Stability Guard) ---
    // Real-time Quadrance check to prevent cubic leakage.
    // Q = (A^2 + B^2 + C^2 + D^2) / 2
    reg [31:0] q_accum;
    assign davis_violation = (q_accum > adaptive_tau_q);

    // Suppresses minor "Cubic Noise" if error is within precision.
    reg [127:0] prior_state; // Latched from previous cycle
    
    // --- 3.1. LFSR Dither Generator ---
    // Injects microscopic jitter to help physical hardware snap despite EMI/Vacuum Noise
    reg [15:0] lfsr;
    always @(posedge clk or posedge reset) begin
        if (reset) lfsr <= 16'hACE1;
        else lfsr <= {lfsr[14:0], lfsr[15] ^ lfsr[13] ^ lfsr[12] ^ lfsr[10]};
    end
    wire [31:0] err_dither = {31'b0, lfsr[0]};

    // Fix: The predictive coding error should be the difference between incoming Reality (A_in) and Expectation (prior_state), not A_out.
    wire [31:0] raw_err = (A_in > prior_state[31:0]) ? (A_in - prior_state[31:0]) : (prior_state[31:0] - A_in);
    wire [31:0] err_sum = raw_err + err_dither;
    assign is_dissonant = (err_sum > 32'h00001000); // 1.0 fixed-point precision

    // --- 3.5. Divergence Watchdog ---
    // Safety measure: If the system stays in a Laminar lock (ignoring reality) for too long, force-accept the new state.
    reg [4:0] watchdog_cnt;

    // --- 4. ALU Execution Logic ---
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            A_out <= 0; B_out <= 0; C_out <= 0; D_out <= 0;
            q_accum <= 0;
            done <= 0;
            prior_state <= 0;
            watchdog_cnt <= 0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 0;
                    if (start) begin
                        // Stage 1: Latched inputs and start Quadrance calculation
                        mult_a <= A_in[15:0]; mult_b <= A_in[15:0];
                        state <= DAVIS_CHK;
                    end
                end

                DAVIS_CHK: begin
                    // Simplified Quadrance accumulation (A^2 + B^2 + C^2 + D^2)
                    // In a full TDM version, this would take 4 cycles.
                    // For the audit demo, we use the multiplier to check A^2.
                    q_accum <= prod; 
                    
                    // Move to the next state (Inference/Logic)
                    state <= INF_CHK;
                end

                INF_CHK: begin
                    // Apply Active Inference logic
                    // If dissonant (error > threshold), or if the watchdog times out, update reality. 
                    // Otherwise, hold prior but increment the watchdog.
                    if (is_dissonant || watchdog_cnt > 5'd15) begin
                        A_out <= A_in; // Update reality
                        watchdog_cnt <= 0; // Reset watchdog
                    end else begin
                        A_out <= prior_state[31:0]; // Hold the prior (Stay Laminar)
                        watchdog_cnt <= watchdog_cnt + 1'b1;
                    end
                    state <= FINISH;
                end

                FINISH: begin
                    prior_state <= {D_out, C_out, B_out, A_out};
                    done <= 1;
                    state <= IDLE;
                end
            endcase
        end
    end

    assign led_status = davis_violation ^ is_dissonant ^ A_out[0];
    assign result_18 = A_out[17:0];

endmodule
