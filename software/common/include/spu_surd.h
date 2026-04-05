// spu_surd.h — Q(√3) rational surd arithmetic for the SPU-13 software stack
//
// An element of Q(√3) is a value p + q·√3 where p, q are integers.
// This field is closed under addition and multiplication — no irrationals
// are ever introduced. Division is not provided (never needed in IVM geometry).
//
// Hardware correspondence: the RTL RationalSurd packs (p:int16, q:int16) into
// a 32-bit word. This C++ layer uses int32_t for overflow headroom in
// intermediate calculations. Values fed to the FPGA must fit in int16_t.
//
// Key identities:
//   (p + q√3) + (p' + q'√3) = (p+p') + (q+q')√3
//   (p + q√3) × (p' + q'√3) = (pp' + 3qq') + (pq' + p'q)√3
//   conj(p + q√3)            = p - q√3
//   norm(s)                  = s × conj(s) = p² - 3q²  (rational integer)
//   pell_next(p, q)          = (2p + 3q, p + 2q)       (Pell orbit step)
//
// Pell invariant: if norm(s) == 1 then norm(pell_next(s)) == 1.
// This is the algebraic guarantee behind bit-exact rotor composition.
//
// CC0 1.0 Universal.

#pragma once
#include <cstdint>
#include <cstdio>

struct RationalSurd {
    int32_t p;  // rational part  (coefficient of 1)
    int32_t q;  // surd part      (coefficient of √3)

    constexpr RationalSurd(int32_t p_ = 0, int32_t q_ = 0) : p(p_), q(q_) {}

    // ── Arithmetic ──────────────────────────────────────────────────────── //

    constexpr RationalSurd operator+(const RationalSurd& o) const {
        return { p + o.p, q + o.q };
    }
    constexpr RationalSurd operator-(const RationalSurd& o) const {
        return { p - o.p, q - o.q };
    }
    constexpr RationalSurd operator-() const {
        return { -p, -q };
    }

    // Field multiplication in Q(√3):
    //   (p + q√3)(p' + q'√3) = (pp' + 3qq') + (pq' + p'q)√3
    constexpr RationalSurd operator*(const RationalSurd& o) const {
        return { p*o.p + 3*q*o.q,  p*o.q + q*o.p };
    }

    constexpr RationalSurd& operator+=(const RationalSurd& o) { *this = *this + o; return *this; }
    constexpr RationalSurd& operator-=(const RationalSurd& o) { *this = *this - o; return *this; }
    constexpr RationalSurd& operator*=(const RationalSurd& o) { *this = *this * o; return *this; }

    // ── Comparison ──────────────────────────────────────────────────────── //

    constexpr bool operator==(const RationalSurd& o) const { return p == o.p && q == o.q; }
    constexpr bool operator!=(const RationalSurd& o) const { return !(*this == o); }
    constexpr bool is_zero()  const { return p == 0 && q == 0; }
    constexpr bool is_unity() const { return p == 1 && q == 0; }

    // ── Field operations ────────────────────────────────────────────────── //

    // Conjugate: p - q√3
    constexpr RationalSurd conj() const { return { p, -q }; }

    // Field norm: s × conj(s) = p² - 3q²
    // Returns a rational integer. Negative values are valid (field norm ≠ length).
    // Pell rotors always have norm == 1.
    constexpr int64_t norm() const {
        return (int64_t)p*p - 3*(int64_t)q*q;
    }

    // Quadrance (squared value): s × s = (p² + 3q²) + 2pq·√3
    // This is the "Davis Quadrance" — always non-negative real component.
    constexpr RationalSurd quadrance() const { return *this * *this; }

    // ── Pell orbit ──────────────────────────────────────────────────────── //

    // Advance to next step on the Pell orbit a² - 3b² = 1.
    // Sequence: (1,0) → (2,1) → (7,4) → (26,15) → (97,56) → …
    // Each step is a rational rotation by the fundamental angle of Q(√3).
    constexpr RationalSurd pell_next() const {
        return { 2*p + 3*q,  p + 2*q };
    }

    // ── Display ─────────────────────────────────────────────────────────── //

    // For display/debug only — never use this result in arithmetic.
    double to_double() const {
        return (double)p + (double)q * 1.7320508075688772; // √3
    }

    void print(const char* label = nullptr) const {
        if (label) printf("%s: ", label);
        if (q == 0)       printf("(%d)", p);
        else if (p == 0)  printf("(%d·√3)", q);
        else if (q > 0)   printf("(%d + %d·√3)", p, q);
        else              printf("(%d - %d·√3)", p, -q);
        printf("  ≈ %.6f\n", to_double());
    }
};

// ── Convenience constants ─────────────────────────────────────────────── //

constexpr RationalSurd SURD_ZERO  { 0, 0 };
constexpr RationalSurd SURD_UNITY { 1, 0 };
constexpr RationalSurd SURD_SQRT3 { 0, 1 };  // √3 itself
constexpr RationalSurd SURD_PHI1  { 2, 1 };  // first non-trivial Pell rotor
