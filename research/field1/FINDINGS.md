# FIELD-1: Surd necessity call-site audit

2026-10-23. Read-only classification. No code, RTL, CI or SIM-CAP1 change; no new workload run.
Evidence is source reading plus FIELD-0 (`research/field0/`) and the earlier VM multiply counts
(demo programs only; operand frequency is NOT used as evidence of necessity).
Scope limit: the GPU statement is only that `hardware/rtl/gpu` contains no Q(√3)/surd references
and the raster edge function is integer (`spu_edge_stepper.v`, `software/lib/gpu_raster_oracle.py`).
No whole-GPU architecture claim.

Classes: RN = RATIONAL-NATIVE, RR = RATIONAL-REPARAMETERIZED, EXT = EXTENSION-REQUIRED,
UNRES = SEMANTICALLY-UNRESOLVED.

## Call-site matrix

| # | Family | Source | Input domain | Intended transformation | Class | Basis |
|---|---|---|---|---|---|---|
| 1 | Scalar Pell `ROT`/`rotate_phi` | `spu_vm.py:262,1384`; `rational_robotics.py:60` | R[d] = (a,b) integer pair | multiply by u=2+√3 (Janus/"rotor") | EXT | Witness: u has infinite order with N(u)=1; Z and Q have no such unit besides ±1. Action on (a,b) is the integer matrix [[2,3],[1,2]] (integer *storage*, extension *semantics*). |
| 2 | `QuadrayVector.rotate` / `QROT` | `spu_vm.py:466,1569` | Quadray, surd components | docstring: quadrance-preserving rotation | UNRES | Computed op is a similarity: Q 24 → 24(7+4√3) (FIELD-0 test; METRIC-VAL-1). If a Euclidean rotation was intended, rows 3–4 supply rational candidates; which was intended is undecided (SIM-CAP1). |
| 3 | ROTC angles 0–5 circulant | `spu_vm.py:535` `circulant_rotate`; `rational_robotics.py:279`; `spu13_rotor_core_tdm.v:~60-100` | Quadray, F,G,H | 60/120/240° about body diagonal | RN | F,G,H ∈ {2/3,2/3,−1/3}-type; RTL fast path `is_small_scalar` requires coefficient b-word = 0, plus `div3`. Identity: R = cI+(1−c)J/3+s[u]×, u=(1,1,1)/√3 ⇒ F=(1+2c)/3, G,H=(1−c)/3 ± σ with s=σ√3 (σ rational). |
| 4 | ROTC 6–35 (thirds conjugates, A₄ perms, S₄) | `knowledge/rotc_tables.md`; `spu13_rotor_core_tdm.v` bypass_* | Quadray | catalog rotations | RN | Signed permutations / integer 3×3 (FIELD-0: 24 cube rotations = ±basis permutations). Thirds entries are rational. Nothing here needs a b-lane. |
| 5 | Off-catalog circulant, general F,G,H | `spu13_rotor_core_tdm.v` `ENABLE_TDM_FALLBACK` surd multiplier | F,G,H ∈ Q(√3) | arbitrary angle about body diagonal | EXT (for Cartesian-rational angles) / RR (for cosθ∈Q, sinθ∈√3Q) | Witness: cosθ=3/5, sinθ=4/5 ⇒ G,H=(1/5)±4/(5√3) ∉ Q. Rational angles of the A₂ type (incl. z/z̄, denominators 7 etc.) are RR with denominator growth. No shipped catalog entry uses the fallback (not exhaustively checked in RTL). |
| 6 | Quadray quadrance / dot / spread | `spu_vm.py:485,~496,508` | integer Quadray | exact metric predicates | RN (metric) + UNRES (VM dot) | Quadrance = Σ_{i<j}(aᵢ−aⱼ)² = Gram form 4Σa²−(Σa)², integer. VM `dot` = Σaᵢbᵢ; Gram inner product is 4Σaᵢbᵢ−ΣaΣb (derived by algebra, not run here); they agree only when sums vanish, so `spread` is inconsistent with `quadrance` otherwise. Already open under METRIC-VAL-1. |
| 7 | `hex_project` | `spu_vm.py:523` | normalized Quadray | A₂ axial coords | RN | Integer (q,r). Cartesian y = r√3/2 only needed at a display boundary (no renderer call site examined). |
| 8 | Cartesian bridge ingest | `cartesian_bridge.py:38`; `spu_cartesian_quantizer.v` | float / S24.8 | quantize to (P,0) | RN | Output Q-lane is 0 by construction. |
| 9 | Cartesian bridge egress | `cartesian_bridge.py:78` `dequantize_surd` | (P,Q) | float display of P+Q√3 | EXT only if Q≠0 reaches egress | Evidence cannot decide whether any shipped path emits Q≠0 to egress. |
| 10 | SOM weighted quadrance / BMU | `rational_som.py:109`; `spu_som_bmu.v` | (P,Q) features, weights | Σ rⱼ(xⱼ−wᵢⱼ)², ordered compare | RN for shipped data; UNRES for training | Shipped CSV path: features Q=0 (`docs/SOM_CSV_TRAINER.md:19`). Trainer comment says Q stays "at/near 0" (`tools/spu4_som_edge_trainer.py:~21`), not exactly 0: not established that trained weights keep Q=0. Fixture node 6 in `tiny_hex_fixture` has Q=1 deliberately (surd-lane test), so EXT is exercised by tests, not by data. |
| 11 | Tensegrity guard | `spu13_tensegrity_guard.v` | Z[φ] | admission/equilibrium predicates | OUT OF SCOPE | Domain is Z[φ], not Q(√3). Not classified. |
| 12 | Metric tensegrity (research) | `research/phy_r1/FINDINGS.md:55-59` | metric (Gram) | materialize coordinates | RN at metric level; EXT at coordinate level | Witness: m₁₂=1/2 is rational and admitted but coordinates materialize only in Q(√3) ("not checkable (needs √3)"). This is the FIELD-0 distinction exactly. |
| 13 | CPU Surd bank / SMUL / SADD | `spu13_surd_bank.v`; `surd_smul_unit.v`; `surd_cpu_products.v`; `isa_reference.md:39-61` | (a,b,d) tuples | exact Q(√3) with explicit denominator | UNRES | Generic carrier: it supports every row above but is demanded as a general multiplier by only rows 1, 5, and any Q≠0 data. Which workload needs it is a product question, not decidable from source. |

## Three strongest potential simplifications (not proposals to build)

1. **ROTC/circulant b-lane.** Rows 3–4: every catalog angle has b=0 coefficients, already visible in
   `is_small_scalar`. The surd multiplier fallback (row 5) is justified only by off-catalog angles.
2. **Integer Gram metric for Quadray predicates.** Row 6: quadrance and spread-type predicates on
   integer Quadrays need no Q(√3) at all, and doing them in Gram form also removes the VM `dot` inconsistency.
3. **SOM P-lane-only comparison.** Row 10: if trained weights are shown to stay at Q=0 exactly, the
   Q lane and √3-aware ordering are unused on the shipped path. Currently unproven (see "at/near 0").

## Negative / unresolved results retained
- Pell is not rational and is not Euclidean (rows 1–2). It is the only family with a clear
  extension witness besides off-catalog Cartesian-rational angles (row 5) and coordinate materialization (row 12).
- Denominator growth: rational non-catalog rotations are not free; row 5 RR cases need denominators other than 3.
- Not examined: `spu13_rotor_core_tdm.v` beyond lines ~1–100, `spu13_core.v` datapaths other than ROTC/Pell grep hits,
  the remaining ~15 RTL files that mention surd, the C++ headers, and any renderer/display call site.
  Rows marked UNRES stay unresolved until those are read.

## Distinctions this document relies on

- **Field necessity vs implementation capability.** EXT/RN describe what the mathematics requires for the
  stated output. The CPU Surd bank (row 13) and the RTL b-lanes are implementation capability; having them
  does not make a call site EXT, and their absence from a path would not make it RN.
- **ROTC catalog vs off-catalog circulant.** Rows 3–4 are the catalog angles (b-lane zero, rational).
  Row 5 is off-catalog general F,G,H; its EXT witness (cosθ=3/5, sinθ=4/5) is not a catalog operation,
  and no catalog entry was shown to use the fallback (not exhaustively checked in RTL).
- **Inner-product convention vs confirmed defect.** The only defect reproduced by execution is
  `QuadrayVector.rotate()` (FIELD-0 test, METRIC-VAL-1). For `dot`/`spread` (row 6), the mismatch with the
  Gram inner product 4Σaᵢbᵢ−ΣaΣb was derived by algebra only; FIELD-1 did not execute it. METRIC-VAL-1 lists
  `spread()` as open; whether `dot` is a defect or a deliberate coordinate-sum convention is undecided.
- **Shipped SOM input vs trained-weight state.** Shipped CSV inputs have Q=0 by construction
  (`docs/SOM_CSV_TRAINER.md:19`). Trained weights are unverified: the trainer comment says "at/near 0".
  The fixture with Q=1 exercises the lane in tests only.
- **Examined GPU RTL vs the rendering system.** The only GPU statement is that `hardware/rtl/gpu` has no
  surd/√3 references and the raster edge function is integer. No claim covers the complete rendering
  system, display scaling, or any unexamined GPU path.
