"""Independent coordinate-free checks from pairwise quadrances only.

Uses the documented stress ratio cable:strut = 2:-3
(docs/TENSEGRITY_BALANCER_FEASIBILITY.md), not the model's solved stress.
  realisable in 3D  <=> centred Gram G = -1/2 J D J is PSD with rank 3
  equilibrium       <=> Omega G Omega = 0      (Omega G Omega = (Omega P)(Omega P)^T)
  strut disjointness   Cayley-Menger volume != 0, or (coplanar) parallel and
                       separated; non-parallel coplanar pairs stay uncertified
"""
from __future__ import annotations

from fractions import Fraction as Fr

from field import det, rank_and_psd

STRUT_Q = Fr(16)


def _mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
            for i in range(len(a))]


def centred_gram(D):
    n = len(D)
    J = [[Fr(int(i == j)) - Fr(1, n) for j in range(n)] for i in range(n)]
    JDJ = _mm(_mm(J, D), J)
    return [[-v / 2 for v in row] for row in JDJ]


def omega(n, E, qc=Fr(2), qs=Fr(-3)):
    om = [[Fr(0)] * n for _ in range(n)]
    for i, j, t in E:
        v = qs if t == "S" else qc
        om[i][j] -= v
        om[j][i] -= v
        om[i][i] += v
        om[j][j] += v
    return om


def cm_volume_sq_x288(D, pts):
    a = [[Fr(0)] + [Fr(1)] * 4]
    for i in pts:
        a.append([Fr(1)] + [D[i][j] for j in pts])
    return det(a)


def coplanar_pair_disjoint(D, a, b, c, d) -> bool:
    """Coplanar strut pair: certify disjoint only if parallel and separated.

    Dot products come from polarisation of quadrances, so no coordinates:
      (b-a).(d-c) = (D_ad + D_bc - D_ac - D_bd) / 2
      (c-a).(b-a) = (D_ac + D_ab - D_bc) / 2
    Parallel  <=> ((b-a).(d-c))^2 == D_ab * D_cd   (spread 0)
    Separated <=> quadrance from c to line ab, D_ac - dot^2 / D_ab, is > 0.
    A non-parallel coplanar pair is left uncertified (returns False).
    """
    cross = (D[a][d] + D[b][c] - D[a][c] - D[b][d]) / 2
    if cross * cross != D[a][b] * D[c][d]:
        return False
    dot = (D[a][c] + D[a][b] - D[b][c]) / 2
    return D[a][c] - dot * dot / D[a][b] > 0


def check(D, E):
    n = len(D)
    G = centred_gram(D)
    rank, psd = rank_and_psd(G)
    om = omega(n, E)
    resid = _mm(_mm(om, G), om)
    struts = [(i, j) for i, j, t in E if t == "S"]
    pairs = [(a, b, c, d) for x, (a, b) in enumerate(struts) for (c, d) in struts[x + 1:]]
    vols = [cm_volume_sq_x288(D, list(p)) for p in pairs]
    disjoint = [v != 0 or coplanar_pair_disjoint(D, *p) for v, p in zip(vols, pairs)]
    return {
        "realisable_3d": psd and rank == 3,
        "equilibrium": all(v == 0 for row in resid for v in row),
        "strut_lengths_ok": all(D[i][j] == STRUT_Q for i, j in struts),
        "cables_taut": all(D[i][j] > 0 for i, j, t in E if t == "C"),
        "struts_disjoint": all(disjoint),
        "coplanar_strut_pairs": sum(v == 0 for v in vols),
        "quadrance_multiset": tuple(sorted(D[i][j] for i in range(n)
                                           for j in range(i + 1, n))),
    }


def balanced(r) -> bool:
    return all(r[k] for k in ("realisable_3d", "equilibrium", "strut_lengths_ok",
                              "cables_taut", "struts_disjoint"))
