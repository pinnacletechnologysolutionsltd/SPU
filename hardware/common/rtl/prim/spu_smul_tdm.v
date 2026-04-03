// SPU Folded Surd Multiplier (v1.0)
// Objective: Resource-efficient Q(sqrt3) multiplication.
// Logic: Uses ONE 32x32 multiplier to perform the 4 cross-products.
// Cycles: 4 cycles per multiplication.

module spu_smul_tdm #(
    parameter BIT_WIDTH = 32
)(
    input  wire clk,
    input  wire reset,
    input  wire start,
    input  wire signed [BIT_WIDTH-1:0] a1, b1, // Operand 1 (Rational + Surd)
    input  wire signed [BIT_WIDTH-1:0] a2, b2, // Operand 2 (Rotor Constant)
    output reg  signed [BIT_WIDTH-1:0] res_a,  // Result Rational
    output reg  signed [BIT_WIDTH-1:0] res_b,  // Result Surd
    output reg  done
);

    // TDM State Machine
    reg [2:0] state;
    localparam IDLE = 3'd0;
    localparam CALC_AA = 3'd1;
    localparam CALC_BB = 3'd2;
    localparam CALC_AB = 3'd3;
    localparam CALC_BA = 3'd4;
    localparam FINISH  = 3'd5;

    // The Single Shared Multiplier
    reg  signed [BIT_WIDTH-1:0] mult_a, mult_b;
    wire signed [63:0] prod = mult_a * mult_b;
    
    // Accumulators for Q(sqrt3) logic:
    // res_a = (a1*a2 + 3*b1*b2)
    // res_b = (a1*b2 + b1*a2)
    reg signed [63:0] acc_a, acc_b;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            res_a <= 0; res_b <= 0;
            acc_a <= 0; acc_b <= 0;
            done  <= 0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 0;
                    if (start) begin
                        mult_a <= a1; mult_b <= a2;
                        state <= CALC_AA;
                    end
                end

                CALC_AA: begin
                    acc_a <= prod; // Start with a1*a2
                    mult_a <= b1; mult_b <= b2; // Prepare for 3*b1*b2
                    state <= CALC_BB;
                end

                CALC_BB: begin
                    // acc_a = (a1*a2) + 3*(b1*b2)
                    acc_a <= acc_a + (prod << 1) + prod;
                    mult_a <= a1; mult_b <= b2; // Prepare for a1*b2
                    state <= CALC_AB;
                end

                CALC_AB: begin
                    acc_b <= prod; // Start with a1*b2
                    mult_a <= b1; mult_b <= a2; // Prepare for b1*a2
                    state <= CALC_BA;
                end

                CALC_BA: begin
                    acc_b <= acc_b + prod; // acc_b = a1*b2 + b1*a2
                    state <= FINISH;
                end

                FINISH: begin
                    res_a <= acc_a >>> 16; // Normalizing shift
                    res_b <= acc_b >>> 16;
                    done <= 1;
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
