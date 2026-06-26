`timescale 1ns / 1ps

// spu_cluster_reduce.v — BMU cluster label + confidence gap arbiter
// Port interface matched to spu13_core.v gen_som instantiation (WIDTH parameter).

module spu_cluster_reduce #(
    parameter WIDTH = 18
) (
    input  wire         clk,
    input  wire         rst_n,

    // From spu_som_bmu
    input  wire         bmu_valid,
    input  wire [15:0]  best_node_id,
    input  wire [15:0]  cluster_label_in,
    input  wire [63:0]  best_q,
    input  wire [63:0]  second_q,
    input  wire [63:0]  confidence_gap_in,
    input  wire         has_second,

    // Thresholds
    input  wire [63:0]  ambiguity_threshold,

    // Outputs
    output reg          classify_valid,
    output reg  [15:0]  label,
    output reg  [63:0]  confidence_gap,
    output reg          ambiguous
);

    wire signed [63:0] best_a_ext   = {32'd0, best_q[63:32]};
    wire signed [63:0] second_a_ext = {32'd0, second_q[63:32]};
    wire signed [63:0] best_b_ext   = {{32{best_q[31]}}, best_q[31:0]};
    wire signed [63:0] second_b_ext = {{32{second_q[31]}}, second_q[31:0]};
    wire signed [63:0] thresh_a     = {32'd0, ambiguity_threshold[63:32]};
    wire signed [63:0] thresh_b     = {{32{ambiguity_threshold[31]}}, ambiguity_threshold[31:0]};
    wire signed [63:0] gap_a = second_a_ext - best_a_ext;
    wire signed [63:0] gap_b = second_b_ext - best_b_ext;
    wire signed [63:0] da = gap_a - thresh_a;
    wire signed [63:0] db = gap_b - thresh_b;

    function [127:0] abs_square64;
        input signed [63:0] v;
        reg signed [63:0] mag;
        begin
            mag = (v < 0) ? -v : v;
            abs_square64 = mag * mag;
        end
    endfunction

    wire [127:0] da_sq = abs_square64(da);
    wire [127:0] db_sq3 = abs_square64(db) * 3;
    wire gap_le_thresh =
        (da == 0 && db == 0) ? 1'b1 :
        (da <= 0 && db <= 0) ? 1'b1 :
        (da >= 0 && db >= 0) ? 1'b0 :
        (da < 0 && db > 0)   ? (da_sq > db_sq3) :
                               (da_sq < db_sq3);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            label <= 0;
            confidence_gap <= 0;
            ambiguous <= 0;
            classify_valid <= 0;
        end else begin
            classify_valid <= 1'b0;
            if (bmu_valid) begin
                label <= cluster_label_in;
                if (has_second) begin
                    confidence_gap <= confidence_gap_in;
                    ambiguous <= gap_le_thresh;
                end else begin
                    confidence_gap <= 64'd0;
                    ambiguous <= 1'b0;
                end
                classify_valid <= 1'b1;
            end
        end
    end

endmodule
