// spu13_sva_guard.v — boolean-flag guard (SVA-equivalent comparison module)
//
// Implements the same functional guards as spu13_typestate_guard.v but using
// independent boolean flags instead of a join-semilattice.  This is the
// "SVA" arm of the head-to-head comparison (§7 of THEOREM_LICENSED_TYPESTATE.md).
//
// Key differences from the typestate version:
//   1. Four independent boolean flags (not a lattice)
//   2. Mutual-exclusion enforced by assertion-style checks, not by structure
//   3. Cross-register consistency is ad-hoc per-opcode checks (no join operator)
//   4. Fault detection requires enumerating forbidden flag combinations
//
// Copyright 2026 John Curley. Licensed under CERN-OHL-W-2.0.

module spu13_sva_guard (
    input  wire        clk, rst_n, ce,
    input  wire        op_valid,
    input  wire [2:0]  op_code,
    input  wire [1:0]  op_tag_a,
    input  wire [1:0]  op_tag_b,
    output reg  [1:0]  result_tag,
    output reg         fault,
    output reg  [1:0]  fault_code
);

    localparam [1:0] TAG_UNTAGGED = 2'b00;
    localparam [1:0] TAG_FRESH    = 2'b01;
    localparam [1:0] TAG_MAIN     = 2'b10;
    localparam [1:0] TAG_CONJ     = 2'b11;

    localparam [1:0] OP_SCALE2     = 2'd0;
    localparam [1:0] OP_IROTC_MAIN = 2'd1;
    localparam [1:0] OP_IROTC_CONJ = 2'd2;
    localparam [1:0] OP_QADD       = 2'd3;

    localparam [1:0] FAULT_NONE     = 2'd0;
    localparam [1:0] FAULT_UNTAGGED = 2'd1;
    localparam [1:0] FAULT_CATMIX   = 2'd2;
    localparam [1:0] FAULT_BAD_OP   = 2'd3;

    // ── Boolean flags (one-hot encoding enforced by assertions) ───
    wire is_untagged_a = (op_tag_a == TAG_UNTAGGED);
    wire is_fresh_a    = (op_tag_a == TAG_FRESH);
    wire is_main_a     = (op_tag_a == TAG_MAIN);
    wire is_conj_a     = (op_tag_a == TAG_CONJ);

    wire is_untagged_b = (op_tag_b == TAG_UNTAGGED);
    wire is_fresh_b    = (op_tag_b == TAG_FRESH);
    wire is_main_b     = (op_tag_b == TAG_MAIN);
    wire is_conj_b     = (op_tag_b == TAG_CONJ);

    // Assertion-style: exactly one flag set per register (mutual exclusion).
    // These are synthesis no-ops but represent what SVA would check at runtime.
    wire sva_onehot_a = (is_untagged_a ^ is_fresh_a ^ is_main_a ^ is_conj_a)
                        && !(is_untagged_a && is_fresh_a)
                        && !(is_untagged_a && is_main_a)
                        && !(is_untagged_a && is_conj_a)
                        && !(is_fresh_a && is_main_a)
                        && !(is_fresh_a && is_conj_a)
                        && !(is_main_a && is_conj_a);
    wire sva_onehot_b = (is_untagged_b ^ is_fresh_b ^ is_main_b ^ is_conj_b)
                        && !(is_untagged_b && is_fresh_b)
                        && !(is_untagged_b && is_main_b)
                        && !(is_untagged_b && is_conj_b)
                        && !(is_fresh_b && is_main_b)
                        && !(is_fresh_b && is_conj_b)
                        && !(is_main_b && is_conj_b);

    // ── Ad-hoc transition guards ──────────────────────────────────
    // Each guard must enumerate all forbidden cases individually,
    // because there is no lattice structure to exploit.

    // IROTC_MAIN guard: forbid UNTAGGED and CONJ sources
    wire guard_main_untagged = is_untagged_a;
    wire guard_main_conj     = is_conj_a;
    wire guard_main_ok       = is_fresh_a || is_main_a;

    // IROTC_CONJ guard: forbid UNTAGGED and MAIN sources
    wire guard_conj_untagged = is_untagged_a;
    wire guard_conj_main     = is_main_a;
    wire guard_conj_ok       = is_fresh_a || is_conj_a;

    // QADD demotion conditions (spec §3: linear ops never fault — the
    // tag silently demotes; each condition enumerated by hand because
    // there is no lattice structure to exploit)
    wire guard_qadd_either_untagged = is_untagged_a || is_untagged_b;
    wire guard_qadd_catmix = (is_main_a && is_conj_b) || (is_conj_a && is_main_b);
    wire guard_qadd_ok = !guard_qadd_either_untagged && !guard_qadd_catmix;

    // QADD result tag (ad-hoc, no join operator — same logic duplicated)
    wire [1:0] qadd_result =
        guard_qadd_either_untagged ? TAG_UNTAGGED :
        guard_qadd_catmix          ? TAG_UNTAGGED :
        is_fresh_a                 ? op_tag_b :
        is_fresh_b                 ? op_tag_a :
        (op_tag_a == op_tag_b)     ? op_tag_a :
        TAG_UNTAGGED;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result_tag <= TAG_UNTAGGED;
            fault <= 1'b0;
            fault_code <= FAULT_NONE;
        end else if (!ce) begin
            fault <= 1'b0;
        end else if (op_valid && !fault) begin
            case (op_code)
                OP_SCALE2: begin
                    result_tag <= TAG_FRESH;
                end

                OP_IROTC_MAIN: begin
                    if (guard_main_untagged) begin
                        fault <= 1'b1;
                        fault_code <= FAULT_UNTAGGED;
                    end else if (guard_main_conj) begin
                        fault <= 1'b1;
                        fault_code <= FAULT_CATMIX;
                    end else begin
                        result_tag <= TAG_MAIN;
                    end
                end

                OP_IROTC_CONJ: begin
                    if (guard_conj_untagged) begin
                        fault <= 1'b1;
                        fault_code <= FAULT_UNTAGGED;
                    end else if (guard_conj_main) begin
                        fault <= 1'b1;
                        fault_code <= FAULT_CATMIX;
                    end else begin
                        result_tag <= TAG_CONJ;
                    end
                end

                OP_QADD: begin
                    // Spec §3: linear ops demote, never fault — refusal
                    // is reserved for IROTC dispatch.
                    result_tag <= qadd_result;
                end

                default: begin
                    fault <= 1'b1;
                    fault_code <= FAULT_BAD_OP;
                end
            endcase
        end
    end

endmodule
