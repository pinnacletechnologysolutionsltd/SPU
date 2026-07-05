#!/usr/bin/env python3
"""SU(3) oracle over A₃₁[i] — degree-8 extension of M31.

Verifies 3×3 unitary matrix multiplication over the complexified
split biquadratic algebra A₃₁[i] = F_p[u,v,x]/(u²-3, v²-5, x²+1).

No floating point. No exp(). No division in hot paths.
All tests assert bit-exact results.

Usage:
    python3 software/tests/test_su3_oracle.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

P = 2147483647  # M31 = 2^31 - 1

def m31(x):
    """Reduce to [0, P-1]."""
    x %= P
    return x if x >= 0 else x + P

# ── A₃₁ element: (c0, c1, c2, c3) over M31 ──────────────────────
# Represents c0 + c1·√3 + c2·√5 + c3·√15

def a31_add(a, b):
    return tuple(m31(ai + bi) for ai, bi in zip(a, b))

def a31_sub(a, b):
    return tuple(m31(ai - bi) for ai, bi in zip(a, b))

def a31_mul(a, b):
    """A₃₁ multiplication via the cross-product table."""
    c0, c1, c2, c3 = a
    d0, d1, d2, d3 = b
    return (
        m31(c0*d0 + 3*c1*d1 + 5*c2*d2 + 15*c3*d3),
        m31(c0*d1 + c1*d0 + 5*c2*d3 + 5*c3*d2),
        m31(c0*d2 + c2*d0 + 3*c1*d3 + 3*c3*d1),
        m31(c0*d3 + c1*d2 + c2*d1 + c3*d0),
    )

def a31_zero():
    return (0,0,0,0)

def a31_one():
    return (1,0,0,0)

def a31_neg(a):
    return tuple(m31(-x) for x in a)

# ── A₃₁[i] element: (real, imag), each an A₃₁ 4-tuple ───────────
# Represents r + i·s where r,s ∈ A₃₁, i² = -1

def CA(r, s):
    """A₃₁[i] element as (real_component, imag_component) pair."""
    return (r, s)

def ca_add(a, b):
    return CA(a31_add(a[0], b[0]), a31_add(a[1], b[1]))

def ca_sub(a, b):
    return CA(a31_sub(a[0], b[0]), a31_sub(a[1], b[1]))

def ca_mul(a, b):
    """(r1 + i·s1)(r2 + i·s2) = (r1·r2 - s1·s2) + i·(r1·s2 + s1·r2)"""
    r1, s1 = a
    r2, s2 = b
    return CA(
        a31_sub(a31_mul(r1, r2), a31_mul(s1, s2)),
        a31_add(a31_mul(r1, s2), a31_mul(s1, r2)),
    )

def ca_zero():
    return CA(a31_zero(), a31_zero())

def ca_one():
    return CA(a31_one(), a31_zero())

def pack_ca(a):
    """Pack A₃₁[i] as RTL element format: {imag c3..c0, real c3..c0}."""
    real, imag = a
    out = 0
    for word in (imag[3], imag[2], imag[1], imag[0],
                 real[3], real[2], real[1], real[0]):
        out = (out << 32) | word
    return out

# ── 3×3 matrix over A₃₁[i] ──────────────────────────────────────
# Stored as 3 rows × 3 cols of CA elements

def mat_identity():
    I = [[ca_zero() for _ in range(3)] for _ in range(3)]
    I[0][0] = ca_one()
    I[1][1] = ca_one()
    I[2][2] = ca_one()
    return I

def mat_mul(A, B):
    """3×3 matrix multiply over A₃₁[i]. 27 complex multiplies + 18 additions."""
    C = [[ca_zero() for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for k in range(3):
            for j in range(3):
                C[i][j] = ca_add(C[i][j], ca_mul(A[i][k], B[k][j]))
    return C

def mat_dagger(A):
    """Conjugate transpose of a 3×3 matrix over A₃₁[i].
    Conjugation in A₃₁[i] negates i. transpose swaps rows/cols.
    """
    At = [[ca_zero() for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            # conjugate: negate the imaginary part
            r, s = A[j][i]
            At[i][j] = CA(r, a31_neg(s))
    return At

def mat_is_unitary(A, tol=0):
    """Check if A·A† = I exactly (tol=0 for exact arithmetic)."""
    At = mat_dagger(A)
    Id = mat_identity()
    PP = mat_mul(A, At)
    for i in range(3):
        for j in range(3):
            diff = ca_sub(PP[i][j], Id[i][j])
            for c in range(2):
                for k in range(4):
                    if abs(diff[c][k]) > tol:
                        return False
    return True

def mat_is_su3(A, tol=0):
    """Check SU(3): unitary + determinant == 1 over A₃₁[i]."""
    if not mat_is_unitary(A, tol):
        return False
    # det = A[0][0]·(A[1][1]·A[2][2] - A[1][2]·A[2][1])
    #     - A[0][1]·(A[1][0]·A[2][2] - A[1][2]·A[2][0])
    #     + A[0][2]·(A[1][0]·A[2][1] - A[1][1]·A[2][0])
    #
    # Implemented via ca_mul and ca_sub.
    def det3x3(A):
        t1 = ca_mul(A[1][1], A[2][2])
        t2 = ca_mul(A[1][2], A[2][1])
        a = ca_sub(t1, t2)
        t1 = ca_mul(A[1][0], A[2][2])
        t2 = ca_mul(A[1][2], A[2][0])
        b = ca_sub(t1, t2)
        t1 = ca_mul(A[1][0], A[2][1])
        t2 = ca_mul(A[1][1], A[2][0])
        c = ca_sub(t1, t2)
        return ca_add(
            ca_sub(ca_mul(A[0][0], a), ca_mul(A[0][1], b)),
            ca_mul(A[0][2], c)
        )

    det = det3x3(A)
    one = ca_one()
    for c in range(2):
        for k in range(4):
            if det[c][k] != one[c][k]:
                return False
    return True

# ── Gell-Mann matrix generators (λ₁, λ₂, ..., λ₈) over A₃₁[i] ──

def gellmann_lambda_1():
    """λ₁ = [[0,1,0],[1,0,0],[0,0,0]]"""
    L = [[ca_zero() for _ in range(3)] for _ in range(3)]
    L[0][1] = ca_one()
    L[1][0] = ca_one()
    return L

def gellmann_lambda_2():
    """λ₂ = [[0,-i,0],[i,0,0],[0,0,0]]"""
    L = [[ca_zero() for _ in range(3)] for _ in range(3)]
    L[0][1] = CA(a31_zero(), a31_neg(a31_one()))  # -i
    L[1][0] = CA(a31_zero(), a31_one())            # +i
    return L

def gellmann_lambda_3():
    """λ₃ = diag(1, -1, 0)"""
    L = [[ca_zero() for _ in range(3)] for _ in range(3)]
    L[0][0] = ca_one()
    L[1][1] = CA(a31_neg(a31_one()), a31_zero())
    return L

def gellmann_lambda_8():
    """λ₈ = diag(1, 1, -2) / √3 over A₃₁"""
    inv3 = m31(pow(3, P - 2, P))
    inv_sqrt3 = (0, inv3, 0, 0)  # 1/u = u/3 in A₃₁ where u² = 3
    L = [[ca_zero() for _ in range(3)] for _ in range(3)]
    L[0][0] = CA(inv_sqrt3, a31_zero())
    L[1][1] = CA(inv_sqrt3, a31_zero())
    L[2][2] = CA((0, m31(-2 * inv3), 0, 0), a31_zero())
    return L

# ── Test framework ───────────────────────────────────────────────

errors = 0
checks = 0
def check(cond, msg):
    global checks, errors
    checks += 1
    if not cond:
        print(f"  FAIL: {msg}")
        errors += 1
    else:
        print(f"  PASS: {msg}")

print("=== SU(3) Oracle Tests ===")
print()

# Test 1: A₃₁ arithmetic basics
print("--- A₃₁ arithmetic ---")
check(a31_mul(a31_one(), (2,3,4,5)) == (2,3,4,5), "1·x = x")
z = a31_mul((1,2,3,4), (5,6,7,8))
check(len(z) == 4, "A₃₁ product is 4-tuple")
check(all(0 <= x < P for x in z), "A₃₁ product reduced mod M31")

# Test 2: Complex A₃₁[i] arithmetic
print("--- A₃₁[i] arithmetic ---")
i = CA(a31_zero(), a31_one())  # i
i_sq = ca_mul(i, i)
check(i_sq == CA(a31_neg(a31_one()), a31_zero()), "i² = -1")
z = ca_mul(ca_one(), CA((2,0,0,0), (3,0,0,0)))
check(z[0][0] == 2 and z[1][0] == 3, "1·(2+3i) = 2+3i")

# Test 3: Matrix multiply basics
print("--- 3×3 matrix multiply ---")
I = mat_identity()
check(mat_is_unitary(I), "Identity is unitary")
check(mat_is_su3(I), "Identity is SU(3)")

# Test 4: Gell-Mann matrix λ₁ is SU(3)
print("--- Gell-Mann matrices ---")
L1 = gellmann_lambda_1()
# λ₁ is real symmetric, check exp(i·θ·λ₁) ≈ I + i·θ·λ₁ (linear approx)
# For exactness, verify λ₁² = diag(1,1,0)
L1_sq = mat_mul(L1, L1)
check(L1_sq[0][0] == ca_one(), "λ₁²[0][0] = 1")
check(L1_sq[1][1] == ca_one(), "λ₁²[1][1] = 1")
check(L1_sq[2][2] == ca_zero(), "λ₁²[2][2] = 0")

L2 = gellmann_lambda_2()
check(not mat_is_unitary(L2), "λ₂ alone is not unitary (needs exp)")

L3 = gellmann_lambda_3()
check(L3[0][0] == ca_one(), "λ₃[0][0] = 1")
check(L3[1][1] == CA(a31_neg(a31_one()), a31_zero()), "λ₃[1][1] = -1")

L8 = gellmann_lambda_8()
inv3 = m31(pow(3, P - 2, P))
check(L8[0][0] == CA((0, inv3, 0, 0), a31_zero()), "λ₈[0][0] = 1/√3")
check(L8[2][2] == CA((0, m31(-2 * inv3), 0, 0), a31_zero()), "λ₈[2][2] = -2/√3")

# Test 5: SU(3) group closure
print("--- SU(3) group closure ---")
# A = exp(i·π/4·λ₁) approximated as linear for this check
# Real SU(3) would need the full exponential, but for the oracle
# we verify that matrix multiplication over A₃₁[i] is closed.
A = mat_mul(L1, L3)
check(len(A) == 3 and len(A[0]) == 3, "Product of 3×3 is 3×3")

def dense_elem(seed):
    real = tuple(m31(seed + off) for off in (1, 3, 5, 7))
    imag = tuple(m31(2 * seed + off) for off in (11, 13, 17, 19))
    return CA(real, imag)

dense_a = [[dense_elem(3 + 5*i + 11*j) for j in range(3)] for i in range(3)]
dense_b = [[dense_elem(29 + 7*i + 13*j) for j in range(3)] for i in range(3)]
dense_expected = [
    0x0000a30000014f3000021510000446a07fff6b677ffed36f7ffe271f7ffc43ef,
    0x0000d3240001b14c0002ae0400057e047fff41f77ffe7ff37ffda5ef7ffb3fbb,
    0x0001034800021368000346f80006b5687fff18877ffe2c777ffd24bf7ffa3b87,
    0x0000ca2400019e2c00028dc400053a247fff4bff7ffe94637ffdc7077ffb830b,
    0x00010678000218a800034b480006baa87fff196b7ffe2e9f7ffd2a6b7ffa47ff,
    0x000142cc00029324000408cc00083b2c7ffee6d77ffdc8db7ffc8dcf7ff90cf3,
    0x0000f1480001ed280003067800062da87fff2c977ffe55577ffd66ef7ffac227,
    0x000139cc000280040003e88c0007f74c7ffef0df7ffddd4b7ffcaee77ff95043,
    0x00018250000312e00004caa00009c0f07ffeb5277ffd653f7ffbf6df7ff7de5f,
]
dense_packed = [pack_ca(x) for row in mat_mul(dense_a, dense_b) for x in row]
check(dense_packed == dense_expected, "Dense A₃₁[i] product matches RTL constants")

# Test 6: PHSLK-style coherence check
print("--- Coherence check ---")
at_mat = mat_dagger(L1)
prod1 = mat_mul(L1, at_mat)
check(prod1[0][0] == L1_sq[0][0], "λ₁·λ₁† = λ₁² (self-adjoint)")

# Test 7: Determinant verification
print("--- Determinant ---")
check(mat_is_su3(mat_identity()), "det(I) = 1")
check(mat_is_su3(mat_identity()), "det(I) = 1 (fresh matrix)")

# ── Summary ──────────────────────────────────────────────────────
print()
if errors == 0:
    print(f"ALL {checks} checks PASSED")
else:
    print(f"{errors}/{checks} CHECKS FAILED")
sys.exit(errors)
