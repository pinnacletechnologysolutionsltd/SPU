// spu13_typestate_guard.v — φ-plane typestate lattice guard (paper comparison)
//
// Implements the 4-state join-semilattice from THEOREM_LICENSED_TYPESTATE.md §4:
//   UNTAGGED(00) ← FRESH(01) → MAIN(10)/CONJ(11)
//   UNTAGGED absorbs everything.
//   FRESH ⊑ MAIN, FRESH ⊑ CONJ.
//   MAIN ⋢ CONJ, CONJ ⋢ MAIN.
//
// This is the "typestate" arm of the SVA head-to-head comparison (§7).
// Synthesised area is measured against spu13_sva_guard.v.
//
// Copyright 2026 John Curley. Licensed under CERN-OHL-W-2.0.

module spu13_typestate_guard (
    input  wire        clk, rst_n, ce,
    input  wire        op_valid,        // pulse: new operation
    input  wire [2:0]  op_code,         // 0=SCALE2 1=IROTC_MAIN 2=IROTC_CONJ 3=QADD
    input  wire [1:0]  op_tag_a,        // operand A tag
    input  wire [1:0]  op_tag_b,        // operand B tag (QADD only)
    output reg  [1:0]  result_tag,      // computed destination tag
    output reg         fault,            // latched fault
    output reg  [1:0]  fault_code        // 0=none 1=UNTAGGED 2=CATMIX 3=BAD_OP
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

    // ── Lattice join operator ─────────────────────────────────────
    // Returns the least upper bound of two tags.
    //   FRESH ⊔ anything = anything   (FRESH ≤ MAIN, FRESH ≤ CONJ)
    //   MAIN ⊔ MAIN = MAIN
    //   CONJ ⊔ CONJ = CONJ
    //   MAIN ⊔ CONJ = UNTAGGED        (CATMIX — no upper bound in the lattice)
    //   UNTAGGED ⊔ anything = UNTAGGED
    function [1:0] tag_join;
        input [1:0] x, y;
        begin
            if (x == TAG_UNTAGGED || y == TAG_UNTAGGED)
                tag_join = TAG_UNTAGGED;
            else if (x == TAG_FRESH)
                tag_join = y;
            else if (y == TAG_FRESH)
                tag_join = x;
            else if (x == y)
                tag_join = x;
            else
                tag_join = TAG_UNTAGGED;  // MAIN ⊔ CONJ → UNTAGGED
        end
    endfunction

    wire [1:0] join_ab = tag_join(op_tag_a, op_tag_b);

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
                    if (op_tag_a == TAG_UNTAGGED) begin
                        fault <= 1'b1;
                        fault_code <= FAULT_UNTAGGED;
                    end else if (op_tag_a == TAG_CONJ) begin
                        fault <= 1'b1;
                        fault_code <= FAULT_CATMIX;
                    end else begin
                        result_tag <= TAG_MAIN;
                    end
                end

                OP_IROTC_CONJ: begin
                    if (op_tag_a == TAG_UNTAGGED) begin
                        fault <= 1'b1;
                        fault_code <= FAULT_UNTAGGED;
                    end else if (op_tag_a == TAG_MAIN) begin
                        fault <= 1'b1;
                        fault_code <= FAULT_CATMIX;
                    end else begin
                        result_tag <= TAG_CONJ;
                    end
                end

                OP_QADD: begin
                    // Spec §3 semantics: linear ops never fault — the sum
                    // is computed and the tag silently demotes via the
                    // lattice join (MAIN ⊔ CONJ or any UNTAGGED → ⊥).
                    // Only IROTC dispatch refuses. This is the load-bearing
                    // asymmetry: demotion is safe (a license is lost),
                    // refusal is reserved for the op whose >>>1 the
                    // license justifies.
                    result_tag <= join_ab;
                end

                default: begin
                    fault <= 1'b1;
                    fault_code <= FAULT_BAD_OP;
                end
            endcase
        end
    end

endmodule
