// spu13_su3_mult.v — 3×3 matrix multiply over A₃₁[i]
//
// Computes C = A × B where A, B, C are 3×3 matrices with elements
// in the degree-8 extension A₃₁[i] = F_p[u,v,x]/(u²-3, v²-5, x²+1).
//
// Algebra stack:
//   F_p         Mersenne prime M31 = 2^31-1          (base field)
//   A₃₁         F_p[u,v]/(u²-3, v²-5)                (~76 cycle inversion)
//   A₃₁[i]      A₃₁[x]/(x²+1)                        (~114 cycle inversion)
//
// Uses an external shared spu13_m31_multiplier via TDM (borrowed from the
// RPLU v2 pipeline when idle). Each complex A₃₁[i]
// multiply sequences 4 A₃₁ base products (RR, II, RI, IR) through the
// 2-stage M31 pipeline. Results stream out in row-major order as each
// C[i][j] accumulator completes.
//
// Interface: element-wise load (9 elements per matrix), start/done handshake.
// Element format: {imag[127:0], real[127:0]}
//   real[127:0] = {c3, c2, c1, c0} × 32-bit A₃₁ components
//   imag[127:0] = {c3, c2, c1, c0} × 32-bit A₃₁ components
//
// Verification:
//   Oracle:   software/tests/test_su3_oracle.py  (20 checks, all PASS)
//   Testbench: hardware/tests/spu13/spu13_su3_mult_tb.v  (5 public-output cases)
//
// References:
//   docs/SU3_EXTENSION_PLAN.md
//   Gell-Mann matrices: λ₁-λ₈ as SU(3) generators over A₃₁[i]
//
// CC0 1.0 Universal.

module spu13_su3_mult (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         start,

    // Element-wise matrix load
    input  wire         load_a,
    input  wire         load_b,
    input  wire [255:0] elem_data,
    output reg  [4:0]   elem_idx,

    // Result
    output reg          done,
    output reg          busy,
    output reg  [255:0] result_data,
    output reg          result_valid,
    output wire [3:0]   debug_state,

    // External shared M31 multiplier interface
    // Borrowed from RPLU v2 pipeline's u_mult_pade when pipeline is idle.
    output reg          m_start,
    output reg  [31:0]  ma0, ma1, ma2, ma3,
    output reg  [31:0]  mb0, mb1, mb2, mb3,
    input  wire [31:0]  mr0, mr1, mr2, mr3,
    input  wire         m_done,
    input  wire         m_busy
);

    // ── Element storage ───────────────────────────────────────
    reg [255:0] mat_a [0:8];
    reg [255:0] mat_b [0:8];
    // Extract A₃₁ components from storage
    wire [31:0] a_rc0 [0:8], a_rc1 [0:8], a_rc2 [0:8], a_rc3 [0:8];
    wire [31:0] a_ic0 [0:8], a_ic1 [0:8], a_ic2 [0:8], a_ic3 [0:8];
    wire [31:0] b_rc0 [0:8], b_rc1 [0:8], b_rc2 [0:8], b_rc3 [0:8];
    wire [31:0] b_ic0 [0:8], b_ic1 [0:8], b_ic2 [0:8], b_ic3 [0:8];
    genvar ge;
    generate
        for (ge = 0; ge < 9; ge = ge + 1) begin : gen_elem
            assign a_rc0[ge] = mat_a[ge][31:0];
            assign a_rc1[ge] = mat_a[ge][63:32];
            assign a_rc2[ge] = mat_a[ge][95:64];
            assign a_rc3[ge] = mat_a[ge][127:96];
            assign a_ic0[ge] = mat_a[ge][159:128];
            assign a_ic1[ge] = mat_a[ge][191:160];
            assign a_ic2[ge] = mat_a[ge][223:192];
            assign a_ic3[ge] = mat_a[ge][255:224];
            assign b_rc0[ge] = mat_b[ge][31:0];
            assign b_rc1[ge] = mat_b[ge][63:32];
            assign b_rc2[ge] = mat_b[ge][95:64];
            assign b_rc3[ge] = mat_b[ge][127:96];
            assign b_ic0[ge] = mat_b[ge][159:128];
            assign b_ic1[ge] = mat_b[ge][191:160];
            assign b_ic2[ge] = mat_b[ge][223:192];
            assign b_ic3[ge] = mat_b[ge][255:224];
        end
    endgenerate

    // ── External M31 multiplier interface (shared) ─────────────
    // The multiplier is provided by the RPLU v2 pipeline.
    // SU(3) drives m_start/ma/mb; reads mr/m_done.
    // The mux lives in the top-level integration (spu_a7_top.v).

    // ── M31 add/sub helpers (combinational) ───────────────────
    function [31:0] m31_add;
        input [31:0] x, y;
        reg [31:0] s;
        begin
            s = x + y;
            if (s >= 32'h7FFFFFFF) s = s - 32'h7FFFFFFF;
            m31_add = s;
        end
    endfunction

    function [31:0] m31_sub;
        input [31:0] x, y;
        reg [31:0] t;
        begin
            t = x - y;
            if (x < y) t = t + 32'h7FFFFFFF;
            m31_sub = t;
        end
    endfunction

    // ── Compute FSM ───────────────────────────────────────────
    localparam S_IDLE      = 0;
    localparam S_LOAD_A    = 1;
    localparam S_LOAD_B    = 2;
    localparam S_LATCH     = 3;  // latch A[i][k] and B[k][j]
    localparam S_MULT_RR   = 4;  // real·real running
    localparam S_MULT_II   = 5;  // imag·imag running
    localparam S_MULT_RI   = 6;  // real·imag running
    localparam S_MULT_IR   = 7;  // imag·real running
    localparam S_ACCUM     = 8;  // add term to accumulator
    localparam S_ADVANCE   = 9;  // advance k/j/i
    reg [3:0] state;

    assign debug_state = state;

    reg [1:0] ci, cj, ck;
    reg [4:0] load_idx;

    // Latched operands
    reg [31:0] l_rc0, l_rc1, l_rc2, l_rc3;
    reg [31:0] l_ic0, l_ic1, l_ic2, l_ic3;

    // Pipeline registers for M31 multiplier results
    reg [31:0] rr0, rr1, rr2, rr3;   // real·real
    reg [31:0] ii0, ii1, ii2, ii3;   // imag·imag
    reg [31:0] ri0, ri1, ri2, ri3;   // real·imag
    reg [31:0] ir0, ir1, ir2, ir3;   // imag·real

    // Accumulators: real and imag parts of C[i][j]
    reg [31:0] ar0, ar1, ar2, ar3;
    reg [31:0] ai0, ai1, ai2, ai3;

    // Addresses within row-major storage
    // Note: ci*3+ck ≠ {ci,ck} for non-power-of-2 dimensions!
    wire [4:0] aik_idx = ci*3 + ck;
    wire [4:0] bkj_idx = ck*3 + cj;
    wire [4:0] cij_idx = ci*3 + cj;

    // ── Main FSM ──────────────────────────────────────────────
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            m_start <= 1'b0;
            result_valid <= 1'b0;
            result_data <= 256'd0;
            elem_idx <= 5'd0;
            load_idx <= 5'd0;
            ci <= 2'd0; cj <= 2'd0; ck <= 2'd0;
            ar0 <= 32'd0; ar1 <= 32'd0; ar2 <= 32'd0; ar3 <= 32'd0;
            ai0 <= 32'd0; ai1 <= 32'd0; ai2 <= 32'd0; ai3 <= 32'd0;
        end else begin
            result_valid <= 1'b0;
            done <= 1'b0;
            m_start <= 1'b0;

            case (state)
                S_IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        load_idx <= 5'd0;
                        busy <= 1'b1;
                        state <= S_LOAD_A;
                    end
                end

                S_LOAD_A: begin
                    if (load_a) begin
                        mat_a[load_idx] <= elem_data;
                        if (load_idx == 5'd8) begin
                            load_idx <= 5'd0;
                            state <= S_LOAD_B;
                        end else begin
                            load_idx <= load_idx + 5'd1;
                        end
                    end
                    elem_idx <= load_idx;
                end

                S_LOAD_B: begin
                    if (load_b) begin
                        mat_b[load_idx] <= elem_data;
                        if (load_idx == 5'd8) begin
                            ci <= 2'd0; cj <= 2'd0; ck <= 2'd0;
                            ar0 <= 32'd0; ar1 <= 32'd0; ar2 <= 32'd0; ar3 <= 32'd0;
                            ai0 <= 32'd0; ai1 <= 32'd0; ai2 <= 32'd0; ai3 <= 32'd0;
                            state <= S_LATCH;
                        end else begin
                            load_idx <= load_idx + 5'd1;
                        end
                    end
                    elem_idx <= load_idx;
                end

                // ── Compute one term: C[i][j] += A[i][k] · B[k][j] ──
                // Complex A₃₁[i] multiply needs 4 A₃₁ base products:
                //   0: RR = real(A) · real(B)   → stored in rr*
                //   1: II = imag(A) · imag(B)   → stored in ii*
                //   2: RI = real(A) · imag(B)   → stored in ri*
                //   3: IR = imag(A) · real(B)   → stored in ir*
                // Accumulate:
                //   ar += RR - II
                //   ai += RI + IR

                S_LATCH: begin
                    l_rc0 <= a_rc0[aik_idx]; l_rc1 <= a_rc1[aik_idx];
                    l_rc2 <= a_rc2[aik_idx]; l_rc3 <= a_rc3[aik_idx];
                    l_ic0 <= a_ic0[aik_idx]; l_ic1 <= a_ic1[aik_idx];
                    l_ic2 <= a_ic2[aik_idx]; l_ic3 <= a_ic3[aik_idx];
                    // Start RR = real(A) · real(B)
                    ma0 <= a_rc0[aik_idx]; ma1 <= a_rc1[aik_idx];
                    ma2 <= a_rc2[aik_idx]; ma3 <= a_rc3[aik_idx];
                    mb0 <= b_rc0[bkj_idx]; mb1 <= b_rc1[bkj_idx];
                    mb2 <= b_rc2[bkj_idx]; mb3 <= b_rc3[bkj_idx];
                    m_start <= 1'b1;
                    state <= S_MULT_RR;
                end

                S_MULT_RR: begin
                    if (m_done) begin
                        rr0 <= mr0; rr1 <= mr1; rr2 <= mr2; rr3 <= mr3;
                        ma0 <= l_ic0; ma1 <= l_ic1; ma2 <= l_ic2; ma3 <= l_ic3;
                        mb0 <= b_ic0[bkj_idx]; mb1 <= b_ic1[bkj_idx];
                        mb2 <= b_ic2[bkj_idx]; mb3 <= b_ic3[bkj_idx];
                        m_start <= 1'b1;
                        state <= S_MULT_II;
                    end
                end

                S_MULT_II: begin
                    if (m_done) begin
                        ii0 <= mr0; ii1 <= mr1; ii2 <= mr2; ii3 <= mr3;
                        ma0 <= l_rc0; ma1 <= l_rc1; ma2 <= l_rc2; ma3 <= l_rc3;
                        mb0 <= b_ic0[bkj_idx]; mb1 <= b_ic1[bkj_idx];
                        mb2 <= b_ic2[bkj_idx]; mb3 <= b_ic3[bkj_idx];
                        m_start <= 1'b1;
                        state <= S_MULT_RI;
                    end
                end

                S_MULT_RI: begin
                    if (m_done) begin
                        ri0 <= mr0; ri1 <= mr1; ri2 <= mr2; ri3 <= mr3;
                        ma0 <= l_ic0; ma1 <= l_ic1; ma2 <= l_ic2; ma3 <= l_ic3;
                        mb0 <= b_rc0[bkj_idx]; mb1 <= b_rc1[bkj_idx];
                        mb2 <= b_rc2[bkj_idx]; mb3 <= b_rc3[bkj_idx];
                        m_start <= 1'b1;
                        state <= S_MULT_IR;
                    end
                end

                S_MULT_IR: begin
                    if (m_done) begin
                        ir0 <= mr0; ir1 <= mr1; ir2 <= mr2; ir3 <= mr3;
                        state <= S_ACCUM;
                    end
                end

                S_ACCUM: begin
                    // ar += RR - II  (element-wise A₃₁ subtraction and add)
                    ar0 <= m31_add(ar0, m31_sub(rr0, ii0));
                    ar1 <= m31_add(ar1, m31_sub(rr1, ii1));
                    ar2 <= m31_add(ar2, m31_sub(rr2, ii2));
                    ar3 <= m31_add(ar3, m31_sub(rr3, ii3));
                    // ai += RI + IR
                    ai0 <= m31_add(ai0, m31_add(ri0, ir0));
                    ai1 <= m31_add(ai1, m31_add(ri1, ir1));
                    ai2 <= m31_add(ai2, m31_add(ri2, ir2));
                    ai3 <= m31_add(ai3, m31_add(ri3, ir3));
                    state <= S_ADVANCE;
                end

                S_ADVANCE: begin
                    if (ck == 2'd2) begin
                        // All k accumulated for C[i][j]. Emit immediately.
                        result_data <= {ai3, ai2, ai1, ai0, ar3, ar2, ar1, ar0};
                        result_valid <= 1'b1;
                        elem_idx <= cij_idx;
                        ck <= 2'd0;
                        // Reset accumulators for next element
                        ar0 <= 32'd0; ar1 <= 32'd0;
                        ar2 <= 32'd0; ar3 <= 32'd0;
                        ai0 <= 32'd0; ai1 <= 32'd0;
                        ai2 <= 32'd0; ai3 <= 32'd0;
                        if (cj == 2'd2) begin
                            cj <= 2'd0;
                            if (ci == 2'd2) begin
                                ci <= 2'd0;
                                load_idx <= 5'd0;
                                done <= 1'b1;
                                busy <= 1'b0;
                                state <= S_IDLE;
                            end else begin
                                ci <= ci + 2'd1;
                                state <= S_LATCH;
                            end
                        end else begin
                            cj <= cj + 2'd1;
                            state <= S_LATCH;
                        end
                    end else begin
                        ck <= ck + 2'd1;
                        state <= S_LATCH;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
