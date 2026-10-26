// spu13_arch_test.cpp — SPU-13 ISA v1.0 C++ behavioral test suite
//
// Cross-validates against software/spu13_arch_sim_test.py.
// Tests temporal ops, quadrance arithmetic, geometric ops,
// RPLU integration, flow control, Wheeler-Feynman phase-lock.
//
// Build: g++ -std=c++17 -I../include spu13_arch_test.cpp -o spu13_arch_test
// Run:   ./spu13_arch_test

#include "spu13_arch.h"
#include <cstdio>
#include <cmath>

static int g_pass = 0;
static int g_fail = 0;

#define OK(cond, msg) do { \
    if (cond) { g_pass++; } \
    else { printf("  FAIL: %s (line %d)\n", msg, __LINE__); g_fail++; } \
} while(0)

#define CHECK(a, b, msg) do { \
    if ((a) == (b)) { g_pass++; } \
    else { printf("  FAIL: %s  got=%lld want=%lld (line %d)\n", \
                  msg, (long long)(a), (long long)(b), __LINE__); g_fail++; } \
} while(0)

void section(const char* name) {
    printf("\n── %s ──\n", name);
}

int main() {
    // ═══════════════════════════════════════════════════════════════════════
    // 1. Instruction Encoding
    // ═══════════════════════════════════════════════════════════════════════
    section("Instruction Encoding");

    // pack_R
    uint64_t w = pack_R(OP_PHSLK, 4, 2, 3);
    auto d = decode(w);
    CHECK(d.opcode, OP_PHSLK, "pack_R opcode");
    CHECK(d.dest, 4, "pack_R dest");
    CHECK(d.srcA, 2, "pack_R srcA");
    CHECK(d.srcB, 3, "pack_R srcB");

    // pack_X
    w = pack_X(OP_HALT);
    CHECK(field_u8(w, 63, 56), OP_HALT, "pack_X HALT opcode");

    // pack_I
    w = pack_I(OP_MOVI, 5, 0xDEAD);
    d = decode(w);
    CHECK(d.opcode, OP_MOVI, "pack_I opcode");
    CHECK(d.dest, 5, "pack_I dest");
    CHECK(d.imm, 0xDEADull, "pack_I imm");

    // pack_U
    w = pack_U(OP_INVJ, 7, 3);
    d = decode(w);
    CHECK(d.opcode, OP_INVJ, "pack_U opcode");
    CHECK(d.dest, 7, "pack_U dest");
    CHECK(d.srcA, 3, "pack_U src");

    // ═══════════════════════════════════════════════════════════════════════
    // 2. OFFR / CNFM — RPLU Material Load
    // ═══════════════════════════════════════════════════════════════════════
    section("OFFR / CNFM — RPLU Material Load");

    {
        SPU13Core c;
        c.load({
            pack_R(OP_OFFR, 8, 1, 5),   // OFFR R8, material=1, addr=5
            pack_R(OP_CNFM, 9, 0, 10),  // CNFM R9, material=0, addr=10
            pack_X(OP_HALT),
        });
        c.run();

        OK(c.R[8].O.quadrance() != 0, "OFFR R8.O non-zero");
        OK(c.R[9].C.quadrance() != 0, "CNFM R9.C non-zero");
        OK(c.R[8].C.quadrance() == 0, "OFFR did not modify R8.C");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 3. PHSLK — Wheeler-Feynman Phase-Lock
    // ═══════════════════════════════════════════════════════════════════════
    section("PHSLK — Wheeler-Feynman Phase-Lock");

    // 3a. Matching Offer/Confirmation → coherent
    {
        SPU13Core c;
        c.load({
            pack_L(OP_LDO, 10, 0, 100),  // R10.O = 100
            pack_L(OP_LDC, 11, 0, 100),  // R11.C = 100
            pack_R(OP_PHSLK, 12, 10, 11),// R12 = PHSLK(R10.O, R11.C)
            pack_X(OP_HALT),
        });
        c.run();
        OK(c.flag_test(FLAG_COHERENT), "PHSLK: matching → COHERENT");
        OK(c.R[12].O.quadrance() != 0, "PHSLK: dest written");
    }

    // 3b. Mismatched → NOT coherent
    {
        SPU13Core c;
        c.load({
            pack_L(OP_LDO, 10, 0, 50),   // R10.O = 50
            pack_L(OP_LDC, 11, 0, 200),  // R11.C = 200
            pack_R(OP_PHSLK, 12, 10, 11),
            pack_X(OP_HALT),
        });
        c.run();
        OK(!c.flag_test(FLAG_COHERENT), "PHSLK: mismatched → NOT COHERENT");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 4. INVJ — Janus Inversion
    // ═══════════════════════════════════════════════════════════════════════
    section("INVJ — Janus Inversion");

    {
        SPU13Core c;
        c.load({
            pack_L(OP_LDO, 15, 0, 42),     // R15.O = 42
            pack_U(OP_INVJ, 16, 15),        // R16 = INVJ(R15) = -42
            pack_X(OP_HALT),
        });
        c.run();

        int64_t q_orig = c.R[15].O.quadrance();
        int64_t q_inv  = c.R[16].O.quadrance();
        OK(q_orig == q_inv, "INVJ: quadrance preserved");

        // Component signs reversed
        OK(c.R[16].O.a == -c.R[15].O.a, "INVJ: component a negated");
        OK(c.R[16].O.b == -c.R[15].O.b, "INVJ: component b negated");
        OK(c.R[16].O.c == -c.R[15].O.c, "INVJ: component c negated");
        OK(c.R[16].O.d == -c.R[15].O.d, "INVJ: component d negated");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 5. PHSTA / PHCLR — Phase-Lock Status
    // ═══════════════════════════════════════════════════════════════════════
    section("PHSTA / PHCLR — Status");

    {
        SPU13Core c;
        c.load({
            pack_X(OP_PHCLR),                   // Clear coherent flag
            pack_U(OP_PHSTA, 17, REG_ZERO),     // R17 = coherent? (0)
            pack_L(OP_LDO, 18, 0, 50),
            pack_L(OP_LDC, 19, 0, 50),
            pack_R(OP_PHSLK, 20, 18, 19),       // Lock → coherent=1
            pack_U(OP_PHSTA, 21, REG_ZERO),     // R21 = coherent? (1)
            pack_X(OP_HALT),
        });
        c.run();

        OK(c.R[17].O.a == 0,
           "PHSTA after PHCLR: should be 0");
        OK(c.R[21].O.a == 1,
           "PHSTA after PHSLK: should be 1");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 6. Quadrance Arithmetic
    // ═══════════════════════════════════════════════════════════════════════
    section("Quadrance Arithmetic");

    {
        SPU13Core c;
        c.load({
            pack_L(OP_LDO, 22, 0, 100),  // R22.O = 100 → Q=10000
            pack_L(OP_LDO, 23, 0, 50),   // R23.O = 50  → Q=2500
            pack_R(OP_QADD, 24, 22, 23), // QADD → Q=12500
            pack_X(OP_HALT),
        });
        c.run();

        OK(c.QUAD_OUT.num > 0, "QADD: positive result");
        // Quadrance of scalar n is n²
        // R22 quadrance = 10000, R23 quadrance = 2500
        // QADD sum = 12500
        CHECK(c.QUAD_OUT.num, 12500, "QADD: 10000 + 2500 = 12500");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 7. Geometric Operations
    // ═══════════════════════════════════════════════════════════════════════
    section("Geometric Operations");

    // TNSR — tensor M = 4I
    {
        SPU13Core c;
        c.load({
            pack_L(OP_LDO, 25, 0, 10),
            pack_R(OP_TNSR, 26, 25, 0),
            pack_X(OP_HALT),
        });
        c.run();

        OK(c.R[26].O.quadrance() > 0, "TNSR: non-zero result");
        // scalar 10 → quadray (10,0,0,0) → scaled to (40,0,0,0)
        // quadrance = 40² = 1600
        CHECK(c.R[26].O.quadrance(), (int64_t)1600, "TNSR: 10→40, Q=1600");
    }

    // CROSS — quadray cross product
    {
        SPU13Core c;
        c.load({
            pack_L(OP_LDO, 10, 0, 3),    // R10 = (3,0,0,0)
            pack_L(OP_LDO, 11, 0, 5),    // R11 = (5,0,0,0)
            pack_R(OP_CROSS, 12, 10, 11), // cross → (0,0,0,0)
            pack_X(OP_HALT),
        });
        c.run();

        OK(c.R[12].O.quadrance() == 0, "CROSS: parallel vectors → zero");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 8. Flow Control
    // ═══════════════════════════════════════════════════════════════════════
    section("Flow Control");

    // JZ — jump if zero (after QCMP with equal values)
    {
        SPU13Core c;
        c.load({
            pack_L(OP_LDO, 27, 0, 10),
            pack_L(OP_LDO, 28, 0, 10),       // Same → QCMP sets ZERO
            pack_R(OP_QCMP, REG_ZERO, 27, 28),
            pack_B(OP_JZ, 2),                 // Should jump forward 2
            pack_I(OP_MOVI, 29, 0xBAD),       // Skipped
            pack_I(OP_MOVI, 29, 0x600D),      // JZ target
            pack_X(OP_HALT),
        });
        c.run();

        // MOVI stores val as Quadray(a=val, b=0, c=0, d=0)
        int32_t val = c.R[29].O.a;
        CHECK(val, 0x600D, "JZ: R29 should be 0x600D (GOOD)");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 9. RPLU Table Simulation
    // ═══════════════════════════════════════════════════════════════════════
    section("RPLU Table Simulation");

    {
        RPLUTable rplu;
        auto p = rplu.read_params(0, 0);
        CHECK(p.a, 0x00010000, "RPLU params[0].a");
        CHECK(p.re, 0x00080000, "RPLU params[0].re");

        // RATIO_CMP cross-multiplication
        CHECK(rplu.ratio_cmp(10, 1, 10, 1), 0,  "RATIO_CMP equal");
        CHECK(rplu.ratio_cmp(10, 1, 20, 1), -1, "RATIO_CMP less");
        CHECK(rplu.ratio_cmp(20, 1, 10, 1), 1,  "RATIO_CMP greater");

        // Dissociation
        OK(rplu.read_dissoc(0, 5) == 1,   "RPLU dissoc at addr 5");
        OK(rplu.read_dissoc(0, 200) == 0, "RPLU dissoc at addr 200");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // 10. Rational Quadray Arithmetic
    // ═══════════════════════════════════════════════════════════════════════
    section("Rational Quadray Arithmetic");

    // Quadrance of (3,4,0,0) = 9+16 = 25
    {
        Quadray q(3, 4, 0, 0);
        CHECK(q.quadrance(), (int64_t)25, "Quadray(3,4,0,0) quadrance = 25");
    }

    // Cross product (1,0,0,0) × (0,1,0,0) = (0,0,1,0)
    {
        Quadray a(1,0,0,0), b(0,1,0,0);
        Quadray c = a.cross(b);
        OK(c.a == 0 && c.b == 0 && c.c == 1 && c.d == 0,
           "Cross product (1,0,0,0)×(0,1,0,0) = (0,0,1,0)");
    }

    // Tensor M = 4I applied to (1,2,3,4) → (4,8,12,16)
    {
        Quadray v(1,2,3,4);
        Quadray t = v.tensor_M();
        OK(t.a==4 && t.b==8 && t.c==12 && t.d==16,
           "TNSR: (1,2,3,4) → (4,8,12,16)");
    }

    // ═══════════════════════════════════════════════════════════════════════
    // Results
    // ═══════════════════════════════════════════════════════════════════════
    printf("\n── SUMMARY ──\n");
    int total = g_pass + g_fail;
    printf("  PASS: %d/%d  FAIL: %d/%d\n", g_pass, total, g_fail, total);
    if (g_fail > 0) {
        printf("  *** %d TESTS FAILED ***\n", g_fail);
        return 1;
    }
    printf("  ALL TESTS PASSED\n");
    return 0;
}
