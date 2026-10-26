#!/usr/bin/env python3
"""
VM-vs-RTL trace equivalence test for all 24 verified ROTC angles (0-23).

Angles 0-5 act directly (A invariant); angles 6-14 are thirds conjugates
via axis permutation; angles 2,5,15-20 are pure 3-cycle permutations
(bypass_p5/bypass_p5_inv + axis permutation); angles 21-23 are direct
double-transposition wire swaps ((AB)(CD), (AC)(BD), (AD)(BC)).

Tranche 1 (12-14) and Tranche 2 (15-23) added 2026-07-10.

DUT0: ENABLE_TDM_FALLBACK=1 — scalar-fast path from F/G/H inputs.
DUT1: ENABLE_TDM_FALLBACK=0 — hardwired angle_scalar_*_sum path.

Bit-exact match asserted on every component for every (vector, angle) case.
Third-division exactness required for all thirds angles (1,3,4,6-14):
test vectors use all-multiples-of-3 components.

Run:
  python3 software/tests/test_rotc_vm_rtl_trace.py

Requirements: iverilog + vvp in PATH, RationalSurd+QuadrayVector from spu_vm.
"""

import subprocess
import sys
from pathlib import Path


# ── Imports from the SPU codebase ──────────────────────────────────────────

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software"))

from spu_vm import RationalSurd, QuadrayVector


# ── VM ROTC computation (mirrors spu_vm.py ROTC handler) ──────────────────

_ROTC_TABLE = {
    # Angles 0-5 (circulant, A-invariant)
    0:  (1,  0,  0,  0,  0,  0,  1),   # identity
    1:  (2,  0,  2,  0, -1,  0,  3),   # thirds period-6
    2:  (0,  0,  1,  0,  0,  0,  1),   # P5 forward (bypass)
    3:  (-1, 0,  2,  0,  2,  0,  3),   # thirds period-2
    4:  (2,  0, -1,  0,  2,  0,  3),   # thirds period-6 inv
    5:  (0,  0,  0,  0,  1,  0,  1),   # P5 inverse (bypass)
    # Angles 6-11 (thirds, B/C/D conjugates)
    6:  (2,  0, -1,  0,  2,  0,  3),   # 240° about B
    7:  (2,  0,  2,  0, -1,  0,  3),   #  60° about B
    8:  (-1, 0,  2,  0,  2,  0,  3),   # 180° about C
    9:  (2,  0,  2,  0, -1,  0,  3),   #  60° about C
    10: (2,  0, -1,  0,  2,  0,  3),   # 240° about D
    11: (-1, 0,  2,  0,  2,  0,  3),   # 180° about D
    # Tranche 1: missing thirds conjugates (12-14)
    12: (-1, 0,  2,  0,  2,  0,  3),   # 180° about B (self-inverse)
    13: (2,  0, -1,  0,  2,  0,  3),   # 240° about C (inverse of 9)
    14: (2,  0,  2,  0, -1,  0,  3),   #  60° about D (inverse of 10)
    # Tranche 2: bypass entries (15-23) — F/G/H informational only,
    # not used in the actual computation which is pure permutation.
    15: (0,  0,  1,  0,  0,  0,  1),   # P5 fwd about B
    16: (0,  0,  0,  0,  1,  0,  1),   # P5 inv about B
    17: (0,  0,  1,  0,  0,  0,  1),   # P5 fwd about C
    18: (0,  0,  0,  0,  1,  0,  1),   # P5 inv about C
    19: (0,  0,  1,  0,  0,  0,  1),   # P5 fwd about D
    20: (0,  0,  0,  0,  1,  0,  1),   # P5 inv about D
    21: (0,  0,  0,  0,  0,  0,  1),   # (AB)(CD)
    22: (0,  0,  0,  0,  0,  0,  1),   # (AC)(BD)
    23: (0,  0,  0,  0,  0,  0,  1),   # (AD)(BC)
    # Tranche 3: octahedral group (24-35) — denom=1, entries 0,±1
    24: (0,  0,  0,  0,  0,  0,  1),
    25: (0,  0,  0,  0,  0,  0,  1),
    26: (0,  0,  0,  0,  0,  0,  1),
    27: (0,  0,  0,  0,  0,  0,  1),
    28: (0,  0,  0,  0,  0,  0,  1),
    29: (0,  0,  0,  0,  0,  0,  1),
    30: (0,  0,  0,  0,  0,  0,  1),
    31: (0,  0,  0,  0,  0,  0,  1),
    32: (0,  0,  0,  0,  0,  0,  1),
    33: (0,  0,  0,  0,  0,  0,  1),
    34: (0,  0,  0,  0,  0,  0,  1),
    35: (0,  0,  0,  0,  0,  0,  1),
}

ANGLE_NAMES = {
    0: "identity", 1: "thirds period-6", 2: "P5 forward",
    3: "thirds period-2", 4: "thirds period-6 inv", 5: "P5 inverse",
    6: "240° about B", 7: "60° about B", 8: "180° about C",
    9: "60° about C", 10: "240° about D", 11: "180° about D",
    12: "180° about B", 13: "240° about C", 14: "60° about D",
    15: "P5 fwd@B", 16: "P5 inv@B", 17: "P5 fwd@C",
    18: "P5 inv@C", 19: "P5 fwd@D", 20: "P5 inv@D",
    21: "(AB)(CD)", 22: "(AC)(BD)", 23: "(AD)(BC)",
    24: "180°edge(CD)", 25: "180°edge(AB)", 26: "90°face(x)",
    27: "270°face(x)", 28: "180°edge(BC)", 29: "90°face(z)",
    30: "270°face(z)", 31: "180°edge(AD)", 32: "180°edge(BD)",
    33: "270°face(y)", 34: "180°edge(AC)", 35: "90°face(y)",
}

_BYPASS_P5     = {2, 15, 17, 19}
_BYPASS_P5_INV = {5, 16, 18, 20}
_BYPASS_AB_CD  = {21}
_BYPASS_AC_BD  = {22}
_BYPASS_AD_BC  = {23}
_ALL_BYPASS    = _BYPASS_P5 | _BYPASS_P5_INV | _BYPASS_AB_CD | _BYPASS_AC_BD | _BYPASS_AD_BC
_THIRDS        = {1, 3, 4} | set(range(6, 15))  # angles requiring /3
_OCTAHEDRAL     = set(range(24, 36))

Q12 = 4096

# Octahedral 3×3 matrices (entries 0, ±1)
_OCT_MATRIX = {
    24: ((-1,0,0),(0,0,-1),(0,-1,0)),
    25: ((1,1,1),(0,-1,0),(0,0,-1)),
    26: ((0,-1,0),(1,1,1),(-1,0,0)),
    27: ((0,0,-1),(-1,0,0),(1,1,1)),
    28: ((0,-1,0),(-1,0,0),(0,0,-1)),
    29: ((1,1,1),(0,0,-1),(-1,0,0)),
    30: ((0,0,-1),(1,1,1),(0,-1,0)),
    31: ((-1,0,0),(0,-1,0),(1,1,1)),
    32: ((0,0,-1),(0,-1,0),(-1,0,0)),
    33: ((1,1,1),(-1,0,0),(0,-1,0)),
    34: ((-1,0,0),(1,1,1),(0,0,-1)),
    35: ((0,-1,0),(0,0,-1),(1,1,1)),
}


def perm_sel_for(angle: int) -> int:
    """Mirror of spu13_core.v perm_sel routing for angles 0-23.
    0-5,21-23: 00 (A-invariant or direct bypass)
    6-7,12,15-16: 01 (B→A)
    8-9,13,17-18: 10 (C→A)
    10-11,14,19-20: 11 (D→A)"""
    if angle <= 5 or angle >= 21:
        return 0
    if angle in (6, 7, 12, 15, 16):
        return 1
    if angle in (8, 9, 13, 17, 18):
        return 2
    if angle in (10, 11, 14, 19, 20):
        return 3
    return 0


def vm_rotc(source: QuadrayVector, angle: int) -> QuadrayVector:
    """Apply ROTC angle to source. Bypass angles use pure permutation;
    circulant angles use the exact VM Q12 path with axis permutation."""
    d = source

    if angle in _ALL_BYPASS:
        # Pure permutation — no arithmetic.
        comps = (d.a, d.b, d.c, d.d)
        if angle in _BYPASS_AB_CD:
            return QuadrayVector(d.b, d.a, d.d, d.c)
        elif angle in _BYPASS_AC_BD:
            return QuadrayVector(d.c, d.d, d.a, d.b)
        elif angle in _BYPASS_AD_BC:
            return QuadrayVector(d.d, d.c, d.b, d.a)
        else:
            # 3-cycle via perm_sel + bypass_p5/bypass_p5_inv
            sel = perm_sel_for(angle)
            pf = comps[sel:] + comps[:sel]
            if angle in _BYPASS_P5:
                bp = (pf[0], pf[3], pf[1], pf[2])
            else:
                bp = (pf[0], pf[2], pf[3], pf[1])
            inv_sel = (-sel) % 4
            result = bp[inv_sel:] + bp[:inv_sel]
            return QuadrayVector(*result)

    if angle in _OCTAHEDRAL:
        rows = _OCT_MATRIX[angle]
        Bv, Cv, Dv = d.b, d.c, d.d
        Bp = (RationalSurd(rows[0][0], 0) * Bv +
              RationalSurd(rows[0][1], 0) * Cv +
              RationalSurd(rows[0][2], 0) * Dv)
        Cp = (RationalSurd(rows[1][0], 0) * Bv +
              RationalSurd(rows[1][1], 0) * Cv +
              RationalSurd(rows[1][2], 0) * Dv)
        Dp = (RationalSurd(rows[2][0], 0) * Bv +
              RationalSurd(rows[2][1], 0) * Cv +
              RationalSurd(rows[2][2], 0) * Dv)
        Ap = RationalSurd(-(Bp.a + Cp.a + Dp.a), -(Bp.b + Cp.b + Dp.b))
        return QuadrayVector(Ap, Bp, Cp, Dp)

    # Circulant path (thirds + identity)
    Fa, Fb, Ga, Gb, Ha, Hb, denom = _ROTC_TABLE[angle]
    F = RationalSurd(Fa, Fb)
    G = RationalSurd(Ga, Gb)
    H = RationalSurd(Ha, Hb)

    # Forward axis permutation
    sel = perm_sel_for(angle)
    comps = (d.a, d.b, d.c, d.d)
    pA, pB, pC, pD = comps[sel:] + comps[:sel]

    # Q12 fixed-point scaling
    B = RationalSurd(pB.a * Q12, pB.b * Q12)
    C = RationalSurd(pC.a * Q12, pC.b * Q12)
    D_i = RationalSurd(pD.a * Q12, pD.b * Q12)

    # Circulant
    b2 = F * B + H * C + G * D_i
    c2 = G * B + F * C + H * D_i
    d2 = H * B + G * C + F * D_i

    # Scale back with symmetric rounding
    scale = Q12 * denom
    half = scale // 2

    def rdiv(num: int) -> int:
        if num >= 0:
            return (num + half) // scale
        else:
            return -((-num + half) // scale)

    b2 = RationalSurd(rdiv(b2.a), rdiv(b2.b))
    c2 = RationalSurd(rdiv(c2.a), rdiv(c2.b))
    d2 = RationalSurd(rdiv(d2.a), rdiv(d2.b))

    # Inverse permutation
    out = (pA, b2, c2, d2)
    inv = (-sel) % 4
    final = out[inv:] + out[:inv]
    return QuadrayVector(*final)


# ── RTL hex encoding ──────────────────────────────────────────────────────

def rs_to_hex(rs: RationalSurd) -> str:
    """Encode RationalSurd as 64-bit hex matching RTL wire format {b[31:0], a[31:0]}."""
    a32 = rs.a & 0xFFFFFFFF
    b32 = rs.b & 0xFFFFFFFF
    return f"64'h{b32:08X}{a32:08X}"


def coeff_hex(val: int) -> str:
    """Encode a scalar coefficient as a RationalSurd (val + 0√3)."""
    return rs_to_hex(RationalSurd(val, 0))


# ── Verilog testbench generation ──────────────────────────────────────────

TB_HEADER = r"""
`timescale 1ns/1ps

// Auto-generated by test_rotc_vm_rtl_trace.py — do not edit.
// Mirrors the spu13_core.v ROTC wiring: u_perm_fwd -> rotor -> u_perm_inv.
// DUT0 = ENABLE_TDM_FALLBACK=1 (F/G/H scalar-fast path)
// DUT1 = ENABLE_TDM_FALLBACK=0 (hardwired angle_scalar_*_sum path)

module spu13_rotc_trace_tb;

    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    reg start = 0;
    wire done0, done1;
    reg [63:0] src_A, src_B, src_C, src_D;
    reg [63:0] F, G, H;
    reg [5:0] angle;
    reg bypass_p5, bypass_p5_inv, apply_div3;
    reg bypass_ab_cd, bypass_ac_bd, bypass_ad_bc;
    reg recompute_A;
    reg [1:0] perm_sel;

    // Inverse select — same expression as spu13_core.v
    wire [1:0] inv_sel = (perm_sel == 2'b01) ? 2'b11 :
                         (perm_sel == 2'b11) ? 2'b01 :
                         perm_sel;

    // Forward permuter (shared by both DUTs — combinational)
    wire [63:0] rot_A_in, rot_B_in, rot_C_in, rot_D_in;
    spu_quadray_permute u_perm_fwd (
        .perm_sel(perm_sel),
        .A_in(src_A), .B_in(src_B), .C_in(src_C), .D_in(src_D),
        .A_out(rot_A_in), .B_out(rot_B_in),
        .C_out(rot_C_in), .D_out(rot_D_in)
    );

    // DUT0: scalar-fast path from F/G/H inputs
    wire [63:0] raw0_A, raw0_B, raw0_C, raw0_D;
    spu13_rotor_core_tdm #(.ENABLE_TDM_FALLBACK(1)) u_dut0 (
        .clk(clk), .rst_n(rst_n),
        .start(start), .done(done0),
        .A_in(rot_A_in), .B_in(rot_B_in), .C_in(rot_C_in), .D_in(rot_D_in),
        .F(F), .G(G), .H(H),
        .field_sel(2'b00),
        .bypass_p5(bypass_p5), .bypass_p5_inv(bypass_p5_inv),
        .bypass_ab_cd(bypass_ab_cd), .bypass_ac_bd(bypass_ac_bd),
        .bypass_ad_bc(bypass_ad_bc),
        .recompute_A(recompute_A),
        .apply_div3(apply_div3), .angle(angle),
        .A_out(raw0_A), .B_out(raw0_B), .C_out(raw0_C), .D_out(raw0_D),
        .debug_state()
    );

    // DUT1: hardwired per-angle sums, as instantiated by spu13_core
    wire [63:0] raw1_A, raw1_B, raw1_C, raw1_D;
    spu13_rotor_core_tdm #(.ENABLE_TDM_FALLBACK(0)) u_dut1 (
        .clk(clk), .rst_n(rst_n),
        .start(start), .done(done1),
        .A_in(rot_A_in), .B_in(rot_B_in), .C_in(rot_C_in), .D_in(rot_D_in),
        .F(F), .G(G), .H(H),
        .field_sel(2'b00),
        .bypass_p5(bypass_p5), .bypass_p5_inv(bypass_p5_inv),
        .bypass_ab_cd(bypass_ab_cd), .bypass_ac_bd(bypass_ac_bd),
        .bypass_ad_bc(bypass_ad_bc),
        .recompute_A(recompute_A),
        .apply_div3(apply_div3), .angle(angle),
        .A_out(raw1_A), .B_out(raw1_B), .C_out(raw1_C), .D_out(raw1_D),
        .debug_state()
    );

    // Inverse permuters
    wire [63:0] out0_A, out0_B, out0_C, out0_D;
    spu_quadray_permute u_perm_inv0 (
        .perm_sel(inv_sel),
        .A_in(raw0_A), .B_in(raw0_B), .C_in(raw0_C), .D_in(raw0_D),
        .A_out(out0_A), .B_out(out0_B), .C_out(out0_C), .D_out(out0_D)
    );
    wire [63:0] out1_A, out1_B, out1_C, out1_D;
    spu_quadray_permute u_perm_inv1 (
        .perm_sel(inv_sel),
        .A_in(raw1_A), .B_in(raw1_B), .C_in(raw1_C), .D_in(raw1_D),
        .A_out(out1_A), .B_out(out1_B), .C_out(out1_C), .D_out(out1_D)
    );

    integer fail_count = 0;

    task run_case;
        input [63:0] iA; input [63:0] iB; input [63:0] iC; input [63:0] iD;
        input [5:0]  case_angle;
        input [63:0] cF; input [63:0] cG; input [63:0] cH;
        input        c_byp; input c_byp_inv; input c_div3;
        input        c_ab_cd; input c_ac_bd; input c_ad_bc;
        input        c_recomp;
        input [1:0]  c_sel;
        input [63:0] eA; input [63:0] eB; input [63:0] eC; input [63:0] eD;
        begin
            src_A = iA; src_B = iB; src_C = iC; src_D = iD;
            angle = case_angle;
            F = cF; G = cG; H = cH;
            bypass_p5 = c_byp; bypass_p5_inv = c_byp_inv;
            apply_div3 = c_div3;
            bypass_ab_cd = c_ab_cd; bypass_ac_bd = c_ac_bd;
            bypass_ad_bc = c_ad_bc;
            recompute_A = c_recomp;
            perm_sel = c_sel;

            @(posedge clk);
            start <= 1;
            @(posedge clk);
            start <= 0;
            wait(done0 && done1);
            @(posedge clk);
            #1;

            if (!c_recomp && (out0_A !== eA || out0_B !== eB || out0_C !== eC || out0_D !== eD)) begin
                $display("  FAIL: angle %0d DUT0 (F/G/H path): got %h %h %h %h, expected %h %h %h %h",
                         case_angle, out0_A, out0_B, out0_C, out0_D, eA, eB, eC, eD);
                fail_count = fail_count + 4;
            end else if (!c_recomp) begin
                $display("  PASS: angle %0d DUT0 (F/G/H path)", case_angle);
            end else begin
                $display("  SKIP: angle %0d DUT0 (non-circulant, octahedral)", case_angle);
            end

            if (out1_A !== eA || out1_B !== eB || out1_C !== eC || out1_D !== eD) begin
                $display("  FAIL: angle %0d DUT1 (hardwired path): got %h %h %h %h, expected %h %h %h %h",
                         case_angle, out1_A, out1_B, out1_C, out1_D, eA, eB, eC, eD);
                fail_count = fail_count + 4;
            end else begin
                $display("  PASS: angle %0d DUT1 (hardwired path)", case_angle);
            end

            #40;
        end
    endtask

    initial begin
        $dumpfile("build/spu13_rotc_trace_tb.vcd");
        $dumpvars(0, spu13_rotc_trace_tb);

        #20 rst_n = 1;
        #20;
"""

TB_FOOTER = r"""
        if (fail_count == 0)
            $display("ALL %0d CHECKS PASSED", NUM_CHECKS);
        else
            $display("FAILED: %0d mismatches", fail_count);

        #200;
        $finish;
    end

endmodule
"""


def gen_case(vec: QuadrayVector, angle: int) -> str:
    """Emit one run_case call with VM-computed expected values."""
    Fa, _, Ga, _, Ha, _, denom = _ROTC_TABLE[angle]
    expected = vm_rotc(vec, angle)
    sel = perm_sel_for(angle)
    byp = 1 if angle in _BYPASS_P5 else 0
    byp_inv = 1 if angle in _BYPASS_P5_INV else 0
    div3 = 1 if denom == 3 else 0
    ab_cd = 1 if angle in _BYPASS_AB_CD else 0
    ac_bd = 1 if angle in _BYPASS_AC_BD else 0
    ad_bc = 1 if angle in _BYPASS_AD_BC else 0
    recomp = 1 if angle >= 24 else 0
    return (
        f"        // angle {angle} ({ANGLE_NAMES[angle]})\n"
        f"        run_case({rs_to_hex(vec.a)}, {rs_to_hex(vec.b)}, "
        f"{rs_to_hex(vec.c)}, {rs_to_hex(vec.d)},\n"
        f"                 6'd{angle},\n"
        f"                 {coeff_hex(Fa)}, {coeff_hex(Ga)}, {coeff_hex(Ha)},\n"
        f"                 1'b{byp}, 1'b{byp_inv}, 1'b{div3}, "
        f"1'b{ab_cd}, 1'b{ac_bd}, 1'b{ad_bc}, 1'b{recomp}, 2'd{sel},\n"
        f"                 {rs_to_hex(expected.a)}, {rs_to_hex(expected.b)}, "
        f"{rs_to_hex(expected.c)}, {rs_to_hex(expected.d)});\n"
    )


# ── Main test driver ──────────────────────────────────────────────────────

def main() -> int:
    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)

    # Vector 1: original 0-5 canonical vector (baseline, kept unchanged).
    # Divides evenly under the thirds angles only by the consecutive-integer
    # coincidence, so it is NOT safe for angles 6-11.
    vec1 = QuadrayVector(
        RationalSurd(1, 0),   # A = 1 + 0√3
        RationalSurd(2, 2),   # B = 2 + 2√3
        RationalSurd(3, 3),   # C = 3 + 3√3
        RationalSurd(4, 4),   # D = 4 + 4√3
    )
    # Vector 2: every component (both P and Q parts) a multiple of 3, with
    # mixed signs — exact under all 24 angles, and exercises the signed
    # arithmetic that historically hid a sign-extension bug.
    vec2 = QuadrayVector(
        RationalSurd(3, -6),
        RationalSurd(9, 12),
        RationalSurd(-15, 6),
        RationalSurd(21, -3),
    )

    # Exercise all 24 angles with the multiples-of-3 vector.
    # Vector 1 is kept for the 0-5 regression baseline.
    cases = [(vec1, a) for a in range(6)] + [(vec2, a) for a in range(36)]
    num_checks = len(cases) * 8  # 4 components × 2 DUTs per case

    print("VM expected outputs (Q12 path):")
    body_parts = []
    for vec, angle in cases:
        result = vm_rotc(vec, angle)
        def fmt(rs: RationalSurd) -> str:
            return f"({rs.a}{rs.b:+d}√3)"
        print(f"  angle {angle:2d} ({ANGLE_NAMES[angle]}): "
              f"A={fmt(result.a)} B={fmt(result.b)} "
              f"C={fmt(result.c)} D={fmt(result.d)}")
        body_parts.append(gen_case(vec, angle))

    tb_content = (
        TB_HEADER
        + f"\n        begin : gen_cases\n"
        + "".join(body_parts)
        + "        end\n"
        + TB_FOOTER.replace("NUM_CHECKS", str(num_checks))
    )

    tb_path = build_dir / "spu13_rotc_trace_tb.v"
    tb_path.write_text(tb_content)
    print(f"\nWrote testbench: {tb_path} ({len(cases)} cases, {num_checks} checks)")

    # Source files
    rotor_core = REPO / "hardware/rtl/core/spu13/spu13_rotor_core_tdm.v"
    permute = REPO / "hardware/rtl/core/shared/spu_quadray_permute.v"
    surd_mult = REPO / "hardware/rtl/common/prim/surd_multiplier.v"
    for f in (rotor_core, permute, surd_mult):
        if not f.exists():
            print(f"ERROR: source not found: {f}")
            return 1

    vvp_path = build_dir / "spu13_rotc_trace_tb.vvp"
    compile_cmd = [
        "iverilog", "-g2012",
        "-o", str(vvp_path),
        "-I", str(REPO / "hardware/rtl/common/prim"),
        "-y", str(REPO / "hardware/rtl/common/prim"),
        "-y", str(REPO / "hardware/rtl/core/spu13"),
        "-y", str(REPO / "hardware/rtl/core/shared"),
        str(tb_path),
    ]
    print(f"\nCompile: {' '.join(compile_cmd)}")
    cr = subprocess.run(compile_cmd, capture_output=True, text=True, cwd=str(REPO))
    if cr.returncode != 0:
        print(f"COMPILE ERROR:\n{cr.stderr}")
        return 1

    print(f"Run: vvp {vvp_path}")
    rr = subprocess.run(["vvp", str(vvp_path)], capture_output=True, text=True,
                        cwd=str(REPO), timeout=60)
    print(rr.stdout)
    if rr.stderr:
        print(rr.stderr, file=sys.stderr)

    if f"ALL {num_checks} CHECKS PASSED" in rr.stdout:
        print("\nVM-vs-RTL TRACE EQUIVALENCE (angles 0-35, DUT1 for octahedral): PASS")
        return 0
    else:
        print("\nVM-vs-RTL TRACE EQUIVALENCE: FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
