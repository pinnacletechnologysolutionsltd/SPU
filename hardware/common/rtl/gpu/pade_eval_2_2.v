// Multi-cycle Padé [2/2] evaluator
// Computes y = P(x)/Q(x) with degree 2 numerator and denominator.
// Inputs:
//  - clk, rst_n
//  - start: capture x_in and begin eval
//  - x_q32: signed Q32 input (signed [63:0])
// Outputs:
//  - done: asserted for one cycle when y_q16 valid
//  - y_q16: signed Q16.16 result (32-bit)

module pade_eval_2_2(
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire signed [63:0] x_q32,
    output reg  signed [31:0] y_q16,
    output reg  done
);
    // coeff memories (Q32, 64-bit signed)
    reg signed [63:0] num_coeff [0:2];
    reg signed [63:0] den_coeff [0:2];
    integer i;
    initial begin
        // initialize coeffs to zero to enable fast-path when memory files are absent
        for (i = 0; i < 3; i = i + 1) begin
            num_coeff[i] = 64'sd0;
            den_coeff[i] = 64'sd0;
        end
        // attempt to read coefficient files; if absent, zeros remain
        $readmemh("hardware/common/rtl/gpu/pade_num_2_2_q32.mem", num_coeff);
        $readmemh("hardware/common/rtl/gpu/pade_den_2_2_q32.mem", den_coeff);
    end

    // internal regs
    reg [3:0] state;
    localparam S_IDLE = 4'd0, S_NUM0 = 4'd1, S_NUM1 = 4'd2, S_NUM2 = 4'd3,
               S_DEN0 = 4'd4, S_DEN1 = 4'd5, S_DEN2 = 4'd6, S_DIV = 4'd7, S_DONE = 4'd8;

    reg signed [127:0] acc_num; // 128-bit accumulator
    reg signed [127:0] acc_den;
    reg signed [191:0] mult;    // mult result (up to 192 bits)
    reg signed [127:0] numer128;
    reg signed [127:0] quot128;

    reg signed [63:0] x_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            done <= 1'b0;
            y_q16 <= 0;
            acc_num <= 0; acc_den <= 0; mult <= 0;
            x_reg <= 0;
        end else begin
            done <= 1'b0;
            case (state)
                S_IDLE: begin
                    if (start) begin
                        x_reg <= x_q32;
                        // quick path: if coefficient files are empty (all zeros) just pass-through x->Q16
                        if ((num_coeff[0] == 64'sd0) && (num_coeff[1] == 64'sd0) && (num_coeff[2] == 64'sd0) && (den_coeff[0] == 64'sd0) && (den_coeff[1] == 64'sd0) && (den_coeff[2] == 64'sd0)) begin
                            // convert Q32 x to Q16 (rounding by truncation)
                            y_q16 <= x_q32[47:16];
                            $display("PADE_EVAL: fast-path Q32->Q16 time=%0t x=%0d y=%0d", $time, x_q32, y_q16);
                            state <= S_DONE;
                        end else begin
                            // begin numerator Horner: acc = num_coeff[2]
                            acc_num <= {{64{num_coeff[2][63]}}, num_coeff[2]};
                            state <= S_NUM1; // proceed to first multiply cycle
                        end
                    end
                end
                // Numerator Horner steps (unrolled over cycles)
                S_NUM1: begin
                    // mult = acc_num * x_reg
                    mult <= acc_num * x_reg;
                    state <= S_NUM2;
                end
                S_NUM2: begin
                    // acc_num = (mult >>> 32) + num_coeff[1]
                    acc_num <= (mult >>> 32) + {{64{num_coeff[1][63]}}, num_coeff[1]};
                    // next multiply
                    mult <= ((mult >>> 32) + {{64{num_coeff[1][63]}}, num_coeff[1]}) * x_reg;
                    state <= S_DEN0; // proceed to finish numerator then jump to denominator's next step in next cycle
                end
                // Denominator Horner similarly (we interleave to keep cycles minimal)
                S_DEN0: begin
                    // finish numerator: acc_num <= (previous mult >>> 32) + num_coeff[0]
                    acc_num <= (mult >>> 32) + {{64{num_coeff[0][63]}}, num_coeff[0]};
                    // start denominator acc
                    acc_den <= {{64{den_coeff[2][63]}}, den_coeff[2]};
                    state <= S_DEN1;
                end
                S_DEN1: begin
                    mult <= acc_den * x_reg;
                    state <= S_DEN2;
                end
                S_DEN2: begin
                    acc_den <= (mult >>> 32) + {{64{den_coeff[1][63]}}, den_coeff[1]};
                    mult <= acc_den * x_reg;
                    state <= S_DIV;
                end
                S_DIV: begin
                    acc_den <= (mult >>> 32) + {{64{den_coeff[0][63]}}, den_coeff[0]};
                    // perform division: y_q16 = (acc_num << 16) / acc_den
                    if (acc_den == 0) begin
                        y_q16 <= 32'sd0;
                    end else begin
                        numer128 <= acc_num <<< 16;
                        quot128 <= numer128 / acc_den; // Q16.16
                        y_q16 <= quot128[31:0];
                    end
                    state <= S_DONE;
                end
                S_DONE: begin
                    done <= 1'b1;
                    $display("PADE_DONE time=%0t y=%0d", $time, quot128[31:0]);
                    state <= S_IDLE;
                end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
