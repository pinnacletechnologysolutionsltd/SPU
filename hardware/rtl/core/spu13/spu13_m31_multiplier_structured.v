`timescale 1ns / 1ps

// Candidate shared-parallel A31 multiplier with a structure-specific request
// mode beside the existing full transaction. OP_FULL preserves the production
// 16-product matrix. The shared-parallel backend deliberately reuses both the
// existing product bank and its A31 combiner: structured requests synthesize
// full operands whose zero/conjugate pattern gives the requested result. This
// avoids adding a second narrow combiner beside the Padé multiplier. The
// logical product count records the algebraic schedule; physical parallel
// hardware remains the retained 16-lane bank.

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

    localparam [2:0] OP_STAGE_A  = 3'd1;
    localparam [2:0] OP_STAGE_B  = 3'd2;
    localparam [2:0] OP_STAGE_D1 = 3'd3;
    localparam [2:0] OP_SCALE    = 3'd4;

    assign logical_products = (op == OP_FULL)     ? 5'd16 :
                              (op == OP_STAGE_A)  ? 5'd6  :
                              (op == OP_STAGE_B)  ? 5'd2  :
                              (op == OP_STAGE_D1) ? 5'd8  :
                              (op == OP_SCALE)    ? 5'd4  : 5'd0;

    function [31:0] m31_neg;
        input [31:0] value;
        begin
            m31_neg = (value == 0) ? 32'd0 : P - value;
        end
    endfunction

    // Convert each structured request into an ordinary A31 transaction. The
    // zero patterns mean only 6/2/8/4 unique products are mathematically live,
    // while the fixed shared-parallel bank remains available to Padé.
    wire [31:0] phys_a0 = a0;
    wire [31:0] phys_a1 = a1;
    wire [31:0] phys_a2 = (op == OP_STAGE_B) ? 32'd0 : a2;
    wire [31:0] phys_a3 = (op == OP_STAGE_B) ? 32'd0 : a3;
    wire [31:0] phys_b0 = (op == OP_STAGE_A || op == OP_STAGE_B) ? a0 : b0;
    wire [31:0] phys_b1 = (op == OP_STAGE_A) ? a1 :
                           (op == OP_STAGE_B) ? m31_neg(a1) :
                           (op == OP_STAGE_D1 || op == OP_FULL) ? b1 : 32'd0;
    wire [31:0] phys_b2 = (op == OP_STAGE_A) ? m31_neg(a2) :
                           (op == OP_FULL) ? b2 : 32'd0;
    wire [31:0] phys_b3 = (op == OP_STAGE_A) ? m31_neg(a3) :
                           (op == OP_FULL) ? b3 : 32'd0;

    wire [31:0] mul_a [0:15];
    wire [31:0] mul_b [0:15];
    wire [63:0] product [0:15];

    assign mul_a[0] = phys_a0; assign mul_b[0] = phys_b0;
    assign mul_a[1] = phys_a0; assign mul_b[1] = phys_b1;
    assign mul_a[2] = phys_a0; assign mul_b[2] = phys_b2;
    assign mul_a[3] = phys_a0; assign mul_b[3] = phys_b3;
    assign mul_a[4] = phys_a1; assign mul_b[4] = phys_b0;
    assign mul_a[5] = phys_a1; assign mul_b[5] = phys_b1;
    assign mul_a[6] = phys_a1; assign mul_b[6] = phys_b2;
    assign mul_a[7] = phys_a1; assign mul_b[7] = phys_b3;
    assign mul_a[8] = phys_a2; assign mul_b[8] = phys_b0;
    assign mul_a[9] = phys_a2; assign mul_b[9] = phys_b1;
    assign mul_a[10] = phys_a2; assign mul_b[10] = phys_b2;
    assign mul_a[11] = phys_a2; assign mul_b[11] = phys_b3;
    assign mul_a[12] = phys_a3; assign mul_b[12] = phys_b0;
    assign mul_a[13] = phys_a3; assign mul_b[13] = phys_b1;
    assign mul_a[14] = phys_a3; assign mul_b[14] = phys_b2;
    assign mul_a[15] = phys_a3; assign mul_b[15] = phys_b3;

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

    wire [31:0] start_r0 = m31_reduce_72(full_acc0);
    wire [31:0] start_r1 = m31_reduce_72(full_acc1);
    wire [31:0] start_r2 = m31_reduce_72(full_acc2);
    wire [31:0] start_r3 = m31_reduce_72(full_acc3);

    reg [71:0] s0_acc0, s0_acc1, s0_acc2, s0_acc3;
    reg [1:0] s0_res0, s0_res1, s0_res2, s0_res3;
    reg s0_valid;
    reg [31:0] s1_r0, s1_r1, s1_r2, s1_r3;
    reg [1:0] s1_res0, s1_res1, s1_res2, s1_res3;
    reg s1_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_acc0 <= 0; s0_acc1 <= 0; s0_acc2 <= 0; s0_acc3 <= 0;
            s0_res0 <= 0; s0_res1 <= 0; s0_res2 <= 0; s0_res3 <= 0;
            s0_valid <= 1'b0;
            s1_r0 <= 0; s1_r1 <= 0; s1_r2 <= 0; s1_r3 <= 0;
            s1_res0 <= 0; s1_res1 <= 0; s1_res2 <= 0; s1_res3 <= 0;
            s1_valid <= 1'b0;
        end else begin
            s0_valid <= start;
            if (start) begin
                s0_acc0 <= full_acc0; s0_acc1 <= full_acc1;
                s0_acc2 <= full_acc2; s0_acc3 <= full_acc3;
                s0_res0 <= mod3_32(start_r0); s0_res1 <= mod3_32(start_r1);
                s0_res2 <= mod3_32(start_r2); s0_res3 <= mod3_32(start_r3);
            end

            s1_valid <= s0_valid;
            if (s0_valid) begin
                s1_r0 <= m31_reduce_72(s0_acc0);
                s1_r1 <= m31_reduce_72(s0_acc1);
                s1_r2 <= m31_reduce_72(s0_acc2);
                s1_r3 <= m31_reduce_72(s0_acc3);
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
