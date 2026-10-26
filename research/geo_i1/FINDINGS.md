# GEO-I1 — Integrated certified geometry execution

2026-10-20. Class A host-only (AGENTS.md §4.3). New files only under `research/geo_i1/`. REL-1 (`research/rel1`: machine, backends)
and HEX-C1 (`research/hex_c1`: hierarchy, bounds, predicates; via it `ngw_h1/gbt`, `h2_hex`) are imported **read-only and unchanged**.
**Result: CONFIRMED within this bounded setting.** 8 test groups pass (27 s, 1 GiB, one process).

```bash
timeout 120 bash -c 'ulimit -v 1048576; python3 -B -I research/geo_i1/test_geo_i1.py'
timeout 60  bash -c 'ulimit -v 1048576; python3 -B -I research/geo_i1/report.py'
```

## Frozen semantic boundaries (stated before the results)
- REL-1's advantage is established against the tested coordinate backends, not every symbolic method. Here the "symbolic" control is an
  exhaustive Gram-matrix evaluator (no coordinates), which is exact too; the coordinate-materialised baseline is the weak one.
- HEX-C1's test reduction is shown on one bounded domain (7⁴ points); it is not shown superior to an optimised BVH.
- PHY-R3's squared-law proof has supporting corroboration; Hooke whole-path stability was not re-derived. Neither is used here.
- No hardware efficiency is claimed. Operation weights below are declared constants, not measurements.
- The coupling is of **state and dependency semantics**, not of physics: a REL-1 metric entry defines a query shape's metric on lattice
  coordinates; no claim that the tensegrity's geometry equals the lattice's.

## What was built
- A REL-1 `Machine` (relational backend) owns the metric state and admits/refuses transitions. The geometry layer reads only the current
  state's metric entries. Shapes: two metric-independent HEX-C1 shapes (`nat_disk`, `nat_halfplane`) and three **metric shapes**
  `md12`, `md13`, `md23`: closed disks {x : Qₘ(x−s) ≤ ρ} with Qₘ(a,b) = a² + 2m·ab + b², m = M[i][j] (plane minor, unit diagonal, PD).
- The HEX-C1 squared-comparison tests carry over to any norm (triangle inequality). Per-metric node bounds are either **exact** (maximum of Qₘ over each finite
  descendant set, enumerated: 2,801 evaluations per distinct m) or a **scaled certificate** 2(1+|m|)·R²_hex (proof: Qₘ ≤ (1+|m|)(a²+b²) ≤ 2(1+|m|)N; checked against all 2,401 points).
- Certificates (node verdict, per-metric bound table) carry a **dependency key = shape parameters + only the metric entries the shape uses**, compared by content.
  Slot policies: 'single' (one slot per node and shape, HEX-C1 style) and 'content' (one per key).
- Engines compared on the same program: hierarchical (exact bounds, refine / static, content slots; scaled bounds), a flat 7×7 bucket index with the same exact bounds and certificate
  semantics (bucket and point certificates), exhaustive-with-cache, an uncached independent exhaustive oracle (own formulas, no geom/gi_metric code),
  and a coordinate-materialised baseline (embedding (a + m·b, √(1−m²)·b), refuses when the root is irrational).

## Program (REL-1 commands; each followed by all five shape queries in every engine)
identity → m12=3/5 → (m12 kept) m13=1/2 → m13=0 restored → **singular transform (refused)** → **non-affine MOVE** → relational-only M2 (1/3,1/4,1/5) → identity restored.

## Results
- **Exactness.** At every step, hierarchical (all variants), flat, exhaustive-cached and the coordinate baseline (where it answers) match the oracle exactly, with cover partitions complete;
  refine mode has zero UNRESOLVED, static mode reports UNRESOLVED explicitly and has no wrong resolved point.
- **Selective invalidation.** Changing only m13 recomputes only `md13` certificates; changing only m12 only `md12`; changing all three leaves the native shapes untouched; a repeated
  query costs zero new tests. Restoration reuses old evidence only with content slots (single-slot engines recompute).
- **Atomic refusal.** REL-1's refused transforms (singular, off-unit diagonal, asymmetric, non-PD) leave metric and all certificates untouched (zero new tests afterwards). A non-affine MOVE
  yields a coordinate state: the geometry layer refuses `NOT_A_METRIC_STATE` and changes nothing.
- **Mutants, all killed by the oracle for the intended reason.** Ignoring dependency keys: wrong only for the shape whose entry changed (`md12` +96 points after m12; `md13` +84 after m13); same for a flat index
  with keys ignored. Declaring the wrong entry: wrong exactly where the declared entry stays fixed while the true one changes. Using the hex bound table for metric shapes: false pruning even at identity (the square and hex norms differ). An over-broad dependency
  stays exact but costs more tests.
- **Representation gap.** The coordinate baseline refuses `OUT_OF_FIELD` at m13=1/2 (`md13`) and at M2 (all three metric shapes); the relational engines decide every query exactly. Selective observation of 3 points costs one materialisation
  at m12=3/5 (coordinates reproduce Qₘ exactly) and is refused at m12=1/3 while geometry queries stay exact. REL-1 needed one coordinate materialisation in the whole program (its own MOVE).

## Measured (whole program, weights: bound test 16, point test 6, table evaluation 5, scaling 2, certificate comparison 1)
| Approach | Bound tests | Point tests | Table evals | Weighted ops | Footprint (certs; nodes/buckets) |
|---|---:|---:|---:|---:|---|
| Hierarchical, exact bounds, refine (single slot) | 1,491 | 1,708 | 16,806 | 125,946 | 1,412; 778 nodes |
| Hierarchical, exact bounds, refine (content slots) | 1,095 | 1,365 | 16,806 | 117,552 | 2,460; 778 nodes |
| Hierarchical, scaled bounds, refine | 1,554 | 1,736 | 0 (30 scalings) | **43,341** | 1,426; 778 nodes |
| Flat 7×7 index (same bounds/cache semantics) | 1,008 | 9,230 | 16,807 | 181,541 | 3,912; 72 buckets |
| Exhaustive + cache | 0 | 33,614 | 0 | 285,719 | 12,005 |
| Exhaustive, uncached (oracle) | 0 | 84,035 | 0 | 504,210 | 0 |
Static hierarchy (no refinement): 169 nodes, 495 certificates, UNRESOLVED points reported.

## Interpretation (capability vs efficiency)
- **Composition (confirmed):** a relational metric state can drive a certified hierarchical query; dependency keys over metric entries give selective invalidation, restoration reuse (content slots) and
  atomic refusal, and answers equal an independent exact evaluator at every step.
- **Test reduction (confirmed here, bounded):** the hierarchy needs 3.2k exact tests against 10.2k (flat, equal cache semantics), 33.6k (exhaustive cached) and 84.0k (uncached), with a 778-node tree against a 3,912-certificate flat store.
- **Work including certificates:** with exact per-metric bounds the enumeration (16.8k evaluations, six distinct metrics) is the dominant cost, leaving only 1.4× over the flat index; the scaled certificate removes it for +2.8% tests (3,290 vs 3,199) and gives 4.2× below the flat index.
  Whether the cheap bound is "better" depends on the declared weights.
- **Not established:** hardware cost; real weights (square-root and multiplier costs unmeasured); behaviour on larger domains, other shape families or an optimised BVH; physical meaning of the metric-to-lattice coupling.

## Limits
One tree (K=4), five shapes, one eight-step program. Shapes use one metric entry each, which makes selective invalidation easy to see; shapes that depend on all entries would invalidate together (the over-broad mutant shows that cost). REL-1's cost model leaves out exact square-root tests.
Shared dependencies are declared above; nothing in REL-1 or HEX-C1 was edited. Stopped after the bounded experiment.
