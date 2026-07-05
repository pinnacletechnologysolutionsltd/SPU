`timescale 1ns / 1ps

// spu13_rplu2_pade_sidecar.v -- SPI-visible RPLU2 Padé evaluator proof.
//
// This is the low-route-pressure Artix-7 bring-up path.  It keeps the same
// southbridge-visible config/start/result protocol as the full RPLU2 live
// sidecar, but bypasses SOM/BTU/Quadray and feeds rplu_thimble_pade directly.
//
// Config writes:
//   sel=1: Padé numerator coefficient, addr[2:0]=coeff, addr[3]=high pair
//   sel=2: Padé denominator coefficient, addr[2:0]=coeff, addr[3]=high pair
//   sel=3: saddle tuple for row 1, addr[6]=pair, data={c1,c0}/{c3,c2}
//
// Instruction:
//   2A [55:48]=QR result lane, starts Padé evaluation.

module spu13_rplu2_pade_sidecar (
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

    reg [31:0] pade_num_c0 [0:4];
    reg [31:0] pade_num_c1 [0:4];
    reg [31:0] pade_den_c0 [0:4];
    reg [31:0] pade_den_c1 [0:4];
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

    reg [31:0] saddle_c0, saddle_c1, saddle_c2, saddle_c3;
    wire cfg_saddle_row1 = cfg_wr_en && (cfg_sel == CFG_BTU_ROW) &&
                           (cfg_addr[5:0] == 6'd1);

    reg        start_pending;
    reg        pade_start;
    reg [3:0]  result_lane;
    reg        cfg_seen;
    reg        start_seen;
    reg        done_seen;
    reg        flags_seen;
    reg        rns_error_seen;
    reg        pade_busy_seen;
    reg        pade_mult_start_seen;
    reg        inv_start_seen;
    reg        inv_start_accept_seen;
    reg        inv_mult_start_seen;
    reg        shared_done_seen;

    wire [31:0] result_c0, result_c1, result_c2, result_c3;
    wire        pade_done, pade_busy, pade_flags_v;
    wire [2:0]  pade_debug_state;

    wire        pade_mult_start;
    wire [31:0] pade_mult_a0, pade_mult_a1, pade_mult_a2, pade_mult_a3;
    wire [31:0] pade_mult_b0, pade_mult_b1, pade_mult_b2, pade_mult_b3;
    wire [31:0] pade_mult_r0, pade_mult_r1, pade_mult_r2, pade_mult_r3;
    wire        pade_mult_done, pade_mult_busy, pade_mult_rns_error;

    wire        inv_start;
    wire [31:0] inv_z0, inv_z1, inv_z2, inv_z3;
    wire [31:0] inv_r0, inv_r1, inv_r2, inv_r3;
    wire        inv_done, inv_busy, inv_flags_v;

    wire        inv_mult_start;
    wire [31:0] inv_mult_a0, inv_mult_a1, inv_mult_a2, inv_mult_a3;
    wire [31:0] inv_mult_b0, inv_mult_b1, inv_mult_b2, inv_mult_b3;
    wire [31:0] inv_mult_r0, inv_mult_r1, inv_mult_r2, inv_mult_r3;
    wire        inv_mult_done, inv_mult_busy, inv_mult_rns_error;
    wire [3:0]  inv_debug_state;
    wire        inv_debug_start_accept;

    wire        shared_start = inv_mult_start ? inv_mult_start : pade_mult_start;
    wire [31:0] shared_a0 = inv_mult_start ? inv_mult_a0 : pade_mult_a0;
    wire [31:0] shared_a1 = inv_mult_start ? inv_mult_a1 : pade_mult_a1;
    wire [31:0] shared_a2 = inv_mult_start ? inv_mult_a2 : pade_mult_a2;
    wire [31:0] shared_a3 = inv_mult_start ? inv_mult_a3 : pade_mult_a3;
    wire [31:0] shared_b0 = inv_mult_start ? inv_mult_b0 : pade_mult_b0;
    wire [31:0] shared_b1 = inv_mult_start ? inv_mult_b1 : pade_mult_b1;
    wire [31:0] shared_b2 = inv_mult_start ? inv_mult_b2 : pade_mult_b2;
    wire [31:0] shared_b3 = inv_mult_start ? inv_mult_b3 : pade_mult_b3;
    wire [31:0] shared_r0, shared_r1, shared_r2, shared_r3;
    wire        shared_done, shared_busy, shared_rns_error;

    assign pade_mult_r0 = shared_r0;
    assign pade_mult_r1 = shared_r1;
    assign pade_mult_r2 = shared_r2;
    assign pade_mult_r3 = shared_r3;
    assign pade_mult_done = inv_mult_start ? 1'b0 : shared_done;
    assign pade_mult_busy = inv_mult_start ? 1'b1 : shared_busy;
    assign pade_mult_rns_error = inv_mult_start ? 1'b0 : shared_rns_error;

    assign inv_mult_r0 = shared_r0;
    assign inv_mult_r1 = shared_r1;
    assign inv_mult_r2 = shared_r2;
    assign inv_mult_r3 = shared_r3;
    assign inv_mult_done = shared_done;
    assign inv_mult_busy = shared_busy;
    assign inv_mult_rns_error = shared_rns_error;

    rplu_thimble_pade u_pade (
        .clk(clk),
        .rst_n(rst_n),
        .start(pade_start),
        .saddle_c0(saddle_c0),
        .saddle_c1(saddle_c1),
        .saddle_c2(saddle_c2),
        .saddle_c3(saddle_c3),
        .coeff_we(pade_coeff_we),
        .coeff_is_den(pade_coeff_is_den),
        .coeff_addr(pade_coeff_addr),
        .coeff_c0(pade_coeff_c0),
        .coeff_c1(pade_coeff_c1),
        .coeff_c2(pade_coeff_c2),
        .coeff_c3(pade_coeff_c3),
        .result_c0(result_c0),
        .result_c1(result_c1),
        .result_c2(result_c2),
        .result_c3(result_c3),
        .done(pade_done),
        .busy(pade_busy),
        .flags_v(pade_flags_v),
        .mult_start(pade_mult_start),
        .mult_a0(pade_mult_a0),
        .mult_a1(pade_mult_a1),
        .mult_a2(pade_mult_a2),
        .mult_a3(pade_mult_a3),
        .mult_b0(pade_mult_b0),
        .mult_b1(pade_mult_b1),
        .mult_b2(pade_mult_b2),
        .mult_b3(pade_mult_b3),
        .mult_r0(pade_mult_r0),
        .mult_r1(pade_mult_r1),
        .mult_r2(pade_mult_r2),
        .mult_r3(pade_mult_r3),
        .mult_done(pade_mult_done),
        .mult_busy(pade_mult_busy),
        .inv_start(inv_start),
        .inv_z0(inv_z0),
        .inv_z1(inv_z1),
        .inv_z2(inv_z2),
        .inv_z3(inv_z3),
        .inv_r0(inv_r0),
        .inv_r1(inv_r1),
        .inv_r2(inv_r2),
        .inv_r3(inv_r3),
        .inv_done(inv_done),
        .inv_busy(inv_busy),
        .inv_flags_v(inv_flags_v),
        .debug_state(pade_debug_state)
    );

    spu13_fp4_inverter u_inv (
        .clk(clk),
        .rst_n(rst_n),
        .start(inv_start),
        .z0(inv_z0),
        .z1(inv_z1),
        .z2(inv_z2),
        .z3(inv_z3),
        .inv0(inv_r0),
        .inv1(inv_r1),
        .inv2(inv_r2),
        .inv3(inv_r3),
        .done(inv_done),
        .busy(inv_busy),
        .flags_v(inv_flags_v),
        .mult_start(inv_mult_start),
        .mult_a0(inv_mult_a0),
        .mult_a1(inv_mult_a1),
        .mult_a2(inv_mult_a2),
        .mult_a3(inv_mult_a3),
        .mult_b0(inv_mult_b0),
        .mult_b1(inv_mult_b1),
        .mult_b2(inv_mult_b2),
        .mult_b3(inv_mult_b3),
        .mult_r0(inv_mult_r0),
        .mult_r1(inv_mult_r1),
        .mult_r2(inv_mult_r2),
        .mult_r3(inv_mult_r3),
        .mult_done(inv_mult_done),
        .mult_busy(inv_mult_busy),
        .debug_state(inv_debug_state),
        .debug_start_accept(inv_debug_start_accept)
    );

    spu13_m31_multiplier u_shared_mult (
        .clk(clk),
        .rst_n(rst_n),
        .start(shared_start),
        .a0(shared_a0),
        .a1(shared_a1),
        .a2(shared_a2),
        .a3(shared_a3),
        .b0(shared_b0),
        .b1(shared_b1),
        .b2(shared_b2),
        .b3(shared_b3),
        .r0(shared_r0),
        .r1(shared_r1),
        .r2(shared_r2),
        .r3(shared_r3),
        .done(shared_done),
        .busy(shared_busy),
        .rns_error(shared_rns_error)
    );

    wire datapath_busy = pade_busy || inv_busy || shared_busy;
    assign busy = start_pending || datapath_busy;
    assign debug_status = {
        rns_error_seen,
        inv_start_accept_seen,
        inv_mult_start_seen,
        inv_start_seen,
        pade_mult_start_seen,
        pade_busy_seen,
        start_seen,
        cfg_seen
    };
    assign debug_state = (pade_debug_state == 3'd2) ? inv_debug_state[2:0]
                                                    : pade_debug_state;

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
            saddle_c0 <= 32'd1;
            saddle_c1 <= 32'd0;
            saddle_c2 <= 32'd0;
            saddle_c3 <= 32'd0;
            start_pending <= 1'b0;
            pade_start <= 1'b0;
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
            done_seen <= 1'b0;
            flags_seen <= 1'b0;
            rns_error_seen <= 1'b0;
            pade_busy_seen <= 1'b0;
            pade_mult_start_seen <= 1'b0;
            inv_start_seen <= 1'b0;
            inv_start_accept_seen <= 1'b0;
            inv_mult_start_seen <= 1'b0;
            shared_done_seen <= 1'b0;
        end else begin
            pade_start <= 1'b0;
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
            if (cfg_saddle_row1) begin
                if (cfg_addr[6]) begin
                    saddle_c2 <= cfg_data[31:0];
                    saddle_c3 <= cfg_data[63:32];
                end else begin
                    saddle_c0 <= cfg_data[31:0];
                    saddle_c1 <= cfg_data[63:32];
                end
            end

            if (start_pending && !datapath_busy) begin
                pade_start <= 1'b1;
                start_seen <= 1'b1;
                done_seen <= 1'b0;
                flags_seen <= 1'b0;
                rns_error_seen <= 1'b0;
                pade_busy_seen <= 1'b0;
                pade_mult_start_seen <= 1'b0;
                inv_start_seen <= 1'b0;
                inv_start_accept_seen <= 1'b0;
                inv_mult_start_seen <= 1'b0;
                shared_done_seen <= 1'b0;
            end
            if (start_pending && datapath_busy)
                start_pending <= 1'b0;

            if (inst_accept && sidecar_op) begin
                if (busy) begin
                    error <= 1'b1;
                end else begin
                    result_lane <= clamp_lane(inst_word[55:48]);
                    start_pending <= 1'b1;
                end
            end

            if (pade_done) begin
                done_seen <= 1'b1;
                flags_seen <= pade_flags_v;
                error <= pade_flags_v;
                qr_commit_valid <= !pade_flags_v;
                qr_commit_lane <= result_lane;
                qr_commit_A <= {32'd0, result_c0};
                qr_commit_B <= {32'd0, result_c1};
                qr_commit_C <= {32'd0, result_c2};
                qr_commit_D <= {32'd0, result_c3};
            end

            if (pade_busy)
                pade_busy_seen <= 1'b1;
            if (pade_mult_start)
                pade_mult_start_seen <= 1'b1;
            if (inv_start)
                inv_start_seen <= 1'b1;
            if (inv_debug_start_accept)
                inv_start_accept_seen <= 1'b1;
            if (inv_mult_start)
                inv_mult_start_seen <= 1'b1;
            if (shared_done)
                shared_done_seen <= 1'b1;

            if (pade_mult_rns_error || inv_mult_rns_error) begin
                error <= 1'b1;
                rns_error_seen <= 1'b1;
            end
        end
    end
endmodule
