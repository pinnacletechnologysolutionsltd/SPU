// spu13_lucas_mac.v — Lucas Phinary MAC Co-Processor
// Ring: Z[phi] / L_p.  All ops exact, zero floating-point.
// PSCALE(1c) PCHIRAL(1c) PMUL(3c) PINV(O(log L_p) via Extended Binary GCD).
module spu13_lucas_mac #(
    parameter L_P = 521, parameter L_P_BITS = 10
) (
    input wire clk, rst_n, start,
    input wire [2:0] opcode,  // 0=PSCALE 1=PCHIRAL 2=PMUL 3=PINV
    input wire [L_P_BITS-1:0] op_a, op_b, op_c, op_d,
    output reg busy, done, error,
    output reg [L_P_BITS-1:0] result_a, result_b
);
    localparam [2:0] OP_PSCALE=0, OP_PCHIRAL=1, OP_PMUL=2, OP_PINV=3;
    localparam [1:0] S_IDLE=0, S_BUSY=1;

    function [L_P_BITS-1:0] red;
        input [31:0] x; reg [31:0] t;
        begin t = x; while (t >= L_P) t = t - L_P; red = t[L_P_BITS-1:0]; end
    endfunction

    wire [L_P_BITS-1:0] ps_b = red(op_a + op_b);
    wire [L_P_BITS-1:0] pc_a = red(op_a + op_b);
    wire [L_P_BITS-1:0] pc_b = (op_b == 0) ? 0 : red(2*L_P - op_b);

    reg [1:0] pm_st; reg [31:0] pm_ac, pm_bd, pm_ad, pm_bc;

    // PINV: Extended Binary GCD for norm modular inverse
    reg [L_P_BITS-1:0] pinv_norm;                          // N(a+b*phi)
    reg [L_P_BITS-1:0] pinv_norm_inv;                      // N^-1 mod L_P
    reg [L_P_BITS-1:0] pinv_ca, pinv_cb;                   // saved conjugate
    reg [L_P_BITS-1:0] pinv_u, pinv_v;                     // GCD: u, v
    reg [L_P_BITS-1:0] pinv_x1, pinv_x2;                   // Bezout: x1, x2
    reg [2:0] pinv_st;  // 0=setup 1=euclidean 2=result

    reg [1:0] state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; done <= 0; error <= 0; busy <= 0;
            result_a <= 0; result_b <= 0;
            pm_st <= 0; pm_ac <= 0; pm_bd <= 0; pm_ad <= 0; pm_bc <= 0;
            pinv_norm <= 0; pinv_norm_inv <= 0;
            pinv_ca <= 0; pinv_cb <= 0;
            pinv_u <= 0; pinv_v <= 0; pinv_x1 <= 0; pinv_x2 <= 0; pinv_st <= 0;
        end else begin
            done <= 0; error <= 0;
            case (state)
                S_IDLE: if (start) begin
                    case (opcode)
                        OP_PSCALE: begin
                            result_a <= op_b; result_b <= ps_b; done <= 1;
                        end
                        OP_PCHIRAL: begin
                            result_a <= pc_a; result_b <= pc_b; done <= 1;
                        end
                        OP_PMUL: begin
                            pm_ac <= op_a * op_c; pm_bd <= op_b * op_d;
                            pm_ad <= op_a * op_d; pm_bc <= op_b * op_c;
                            pm_st <= 0; state <= S_BUSY; busy <= 1;
                        end
                        OP_PINV: begin
                            pinv_norm <= red(op_a*op_a + op_a*op_b + L_P*L_P - op_b*op_b);
                            pinv_ca <= pc_a; pinv_cb <= pc_b;  // save conjugate
                            pinv_st <= 0; state <= S_BUSY; busy <= 1;
                        end
                        default: error <= 1;
                    endcase
                end

                S_BUSY: case (opcode)
                    OP_PMUL: begin
                        if (pm_st == 0) pm_st <= 1;
                        else if (pm_st == 1) pm_st <= 2;
                        else begin
                            result_a <= red(pm_ac + pm_bd);
                            result_b <= red(pm_ad + pm_bc + pm_bd);
                            done <= 1; busy <= 0; pm_st <= 0; state <= S_IDLE;
                        end
                    end
                    OP_PINV: begin
                        if (pinv_st == 0) begin
                            if (pinv_norm == 0) begin error <= 1; busy <= 0; state <= S_IDLE; end
                            else begin
                                pinv_u <= pinv_norm; pinv_v <= L_P;
                                pinv_x1 <= 1; pinv_x2 <= 0;
                                pinv_st <= 1;
                            end
                        end else if (pinv_st == 1) begin
                            // Extended Binary GCD for N^-1 mod L_P
                            if (pinv_u == 1) begin
                                pinv_norm_inv <= red(pinv_x1); pinv_st <= 2;
                            end else if (pinv_v == 1) begin
                                pinv_norm_inv <= red(pinv_x2); pinv_st <= 2;
                            end else if (pinv_u[0] == 0) begin
                                pinv_u <= pinv_u >> 1;
                                pinv_x1 <= (pinv_x1[0] == 0) ? (pinv_x1 >> 1) : ((pinv_x1 + L_P) >> 1);
                            end else if (pinv_v[0] == 0) begin
                                pinv_v <= pinv_v >> 1;
                                pinv_x2 <= (pinv_x2[0] == 0) ? (pinv_x2 >> 1) : ((pinv_x2 + L_P) >> 1);
                            end else if (pinv_u >= pinv_v) begin
                                pinv_u <= pinv_u - pinv_v;
                                pinv_x1 <= (pinv_x1 >= pinv_x2) ? (pinv_x1 - pinv_x2) : (pinv_x1 + L_P - pinv_x2);
                            end else begin
                                pinv_v <= pinv_v - pinv_u;
                                pinv_x2 <= (pinv_x2 >= pinv_x1) ? (pinv_x2 - pinv_x1) : (pinv_x2 + L_P - pinv_x1);
                            end
                        end else begin  // pinv_st == 2
                            result_a <= red(pinv_ca * pinv_norm_inv);
                            result_b <= red(pinv_cb * pinv_norm_inv);
                            done <= 1; busy <= 0; pinv_st <= 0; state <= S_IDLE;
                        end
                    end
                    default: begin busy <= 0; state <= S_IDLE; end
                endcase
            endcase
        end
    end
endmodule
