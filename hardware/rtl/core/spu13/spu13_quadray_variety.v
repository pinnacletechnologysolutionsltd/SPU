`timescale 1ns / 1ps

// spu13_quadray_variety.v
//
// Division-free Quadray SQR variety predicate over M31.
//
//   delta = sum_{i<j}(c_i - c_j)^2 - target_kappa mod (2^31 - 1)
//
// The four input lanes are native Quadray coordinates A/B/C/D.  The block
// registers the residual two cycles after valid_in so the RPLU pipeline can
// observe structural coherence without invoking the A31 inverter path.

module spu13_quadray_variety (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        valid_in,
    input  wire [31:0] coord_a,
    input  wire [31:0] coord_b,
    input  wire [31:0] coord_c,
    input  wire [31:0] coord_d,
    input  wire [31:0] target_kappa,
    output reg         valid_out,
    output reg  [31:0] delta_out,
    output reg         coherent
);

    localparam [31:0] P = 32'h7FFFFFFF;

    function [31:0] m31_reduce_72;
        input [71:0] z;
        reg [33:0] chunk0, chunk1, chunk2, sum_all;
        begin
            chunk0  = {3'd0, z[30:0]};
            chunk1  = {3'd0, z[61:31]};
            chunk2  = {24'd0, z[71:62]};
            sum_all = chunk0 + chunk1 + chunk2;
            if (sum_all >= P) sum_all = sum_all - P;
            if (sum_all >= P) sum_all = sum_all - P;
            m31_reduce_72 = sum_all[31:0];
        end
    endfunction

    function [31:0] m31_norm;
        input [31:0] x;
        begin
            m31_norm = m31_reduce_72({40'd0, x});
        end
    endfunction

    function [31:0] m31_add;
        input [31:0] x, y;
        reg [32:0] sum;
        begin
            sum = {1'b0, x} + {1'b0, y};
            m31_add = (sum >= P) ? (sum - P) : sum[31:0];
        end
    endfunction

    function [31:0] m31_sub;
        input [31:0] x, y;
        begin
            m31_sub = (x >= y) ? (x - y) : (x + P - y);
        end
    endfunction

    function [31:0] m31_mul;
        input [31:0] x, y;
        reg [63:0] product;
        begin
            product = {32'd0, x} * {32'd0, y};
            m31_mul = m31_reduce_72({8'd0, product});
        end
    endfunction

    reg         s0_valid;
    reg [31:0] a_s0, b_s0, c_s0, d_s0, k_s0;

    wire [31:0] diff_ab = m31_sub(a_s0, b_s0);
    wire [31:0] diff_ac = m31_sub(a_s0, c_s0);
    wire [31:0] diff_ad = m31_sub(a_s0, d_s0);
    wire [31:0] diff_bc = m31_sub(b_s0, c_s0);
    wire [31:0] diff_bd = m31_sub(b_s0, d_s0);
    wire [31:0] diff_cd = m31_sub(c_s0, d_s0);

    wire [31:0] q_ab = m31_mul(diff_ab, diff_ab);
    wire [31:0] q_ac = m31_mul(diff_ac, diff_ac);
    wire [31:0] q_ad = m31_mul(diff_ad, diff_ad);
    wire [31:0] q_bc = m31_mul(diff_bc, diff_bc);
    wire [31:0] q_bd = m31_mul(diff_bd, diff_bd);
    wire [31:0] q_cd = m31_mul(diff_cd, diff_cd);

    reg         s1_valid;
    reg [31:0] q_ab_s1, q_ac_s1, q_ad_s1;
    reg [31:0] q_bc_s1, q_bd_s1, q_cd_s1;
    reg [31:0] k_s1;

    wire [31:0] q_sum0 = m31_add(q_ab_s1, q_ac_s1);
    wire [31:0] q_sum1 = m31_add(q_ad_s1, q_bc_s1);
    wire [31:0] q_sum2 = m31_add(q_bd_s1, q_cd_s1);
    wire [31:0] q_sum3 = m31_add(q_sum0, q_sum1);
    wire [31:0] quadrance = m31_add(q_sum3, q_sum2);
    wire [31:0] delta_w = m31_sub(quadrance, k_s1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_valid <= 1'b0;
            a_s0 <= 32'd0;
            b_s0 <= 32'd0;
            c_s0 <= 32'd0;
            d_s0 <= 32'd0;
            k_s0 <= 32'd0;
            s1_valid <= 1'b0;
            q_ab_s1 <= 32'd0;
            q_ac_s1 <= 32'd0;
            q_ad_s1 <= 32'd0;
            q_bc_s1 <= 32'd0;
            q_bd_s1 <= 32'd0;
            q_cd_s1 <= 32'd0;
            k_s1 <= 32'd0;
            valid_out <= 1'b0;
            delta_out <= 32'd0;
            coherent  <= 1'b0;
        end else begin
            s0_valid <= valid_in;
            if (valid_in) begin
                a_s0 <= m31_norm(coord_a);
                b_s0 <= m31_norm(coord_b);
                c_s0 <= m31_norm(coord_c);
                d_s0 <= m31_norm(coord_d);
                k_s0 <= m31_norm(target_kappa);
            end

            s1_valid <= s0_valid;
            if (s0_valid) begin
                q_ab_s1 <= q_ab;
                q_ac_s1 <= q_ac;
                q_ad_s1 <= q_ad;
                q_bc_s1 <= q_bc;
                q_bd_s1 <= q_bd;
                q_cd_s1 <= q_cd;
                k_s1 <= k_s0;
            end

            valid_out <= s1_valid;
            if (s1_valid) begin
                delta_out <= delta_w;
                coherent  <= (delta_w == 32'd0);
            end else begin
                delta_out <= 32'd0;
                coherent  <= 1'b0;
            end
        end
    end

endmodule
