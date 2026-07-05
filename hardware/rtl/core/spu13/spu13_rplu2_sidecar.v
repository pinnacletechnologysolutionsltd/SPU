`timescale 1ns / 1ps

// spu13_rplu2_sidecar.v -- SPI-visible RPLU2 live evaluator adapter.
//
// Probe instruction format, delivered through the existing SPI CMD 0xB1 path:
//   2A RPLU2_START [55:48]=QR result lane, starts fixed-fixture evaluation
//
// Config writes use the same CMD 0xA5 decode as spu13_core:
//   sel=1: Padé numerator coefficient, addr[2:0]=coeff, addr[3]=high pair
//   sel=2: Padé denominator coefficient, addr[2:0]=coeff, addr[3]=high pair
//   sel=3: BTU row, addr[5:0]=row, addr[6]=lane pair
//   sel=6: Quadray target kappa
//
// This sidecar intentionally omits the QR register file and feeds the RPLU2
// pipeline with the proven bring-up fixture QR=(2,0,0,0), which classifies to
// SOM node 1.  The Padé result is committed through the existing QR telemetry.

module spu13_rplu2_sidecar #(
    parameter WIDTH = 18
) (
    input  wire        clk,
    input  wire        rst_n,

    input  wire        inst_valid,
    input  wire [63:0] inst_word,
    output wire        inst_claimed,
    output wire        busy,
    output reg         error,

    input  wire        cfg_wr_en,
    input  wire [2:0]  cfg_sel,
    input  wire [9:0]  cfg_addr,
    input  wire [63:0] cfg_data,

    output reg         qr_commit_valid,
    output reg  [3:0]  qr_commit_lane,
    output reg  [63:0] qr_commit_A,
    output reg  [63:0] qr_commit_B,
    output reg  [63:0] qr_commit_C,
    output reg  [63:0] qr_commit_D,

    output wire [7:0]  debug_status,
    output wire [2:0]  debug_state
);
    localparam [7:0] OP_RPLU2_START = 8'h2A;
    localparam [2:0] CFG_PADE_NUM   = 3'd1;
    localparam [2:0] CFG_PADE_DEN   = 3'd2;
    localparam [2:0] CFG_BTU_ROW    = 3'd3;
    localparam [2:0] CFG_KAPPA      = 3'd6;
    localparam FEATURE_W = 2 * WIDTH;

    wire [7:0] op = inst_word[63:56];
    wire sidecar_op = (op == OP_RPLU2_START);
    assign inst_claimed = inst_valid && sidecar_op;

    reg inst_seen;
    wire inst_accept = inst_valid && !inst_seen;

    function [3:0] clamp_lane;
        input [7:0] lane;
        begin
            clamp_lane = (lane < 8'd13) ? lane[3:0] : 4'd0;
        end
    endfunction

    function [FEATURE_W-1:0] pack_rs;
        input [WIDTH-1:0] p;
        input [WIDTH-1:0] q;
        begin
            pack_rs = {q, p};
        end
    endfunction

    wire [4*FEATURE_W-1:0] fixture_features = {
        pack_rs({WIDTH{1'b0}}, {WIDTH{1'b0}}),
        pack_rs({WIDTH{1'b0}}, {WIDTH{1'b0}}),
        pack_rs({WIDTH{1'b0}}, {WIDTH{1'b0}}),
        pack_rs({{(WIDTH-2){1'b0}}, 2'd2}, {WIDTH{1'b0}})
    };

    reg [31:0] pade_num_c0 [0:4];
    reg [31:0] pade_num_c1 [0:4];
    reg [31:0] pade_den_c0 [0:4];
    reg [31:0] pade_den_c1 [0:4];
    reg [31:0] quadray_target_kappa;
    reg        quadray_target_valid;
    integer i;

    wire [2:0] pade_cfg_idx_raw = cfg_addr[2:0];
    wire       pade_cfg_idx_valid = (pade_cfg_idx_raw < 3'd5);
    wire [2:0] pade_cfg_idx = pade_cfg_idx_valid ? pade_cfg_idx_raw : 3'd0;
    wire       pade_cfg_high = cfg_addr[3];
    wire       cfg_pade_num = cfg_wr_en && (cfg_sel == CFG_PADE_NUM) && pade_cfg_idx_valid;
    wire       cfg_pade_den = cfg_wr_en && (cfg_sel == CFG_PADE_DEN) && pade_cfg_idx_valid;
    wire       pade_coeff_we = (cfg_pade_num || cfg_pade_den) && pade_cfg_high;
    wire       pade_coeff_is_den = cfg_pade_den;
    wire [2:0] pade_coeff_addr = pade_cfg_idx;
    wire [31:0] pade_coeff_c0 = cfg_pade_den ? pade_den_c0[pade_cfg_idx]
                                             : pade_num_c0[pade_cfg_idx];
    wire [31:0] pade_coeff_c1 = cfg_pade_den ? pade_den_c1[pade_cfg_idx]
                                             : pade_num_c1[pade_cfg_idx];
    wire [31:0] pade_coeff_c2 = cfg_data[31:0];
    wire [31:0] pade_coeff_c3 = cfg_data[63:32];

    wire       btu_cfg_we = cfg_wr_en && (cfg_sel == CFG_BTU_ROW);
    wire [5:0] btu_cfg_addr = cfg_addr[5:0];
    wire       btu_cfg_pair = cfg_addr[6];
    wire [63:0] btu_cfg_data = cfg_data;

    reg        start_pending;
    reg        som_start;
    reg [3:0]  result_lane;
    reg        cfg_seen;
    reg        start_seen;
    reg        quadray_seen;
    reg        quadray_coherent_seen;
    reg        thimble_seen;
    reg        rns_error_seen;

    wire        som_done;
    wire [15:0] som_best_id;
    wire [15:0] som_label;
    wire [63:0] som_best_q;
    wire [31:0] thimble_c0, thimble_c1, thimble_c2, thimble_c3;
    wire        thimble_valid;
    wire [31:0] quadray_delta;
    wire        quadray_coherent;
    wire        quadray_valid;
    wire        pipeline_busy;
    wire        pipeline_stall;
    wire        rns_error;

    rplu_pipeline #(
        .WIDTH(WIDTH),
        .SHARE_PADE_INV_MULT(1)
    ) u_rplu2 (
        .clk(clk),
        .rst_n(rst_n),
        .som_features(fixture_features),
        .som_start(som_start),
        .som_done(som_done),
        .som_best_id(som_best_id),
        .som_cluster_label(som_label),
        .som_best_q(som_best_q),
        .pade_coeff_we(pade_coeff_we),
        .pade_coeff_is_den(pade_coeff_is_den),
        .pade_coeff_addr(pade_coeff_addr),
        .pade_c0(pade_coeff_c0),
        .pade_c1(pade_coeff_c1),
        .pade_c2(pade_coeff_c2),
        .pade_c3(pade_coeff_c3),
        .btu_cfg_we(btu_cfg_we),
        .btu_cfg_addr(btu_cfg_addr),
        .btu_cfg_pair(btu_cfg_pair),
        .btu_cfg_data(btu_cfg_data),
        .quadray_target_kappa(quadray_target_kappa),
        .thimble_c0(thimble_c0),
        .thimble_c1(thimble_c1),
        .thimble_c2(thimble_c2),
        .thimble_c3(thimble_c3),
        .thimble_valid(thimble_valid),
        .quadray_delta(quadray_delta),
        .quadray_coherent(quadray_coherent),
        .quadray_valid(quadray_valid),
        .pipeline_busy(pipeline_busy),
        .pipeline_stall(pipeline_stall),
        .rns_error(rns_error),
        .pade_mult_start(),
        .pade_mult_a0(),
        .pade_mult_a1(),
        .pade_mult_a2(),
        .pade_mult_a3(),
        .pade_mult_b0(),
        .pade_mult_b1(),
        .pade_mult_b2(),
        .pade_mult_b3(),
        .pade_mult_r0(32'd0),
        .pade_mult_r1(32'd0),
        .pade_mult_r2(32'd0),
        .pade_mult_r3(32'd0),
        .pade_mult_done(1'b0),
        .pade_mult_busy(1'b0),
        .pade_mult_rns_error(1'b0)
    );

    assign busy = start_pending || pipeline_busy;
    assign debug_status = {
        rns_error_seen,
        pipeline_stall,
        quadray_seen,
        quadray_coherent_seen,
        thimble_seen,
        start_seen,
        cfg_seen,
        busy
    };
    assign debug_state = {start_pending, pipeline_busy, thimble_seen};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            inst_seen <= 1'b0;
        else if (!inst_valid)
            inst_seen <= 1'b0;
        else if (inst_accept)
            inst_seen <= 1'b1;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1) begin
                pade_num_c0[i] <= 32'd0;
                pade_num_c1[i] <= 32'd0;
                pade_den_c0[i] <= 32'd0;
                pade_den_c1[i] <= 32'd0;
            end
            pade_num_c0[0] <= 32'd1;
            pade_den_c0[0] <= 32'd1;
            quadray_target_kappa <= 32'd0;
            quadray_target_valid <= 1'b0;
            start_pending <= 1'b0;
            som_start <= 1'b0;
            result_lane <= 4'd0;
            qr_commit_valid <= 1'b0;
            qr_commit_lane <= 4'd0;
            qr_commit_A <= 64'd0;
            qr_commit_B <= 64'd0;
            qr_commit_C <= 64'd0;
            qr_commit_D <= 64'd0;
            error <= 1'b0;
            cfg_seen <= 1'b0;
            start_seen <= 1'b0;
            quadray_seen <= 1'b0;
            quadray_coherent_seen <= 1'b0;
            thimble_seen <= 1'b0;
            rns_error_seen <= 1'b0;
        end else begin
            som_start <= 1'b0;
            qr_commit_valid <= 1'b0;
            error <= 1'b0;

            if (cfg_wr_en)
                cfg_seen <= 1'b1;

            if (cfg_pade_num && !pade_cfg_high) begin
                pade_num_c0[pade_cfg_idx] <= cfg_data[31:0];
                pade_num_c1[pade_cfg_idx] <= cfg_data[63:32];
            end
            if (cfg_pade_den && !pade_cfg_high) begin
                pade_den_c0[pade_cfg_idx] <= cfg_data[31:0];
                pade_den_c1[pade_cfg_idx] <= cfg_data[63:32];
            end
            if (cfg_wr_en && cfg_sel == CFG_KAPPA) begin
                quadray_target_kappa <= cfg_data[31:0];
                quadray_target_valid <= 1'b1;
            end

            if (start_pending && !pipeline_busy) begin
                som_start <= 1'b1;
                start_pending <= 1'b0;
                start_seen <= 1'b1;
            end

            if (inst_accept && sidecar_op) begin
                if (busy) begin
                    error <= 1'b1;
                end else begin
                    result_lane <= clamp_lane(inst_word[55:48]);
                    start_pending <= 1'b1;
                    quadray_seen <= 1'b0;
                    quadray_coherent_seen <= 1'b0;
                    thimble_seen <= 1'b0;
                    rns_error_seen <= 1'b0;
                end
            end

            if (quadray_valid) begin
                quadray_seen <= 1'b1;
                quadray_coherent_seen <= quadray_coherent;
                if (quadray_target_valid && !quadray_coherent)
                    error <= 1'b1;
            end

            if (rns_error || pipeline_stall) begin
                error <= 1'b1;
                if (rns_error)
                    rns_error_seen <= 1'b1;
            end

            if (thimble_valid) begin
                thimble_seen <= 1'b1;
                qr_commit_valid <= 1'b1;
                qr_commit_lane <= result_lane;
                qr_commit_A <= {32'd0, thimble_c0};
                qr_commit_B <= {32'd0, thimble_c1};
                qr_commit_C <= {32'd0, thimble_c2};
                qr_commit_D <= {32'd0, thimble_c3};
            end
        end
    end
endmodule
