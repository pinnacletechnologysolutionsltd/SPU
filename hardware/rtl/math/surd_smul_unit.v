// Exact fixed-width Q(sqrt(3)) multiply; normalization is a separate unit.
// LANES=1,2,5 selects a serialized, paired, or fully parallel product schedule.
module surd_smul_unit #(
    parameter integer W = 16,
    parameter integer LANES = 5
) (
    input wire clk,
    input wire rst,
    input wire start,
    input wire signed [W-1:0] a_in,
    input wire signed [W-1:0] b_in,
    input wire [W-1:0] d_in,
    input wire signed [W-1:0] c_in,
    input wire signed [W-1:0] e_in,
    input wire [W-1:0] f_in,
    input wire signed [W-1:0] dst_a,
    input wire signed [W-1:0] dst_b,
    input wire [W-1:0] dst_d,
    output reg signed [W-1:0] result_a,
    output reg signed [W-1:0] result_b,
    output reg [W-1:0] result_d,
    output reg busy,
    output reg done,
    output reg overflow,
    output reg invalid,
    output wire norm_req,
    output wire signed [2*W+1:0] raw_a,
    output wire signed [2*W+1:0] raw_b,
    output wire [2*W-1:0] raw_d,
    input wire norm_valid,
    input wire signed [2*W+1:0] norm_a,
    input wire signed [2*W+1:0] norm_b,
    input wire [2*W-1:0] norm_d
);
    localparam [2:0] IDLE=3'd0, CALC=3'd1, FINAL=3'd2, WAIT_NORM=3'd3;
    reg [2:0] state;
    reg [2:0] index;
    reg signed [2*W-1:0] p_aa, p_bb, p_ab, p_ba;
    reg [2*W-1:0] p_dd;
    reg [W-1:0] held_a, held_b, held_d;
    reg [W-1:0] m0_x, m0_y, m1_x, m1_y;
    reg m0_signed, m1_signed;
    wire [2*W-1:0] m0 = m0_x * m0_y;
    wire [2*W-1:0] m1 = m1_x * m1_y;
    wire [2*W-1:0] m0_exact = signed_product(m0_x,m0_y,m0,m0_signed);
    wire [2*W-1:0] m1_exact = signed_product(m1_x,m1_y,m1,m1_signed);
    wire signed [2*W-1:0] p5_aa = $signed(a_in) * $signed(c_in);
    wire signed [2*W-1:0] p5_bb = $signed(b_in) * $signed(e_in);
    wire signed [2*W-1:0] p5_ab = $signed(a_in) * $signed(e_in);
    wire signed [2*W-1:0] p5_ba = $signed(b_in) * $signed(c_in);
    wire [2*W-1:0] p5_dd = d_in * f_in;
    wire signed [2*W+1:0] aa_w = {{2{p_aa[2*W-1]}},p_aa};
    wire signed [2*W+1:0] bb_w = {{2{p_bb[2*W-1]}},p_bb};
    wire signed [2*W+1:0] ab_w = {{2{p_ab[2*W-1]}},p_ab};
    wire signed [2*W+1:0] ba_w = {{2{p_ba[2*W-1]}},p_ba};
    wire signed [2*W+1:0] three_bb = (bb_w <<< 1) + bb_w;
    wire signed [2*W+1:0] sum_a = aa_w + three_bb;
    wire signed [2*W+1:0] sum_b = ab_w + ba_w;
    wire raw_fits = signed_fits(sum_a) && signed_fits(sum_b) && unsigned_fits(p_dd);
    assign raw_a = sum_a;
    assign raw_b = sum_b;
    assign raw_d = p_dd;
    assign norm_req = (state == WAIT_NORM);

    function signed_fits;
        input signed [2*W+1:0] value;
        begin signed_fits = (value[2*W+1:W] == {(W+2){value[W-1]}}); end
    endfunction
    function unsigned_fits;
        input [2*W-1:0] value;
        begin unsigned_fits = (value[2*W-1:W] == {(W){1'b0}}); end
    endfunction
    function [2*W-1:0] signed_product;
        input [W-1:0] x, y;
        input [2*W-1:0] unsigned_value;
        input is_signed;
        reg [2*W-1:0] corrected;
        begin
            corrected = unsigned_value;
            if (is_signed && x[W-1]) corrected = corrected - ({{W{1'b0}},y} << W);
            if (is_signed && y[W-1]) corrected = corrected - ({{W{1'b0}},x} << W);
            signed_product = corrected;
        end
    endfunction

    always @* begin
        m0_x = a_in & {W{1'b0}}; m0_y = c_in & {W{1'b0}};
        m1_x = b_in & {W{1'b0}}; m1_y = e_in & {W{1'b0}};
        m0_signed = 0; m1_signed = 0;
        if (LANES == 1) begin
            case (index)
                0: begin m0_x=a_in; m0_y=c_in; m0_signed=1; end
                1: begin m0_x=b_in; m0_y=e_in; m0_signed=1; end
                2: begin m0_x=a_in; m0_y=e_in; m0_signed=1; end
                3: begin m0_x=b_in; m0_y=c_in; m0_signed=1; end
                4: begin m0_x=d_in; m0_y=f_in; end
                default: begin end
            endcase
        end else if (LANES == 2) begin
            case (index)
                0: begin m0_x=a_in; m0_y=c_in; m0_signed=1; m1_x=b_in; m1_y=e_in; m1_signed=1; end
                1: begin m0_x=a_in; m0_y=e_in; m0_signed=1; m1_x=b_in; m1_y=c_in; m1_signed=1; end
                2: begin m0_x=d_in; m0_y=f_in; end
                default: begin end
            endcase
        end
    end

    task save_one;
        input [2:0] at;
        input [2*W-1:0] value;
        begin
            case (at)
                0: p_aa <= $signed(value);
                1: p_bb <= $signed(value);
                2: p_ab <= $signed(value);
                3: p_ba <= $signed(value);
                4: p_dd <= value;
                default: begin end
            endcase
        end
    endtask

    task save_two;
        input [2:0] at;
        input [2*W-1:0] first;
        input [2*W-1:0] second;
        begin
            case (at)
                0: begin p_aa <= $signed(first); p_bb <= $signed(second); end
                1: begin p_ab <= $signed(first); p_ba <= $signed(second); end
                2: p_dd <= first;
                default: begin end
            endcase
        end
    endtask

    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE; index <= 0; busy <= 0; done <= 0;
            overflow <= 0; invalid <= 0;
            result_a <= 0; result_b <= 0; result_d <= 1;
            p_aa <= 0; p_bb <= 0; p_ab <= 0; p_ba <= 0; p_dd <= 0;
            held_a <= 0; held_b <= 0; held_d <= 1;
        end else begin
            done <= 0; overflow <= 0; invalid <= 0;
            case (state)
                IDLE: if (start) begin
            if (d_in == 0 || f_in == 0) begin done <= 1; invalid <= 1; end
                    else begin
                        held_a <= dst_a; held_b <= dst_b; held_d <= dst_d;
                        busy <= 1; index <= 0;
                        if (LANES == 5) begin
                            p_aa <= p5_aa; p_bb <= p5_bb;
                            p_ab <= p5_ab; p_ba <= p5_ba; p_dd <= p5_dd;
                            state <= FINAL;
                        end else state <= CALC;
                    end
                end
                CALC: begin
                    if (LANES == 1) save_one(index,m0_exact);
                    else save_two(index,m0_exact,m1_exact);
                    if ((LANES == 1 && index == 4) ||
                        (LANES == 2 && index == 2)) state <= FINAL;
                    else index <= index + 1'b1;
                end
                FINAL: begin
                    if (raw_fits) begin
                        result_a <= sum_a[W-1:0]; result_b <= sum_b[W-1:0];
                        result_d <= p_dd[W-1:0]; done <= 1; busy <= 0; state <= IDLE;
                    end else state <= WAIT_NORM;
                end
                WAIT_NORM: if (norm_valid) begin
                    if (signed_fits(norm_a) && signed_fits(norm_b) && unsigned_fits(norm_d)) begin
                        result_a <= norm_a[W-1:0]; result_b <= norm_b[W-1:0];
                        result_d <= norm_d[W-1:0];
                    end else begin
                        result_a <= held_a; result_b <= held_b; result_d <= held_d;
                        overflow <= 1;
                    end
                    done <= 1; busy <= 0; state <= IDLE;
                end
                default: begin state <= IDLE; busy <= 0; end
            endcase
        end
    end
endmodule
