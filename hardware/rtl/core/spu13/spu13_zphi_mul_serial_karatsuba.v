// SPDX-License-Identifier: CERN-OHL-W-2.0
// Three-product term-serial exact multiplication in Z[phi], phi^2 = phi + 1.
//
// This proof candidate remains beside spu13_zphi_mul_serial until its formal,
// simulation, and mapped-resource gates are complete.  It uses
//
//   t_ac  = xa * ya
//   t_bd  = xb * yb
//   t_sum = (xa + xb) * (ya + yb)
//
//   out_a = t_ac + t_bd
//   out_b = t_sum - t_ac
//
// because t_sum - t_ac = xa*yb + xb*ya + xb*yb.  The third product has
// operands one bit wider on each side.  OUT_W must therefore be at least
// X_W + Y_W + 2 for the unrestricted signed-input contract.
module spu13_zphi_mul_serial_karatsuba #(
    parameter X_W = 72,
    parameter Y_W = 34,
    parameter OUT_W = 108
) (
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire signed [X_W-1:0] xa,
    input  wire signed [X_W-1:0] xb,
    input  wire signed [Y_W-1:0] ya,
    input  wire signed [Y_W-1:0] yb,
    output reg  busy,
    output reg  done,
    output reg  signed [OUT_W-1:0] out_a,
    output reg  signed [OUT_W-1:0] out_b
);
    localparam SUM_X_W = X_W + 1;
    localparam SUM_Y_W = Y_W + 1;
    localparam PRODUCT_W = SUM_X_W + SUM_Y_W;

    reg signed [X_W-1:0] xa_q, xb_q;
    reg signed [Y_W-1:0] ya_q, yb_q;
    reg [1:0] phase;
    reg signed [OUT_W-1:0] term_ac, term_bd;

    wire signed [SUM_X_W-1:0] xa_ext =
        {{(SUM_X_W-X_W){xa_q[X_W-1]}}, xa_q};
    wire signed [SUM_X_W-1:0] xb_ext =
        {{(SUM_X_W-X_W){xb_q[X_W-1]}}, xb_q};
    wire signed [SUM_Y_W-1:0] ya_ext =
        {{(SUM_Y_W-Y_W){ya_q[Y_W-1]}}, ya_q};
    wire signed [SUM_Y_W-1:0] yb_ext =
        {{(SUM_Y_W-Y_W){yb_q[Y_W-1]}}, yb_q};

    reg signed [SUM_X_W-1:0] lhs;
    reg signed [SUM_Y_W-1:0] rhs;
    wire signed [PRODUCT_W-1:0] product_raw = lhs * rhs;
    wire signed [OUT_W-1:0] product =
        {{(OUT_W-PRODUCT_W){product_raw[PRODUCT_W-1]}}, product_raw};

    always @* begin
        lhs = xa_ext;
        rhs = ya_ext;
        case (phase)
            2'd0: begin lhs = xa_ext;      rhs = ya_ext;      end
            2'd1: begin lhs = xb_ext;      rhs = yb_ext;      end
            default: begin lhs = xa_ext + xb_ext; rhs = ya_ext + yb_ext; end
        endcase
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            busy <= 1'b0;
            done <= 1'b0;
            phase <= 2'd0;
            xa_q <= 0; xb_q <= 0; ya_q <= 0; yb_q <= 0;
            term_ac <= 0; term_bd <= 0;
            out_a <= 0; out_b <= 0;
        end else begin
            done <= 1'b0;
            if (!busy) begin
                if (start) begin
                    xa_q <= xa; xb_q <= xb;
                    ya_q <= ya; yb_q <= yb;
                    phase <= 2'd0;
                    busy <= 1'b1;
                end
            end else begin
                case (phase)
                    2'd0: begin
                        term_ac <= product;
                        phase <= 2'd1;
                    end
                    2'd1: begin
                        term_bd <= product;
                        phase <= 2'd2;
                    end
                    default: begin
                        out_a <= term_ac + term_bd;
                        out_b <= product - term_ac;
                        busy <= 1'b0;
                        done <= 1'b1;
                        phase <= 2'd0;
                    end
                endcase
            end
        end
    end
endmodule
