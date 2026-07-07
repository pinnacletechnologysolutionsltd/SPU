# Montgomery Batch Inversion — RTL Contract

Contract for the batch inversion block (RTL in progress). The Python oracle
is the source of truth: `software/lib/a31_field.py::batch_tower_inv`, verified
by `software/tests/test_pade_batch_inversion.py` (25 checks). RTL acceptance
means **bit-exact agreement with the oracle**, including singular-lane
semantics — not just "inverses come out right."

## 1. What it computes

Given k denominators `d_0..d_{k-1}` in A₃₁ (basis `[1, √3, √5, √15]` over
M31), produce all k inverses using **one** Conjugate Reduction Tower run
instead of k:

```
prefix_0 = d_0                       # (k-1) A31 multiplies
prefix_i = prefix_{i-1} · d_i
T        = tower_inv(prefix_{k-1})   # 1 tower (~76 cycles, deterministic)
acc      = T                         # unwind: 2(k-1) A31 multiplies
inv_i    = acc · prefix_{i-1}        #   for i = k-1 down to 1
acc      = acc · d_i
inv_0    = acc
```

Total: `1 tower + 3(k-1) multiplies`. Inverses in a commutative ring are
unique, so any correct implementation is automatically bit-exact with the
oracle — matching the oracle's prefix/unwind *order* is still recommended so
waveform debugging lines up step-for-step with a Python trace.

## 2. Zero-divisor semantics (the part that must not be improvised)

The norm N maps A₃₁ into the field F_p and is multiplicative. Therefore
`N(prefix_{k-1}) = ∏ N(d_i)`, which is zero **iff at least one** `d_i` is
zero or a zero divisor. The tower's existing Stage-B zero check on the
accumulated product is thus an *exact* deferred test for "some lane is
singular" — no per-lane checks needed on the happy path.

On `FLAGS.V` from the tower, two implementation tiers:

- **Tier 1 (recommended for RTL v1):** abort the batch, assert `flags_v`,
  and expose a singular-lane bitmap by probing each `d_i` with a 2-multiply
  norm check (tower Stages A+B only, no Fermat — ~6 cycles/lane). Software
  re-issues the unit subset. This is what the bench needs first.
- **Tier 2 (oracle behavior):** after isolation, re-batch the unit subset in
  hardware (second tower). The oracle (`batch_tower_inv`) implements this;
  RTL may defer it. Either tier must produce: singular lanes flagged exactly,
  unit lanes bit-exact.

Do **not** skip the deferred check in favor of per-lane checks "to be safe" —
that reintroduces k norm computations the mathematics makes unnecessary, and
the uniformity of the happy path is the point of the design.

## 3. Interface and integration

- Reuse the shared-resource handshake pattern of `rplu_thimble_pade.v` /
  `spu13_jet_inv.v`: external `spu13_m31_multiplier` (mult_start/mult_done)
  and external `spu13_fp4_inverter` (inv_start/inv_done/inv_flags_v). No
  private multiplier — the SU3SHARE silicon proof established the shared-mult
  discipline.
- `busy` / `done` / `abort` pulses must be **completion-coupled** for
  `spu13_scoreboard_v2` (busy bits clear on actual done/abort, never on a
  latency assumption). Latency is variable in k by design; that is fine.
- Prefix storage: `K_MAX × 128` bits. Recommend `K_MAX = 16` for v1 — covers
  the 13-lane manifold sweep with margin; a distributed-RAM/BRAM decision is
  the implementer's, but note the Tang 25K probe budget before adding BRAM.
- Hard constraints apply: no division, no floating point, no branches in the
  hot path (control as MUX polynomials / uniform FSM steps), and no
  FIFO/skew-buffer papering over timing.

## 4. Measured budget (from the oracle, tower=76, mult=3 cycles)

Batched [4/4] Padé evaluation (Horner + inversion + final multiply):

| k | baseline cyc | batch cyc | speedup | MAC volume |
|---|---|---|---|---|
| 1 | 103 | 103 | 1.00x | +0% |
| 2 | 206 | 139 | 1.48x | +17% |
| 13 | 1339 | 535 | 2.50x | +31% |
| 104 | 10712 | 3811 | 2.81x | +33% |
| asymptote | — | — | 2.86x | +33% |

Crossover is k=2: there is no batch size that loses cycles. The +33% MAC
ceiling matters because the multiplier is shared — batch inversion belongs
where towers serialize (batched Padé/thimble runs), not as a blanket policy.

## 5. Acceptance checklist

1. Self-checking `_tb.v` under `hardware/tests/spu13/`, prints `PASS`/`FAIL`,
   calls `$finish`, discovered by `run_all_tests.py`.
2. Golden vectors generated from the oracle (`batch_tower_inv`) — random unit
   batches at k ∈ {1, 2, 3, 13, 16}, plus: one singular lane, multiple
   singular lanes, all-singular, and the same-cycle done+reissue collision
   against the scoreboard.
3. Bit-exact inverse values on unit lanes in every singular scenario.
4. `TB_FILTER=<tb_name> python3 run_all_tests.py` green, then the full suite.
5. Wire into the relevant board `.ys` only after simulation acceptance.

## 6. Cross-references

- Oracle: `software/lib/a31_field.py` (`batch_tower_inv`, `a31_norm`,
  `a31_tower_inv`) — op-for-op model of the tower incl. `FLAGS.V`.
- Oracle tests: `software/tests/test_pade_batch_inversion.py`.
- Tower RTL: `hardware/rtl/core/spu13/spu13_fp4_inverter.v` (~76 cycles).
- Shared multiplier: `hardware/rtl/core/spu13/spu13_m31_multiplier.v`.
- Hazard tracking: `hardware/rtl/core/spu13/spu13_scoreboard_v2.v`.
- Background: batch inversion is a standard primitive in ZK-prover
  implementations over M31-class fields; this block doubles as the field
  arithmetic layer for any future Circle-STARK-adjacent experiment.
