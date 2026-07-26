`timescale 1ns / 1ps

// Candidate sequential A31 multiplier. OP_FULL retains the 16-entry general
// schedule; structured requests execute only 6/2/8/4 entries. Operands are
// captured at acceptance, so a shared-client mux may change after start
// without corrupting the in-flight transaction.

module spu13_m31_multiplier_seq_structured #(
    parameter DEVICE = "SIM"
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,
    input  wire [2:0]   op,
    input  wire [31:0]  a0, a1, a2, a3,
    input  wire [31:0]  b0, b1, b2, b3,
    output reg  [31:0]  r0, r1, r2, r3,
    output reg          done,
    output reg          busy,
    output wire         rns_error,
    output wire [4:0]   logical_products
);
    localparam [2:0] OP_FULL = 3'd0;
    localparam [31:0] P = 32'h7FFFFFFF;

    reg [2:0] op_reg;
    reg [31:0] a0_reg, a1_reg, a2_reg, a3_reg;
    reg [31:0] b0_reg, b1_reg, b2_reg, b3_reg;

    wire [30:0] nlhs0, nlhs1, nlhs2, nlhs3;
    wire [30:0] nlhs4, nlhs5, nlhs6, nlhs7;
    wire [30:0] nrhs0, nrhs1, nrhs2, nrhs3;
    wire [30:0] nrhs4, nrhs5, nrhs6, nrhs7;
    wire [3:0] narrow_product_count;

    spu13_fp4_structured_operand_map #(.FIELD_W(31)) u_operand_map (
        .op(op_reg),
        .a0(a0_reg[30:0]), .a1(a1_reg[30:0]),
        .a2(a2_reg[30:0]), .a3(a3_reg[30:0]),
        .b0(b0_reg[30:0]), .b1(b1_reg[30:0]),
        .lhs0(nlhs0), .lhs1(nlhs1), .lhs2(nlhs2), .lhs3(nlhs3),
        .lhs4(nlhs4), .lhs5(nlhs5), .lhs6(nlhs6), .lhs7(nlhs7),
        .rhs0(nrhs0), .rhs1(nrhs1), .rhs2(nrhs2), .rhs3(nrhs3),
        .rhs4(nrhs4), .rhs5(nrhs5), .rhs6(nrhs6), .rhs7(nrhs7),
        .product_count(narrow_product_count)
    );

    function [4:0] op_product_count;
        input [2:0] request_op;
        begin
            case (request_op)
                3'd0: op_product_count = 5'd16;
                3'd1: op_product_count = 5'd6;
                3'd2: op_product_count = 5'd2;
                3'd3: op_product_count = 5'd8;
                3'd4: op_product_count = 5'd4;
                default: op_product_count = 5'd0;
            endcase
        end
    endfunction

    assign logical_products = op_product_count(op);

    function [7:0] full_sched;
        input [3:0] index;
        begin
            case (index)
                0:  full_sched = {2'd0,2'd0,2'd0,2'd0};
                1:  full_sched = {2'd0,2'd1,2'd1,2'd1};
                2:  full_sched = {2'd0,2'd2,2'd2,2'd2};
                3:  full_sched = {2'd0,2'd3,2'd3,2'd3};
                4:  full_sched = {2'd1,2'd0,2'd1,2'd0};
                5:  full_sched = {2'd1,2'd1,2'd0,2'd0};
                6:  full_sched = {2'd1,2'd2,2'd3,2'd2};
                7:  full_sched = {2'd1,2'd3,2'd2,2'd2};
                8:  full_sched = {2'd2,2'd0,2'd2,2'd0};
                9:  full_sched = {2'd2,2'd1,2'd3,2'd1};
                10: full_sched = {2'd2,2'd2,2'd0,2'd0};
                11: full_sched = {2'd2,2'd3,2'd1,2'd1};
                12: full_sched = {2'd3,2'd0,2'd3,2'd0};
                13: full_sched = {2'd3,2'd1,2'd2,2'd0};
                14: full_sched = {2'd3,2'd2,2'd1,2'd0};
                default: full_sched = {2'd3,2'd3,2'd0,2'd0};
            endcase
        end
    endfunction

    function [31:0] select_a;
        input [1:0] index;
        begin
            case (index)
                0: select_a = a0_reg;
                1: select_a = a1_reg;
                2: select_a = a2_reg;
                default: select_a = a3_reg;
            endcase
        end
    endfunction

    function [31:0] select_b;
        input [1:0] index;
        begin
            case (index)
                0: select_b = b0_reg;
                1: select_b = b1_reg;
                2: select_b = b2_reg;
                default: select_b = b3_reg;
            endcase
        end
    endfunction

    function [31:0] narrow_lhs;
        input [2:0] index;
        begin
            case (index)
                0: narrow_lhs = {1'b0,nlhs0}; 1: narrow_lhs = {1'b0,nlhs1};
                2: narrow_lhs = {1'b0,nlhs2}; 3: narrow_lhs = {1'b0,nlhs3};
                4: narrow_lhs = {1'b0,nlhs4}; 5: narrow_lhs = {1'b0,nlhs5};
                6: narrow_lhs = {1'b0,nlhs6}; default: narrow_lhs = {1'b0,nlhs7};
            endcase
        end
    endfunction

    function [31:0] narrow_rhs;
        input [2:0] index;
        begin
            case (index)
                0: narrow_rhs = {1'b0,nrhs0}; 1: narrow_rhs = {1'b0,nrhs1};
                2: narrow_rhs = {1'b0,nrhs2}; 3: narrow_rhs = {1'b0,nrhs3};
                4: narrow_rhs = {1'b0,nrhs4}; 5: narrow_rhs = {1'b0,nrhs5};
                6: narrow_rhs = {1'b0,nrhs6}; default: narrow_rhs = {1'b0,nrhs7};
            endcase
        end
    endfunction

    reg [31:0] mul_a, mul_b;
    wire [63:0] product;
    generate
        if (DEVICE == "GW5A" || DEVICE == "GOWIN") begin : gen_gowin
            wire signed [35:0] product_raw;
            spu_gowin_multiplier #(.DEVICE(DEVICE)) u_mul (
                .clk(clk), .a(mul_a), .b(mul_b), .p(product_raw)
            );
            assign product = product_raw;
        end else begin : gen_sim
            assign product = mul_a * mul_b;
        end
    endgenerate

    function [71:0] scale72;
        input [63:0] value;
        input [1:0] scale;
        begin
            case (scale)
                0: scale72 = {8'd0,value};
                1: scale72 = {7'd0,value,1'b0} + {8'd0,value};
                2: scale72 = {6'd0,value,2'b0} + {8'd0,value};
                default: scale72 = {4'd0,value,4'b0} - {8'd0,value};
            endcase
        end
    endfunction

    function [31:0] m31_reduce_72;
        input [71:0] value;
        reg [32:0] sum;
        begin
            sum = value[30:0] + value[61:31] + {21'd0,value[71:62]};
            if (sum >= P) sum = sum - P;
            if (sum >= P) sum = sum - P;
            m31_reduce_72 = sum[31:0];
        end
    endfunction

    function [30:0] m31_reduce_product;
        input [61:0] value;
        reg [31:0] sum;
        begin
            sum = {1'b0,value[30:0]} + {1'b0,value[61:31]};
            if (sum >= P) sum = sum - P;
            if (sum >= P) sum = sum - P;
            m31_reduce_product = sum[30:0];
        end
    endfunction

    function [1:0] mod3_32;
        input [31:0] value;
        reg [5:0] even, odd;
        reg signed [6:0] delta;
        integer bit_index;
        begin
            even = 0; odd = 0;
            for (bit_index = 0; bit_index < 16; bit_index = bit_index + 1) begin
                even = even + value[2*bit_index];
                odd = odd + value[2*bit_index+1];
            end
            delta = even - odd;
            if (delta < 0) delta = delta + 18;
            if (delta >= 18) delta = delta - 18;
            if (delta >= 12) delta = delta - 12;
            if (delta >= 9) delta = delta - 9;
            if (delta >= 6) delta = delta - 6;
            if (delta >= 3) delta = delta - 3;
            mod3_32 = delta[1:0];
        end
    endfunction

    reg [30:0] q0, q1, q2, q3, q4, q5, q6, q7;
    wire [30:0] narrow_r0, narrow_r1, narrow_r2, narrow_r3;
    spu13_fp4_structured_combine #(.FIELD_W(31), .PRODUCT_W(62)) u_combine (
        .op(op_reg),
        .prod0({31'd0,q0}), .prod1({31'd0,q1}),
        .prod2({31'd0,q2}), .prod3({31'd0,q3}),
        .prod4({31'd0,q4}), .prod5({31'd0,q5}),
        .prod6({31'd0,q6}), .prod7({31'd0,q7}),
        .r0(narrow_r0), .r1(narrow_r1), .r2(narrow_r2), .r3(narrow_r3)
    );

    localparam S_IDLE = 3'd0;
    localparam S_ISSUE = 3'd1;
    localparam S_CAPTURE = 3'd2;
    localparam S_FINAL = 3'd3;
    reg [2:0] state;
    reg [4:0] index, product_limit;
    reg [71:0] acc0, acc1, acc2, acc3;
    reg [1:0] expected0, expected1, expected2, expected3;
    wire [7:0] schedule = full_sched(index[3:0]);
    wire [31:0] final0 = (op_reg == OP_FULL) ? m31_reduce_72(acc0) : {1'b0,narrow_r0};
    wire [31:0] final1 = (op_reg == OP_FULL) ? m31_reduce_72(acc1) : {1'b0,narrow_r1};
    wire [31:0] final2 = (op_reg == OP_FULL) ? m31_reduce_72(acc2) : {1'b0,narrow_r2};
    wire [31:0] final3 = (op_reg == OP_FULL) ? m31_reduce_72(acc3) : {1'b0,narrow_r3};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; index <= 0; product_limit <= 0;
            op_reg <= OP_FULL;
            a0_reg <= 0; a1_reg <= 0; a2_reg <= 0; a3_reg <= 0;
            b0_reg <= 0; b1_reg <= 0; b2_reg <= 0; b3_reg <= 0;
            mul_a <= 0; mul_b <= 0;
            acc0 <= 0; acc1 <= 0; acc2 <= 0; acc3 <= 0;
            q0 <= 0; q1 <= 0; q2 <= 0; q3 <= 0;
            q4 <= 0; q5 <= 0; q6 <= 0; q7 <= 0;
            r0 <= 0; r1 <= 0; r2 <= 0; r3 <= 0;
            expected0 <= 0; expected1 <= 0; expected2 <= 0; expected3 <= 0;
            done <= 0; busy <= 0;
        end else begin
            done <= 1'b0;
            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        op_reg <= op;
                        a0_reg <= a0; a1_reg <= a1; a2_reg <= a2; a3_reg <= a3;
                        b0_reg <= b0; b1_reg <= b1; b2_reg <= b2; b3_reg <= b3;
                        product_limit <= op_product_count(op);
                        index <= 0;
                        acc0 <= 0; acc1 <= 0; acc2 <= 0; acc3 <= 0;
                        q0 <= 0; q1 <= 0; q2 <= 0; q3 <= 0;
                        q4 <= 0; q5 <= 0; q6 <= 0; q7 <= 0;
                        busy <= 1'b1;
                        state <= S_ISSUE;
                    end
                end
                S_ISSUE: begin
                    if (op_reg == OP_FULL) begin
                        mul_a <= select_a(schedule[5:4]);
                        mul_b <= select_b(schedule[3:2]);
                    end else begin
                        mul_a <= narrow_lhs(index[2:0]);
                        mul_b <= narrow_rhs(index[2:0]);
                    end
                    state <= S_CAPTURE;
                end
                S_CAPTURE: begin
                    if (op_reg == OP_FULL) begin
                        case (schedule[7:6])
                            0: acc0 <= acc0 + scale72(product, schedule[1:0]);
                            1: acc1 <= acc1 + scale72(product, schedule[1:0]);
                            2: acc2 <= acc2 + scale72(product, schedule[1:0]);
                            3: acc3 <= acc3 + scale72(product, schedule[1:0]);
                        endcase
                    end else begin
                        case (index[2:0])
                            0: q0 <= m31_reduce_product(product[61:0]);
                            1: q1 <= m31_reduce_product(product[61:0]);
                            2: q2 <= m31_reduce_product(product[61:0]);
                            3: q3 <= m31_reduce_product(product[61:0]);
                            4: q4 <= m31_reduce_product(product[61:0]);
                            5: q5 <= m31_reduce_product(product[61:0]);
                            6: q6 <= m31_reduce_product(product[61:0]);
                            7: q7 <= m31_reduce_product(product[61:0]);
                        endcase
                    end
                    if (index + 1'b1 == product_limit)
                        state <= S_FINAL;
                    else begin
                        index <= index + 1'b1;
                        state <= S_ISSUE;
                    end
                end
                S_FINAL: begin
                    r0 <= final0; r1 <= final1; r2 <= final2; r3 <= final3;
                    expected0 <= mod3_32(final0); expected1 <= mod3_32(final1);
                    expected2 <= mod3_32(final2); expected3 <= mod3_32(final3);
                    done <= 1'b1;
                    busy <= 1'b0;
                    state <= S_IDLE;
                end
                default: state <= S_IDLE;
            endcase
        end
    end

    assign rns_error = done &&
        ((mod3_32(r0) != expected0) || (mod3_32(r1) != expected1) ||
         (mod3_32(r2) != expected2) || (mod3_32(r3) != expected3));
endmodule
