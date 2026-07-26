`timescale 1ns / 1ps

// Candidate shared-parallel A31 multiplier with a structure-specific request
// mode beside the existing full transaction. OP_FULL preserves the production
// 16-product matrix. The four inverter operations remap the same product bank;
// no second multiplier bank is instantiated.

module spu13_m31_multiplier_structured (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [2:0]   op,
    input  wire [31:0]  a0, a1, a2, a3,
    input  wire [31:0]  b0, b1, b2, b3,
    output wire [31:0]  r0, r1, r2, r3,
    output wire         done,
    output wire         busy,
    output wire         rns_error,
    output wire [4:0]   logical_products
);
    localparam [2:0] OP_FULL = 3'd0;
    localparam [31:0] P = 32'h7FFFFFFF;

    wire [30:0] nlhs0, nlhs1, nlhs2, nlhs3;
    wire [30:0] nlhs4, nlhs5, nlhs6, nlhs7;
    wire [30:0] nrhs0, nrhs1, nrhs2, nrhs3;
    wire [30:0] nrhs4, nrhs5, nrhs6, nrhs7;
    wire [3:0] narrow_product_count;

    spu13_fp4_structured_operand_map #(.FIELD_W(31)) u_operand_map (
        .op(op),
        .a0(a0[30:0]), .a1(a1[30:0]), .a2(a2[30:0]), .a3(a3[30:0]),
        .b0(b0[30:0]), .b1(b1[30:0]),
        .lhs0(nlhs0), .lhs1(nlhs1), .lhs2(nlhs2), .lhs3(nlhs3),
        .lhs4(nlhs4), .lhs5(nlhs5), .lhs6(nlhs6), .lhs7(nlhs7),
        .rhs0(nrhs0), .rhs1(nrhs1), .rhs2(nrhs2), .rhs3(nrhs3),
        .rhs4(nrhs4), .rhs5(nrhs5), .rhs6(nrhs6), .rhs7(nrhs7),
        .product_count(narrow_product_count)
    );

    assign logical_products = (op == OP_FULL) ? 5'd16
                                                : {1'b0, narrow_product_count};

    // Sixteen physical products remain available for OP_FULL. Narrow requests
    // use lanes 0..7 and drive the unused lanes to zero.
    wire [31:0] mul_a [0:15];
    wire [31:0] mul_b [0:15];
    wire [63:0] product [0:15];
    wire narrow = (op != OP_FULL);

    assign mul_a[0]  = narrow ? {1'b0, nlhs0} : a0;
    assign mul_b[0]  = narrow ? {1'b0, nrhs0} : b0;
    assign mul_a[1]  = narrow ? {1'b0, nlhs1} : a0;
    assign mul_b[1]  = narrow ? {1'b0, nrhs1} : b1;
    assign mul_a[2]  = narrow ? {1'b0, nlhs2} : a0;
    assign mul_b[2]  = narrow ? {1'b0, nrhs2} : b2;
    assign mul_a[3]  = narrow ? {1'b0, nlhs3} : a0;
    assign mul_b[3]  = narrow ? {1'b0, nrhs3} : b3;
    assign mul_a[4]  = narrow ? {1'b0, nlhs4} : a1;
    assign mul_b[4]  = narrow ? {1'b0, nrhs4} : b0;
    assign mul_a[5]  = narrow ? {1'b0, nlhs5} : a1;
    assign mul_b[5]  = narrow ? {1'b0, nrhs5} : b1;
    assign mul_a[6]  = narrow ? {1'b0, nlhs6} : a1;
    assign mul_b[6]  = narrow ? {1'b0, nrhs6} : b2;
    assign mul_a[7]  = narrow ? {1'b0, nlhs7} : a1;
    assign mul_b[7]  = narrow ? {1'b0, nrhs7} : b3;
    assign mul_a[8]  = narrow ? 32'd0 : a2;
    assign mul_b[8]  = narrow ? 32'd0 : b0;
    assign mul_a[9]  = narrow ? 32'd0 : a2;
    assign mul_b[9]  = narrow ? 32'd0 : b1;
    assign mul_a[10] = narrow ? 32'd0 : a2;
    assign mul_b[10] = narrow ? 32'd0 : b2;
    assign mul_a[11] = narrow ? 32'd0 : a2;
    assign mul_b[11] = narrow ? 32'd0 : b3;
    assign mul_a[12] = narrow ? 32'd0 : a3;
    assign mul_b[12] = narrow ? 32'd0 : b0;
    assign mul_a[13] = narrow ? 32'd0 : a3;
    assign mul_b[13] = narrow ? 32'd0 : b1;
    assign mul_a[14] = narrow ? 32'd0 : a3;
    assign mul_b[14] = narrow ? 32'd0 : b2;
    assign mul_a[15] = narrow ? 32'd0 : a3;
    assign mul_b[15] = narrow ? 32'd0 : b3;

    genvar product_index;
    generate
        for (product_index = 0; product_index < 16; product_index = product_index + 1) begin : gen_product_bank
            assign product[product_index] = mul_a[product_index] * mul_b[product_index];
        end
    endgenerate

    wire [71:0] full_acc0 = {8'd0, product[0]} +
                            {7'd0, product[5], 1'b0} + {8'd0, product[5]} +
                            {6'd0, product[10], 2'b0} + {8'd0, product[10]} +
                            {4'd0, product[15], 4'b0} - {8'd0, product[15]};
    wire [71:0] full_acc1 = {8'd0, product[1]} + {8'd0, product[4]} +
                            {6'd0, product[11], 2'b0} + {8'd0, product[11]} +
                            {6'd0, product[14], 2'b0} + {8'd0, product[14]};
    wire [71:0] full_acc2 = {8'd0, product[2]} +
                            {7'd0, product[7], 1'b0} + {8'd0, product[7]} +
                            {8'd0, product[8]} +
                            {7'd0, product[13], 1'b0} + {8'd0, product[13]};
    wire [71:0] full_acc3 = {8'd0, product[3]} + {8'd0, product[6]} +
                            {8'd0, product[9]} + {8'd0, product[12]};

    wire [30:0] narrow_r0, narrow_r1, narrow_r2, narrow_r3;
    spu13_fp4_structured_combine #(
        .FIELD_W(31), .PRODUCT_W(62)
    ) u_narrow_combine (
        .op(op),
        .prod0(product[0][61:0]), .prod1(product[1][61:0]),
        .prod2(product[2][61:0]), .prod3(product[3][61:0]),
        .prod4(product[4][61:0]), .prod5(product[5][61:0]),
        .prod6(product[6][61:0]), .prod7(product[7][61:0]),
        .r0(narrow_r0), .r1(narrow_r1),
        .r2(narrow_r2), .r3(narrow_r3)
    );

    function [31:0] m31_reduce_72;
        input [71:0] value;
        reg [31:0] chunk0, chunk1, chunk2;
        reg [32:0] sum;
        begin
            chunk0 = value[30:0];
            chunk1 = value[61:31];
            chunk2 = {21'd0, value[71:62]};
            sum = chunk0 + chunk1 + chunk2;
            if (sum >= P) sum = sum - P;
            if (sum >= P) sum = sum - P;
            m31_reduce_72 = sum[31:0];
        end
    endfunction

    function [1:0] mod3_32;
        input [31:0] value;
        reg [5:0] even, odd;
        reg signed [6:0] delta;
        integer bit_index;
        begin
            even = 0;
            odd = 0;
            for (bit_index = 0; bit_index < 16; bit_index = bit_index + 1) begin
                even = even + value[2*bit_index];
                odd = odd + value[2*bit_index+1];
            end
            delta = even - odd;
            if (delta < 0) delta = delta + 18;
            if (delta >= 18) delta = delta - 18;
            if (delta >= 12) delta = delta - 12;
            if (delta >= 9)  delta = delta - 9;
            if (delta >= 6)  delta = delta - 6;
            if (delta >= 3)  delta = delta - 3;
            mod3_32 = delta[1:0];
        end
    endfunction

    wire [31:0] start_r0 = narrow ? {1'b0, narrow_r0} : m31_reduce_72(full_acc0);
    wire [31:0] start_r1 = narrow ? {1'b0, narrow_r1} : m31_reduce_72(full_acc1);
    wire [31:0] start_r2 = narrow ? {1'b0, narrow_r2} : m31_reduce_72(full_acc2);
    wire [31:0] start_r3 = narrow ? {1'b0, narrow_r3} : m31_reduce_72(full_acc3);

    reg [71:0] s0_acc0, s0_acc1, s0_acc2, s0_acc3;
    reg [31:0] s0_narrow_r0, s0_narrow_r1, s0_narrow_r2, s0_narrow_r3;
    reg [1:0] s0_res0, s0_res1, s0_res2, s0_res3;
    reg s0_narrow, s0_valid;
    reg [31:0] s1_r0, s1_r1, s1_r2, s1_r3;
    reg [1:0] s1_res0, s1_res1, s1_res2, s1_res3;
    reg s1_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_acc0 <= 0; s0_acc1 <= 0; s0_acc2 <= 0; s0_acc3 <= 0;
            s0_narrow_r0 <= 0; s0_narrow_r1 <= 0;
            s0_narrow_r2 <= 0; s0_narrow_r3 <= 0;
            s0_res0 <= 0; s0_res1 <= 0; s0_res2 <= 0; s0_res3 <= 0;
            s0_narrow <= 1'b0;
            s0_valid <= 1'b0;
            s1_r0 <= 0; s1_r1 <= 0; s1_r2 <= 0; s1_r3 <= 0;
            s1_res0 <= 0; s1_res1 <= 0; s1_res2 <= 0; s1_res3 <= 0;
            s1_valid <= 1'b0;
        end else begin
            s0_valid <= start;
            if (start) begin
                s0_acc0 <= full_acc0; s0_acc1 <= full_acc1;
                s0_acc2 <= full_acc2; s0_acc3 <= full_acc3;
                s0_narrow_r0 <= {1'b0, narrow_r0};
                s0_narrow_r1 <= {1'b0, narrow_r1};
                s0_narrow_r2 <= {1'b0, narrow_r2};
                s0_narrow_r3 <= {1'b0, narrow_r3};
                s0_res0 <= mod3_32(start_r0); s0_res1 <= mod3_32(start_r1);
                s0_res2 <= mod3_32(start_r2); s0_res3 <= mod3_32(start_r3);
                s0_narrow <= narrow;
            end

            s1_valid <= s0_valid;
            if (s0_valid) begin
                s1_r0 <= s0_narrow ? s0_narrow_r0 : m31_reduce_72(s0_acc0);
                s1_r1 <= s0_narrow ? s0_narrow_r1 : m31_reduce_72(s0_acc1);
                s1_r2 <= s0_narrow ? s0_narrow_r2 : m31_reduce_72(s0_acc2);
                s1_r3 <= s0_narrow ? s0_narrow_r3 : m31_reduce_72(s0_acc3);
                s1_res0 <= s0_res0; s1_res1 <= s0_res1;
                s1_res2 <= s0_res2; s1_res3 <= s0_res3;
            end
        end
    end

    assign r0 = s1_r0;
    assign r1 = s1_r1;
    assign r2 = s1_r2;
    assign r3 = s1_r3;
    assign done = s1_valid;
    assign busy = s0_valid || s1_valid;
    assign rns_error = s1_valid &&
        ((mod3_32(s1_r0) != s1_res0) || (mod3_32(s1_r1) != s1_res1) ||
         (mod3_32(s1_r2) != s1_res2) || (mod3_32(s1_r3) != s1_res3));
endmodule
