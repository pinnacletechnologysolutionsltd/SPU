// SPDX-License-Identifier: CERN-OHL-W-2.0
// Exact closed-segment contact over Z[phi], phi^2 = phi + 1.
//
// The engine solves s*u - t*v = w using the first nonzero 2x2 coordinate
// minor, checks s,t in [0,1] with exact Q(sqrt(5)) sign predicates, and then
// verifies the remaining coordinate. Parallel lines take a separate exact
// collinearity/interval-overlap path. One asymmetric phi multiplier and one
// sign comparator are shared across the fixed micro-program.
module spu13_tensegrity_intersection (
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire signed [31:0] p0_xa, p0_xb, p0_ya, p0_yb, p0_za, p0_zb,
    input  wire signed [31:0] p1_xa, p1_xb, p1_ya, p1_yb, p1_za, p1_zb,
    input  wire signed [31:0] q0_xa, q0_xb, q0_ya, q0_yb, q0_za, q0_zb,
    input  wire signed [31:0] q1_xa, q1_xb, q1_ya, q1_yb, q1_za, q1_zb,
    output reg  busy,
    output reg  done,
    output reg  contact
);
    localparam [1:0] SG_ZERO = 2'd0, SG_POS = 2'd1, SG_NEG = 2'd2;

    localparam [4:0] X_IDLE       = 5'd0,
                     X_PREP       = 5'd1,
                     X_D0         = 5'd2,
                     X_D1         = 5'd3,
                     X_S0         = 5'd4,
                     X_S1         = 5'd5,
                     X_T0         = 5'd6,
                     X_T1         = 5'd7,
                     X_SIGN_D     = 5'd8,
                     X_SIGN_S     = 5'd9,
                     X_SIGN_DS    = 5'd10,
                     X_SIGN_T     = 5'd11,
                     X_SIGN_DT    = 5'd12,
                     X_EQ0        = 5'd13,
                     X_EQ1        = 5'd14,
                     X_EQ2        = 5'd15,
                     X_COL0       = 5'd16,
                     X_COL1       = 5'd17,
                     X_SIGN_PDIR  = 5'd18,
                     X_SIGN_QDIR  = 5'd19,
                     X_OVERLAP0   = 5'd20,
                     X_OVERLAP1   = 5'd21,
                     X_DONE       = 5'd22,
                     X_SIGN_EVAL  = 5'd23,
                     X_CAND_EVAL  = 5'd24,
                     X_EQ_EVAL    = 5'd25;

    reg [4:0] state;
    reg [1:0] minor_index;
    reg [1:0] col_axis;

    reg signed [31:0] p0a [0:2], p0b [0:2];
    reg signed [31:0] p1a [0:2], p1b [0:2];
    reg signed [31:0] q0a [0:2], q0b [0:2];
    reg signed [31:0] q1a [0:2], q1b [0:2];
    reg signed [32:0] ua [0:2], ub [0:2];
    reg signed [32:0] va [0:2], vb [0:2];
    reg signed [32:0] wa [0:2], wb [0:2];

    reg signed [107:0] product0_a, product0_b;
    reg signed [107:0] product1_a, product1_b;
    reg signed [107:0] product2_a, product2_b;
    reg signed [107:0] candidate_hold_a, candidate_hold_b;
    reg [1:0] candidate_op;
    reg signed [71:0] det_a, det_b;
    reg signed [71:0] s_num_a, s_num_b;
    reg signed [71:0] t_num_a, t_num_b;
    reg [1:0] sign_d, sign_s, sign_ds, sign_t;
    reg [3:0] sign_op;
    reg p_forward, q_forward, overlap0_ok;

    function signed [32:0] pick33;
        input [1:0] axis;
        input signed [32:0] x, y, z;
        begin
            case (axis)
                2'd0: pick33 = x;
                2'd1: pick33 = y;
                default: pick33 = z;
            endcase
        end
    endfunction

    function signed [31:0] pick32;
        input [1:0] axis;
        input signed [31:0] x, y, z;
        begin
            case (axis)
                2'd0: pick32 = x;
                2'd1: pick32 = y;
                default: pick32 = z;
            endcase
        end
    endfunction

    wire [1:0] axis_i = (minor_index == 2'd2) ? 2'd1 : 2'd0;
    wire [1:0] axis_j = (minor_index == 2'd0) ? 2'd1 : 2'd2;
    wire [1:0] axis_k = (minor_index == 2'd0) ? 2'd2 :
                        (minor_index == 2'd1) ? 2'd1 : 2'd0;

    wire signed [32:0] ui_a = pick33(axis_i, ua[0], ua[1], ua[2]);
    wire signed [32:0] ui_b = pick33(axis_i, ub[0], ub[1], ub[2]);
    wire signed [32:0] uj_a = pick33(axis_j, ua[0], ua[1], ua[2]);
    wire signed [32:0] uj_b = pick33(axis_j, ub[0], ub[1], ub[2]);
    wire signed [32:0] uk_a = pick33(axis_k, ua[0], ua[1], ua[2]);
    wire signed [32:0] uk_b = pick33(axis_k, ub[0], ub[1], ub[2]);
    wire signed [32:0] vi_a = pick33(axis_i, va[0], va[1], va[2]);
    wire signed [32:0] vi_b = pick33(axis_i, vb[0], vb[1], vb[2]);
    wire signed [32:0] vj_a = pick33(axis_j, va[0], va[1], va[2]);
    wire signed [32:0] vj_b = pick33(axis_j, vb[0], vb[1], vb[2]);
    wire signed [32:0] vk_a = pick33(axis_k, va[0], va[1], va[2]);
    wire signed [32:0] vk_b = pick33(axis_k, vb[0], vb[1], vb[2]);
    wire signed [32:0] wi_a = pick33(axis_i, wa[0], wa[1], wa[2]);
    wire signed [32:0] wi_b = pick33(axis_i, wb[0], wb[1], wb[2]);
    wire signed [32:0] wj_a = pick33(axis_j, wa[0], wa[1], wa[2]);
    wire signed [32:0] wj_b = pick33(axis_j, wb[0], wb[1], wb[2]);
    wire signed [32:0] wk_a = pick33(axis_k, wa[0], wa[1], wa[2]);
    wire signed [32:0] wk_b = pick33(axis_k, wb[0], wb[1], wb[2]);

    // Shared asymmetric phi product. The wide operand is a determinant or a
    // sign-extended coordinate; the narrow operand is always a coordinate
    // difference. Products are retained at 108 bits for the final equality.
    reg signed [71:0] mul_xa, mul_xb;
    reg signed [33:0] mul_ya, mul_yb;
    wire signed [105:0] mul_ac_raw = mul_xa * mul_ya;
    wire signed [105:0] mul_bd_raw = mul_xb * mul_yb;
    wire signed [105:0] mul_ad_raw = mul_xa * mul_yb;
    wire signed [105:0] mul_bc_raw = mul_xb * mul_ya;
    wire signed [107:0] mul_ac = {{2{mul_ac_raw[105]}}, mul_ac_raw};
    wire signed [107:0] mul_bd = {{2{mul_bd_raw[105]}}, mul_bd_raw};
    wire signed [107:0] mul_ad = {{2{mul_ad_raw[105]}}, mul_ad_raw};
    wire signed [107:0] mul_bc = {{2{mul_bc_raw[105]}}, mul_bc_raw};
    wire signed [107:0] mul_out_a = mul_ac + mul_bd;
    wire signed [107:0] mul_out_b = mul_ad + mul_bc + mul_bd;

    wire signed [107:0] candidate_a = mul_out_a - product0_a;
    wire signed [107:0] candidate_b = mul_out_b - product0_b;
    wire candidate_zero = (candidate_a == 0 && candidate_b == 0);

    always @* begin
        mul_xa = 72'sd0; mul_xb = 72'sd0;
        mul_ya = 34'sd0; mul_yb = 34'sd0;
        case (state)
            X_D0: begin
                mul_xa = {{39{ui_a[32]}}, ui_a}; mul_xb = {{39{ui_b[32]}}, ui_b};
                mul_ya = {{1{vj_a[32]}}, vj_a}; mul_yb = {{1{vj_b[32]}}, vj_b};
            end
            X_D1: begin
                mul_xa = {{39{uj_a[32]}}, uj_a}; mul_xb = {{39{uj_b[32]}}, uj_b};
                mul_ya = {{1{vi_a[32]}}, vi_a}; mul_yb = {{1{vi_b[32]}}, vi_b};
            end
            X_S0: begin
                mul_xa = {{39{wi_a[32]}}, wi_a}; mul_xb = {{39{wi_b[32]}}, wi_b};
                mul_ya = {{1{vj_a[32]}}, vj_a}; mul_yb = {{1{vj_b[32]}}, vj_b};
            end
            X_S1: begin
                mul_xa = {{39{wj_a[32]}}, wj_a}; mul_xb = {{39{wj_b[32]}}, wj_b};
                mul_ya = {{1{vi_a[32]}}, vi_a}; mul_yb = {{1{vi_b[32]}}, vi_b};
            end
            X_T0: begin
                mul_xa = {{39{ui_a[32]}}, ui_a}; mul_xb = {{39{ui_b[32]}}, ui_b};
                mul_ya = {{1{wj_a[32]}}, wj_a}; mul_yb = {{1{wj_b[32]}}, wj_b};
            end
            X_T1: begin
                mul_xa = {{39{uj_a[32]}}, uj_a}; mul_xb = {{39{uj_b[32]}}, uj_b};
                mul_ya = {{1{wi_a[32]}}, wi_a}; mul_yb = {{1{wi_b[32]}}, wi_b};
            end
            X_EQ0: begin
                mul_xa = s_num_a; mul_xb = s_num_b;
                mul_ya = {{1{uk_a[32]}}, uk_a}; mul_yb = {{1{uk_b[32]}}, uk_b};
            end
            X_EQ1: begin
                mul_xa = t_num_a; mul_xb = t_num_b;
                mul_ya = {{1{vk_a[32]}}, vk_a}; mul_yb = {{1{vk_b[32]}}, vk_b};
            end
            X_EQ2: begin
                mul_xa = det_a; mul_xb = det_b;
                mul_ya = {{1{wk_a[32]}}, wk_a}; mul_yb = {{1{wk_b[32]}}, wk_b};
            end
            X_COL0: begin
                mul_xa = {{39{wi_a[32]}}, wi_a}; mul_xb = {{39{wi_b[32]}}, wi_b};
                mul_ya = {{1{uj_a[32]}}, uj_a}; mul_yb = {{1{uj_b[32]}}, uj_b};
            end
            X_COL1: begin
                mul_xa = {{39{wj_a[32]}}, wj_a}; mul_xb = {{39{wj_b[32]}}, wj_b};
                mul_ya = {{1{ui_a[32]}}, ui_a}; mul_yb = {{1{ui_b[32]}}, ui_b};
            end
            default: begin end
        endcase
    end

    // Exact sign of a+b*phi via r+s*sqrt(5), r=2a+b, s=b. The determinant
    // range is 72 bits; 148-bit squares cover every legal 32-bit TGR1 input.
    reg signed [71:0] sign_in_a, sign_in_b;
    wire signed [73:0] sign_r = ({{2{sign_in_a[71]}}, sign_in_a} <<< 1) +
                                {{2{sign_in_b[71]}}, sign_in_b};
    wire signed [73:0] sign_root = {{2{sign_in_b[71]}}, sign_in_b};
    wire [147:0] sign_r_sq = sign_r * sign_r;
    wire [147:0] sign_s_sq = sign_root * sign_root;
    wire [147:0] sign_5s_sq = (sign_s_sq << 2) + sign_s_sq;
    reg [1:0] sign_value;

    always @* begin
        if (sign_r == 0 && sign_root == 0)
            sign_value = SG_ZERO;
        else if (!sign_r[73] && !sign_root[73])
            sign_value = SG_POS;
        else if (sign_r[73] && sign_root[73])
            sign_value = SG_NEG;
        else if (!sign_r[73] && sign_root[73])
            sign_value = (sign_r_sq > sign_5s_sq) ? SG_POS : SG_NEG;
        else
            sign_value = (sign_5s_sq > sign_r_sq) ? SG_POS : SG_NEG;
    end

    wire signed [31:0] p0_axis_a = pick32(col_axis, p0a[0], p0a[1], p0a[2]);
    wire signed [31:0] p0_axis_b = pick32(col_axis, p0b[0], p0b[1], p0b[2]);
    wire signed [31:0] p1_axis_a = pick32(col_axis, p1a[0], p1a[1], p1a[2]);
    wire signed [31:0] p1_axis_b = pick32(col_axis, p1b[0], p1b[1], p1b[2]);
    wire signed [31:0] q0_axis_a = pick32(col_axis, q0a[0], q0a[1], q0a[2]);
    wire signed [31:0] q0_axis_b = pick32(col_axis, q0b[0], q0b[1], q0b[2]);
    wire signed [31:0] q1_axis_a = pick32(col_axis, q1a[0], q1a[1], q1a[2]);
    wire signed [31:0] q1_axis_b = pick32(col_axis, q1b[0], q1b[1], q1b[2]);
    wire signed [31:0] p_lo_a = p_forward ? p0_axis_a : p1_axis_a;
    wire signed [31:0] p_lo_b = p_forward ? p0_axis_b : p1_axis_b;
    wire signed [31:0] p_hi_a = p_forward ? p1_axis_a : p0_axis_a;
    wire signed [31:0] p_hi_b = p_forward ? p1_axis_b : p0_axis_b;
    wire signed [31:0] q_lo_a = q_forward ? q0_axis_a : q1_axis_a;
    wire signed [31:0] q_lo_b = q_forward ? q0_axis_b : q1_axis_b;
    wire signed [31:0] q_hi_a = q_forward ? q1_axis_a : q0_axis_a;
    wire signed [31:0] q_hi_b = q_forward ? q1_axis_b : q0_axis_b;
    wire signed [32:0] col_ua = pick33(col_axis,ua[0],ua[1],ua[2]);
    wire signed [32:0] col_ub = pick33(col_axis,ub[0],ub[1],ub[2]);
    wire signed [32:0] col_va = pick33(col_axis,va[0],va[1],va[2]);
    wire signed [32:0] col_vb = pick33(col_axis,vb[0],vb[1],vb[2]);

    reg signed [71:0] sign_source_a, sign_source_b;
    always @* begin
        sign_source_a = 72'sd0;
        sign_source_b = 72'sd0;
        case (state)
            X_SIGN_D: begin sign_source_a=det_a; sign_source_b=det_b; end
            X_SIGN_S: begin sign_source_a=s_num_a; sign_source_b=s_num_b; end
            X_SIGN_DS: begin sign_source_a=det_a-s_num_a; sign_source_b=det_b-s_num_b; end
            X_SIGN_T: begin sign_source_a=t_num_a; sign_source_b=t_num_b; end
            X_SIGN_DT: begin sign_source_a=det_a-t_num_a; sign_source_b=det_b-t_num_b; end
            X_SIGN_PDIR: begin
                sign_source_a={{39{col_ua[32]}},col_ua};
                sign_source_b={{39{col_ub[32]}},col_ub};
            end
            X_SIGN_QDIR: begin
                sign_source_a={{39{col_va[32]}},col_va};
                sign_source_b={{39{col_vb[32]}},col_vb};
            end
            X_OVERLAP0: begin
                sign_source_a={{40{p_hi_a[31]}},p_hi_a}-{{40{q_lo_a[31]}},q_lo_a};
                sign_source_b={{40{p_hi_b[31]}},p_hi_b}-{{40{q_lo_b[31]}},q_lo_b};
            end
            X_OVERLAP1: begin
                sign_source_a={{40{q_hi_a[31]}},q_hi_a}-{{40{p_lo_a[31]}},p_lo_a};
                sign_source_b={{40{q_hi_b[31]}},q_hi_b}-{{40{p_lo_b[31]}},p_lo_b};
            end
            default: begin end
        endcase
    end

    function interval_ok;
        input [1:0] denominator_sign;
        input [1:0] numerator_sign;
        input [1:0] remainder_sign;
        begin
            if (denominator_sign == SG_POS)
                interval_ok = numerator_sign != SG_NEG && remainder_sign != SG_NEG;
            else
                interval_ok = numerator_sign != SG_POS && remainder_sign != SG_POS;
        end
    endfunction

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= X_IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            contact <= 1'b0;
            minor_index <= 2'd0;
            col_axis <= 2'd0;
            sign_in_a <= 72'sd0;
            sign_in_b <= 72'sd0;
            sign_op <= 4'd0;
        end else begin
            done <= 1'b0;
            case (state)
                X_IDLE: if (start) begin
                    p0a[0]<=p0_xa; p0b[0]<=p0_xb; p0a[1]<=p0_ya; p0b[1]<=p0_yb; p0a[2]<=p0_za; p0b[2]<=p0_zb;
                    p1a[0]<=p1_xa; p1b[0]<=p1_xb; p1a[1]<=p1_ya; p1b[1]<=p1_yb; p1a[2]<=p1_za; p1b[2]<=p1_zb;
                    q0a[0]<=q0_xa; q0b[0]<=q0_xb; q0a[1]<=q0_ya; q0b[1]<=q0_yb; q0a[2]<=q0_za; q0b[2]<=q0_zb;
                    q1a[0]<=q1_xa; q1b[0]<=q1_xb; q1a[1]<=q1_ya; q1b[1]<=q1_yb; q1a[2]<=q1_za; q1b[2]<=q1_zb;
                    ua[0]<={p1_xa[31],p1_xa}-{p0_xa[31],p0_xa}; ub[0]<={p1_xb[31],p1_xb}-{p0_xb[31],p0_xb};
                    ua[1]<={p1_ya[31],p1_ya}-{p0_ya[31],p0_ya}; ub[1]<={p1_yb[31],p1_yb}-{p0_yb[31],p0_yb};
                    ua[2]<={p1_za[31],p1_za}-{p0_za[31],p0_za}; ub[2]<={p1_zb[31],p1_zb}-{p0_zb[31],p0_zb};
                    va[0]<={q1_xa[31],q1_xa}-{q0_xa[31],q0_xa}; vb[0]<={q1_xb[31],q1_xb}-{q0_xb[31],q0_xb};
                    va[1]<={q1_ya[31],q1_ya}-{q0_ya[31],q0_ya}; vb[1]<={q1_yb[31],q1_yb}-{q0_yb[31],q0_yb};
                    va[2]<={q1_za[31],q1_za}-{q0_za[31],q0_za}; vb[2]<={q1_zb[31],q1_zb}-{q0_zb[31],q0_zb};
                    wa[0]<={q0_xa[31],q0_xa}-{p0_xa[31],p0_xa}; wb[0]<={q0_xb[31],q0_xb}-{p0_xb[31],p0_xb};
                    wa[1]<={q0_ya[31],q0_ya}-{p0_ya[31],p0_ya}; wb[1]<={q0_yb[31],q0_yb}-{p0_yb[31],p0_yb};
                    wa[2]<={q0_za[31],q0_za}-{p0_za[31],p0_za}; wb[2]<={q0_zb[31],q0_zb}-{p0_zb[31],p0_zb};
                    minor_index <= 2'd0;
                    contact <= 1'b0;
                    busy <= 1'b1;
                    state <= X_PREP;
                end
                X_PREP: state <= X_D0;
                X_D0: begin product0_a<=mul_out_a; product0_b<=mul_out_b; state<=X_D1; end
                X_D1: begin
                    candidate_hold_a<=candidate_a;
                    candidate_hold_b<=candidate_b;
                    candidate_op<=2'd0;
                    state<=X_CAND_EVAL;
                end
                X_S0: begin product0_a<=mul_out_a; product0_b<=mul_out_b; state<=X_S1; end
                X_S1: begin
                    candidate_hold_a<=candidate_a;
                    candidate_hold_b<=candidate_b;
                    candidate_op<=2'd1;
                    state<=X_CAND_EVAL;
                end
                X_T0: begin product0_a<=mul_out_a; product0_b<=mul_out_b; state<=X_T1; end
                X_T1: begin
                    t_num_a<=(product0_a-mul_out_a); t_num_b<=(product0_b-mul_out_b); state<=X_SIGN_D;
                end
                X_SIGN_D: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd0; state<=X_SIGN_EVAL; end
                X_SIGN_S: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd1; state<=X_SIGN_EVAL; end
                X_SIGN_DS: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd2; state<=X_SIGN_EVAL; end
                X_SIGN_T: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd3; state<=X_SIGN_EVAL; end
                X_SIGN_DT: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd4; state<=X_SIGN_EVAL; end
                X_EQ0: begin product0_a<=mul_out_a; product0_b<=mul_out_b; state<=X_EQ1; end
                X_EQ1: begin product1_a<=mul_out_a; product1_b<=mul_out_b; state<=X_EQ2; end
                X_EQ2: begin
                    candidate_hold_a <= product0_a-product1_a;
                    candidate_hold_b <= product0_b-product1_b;
                    product2_a <= mul_out_a;
                    product2_b <= mul_out_b;
                    state <= X_EQ_EVAL;
                end
                X_COL0: begin product0_a<=mul_out_a; product0_b<=mul_out_b; state<=X_COL1; end
                X_COL1: begin
                    candidate_hold_a<=candidate_a;
                    candidate_hold_b<=candidate_b;
                    candidate_op<=2'd2;
                    state<=X_CAND_EVAL;
                end
                X_CAND_EVAL: begin
                    case (candidate_op)
                        2'd0: begin
                            if (candidate_hold_a == 0 && candidate_hold_b == 0) begin
                                if (minor_index == 2'd2) begin minor_index<=2'd0; state<=X_COL0; end
                                else begin minor_index<=minor_index+1'b1; state<=X_D0; end
                            end else begin
                                det_a<=candidate_hold_a[71:0];
                                det_b<=candidate_hold_b[71:0];
                                state<=X_S0;
                            end
                        end
                        2'd1: begin
                            s_num_a<=candidate_hold_a[71:0];
                            s_num_b<=candidate_hold_b[71:0];
                            state<=X_T0;
                        end
                        default: begin
                            if (candidate_hold_a != 0 || candidate_hold_b != 0) begin
                                contact<=1'b0;
                                state<=X_DONE;
                            end else if (minor_index != 2'd2) begin
                                minor_index<=minor_index+1'b1;
                                state<=X_COL0;
                            end else begin
                                if ((ua[0] != 0) || (ub[0] != 0)) col_axis<=2'd0;
                                else if ((ua[1] != 0) || (ub[1] != 0)) col_axis<=2'd1;
                                else col_axis<=2'd2;
                                state<=X_SIGN_PDIR;
                            end
                        end
                    endcase
                end
                X_EQ_EVAL: begin
                    contact <= (candidate_hold_a == product2_a &&
                                candidate_hold_b == product2_b);
                    state <= X_DONE;
                end
                X_SIGN_PDIR: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd5; state<=X_SIGN_EVAL; end
                X_SIGN_QDIR: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd6; state<=X_SIGN_EVAL; end
                X_OVERLAP0: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd7; state<=X_SIGN_EVAL; end
                X_OVERLAP1: begin sign_in_a<=sign_source_a; sign_in_b<=sign_source_b; sign_op<=4'd8; state<=X_SIGN_EVAL; end
                X_SIGN_EVAL: begin
                    case (sign_op)
                        4'd0: begin sign_d<=sign_value; state<=X_SIGN_S; end
                        4'd1: begin sign_s<=sign_value; state<=X_SIGN_DS; end
                        4'd2: begin sign_ds<=sign_value; state<=X_SIGN_T; end
                        4'd3: begin sign_t<=sign_value; state<=X_SIGN_DT; end
                        4'd4: begin
                            if (!interval_ok(sign_d,sign_s,sign_ds) ||
                                !interval_ok(sign_d,sign_t,sign_value)) begin
                                contact<=1'b0; state<=X_DONE;
                            end else state<=X_EQ0;
                        end
                        4'd5: begin p_forward<=(sign_value != SG_NEG); state<=X_SIGN_QDIR; end
                        4'd6: begin q_forward<=(sign_value != SG_NEG); state<=X_OVERLAP0; end
                        4'd7: begin overlap0_ok<=(sign_value != SG_NEG); state<=X_OVERLAP1; end
                        default: begin contact<=overlap0_ok && (sign_value != SG_NEG); state<=X_DONE; end
                    endcase
                end
                X_DONE: begin done<=1'b1; busy<=1'b0; state<=X_IDLE; end
                default: begin contact<=1'b0; busy<=1'b0; state<=X_IDLE; end
            endcase
        end
    end
endmodule
