// SPDX-License-Identifier: CERN-OHL-W-2.0
// Term-serial exact multiplication in Z[phi], phi^2 = phi + 1.
//
// (xa + xb*phi) * (ya + yb*phi)
//   = (xa*ya + xb*yb)
//   + (xa*yb + xb*ya + xb*yb)*phi
//
// One signed integer multiplier is reused across the four terms. Inputs are
// captured on start; done pulses with registered, stable outputs four cycles
// later. OUT_W must retain the exact sums for the selected operand widths.
module spu13_zphi_mul_serial #(
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
    localparam PRODUCT_W = X_W + Y_W;

    reg signed [X_W-1:0] xa_q, xb_q;
    reg signed [Y_W-1:0] ya_q, yb_q;
    reg [1:0] phase;
    reg signed [OUT_W-1:0] term_ac, term_bd, term_ad;
    reg signed [X_W-1:0] lhs;
    reg signed [Y_W-1:0] rhs;
    wire signed [PRODUCT_W-1:0] product_raw = lhs * rhs;
    wire signed [OUT_W-1:0] product =
        {{(OUT_W-PRODUCT_W){product_raw[PRODUCT_W-1]}}, product_raw};

    always @* begin
        lhs = xa_q;
        rhs = ya_q;
        case (phase)
            2'd0: begin lhs = xa_q; rhs = ya_q; end
            2'd1: begin lhs = xb_q; rhs = yb_q; end
            2'd2: begin lhs = xa_q; rhs = yb_q; end
            default: begin lhs = xb_q; rhs = ya_q; end
        endcase
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            busy <= 1'b0;
            done <= 1'b0;
            phase <= 2'd0;
            xa_q <= 0; xb_q <= 0; ya_q <= 0; yb_q <= 0;
            term_ac <= 0; term_bd <= 0; term_ad <= 0;
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
                    2'd0: begin term_ac <= product; phase <= 2'd1; end
                    2'd1: begin term_bd <= product; phase <= 2'd2; end
                    2'd2: begin term_ad <= product; phase <= 2'd3; end
                    default: begin
                        out_a <= term_ac + term_bd;
                        out_b <= term_ad + product + term_bd;
                        busy <= 1'b0;
                        done <= 1'b1;
                        phase <= 2'd0;
                    end
                endcase
            end
        end
    end
endmodule
