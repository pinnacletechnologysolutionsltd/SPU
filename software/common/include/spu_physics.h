// spu_physics.h — Davis Law gasket + Jitterbug morph for the SPU-13 software stack
//
// Builds on spu_ivm.h (Manifold13, is_cubic_leak, laminar_weight).
//
// The three physics primitives:
//
//   DavisGasket   — tracks manifold tension τ, stiffness K, leak history
//   gasket_tick() — one Davis Gate cycle: check leak, update τ, return Henosis flag
//   henosis_pulse() — soft recovery: halve each axis component toward VE zero-point
//                     (matches ANNE opcode in spu_vm.py — bit-shift by 1)
//
// The Jitterbug morph (Fuller's VE ↔ Icosahedron ↔ Octahedron):
//
//   JitterbugState — current phase (0=VE, 4=Icosahedron, 8=Octahedron)
//   jitterbug_step() — advance one Pell phase step (expand or contract)
//   jitterbug_phase() — current phase as RationalSurd fraction [0..1]
//
// Key design decisions:
//   - Tension τ accumulates as RationalSurd (quadrance of vec_sum)
//   - Stiffness K is fixed externally (hardware parameter, e.g. (1,0) = unity)
//   - Henosis = ANNE opcode: component >>1 (exact integer halving, no rounding)
//   - Jitterbug uses Pell orbit: even axes expand, odd axes contract per phase step
//   - Phase wraps modulo 8 (Pell octave: 8 steps before magnitudes repeat)
//   - No floating point. No division. No transcendental functions.
//
// CC0 1.0 Universal.

#pragma once
#include "spu_ivm.h"

// ── DavisGasket ───────────────────────────────────────────────────────────── //

struct DavisGasket {
    RationalSurd tau;          // accumulated manifold tension (quadrance of vec_sum)
    RationalSurd K;            // stiffness constant (default: unity)
    uint32_t     henosis_count = 0;  // soft recoveries triggered so far
    uint32_t     tick_count    = 0;  // total gasket ticks
    bool         leak          = false;  // cubic leak flag from last tick

    DavisGasket() : tau{0,0}, K{1,0} {}
    explicit DavisGasket(const RationalSurd& stiffness) : tau{0,0}, K(stiffness) {}

    // Davis Ratio in cross-multiply form: τ × K
    // To compare two ratios: cross-multiply (no division needed).
    RationalSurd ratio_product() const { return tau * K; }

    // Is the manifold laminar this tick?
    bool is_laminar() const { return !leak; }
};

// ── Gasket tick ───────────────────────────────────────────────────────────── //

// One Davis Gate cycle. Updates gasket state from the current manifold.
// Returns true if a Cubic Leak was detected (Henosis needed).
//
// Tension model:
//   - Leak:    τ ← τ + quadrance(vec_sum)  (tension accumulates)
//   - No leak: τ ← τ × (1,0) halved next ANNE — kept for caller to decay
//
// Matches the SNAP opcode in spu_vm.py: checks all axes, sets snap_failures.
inline bool gasket_tick(DavisGasket& g, const Manifold13& m) {
    g.tick_count++;
    g.leak = is_cubic_leak(m);
    if (g.leak) {
        // Accumulate tension: how far off-balance is the manifold?
        Quadray vs = manifold_vec_sum(m);
        g.tau = g.tau + vs.quadrance();
        g.henosis_count++;
    } else {
        // Decay tension by one Pell inverse step when stable
        // (Pell conj of (2,1) is (2,-1); multiplying by it reduces norm)
        // Simple approach: halve τ each stable tick (integer right-shift)
        g.tau = RationalSurd(g.tau.p >> 1, g.tau.q >> 1);
    }
    return g.leak;
}

// ── Henosis pulse ─────────────────────────────────────────────────────────── //

// Soft manifold recovery: halve each component of every axis.
// Models the IVM lattice relaxation toward the VE zero-point.
// Matches the ANNE opcode in spu_vm.py: component >>1.
// Exact integer halving — no rounding, no float.
// After henosis_pulse(), re-run gasket_tick() to check recovery.
inline void henosis_pulse(Manifold13& m) {
    for (int i = 0; i < Manifold13::AXES; i++) {
        Quadray& q = m.qr[i];
        q = Quadray {
            RationalSurd(q.a.p >> 1, q.a.q >> 1),
            RationalSurd(q.b.p >> 1, q.b.q >> 1),
            RationalSurd(q.c.p >> 1, q.c.q >> 1),
            RationalSurd(q.d.p >> 1, q.d.q >> 1),
        }.normalize();
    }
}

// Full recovery cycle: pulse until laminar or max_pulses reached.
// Returns the number of pulses applied. 0 = already laminar.
inline int henosis_recover(DavisGasket& g, Manifold13& m, int max_pulses = 8) {
    int pulses = 0;
    while (pulses < max_pulses && gasket_tick(g, m)) {
        henosis_pulse(m);
        pulses++;
    }
    return pulses;
}

// ── Jitterbug morph ───────────────────────────────────────────────────────── //
//
// Fuller's Jitterbug: the continuous transformation of the Vector Equilibrium
// (cuboctahedron, 12 vertices) through the Icosahedron to the Octahedron (6
// vertices), and back.
//
// Q(√3) formulation:
//   - EXPAND axes: even-indexed QR[0,2,4,...10] scale by pell_orbit[phase]
//   - CONTRACT axes: odd-indexed QR[1,3,5,...11] scale by pell_orbit[7-phase]
//                    (counts down as expand counts up)
//   - QR[12] (nucleus): always QR_A (unchanged)
//
// Phase table (Pell orbit, 8 steps):
//   phase 0: expand=(1,0)  contract=(97,56) — VE: both at same scale → balanced
//   phase 1: expand=(2,1)  contract=(26,15)
//   phase 2: expand=(7,4)  contract=(7,4)   — Icosahedron crossover point
//   phase 3: expand=(26,15) contract=(2,1)
//   phase 4: expand=(97,56) contract=(1,0)  — Octahedron: odd axes at min scale
//   (phase 5-7: same orbit in reverse for full cycle back to VE)
//
// The crossover at phase==2 is the Icosahedron: both rings have equal Pell weight.

constexpr int JITTERBUG_PHASES = 8;

// Pre-computed Pell orbit for phases 0..7
inline RationalSurd pell_orbit(int step) {
    // Clamp to 0..7
    step = ((step % 8) + 8) % 8;
    RationalSurd s {1, 0};
    for (int i = 0; i < step; i++) s = s.pell_next();
    return s;
}

struct JitterbugState {
    int phase = 0;  // 0=VE, 2=Icosahedron, 4=Octahedron, wraps mod 8
    bool expanding = true;  // direction of morph

    // Named phase checks
    bool is_ve()          const { return phase == 0; }
    bool is_icosahedron() const { return phase == 2; }
    bool is_octahedron()  const { return phase == 4; }

    const char* phase_name() const {
        switch (phase) {
            case 0: return "VE (Vector Equilibrium)";
            case 1: return "pre-icosahedron";
            case 2: return "Icosahedron";
            case 3: return "post-icosahedron";
            case 4: return "Octahedron";
            case 5: return "post-octahedron";
            case 6: return "re-icosahedron";
            case 7: return "pre-VE";
            default: return "?";
        }
    }
};

// Apply the current Jitterbug phase to a manifold built from IVM_CUBE_12.
// QR[0] = nucleus (unchanged). QR[1..12] = 12 cuboctahedral axes split
// into even/odd rings that expand and contract in opposing Pell steps.
inline Manifold13 jitterbug_apply(const JitterbugState& js) {
    Manifold13 m;
    m.qr[0] = QR_A;  // nucleus fixed

    RationalSurd expand   = pell_orbit(js.phase);
    RationalSurd contract = pell_orbit(JITTERBUG_PHASES - 1 - js.phase);

    for (int i = 0; i < 12; i++) {
        const RationalSurd& scale = (i % 2 == 0) ? expand : contract;
        m.qr[i + 1] = IVM_CUBE_12[i].scale(scale).normalize();
    }
    return m;
}

// Step the Jitterbug forward (expand) or backward (contract) by one Pell phase.
// Returns the new manifold state.
inline Manifold13 jitterbug_step(JitterbugState& js, bool forward = true) {
    if (forward) {
        js.phase = (js.phase + 1) % JITTERBUG_PHASES;
    } else {
        js.phase = (js.phase + JITTERBUG_PHASES - 1) % JITTERBUG_PHASES;
    }
    return jitterbug_apply(js);
}

// Phase as a rational fraction [0..1): phase/8 as (phase, 8) pair.
inline WeightFraction jitterbug_phase_fraction(const JitterbugState& js) {
    return { RationalSurd(js.phase, 0), RationalSurd(JITTERBUG_PHASES, 0) };
}

// ── Fibonacci dispatch gates ──────────────────────────────────────────────── //
// The SPU-13 dispatches instructions at Fibonacci intervals (8, 13, 21 cycles).
// These predicates check whether a given cycle count is a dispatch gate.

inline bool is_phi8_gate(uint32_t cycle)  { return (cycle % 8)  == 0; }
inline bool is_phi13_gate(uint32_t cycle) { return (cycle % 13) == 0; }
inline bool is_phi21_gate(uint32_t cycle) { return (cycle % 21) == 0; }

// Combined gate: true on phi_8 (micro), phi_13 (meso), phi_21 (macro) cycles.
enum class FibGate { NONE, PHI8, PHI13, PHI21 };

inline FibGate fibonacci_gate(uint32_t cycle) {
    if (cycle == 0) return FibGate::NONE;
    if (is_phi21_gate(cycle)) return FibGate::PHI21;   // coarsest wins
    if (is_phi13_gate(cycle)) return FibGate::PHI13;
    if (is_phi8_gate(cycle))  return FibGate::PHI8;
    return FibGate::NONE;
}

inline const char* fib_gate_name(FibGate g) {
    switch (g) {
        case FibGate::PHI8:  return "φ₈  (micro)";
        case FibGate::PHI13: return "φ₁₃ (meso)";
        case FibGate::PHI21: return "φ₂₁ (macro)";
        default:             return "—";
    }
}

// ── Physics tick (combined) ───────────────────────────────────────────────── //
// One complete physics frame: gasket check, optional Jitterbug step, optional
// Henosis recovery. Called once per Fibonacci gate cycle.
//
// Returns true if the frame is stable (no cubic leak after recovery).
struct PhysicsFrame {
    uint32_t     cycle;
    FibGate      gate;
    bool         had_leak;
    int          henosis_pulses;
    RationalSurd tau_after;
};

inline PhysicsFrame physics_tick(DavisGasket& g, Manifold13& m,
                                  JitterbugState& js, uint32_t cycle) {
    PhysicsFrame f;
    f.cycle  = cycle;
    f.gate   = fibonacci_gate(cycle);

    // Advance Jitterbug on macro gate (φ₂₁)
    if (f.gate == FibGate::PHI21)
        jitterbug_step(js, true);

    // Davis Gate check + optional Henosis recovery
    f.had_leak = gasket_tick(g, m);
    f.henosis_pulses = 0;

    if (f.had_leak && f.gate >= FibGate::PHI13) {
        // Meso/macro gate: attempt recovery
        f.henosis_pulses = henosis_recover(g, m, /*max_pulses=*/3);
    }

    f.tau_after = g.tau;
    return f;
}
