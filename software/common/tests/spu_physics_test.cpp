// spu_physics_test.cpp — Unit tests for spu_physics.h
// CC0 1.0 Universal.

#include "spu_physics.h"
#include <cstdio>

static int failures = 0;

#define CHECK(label, cond) do { \
    if (!(cond)) { printf("  FAIL: %s\n", label); failures++; } \
} while(0)

#define CHECK_SURD(label, got, want) do { \
    RationalSurd _g=(got), _w=(want); \
    if (_g != _w) { \
        printf("  FAIL: %s  got (%d,%d) want (%d,%d)\n", \
               label, _g.p, _g.q, _w.p, _w.q); \
        failures++; \
    } \
} while(0)

#define CHECK_INT(label, got, want) do { \
    int _g=(got), _w=(want); \
    if (_g != _w) { \
        printf("  FAIL: %s  got %d want %d\n", label, _g, _w); \
        failures++; \
    } \
} while(0)

int main() {

    // ── Pell orbit ────────────────────────────────────────────────────────── //
    CHECK_SURD("pell_orbit 0", pell_orbit(0), RationalSurd(1,0));
    CHECK_SURD("pell_orbit 1", pell_orbit(1), RationalSurd(2,1));
    CHECK_SURD("pell_orbit 2", pell_orbit(2), RationalSurd(7,4));
    CHECK_SURD("pell_orbit 3", pell_orbit(3), RationalSurd(26,15));
    // Wraps mod 8
    CHECK_SURD("pell_orbit 8 == 0", pell_orbit(8), pell_orbit(0));
    // Negative step wraps correctly
    CHECK_SURD("pell_orbit -1 == 7", pell_orbit(-1), pell_orbit(7));

    // ── DavisGasket construction ──────────────────────────────────────────── //
    {
        DavisGasket g;
        CHECK("gasket: tau starts zero",        g.tau.is_zero());
        CHECK("gasket: K starts unity",         g.K.is_unity());
        CHECK("gasket: henosis_count zero",     g.henosis_count == 0);
        CHECK("gasket: tick_count zero",        g.tick_count == 0);
        CHECK("gasket: is_laminar at start",    g.is_laminar());
    }

    // ── gasket_tick: laminar manifold → no leak ───────────────────────────── //
    {
        DavisGasket g;
        Manifold13 zero;  // all axes zero → vec_sum = zero → no cubic leak
        bool leaked = gasket_tick(g, zero);
        CHECK("tick: zero manifold no leak",    !leaked);
        CHECK("tick: count incremented",        g.tick_count == 1);
        CHECK("tick: henosis not triggered",    g.henosis_count == 0);
    }

    // ── gasket_tick: unbalanced manifold → leak ───────────────────────────── //
    {
        DavisGasket g;
        Manifold13 m;
        m.qr[0] = QR_A;  // single axis → vec_sum != 0 → cubic leak
        bool leaked = gasket_tick(g, m);
        CHECK("tick: single axis leaks",        leaked);
        CHECK("tick: tau accumulated",          !g.tau.is_zero());
        CHECK("tick: henosis_count == 1",       g.henosis_count == 1);
    }

    // ── gasket_tick: tension decays when stable ───────────────────────────── //
    {
        DavisGasket g;
        g.tau = RationalSurd(8, 0);  // seed with non-zero tension
        Manifold13 zero;
        gasket_tick(g, zero);  // stable tick → tau should halve
        CHECK_SURD("tick: tau decays on stable", g.tau, RationalSurd(4, 0));
    }

    // ── henosis_pulse: halves all components ──────────────────────────────── //
    {
        Manifold13 m = Manifold13::canonical();
        // QR[0] = QR_A = (1,0,0,0)
        CHECK("before henosis: QR[0]==QR_A", m.qr[0] == QR_A);
        henosis_pulse(m);
        // (1,0,0,0) >> 1 = (0,0,0,0) → all zeros → normalize → zero
        CHECK("after henosis: QR[0] is zero", m.qr[0].is_zero());
    }
    {
        // Larger values halve correctly
        Manifold13 m;
        m.qr[0] = Quadray{{4,0},{2,0},{0,0},{0,0}};
        henosis_pulse(m);
        // (4,0,2,0,0,0,0,0) >> 1 = (2,0,1,0,0,0,0,0) → min=0 → unchanged
        Quadray expected{{2,0},{1,0},{0,0},{0,0}};
        CHECK("henosis: halves (4,2,0,0) → (2,1,0,0)", m.qr[0] == expected);
    }

    // ── henosis_recover: recovers in bounded steps ────────────────────────── //
    {
        DavisGasket g;
        Manifold13 m;
        m.qr[0] = QR_A;  // single leaking axis
        int pulses = henosis_recover(g, m, 8);
        // After enough halvings, QR_A = (1,0,0,0) → (0,0,0,0) → no leak
        CHECK("recover: terminates",       pulses <= 8);
        CHECK("recover: pulses > 0",       pulses > 0);
        // After recovery, manifold should be laminar (all axes zeroed)
        CHECK("recover: laminar after",    !is_cubic_leak(m));
    }

    // ── Jitterbug: phase names and predicates ─────────────────────────────── //
    {
        JitterbugState js;
        CHECK("jitterbug: starts at VE (phase 0)", js.is_ve());
        CHECK("jitterbug: not icosahedron",         !js.is_icosahedron());
        CHECK("jitterbug: not octahedron",          !js.is_octahedron());
    }

    // ── jitterbug_apply: phase 0 → balanced VE (even/odd same scale) ─────── //
    {
        JitterbugState js;  // phase == 0
        Manifold13 m = jitterbug_apply(js);
        CHECK("jitterbug VE: nucleus is QR_A", m.qr[0] == QR_A);
        // At phase 0: expand=pell(0)=(1,0), contract=pell(7)
        // All IVM_CUBE_12 axes scaled by either (1,0) or pell(7), then normalised
        // Even axes (i=0,2,4,...): scaled by (1,0) → same as IVM_CUBE_12
        CHECK("jitterbug VE: even axis unchanged", m.qr[1] == IVM_CUBE_12[0]);
    }

    // ── jitterbug_step: advances phase ───────────────────────────────────── //
    {
        JitterbugState js;
        jitterbug_step(js, true);
        CHECK_INT("jitterbug_step forward: phase == 1", js.phase, 1);
        jitterbug_step(js, true);
        CHECK_INT("jitterbug_step forward: phase == 2", js.phase, 2);
        CHECK("jitterbug: phase 2 = icosahedron", js.is_icosahedron());
        jitterbug_step(js, true);
        jitterbug_step(js, true);
        CHECK("jitterbug: phase 4 = octahedron", js.is_octahedron());
    }
    // Full 8-step orbit returns to start
    {
        JitterbugState js;
        int start = js.phase;
        for (int i = 0; i < 8; i++) jitterbug_step(js, true);
        CHECK_INT("jitterbug: 8 steps = full orbit", js.phase, start);
    }
    // Step backward undoes step forward
    {
        JitterbugState js;
        jitterbug_step(js, true);
        int after_fwd = js.phase;
        jitterbug_step(js, false);
        CHECK_INT("jitterbug: back undoes forward", js.phase, 0);
        (void)after_fwd;
    }

    // ── jitterbug_phase_fraction ──────────────────────────────────────────── //
    {
        JitterbugState js;
        auto frac = jitterbug_phase_fraction(js);
        CHECK_SURD("phase_frac: phase 0 numer = 0", frac.numer, SURD_ZERO);
        CHECK_SURD("phase_frac: phase 0 denom = 8", frac.denom, RationalSurd(8,0));

        js.phase = 4;  // octahedron
        frac = jitterbug_phase_fraction(js);
        CHECK_SURD("phase_frac: phase 4 numer = 4", frac.numer, RationalSurd(4,0));
    }

    // ── Fibonacci gates ───────────────────────────────────────────────────── //
    CHECK("phi8 gate:  0", !is_phi8_gate(0)  == false);  // cycle 0 is degenerate
    CHECK("phi8 gate:  8", is_phi8_gate(8));
    CHECK("phi8 gate: 16", is_phi8_gate(16));
    CHECK("phi8 gate:  9", !is_phi8_gate(9));
    CHECK("phi13 gate: 13", is_phi13_gate(13));
    CHECK("phi13 gate: 26", is_phi13_gate(26));
    CHECK("phi13 gate: 14", !is_phi13_gate(14));
    CHECK("phi21 gate: 21", is_phi21_gate(21));
    CHECK("phi21 gate: 42", is_phi21_gate(42));
    CHECK("phi21 gate: 22", !is_phi21_gate(22));

    // fibonacci_gate() priority: PHI21 > PHI13 > PHI8
    CHECK("fib_gate:  8  = PHI8",  fibonacci_gate(8)  == FibGate::PHI8);
    CHECK("fib_gate: 13  = PHI13", fibonacci_gate(13) == FibGate::PHI13);
    CHECK("fib_gate: 21  = PHI21", fibonacci_gate(21) == FibGate::PHI21);
    // LCM(8,13)=104 → both PHI8 and PHI13 → PHI13 wins? No, 104%21≠0, so PHI13
    CHECK("fib_gate: 104 = PHI13", fibonacci_gate(104) == FibGate::PHI13);
    // LCM(13,21)=273 → PHI21 wins
    CHECK("fib_gate: 273 = PHI21", fibonacci_gate(273) == FibGate::PHI21);
    CHECK("fib_gate:   7 = NONE",  fibonacci_gate(7)  == FibGate::NONE);

    // ── physics_tick: combined frame ─────────────────────────────────────── //
    {
        DavisGasket g;
        Manifold13 m = Manifold13::ivm_full();
        JitterbugState js;

        // Tick 21 (PHI21 gate): Jitterbug advances
        PhysicsFrame f = physics_tick(g, m, js, 21);
        CHECK("physics_tick: cycle=21",        f.cycle == 21);
        CHECK("physics_tick: gate=PHI21",      f.gate == FibGate::PHI21);
        CHECK_INT("physics_tick: jb advanced", js.phase, 1);

        // IVM full manifold is unbalanced (QR_A nucleus + 12 cube axes)
        CHECK("physics_tick: had_leak",        f.had_leak);

        // Tick 1 (NONE gate): no Jitterbug, no Henosis recovery
        PhysicsFrame f2 = physics_tick(g, m, js, 1);
        CHECK("physics_tick: gate=NONE", f2.gate == FibGate::NONE);
        CHECK_INT("physics_tick: no jb advance", js.phase, 1);
    }

    // ── Jitterbug icosahedron crossover: even/odd at equal Pell weight ────── //
    {
        JitterbugState js;
        js.phase = 2;  // icosahedron
        // At phase 2: expand=pell(2)=(7,4), contract=pell(8-1-2)=pell(5)
        RationalSurd expand   = pell_orbit(2);
        RationalSurd contract = pell_orbit(JITTERBUG_PHASES - 1 - 2);
        // expand = (7,4), contract = pell(5)
        CHECK_SURD("ico: expand at phase 2",   expand,   RationalSurd(7,4));
        CHECK_SURD("ico: contract at phase 2", contract, pell_orbit(5));
        // The crossover is NOT equal scales (that's phase 2 of a different convention)
        // — verify they are distinct
        CHECK("ico: expand != contract at phase 2", expand != contract);
        // Both have norm == 1 (Pell invariant)
        CHECK("ico: expand norm=1",   expand.norm()   == 1);
        CHECK("ico: contract norm=1", contract.norm() == 1);
    }

    // ── Result ────────────────────────────────────────────────────────────── //
    if (failures == 0) {
        printf("PASS\n");
        return 0;
    }
    printf("FAIL (%d failures)\n", failures);
    return 1;
}
