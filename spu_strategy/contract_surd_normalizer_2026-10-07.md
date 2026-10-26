# Exact Surd normalizer

## Scope

Implement a standalone normalizer for the exact tuple `(A,B,D)` representing
`(A+B*sqrt(3))/D`. Do not add a register bank, ISA operation, CPU/GPU integration,
or alter sidecar work. Feed the normalizer from the existing Surd multiply's
wide-result handshake in a later integration change.

## Representation and widths

1. Set `N = 2*W+2`.
2. Accept signed `A` and `B` in `N` bits and unsigned `D` in `2*W` bits.
3. Reject `D==0`; do not assert `valid` and do not modify the caller's
   destination.
4. Form unsigned magnitudes `MA=abs(A)` and `MB=abs(B)` in N bits. Convert a
   negative input with width-preserving two's-complement inversion and add-one;
   this must represent `abs(-2^(N-1)) == 2^(N-1)`.
5. Zero is canonicalized to `(0,0,1)` whenever `A==0 && B==0 && D>0`.
6. For nonzero numerator, calculate `G=gcd(MA,MB,D)`, and calculate all three
   exact quotients `QA=MA/G`, `QB=MB/G`, and `QD=D/G`. Quotient datapaths are
   unsigned N-bit values. Check all three remainders are zero before sign
   restoration or commit.
7. Restore the signs of A and B. A negative magnitude `2^(W-1)` may encode
   `-2^(W-1)`; a positive magnitude must be at most `2^(W-1)-1`. Require
   `QD` in `[1,2^W-1]`. Return the reduced tuple at wide width with a
   `fits_W` status; destination fit and commit remain the caller's operation.

## GCD algorithm and bound

1. Implement the two-input Stein binary-GCD step using unsigned N-bit values:
   return the other operand when either is zero; remove common factors of two
   while both are even; then iterate until equal, shifting an even operand right
   by one, or replacing the larger odd operand with `(larger-smaller)>>1`.
2. Compute the three-input GCD as `g1=gcd(MA,MB)` followed by `G=gcd(g1,D)`.
   The second phase reuses the same GCD datapath.
3. Bound each pairwise phase to `N*N+3*N+1` arithmetic iterations. Common-factor
   removal takes at most N iterations. Afterward, each odd/odd subtract-and-half
   iteration halves the positive operand sum, so there are at most N+1 such
   iterations. Between them, at most N single-operand shifts are needed to make
   an even operand odd. A phase exceeding the bound raises `fault`, never
   `valid`.
4. GCD of `(0,0,D)` is handled by the canonical-zero bypass. For `(0,B,D)` or
   `(A,0,D)`, the zero-operand rule in Stein GCD applies.

## Exact quotient algorithm

1. Instantiate three unsigned restoring quotient engines, each with N fixed
   iterations, using only shift, compare, and subtract operations.
2. Use an N+1-bit remainder register. Shift in one dividend bit per iteration;
   subtract the zero-extended divisor when the shifted remainder is greater or
   equal, and set the corresponding quotient bit.
3. Reject divisor zero. At the final iteration require remainder zero for all
   three quotients. Any nonzero remainder raises `fault`, never `valid`.
4. Synthesizable RTL must contain no runtime `/` or `%` operators and must not
   infer divider or modulo cells.

## Handshake and state preservation

1. Accept `start` only in `IDLE`; latch all inputs on the accepting edge.
2. Ignore `start` while busy. Assert `busy` until one terminal result is
   available. Pulse `valid` for one cycle on a successful normalized tuple.
3. On `D==0`, assert `invalid` with a one-cycle `done`; do not assert `valid`.
4. On iteration-bound, divisor, or remainder failure, assert `fault` with a
   one-cycle `done`; do not assert `valid`.
5. On success, return a mathematically equivalent canonical tuple and `fits_W`.
   The caller commits only when `fits_W` is true. Otherwise it preserves the
   destination and reports overflow.
6. Reset clears status and returns the unit to `IDLE`; no partial result may be
   committed on reset or any failure.

## Verification commands

```bash
python3 software/tests/test_surd_wide_rtl_vectors.py --output-dir build/spu_surd_register/mul_arch_20261007/wide_correctness_04 --widths 32 64 --lanes 1 2 5
TB_FILTER=surd_register python3 run_all_tests.py
bash tools/verify_repo.sh
```

Run any synthesis or full regression expected to exceed 60 seconds through
`tools/run_detached_job.sh` with a new `build/` evidence directory, desktop
notification, frozen timeout, and owner-authorized campaign budget.

## Acceptance

1. Prove magnitude conversion for signed minimum and both signs at W=16/32/64.
2. Verify canonical zero, one-zero numerator, unit GCD, shared odd/even factors,
   GCD greater than one, denominator zero, and all three exact quotient results.
3. Drive Python-oracle W=32/64 vectors through the normalizer and multiply
   handshake for LANES=1/2/5. Compare raw tuple, normalized tuple, valid/invalid/
   fault/overflow status, and destination preservation.
4. Check the real-intermediate witness `A=2^128` at W=64 in its 130-bit signed
   input without truncation; verify reduction and commit/overflow behavior.
5. Assert the GCD transition bound, exactly N quotient iterations, one-cycle
   `valid`/`done` pulses, and no state update on failed normalization.
6. Inspect synthesized RTLIL/netlist to confirm no `$div`, `$mod`, or mapped
   divider/modulo cells.
7. Record simulation and synthesis evidence. Do not claim board timing, CPU/GPU
   integration, or silicon verification.
