// spu_quadray_test.cpp — Unit tests for spu_quadray.h (IVM Quadray arithmetic)
//
// Run:  g++ -std=c++17 -I software/common/include -o build/spu_quadray_test \
//           software/common/tests/spu_quadray_test.cpp && ./build/spu_quadray_test
//
// CC0 1.0 Universal.

#include "spu_quadray.h"
#include <cstdio>

static int failures = 0;

#define CHECK(label, cond) do { \
    if (!(cond)) { printf("  FAIL: %s\n", label); failures++; } \
} while(0)

#define CHECK_EQ(label, got, want) do { \
    Quadray _g=(got), _w=(want); \
    if (_g != _w) { \
        printf("  FAIL: %s\n  got  [(%d,%d)(%d,%d)(%d,%d)(%d,%d)]\n  want [(%d,%d)(%d,%d)(%d,%d)(%d,%d)]\n", \
               label, \
               _g.a.p,_g.a.q, _g.b.p,_g.b.q, _g.c.p,_g.c.q, _g.d.p,_g.d.q, \
               _w.a.p,_w.a.q, _w.b.p,_w.b.q, _w.c.p,_w.c.q, _w.d.p,_w.d.q); \
        failures++; \
    } \
} while(0)

#define CHECK_SURD(label, a, b) do { \
    RationalSurd _a=(a), _b=(b); \
    if (_a != _b) { \
        printf("  FAIL: %s  got (%d,%d) expected (%d,%d)\n", label, _a.p,_a.q,_b.p,_b.q); \
        failures++; \
    } \
} while(0)

static Quadray Q(int ap, int aq, int bp, int bq,
                  int cp, int cq, int dp, int dq) {
    return { {ap,aq},{bp,bq},{cp,cq},{dp,dq} };
}

int main() {

    // ── Exact ordering (rs_lt / rs_min) ──────────────────────────────────── //
    CHECK("rs_lt: 0 < 1",           rs_lt({0,0}, {1,0}));
    CHECK("rs_lt: -1 < 0",          rs_lt({-1,0}, {0,0}));
    CHECK("rs_lt: equal false",     !rs_lt({2,1}, {2,1}));
    // (0,1) = √3 ≈ 1.732, (2,0) = 2 → √3 < 2
    CHECK("rs_lt: √3 < 2",          rs_lt({0,1}, {2,0}));
    // (0,2) = 2√3 ≈ 3.46, (3,0) = 3 → 3 < 2√3
    CHECK("rs_lt: 3 < 2√3",         rs_lt({3,0}, {0,2}));

    CHECK_SURD("rs_min: picks -1 over 0", rs_min({-1,0},{0,0}), RationalSurd(-1,0));
    CHECK_SURD("rs_min4: picks zero",
        rs_min4({1,0},{0,0},{2,0},{3,0}), RationalSurd(0,0));
    CHECK_SURD("rs_min4: mixed surd",
        rs_min4({0,1},{2,0},{1,0},{3,0}), RationalSurd(1,0));  // √3 > 1

    // ── Construction & equality ───────────────────────────────────────────── //
    CHECK("QR_A == QR_A",           QR_A == QR_A);
    CHECK("QR_A != QR_B",           QR_A != QR_B);
    CHECK("QR_ZERO is_zero",        QR_ZERO.is_zero());
    CHECK("QR_A not is_zero",       !QR_A.is_zero());

    // ── Addition ─────────────────────────────────────────────────────────── //
    CHECK_EQ("add: A+B",            QR_A + QR_B, Q(1,0,1,0,0,0,0,0));
    CHECK_EQ("add: zero identity",  QR_A + QR_ZERO, QR_A);
    // Component-wise
    CHECK_EQ("add: surd comps",
        Q(1,1,0,0,0,0,0,0) + Q(0,0,1,1,0,0,0,0),
        Q(1,1,1,1,0,0,0,0));

    // ── Subtraction ──────────────────────────────────────────────────────── //
    CHECK_EQ("sub: A-A = zero",     QR_A - QR_A, QR_ZERO);

    // ── Scale ────────────────────────────────────────────────────────────── //
    CHECK_EQ("scale: by 2",         QR_A.scale({2,0}), Q(2,0,0,0,0,0,0,0));
    CHECK_EQ("scale: by SURD_PHI1", QR_A.scale(SURD_PHI1), Q(2,1,0,0,0,0,0,0));

    // ── Normalisation ────────────────────────────────────────────────────── //
    // (2,0,0,0) → min=0, unchanged
    CHECK_EQ("normalize: already canonical",
        Q(2,0,0,0,0,0,0,0).normalize(), Q(2,0,0,0,0,0,0,0));
    // (2,1,1,1) → min=1, subtract → (1,0,0,0)
    CHECK_EQ("normalize: (2,1,1,1) → (1,0,0,0)",
        Q(2,0,1,0,1,0,1,0).normalize(), Q(1,0,0,0,0,0,0,0));
    // (-1,0,0,0) → min=-1, subtract → (0,1,1,1)
    CHECK_EQ("normalize: (-1,0,0,0) → (0,1,1,1)",
        Q(-1,0,0,0,0,0,0,0).normalize(), Q(0,0,1,0,1,0,1,0));
    // QR_A..D are already canonical
    CHECK_EQ("normalize: QR_A canonical", QR_A.normalize(), QR_A);

    // ── Quadrance ────────────────────────────────────────────────────────── //
    // Q((1,0,0,0)) = (1-0)²+(1-0)²+(1-0)²+0+0+0 = 3
    CHECK_SURD("quadrance: QR_A = 3", QR_A.quadrance(), RationalSurd(3,0));
    CHECK_SURD("quadrance: QR_B = 3", QR_B.quadrance(), RationalSurd(3,0));
    // Q((1,1,0,0)) = 0+1+1+1+1+0 = 4
    CHECK_SURD("quadrance: (1,1,0,0) = 4",
        (QR_A + QR_B).quadrance(), RationalSurd(4,0));
    // Q(ZERO) = 0
    CHECK_SURD("quadrance: zero = 0", QR_ZERO.quadrance(), SURD_ZERO);
    // All 12 IVM cube vectors have Q=8
    for (int i = 0; i < 12; i++) {
        if (IVM_CUBE_12[i].quadrance() != RationalSurd(8,0)) {
            printf("  FAIL: IVM_CUBE_12[%d] quadrance != 8  got (%d,%d)\n",
                   i, IVM_CUBE_12[i].quadrance().p, IVM_CUBE_12[i].quadrance().q);
            failures++;
        }
    }
    // All 6 face vectors have Q=4
    for (int i = 0; i < 6; i++) {
        if (IVM_FACE_6[i].quadrance() != RationalSurd(4,0)) {
            printf("  FAIL: IVM_FACE_6[%d] quadrance != 4  got (%d,%d)\n",
                   i, IVM_FACE_6[i].quadrance().p, IVM_FACE_6[i].quadrance().q);
            failures++;
        }
    }

    // ── Dot product ──────────────────────────────────────────────────────── //
    // A·A = 1+0+0+0 = 1
    CHECK_SURD("dot: A·A = 1", QR_A.dot(QR_A), SURD_UNITY);
    // A·B = 0
    CHECK_SURD("dot: A·B = 0", QR_A.dot(QR_B), SURD_ZERO);
    // (1,1,0,0)·(1,1,0,0) = 1+1+0+0 = 2
    CHECK_SURD("dot: (1,1,0,0)·self = 2",
        (QR_A+QR_B).dot(QR_A+QR_B), RationalSurd(2,0));

    // ── Spread ───────────────────────────────────────────────────────────── //
    // spread(A,A): numer = Q(A)*Q(A) - (A·A)² = 9-1 = 8, denom = 9
    // (Component-wise dot ≠ Euclidean inner product in Quadray metric;
    //  this matches spu_vm.py exactly.)
    {
        auto s = QR_A.spread(QR_A);
        CHECK_SURD("spread: A vs A numer=(8,0)", s.numer, RationalSurd(8,0));
        CHECK_SURD("spread: A vs A denom=(9,0)", s.denom, RationalSurd(9,0));
    }
    // spread of zero vector: denom == 0
    {
        auto s = QR_ZERO.spread(QR_A);
        CHECK_SURD("spread: zero vs A denom=0", s.denom, SURD_ZERO);
    }
    // spread(A,B): non-zero numer, symmetric
    {
        auto sAB = QR_A.spread(QR_B);
        auto sBA = QR_B.spread(QR_A);
        CHECK_SURD("spread: A vs B symmetric numer", sAB.numer, sBA.numer);
        CHECK_SURD("spread: A vs B symmetric denom", sAB.denom, sBA.denom);
    }

    // ── Cycle ────────────────────────────────────────────────────────────── //
    // cycle() maps (a,b,c,d) → (b,c,d,a), so the non-zero slot shifts right:
    // A=(1,0,0,0) → (0,0,0,1)=D, D=(0,0,0,1) → (0,0,1,0)=C,
    // C=(0,0,1,0) → (0,1,0,0)=B, B=(0,1,0,0) → (1,0,0,0)=A
    CHECK_EQ("cycle: A→D",  QR_A.cycle(), QR_D);
    CHECK_EQ("cycle: D→C",  QR_D.cycle(), QR_C);
    CHECK_EQ("cycle: C→B",  QR_C.cycle(), QR_B);
    CHECK_EQ("cycle: B→A",  QR_B.cycle(), QR_A);
    CHECK_EQ("cycle: 4× = identity",
        QR_A.cycle().cycle().cycle().cycle(), QR_A);

    // ── Pell rotate ──────────────────────────────────────────────────────── //
    // pell_rotate() = scale by (2,1) then normalize.
    // QR_A = (1,0,0,0). Scale by (2,1): (2,1,0,0,0,0,0,0). Min=0 → unchanged.
    CHECK_EQ("pell_rotate: QR_A step 1",
        QR_A.pell_rotate(), Q(2,1,0,0,0,0,0,0));
    // Second step: (2,1)·(2,1) = (7,4)
    CHECK_EQ("pell_rotate: QR_A step 2",
        QR_A.pell_rotate().pell_rotate(), Q(7,4,0,0,0,0,0,0));
    // pell_rotate and cycle commute:
    // cycle(pell_rotate(A)) == pell_rotate(cycle(A))
    CHECK_EQ("pell_rotate commutes with cycle",
        QR_A.pell_rotate().cycle(), QR_A.cycle().pell_rotate());

    // ── Hex projection ───────────────────────────────────────────────────── //
    // QR_A = (1,0,0,0), d_off=0, col=1, row=0
    {
        auto hx = QR_A.hex_project();
        CHECK("hex: QR_A col=1", hx.col == 1);
        CHECK("hex: QR_A row=0", hx.row == 0);
    }
    // QR_B = (0,1,0,0), d_off=0, col=0, row=1
    {
        auto hx = QR_B.hex_project();
        CHECK("hex: QR_B col=0", hx.col == 0);
        CHECK("hex: QR_B row=1", hx.row == 1);
    }
    // QR_D = (0,0,0,1), d_off=1, col=-1, row=-1
    {
        auto hx = QR_D.hex_project();
        CHECK("hex: QR_D col=-1", hx.col == -1);
        CHECK("hex: QR_D row=-1", hx.row == -1);
    }
    // ZERO → (0,0)
    {
        auto hx = QR_ZERO.hex_project();
        CHECK("hex: zero col=0", hx.col == 0);
        CHECK("hex: zero row=0", hx.row == 0);
    }

    // ── IVM_CUBE_12: all 12 distinct vectors ─────────────────────────────── //
    for (int i = 0; i < 12; i++)
        for (int j = i+1; j < 12; j++) {
            if (IVM_CUBE_12[i] == IVM_CUBE_12[j]) {
                printf("  FAIL: IVM_CUBE_12[%d] == IVM_CUBE_12[%d] (duplicates)\n", i, j);
                failures++;
            }
        }

    // ── Result ───────────────────────────────────────────────────────────── //
    if (failures == 0) {
        printf("PASS\n");
        return 0;
    }
    printf("FAIL (%d failures)\n", failures);
    return 1;
}
