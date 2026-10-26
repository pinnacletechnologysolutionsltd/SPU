"""H2: exact hex-lattice refinement enumeration.

Compares Eisenstein multipliers, real Pell scaling and the exact 30-degree
Cayley rotation on a finite Eisenstein patch. Finite enumeration is a
regression check; the general statements are proved in FINDINGS.md.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F

import algebra as A

U = A.Q3(F(2), F(1))          # Pell unit 2 + sqrt3
U_INV = A.Q3(F(2), F(-1))     # 2 - sqrt3 = tan 15 degrees
R30 = A.cayley_rotation(U_INV)
R30_INV = A.cayley_rotation(-U_INV)

OPERATORS = {
    "eis_1-w": A.eis_matrix((1, -1)),
    "eis_2": A.eis_matrix((2, 0)),
    "eis_3+w": A.eis_matrix((3, 1)),
    "eis_unit_1+w": A.eis_matrix((1, 1)),   # 60-degree unit: automorphism control
    "pell_u": A.scale_matrix(U),
    "pell_u_inv": A.scale_matrix(U_INV),
    "rot30_cayley": R30,
}


def patch(radius: int):
    return [(a, b) for a in range(-radius, radius + 1)
            for b in range(-radius, radius + 1)]


def similarity_scale2(m):
    """Return s with M^T M = s*I exactly, or None if M is not a similarity."""
    (g00, g01), (g10, g11) = A.gram(m)
    zero = A.ZERO
    return g00 if (g01 == zero and g10 == zero and g00 == g11) else None


def lattice_matrix(m, member=A.from_cart):
    """Integer matrix of m in basis (1, w) if m maps L into L, else None."""
    cols = [member(A.apply(m, A.to_cart(e))) for e in ((1, 0), (0, 1))]
    return None if None in cols else cols


def classify(m, member=A.from_cart):
    s2 = similarity_scale2(m)
    cols = lattice_matrix(m, member)
    d = A.det(m)
    if cols is not None:
        (a, c), (b, e) = cols
        index = abs(a * e - b * c)
        kind = "lattice_automorphism" if index == 1 else "sublattice_similarity"
        return {"kind": kind, "index": index, "scale2": s2, "det": d}
    is_scalar = m[0][1] == A.ZERO and m[1][0] == A.ZERO and m[0][0] == m[1][1]
    if s2 == A.ONE and d == A.ONE:
        kind = "euclidean_rotation_not_lattice"
    elif is_scalar:
        kind = "algebraic_dilation_not_lattice"
    else:
        kind = "other_not_lattice"
    return {"kind": kind, "index": None, "scale2": s2, "det": d}


def residue_index(z, pts):
    """Count classes of L/zL seen in pts, independent of the determinant."""
    n = A.e_norm(z)
    zc = A.e_conj(z)
    keys = {tuple(c % n for c in A.e_mul(p, zc)) for p in pts}
    return len(keys)


def enumerate_patch(m, pts):
    images = [A.apply(m, A.to_cart(p)) for p in pts]
    on = [A.from_cart(q) for q in images]
    nonzero_on = sum(1 for p, q in zip(pts, on) if q is not None and p != (0, 0))
    return {"points": len(pts), "images_on_lattice": sum(q is not None for q in on),
            "nonzero_images_on_lattice": nonzero_on}


def mat_eq(m, n):
    return m == n


def rot_power(k):
    m = A.IDENT
    for _ in range(k):
        m = A.compose(R30, m)
    return m


def q3s(x):
    return None if x is None else f"{x.r}+{x.s}*sqrt3"


def run(radius: int = 6) -> dict:
    pts = patch(radius)
    out = {"radius": radius, "operators": {}}
    for name, m in OPERATORS.items():
        c = classify(m)
        c.update(enumerate_patch(m, pts))
        c["scale2"], c["det"] = q3s(c["scale2"]), q3s(c["det"])
        out["operators"][name] = c
    out["residue_index"] = {str(z): residue_index(z, pts)
                            for z in ((1, -1), (2, 0), (3, 1))}
    out["pell_rotated_any_lattice_preserving"] = any(
        lattice_matrix(A.compose(A.scale_matrix(U), rot_power(k))) is not None
        for k in range(12))
    return out


if __name__ == "__main__":
    r = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    print(json.dumps(run(r), indent=1, default=str))
