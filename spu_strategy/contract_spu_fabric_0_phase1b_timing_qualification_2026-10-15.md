# SPU-FABRIC-0 Phase 1B Candidate A Timing Qualification

**Date:** 2026-10-15
**Status:** SOURCE-DERIVED TIMING QUALIFICATION — REVIEW PENDING; SCHEDULER HELD
**Parents:** `contract_spu_fabric_0_phase1b_timing_addendum_2026-10-15.md`;
`contract_spu_fabric_0_phase1b_cycle_qualification_2026-10-15.md`
**RTL timing scope:** Candidate A, W=32/64, `LANES=5`, connected
SMUL/normalizer.
**Excluded:** Phase 1B scheduler, candidate B/C evaluation, RTL simulation,
synthesis, place-and-route, and FPGA operations.

## 1. Evidence classification

This packet contains (a) a source-derived full-domain upper bound and (b) a
deterministic cycle-model maximum over all 327 Surd source cases per width in
each of the three frozen Phase 1A profiles. The calculation is separate from
the scheduler evaluator and refuses changed RTL or trace hashes.

It is **not** an independent RTL cycle measurement. The representative W32
fixture trace was hand-derived in the parent cycle packet. RTL simulation
confirmation remains a separate gate before treating this table as
RTL-cycle-qualified.

## 2. Full-domain GCD iteration bound

Let `N=2W+2`, the width of each unsigned magnitude presented to
`surd_binary_gcd3`. Its guard is
`M=N^2+3N+1`.

For either GCD phase, define `B(z)=bit_length(z)`, with `B(0)=0`. The
initial pair has `B(u)+B(v) <= 2N`. Each successful increment of
`iter_count` strictly decreases that sum:

- A common-factor iteration shifts two nonzero even operands, decreasing the
  sum by two.
- A single-even loop iteration halves one operand, decreasing the sum by one.
- With two unequal odd operands, the larger becomes
  `(larger-smaller)/2`, a positive value strictly below half the old larger
  operand; its bit length decreases by at least one.

Thus each phase performs at most `2N` counted updates. The common-even state
can transition to its odd loop at most once, and the loop has one terminal
comparison after the final update. The phase initializer costs one edge.
Therefore each phase costs at most `2N+3` edges from its initializer through
its terminal edge. Including the GCD start edge and both phase initializers,
accepted-start to GCD-done is bounded by:

`L_GCD <= 4N+6`.

Since `M=N^2+3N+1 > 2N` for these supported widths, neither phase can reach
the iteration guard. This is necessary because the normalizer reports a GCD
fault without asserting `valid`, while SMUL waits for `norm_valid`; the
bound establishes that this fault path is unreachable for N-bit inputs.
Zero operands take the explicit early paths and are no slower.

In edge terms, if GCD accepts start at edge `t`, `INIT_AB` runs at
`t+1`; the first phase must finish by `t+2N+3`; `INIT_GD` then runs at
`t+2N+4`; and the second phase must assert GCD done by `t+4N+6`. The
accepted-start to done latency is therefore at most `4N+6` cycles.

The scale shift is also bounded: the common factor of two can be removed at
most `N-1` times from N-bit operands. Its `$clog2(N+1)`-bit register holds
that count, and restoring the gcd cannot exceed either original operand.

## 3. Normalizer and SMUL handshake bound

For a nonzero numerator requiring normalization, the boundaries are:

1. SMUL accepts at edge `n`; its five products are captured.
2. SMUL detects raw overflow and raises `norm_req` at `n+1`.
3. Normalizer accepts at `n+2` and raises `gcd_start`.
4. GCD accepts at `n+3`; it asserts done no later than
   `n+3+L_GCD`.
5. Normalizer observes GCD done and raises `quotient_start` one edge later.
6. The three quotient engines accept on the following edge, then each executes
   exactly N RUN iterations in parallel.
7. Normalizer observes all quotient done signals and asserts valid; SMUL
   observes valid on the following edge and retires.

Counting each start/return boundary once gives:

`L_SMUL_normalized = L_GCD + N + 7 <= 5N+13`.

Special paths are shorter: invalid zero denominator completes on the SMUL
accepting edge (0 cycles); a valid raw-fit result completes one edge later
(1 cycle); a normalization request with both numerators zero uses the
normalizer fast path and completes in 3 cycles from SMUL acceptance.

| W | N | GCD `MAX_ITER` guard M | Domain GCD bound | Domain SMUL bound |
|---:|---:|---:|---:|---:|
| 32 | 66 | 4,555 | 270 cycles | 343 cycles |
| 64 | 130 | 17,291 | 526 cycles | 663 cycles |

These are derived upper bounds, not measured maxima and not constant-time
guarantees.

## 4. Frozen-fixture maxima

The reference command verifies every compressed trace digest, operation
counts, and per-operation equality of client, operands, and expected
semantics across `isolated`, `burst_synthetic`, and `steady_synthetic`.
Arrival times differ by profile but do not alter Candidate A intrinsic
operator service time.

| W | Source cases/profile | Normalization requests | Invalid cases | Max GCD cycles | Max SMUL cycles | Max operation |
|---:|---:|---:|---:|---:|---:|---|
| 32 | 327 | 275 | 3 | 164 | 237 | `surd_w32:random_0046` |
| 64 | 327 | 275 | 3 | 330 | 467 | `surd_w64:random_0137` |

The selected `surd_w32:min_negation_overflow` case is 107 cycles, below the
W32 fixture maximum of 237. Fixture maxima are not full-domain bounds.

The exact profile digests are:

| Profile | SHA-256 |
|---|---|
| `isolated` | `18585af72c7f65b4767e0526890424e56218af9eb20a6dbf90d943bf30c8a440` |
| `burst_synthetic` | `4db6e7458794b4a36f07d2cfd29a135f4301fb1a9e46ec73f77dc7f5b1060067` |
| `steady_synthetic` | `64359fdf2079299bbc1bfe95fe1b439f601084be288b62c9ace234dd5c4f3844` |

## 5. Reproduction and pinned sources

Run from the repository root:

```sh
python3 software/experiments/spu_fabric_0_timing_reference.py
```

The run completed and produced the values above. It uses the source-level
cycle model in `software/experiments/spu_fabric_0_timing_reference.py`,
SHA-256 `80b753da559a19b4a3fc3dada6829806846b74449513040bc52adfdc516a603d`.
The script pins these RTL inputs:

| RTL source | SHA-256 |
|---|---|
| `surd_smul_unit.v` | `0cebd08aec2cd9ea6603ae655b9a15d65d9651eca958e1935137bd6deb04fdaa` |
| `surd_normalize_unit.v` | `4d43e03f3745326a3f7d26fcf7a34219c8bc0ba1a4826a568eb3c74ab82291fa` |
| `surd_binary_gcd3.v` | `e994552b50f34017b176d91303ac6c85774748d64d4014755d0979d6fcd3097c` |
| `surd_exact_quotient.v` | `2a78246d9ab13d439ee0be88b57dd58029d1d5ed0e77fcd61d1bac4837fd15cd` |

The timing script consumes only frozen oracle `raw` tuples and status fields;
it does not derive or replace arithmetic expected values. It checks
normalization classification against the W-bit raw-fit rule and checks
invalid-denominator classification against the input operands.

## 6. Review status and remaining Phase 1B gates

This packet supplies the full-domain bound and fixture maxima requested by
the timing addendum. It does not close the RTL-confirmation gate or freeze the
final candidate schedules. The cycle packet remains review pending.

The schedule draft also needs one architectural choice before C is unique:
The schedule draft now proposes Candidate C2 with separate width-specific
W32 and W64 Surd final reducers. This is pending independent review and must
be frozen in the execution packet; it is a scheduling model, not a physical
resource measurement. No evaluator may choose C1 or another reducer mapping
implicitly.

After the cycle and timing packets and final resource schedules are reviewed,
the execution contract must freeze source/config hashes, command, output
directory, attempt count, per-attempt timeout, cumulative budget, and retry
policy. The Phase 1B scheduler remains held; no RTL simulation or hardware
operation is authorized by this timing packet.
