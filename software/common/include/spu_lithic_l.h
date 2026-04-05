// spu_lithic_l.h — Lithic-L ISA: 64-bit Chord instruction encoding
// Layer 5 of the Q(√3) software stack for the SPU-13 Sovereign Engine.
//
// Encoding (64-bit control word, matches spu_vm.py v1.2):
//   [63:56]  opcode   (8-bit)
//   [55:48]  r1       (8-bit register index, scalar R0-R25 or Quadray QR0-QR12)
//   [47:40]  r2       (8-bit register index)
//   [39:24]  p1_a     (16-bit immediate / address / QR index A)
//   [23: 8]  p1_b     (16-bit immediate / QR index B)
//   [ 7: 0]  (zero)
//
// MUX primitive: branchless control flow via Boolean polynomial selection.
// All "branches" in Lithic-L programs must compile to L_MUX chains — never
// to JMP unless jumping to a fixed label at compile time.
//
// Usage:
//   #include "spu_lithic_l.h"
//   uint64_t prog[] = { L_LD(0, 2, 1), L_QROT(3), L_SNAP(), L_NOP() };

#ifndef SPU_LITHIC_L_H
#define SPU_LITHIC_L_H

#include <stdint.h>
#include <stddef.h>
#include "spu_surd.h"

// ── Opcode constants (mirrors OPCODES dict in spu_vm.py v1.2) ─────────────
// Scalar Q(√3) arithmetic
#define L_OP_LD     0x00u  // LD  Rn, p, q   — load immediate surd (p + q√3)
#define L_OP_ADD    0x01u  // ADD Rd, Rs      — Rd = Rd + Rs
#define L_OP_SUB    0x02u  // SUB Rd, Rs      — Rd = Rd - Rs
#define L_OP_MUL    0x03u  // MUL Rd, Rs      — Rd = Rd * Rs
#define L_OP_ROT    0x04u  // ROT Rn          — Rn = Rn × (2+√3)  Pell step
#define L_OP_LOG    0x05u  // LOG Rn          — emit Rn to trace
// Control flow
#define L_OP_JMP    0x06u  // JMP addr        — unconditional jump (label/addr)
#define L_OP_SNAP   0x07u  // SNAP            — Davis Gate: assert all regs laminar
#define L_OP_COND   0x20u  // COND Rn, addr   — branch if Rn.quadrance() > 0
#define L_OP_CALL   0x21u  // CALL addr       — push return addr, jump
#define L_OP_RET    0x22u  // RET             — pop return addr, jump
// Quadray IVM operations
#define L_OP_QADD   0x10u  // QADD QRd, QRs   — QRd = QRd + QRs
#define L_OP_QROT   0x11u  // QROT QRn        — Pell rotor on each component
#define L_OP_QNORM  0x12u  // QNORM QRn       — normalize (subtract min4)
#define L_OP_QLOAD  0x13u  // QLOAD QRn, a, b, c, d — load 4 immediate components
#define L_OP_QLOG   0x14u  // QLOG QRn        — emit QRn to trace
// Geometry output
#define L_OP_SPREAD 0x15u  // SPREAD Rd, QRa, QRb — Rd = Spread(QRa, QRb)
#define L_OP_HEX    0x16u  // HEX QRn         — output hex projection of QRn
// Vector Equilibrium + Janus (v1.2)
#define L_OP_EQUIL  0x17u  // EQUIL           — assert Σ(QR0..12) == zero vector
#define L_OP_IDNT   0x18u  // IDNT QRn        — reset QRn to canonical unity (1,0,0,0)
#define L_OP_JINV   0x19u  // JINV Rn         — negate surd component (Janus bit)
#define L_OP_ANNE   0x1Au  // ANNE QRn        — anneal toward VE (halve components)
// No-op
#define L_OP_NOP    0xFFu  // NOP

// ── Low-level instruction word builder ────────────────────────────────────
// [op:8][r1:8][r2:8][p1_a:16][p1_b:16][0:8]
constexpr uint64_t l_encode(uint8_t op, uint8_t r1 = 0, uint8_t r2 = 0,
                              uint16_t p1_a = 0, uint16_t p1_b = 0) {
    return (uint64_t(op)   << 56)
         | (uint64_t(r1)   << 48)
         | (uint64_t(r2)   << 40)
         | (uint64_t(p1_a) << 24)
         | (uint64_t(p1_b) <<  8);
}

// ── Instruction constructors ───────────────────────────────────────────────
// Scalar instructions
// LD Rn, p, q  (p and q as int16_t, cast to uint16_t for encoding)
constexpr uint64_t L_LD(uint8_t rn, int16_t p, int16_t q = 0) {
    return l_encode(L_OP_LD, rn, 0,
                    static_cast<uint16_t>(p),
                    static_cast<uint16_t>(q));
}
constexpr uint64_t L_ADD(uint8_t rd, uint8_t rs) {
    return l_encode(L_OP_ADD, rd, rs);
}
constexpr uint64_t L_SUB(uint8_t rd, uint8_t rs) {
    return l_encode(L_OP_SUB, rd, rs);
}
constexpr uint64_t L_MUL(uint8_t rd, uint8_t rs) {
    return l_encode(L_OP_MUL, rd, rs);
}
constexpr uint64_t L_ROT(uint8_t rn) {
    return l_encode(L_OP_ROT, rn);
}
constexpr uint64_t L_LOG(uint8_t rn) {
    return l_encode(L_OP_LOG, rn);
}

// Control flow
constexpr uint64_t L_JMP(uint16_t addr) {
    return l_encode(L_OP_JMP, 0, 0, addr);
}
constexpr uint64_t L_SNAP() {
    return l_encode(L_OP_SNAP);
}
constexpr uint64_t L_COND(uint8_t rn, uint16_t addr) {
    return l_encode(L_OP_COND, rn, 0, addr);
}
constexpr uint64_t L_CALL(uint16_t addr) {
    return l_encode(L_OP_CALL, 0, 0, addr);
}
constexpr uint64_t L_RET() {
    return l_encode(L_OP_RET);
}

// Quadray instructions
constexpr uint64_t L_QADD(uint8_t qrd, uint8_t qrs) {
    return l_encode(L_OP_QADD, qrd, qrs);
}
constexpr uint64_t L_QROT(uint8_t qrn) {
    return l_encode(L_OP_QROT, qrn);
}
constexpr uint64_t L_QNORM(uint8_t qrn) {
    return l_encode(L_OP_QNORM, qrn);
}
// QLOAD QRn, a_p, a_q, b_p — encodes first component p/q; extend for full 4D
// spu_vm.py stores a_p in p1_a and a_q in p1_b for the first axis component
constexpr uint64_t L_QLOAD(uint8_t qrn, int16_t a_p, int16_t a_q = 0) {
    return l_encode(L_OP_QLOAD, qrn, 0,
                    static_cast<uint16_t>(a_p),
                    static_cast<uint16_t>(a_q));
}
constexpr uint64_t L_QLOG(uint8_t qrn) {
    return l_encode(L_OP_QLOG, qrn);
}

// Geometry
constexpr uint64_t L_SPREAD(uint8_t rd, uint8_t qra, uint8_t qrb) {
    return l_encode(L_OP_SPREAD, rd, qra, 0, qrb);
}
constexpr uint64_t L_HEX(uint8_t qrn) {
    return l_encode(L_OP_HEX, qrn);
}

// VE + Janus
constexpr uint64_t L_EQUIL() {
    return l_encode(L_OP_EQUIL);
}
constexpr uint64_t L_IDNT(uint8_t qrn) {
    return l_encode(L_OP_IDNT, qrn);
}
constexpr uint64_t L_JINV(uint8_t rn) {
    return l_encode(L_OP_JINV, rn);
}
constexpr uint64_t L_ANNE(uint8_t qrn) {
    return l_encode(L_OP_ANNE, qrn);
}
constexpr uint64_t L_NOP() {
    return l_encode(L_OP_NOP);
}

// ── Opcode decode helper (for emulators / disassemblers) ──────────────────
constexpr uint8_t  l_opcode(uint64_t w) { return static_cast<uint8_t>(w >> 56); }
constexpr uint8_t  l_r1(uint64_t w)     { return static_cast<uint8_t>(w >> 48); }
constexpr uint8_t  l_r2(uint64_t w)     { return static_cast<uint8_t>(w >> 40); }
constexpr uint16_t l_p1_a(uint64_t w)   { return static_cast<uint16_t>(w >> 24); }
constexpr uint16_t l_p1_b(uint64_t w)   { return static_cast<uint16_t>(w >>  8); }
// Signed immediate extraction (for LD p/q components)
constexpr int16_t  l_imm_p(uint64_t w)  { return static_cast<int16_t>(l_p1_a(w)); }
constexpr int16_t  l_imm_q(uint64_t w)  { return static_cast<int16_t>(l_p1_b(w)); }

// ── MUX primitive — branchless control flow ───────────────────────────────
// Replace all branches with Boolean polynomial selection.
// L_MUX(sel, a, b) = sel ? a : b  (compile-time selection on integer sel)
// For runtime RationalSurd selection:
//   result = (sel_is_nonzero * a) + ((1 - sel_is_nonzero) * b)
//   The hardware evaluates both and selects — no branch, no pipeline stall.
//
// Usage:
//   RationalSurd r = L_MUX_SURD(condition_surd, val_true, val_false);
//   where condition_surd is laminar (quadrance > 0) → selects val_true.

#define L_MUX(sel, a, b)          ((sel) ? (a) : (b))
#define L_MUX_SURD(cond, vt, vf)  ((cond).norm() > 0 ? (vt) : (vf))

// ── Fibonacci dispatch table ───────────────────────────────────────────────
// Gate labels: which Fibonacci position in the 34-cycle Sierpinski frame
// fired this instruction.  Mirrors FibGate in spu_physics.h.
// Include spu_physics.h before using these if you need FibGate type.
#define L_GATE_NONE  0u
#define L_GATE_PHI8  1u   // cycle % 8  == 0  (micro gate)
#define L_GATE_PHI13 2u   // cycle % 13 == 0  (meso gate)
#define L_GATE_PHI21 3u   // cycle % 21 == 0  (macro gate)

// ── Chord packing ──────────────────────────────────────────────────────────
// A Chord packs 4 RationalSurd p-values into a 64-bit word (hardware Artery
// wire format).  Only the rational (p) components are transmitted over the bus;
// the surd (q) components are carried separately or set to zero.
//
// Wire format: [a.p:16][b.p:16][c.p:16][d.p:16]
constexpr uint64_t chord_pack(const RationalSurd& a, const RationalSurd& b,
                               const RationalSurd& c, const RationalSurd& d) {
    return (uint64_t(uint16_t(a.p)) << 48)
         | (uint64_t(uint16_t(b.p)) << 32)
         | (uint64_t(uint16_t(c.p)) << 16)
         | (uint64_t(uint16_t(d.p)) <<  0);
}

// ── Simple bytecode program buffer ────────────────────────────────────────
// Fixed-capacity word array for building Lithic-L programs at runtime.
template<size_t N>
struct LithicProg {
    uint64_t words[N] = {};
    size_t   len      = 0;

    bool emit(uint64_t w) {
        if (len >= N) return false;
        words[len++] = w;
        return true;
    }

    void reset() { len = 0; }

    // Patch a JMP or COND destination after the target address is known.
    bool patch_addr(size_t instr_idx, uint16_t new_addr) {
        if (instr_idx >= len) return false;
        uint64_t w    = words[instr_idx];
        uint8_t  op   = l_opcode(w);
        uint8_t  r1_v = l_r1(w);
        uint8_t  r2_v = l_r2(w);
        uint16_t p1b  = l_p1_b(w);
        words[instr_idx] = l_encode(op, r1_v, r2_v, new_addr, p1b);
        return true;
    }
};

// ── Canned Jitterbug morph program ────────────────────────────────────────
// 5-word loop: rotate QR0, assert equilibrium, Pell-rotate scalar R0,
//              SNAP (Davis Gate), then loop back.
// This is the reference "heartbeat" program — feed it to spu_vm.py.
inline void jitterbug_prog_fill(uint64_t out[5]) {
    out[0] = L_QROT(0);     // QROT  QR0   — Pell step on first axis
    out[1] = L_EQUIL();     // EQUIL        — assert VE balance
    out[2] = L_ROT(0);      // ROT   R0    — Pell step on scalar
    out[3] = L_SNAP();      // SNAP         — Davis Gate check
    out[4] = L_JMP(0);      // JMP   0     — loop forever
}

#endif // SPU_LITHIC_L_H

