# Series Stream Controller — RTL Contract

The module that drives a tagged `spu13_jet_mac` through the digon-lattice
traversal, computing the Hyper-Catalan series root over the jet ring
J_N = A31[ε]/(ε^(N+1)).  Targets N = 2 (ε³) and N = 4 (ε⁵).

## 1. What it computes

Given a Taylor-shifted polynomial's coefficients `c[0..deg]` (jets over
A31) with `c[0] = O(ε)` and `c[1]` a unit, compute:

```
x = Σ_{m : V-1 ≤ N}  C_m · c[0]^{V-1} · c[1]^{-E} · c[2]^{m₂} · c[3]^{m₃} · ...
```

in J_N.  This is `soft_poly_root(c, types, ring)` from
`software/lib/hyper_catalan.py`, with the type set restricted to
surviving types at depth N.

The output `x` is a jet; when added to the base root x₀, the result
satisfies p(x₀ + x) = 0 EXACTLY in J_N (nilpotent series reversion,
Theorem 4 of Wildberger & Rubine 2025).

## 2. Static schedule — the digon lattice

The type lattice is **fully static** for each target N.  It can be
synthesized as a ROM or hardwired as a sequencer table.  No runtime
enumeration — the schedule is a compile-time constant of the bitstream.

| N | Depth | Surviving types | Max V | Max E | Series terms |
|--:|:------|:----------------|:------|:------|:-------------|
| 2 | ε³    | 2               | 3     | 3     | 2            |
| 4 | ε⁵    | 7               | 5     | 7     | 7            |

(Type counts per the fixed affine-weight enumeration — the survivor set at
ε⁵ includes `(3,0,0,0)`, weight 4; the earlier 6-type table came from the
`enumerate_types` range-bound bug fixed 2026-07-08.)

**Lattice order:** types sorted by V ascending, then lexicographic.
This is a topological sort of the face-addition DAG — each type (except
the null type) has a unique predecessor obtained by removing one face.

The schedule ROM encodes, for each term:

| Field | Width | Description |
|:------|:------|:------------|
| `C_m` | 16    | Hyper-Catalan integer (small; C₀=1, C_(1,0,0,0)=1) |
| `v1`  | 5     | V-1 exponent on c₀ |
| `e`   | 5     | E exponent on c₁⁻¹ |
| `m2, m3, m4, m5` | 4×3 | face counts (max per face is cap=4 at ε⁵) |
| `last`| 1     | terminal term flag |

Total ROM depth: |types| entries × ~35 bits.  At N=4 (7 types): 245 bits
(~31 bytes).  At N=6 (18 types): 630 bits.  Negligible.

## 3. Power precomputation phase

Before term accumulation begins, precompute the shared powers:

### Phase A: c₁⁻¹ via jet_inv
Launch `spu13_jet_inv` on c[1] (the derivative p'(x₀), guaranteed unit).
Yield: `ci = c₁⁻¹` (dense jet).  Cost: 1 tower + O(N²) mults.

### Phase B: c₁⁻¹ powers (dense chain)
```
ci_pow[0] = (1,0,...)          // identity
ci_pow[1] = ci                 // from Phase A
ci_pow[k] = ci_pow[k-1] * ci   // for k = 2..max_E
```
Each step is one dense jet_mul (tag `[0,N] × [0,N]`).  Cost: max_E dense
multiplies.  At ε³: max_E = 3 → 3 dense mults (18 base products).  At ε⁵:
max_E = 7 → 7 dense mults.

Store in a local register file addressed by exponent `e`.

### Phase C: c₀ powers (sparse chain)
```
c0_pow[0] = (1,0,...)          // identity
c0_pow[1] = c[0]               // O(ε), tag [1,N]
c0_pow[p] = c0_pow[p-1] * c[0] // tag [p,N] × [1,N] → result tag [p+1,N]
```
Each step is one sparse jet_mul (windowed operands).  Cost: V_max sparse
multiplies.  At ε³: V_max=3 → 2 sparse mults (cheap).  At ε⁵: V_max=5 →
4 sparse mults.

Store in a local register file addressed by exponent `v1`.

### Phase D: face coefficient powers (scalar chain)
For each face variable `i` where max exponent `max_mi > 0`:
```
face_pow[i][0] = (1,0,...)               // identity
face_pow[i][k] = face_pow[i][k-1] * c[i+2]  // tag [0,0] × [0,0] → scalar
```
Each step is one scalar multiply (tag `[0,0]` — a single base product).
Cost: Σ max_mi base mults.  Negligible.

## 4. Term accumulation datapath

```
                    ┌─────────────┐
   schedule ROM ───▶│  controller │
   (C_m, v1, e, m)  │   (FSM)     │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
   ┌──────────┐    ┌──────────────┐   ┌──────────────┐
   │ c0_pow   │    │ ci_pow       │   │ face_pow[i]  │
   │ regfile  │    │ regfile      │   │ regfile      │
   │ [v1]     │    │ [e]          │   │ [mi]         │
   └────┬─────┘    └──────┬───────┘   └──────┬───────┘
        │                 │                  │
        │    ┌────────────▼──────────────────▼──┐
        │    │  term = C_m · c0_pow[v1]          │
        │    │        · ci_pow[e]                │
        │    │        · Π face_pow[i][mi]        │
        │    │  (chained spare jet_mul ops)      │
        │    └────────────────┬──────────────────┘
        │                     │
        ▼                     ▼
   ┌────────────────────────────────┐
   │  acc += term                   │
   │  (spu13_jet_mac in add mode    │
   │   or dedicated jet accumulator)│
   └────────────────────────────────┘
```

**Per-term multiply sequence** (factors chained into result register):
1. `C_m` (scalar integer → jet via `from_int`, tag `[0,0]`)
2. `× c0_pow[v1]` — sparse: tag `[0,0] × [v1,N]` → result tag `[v1,N]`
3. `× ci_pow[e]`   — dense:  tag `[v1,N] × [0,N]` → result tag `[v1,N]`
4. For each face `i` with `mi > 0`: `× face_pow[i][mi]` — scalar: `[v1,N] × [0,0]`
5. `acc += term` — pairwise jet add

**Critical path note:** step 3 (dense multiply) dominates.  At ε³ it's
6 base products; at ε⁵ it's 15.  This is the bottleneck identified in
`digon_recursive.py` — one dense multiply per term.

## 5. Interface

```
module spu13_series_stream #(
    parameter N = 2,           // jet truncation order (ε^(N+1) = 0)
    parameter DEGREE = 5       // polynomial degree
) (
    input  wire         clk, rst_n,
    input  wire         start,

    // Polynomial coefficients c[0..DEGREE] as jets
    // (DEGREE+1) × (N+1) × 4 × 32 bits — provisioned, not all read
    input  wire [31:0]  c_coeff [0:DEGREE][0:N][0:3],

    // Base root x0 (A31, order-0 jet)
    input  wire [31:0]  x0_z0, x0_z1, x0_z2, x0_z3,

    // Series root output (jet)
    output reg  [31:0]  x_z [0:N][0:3],
    output reg          done,
    output reg          err_singular,  // c[1] not a unit → cannot invert

    // Shared M31 multiplier
    output reg          mult_start,
    output reg  [31:0]  mult_a [0:3],
    output reg  [31:0]  mult_b [0:3],
    input  wire [31:0]  mult_r [0:3],
    input  wire         mult_done,

    // Fp4 inverter interface (for c₁⁻¹)
    output reg          inv_start,
    output reg  [31:0]  inv_z [0:3],
    input  wire [31:0]  inv_r [0:3],
    input  wire         inv_done, inv_busy, inv_flags_v
);
```

## 6. FSM phases

```
IDLE
  │ start
  ▼
TAYLOR_SHIFT       — compute c ← p(x + x₀) via Horner (degree jet_muls)
  │                   c[0] becomes O(ε), c[1] = p'(x₀)
  ▼
PRE_INV            — launch jet_inv on c[1]
  │ inv_done
  ▼
PRE_CI_POWERS      — chain: ci_pow[2..max_E] via dense jet_mul
  │
  ▼
PRE_C0_POWERS      — chain: c0_pow[2..V_max] via sparse jet_mul
  │
  ▼
PRE_FACE_POWERS    — chain: face_pow[i][2..max_mi] via scalar mult
  │
  ▼
TERM_LOOP          — for each type in ROM:
  │                   1. build term via chained jet_mul
  │                   2. acc += term
  │                   if last: → DONE
  │
  ▼
DONE               — pulse done, hold x valid
```

## 7. Cost model verification

The controller's multiply count is verified against
`software/lib/digon_recursive.py`'s `series_sparse_cost()` function.
Acceptance test: run the controller in simulation, count `mult_start`
pulses, assert equality with the oracle's predicted count for the same
(N, DEGREE, random coefficients).

Caveat (see `docs/SPARSE_JET_MAC.md` §5): the Python sparse cost model
approximates some per-term counts; the RTL's exact count is the window-
intersection formula.  Before RTL acceptance, update `series_sparse_cost()`
to the exact formula so there is a single source of truth — do not tune
the RTL to match an approximate model.

| N | Series terms | Predicted mults | Predicted towers | Predicted cycles |
|--:|:-------------|:----------------|:-----------------|:-----------------|
| 2 | 2            | 45              | 1                | 211              |
| 4 | 7            | 276             | 1                | 904              |

## 8. Non-goals (v1)

- No N=6 (ε⁷) or N=8 (ε⁹) — Newton wins at these depths per the oracle.
- No dynamic type set — the schedule is a hardwired ROM.
- No on-the-fly Taylor shift — caller pre-shifts coefficients.
- No batch inversion — this is a single-series evaluator; batch belongs
  at the Padé level.

## 9. Acceptance checklist

1. **ε³ correctness:** 20 random perturbed quintics; series root × Taylor
   shift yields p(x₀ + x) = 0 exactly in J₂.  Bit-exact vs
   `jet_ring_N.py:series_root_N` (validated 20/20 against Newton in
   `digon_recursive.py:validate_series_vs_newton`).
2. **ε⁵ correctness:** same for J₄ via `jet_ring_N.py` (validated 20/20).
3. **Multiply-count assertion:** counter vs `digon_recursive.py` predictions.
4. **Singularity trap:** c[1] with zero norm → `err_singular` asserted,
   `done` pulsed, no multiplies wasted.
5. **Annihilation:** terms where V-1 > N produce zero contribution —
   ROM includes them as `C_m = 0` (no-ops) or excludes them.  The
   controller must not hang on a term that evaluates to the zero jet.
6. `python3 run_all_tests.py` — 100% pass.
