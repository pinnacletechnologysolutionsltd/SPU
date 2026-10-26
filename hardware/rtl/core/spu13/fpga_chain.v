// fpga_chain.v — Stage B fixed-point chain (FPGA reference backend)
// (contract_regen_stageB_2026-08-20.md)
//
// Mirrors the E_REGEN state-transform ops (QLDI loads, QSUB, ROTC angles
// 0-5) on a 2-lane (QR0, QR1) field with 2-normalized normalization:
// each lane carries its own scale exponent m_lane (field = s*v/2^m_lane),
// so Sigma_total = 2^m_lane and the REGEN BQE divide is a shift. Operands
// are re-scaled to a common scale before QSUB. Per-op common-mode rotation
// (dphi_cfg, 2^-16 rad units) exercises the frozen compensation law
// (experiment #3); the REGEN trim restores the exact state.
//
// Q2.40 field: 42-bit signed, 2 integer + 40 fractional. All products and
// differences are computed in 84-bit signed space to avoid edge overflow.
// HALT-AND-FLAG (recorded): the frozen Q2.30 is insufficient for bit-exact
// recovery (recovery amplifies field error by 2^m); Q2.40 restores the
// required margin. Interface extended from the scoping contract's 2-word
// bk_meas_a/b to 8 words + per-lane exponents for the QR domain.
module fpga_chain (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        regen_reload,  // valid K>0 REGEN done: re-encode the
                                      // recovered canonical state (boundary)
    input  wire [31:0] rec_qr0_a, rec_qr0_b, rec_qr0_c, rec_qr0_d,
    input  wire [31:0] rec_qr1_a, rec_qr1_b, rec_qr1_c, rec_qr1_d,

    // op interface (from core dispatch)
    input  wire        op_strobe,    // inst_accept && E_REGEN state-transform
    input  wire [2:0]  op_type,      // 0=LOAD 1=QSUB 2=ROTC
    input  wire [3:0]  op_dst,       // dest lane (0 or 1)
    input  wire [3:0]  op_src_a,     // QSUB lhs / ROTC source lane
    input  wire [3:0]  op_src_b,     // QSUB rhs lane
    input  wire [5:0]  rotc_angle,   // ROTC angle (0-5 mirrored)
    input  wire [31:0] load_a, load_b, load_c, load_d, // signed 32-bit load
    input  wire [7:0]  dphi_cfg,     // per-op common-mode rotation (2^-16 rad)

    // measurement (to spu13_regen)
    output wire [41:0] bk_qr0_meas_a, bk_qr0_meas_b, bk_qr0_meas_c, bk_qr0_meas_d,
    output wire [41:0] bk_qr1_meas_a, bk_qr1_meas_b, bk_qr1_meas_c, bk_qr1_meas_d,
    output wire [9:0]  bk_sigma_exp0,   // QR0 scale exponent
    output wire [9:0]  bk_sigma_exp1,   // QR1 scale exponent
    output wire [15:0] bk_angle_k
);
    // ---- state: QR0 / QR1 fields + per-lane scale exponents ----
    reg [41:0] fld0_a, fld0_b, fld0_c, fld0_d;
    reg [41:0] fld1_a, fld1_b, fld1_c, fld1_d;
    reg [9:0]  m_l0, m_l1;
    reg [15:0] angle_k;

    // ---- helpers (all arithmetic in 84-bit signed space) ----
    // Split into fpga_chain_arith.vh for the 150-line Lithic cap (AGENTS.md).
    `include "fpga_chain_arith.vh"

    wire [41:0] F = fgh(rotc_angle, 2'd0);
    wire [41:0] G = fgh(rotc_angle, 2'd1);
    wire [41:0] H = fgh(rotc_angle, 2'd2);
    wire [41:0] cosv = cos_const(dphi_cfg);
    wire [4:0]  le   = load_exp(load_a, load_b, load_c, load_d);
    wire [4:0]  le0  = load_exp(rec_qr0_a, rec_qr0_b, rec_qr0_c, rec_qr0_d);
    wire [4:0]  le1  = load_exp(rec_qr1_a, rec_qr1_b, rec_qr1_c, rec_qr1_d);

    // source/dest lane field and exponent selection (lanes 0/1; harness)
    wire        sa_is0 = (op_src_a == 4'd0);
    wire        sb_is0 = (op_src_b == 4'd0);
    wire        dst_is0 = (op_dst == 4'd0);

    wire [41:0] sa_a = sa_is0 ? fld0_a : fld1_a;
    wire [41:0] sa_b = sa_is0 ? fld0_b : fld1_b;
    wire [41:0] sa_c = sa_is0 ? fld0_c : fld1_c;
    wire [41:0] sa_d = sa_is0 ? fld0_d : fld1_d;
    wire [9:0]  m_sa = sa_is0 ? m_l0 : m_l1;
    wire [41:0] sb_a = sb_is0 ? fld0_a : fld1_a;
    wire [41:0] sb_b = sb_is0 ? fld0_b : fld1_b;
    wire [41:0] sb_c = sb_is0 ? fld0_c : fld1_c;
    wire [41:0] sb_d = sb_is0 ? fld0_d : fld1_d;
    wire [9:0]  m_sb = sb_is0 ? m_l0 : m_l1;

    // QSUB: operands re-scaled to the common scale max(m_sa, m_sb)
    wire [9:0]  m_c = (m_sa >= m_sb) ? m_sa : m_sb;
    wire [41:0] qa_a = rescale(sa_a, m_sa, m_c);
    wire [41:0] qa_b = rescale(sa_b, m_sa, m_c);
    wire [41:0] qa_c = rescale(sa_c, m_sa, m_c);
    wire [41:0] qa_d = rescale(sa_d, m_sa, m_c);
    wire [41:0] qb_a = rescale(sb_a, m_sb, m_c);
    wire [41:0] qb_b = rescale(sb_b, m_sb, m_c);
    wire [41:0] qb_c = rescale(sb_c, m_sb, m_c);
    wire [41:0] qb_d = rescale(sb_d, m_sb, m_c);

    // ROTC: circulant on the SOURCE (B=fld_b, C=fld_c, D=fld_d), A invariant
    wire [41:0] rot_a = $signed(rescale(sa_a, m_sa, m_sa)) >>> 1;   // A/2 (arith)
    wire [41:0] rot_b = circ_half(F, sa_b, H, sa_c, G, sa_d);
    wire [41:0] rot_c = circ_half(G, sa_b, F, sa_c, H, sa_d);
    wire [41:0] rot_d = circ_half(H, sa_b, G, sa_c, F, sa_d);

    // load value at the load scale (m_lane = le)
    wire [41:0] lv_a = ashr(load_a, le);
    wire [41:0] lv_b = ashr(load_b, le);
    wire [41:0] lv_c = ashr(load_c, le);
    wire [41:0] lv_d = ashr(load_d, le);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fld0_a <= 0; fld0_b <= 0; fld0_c <= 0; fld0_d <= 0;
            fld1_a <= 0; fld1_b <= 0; fld1_c <= 0; fld1_d <= 0;
            m_l0 <= 0; m_l1 <= 0;
            angle_k <= 0;
        end else if (regen_reload) begin
            // REGEN boundary (valid K>0): re-encode the recovered canonical
            // state as the entry for the next block. This resets the chain
            // (fields, per-lane scale, accumulated angle) and is the
            // fixed-point analogue of the regenerated field continuing into
            // the next block. No cos: the common-mode rotation applies per
            // operation, not at the boundary.
            fld0_a <= ashr(rec_qr0_a, le0); fld0_b <= ashr(rec_qr0_b, le0);
            fld0_c <= ashr(rec_qr0_c, le0); fld0_d <= ashr(rec_qr0_d, le0);
            fld1_a <= ashr(rec_qr1_a, le1); fld1_b <= ashr(rec_qr1_b, le1);
            fld1_c <= ashr(rec_qr1_c, le1); fld1_d <= ashr(rec_qr1_d, le1);
            m_l0 <= le0; m_l1 <= le1;
            angle_k <= 0;
        end else if (op_strobe) begin
            angle_k <= angle_k + dphi_cfg;
            case (op_type)
                3'd0: begin  // LOAD: field = v*2^-(2+le) * cos ; m_lane = le
                    if (dst_is0) begin
                        fld0_a <= mul40(lv_a, cosv);
                        fld0_b <= mul40(lv_b, cosv);
                        fld0_c <= mul40(lv_c, cosv);
                        fld0_d <= mul40(lv_d, cosv);
                        m_l0 <= le;
                    end else begin
                        fld1_a <= mul40(lv_a, cosv);
                        fld1_b <= mul40(lv_b, cosv);
                        fld1_c <= mul40(lv_c, cosv);
                        fld1_d <= mul40(lv_d, cosv);
                        m_l1 <= le;
                    end
                end
                3'd1: begin  // QSUB: dst = (src_a - src_b)/2 * cos ; m_dst = m_c+1
                    if (dst_is0) begin
                        fld0_a <= mul40(diff_half(qa_a, qb_a), cosv);
                        fld0_b <= mul40(diff_half(qa_b, qb_b), cosv);
                        fld0_c <= mul40(diff_half(qa_c, qb_c), cosv);
                        fld0_d <= mul40(diff_half(qa_d, qb_d), cosv);
                        m_l0 <= m_c + 1;
                    end else begin
                        fld1_a <= mul40(diff_half(qa_a, qb_a), cosv);
                        fld1_b <= mul40(diff_half(qa_b, qb_b), cosv);
                        fld1_c <= mul40(diff_half(qa_c, qb_c), cosv);
                        fld1_d <= mul40(diff_half(qa_d, qb_d), cosv);
                        m_l1 <= m_c + 1;
                    end
                end
                3'd2: begin  // ROTC: dst = circulant(src)/2 * cos ; m_dst = m_src+1
                    if (dst_is0) begin
                        fld0_a <= mul40(rot_a, cosv);
                        fld0_b <= mul40(rot_b, cosv);
                        fld0_c <= mul40(rot_c, cosv);
                        fld0_d <= mul40(rot_d, cosv);
                        m_l0 <= m_sa + 1;
                    end else begin
                        fld1_a <= mul40(rot_a, cosv);
                        fld1_b <= mul40(rot_b, cosv);
                        fld1_c <= mul40(rot_c, cosv);
                        fld1_d <= mul40(rot_d, cosv);
                        m_l1 <= m_sa + 1;
                    end
                end
            endcase
        end
    end

    // ---- measurement (combinational, consumed by REGEN at start) ----
    assign bk_qr0_meas_a = fld0_a; assign bk_qr0_meas_b = fld0_b;
    assign bk_qr0_meas_c = fld0_c; assign bk_qr0_meas_d = fld0_d;
    assign bk_qr1_meas_a = fld1_a; assign bk_qr1_meas_b = fld1_b;
    assign bk_qr1_meas_c = fld1_c; assign bk_qr1_meas_d = fld1_d;
    assign bk_sigma_exp0 = m_l0;
    assign bk_sigma_exp1 = m_l1;
    assign bk_angle_k    = angle_k;
endmodule
