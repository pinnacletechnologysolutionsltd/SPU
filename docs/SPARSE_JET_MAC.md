# Sparse Jet MAC — RTL Contract

Contract for the sparse variant of `spu13_jet_mac` (RTL not started). The
Python oracles are the source of truth: `software/lib/jet_ring.py` for ring
semantics (the sparse variant must be **bit-exact with the dense Cauchy
product** — sparsity changes the schedule, never the values), and
`software/lib/digon_recursive.py` for the cost model that justifies building
it. RTL acceptance means bit-exact agreement with the dense path plus a
verified multiply count — not just "results come out right."

## 1. Why it exists

The digon-recursive series evaluator (revised verdict, AGENTS.md) beats
Newton-Hensel at eps^3 (211c vs 506c) and eps^5 (793c vs 1569c) **only if**
the jet multiplies exploit operand sparsity. The dense `spu13_jet_mac` issues
all (N+1)(N+2)/2 base products per multiply regardless of which channels are
zero. In the series datapath the operands are highly structured:

| Operand              | Populated eps channels | Window `[lo, hi]` |
|----------------------|------------------------|-------------------|
| c0 (Taylor-shifted)  | 1..N (it is O(eps))    | `[1, N]`          |
| c0^p                 | p..N                   | `[p, N]`          |
| c1^-1 and its powers | all (dense, from `spu13_jet_inv` reassembly) | `[0, N]` |
| Face coeffs c2, c3.. | eps^0 only (A31 scalars) | `[0, 0]`        |

A scalar-by-jet multiply needs one base product per populated channel of the
jet, not a full Cauchy product. Skipping the guaranteed-zero products is
where the 2.4x at eps^3 comes from.

## 2. What it computes

Identical ring semantics to `spu13_jet_mac`: the truncated Cauchy product in
F_{p^4}[eps]/(eps^(N+1)),

```
(J*K)_k = SUM_{i=0}^{k} j_i * k_{k-i}       for k = 0..N
```

Each operand additionally carries a **nilpotency window tag** `[lo, hi]`,
a promise that all channels outside `lo..hi` are zero:

```
j_i = 0  for i < j_lo or i > j_hi     (and likewise for K)
```

**Skip rule.** The base product `j_i * k_{k-i}` is issued to the shared
multiplier iff

```
j_lo <= i <= j_hi   AND   k_lo <= (k-i) <= k_hi
```

All other (i, k-i) pairs contribute an exact zero and are never launched.
This is value-blind: it uses only the tags, so the schedule (and cycle count)
is data-independent — no branches on operand values, per the hot-path rule.

**Tag algebra.** The result tag is computed combinationally from the input
tags, before any multiply launches:

```
r_lo = j_lo + k_lo                    (clamped to N+1)
r_hi = min(N, j_hi + k_hi)
```

- If `r_lo > N` the product is **annihilated** by eps^(N+1) = 0: the block
  writes an all-zero result with tag `[N+1, 0]` (canonical empty window),
  pulses `done`, and issues **zero** multiplies.
- The dense case `[0, N] x [0, N]` degenerates to exactly the schedule of
  the existing `spu13_jet_mac` — same products, same order. Dense is a
  special case, not a separate mode.

Note `r_lo` is a guarantee, not a claim of exactness: channel `r_lo` of the
result *can* still be zero by value (e.g. j_{lo} * k_{lo} = 0 in a ring with
zero divisors... A31 products of units are units, but sums of base products
can cancel). Tags only ever promise zeros, never non-zeros. Downstream
consumers must not sharpen a tag based on observed values — that would make
the schedule data-dependent.

**Addition** (`op_mul = 0`) stays single-cycle pairwise, with
`r_lo = min(j_lo, k_lo)`, `r_hi = max(j_hi, k_hi)`.

## 3. Tag integrity — the part that must not be improvised

A wrong tag (a non-zero channel outside `[lo, hi]`) silently corrupts the
result: the skipped products are simply absent from the sum. The hardware
**trusts tags**; it must not scan operand channels to verify them (that
reintroduces the reads the tags exist to avoid, and makes timing
data-dependent).

Consequences:

- Tags originate in the sequencer/series-controller, which knows them
  **statically** from the term structure (the table in §1). They are wired
  constants of the schedule, not computed from data.
- Simulation must check the promise: a testbench-side monitor asserts, on
  every `start`, that all operand channels outside the declared windows are
  zero. Violation is a FAIL, not a warning.
- The zero-divisor / unit check changes meaning: a jet is a unit iff its
  eps^0 channel is a unit, i.e. `lo = 0` **and** c0 passes the norm check.
  Any operand with `lo >= 1` is nilpotent by construction — do not route it
  to `spu13_jet_inv`. `err_zero_divisor` on the sparse MAC itself should
  fire only where the dense block would fire (multiplicative-identity path),
  so dense-equivalence holds flag-for-flag.

## 4. Interface and integration

Extend the `spu13_jet_mac` port list minimally; keep the shared-resource
discipline:

- Same external `spu13_m31_multiplier` handshake (`mult_start`/`mult_done`,
  four-component operand/result buses). No private multiplier — the SU3SHARE
  silicon proof established the shared-mult rule, and the batch inverter
  (2d8658b) established the mux pattern.
- New inputs: `j_lo`, `j_hi`, `k_lo`, `k_hi` (4 bits each is enough through
  eps^15). New outputs: `r_lo`, `r_hi`, registered with the result.
- `busy`/`done` must be **completion-coupled** exactly as fixed in the batch
  inverter scoreboard-collision work (dd4ebdf): `done` pulses one cycle,
  `busy` covers the whole operation including the zero-multiply annihilation
  path (which still takes its FSM transit cycles — `done` must never be
  combinationally simultaneous with `start`).
- FSM: reuse the dense block's LAUNCH/WAIT/COMBINE structure. The sequencer
  change is confined to index generation: for order k, `i` runs over
  `max(j_lo, k - k_hi) .. min(j_hi, k - k_lo)` (empty range → order k is
  written as zero with no launch), and `k` runs over `r_lo .. r_hi` with
  orders outside that window written as zero.
- Keep the module Lithic: if the windowed index generator wants to grow,
  split it into `spu13_jet_idx.v` rather than inflating the MAC.

## 5. Cost accounting

The exact multiply count is the window-intersection count:

```
mults(J, K) = SUM_{k = r_lo}^{r_hi}  max(0, min(j_hi, k - k_lo) - max(j_lo, k - k_hi) + 1)
```

Reference points at N = 2 (eps^3): dense x dense = 6, scalar x dense = 3,
c0 x c0 = 1, scalar x scalar = 1, c0 x c0^2 = 0 (annihilated).

Note: `digon_recursive.py`'s sparse cost model approximates some of these
counts (e.g. it charges `p+2` for the c0-chain step and `v1+1` for
scalar-by-jet, rather than the exact window intersection). The window rule
is the *minimal* value-blind schedule, so the RTL will meet or beat the
oracle's totals term-by-term at eps^3/eps^5; once RTL lands, update
`digon_recursive.py` to the exact formula above so the cost tables and the
hardware counters agree number-for-number.

## 6. Acceptance checklist

1. **Dense equivalence:** random jets tagged `[0, N]` produce bit-identical
   `r_coeff` and flags to the existing `spu13_jet_mac` (same-vector A/B run
   in one testbench).
2. **Sparse correctness:** random jets *conforming to* random windows,
   result bit-exact vs `jet_ring.py` dense reference; includes windows
   `[0,0]`, `[1,N]`, `[p,N]`, `[N,N]`, and the annihilation case.
3. **Multiply-count assertion:** testbench counts `mult_start` pulses and
   asserts exact equality with the §5 formula for every vector. This is the
   point of the block — a correct-but-dense implementation must FAIL.
4. **Tag-integrity monitor:** operands violating their window are caught by
   the testbench monitor (negative test: deliberately mis-tagged vector must
   trip the monitor, proving the monitor is alive).
5. **Annihilation path:** `r_lo > N` issues zero multiplies, returns the
   zero jet, and still exhibits correct `busy`/`done` pulse discipline
   (scoreboard-collision test per the batch-inverter precedent).
6. **Golden vectors:** commit a `.mem` golden file regenerated from the
   Python oracle (pattern: `spu13_batch_inv_golden.mem`), including
   ordering-adversarial cases.
7. `python3 run_all_tests.py` — 100% pass, including the untouched dense
   `spu13_jet_mac_tb.v`.

## 7. Non-goals (v1)

- No value-level zero skipping (data-dependent timing — forbidden).
- No sharpening of output tags from observed values (same reason).
- No sparse variant of `spu13_jet_inv`: c1^-1 is dense by construction, and
  the inverse's input must have `lo = 0` anyway. The dense jet_inv stays.
- The series-stream controller (SRU) that *drives* this block with the
  digon-lattice schedule is a separate module and a separate contract —
  this document covers only the tagged MAC primitive.
