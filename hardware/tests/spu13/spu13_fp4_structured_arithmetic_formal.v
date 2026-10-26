// Two-width arithmetic equivalence harness for the structured inverter blocks.
// The reference side spells out the corresponding full A31 products and uses
// mathematical modulo; it does not reuse the candidate combiner.

`define ASSERT assert
`define ASSUME assume

module spu13_fp4_structured_arithmetic_formal #(
    parameter FIELD_W = 3,
    parameter PRODUCT_W = 6,
    parameter FORMAL_OP = 0
) (input wire clk);
    localparam REF_W = PRODUCT_W + 6;
    localparam [FIELD_W-1:0] P = {FIELD_W{1'b1}};

    (* anyconst *) reg [2:0] any_op;
    wire [2:0] op = (FORMAL_OP == 0) ? any_op : FORMAL_OP[2:0];
    (* anyconst *) reg [FIELD_W-1:0] a0, a1, a2, a3, b0, b1;

    wire [FIELD_W-1:0] lhs0, lhs1, lhs2, lhs3;
    wire [FIELD_W-1:0] lhs4, lhs5, lhs6, lhs7;
    wire [FIELD_W-1:0] rhs0, rhs1, rhs2, rhs3;
    wire [FIELD_W-1:0] rhs4, rhs5, rhs6, rhs7;
    wire [3:0] product_count;
    wire [PRODUCT_W-1:0] prod0 = lhs0 * rhs0;
    wire [PRODUCT_W-1:0] prod1 = lhs1 * rhs1;
    wire [PRODUCT_W-1:0] prod2 = lhs2 * rhs2;
    wire [PRODUCT_W-1:0] prod3 = lhs3 * rhs3;
    wire [PRODUCT_W-1:0] prod4 = lhs4 * rhs4;
    wire [PRODUCT_W-1:0] prod5 = lhs5 * rhs5;
    wire [PRODUCT_W-1:0] prod6 = lhs6 * rhs6;
    wire [PRODUCT_W-1:0] prod7 = lhs7 * rhs7;
    wire [FIELD_W-1:0] got0, got1, got2, got3;

    spu13_fp4_structured_operand_map #(
        .FIELD_W(FIELD_W)
    ) u_map (
        .op(op), .a0(a0), .a1(a1), .a2(a2), .a3(a3), .b0(b0), .b1(b1),
        .lhs0(lhs0), .lhs1(lhs1), .lhs2(lhs2), .lhs3(lhs3),
        .lhs4(lhs4), .lhs5(lhs5), .lhs6(lhs6), .lhs7(lhs7),
        .rhs0(rhs0), .rhs1(rhs1), .rhs2(rhs2), .rhs3(rhs3),
        .rhs4(rhs4), .rhs5(rhs5), .rhs6(rhs6), .rhs7(rhs7),
        .product_count(product_count)
    );

    spu13_fp4_structured_combine #(
        .FIELD_W(FIELD_W), .PRODUCT_W(PRODUCT_W)
    ) u_combine (
        .op(op),
        .prod0(prod0), .prod1(prod1), .prod2(prod2), .prod3(prod3),
        .prod4(prod4), .prod5(prod5), .prod6(prod6), .prod7(prod7),
        .r0(got0), .r1(got1), .r2(got2), .r3(got3)
    );

    function [FIELD_W-1:0] mneg;
        input [FIELD_W-1:0] x;
        begin mneg = (x == 0) ? 0 : P - x; end
    endfunction

    function [PRODUCT_W-1:0] mulw;
        input [FIELD_W-1:0] x, y;
        begin mulw = x * y; end
    endfunction

    function [REF_W-1:0] extp;
        input [PRODUCT_W-1:0] x;
        begin extp = {{(REF_W-PRODUCT_W){1'b0}}, x}; end
    endfunction

    function [REF_W-1:0] sc3;
        input [PRODUCT_W-1:0] x;
        begin sc3 = (extp(x) << 1) + extp(x); end
    endfunction

    function [REF_W-1:0] sc5;
        input [PRODUCT_W-1:0] x;
        begin sc5 = (extp(x) << 2) + extp(x); end
    endfunction

    function [REF_W-1:0] sc15;
        input [PRODUCT_W-1:0] x;
        begin sc15 = (extp(x) << 4) - extp(x); end
    endfunction

    function [FIELD_W-1:0] ref_reduce;
        input [REF_W-1:0] x;
        begin ref_reduce = x % P; end
    endfunction

    reg [FIELD_W-1:0] ref0, ref1, ref2, ref3;
    always @* begin
        ref0 = 0; ref1 = 0; ref2 = 0; ref3 = 0;
        case (op)
            3'd1: begin
                ref0 = ref_reduce(extp(mulw(a0, a0)) + sc3(mulw(a1, a1)) +
                                  sc5(mulw(a2, mneg(a2))) +
                                  sc15(mulw(a3, mneg(a3))));
                ref1 = ref_reduce(extp(mulw(a0, a1)) + extp(mulw(a1, a0)) +
                                  sc5(mulw(a2, mneg(a3))) +
                                  sc5(mulw(a3, mneg(a2))));
                ref2 = ref_reduce(extp(mulw(a0, mneg(a2))) +
                                  sc3(mulw(a1, mneg(a3))) +
                                  extp(mulw(a2, a0)) + sc3(mulw(a3, a1)));
                ref3 = ref_reduce(extp(mulw(a0, mneg(a3))) +
                                  extp(mulw(a1, mneg(a2))) +
                                  extp(mulw(a2, a1)) + extp(mulw(a3, a0)));
            end
            3'd2: begin
                ref0 = ref_reduce(extp(mulw(a0, a0)) +
                                  sc3(mulw(a1, mneg(a1))));
                ref1 = ref_reduce(extp(mulw(a0, mneg(a1))) +
                                  extp(mulw(a1, a0)));
            end
            3'd3: begin
                ref0 = ref_reduce(extp(mulw(a0, b0)) + sc3(mulw(a1, b1)));
                ref1 = ref_reduce(extp(mulw(a0, b1)) + extp(mulw(a1, b0)));
                ref2 = ref_reduce(extp(mulw(a2, b0)) + sc3(mulw(a3, b1)));
                ref3 = ref_reduce(extp(mulw(a2, b1)) + extp(mulw(a3, b0)));
            end
            3'd4: begin
                ref0 = ref_reduce(extp(mulw(a0, b0)));
                ref1 = ref_reduce(extp(mulw(a1, b0)));
                ref2 = ref_reduce(extp(mulw(a2, b0)));
                ref3 = ref_reduce(extp(mulw(a3, b0)));
            end
        endcase
    end

    always @* begin
        `ASSUME(PRODUCT_W == 2 * FIELD_W);
        `ASSUME(op >= 3'd1 && op <= 3'd4);
        `ASSUME(a0 < P && a1 < P && a2 < P && a3 < P);
        `ASSUME(b0 < P && b1 < P);
        `ASSERT(got0 == ref0);
        `ASSERT(got1 == ref1);
        `ASSERT(got2 == ref2);
        `ASSERT(got3 == ref3);
        if (op == 3'd1) `ASSERT(product_count == 4'd6);
        if (op == 3'd2) `ASSERT(product_count == 4'd2);
        if (op == 3'd3) `ASSERT(product_count == 4'd8);
        if (op == 3'd4) `ASSERT(product_count == 4'd4);
    end
endmodule
