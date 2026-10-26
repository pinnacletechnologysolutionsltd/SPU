`timescale 1ns / 1ps

// Parameterized product map and modular combiner for the structured A31
// inverter stages. FIELD_W denotes the Mersenne field p = 2^FIELD_W - 1;
// production M31 uses FIELD_W=31 and zero-extends results onto 32-bit ports.
//
// Logical product counts:
//   STAGE_A  Z * conj_5(Z), collapsed to (w0,w1):       6
//   STAGE_B  (w0,w1) * conj_3(w0,w1), scalar norm:      2
//   STAGE_D1 Z_conj * (wc0,wc1,0,0):                    8
//   SCALE    four independent temp[i] * norm_inverse:   4

module spu13_fp4_structured_operand_map #(
    parameter FIELD_W = 31
) (
    input  wire [2:0] op,
    input  wire [FIELD_W-1:0] a0, a1, a2, a3,
    input  wire [FIELD_W-1:0] b0, b1,
    output reg  [FIELD_W-1:0] lhs0, lhs1, lhs2, lhs3,
    output reg  [FIELD_W-1:0] lhs4, lhs5, lhs6, lhs7,
    output reg  [FIELD_W-1:0] rhs0, rhs1, rhs2, rhs3,
    output reg  [FIELD_W-1:0] rhs4, rhs5, rhs6, rhs7,
    output reg  [3:0] product_count
);
    localparam OP_STAGE_A  = 3'd1;
    localparam OP_STAGE_B  = 3'd2;
    localparam OP_STAGE_D1 = 3'd3;
    localparam OP_SCALE    = 3'd4;

    always @* begin
        lhs0 = {FIELD_W{1'b0}}; rhs0 = {FIELD_W{1'b0}};
        lhs1 = {FIELD_W{1'b0}}; rhs1 = {FIELD_W{1'b0}};
        lhs2 = {FIELD_W{1'b0}}; rhs2 = {FIELD_W{1'b0}};
        lhs3 = {FIELD_W{1'b0}}; rhs3 = {FIELD_W{1'b0}};
        lhs4 = {FIELD_W{1'b0}}; rhs4 = {FIELD_W{1'b0}};
        lhs5 = {FIELD_W{1'b0}}; rhs5 = {FIELD_W{1'b0}};
        lhs6 = {FIELD_W{1'b0}}; rhs6 = {FIELD_W{1'b0}};
        lhs7 = {FIELD_W{1'b0}}; rhs7 = {FIELD_W{1'b0}};
        product_count = 4'd0;
        case (op)
            OP_STAGE_A: begin
                lhs0 = a0; rhs0 = a0;  // z0^2
                lhs1 = a1; rhs1 = a1;  // z1^2
                lhs2 = a2; rhs2 = a2;  // z2^2
                lhs3 = a3; rhs3 = a3;  // z3^2
                lhs4 = a0; rhs4 = a1;  // z0*z1
                lhs5 = a2; rhs5 = a3;  // z2*z3
                product_count = 4'd6;
            end
            OP_STAGE_B: begin
                lhs0 = a0; rhs0 = a0;  // w0^2
                lhs1 = a1; rhs1 = a1;  // w1^2
                product_count = 4'd2;
            end
            OP_STAGE_D1: begin
                lhs0 = a0; rhs0 = b0;
                lhs1 = a1; rhs1 = b1;
                lhs2 = a0; rhs2 = b1;
                lhs3 = a1; rhs3 = b0;
                lhs4 = a2; rhs4 = b0;
                lhs5 = a3; rhs5 = b1;
                lhs6 = a2; rhs6 = b1;
                lhs7 = a3; rhs7 = b0;
                product_count = 4'd8;
            end
            OP_SCALE: begin
                lhs0 = a0; rhs0 = b0;
                lhs1 = a1; rhs1 = b0;
                lhs2 = a2; rhs2 = b0;
                lhs3 = a3; rhs3 = b0;
                product_count = 4'd4;
            end
            default: begin
                product_count = 4'd0;
            end
        endcase
    end
endmodule


module spu13_fp4_structured_combine #(
    parameter FIELD_W = 31,
    parameter PRODUCT_W = 2 * FIELD_W
) (
    input  wire [2:0] op,
    input  wire [PRODUCT_W-1:0] prod0, prod1, prod2, prod3,
    input  wire [PRODUCT_W-1:0] prod4, prod5, prod6, prod7,
    output reg  [FIELD_W-1:0] r0, r1, r2, r3
);
    localparam OP_STAGE_A  = 3'd1;
    localparam OP_STAGE_B  = 3'd2;
    localparam OP_STAGE_D1 = 3'd3;
    localparam OP_SCALE    = 3'd4;
    localparam [FIELD_W-1:0] P = {FIELD_W{1'b1}};

    function [FIELD_W-1:0] reduce_product;
        input [PRODUCT_W-1:0] value;
        reg [FIELD_W:0] folded;
        begin
            folded = {1'b0, value[FIELD_W-1:0]} +
                     {1'b0, value[PRODUCT_W-1:FIELD_W]};
            if (folded >= {1'b0, P})
                folded = folded - {1'b0, P};
            if (folded >= {1'b0, P})
                folded = folded - {1'b0, P};
            reduce_product = folded[FIELD_W-1:0];
        end
    endfunction

    function [FIELD_W-1:0] madd;
        input [FIELD_W-1:0] x, y;
        reg [FIELD_W:0] sum;
        begin
            sum = {1'b0, x} + {1'b0, y};
            if (sum >= {1'b0, P})
                sum = sum - {1'b0, P};
            madd = sum[FIELD_W-1:0];
        end
    endfunction

    function [FIELD_W-1:0] msub;
        input [FIELD_W-1:0] x, y;
        begin
            if (x >= y)
                msub = x - y;
            else
                msub = x + P - y;
        end
    endfunction

    function [FIELD_W-1:0] scale2;
        input [FIELD_W-1:0] x;
        begin scale2 = madd(x, x); end
    endfunction

    function [FIELD_W-1:0] scale3;
        input [FIELD_W-1:0] x;
        begin scale3 = madd(scale2(x), x); end
    endfunction

    function [FIELD_W-1:0] scale5;
        input [FIELD_W-1:0] x;
        reg [FIELD_W-1:0] x2, x4;
        begin
            x2 = scale2(x);
            x4 = scale2(x2);
            scale5 = madd(x4, x);
        end
    endfunction

    function [FIELD_W-1:0] scale10;
        input [FIELD_W-1:0] x;
        begin scale10 = scale2(scale5(x)); end
    endfunction

    function [FIELD_W-1:0] scale15;
        input [FIELD_W-1:0] x;
        begin scale15 = madd(scale10(x), scale5(x)); end
    endfunction

    wire [FIELD_W-1:0] q0 = reduce_product(prod0);
    wire [FIELD_W-1:0] q1 = reduce_product(prod1);
    wire [FIELD_W-1:0] q2 = reduce_product(prod2);
    wire [FIELD_W-1:0] q3 = reduce_product(prod3);
    wire [FIELD_W-1:0] q4 = reduce_product(prod4);
    wire [FIELD_W-1:0] q5 = reduce_product(prod5);
    wire [FIELD_W-1:0] q6 = reduce_product(prod6);
    wire [FIELD_W-1:0] q7 = reduce_product(prod7);

    always @* begin
        r0 = {FIELD_W{1'b0}};
        r1 = {FIELD_W{1'b0}};
        r2 = {FIELD_W{1'b0}};
        r3 = {FIELD_W{1'b0}};
        case (op)
            OP_STAGE_A: begin
                r0 = msub(madd(q0, scale3(q1)),
                          madd(scale5(q2), scale15(q3)));
                r1 = msub(scale2(q4), scale10(q5));
            end
            OP_STAGE_B: begin
                r0 = msub(q0, scale3(q1));
            end
            OP_STAGE_D1: begin
                r0 = madd(q0, scale3(q1));
                r1 = madd(q2, q3);
                r2 = madd(q4, scale3(q5));
                r3 = madd(q6, q7);
            end
            OP_SCALE: begin
                r0 = q0;
                r1 = q1;
                r2 = q2;
                r3 = q3;
            end
            default: begin
                r0 = {FIELD_W{1'b0}};
                r1 = {FIELD_W{1'b0}};
                r2 = {FIELD_W{1'b0}};
                r3 = {FIELD_W{1'b0}};
            end
        endcase
    end
endmodule
