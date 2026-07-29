# Candidate-Tranche Feasibility Audit Verdict

**Date:** 2026-07-29

**Closure update:** 2026-07-30

**Input contract:** `docs/FEASIBILITY_AUDIT_HANDOFF_2026-07-28.md`

**Audit mode:** independent, read-only; primary sources and current worktree
inspected; no board builds rerun

## Verdict

| Candidate | Verdict | Disposition |
|---|---|---|
| Cyclotomic Fibonacci arithmetic | `GO_ORACLE_COMPLETE` | Host oracle independently audited; retain it and stop before RTL. |
| Locality-aware FPGA floorplanning | `NO_GO` | Predeclared gate measured 2026-07-30 and failed on both axes; no P&R campaign. |
| Exact tetrahedral cages / relative-4D BVH | `DOC_ONLY` | Retain citation and analysis; do not implement. |
| Chaitin, *How Real Are Real Numbers?* | `DOC_ONLY` | Philosophical context only; excluded from engineering priority. |

The cyclotomic oracle is now closed and the floorplanning measurement has been
run and failed. **No candidate in this audit carries an open engineering
action.** All three dispositions are terminal: retain the oracle, do not build
a floorplanner, do not implement tetrahedral cages.

## Load-bearing audit findings

### Cyclotomic arithmetic

- A complete Fibonacci braid representation fits in rank-4
  `Z[zeta_5]` when the integral gauge

  ```text
  F = [[phi^-1, 1], [phi^-1, -phi^-1]]
  ```

  is paired with its weighted metric. The standard orthonormal/unitary gauge
  still requires the additional `sqrt(phi)` radical and is rank 8 over the
  fifth-cyclotomic field.
- The existing Lucas modulus 521 is unsuitable for a field-valued
  fifth-cyclotomic backend. Since `521 == 1 (mod 5)`, `Phi_5` splits completely
  and `Z[zeta_5]/521` contains zero divisors.
- For prime `p != 5`, `Phi_5` is irreducible over `F_p` exactly when
  `p == 2 or 3 (mod 5)`. M31 satisfies `M31 == 2 (mod 5)`, so
  `F_M31[x]/Phi_5` is a genuine degree-4 field and is the first modular image
  to evaluate.
- This remains a host oracle until a named consumer supplies a latency or
  determinism requirement. Exact coefficients do not remove exponential
  fusion-state growth.
- Independent review on 2026-07-30 cleared all five contract gates against
  the 48-check audited baseline. Mutation testing also established that the
  Pentagon and Hexagon checks are non-vacuous. Closure hardening expanded the
  final suite to 52 checks and the corpus to 100 words, with 50 generic streams
  reported separately from finite-order patterns.
- The finite-field success is specific to `Phi_5`: for `p` not dividing `n`,
  `Phi_n` factor degrees equal `ord_n(p)`. The unit groups modulo 8, 12, 16,
  and 24 have maximum orders 2, 2, 4, and 2 respectively, below their
  cyclotomic degrees 4, 4, 8, and 8. Their full power-basis quotients therefore
  cannot become fields by selecting a different prime; modular versions need
  explicit factor/CRT and zero-divisor semantics.
- The implemented SU3 arithmetic domain is authoritatively declared at
  `hardware/rtl/core/spu13/spu13_su3_mult.v:1-6`: degree-8 modular `A31[i]`,
  not rank-4 characteristic-zero `Q(zeta_12)`.

### Floorplanning

- Legal seeded-placement mechanisms exist: the active Himbächel flow exposes a
  Python pre-place hook/region constraint path, and both active flows honour a
  per-cell BEL attribute.
- The deleted Gowin CST files were syntactically invalid: the Himbächel parser
  requires complete `R...C...[slice][A|B]` locations.
- The blocker is logical-group to packed-cell association. Global `-noflatten`
  preserved names but increased one measured probe from 883 to 38,738 cells,
  invalidating a matched placement comparison.
- The selective `keep_hierarchy` measurement was run on 2026-07-30 against the
  Tang 25K SOM sidecar spin, both arms to scratch. Gate was at least 90%
  target-cell prefix coverage **and** no more than 2% total cell-count growth.
  **Both halves failed:**

  | Arm | cells | addressable by `u_*` prefix |
  |---|---|---|
  | baseline | 36,264 | 4 (0.0%) |
  | selective `keep_hierarchy` | 38,568 | 4,560 (11.8%) |

  Cell-count growth was **+6.35%**. Worse, the addressable cells were
  `u_som1_frame` 2,797 and `u_spi` 1,759 against `u_bmu` **4** —
  `keep_hierarchy` did not hold on the BMU datapath, which is the block a
  floorplan would exist to place. The two arms are therefore not the same
  netlist, so the matched-netlist multi-seed comparison the experiment requires
  cannot be constructed.
- Verdict: **`NO_GO`** for the physical experiment. `tools/floorplanner/`
  remains a research aid, as its README states. The negative is about
  name/optimization coupling, not the toolchain: the pre-place and BEL
  mechanisms above are real and simply have nothing stable to address.

### Tetrahedral cages

- Exact homogeneous barycentrics can remove order-dependent float32 cracks,
  but the paper's four lanes are local barycentric weights ordered by global
  vertex ID, not a fixed Quadray/IVM basis.
- Appendix A is an interval-enclosure argument and does not depend on exact
  arithmetic. Reproducing it is not evidence for an SPU accelerator.
- The active repository has no live graphics consumer for the proposed unit;
  the missing BVH traversal and memory hierarchy dominate the arithmetic.
- The AMD paper already presents its 4D path as a watertight reference
  solution. No implementation tranche is justified without evidence that its
  remaining snapping threshold fails on real content.

## Cyclotomic closure record

1. Characteristic-zero rank-4 Fibonacci oracle: **complete**.
2. Weighted-metric, full Pentagon, and directed Hexagon checks: **complete**.
3. Declared length-100 growth corpus: **complete**, reported by class — 55
   coefficient-magnitude bits (56 signed storage bits) on structured words,
   14 magnitude bits (15 signed storage bits) on the 50 generic streams. The
   two are distinct: the oracle measures `abs(v).bit_length()`, which excludes
   the sign, so a magnitude figure is not a storage width and the test pins
   both. Three structured patterns are finite-order and contribute no growth
   evidence; their orders are pinned so the corpus cannot silently become
   inert.
4. Independent M31 modular-image comparison: **complete**, all 100 words
   agree in the hardened final corpus.
5. Independent contract audit and mutation testing: **complete**.
6. RTL/cost model: **not authorized** without a named consumer.
7. Bounded selective-hierarchy floorplanning measurement: **complete**, gate
   failed on both axes, physical experiment `NO_GO`.

The tetrahedral and Chaitin candidates remain documentation-only. No candidate
in this audit has an open engineering action.

Full repository regression after closure hardening: **178/178, exit 0.**
