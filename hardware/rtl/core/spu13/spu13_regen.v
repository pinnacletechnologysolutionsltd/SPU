// spu13_regen.v — REGEN boundary, Stages A+B (contract_regen_stageA/B)
//
// Stage A (pass-through): block accounting (declared K vs E_REGEN count),
// REGEN_PREC faulting, idempotence REGEN(REGEN(S)) = S.
// Stage B (fixed-point datapath): the measurement interface (bk_meas*,
// bk_sigma_exp, bk_angle_k from fpga_chain) is consumed with the real
// compensation trim (Taylor 1/cos(K*dphi), precision bound by the frozen
// experiment #2 requirement) and the BQE (2^m shift + round, since the
// chain is 2-normalized). The recovered QR0/QR1 state is committed whole.
//
// regen_debug_status is NON-ARCHITECTURAL telemetry; software must not
// depend on it for program semantics.
module spu13_regen (
    input  wire        clk,
    input  wire        rst_n,

    // instruction interface (from core dispatch)
    input  wire        start,        // REGEN accepted
    input  wire [15:0] declared_k,   // P1_A: compile-time .block K (metadata)
    input  wire        eligible_op,  // pulse per E_REGEN op executed
    input  wire        bk_valid,     // backend measurement valid

    // measurement interface (Stage B; driven by fpga_chain in the core)
    input  wire [41:0] bk_qr0_meas_a, bk_qr0_meas_b, bk_qr0_meas_c, bk_qr0_meas_d,
    input  wire [41:0] bk_qr1_meas_a, bk_qr1_meas_b, bk_qr1_meas_c, bk_qr1_meas_d,
    input  wire [9:0]  bk_sigma_exp0,
    input  wire [9:0]  bk_sigma_exp1,
    input  wire [15:0] bk_angle_k,

    // recovered whole-state commit (Stage B)
    output reg  [31:0] rec_qr0_a, rec_qr0_b, rec_qr0_c, rec_qr0_d,
    output reg  [31:0] rec_qr1_a, rec_qr1_b, rec_qr1_c, rec_qr1_d,
    output reg         commit_valid,

    // status
    output reg         done,             // REGEN completed (one-cycle pulse)
    output reg         regen_prec_fault, // block-count mismatch / out-of-envelope
    output reg  [15:0] block_op_count,   // live count (non-architectural)
    output reg  [15:0] regen_debug_status
);
    localparam S_IDLE = 1'b0;
    localparam S_DONE = 1'b1;

    reg        state;
    reg        k_mismatch;
    reg        count_active;
    reg        k_valid;
    reg        busy;

    // Split into spu13_regen_arith.vh for the 150-line Lithic cap (AGENTS.md).
    `include "spu13_regen_arith.vh"

    wire [41:0] trimv = trim_const(bk_angle_k);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state            <= S_IDLE;
            done             <= 0;
            regen_prec_fault <= 0;
            block_op_count   <= 16'd0;
            k_mismatch       <= 0;
            count_active     <= 0;
            k_valid          <= 0;
            busy             <= 0;
            commit_valid     <= 0;
            rec_qr0_a <= 0; rec_qr0_b <= 0; rec_qr0_c <= 0; rec_qr0_d <= 0;
            rec_qr1_a <= 0; rec_qr1_b <= 0; rec_qr1_c <= 0; rec_qr1_d <= 0;
        end else begin
            done <= 0;
            case (state)
                S_IDLE: begin
                    if (start) begin
                        busy       <= 1;
                        k_valid    <= 1;
                        k_mismatch <= (block_op_count != declared_k);
                        commit_valid <= 0;   // default: no commit unless the
                                             // K>0 valid path overrides below
                        if (!bk_valid) begin
                            regen_prec_fault <= 1;
                            state <= S_DONE;
                        end else if (block_op_count == declared_k) begin
                            regen_prec_fault <= 0;
                            if (declared_k == 0) begin
                                // empty-block pass-through (idempotence):
                                // REGEN(REGEN(S)) == S — no measurement exists
                                // for an empty chain, so the exact state in
                                // the QR file is preserved (no commit)
                                commit_valid <= 0;
                            end else begin
                                // Stage-B recovery: BQE each measured component
                                rec_qr0_a <= bqe(bk_qr0_meas_a, trimv, bk_sigma_exp0);
                                rec_qr0_b <= bqe(bk_qr0_meas_b, trimv, bk_sigma_exp0);
                                rec_qr0_c <= bqe(bk_qr0_meas_c, trimv, bk_sigma_exp0);
                                rec_qr0_d <= bqe(bk_qr0_meas_d, trimv, bk_sigma_exp0);
                                rec_qr1_a <= bqe(bk_qr1_meas_a, trimv, bk_sigma_exp1);
                                rec_qr1_b <= bqe(bk_qr1_meas_b, trimv, bk_sigma_exp1);
                                rec_qr1_c <= bqe(bk_qr1_meas_c, trimv, bk_sigma_exp1);
                                rec_qr1_d <= bqe(bk_qr1_meas_d, trimv, bk_sigma_exp1);
                                commit_valid <= 1;
                            end
                            block_op_count <= 16'd0;
                            count_active   <= 0;
                            state <= S_DONE;
                        end else begin
                            regen_prec_fault <= 1;
                            state <= S_DONE;
                        end
                    end else if (eligible_op) begin
                        block_op_count <= block_op_count + 16'd1;
                        count_active   <= 1;
                    end
                end
                S_DONE: begin
                    busy <= 0;
                    done <= 1;
                    state <= S_IDLE;
                end
            endcase
        end
    end

    // Non-architectural telemetry layout (contract §3):
    // [11] done, [10] busy, [9] REGEN_PREC fault, [8] K mismatch,
    // [7:2] block count, [1] K valid, [0] block active.
    assign regen_debug_status = {
        4'd0,
        done,
        busy,
        regen_prec_fault,
        k_mismatch,
        block_op_count[5:0],
        k_valid,
        count_active
    };
endmodule
