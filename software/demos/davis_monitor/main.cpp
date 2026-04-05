// Davis Law Live Monitor — SPU-13 Sovereign Engine
// Demonstrates the complete physics stack end-to-end:
//   Q(√3) → Quadray → IVM Manifold13 → Davis Gasket + Jitterbug
//
// Terminal output: scrolling table of manifold state per tick.
// No float anywhere.  All arithmetic in Q(√3).
//
// Build:  make  (or see Makefile)
// Run:    ./davis_monitor [ticks]   default = 64 ticks

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "spu_surd.h"
#include "spu_quadray.h"
#include "spu_ivm.h"
#include "spu_physics.h"

// ── ANSI colours ──────────────────────────────────────────────────────────────
#define COL_RESET  "\033[0m"
#define COL_GREEN  "\033[32m"
#define COL_YELLOW "\033[33m"
#define COL_RED    "\033[31m"
#define COL_CYAN   "\033[36m"
#define COL_BOLD   "\033[1m"

// ── Helpers ───────────────────────────────────────────────────────────────────

static void print_surd(RationalSurd s) {
    if (s.q == 0)
        printf("(%4d,   0)", (int)s.p);
    else if (s.p == 0)
        printf("(  0, %3d√3)", (int)s.q);
    else
        printf("(%4d,%3d√3)", (int)s.p, (int)s.q);
}

static void print_header(void) {
    printf(COL_BOLD);
    printf("%-5s  %-13s  %-13s  %-13s  %-13s  %-9s  State\n",
           "Tick", "τ  (p,q)", "K  (p,q)", "τ×K  (p,q)", "ΣABCD (p,q)",
           "Gate");
    printf("──────  ─────────────  ─────────────  ─────────────"
           "  ─────────────  ─────────  ──────────────────\n");
    printf(COL_RESET);
}

static void print_row(uint32_t tick,
                      DavisGasket *g,
                      Manifold13  *m,
                      PhysicsFrame *f) {
    // State colour + label
    const char *col, *label;
    if (f->henosis_pulses > 0) {
        col   = COL_YELLOW;
        label = "HENOSIS";
    } else if (f->had_leak) {
        col   = COL_RED;
        label = "CUBIC-LEAK";
    } else {
        col   = COL_GREEN;
        label = "LAMINAR";
    }

    Quadray sigma = manifold_vec_sum(*m);
    RationalSurd sigma_q = sigma.a + sigma.b + sigma.c + sigma.d;

    printf("%5u  ", tick);
    print_surd(g->tau);
    printf("  ");
    print_surd(g->K);
    printf("  ");
    // τ×K cross product (no division)
    {
        RationalSurd tk = g->tau * g->K;
        print_surd(tk);
    }
    printf("  ");
    print_surd(sigma_q);
    printf("  %-6s  %s%s%s\n",
           fib_gate_name(f->gate),
           col, label, COL_RESET);
}

// ── Main ──────────────────────────────────────────────────────────────────────
int main(int argc, char *argv[]) {
    uint32_t total_ticks = 64;
    if (argc >= 2) {
        int n = atoi(argv[1]);
        if (n > 0 && n <= 4096) total_ticks = (uint32_t)n;
    }

    printf(COL_BOLD COL_CYAN
           "\n  SPU-13 Davis Law Live Monitor\n"
           "  ──────────────────────────────────────────────────\n"
           "  Q(√3) rational field · Jitterbug · Fibonacci gates\n"
           "  Ticks: %u\n\n" COL_RESET, total_ticks);

    // ── Initialise manifold ──────────────────────────────────────────────────
    Manifold13 m = Manifold13::ivm_full();

    // ── Initialise Davis Gasket ──────────────────────────────────────────────
    DavisGasket g;
    g.tau           = RationalSurd(8, 0);   // τ starts at 8 (system resonance)
    g.K             = RationalSurd(1, 0);   // K = unity stiffness
    g.henosis_count = 0;
    g.tick_count    = 0;
    g.leak          = 0;

    // ── Initialise Jitterbug ─────────────────────────────────────────────────
    JitterbugState jb;
    jb.phase = 0;

    // ── Stats ────────────────────────────────────────────────────────────────
    uint32_t total_leaks    = 0;
    uint32_t total_henosis  = 0;
    uint32_t total_laminar  = 0;

    print_header();

    for (uint32_t t = 0; t < total_ticks; t++) {
        PhysicsFrame f = physics_tick(g, m, jb, t);

        // Accumulate stats
        if (f.henosis_pulses > 0) {
            total_henosis++;
            total_leaks++;
        } else if (f.had_leak) {
            total_leaks++;
        } else {
            total_laminar++;
        }
        total_henosis += (f.henosis_pulses > 1) ? (f.henosis_pulses - 1) : 0;

        print_row(t, &g, &m, &f);
    }

    // ── Summary ──────────────────────────────────────────────────────────────
    printf(COL_BOLD
           "\n  ══ Summary ══════════════════════════════════════════\n"
           COL_RESET);
    printf("  Ticks     : %u\n", total_ticks);
    printf("  " COL_GREEN  "Laminar   : %u" COL_RESET "\n", total_laminar);
    printf("  " COL_RED    "Leaks     : %u" COL_RESET "\n", total_leaks);
    printf("  " COL_YELLOW "Henosis   : %u pulses" COL_RESET "\n",
           (unsigned)g.henosis_count);
    printf("  Final τ   : "); print_surd(g.tau); printf("\n");
    printf("  Final K   : "); print_surd(g.K);   printf("\n");

    // Print BRAM tier table for the final manifold state
    printf(COL_BOLD "\n  ══ BRAM Tier Table (final manifold) ════════════\n"
           COL_RESET);
    print_weight_table(m);

    printf("\n");
    return 0;
}
