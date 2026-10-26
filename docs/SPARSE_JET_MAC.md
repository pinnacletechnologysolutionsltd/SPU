# Sparse Jet MAC — RTL Contract

Corrected contract, 2026-10-10. Software checks are bounded to N=2 and N=4;
Software qualification is COMPLETE within the frozen N=2/N=4 scope.
RTL proceeds under a [separate implementation contract](../spu_strategy/contract_sparse_jet_mac_rtl_2026-10-11.md).

Contract for the standalone sparse variant of `spu13_jet_mac`. RTL and
focused simulation are implemented; frozen standalone qualification is COMPLETE
within its recorded simulation scope. Sparse mapping, timing and core integration
remain unverified. See
[RTL review](SPARSE_JET_MAC_RTL_REVIEW_2026-10-11.md). The
Python oracles are the source of truth: `software/lib/jet_ring.py` for ring
semantics (the sparse variant must be **bit-exact with the dense Cauchy
product** — sparsity changes the schedule, never the values), and the independent polynomial oracle in
`software/tests/sparse_jet_reference.py`. The historical
`software/lib/digon_recursive.py` workload model is approximate and does not
qualify the primitive multiply counts or projected speedup. RTL acceptance means bit-exact agreement with the dense path plus a
verified multiply count — not just "results come out right."

## 1. Why it exists

The digon-recursive series evaluator (revised verdict, AGENTS.md) beats
Newton-Hensel at eps^3 (211c vs 506c) and eps^5 (904c vs 1569c) **only if**
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
the intended optimization. Historical cycle and speedup figures above are
model estimates, not qualified sparse hardware performance.

## 2. What it computes

Identical ring semantics to `spu13_jet_mac`: the truncated Cauchy product in
A31[eps]/(eps^(N+1)),

```
(J*K)_k = SUM_{i=0}^{k} j_i * k_{k-i}       for k = 0..N
```

A31 is the split biquadratic algebra over p=2^31-1, with basis
[1,sqrt(3),sqrt(5),sqrt(15)], not a field. Nonunits are valid MAC operands.
Each coefficient is four canonical residues 0..p-1 in 32-bit lanes.

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

- An empty input tag `[N+1,0]` makes the product empty immediately.
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

**Addition** (`op_mul = 0`) uses pairwise addition and the same completion
protocol. An empty input is the tag-union identity; both empty returns
`[N+1,0]`. Otherwise `r_lo = min(j_lo,k_lo)`, `r_hi = max(j_hi,k_hi)`.
No cycle equivalence with the existing dense RTL is claimed.

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
- Valid tags are exactly `0<=lo<=hi<=N` or `[N+1,0]`; other tags are
  rejected by the software monitor. Hardware validation of malformed tags
  is outside this software tranche.
- Valid addition/multiplication returns `err_zero_divisor=0`, including
  nonzero zero divisors. The dense MAC never asserts this flag; it has no
  multiplicative-identity fault path. Inversion is separate: the constant
  coefficient must be a unit, tested by norm, and a tag alone cannot prove it.

## 4. Interface and integration

Extend the `spu13_jet_mac` port list minimally; keep the shared-resource
discipline:

- Same external `spu13_m31_multiplier` handshake (`mult_start`/`mult_done`,
  four-component operand/result buses). No private multiplier — the SU3SHARE
  silicon proof established the shared-mult rule, and the batch inverter
  (2d8658b) established the mux pattern.
- New tags use `TAG_BITS=ceil(log2(N+2))`, five bits at N=15. Compute
  sums with `TAG_BITS+1` bits before clamping; empty lo=16 must not wrap.
- Proposed sparse completion protocol (not existing dense timing): start is
  sampled only in IDLE; acceptance captures operands and tags. Starts while
  busy or on the completion edge are ignored. A next request may be accepted
  on the following edge. `done` pulses for one cycle; busy stays high from
  acceptance through every issue/wait/retirement phase and drops on completion.
  No busy=0/done=0 gap may occur before completion. No request completes on
  its acceptance edge, including empty multiplication and addition.
- Issue one shared multiply per scheduled pair, in increasing result order
  and source index. Pulse `mult_start` once, then wait for one `mult_done`
  response before advancing. At most one multiply is outstanding. A stalled
  multiplier leaves busy asserted indefinitely; it must not fabricate done.
- Retirement publishes result and tag together, once, after all responses.
  The software contract uses ISSUE/WAIT/RETIRE states; physical latency and
  RTL implementation are unverified. Dense RTL has a pre-done busy gap;
  compare its arithmetic/flags, not its busy/done trace, against this contract.
- Reset dominates every phase, cancels the operation, clears busy/done/start
  and the result, and sets the empty result tag. Shared-fabric reset or drain
  must complete before accepting another request. Responses outside WAIT are
  ignored. An untagged old response in a new WAIT cannot be distinguished;
  this primitive alone cannot promise stale-response protection. No epoch
  interface or transport change is introduced by this tranche.
- Keep the module Lithic: if the windowed index generator wants to grow,
  split it into `spu13_jet_idx.v` rather than inflating the MAC.

## 5. Cost accounting

The exact multiply count is the window-intersection count:

```
mults(J, K) = SUM_{k = r_lo}^{r_hi}  max(0, min(j_hi, k - k_lo) - max(j_lo, k - k_hi) + 1)
```

Reference points at N = 2 (eps^3): dense x dense = 6, scalar x dense = 3,
c0 x c0 = 1, scalar x scalar = 1, c0 x c0^2 = 0 (annihilated).

`digon_recursive.py` approximates counts using `p+2` and `v1+1`.
At N=4, `[1,4] x [1,4]` requires six products versus modeled three;
`[0,0] x [1,4]` requires four versus modeled two. Exact scheduling therefore
need not meet or beat those old term estimates. Preserve historical tables
as approximate evidence; audit full workloads separately before revising
performance claims or the production cost model.

The software oracle independently enumerates rectangular source indices,
checks the exact formula and order-major candidate schedule, and compares
coefficients with polynomial-basis multiplication. Execute:

```bash
python3 -B software/tests/test_sparse_jet_mac_oracle.py
```

All 305 ordered window pairs at N=2/N=4 are covered. N=15 has a tag-width
boundary control only. Protocol simulation validates the proposed contract,
not RTL, timing, resources, or arbitrary multiplier/reset implementations.

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
