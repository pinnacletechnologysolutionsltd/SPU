// spu_surd_test.cpp — Unit tests for spu_surd.h (Q(√3) arithmetic)
//
// Run:  g++ -std=c++17 -I software/common/include -o build/spu_surd_test \
//           software/common/tests/spu_surd_test.cpp && ./build/spu_surd_test
//
// Prints PASS or FAIL to stdout (compatible with run_all_tests.py).
// CC0 1.0 Universal.

#include "spu_surd.h"
#include <cstdio>
#include <cstdlib>

static int failures = 0;

#define CHECK(label, cond) do { \
    if (!(cond)) { \
        printf("  FAIL: %s\n", label); \
        failures++; \
    } \
} while(0)

#define CHECK_EQ(label, a, b) do { \
    RationalSurd _a = (a), _b = (b); \
    if (_a != _b) { \
        printf("  FAIL: %s  got (%d,%d) expected (%d,%d)\n", \
               label, _a.p, _a.q, _b.p, _b.q); \
        failures++; \
    } \
} while(0)

#define CHECK_I64(label, a, b) do { \
    int64_t _a = (a), _b = (b); \
    if (_a != _b) { \
        printf("  FAIL: %s  got %lld expected %lld\n", \
               label, (long long)_a, (long long)_b); \
        failures++; \
    } \
} while(0)

int main() {
    // ── Addition ──────────────────────────────────────────────────────── //
    CHECK_EQ("add: (1,0)+(0,1)",   RationalSurd(1,0) + RationalSurd(0,1), RationalSurd(1,1));
    CHECK_EQ("add: (2,3)+(-1,2)",  RationalSurd(2,3) + RationalSurd(-1,2), RationalSurd(1,5));
    CHECK_EQ("add: zero identity", RationalSurd(5,7) + SURD_ZERO, RationalSurd(5,7));

    // ── Subtraction ───────────────────────────────────────────────────── //
    CHECK_EQ("sub: (3,2)-(1,1)",   RationalSurd(3,2) - RationalSurd(1,1), RationalSurd(2,1));
    CHECK_EQ("sub: self",          RationalSurd(4,3) - RationalSurd(4,3), SURD_ZERO);

    // ── Negation ──────────────────────────────────────────────────────── //
    CHECK_EQ("neg: -(2,3)",        -RationalSurd(2,3), RationalSurd(-2,-3));
    CHECK_EQ("neg: double neg",    -(-RationalSurd(5,1)), RationalSurd(5,1));

    // ── Multiplication ────────────────────────────────────────────────── //
    // (0,1)*(0,1) = √3·√3 = 3  →  (3,0)
    CHECK_EQ("mul: √3·√3 = 3",     SURD_SQRT3 * SURD_SQRT3, RationalSurd(3,0));

    // (1,0)*s = s  (unity)
    CHECK_EQ("mul: unity left",    SURD_UNITY * RationalSurd(5,3), RationalSurd(5,3));
    CHECK_EQ("mul: unity right",   RationalSurd(5,3) * SURD_UNITY, RationalSurd(5,3));

    // (2,1)*(2,1) = (4+3, 4+2) = (7,4)  — first Pell step squared
    CHECK_EQ("mul: Pell (2,1)²",   SURD_PHI1 * SURD_PHI1, RationalSurd(7,4));

    // (1,1)*(1,1) = (1+3, 1+1) = (4,2)
    CHECK_EQ("mul: (1,1)²",        RationalSurd(1,1) * RationalSurd(1,1), RationalSurd(4,2));

    // Commutativity
    CHECK_EQ("mul: commutative",   RationalSurd(3,2) * RationalSurd(1,4),
                                   RationalSurd(1,4) * RationalSurd(3,2));

    // Distributive: (a+b)*c == a*c + b*c
    {
        RationalSurd a(2,1), b(1,3), c(4,2);
        CHECK_EQ("mul: distributive", (a+b)*c, a*c + b*c);
    }

    // ── Conjugate ─────────────────────────────────────────────────────── //
    CHECK_EQ("conj: (3,2)",        RationalSurd(3,2).conj(), RationalSurd(3,-2));
    CHECK_EQ("conj: neg q",        RationalSurd(1,-5).conj(), RationalSurd(1,5));
    // s + conj(s) = (2p, 0)
    {
        RationalSurd s(4,3);
        CHECK_EQ("conj: s+conj = 2p", s + s.conj(), RationalSurd(8,0));
    }

    // ── Field norm ────────────────────────────────────────────────────── //
    CHECK_I64("norm: (1,0) = 1",   SURD_UNITY.norm(), 1LL);
    CHECK_I64("norm: (0,1) = -3",  SURD_SQRT3.norm(), -3LL);
    CHECK_I64("norm: (2,1) = 1",   SURD_PHI1.norm(),  1LL);   // Pell invariant
    CHECK_I64("norm: (7,4) = 1",   RationalSurd(7,4).norm(),   1LL);
    CHECK_I64("norm: (26,15) = 1", RationalSurd(26,15).norm(), 1LL);

    // norm(a*b) = norm(a)*norm(b)  (multiplicative)
    {
        RationalSurd a(3,1), b(2,2);
        CHECK_I64("norm: multiplicative", (a*b).norm(), a.norm() * b.norm());
    }

    // ── Quadrance ─────────────────────────────────────────────────────── //
    // s.quadrance() = s*s
    CHECK_EQ("quadrance: (1,0)",   SURD_UNITY.quadrance(),    RationalSurd(1,0));
    CHECK_EQ("quadrance: (0,1)",   SURD_SQRT3.quadrance(),    RationalSurd(3,0));  // (√3)²=3
    CHECK_EQ("quadrance: (1,1)",   RationalSurd(1,1).quadrance(), RationalSurd(4,2));
    CHECK_EQ("quadrance: (2,1)",   SURD_PHI1.quadrance(),     RationalSurd(7,4));

    // ── Pell orbit ────────────────────────────────────────────────────── //
    // Sequence: (1,0) → (2,1) → (7,4) → (26,15) → (97,56)
    RationalSurd pell = SURD_UNITY;
    CHECK_EQ("pell: step 0",       pell,              RationalSurd(1,0));
    pell = pell.pell_next();
    CHECK_EQ("pell: step 1",       pell,              RationalSurd(2,1));
    pell = pell.pell_next();
    CHECK_EQ("pell: step 2",       pell,              RationalSurd(7,4));
    pell = pell.pell_next();
    CHECK_EQ("pell: step 3",       pell,              RationalSurd(26,15));
    pell = pell.pell_next();
    CHECK_EQ("pell: step 4",       pell,              RationalSurd(97,56));

    // All Pell steps must have norm == 1
    pell = SURD_UNITY;
    for (int i = 0; i < 8; i++) {
        CHECK_I64("pell: norm==1 at each step", pell.norm(), 1LL);
        pell = pell.pell_next();
    }

    // ── Zero and unity predicates ─────────────────────────────────────── //
    CHECK("is_zero: (0,0)",        SURD_ZERO.is_zero());
    CHECK("is_zero: false (1,0)",  !SURD_UNITY.is_zero());
    CHECK("is_unity: (1,0)",       SURD_UNITY.is_unity());
    CHECK("is_unity: false (2,0)", !RationalSurd(2,0).is_unity());

    // ── Additive inverse ──────────────────────────────────────────────── //
    {
        RationalSurd s(5, -3);
        CHECK_EQ("additive inverse", s + (-s), SURD_ZERO);
    }

    // ── Result ────────────────────────────────────────────────────────── //
    if (failures == 0) {
        printf("PASS\n");
        return 0;
    } else {
        printf("FAIL (%d failures)\n", failures);
        return 1;
    }
}
