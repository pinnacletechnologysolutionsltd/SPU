# Wildberger Pass 2: Quadrance, Quadrea, Oriented Triangles, Turns (2026-10-23)

Status: exploratory, host-only; no ISA/RTL/simulator/hardware change; outside qualified campaigns; follows `docs/WILDBERGER_SPREAD_INVENTORY_2026-10-23.md`.
Verification: `python3 software/experiments/wildberger_quadrance_turn_inventory.py` (SymPy 1.14 in a throwaway venv, ~14 s). 26 exact symbolic checks, all PASS. D* = book statements as printed in the supplied *Divine Proportions* text (Ch. 5 pp. 59–72, §9.1–9.3 pp. 113–118, Ch. 7 Thm 47/50); E* = my derivations. Formula identities are polynomial identities (exact); n-indexed ones cover n ≤ 8.

## Chapter 5: what the foundations actually are (book, all re-verified)
- Quadrance Q = dx²+dy² (no sqrt). Archimedes' function A(a,b,c) = (a+b+c)² − 2(a²+b²+c²) = 4ab − (a+b−c)² (five equivalent forms, D2/D3).
- One polynomial does four jobs: collinearity (A(Q1,Q2,Q3)=0, Thm 22), area (A = **4·cross²** = 16·a², D1/D10), Heron/Archimedes factorisation (D4), right triangle (A=4Q1Q2 iff Q1+Q2=Q3, D5). Quadrance to a line needs one division by a²+b² (D6). Four collinear points: Quadruple quad formula = resultant of two quad triples (D7), Brahmagupta factorisation (D8), Bretschneider (D9).
- Smallest field: Q (or Z for integer coordinates: quadrea is an integer, 4·cross²).

## Chapter 9: orientation (book, re-verified)
- Signed area a = cross/2: additive over polygons, independent of the base point P, sign flips on reversal (D11, D12). Quadrea A = 16a² keeps magnitude and **loses sign** (D10).
- Turn u(l1,l2) = cross/dot of the line normals (= tan θ). Composition u(l0,l2) = (u+v)/(1−uv) (D15): a Möbius map, **oriented and additive, no root choice**. Triple turn: u1+u2+u3 = u1u2u3, *linear* in each variable (D13). Coturn form (D14). U_n(u) = Im/Re (1+iu)ⁿ reproduces the printed U_2..U_5 (D16). Twist t = u² obeys the quadratic Triple twist formula (D17).

## Bridges (mine, E1–E9)
| # | Result | Meaning |
|---|---|---|
| E1 | S_n(u²/(1+u²)) = U_n²/(1+U_n²), n≤8 | spread polynomial = the turn function with the sign (and one branch) quotiented out |
| E2 | triple turn ⇒ triple spread (Thm 47) | the oriented relation is the primitive; the unoriented one is its image |
| E3 | triple-spread fn = Archimedes(s1,s2,s3) − 4s1s2s3 | quadrea polynomial is the shared core |
| E4 | U_n(i v) = i·(n-fold ⊕ of v), n≤8 | **Euclid turn ↔ Lorentz velocity by u→iv** (u²→−v², i.e. s→σ of the earlier note) |
| E5 | va+vb+v3 = −va vb v3 for v3 = −(va⊕vb) | velocity triple relation = Triple turn under u=iv |
| E6 | book (23.11) symmetric form = Triple twist formula with t = −V | this *is* the book's "closely connected to velocity addition" (p.93); upgrades the earlier D7 bridge to the oriented level |
| E7 | (23.11) = −Archimedes(V1,V2,V) + terms of degree ≥3 | Newtonian quad triple (23.9) is its lowest-order part |
| E8 | U_n odd under reversal; spread/twist even | turn carries the orientation that spread loses |
| E9 | M31: −1 and 3 non-residues, −1/3 residue ⇒ (b√3)²=−1 in F_p(√3) | **A31 (algebra, not field) has null vectors** — Quadrance-0 nonzero vectors; Midpoint/null-line theorems need non-null hypotheses there |

## Classification
- **Identical mechanism:** triple turn / triple twist / triple spread / (23.11) velocity relation (one relation, three coordinates: u, t=u², s=u²/(1+u²); velocity by u→iv); turn composition and ⊕ (same Möbius group, sign of uv differs).
- **Related, different state:** turn (oriented, projective: ∞ at perpendicular) vs spread (even, bounded) vs quadrea (squared, sign lost). Signed area vs quadrea. Euclid (norm-1 torus over Q(i)-type) vs Lorentz/Pell (split torus): related by analytic continuation, not the same real group.
- **Superficial:** quad triple vs Pell by name only.

## Deletion-ledger candidates (observations; nothing implemented, nothing measured)
| Observation | Possible redundancy | Caveat |
|---|---|---|
| Quadrea = 4·cross² and orientation = sign(cross) | a separate "area" and "orientation" evaluation share one cross product; sqrt never needed for sign/zero tests | already how exact predicates work; no new gain claimed |
| Turn is the oriented primitive; spread/twist are images (E1, E2) | storing spread discards sign and forces root choices on composition (earlier note A5/C8) | turn is undefined at perpendicular; projective pair (cos,sin) ≈ the existing Pell rotor (a,b) with turn = b/a — hypothesis only |
| Euclid/Lorentz differ by u→iv (E4) | rotation and boost composition formulas need not be separate "theories" | different domains/branches; implementations may still differ |
| M31 has null vectors (E9) | none; this adds a **hazard** | any quadrance-based predicate over A31 must treat Q=0 ≠ zero vector |
No new opcode proposed.

## Limitations
Finite symbolic checks; E9 is a residue computation, not a full A31 geometry; no hardware/cost claim; book read only for the cited pages; no independent qualification. Next candidate (one at a time): §19 Taylor/tangent, driven by whether a Taylor shift gives cheaper exact certificates than de Casteljau (see `docs/EXACT_SIGN_CERTIFICATES_RESULTS_2026-10-23.md`).
