# HEX-C1 — Certified Eisenstein hierarchical geometry

**Status: COMPLETE (owner decision 2026-10-20)** within its finite-domain geometric-query
scope. Passing tests, negative controls and counted test reductions are preserved.
The 3.4–4.9× figure counts tests, not runtime. Bound and point tests are weighted
equally, and the flat baseline uses a single bucket size. The growth from 169 to 799
nodes in refine mode is a state cost to account for. A strong conventional hierarchy
(e.g. a BVH) under matched query and memory constraints is the required next
performance comparison. HEX-C2, Nguyen weighting and SOM residency remain on HOLD.

2026-10-20. Class A host-only experiment (AGENTS.md §4.3,
[execution policy](../../spu_strategy/RESEARCH_EXECUTION_POLICY.md)), owner-approved.
Writes only under `research/hex_c1/`. Imports read-only from `research/h2_hex`,
`research/ngw_h1` and `research/phy_r1/field.py`. REL-1 runs in a parallel session
under `research/rel1/`, and the file ownership split was confirmed with that session.
No GPU RTL, memory-policy, SOM or simulator change was made.

**Result: CONFIRMED within a bounded domain.** A finite aperture-7 hierarchy with
exactly verified conservative bounds answers region queries with zero wrong
answers. It returns UNRESOLVED only where refinement is absent, and it resolves
everything when refining on demand. Logical ancestry is shown **not** to imply
containment in the regular parent hexagon, and a hexagon-assumption mutant falsely
prunes. 9 test groups passed, exit 0, 1.9 s, with no failed run.

```bash
timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/hex_c1/test_hex_c1.py'
timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/hex_c1/run.py'
```

## Construction

- **Coordinates and predicates.** Lattice coordinates (a, b) = a + bω, with Euclidean
  quadrance N = a² − ab + b². Half-planes αa + βb + γ ≥ 0 have Euclidean gradient
  norm² (4/3)(α² + αβ + β²). All tests are rational, with no square roots.
  Shapes are **closed**, and touching is never disjoint.
- **Domain and ownership.** The domain is the 7⁴ = 2,401 points with 4-digit
  aperture-7 expansions (π = 2 − ω). Ownership is logical, by digits, never Voronoi:
  each point has exactly one level-ℓ owner, and each level-2 node owns exactly 49
  points.
- **Finite descendant sets.** A level-ℓ node at c owns the **finite** set c + D_ℓ.
  Nothing is claimed about the infinite fractal (Gosper-island) limit.
- **Bounds.** Each node's bound is the closed disk N(x − c) ≤ R²_ℓ, with
  R² = [0, 1, 13, 109, 819] for levels 0–4, each the exact maximum over D_ℓ.
  This was verified on **every node** of the full tree by enumerating its
  descendants. It was also checked against an independent triangle-inequality
  bound (Σ√7ⁱ)² computed in Q(√7).
- **Query.** Each node returns EXACT_INSIDE (bound disk inside the shape),
  EXACT_OUTSIDE (bound strictly disjoint) or refines. Level 0 is an exact point test.
  An unrefined straddling node returns **UNRESOLVED** in static mode, or is expanded
  in refine mode.
- **Certificates.** Each (node, shape) verdict is stored with the shape's version.
  It is reused only when the version matches. A shape edit bumps the version.
  Refinement edits do **not** invalidate certificates, because a node's descendant
  set and bound are fixed.

## Ancestry is not geometric containment

This counts descendants that are closer to a neighbouring same-level centre than to
their own ancestor, i.e. that lie outside the parent's regular hexagon:

| Level | Descendants | Outside parent hexagon |
|---|---:|---:|
| 1 | 7 | 0 |
| 2 | 49 | 0 |
| 3 | 343 | **24** |
| 4 | 2,401 | **192** |

At level 4 the exact bound R² = 819 exceeds even the hexagon's circumscribed
disk (7⁴/3 ≈ 800.3). So no regular-hexagon parent boundary may be inferred
from base-7 addresses.

## Scene and results

Six closed shapes on an irregular tree, refined only near (3,1): 169 nodes.
1. **disk:** centre (3,1), ρ = 40.
2. **halfplane:** a − 2b + 5 ≥ 0.
3. **triangle:** three half-planes.
4. **tangent:** a half-plane exactly tangent to a level-1 bound disk, with a lattice point on its boundary.
5. **lattice_circle:** ρ = 49, whose boundary passes through lattice points.
6. **sparse_disk:** in the unrefined region.

| Shape | Static: tests (bound+point) / unresolved pts | Refine: tests / nodes visited | Flat baseline tests | Exhaustive |
|---|---|---|---:|---:|
| disk | 78 / 91 | 169 / 169 | 709 | 2401 |
| halfplane | 71 / 224 | 190 / 190 | 882 | 2401 |
| triangle | 64 / 413 | 281 / 281 | 910 | 2401 |
| tangent | 50 / 357 | 225 / 225 | 868 | 2401 |
| lattice_circle | 57 / 126 | 183 / 183 | 709 | 2401 |
| sparse_disk | 15 / 98 | 57 / 57 | 279 | 2401 |

There are **0 wrong answers** for every shape in both modes, and 0 unresolved points in
refine mode. The flat baseline uses 72 buckets (7×7 in (a, b)), each with an exact
enumerated bounding disk, and matches the exhaustive test exactly. In refine mode the
hierarchy used 3.4–4.9× fewer exact tests than that baseline and 8.5–42× fewer than
exhaustive testing.

Refinement on demand grew the tree from 169 to 799 nodes (90 expansions). That growth
is a real cost the static hierarchy avoids by answering UNRESOLVED instead.

**Boundary contact.**
- The tangent bound disk is classified INSIDE, since the shape is closed.
- The tangent point lies on the line (f = 0) and counts as inside.
- Externally touching disks are STRADDLE, not OUTSIDE.
- Lattice points exactly on the ρ = 49 circle are inside.

**Certificate reuse.**
- Re-querying all six shapes reuses every certificate, with zero new tests.
- After moving the disk, its certificates are all stale (0 reused) and its recomputed answer is exact. The other shapes' certificates survive in full.
- After refining an UNRESOLVED node, ancestor certificates are reused and only the new nodes are tested. The answer stays exact.

## Negative controls (all fail as required)

- **Stale certificate:** reusing verdicts across a shape edit while ignoring versions gives wrong answers. A fresh query is exact.
- **False pruning:** using the regular hexagon as the parent region, with a half-plane equal to one hexagon edge, marks a level-3 node INSIDE although one of its descendants lies outside. That gives wrong answers, while the true bound gives (0 wrong, 0 unresolved).

## Metadata cost (model estimate)

- **Hierarchy:** 169 nodes (static) or 799 (after refine mode) at about 4 B each (12-bit address, level, child link). The bound table holds just **5 integers**, because bounds are translation-invariant per level. Certificates: 335 (static) and 1,105 (refine) at about 6 B each (node, shape, verdict, version).
- **Flat baseline:** 72 buckets × about 8 B (centre and R²).
- Test counts treat a bound test and a point test as one unit each. A bound test costs a few more multiplications, which is not weighted.

## Dispositions and limits

| Hypothesis | Result |
|---|---|
| Finite aperture-7 descendant sets admit exact, verified conservative bounds | **CONFIRMED** |
| Hierarchical queries preserve exact answers (no false INSIDE/OUTSIDE) | **CONFIRMED** (0 wrong, every shape, both modes) |
| Selective refinement resolves every UNRESOLVED region exactly | **CONFIRMED** (refine mode) |
| Base-7 ancestry implies containment in the regular parent hexagon | **FALSIFIED** (24 and 192 counterexamples; mutant false-prunes) |
| Certificates with version dependencies reuse correctly and invalidate on edits | **CONFIRMED**; the stale control fails as required |
| Hierarchy needs fewer exact tests than a flat bounding baseline | **CONFIRMED in this scene** (3.4–4.9×), but with refinement and certificate storage overhead; one scene, 4 levels |

**Limits.** One bounded domain (K = 4), six shapes, and disk bounds only (tighter
hull bounds were not tried). Cost is counted in tests, not time. The flat baseline uses one
bucket size. Nothing here establishes GPU or hardware benefit.
