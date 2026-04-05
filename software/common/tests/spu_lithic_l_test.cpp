// spu_lithic_l_test.cpp — Tests for spu_lithic_l.h (Layer 5: ISA encoding)
// Checks:
//  1. Opcode constants match spu_vm.py OPCODES dict
//  2. l_encode() bit packing
//  3. Instruction constructors (L_LD, L_ADD, L_SNAP, etc.)
//  4. Decode helpers (l_opcode, l_r1, l_r2, l_p1_a, l_p1_b)
//  5. Signed immediate round-trip (L_LD with negative p/q)
//  6. MUX primitive
//  7. Chord packing
//  8. LithicProg buffer: emit, patch_addr
//  9. jitterbug_prog_fill opcode sequence

#include <cstdio>
#include <cstdint>
#include <cstring>
#include "spu_surd.h"
#include "spu_lithic_l.h"

static int g_pass = 0;
static int g_fail = 0;

#define ASSERT(cond, msg) do { \
    if (cond) { g_pass++; } \
    else { printf("FAIL: %s (line %d)\n", msg, __LINE__); g_fail++; } \
} while(0)

#define ASSERT_EQ(got, want, msg) do { \
    if ((got) == (want)) { g_pass++; } \
    else { printf("FAIL: %s  got=0x%llx want=0x%llx (line %d)\n", \
                  msg, (unsigned long long)(got), (unsigned long long)(want), __LINE__); g_fail++; } \
} while(0)

int main() {
    // ── 1. Opcode constants match spu_vm.py ──────────────────────────────
    ASSERT_EQ(L_OP_LD,     0x00u, "LD opcode");
    ASSERT_EQ(L_OP_ADD,    0x01u, "ADD opcode");
    ASSERT_EQ(L_OP_SUB,    0x02u, "SUB opcode");
    ASSERT_EQ(L_OP_MUL,    0x03u, "MUL opcode");
    ASSERT_EQ(L_OP_ROT,    0x04u, "ROT opcode");
    ASSERT_EQ(L_OP_LOG,    0x05u, "LOG opcode");
    ASSERT_EQ(L_OP_JMP,    0x06u, "JMP opcode");
    ASSERT_EQ(L_OP_SNAP,   0x07u, "SNAP opcode");
    ASSERT_EQ(L_OP_QADD,   0x10u, "QADD opcode");
    ASSERT_EQ(L_OP_QROT,   0x11u, "QROT opcode");
    ASSERT_EQ(L_OP_QNORM,  0x12u, "QNORM opcode");
    ASSERT_EQ(L_OP_QLOAD,  0x13u, "QLOAD opcode");
    ASSERT_EQ(L_OP_QLOG,   0x14u, "QLOG opcode");
    ASSERT_EQ(L_OP_SPREAD, 0x15u, "SPREAD opcode");
    ASSERT_EQ(L_OP_HEX,    0x16u, "HEX opcode");
    ASSERT_EQ(L_OP_EQUIL,  0x17u, "EQUIL opcode");
    ASSERT_EQ(L_OP_IDNT,   0x18u, "IDNT opcode");
    ASSERT_EQ(L_OP_JINV,   0x19u, "JINV opcode");
    ASSERT_EQ(L_OP_ANNE,   0x1Au, "ANNE opcode");
    ASSERT_EQ(L_OP_COND,   0x20u, "COND opcode");
    ASSERT_EQ(L_OP_CALL,   0x21u, "CALL opcode");
    ASSERT_EQ(L_OP_RET,    0x22u, "RET opcode");
    ASSERT_EQ(L_OP_NOP,    0xFFu, "NOP opcode");

    // ── 2. l_encode bit packing ───────────────────────────────────────────
    // All fields at known values: op=0x01, r1=0x02, r2=0x03, p1_a=0x0004, p1_b=0x0005
    {
        uint64_t w = l_encode(0x01, 0x02, 0x03, 0x0004, 0x0005);
        // [63:56]=01 [55:48]=02 [47:40]=03 [39:24]=0004 [23:8]=0005 [7:0]=00
        uint64_t expected =
            (uint64_t(0x01) << 56) |
            (uint64_t(0x02) << 48) |
            (uint64_t(0x03) << 40) |
            (uint64_t(0x0004) << 24) |
            (uint64_t(0x0005) << 8);
        ASSERT_EQ(w, expected, "l_encode bit layout");
    }

    // ── 3. Instruction constructors ───────────────────────────────────────
    // L_LD R5, 7, 4  → op=LD, r1=5, p1_a=7, p1_b=4
    {
        uint64_t w = L_LD(5, 7, 4);
        ASSERT_EQ(l_opcode(w), (uint8_t)L_OP_LD,  "L_LD opcode field");
        ASSERT_EQ(l_r1(w),     (uint8_t)5,         "L_LD r1 field");
        ASSERT_EQ(l_imm_p(w),  (int16_t)7,         "L_LD p component");
        ASSERT_EQ(l_imm_q(w),  (int16_t)4,         "L_LD q component");
    }

    // L_ADD R2, R3 → op=ADD, r1=2, r2=3
    {
        uint64_t w = L_ADD(2, 3);
        ASSERT_EQ(l_opcode(w), (uint8_t)L_OP_ADD, "L_ADD opcode");
        ASSERT_EQ(l_r1(w),     (uint8_t)2,         "L_ADD r1");
        ASSERT_EQ(l_r2(w),     (uint8_t)3,         "L_ADD r2");
    }

    // L_SUB, L_MUL shape check
    ASSERT_EQ(l_opcode(L_SUB(1,2)), (uint8_t)L_OP_SUB, "L_SUB opcode");
    ASSERT_EQ(l_opcode(L_MUL(0,1)), (uint8_t)L_OP_MUL, "L_MUL opcode");

    // L_ROT R4
    {
        uint64_t w = L_ROT(4);
        ASSERT_EQ(l_opcode(w), (uint8_t)L_OP_ROT, "L_ROT opcode");
        ASSERT_EQ(l_r1(w),     (uint8_t)4,          "L_ROT r1");
    }

    // L_JMP(42)
    {
        uint64_t w = L_JMP(42);
        ASSERT_EQ(l_opcode(w), (uint8_t)L_OP_JMP, "L_JMP opcode");
        ASSERT_EQ(l_p1_a(w),   (uint16_t)42,        "L_JMP addr in p1_a");
    }

    // L_SNAP
    ASSERT_EQ(l_opcode(L_SNAP()), (uint8_t)L_OP_SNAP, "L_SNAP opcode");

    // L_COND R7, 100
    {
        uint64_t w = L_COND(7, 100);
        ASSERT_EQ(l_opcode(w), (uint8_t)L_OP_COND, "L_COND opcode");
        ASSERT_EQ(l_r1(w),     (uint8_t)7,           "L_COND r1");
        ASSERT_EQ(l_p1_a(w),   (uint16_t)100,         "L_COND addr");
    }

    // L_CALL, L_RET
    ASSERT_EQ(l_opcode(L_CALL(5)), (uint8_t)L_OP_CALL, "L_CALL opcode");
    ASSERT_EQ(l_opcode(L_RET()),   (uint8_t)L_OP_RET,  "L_RET opcode");

    // Quadray instructions
    {
        uint64_t w = L_QADD(3, 7);
        ASSERT_EQ(l_opcode(w), (uint8_t)L_OP_QADD, "L_QADD opcode");
        ASSERT_EQ(l_r1(w), (uint8_t)3, "L_QADD QRd");
        ASSERT_EQ(l_r2(w), (uint8_t)7, "L_QADD QRs");
    }
    {
        uint64_t w = L_QROT(6);
        ASSERT_EQ(l_opcode(w), (uint8_t)L_OP_QROT, "L_QROT opcode");
        ASSERT_EQ(l_r1(w),     (uint8_t)6,           "L_QROT QRn");
    }
    ASSERT_EQ(l_opcode(L_QNORM(2)), (uint8_t)L_OP_QNORM, "L_QNORM opcode");
    ASSERT_EQ(l_opcode(L_QLOG(1)),  (uint8_t)L_OP_QLOG,  "L_QLOG opcode");

    // L_SPREAD R1, QR2, QR5  → r1=1 (dest scalar), r2=2 (QRa), p1_b=5 (QRb)
    {
        uint64_t w = L_SPREAD(1, 2, 5);
        ASSERT_EQ(l_opcode(w),  (uint8_t)L_OP_SPREAD, "L_SPREAD opcode");
        ASSERT_EQ(l_r1(w),      (uint8_t)1,             "L_SPREAD Rd");
        ASSERT_EQ(l_r2(w),      (uint8_t)2,             "L_SPREAD QRa");
        ASSERT_EQ(l_p1_b(w),    (uint16_t)5,             "L_SPREAD QRb");
    }

    // VE + Janus
    ASSERT_EQ(l_opcode(L_EQUIL()),  (uint8_t)L_OP_EQUIL,  "L_EQUIL opcode");
    ASSERT_EQ(l_opcode(L_IDNT(3)),  (uint8_t)L_OP_IDNT,   "L_IDNT opcode");
    ASSERT_EQ(l_opcode(L_JINV(0)),  (uint8_t)L_OP_JINV,   "L_JINV opcode");
    ASSERT_EQ(l_opcode(L_ANNE(12)), (uint8_t)L_OP_ANNE,   "L_ANNE opcode");
    ASSERT_EQ(l_opcode(L_NOP()),    (uint8_t)L_OP_NOP,    "L_NOP opcode");

    // ── 4. Signed immediate round-trip ────────────────────────────────────
    // L_LD R0, -1, -3  (negative Pell component)
    {
        uint64_t w = L_LD(0, -1, -3);
        ASSERT_EQ(l_imm_p(w), (int16_t)(-1), "L_LD negative p");
        ASSERT_EQ(l_imm_q(w), (int16_t)(-3), "L_LD negative q");
    }
    // Large value: 2911 (5042th Pell component)
    {
        uint64_t w = L_LD(1, 5042, 2911);
        ASSERT_EQ(l_imm_p(w), (int16_t)5042, "L_LD large p");
        ASSERT_EQ(l_imm_q(w), (int16_t)2911, "L_LD large q");
    }

    // ── 5. MUX primitive ──────────────────────────────────────────────────
    ASSERT_EQ(L_MUX(1, 10, 20), 10, "L_MUX true branch");
    ASSERT_EQ(L_MUX(0, 10, 20), 20, "L_MUX false branch");
    // L_MUX_SURD: SURD_UNITY has norm=1>0 → true
    {
        RationalSurd t = SURD_UNITY;
        RationalSurd f = SURD_ZERO;
        RationalSurd res = L_MUX_SURD(t, SURD_PHI1, SURD_ZERO);
        ASSERT(res == SURD_PHI1, "L_MUX_SURD: unity selects true");
        res = L_MUX_SURD(f, SURD_PHI1, SURD_ZERO);
        ASSERT(res == SURD_ZERO, "L_MUX_SURD: zero selects false");
    }

    // ── 6. Chord packing ──────────────────────────────────────────────────
    {
        RationalSurd a{1, 0}, b{2, 0}, c{3, 0}, d{4, 0};
        uint64_t chord = chord_pack(a, b, c, d);
        ASSERT_EQ((chord >> 48) & 0xFFFF, (uint64_t)1, "chord a.p");
        ASSERT_EQ((chord >> 32) & 0xFFFF, (uint64_t)2, "chord b.p");
        ASSERT_EQ((chord >> 16) & 0xFFFF, (uint64_t)3, "chord c.p");
        ASSERT_EQ((chord >>  0) & 0xFFFF, (uint64_t)4, "chord d.p");
    }
    // Negative components use two's complement in 16-bit slot
    {
        RationalSurd n{-1, 0};
        uint64_t chord = chord_pack(n, n, n, n);
        ASSERT_EQ((chord >> 48) & 0xFFFF, (uint64_t)0xFFFF, "chord neg a.p");
    }

    // ── 7. LithicProg buffer ──────────────────────────────────────────────
    {
        LithicProg<8> prog;
        ASSERT_EQ(prog.len, (size_t)0, "LithicProg initial length");

        ASSERT(prog.emit(L_LD(0, 1, 0)),  "LithicProg emit 1");
        ASSERT(prog.emit(L_QROT(0)),       "LithicProg emit 2");
        ASSERT(prog.emit(L_JMP(0)),        "LithicProg emit JMP");
        ASSERT_EQ(prog.len, (size_t)3,     "LithicProg length after 3 emits");

        // Decode first instruction
        ASSERT_EQ(l_opcode(prog.words[0]), (uint8_t)L_OP_LD,   "prog[0] LD");
        ASSERT_EQ(l_opcode(prog.words[1]), (uint8_t)L_OP_QROT, "prog[1] QROT");
        ASSERT_EQ(l_opcode(prog.words[2]), (uint8_t)L_OP_JMP,  "prog[2] JMP");

        // patch_addr: fix JMP target
        prog.patch_addr(2, 1);
        ASSERT_EQ(l_p1_a(prog.words[2]), (uint16_t)1, "patch_addr JMP→1");

        // Fill to capacity then reject
        for (int i = 3; i < 8; i++) prog.emit(L_NOP());
        ASSERT_EQ(prog.len, (size_t)8, "LithicProg full");
        ASSERT(!prog.emit(L_NOP()), "LithicProg overflow rejected");

        prog.reset();
        ASSERT_EQ(prog.len, (size_t)0, "LithicProg reset");
    }

    // ── 8. jitterbug_prog_fill ────────────────────────────────────────────
    {
        uint64_t prog[5];
        jitterbug_prog_fill(prog);
        ASSERT_EQ(l_opcode(prog[0]), (uint8_t)L_OP_QROT,  "jitterbug prog[0] QROT");
        ASSERT_EQ(l_opcode(prog[1]), (uint8_t)L_OP_EQUIL, "jitterbug prog[1] EQUIL");
        ASSERT_EQ(l_opcode(prog[2]), (uint8_t)L_OP_ROT,   "jitterbug prog[2] ROT");
        ASSERT_EQ(l_opcode(prog[3]), (uint8_t)L_OP_SNAP,  "jitterbug prog[3] SNAP");
        ASSERT_EQ(l_opcode(prog[4]), (uint8_t)L_OP_JMP,   "jitterbug prog[4] JMP");
        // Loop back to address 0
        ASSERT_EQ(l_p1_a(prog[4]),   (uint16_t)0,          "jitterbug JMP→0");
    }

    // ── Result ────────────────────────────────────────────────────────────
    if (g_fail == 0)
        printf("PASS\n");
    else
        printf("FAIL (%d failures / %d total)\n", g_fail, g_pass + g_fail);

    return g_fail > 0 ? 1 : 0;
}
