// spu_4_euclidean_alu.v (v1.1 - Phi-Fold Laminar)
// A 1-DSP TDM-folded Autonomous Euclidean 4D Processor for SPU-4 clusters.
// Handles the local 4-axis Circulant Matrix:
// B' = F*B + H*C + G*D
// C' = G*B + F*C + H*D
// D' = H*B + G*C + F*D
//
// Overflow handling: 18-bit internal accumulator with Phi-step fold.
// When the three-product sum overflows 16-bit Q8.8 range, the result is
// folded by arithmetic right-shift (÷2 or ÷4) rather than silently wrapping.
// Cost: zero extra DSPs, ~6 LUTs per axis fold.  henosis_pulse is asserted
// whenever any axis fold fires.

module spu_4_euclidean_alu (
    input  wire        clk,
    input  wire        reset,
    input  wire        start,
    input  wire [7:0]  bloom_intensity,
    input  wire        mode_autonomous, // 0 = slave, 1 = autonomous dream
    
    // Quadray Inputs (16-bit: Q8.8)
    input  wire [15:0] A_in, B_in, C_in, D_in,
    
    // Rotor Coefficients (F, G, H)
    input  wire [15:0] F,
    input  wire [15:0] G,
    input  wire [15:0] H,
    
    // Quadray Outputs (State Persists in Autonomous Mode)
    output reg  [15:0] A_out, B_out, C_out, D_out,
    output reg         done,
    output wire        henosis_pulse   // 1 = Phi-fold fired this cycle
);

    // Resource-Folded Power Dispatch (Shift-only)
    function [15:0] scale_flow(input [15:0] val, input [7:0] intensity);
        begin
            if (intensity == 8'hFF) scale_flow = val;
            else if (intensity >= 8'hC0) scale_flow = val >> 1;
            else if (intensity >= 8'h80) scale_flow = val >> 2;
            else if (intensity >= 8'h40) scale_flow = val >> 3;
            else scale_flow = 16'h0;
        end
    endfunction

    // Sequential Multiplier Instance
    reg  [15:0] mult_a, mult_b;
    reg         mult_start;
    wire [31:0] mult_prod;
    wire        mult_done;

    spu_multiplier_serial u_mult (
        .clk(clk),
        .reset(reset),
        .start(mult_start),
        .a(mult_a),
        .b(mult_b),
        .product(mult_prod),
        .done(mult_done)
    );
    
    // Fixed Point Q8.8 Truncation
    wire [15:0] prod_trunc;
    assign prod_trunc = mult_prod[23:8];

    // ── Phi-Step Fold ──────────────────────────────────────────────────────
    // 18-bit accumulator prevents silent wrap-around.  phi_fold() halves the
    // result when the sum of three Q8.8 products exceeds 16-bit range.
    function [15:0] phi_fold;
        input [17:0] val;
        begin
            if      (val[17]) phi_fold = val[17:2];  // 2-bit overflow → >>2
            else if (val[16]) phi_fold = val[16:1];  // 1-bit overflow → >>1
            else              phi_fold = val[15:0];  // in range
        end
    endfunction

    // Henosis wires — set from combinatorial sum BEFORE registering output
    reg  henosis_B, henosis_C, henosis_D;
    assign henosis_pulse = henosis_B | henosis_C | henosis_D;

    // State Machine
    reg [3:0] state;
    reg [17:0] accum;   // 18-bit: covers worst-case sum of 3 × 16-bit products
    
    // Internal Latch for scaled inputs
    reg [15:0] A_s, B_s, C_s, D_s;

    // Execution States
    localparam S_IDLE  = 4'd0;
    localparam S_BMULT = 4'd1;  // Multiplier sequence
    localparam S_BADD  = 4'd2;  // Accumulate and move to next mult

    reg [3:0] sub_state;

    // Combinatorial preview of the final three-product sum (accum + last product).
    // Valid in S_BADD sub-states 2, 5, 8 when the third product has just arrived.
    wire [17:0] final_sum;
    assign final_sum = accum + {2'b00, prod_trunc};
    
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= S_IDLE;
            sub_state <= 0;
            A_out <= 0; B_out <= 0; C_out <= 0; D_out <= 0;
            A_s <= 0; B_s <= 0; C_s <= 0; D_s <= 0;
            accum <= 0;
            done <= 0;
            mult_start <= 0;
            henosis_B <= 0; henosis_C <= 0; henosis_D <= 0;
        end else begin
            case (state)
                S_IDLE: begin
                    done <= 0;
                    if (start) begin
                        // Select between slave input or persistent state
                        A_s <= scale_flow((mode_autonomous ? A_out : A_in), bloom_intensity);
                        B_s <= scale_flow((mode_autonomous ? B_out : B_in), bloom_intensity);
                        C_s <= scale_flow((mode_autonomous ? C_out : C_in), bloom_intensity);
                        D_s <= scale_flow((mode_autonomous ? D_out : D_in), bloom_intensity);
                        
                        A_out <= scale_flow((mode_autonomous ? A_out : A_in), bloom_intensity);
                        sub_state <= 0;
                        mult_start <= 1;
                        mult_a <= scale_flow((mode_autonomous ? B_out : B_in), bloom_intensity); 
                        mult_b <= F; 
                        state <= S_BMULT;
                    end
                end
                
                S_BMULT: begin
                    mult_start <= 0;
                    if (mult_done) state <= S_BADD;
                end
                
                S_BADD: begin
                    case (sub_state)
                        0: begin // B1
                            accum <= {2'b00, prod_trunc};
                            mult_a <= C_s; mult_b <= H; mult_start <= 1;
                            sub_state <= 1; state <= S_BMULT;
                        end
                        1: begin // B2
                            accum <= accum + {2'b00, prod_trunc};
                            mult_a <= D_s; mult_b <= G; mult_start <= 1;
                            sub_state <= 2; state <= S_BMULT;
                        end
                        2: begin // B_final — apply Phi-fold
                            henosis_B <= (final_sum[17:16] != 2'b00);
                            B_out <= phi_fold(final_sum);
                            mult_a <= B_s; mult_b <= G; mult_start <= 1;
                            sub_state <= 3; state <= S_BMULT;
                        end
                        3: begin // C1
                            accum <= {2'b00, prod_trunc};
                            mult_a <= C_s; mult_b <= F; mult_start <= 1;
                            sub_state <= 4; state <= S_BMULT;
                        end
                        4: begin // C2
                            accum <= accum + {2'b00, prod_trunc};
                            mult_a <= D_s; mult_b <= H; mult_start <= 1;
                            sub_state <= 5; state <= S_BMULT;
                        end
                        5: begin // C_final — apply Phi-fold
                            henosis_C <= (final_sum[17:16] != 2'b00);
                            C_out <= phi_fold(final_sum);
                            mult_a <= B_s; mult_b <= H; mult_start <= 1;
                            sub_state <= 6; state <= S_BMULT;
                        end
                        6: begin // D1
                            accum <= {2'b00, prod_trunc};
                            mult_a <= C_s; mult_b <= G; mult_start <= 1;
                            sub_state <= 7; state <= S_BMULT;
                        end
                        7: begin // D2
                            accum <= accum + {2'b00, prod_trunc};
                            mult_a <= D_s; mult_b <= F; mult_start <= 1;
                            sub_state <= 8; state <= S_BMULT;
                        end
                        8: begin // D_final — apply Phi-fold
                            henosis_D <= (final_sum[17:16] != 2'b00);
                            D_out <= phi_fold(final_sum);
                            done <= 1;
                            state <= S_IDLE;
                        end
                    endcase
                end
            endcase
        end
    end
endmodule
