// spu13_composition_policy.v
//
// Composition policy: accept / hold / escalate.
//
// Normative reference: docs/SERVICE_COMPOSITION_POLICY.md §3.
// Software oracle:     software/lib/composition_policy.py
// This module must match that oracle bit-exactly, in the same relationship
// spu13_a31_* bears to software/lib/a31_field.py.
//
// The policy is a pure function of SOM1 status flags, the classifier error
// code, and one algebra verdict symbol. It is deliberately combinational and
// branch-free: the whole decision is a MUX polynomial over five predicates,
// so it adds no cycles to the decision path and cannot stall it.
//
// It introduces NO threshold of its own. Ambiguity is SOM1 flag bit 3 -- the
// classifier's own determination, already proven in silicon -- so "thresholds
// fixed in RTL" costs nothing to re-prove here: there is no new constant.
//
// Quadrances are not read. The policy never compares Q(sqrt(3)) values, so no
// cross-domain numeric conversion occurs anywhere in this module. Verdicts
// compose; values do not (policy §1).

`default_nettype none

module spu13_composition_policy (
    input  wire [7:0] som1_flags,   // bit0 valid, 1 busy, 2 has_second,
                                    // bit3 ambiguous, bit4 map_valid
    input  wire [7:0] som1_error,   // classifier error code, 0 = none
    input  wire [1:0] verdict,      // 00 concur, 01 dissent, 10 unavailable
    output wire [1:0] outcome,      // 00 accept, 01 hold,   10 escalate
    output wire [2:0] reason        // see REASON_* below
);

    // Verdict encoding -- must match Verdict in the oracle.
    localparam [1:0] V_CONCUR      = 2'b00;
    localparam [1:0] V_DISSENT     = 2'b01;
    localparam [1:0] V_UNAVAILABLE = 2'b10;

    // Outcome encoding -- must match Outcome in the oracle.
    localparam [1:0] O_ACCEPT   = 2'b00;
    localparam [1:0] O_HOLD     = 2'b01;
    localparam [1:0] O_ESCALATE = 2'b10;

    // Reason codes. Not decorative: the silicon composition trace records
    // why an outcome was reached, and a bare outcome cannot distinguish
    // "classifier said ambiguous" from "algebra dissented" after the fact.
    localparam [2:0] REASON_CONCUR      = 3'd0;
    localparam [2:0] REASON_DISSENT     = 3'd1;
    localparam [2:0] REASON_UNAVAILABLE = 3'd2;
    localparam [2:0] REASON_NOT_VALID   = 3'd3;
    localparam [2:0] REASON_ERROR       = 3'd4;
    localparam [2:0] REASON_NO_MAP      = 3'd5;
    localparam [2:0] REASON_BUSY        = 3'd6;
    localparam [2:0] REASON_AMBIGUOUS   = 3'd7;

    wire valid     = som1_flags[0];
    wire busy      = som1_flags[1];
    wire ambiguous = som1_flags[3];
    wire map_valid = som1_flags[4];
    wire has_error = |som1_error;

    // Escalation is decided before the algebra is consulted at all: if the
    // decision service produced no usable evidence, a coherence predicate
    // cannot supply it. PHSLK has no ordering to give, so it cannot break a
    // tie the classifier has already declared (policy §2).
    wire escalate = (~valid) | has_error | (~map_valid) | busy | ambiguous;

    wire concurs  = (verdict == V_CONCUR);

    assign outcome = escalate ? O_ESCALATE :
                     concurs  ? O_ACCEPT   : O_HOLD;

    // Priority matches the oracle's evaluation order exactly, so that a
    // frame failing several predicates reports the same reason in both.
    assign reason =
        (~valid)    ? REASON_NOT_VALID   :
        has_error   ? REASON_ERROR       :
        (~map_valid)? REASON_NO_MAP      :
        busy        ? REASON_BUSY        :
        ambiguous   ? REASON_AMBIGUOUS   :
        (verdict == V_UNAVAILABLE) ? REASON_UNAVAILABLE :
        (verdict == V_DISSENT)     ? REASON_DISSENT     :
                                     REASON_CONCUR;

endmodule

`default_nettype wire
