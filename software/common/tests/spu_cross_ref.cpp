// spu_cross_ref.cpp — Cross-validation reference runner for spu_vm.py
//
// Executes the canonical cross-validate test suite using the C++ Q(√3) layers
// and prints register state at each SNAP boundary in a machine-parseable format:
//
//   SNAP <n>
//   R<i> <p> <q>
//   QR<i> <a_p> <a_q> <b_p> <b_q> <c_p> <c_q> <d_p> <d_q>
//   END_SNAP
//
// cross_validate.py runs spu_vm.py on the same operations, parses both outputs,
// and reports any divergence.
//
// CC0 1.0 Universal.

#include "spu_surd.h"
#include "spu_quadray.h"
#include <cstdio>

// ── Helpers ────────────────────────────────────────────────────────────────

static void print_surd(const char* label, const RationalSurd& s) {
    printf("%s %d %d\n", label, (int)s.p, (int)s.q);
}

static void print_qr(int idx, const Quadray& q) {
    printf("QR%d %d %d %d %d %d %d %d %d\n",
        idx,
        (int)q.a.p, (int)q.a.q,
        (int)q.b.p, (int)q.b.q,
        (int)q.c.p, (int)q.c.q,
        (int)q.d.p, (int)q.d.q);
}

static int snap_n = 0;

// Emit SNAP boundary dump for the nominated scalar registers + QR registers.
// We only dump the registers touched by the test program to keep output stable.
static void do_snap(const char* label,
                    const RationalSurd regs[], int n_regs,
                    const Quadray      qregs[], int n_qregs)
{
    snap_n++;
    printf("SNAP %d ; %s\n", snap_n, label);
    for (int i = 0; i < n_regs; i++) {
        char buf[16];
        snprintf(buf, sizeof(buf), "R%d", i);
        print_surd(buf, regs[i]);
    }
    for (int i = 0; i < n_qregs; i++) {
        print_qr(i, qregs[i]);
    }
    printf("END_SNAP\n");
}

// ── Test programs ──────────────────────────────────────────────────────────

// Program A: Scalar arithmetic — LD, ADD, SUB, MUL, SNAP
static void prog_scalar_arith() {
    RationalSurd regs[4] = {};
    Quadray       qregs[1] = {};

    // R0 = 2 + 0·√3  (LD R0, 2, 0)
    regs[0] = RationalSurd(2, 0);

    // R1 = 0 + 1·√3  (LD R1, 0, 1)
    regs[1] = RationalSurd(0, 1);

    // R2 = R0 + R1   (ADD R2, R0, R1)
    regs[2] = regs[0] + regs[1];

    // R3 = R0 * R1   (MUL R3, R0, R1)  → (2·0 + 3·0·1) + (2·1 + 0·0)·√3 = 0 + 2√3
    regs[3] = regs[0] * regs[1];

    do_snap("scalar_arith", regs, 4, qregs, 0);
}

// Program B: Quadray load + normalize + SNAP
static void prog_quadray_load() {
    RationalSurd regs[1] = {};
    Quadray       qregs[3] = {};

    // QR0 = (1,0,0,0)  (QLOAD QR0, QR_A)
    qregs[0] = Quadray(RationalSurd(1), RationalSurd(0),
                       RationalSurd(0), RationalSurd(0));

    // QR1 = (1,1,0,0).normalize() — cuboctahedral neighbour
    qregs[1] = Quadray(RationalSurd(1), RationalSurd(1),
                       RationalSurd(0), RationalSurd(0)).normalize();

    // QR2 = QR0 + QR1  (QADD QR2, QR0, QR1)
    qregs[2] = Quadray(
        qregs[0].a + qregs[1].a, qregs[0].b + qregs[1].b,
        qregs[0].c + qregs[1].c, qregs[0].d + qregs[1].d
    ).normalize();

    do_snap("quadray_load", regs, 1, qregs, 3);
}

// Program C: Pell rotation
static void prog_pell_rotate() {
    RationalSurd regs[1] = {};
    Quadray       qregs[2] = {};

    // QR0 = (1,0,0,0)
    qregs[0] = Quadray(RationalSurd(1), RationalSurd(0),
                       RationalSurd(0), RationalSurd(0));

    // QR1 = pell_rotate(QR0)   — multiply each component by (2,1) then normalize
    qregs[1] = qregs[0].pell_rotate().normalize();

    do_snap("pell_rotate", regs, 1, qregs, 2);
}

// Program D: Quadrance and spread
static void prog_quadrance_spread() {
    RationalSurd regs[4] = {};
    Quadray       qregs[2] = {};

    qregs[0] = Quadray(RationalSurd(1), RationalSurd(0),
                       RationalSurd(0), RationalSurd(0));
    qregs[1] = Quadray(RationalSurd(0), RationalSurd(1),
                       RationalSurd(0), RationalSurd(0));

    // R0 = quadrance(QR0)
    regs[0] = qregs[0].quadrance();
    // R1 = quadrance(QR1)
    regs[1] = qregs[1].quadrance();
    // R2, R3 = spread(QR0, QR1)  → numerator + denominator
    auto [s_n, s_d] = qregs[0].spread(qregs[1]);
    regs[2] = s_n;
    regs[3] = s_d;

    do_snap("quadrance_spread", regs, 4, qregs, 2);
}

// Program E: Pell invariant chain  (R0 = pell_next applied 4 times from (1,0))
static void prog_pell_chain() {
    RationalSurd regs[5] = {};
    Quadray       qregs[0] = {};

    regs[0] = RationalSurd(1, 0);
    for (int i = 1; i <= 4; i++) {
        regs[i] = RationalSurd(2*regs[i-1].p + 3*regs[i-1].q,
                               regs[i-1].p   + 2*regs[i-1].q);
    }

    do_snap("pell_chain", regs, 5, qregs, 0);
}

// ── Main ───────────────────────────────────────────────────────────────────

int main() {
    printf("SPU_CROSS_REF_BEGIN\n");
    prog_scalar_arith();
    prog_quadray_load();
    prog_pell_rotate();
    prog_quadrance_spread();
    prog_pell_chain();
    printf("SPU_CROSS_REF_END\n");
    return 0;
}
