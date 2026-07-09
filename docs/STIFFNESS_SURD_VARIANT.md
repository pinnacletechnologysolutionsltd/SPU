# SPU-13 Surd-Component Stiffness Variant — Proposal

The Davis stiffness formula `4Σcᵢ²` (implemented 2026-07-08) is correct and
positive-definite — but defined for scalar component inputs. SPU-13
operates on **RationalSurd** components `(p, q)` where the real value is
`p + q√3`. This proposal resolves how `4Σcᵢ²` generalises when each `cᵢ`
is a surd.

## 1. The two candidates

| Candidate | Formula | τ type | DSP cost (per component) |
|---|---|---|---|
| **Field-square (SOM convention)** | `4·Σ(pᵢ² + 3qᵢ²)` | scalar RationalSurd `(val, 0)` | 2 multiplies + 1 add (per component) |
| **Surd-square** | `4·Σ((pᵢ + qᵢ√3)²)` = `4·Σ(pᵢ²+3qᵢ²,  2pᵢqᵢ)` | full RationalSurd `(P, Q)` | 3 multiplies + 2 adds (per component) |

Both reduce to the identical scalar form when `qᵢ = 0` (SPU-4 Euclidean case).

## 2. What leaks look like in Q(√3)

A cubic leak on SPU-13 produces a vector sum `ΣQRᵢ = (sₐ, s_b, s_c, s_d)`
where each `sᵢ` is a RationalSurd. The question is: does a surd leak
component `(1, 1)` (real value `1+√3 ≈ 2.732`) carry more severity than
the pure-rational leak `(2, 0)` (real value 2)?

- **Field-square** says: severity is `1² + 3·1² = 4` for `(1,1)` and `2² + 0 = 4`
  for `(2,0)` — equal severity because both have the same Q(√3) norm.
- **Surd-square** says: severity for `(1,1)` is `(4, 2)` (a RationalSurd
  with real value `4 + 2√3 ≈ 7.46`) while `(2,0)` gives `(4, 0)` (real
  value 4) — the surd leak is ~1.87× more severe.

## 3. Which τ type does the downstream code expect?

τ is currently `RationalSurd` in both C++ and Python. In the C++ `DavisGasket`,
τ has both `p` and `q` fields, and the halving operation (`τ.p >>= 1,
τ.q >>= 1`) operates on both independently. The `ratio_product()` method
returns `τ * K` as a full RationalSurd. So **the accumulator already
accepts surd-valued increments** — no type change needed for surd-square.

## 4. Recommendation: surd-square

**Choose surd-square** `4·Σ((pᵢ + qᵢ√3)²)` for SPU-13, keeping the
field-square form for SPU-4 (which has no qᵢ=nonzero inputs).

Rationale:
1. **The accumulator already handles surd increments.** Switching to
   field-square would *discard* the surd component of leak severity —
   information the Q=0 flattening hides. A leak of `(1, 1)` on every axis
   is physically larger than `(1, 0)` everywhere, and τ should reflect
   that.
2. **No false equivalence.** Field-square collapses
   `(p, q)=(-1, 1)` (real value `√3-1 ≈ 0.732`, norm `1+3·1 = 4`) and
   `(p, q)=(2, 0)` (real value 2, norm `4+0 = 4`) to the same severity,
   despite the real magnitudes differing by nearly 3×. Surd-square keeps
   them distinguishable: `(-1,1)` → `(4, -2)` (real value
   `4-2√3 ≈ 0.536`, matching `0.732² ≈ 0.536`) vs `(2,0)` → `(4, 0)`
   (real value 4) — same field-square norm, different surd-square value.
3. **Consistency with the rest of the SPU stack.** All other RationalSurd
   operations (spread, quadrance, dot) produce RationalSurd results.
   Making τ a RationalSurd increment is consistent; making it field-square
   is the special case.
4. **The SOM convention is answering a different question.** SOM uses
   field-square (`p²+3q²`) as the Q(√3) *norm* for BMU comparison — it
   needs a total order. τ accumulation is additive, not comparative; surd
   values are fine.

## 5. Implementation impact

| Layer | Change |
|---|---|
| C++ `gasket_tick` | Already uses `vs.quadrance()` (pairwise, surd-valued) + `gs.quadrance()` (surd square of scalar sum). Components are already surd — no change needed. |
| Python VM `gasket_tick` | Same — `diff * diff` preserves surd components, `gs * gs` preserves them. No change needed. |
| RTL `davis_gate_dsp.v` | SPU-4 path unchanged (q=0 always). SPU-13 Davis gate (if separate from the SPU-4 gate) needs surd-aware squaring via `spu13_m31_multiplier` or equivalent. The existing `ivm_quadrance` + `gasket_sum²` identity `4Σc²` still holds for surds if each `c²` is a surd square. |
| Testbench | Already derives expected values from oracle functions. For the SPU-13 variant, the oracle computes surd squares. |

## 6. SPU-4 path: intentional divergence

SPU-4 Sentinel operates on 16-bit signed scalars (Q=0 always). For SPU-4,
`4ΣA²` is identical to both candidates. The current RTL implementation —
`ivm_accum + gasket_sum²`, both as 32-bit scalar integers — is correct
and minimal for SPU-4. No change needed.

## 7. Decision

**Adopt surd-square severity for SPU-13, keep scalar stiffness for SPU-4.**
The C++ and Python oracles already produce surd-valued increments through
their existing multiplication paths (`RationalSurd * RationalSurd`).
The open question is whether SPU-13 gets a separate Davis gate instance
with surd-aware squaring, or whether a unified gate handles both via a
parameter. That is an RTL design question, not an oracle question —
proceed with the RTL after this proposal is accepted.

*CC0 1.0 Universal.*
