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
        input [2:0] request_op;
        input [2:0] index;
        begin
            case (request_op)
                3'd1: begin
                    case (index)
                        0, 4: narrow_lhs = a0_reg;
                        1:    narrow_lhs = a1_reg;
                        2, 5: narrow_lhs = a2_reg;
                        default: narrow_lhs = a3_reg;
                    endcase
                end
                3'd2: narrow_lhs = (index == 0) ? a0_reg : a1_reg;
                3'd3: begin
                    case (index)
                        0, 2: narrow_lhs = a0_reg;
                        1, 3: narrow_lhs = a1_reg;
                        4, 6: narrow_lhs = a2_reg;
                        default: narrow_lhs = a3_reg;
                    endcase
                end
                3'd4: begin
                    case (index)
                        0: narrow_lhs = a0_reg;
                        1: narrow_lhs = a1_reg;
                        2: narrow_lhs = a2_reg;
                        default: narrow_lhs = a3_reg;
                    endcase
                end
                default: narrow_lhs = 0;
            endcase
        end
    endfunction

    function [31:0] narrow_rhs;
        input [2:0] request_op;
        input [2:0] index;
        begin
            case (request_op)
                3'd1: begin
                    case (index)
                        0: narrow_rhs = a0_reg;
                        1: narrow_rhs = a1_reg;
                        2: narrow_rhs = a2_reg;
                        3: narrow_rhs = a3_reg;
                        4: narrow_rhs = a1_reg;
                        default: narrow_rhs = a3_reg;
                    endcase
                end
                3'd2: narrow_rhs = (index == 0) ? a0_reg : a1_reg;
                3'd3: begin
                    case (index)
                        1, 2, 5, 6: narrow_rhs = b1_reg;
                        default: narrow_rhs = b0_reg;
                    endcase
                end
                3'd4: narrow_rhs = b0_reg;
                default: narrow_rhs = 0;
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

    function [31:0] scale_operand;
        input [31:0] value;
        input [3:0] coefficient;
        reg [35:0] scaled;
        reg [32:0] folded;
        begin
            case (coefficient)
                4'd2:  scaled = {3'd0,value,1'b0};
                4'd3:  scaled = {3'd0,value,1'b0} + {4'd0,value};
                4'd5:  scaled = {2'd0,value,2'b0} + {4'd0,value};
                4'd10: scaled = {1'd0,value,3'b0} + {3'd0,value,1'b0};
                4'd15: scaled = {value,4'b0} - {4'd0,value};
                default: scaled = {4'd0,value};
            endcase
            folded = {2'd0,scaled[30:0]} + {28'd0,scaled[35:31]};
            if (folded >= {1'b0,P}) folded = folded - {1'b0,P};
            scale_operand = folded[31:0];
        end
    endfunction

    // {destination component, subtract, coefficient}.  The single serial
    // reduction/adder consumes this schedule one entry at a time; unlike the
    // shared-parallel backend, it does not instantiate an eight-product
    // combiner beside the general multiplier.
    function [6:0] narrow_accum_schedule;
        input [2:0] request_op;
        input [2:0] index;
        begin
            narrow_accum_schedule = {2'd0,1'b0,4'd1};
            case (request_op)
                3'd1: begin
                    case (index)
                        0: narrow_accum_schedule = {2'd0,1'b0,4'd1};
                        1: narrow_accum_schedule = {2'd0,1'b0,4'd3};
                        2: narrow_accum_schedule = {2'd0,1'b1,4'd5};
                        3: narrow_accum_schedule = {2'd0,1'b1,4'd15};
                        4: narrow_accum_schedule = {2'd1,1'b0,4'd2};
                        default: narrow_accum_schedule = {2'd1,1'b1,4'd10};
                    endcase
                end
                3'd2: begin
                    if (index == 0)
                        narrow_accum_schedule = {2'd0,1'b0,4'd1};
                    else
                        narrow_accum_schedule = {2'd0,1'b1,4'd3};
                end
                3'd3: begin
                    case (index)
                        0: narrow_accum_schedule = {2'd0,1'b0,4'd1};
                        1: narrow_accum_schedule = {2'd0,1'b0,4'd3};
                        2,3: narrow_accum_schedule = {2'd1,1'b0,4'd1};
                        4: narrow_accum_schedule = {2'd2,1'b0,4'd1};
                        5: narrow_accum_schedule = {2'd2,1'b0,4'd3};
                        default: narrow_accum_schedule = {2'd3,1'b0,4'd1};
                    endcase
                end
                3'd4:
                    narrow_accum_schedule = {index[1:0],1'b0,4'd1};
                default: narrow_accum_schedule = {2'd0,1'b0,4'd1};
            endcase
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

    localparam S_IDLE = 3'd0;
    localparam S_ISSUE = 3'd1;
    localparam S_CAPTURE = 3'd2;
    localparam S_FINAL = 3'd3;
    reg [2:0] state;
    reg [4:0] index, product_limit;
    reg [71:0] acc0, acc1, acc2, acc3;
    reg [1:0] expected0, expected1, expected2, expected3;
    wire [7:0] schedule = full_sched(index[3:0]);
    wire [6:0] narrow_schedule = narrow_accum_schedule(op_reg, index[2:0]);
    // p^2 is congruent to zero mod p and exceeds every product.  Coefficients
    // are folded into one multiplier operand before issue.  The bias turns a
    // negative contribution into a non-negative 72-bit addend, so
    // structured and full requests share the existing wide accumulators and
    // final Mersenne reducers.
    localparam [71:0] NEGATIVE_BIAS = 72'h003FFFFFFF00000001;
    wire [71:0] narrow_contribution = narrow_schedule[4] ?
        (NEGATIVE_BIAS - {8'd0,product}) : {8'd0,product};
    wire [71:0] narrow_accumulator =
        (narrow_schedule[6:5] == 0) ? acc0 :
        (narrow_schedule[6:5] == 1) ? acc1 :
        (narrow_schedule[6:5] == 2) ? acc2 : acc3;
    wire [71:0] narrow_accumulator_next =
        narrow_accumulator + narrow_contribution;
    wire [31:0] final0 = m31_reduce_72(acc0);
    wire [31:0] final1 = m31_reduce_72(acc1);
    wire [31:0] final2 = m31_reduce_72(acc2);
    wire [31:0] final3 = m31_reduce_72(acc3);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; index <= 0; product_limit <= 0;
            op_reg <= OP_FULL;
            a0_reg <= 0; a1_reg <= 0; a2_reg <= 0; a3_reg <= 0;
            b0_reg <= 0; b1_reg <= 0; b2_reg <= 0; b3_reg <= 0;
            mul_a <= 0; mul_b <= 0;
            acc0 <= 0; acc1 <= 0; acc2 <= 0; acc3 <= 0;
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
                        busy <= 1'b1;
                        state <= S_ISSUE;
                    end
                end
                S_ISSUE: begin
                    if (op_reg == OP_FULL) begin
                        mul_a <= select_a(schedule[5:4]);
                        mul_b <= select_b(schedule[3:2]);
                    end else begin
                        mul_a <= narrow_lhs(op_reg, index[2:0]);
                        mul_b <= scale_operand(
                            narrow_rhs(op_reg, index[2:0]),
                            narrow_schedule[3:0]);
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
                        case (narrow_schedule[6:5])
                            0: acc0 <= narrow_accumulator_next;
                            1: acc1 <= narrow_accumulator_next;
                            2: acc2 <= narrow_accumulator_next;
                            3: acc3 <= narrow_accumulator_next;
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
