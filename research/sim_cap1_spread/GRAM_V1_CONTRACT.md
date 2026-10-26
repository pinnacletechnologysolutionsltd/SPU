# SIM-CAP1 `gram_v1` SPREAD — semantic and refusal contract (superseded by the frozen version for §4; see GRAM_V1_CONTRACT_FROZEN.md)

2026-10-25. Software-only. Records the six owner decisions; defines the contract that must be
frozen BEFORE any code changes. Nothing implemented, no baselines touched, nothing staged.
Supersedes the open items of `PREPARATION.md` §6.

## 1. Mathematical definition (unbounded; the oracle)
For Quadray vectors with components in Q(sqrt3) (a_i = p_i + q_i*sqrt3, p_i,q_i integers):
  B(a,b) = 4*sum_i a_i b_i - (sum_i a_i)(sum_i b_i)      (product in Q(sqrt3))
  N = B(a,a)*B(b,b) - B(a,b)^2 ,   D = B(a,a)*B(b,b)      (unreduced; spread = N/D)
Result is the pair (N, D), each a Q(sqrt3) element (p,q), written as legacy: R[d]=N, R[d+1]=D.
B(a,a) equals the VM `quadrance()` exactly (PREPARATION §2), so quadrance is not redefined.
Degenerate: B(v,v)=0 iff all four components equal (Q(sqrt3) is a subfield of R, so a sum of
squares of differences vanishes only when each difference is 0). Testable by `quadrance()==0`.

## 2. Profile selection (decisions 5, 6)
* Opcode 0x15 and its encoding are unchanged. No instruction bit.
* Manifest field `metric_semantics` in {`legacy_dot`, `gram_v1`}, independent of the existing
  `profile` (full/base) field and of `VM_PROFILES`. The existing schema is NOT otherwise changed.
* Default `legacy_dot`. Selection is fixed at VM construction (Python ctor arg; C++ ctor/CLI
  option) and cannot change mid-run. Hardware-profile changes must not alter it.
* `legacy_dot`: results bit-identical; manifest marks `qualified: false` with a note that
  spread(A,A)!=0 (e.g. 8/9 for (1,0,0,0)). Its existing tests are retained verbatim.
* Selected semantics govern: Python `spread()`, SPREAD execution, `--proof` output, C++
  `Quadray::spread()` (spu_quadray.h), C++ VM SPREAD (spu_vm.cpp:884) and their test oracles.
  Proof output under `gram_v1` prints B(a,a), B(b,b), B(a,b) (not sum a^2).

## 3. Operand form (decision 4)
Canonical: `SPREAD Rd, QRa, QRb` (assembler class `RQQ`, as implemented). The ISA reference
line `0x15 SPREAD QRd,Q1,Q2,Q3` is recorded as a **specification discrepancy**: add a
versioned clarification entry that keeps the original text (quoted, with commit provenance)
and states which description the implementations follow. Do not delete or silently rewrite.
The three-quadrance computation remains available as `spread_from_quadrances` / DELTA.

## 4. Atomic refusal (decisions 1, 2)
SPREAD under `gram_v1` either commits BOTH R[d] and R[(d+1)%NUM_REGS] with the exact (N,D),
or commits nothing and halts with a fault. A refusal leaves all registers, QR registers,
PC, step count, call stack and log unchanged (pre-instruction state). Order of checks:
1. Operand validity (existing INVALID_REGISTER rule on Rd; QR indices keep the legacy %13).
2. Degenerate metric: B(a,a)==0 or B(b,b)==0 -> fault kind **`DEGENERATE_METRIC`** (new).
   No numerical spread is ever produced; the zero denominator is never stored.
3. Representability -> fault kind **`OVERFLOW`** (existing C++ kind) if any of N.p, N.q, D.p,
   D.q lies outside int32 (the existing C++ result format). Intermediates use `Wide`
   (__int128) and are range-checked before narrowing; no wrapping, no saturation.
Python VM: no result-width limit exists for its register type, so it computes the unbounded
oracle value and never raises OVERFLOW. Conformance rule: wherever C++ returns, the pair is
identical to Python and the oracle; C++ OVERFLOW occurs iff the oracle value is outside int32.
(Whether a Python-side int32 mode is wanted is an open question, not assumed.)
Intermediate bound: for int32 components, 4*sum a_i b_i and (sum a)(sum b) fit in __int128
by a wide margin (<~2^70 per surd coefficient before products); N and D are degree 4 in the
inputs (~2^130 worst case for full-range int32 inputs), which can exceed __int128. The C++
implementation must therefore check each multiplication step against __int128 bounds, or
reject by range check on B-values first (|B| coefficients < 2^66 guarantees B*B < 2^133:
still too large). **Open item for halt-and-flag:** worst-case int32 inputs can overflow
__int128 in N/D; decide between a checked-multiply helper (`__builtin_mul_overflow` on
__int128) mapping to OVERFLOW, or a 256-bit helper. Recommended: checked multiplies ->
OVERFLOW, since any such value is far outside int32 and refusal is correct either way.
The Python and C++ `gram_v1` paths do NOT pass through the legacy `RationalSurd *` that
already throws on int32 narrowing mid-expression, so the refusal point is defined here
(final N/D range), not wherever an intermediate first exceeds int32.

## 5. Tests (independent of the implementations under test)
Oracle: `fractions.Fraction`/Python int arithmetic over (p,q) pairs written separately from
the VM; second route via `spread_from_quadrances` with Q3=B(a-b,a-b) for rational inputs.
Required: the four supplied pairs (legacy 8/9, 9/9, 48/48, 1319/1344 vs gram 8/9, 8/9,
32/48, 1200/1344); self-spread N=0 for nondegenerate (e.g. (1,0,0,0): 0/9); collinear
(1,0,0,0),(2,0,0,0): 0/36 (legacy 32/36); symmetry; the 24 coordinate permutations leave
(N,D) unchanged; adding (t,t,t,t) to either argument leaves B, N, D unchanged — a
coordinate-gauge change, not a translation; one surd-valued pair; degenerate (1,1,1,1),
(0,0,0,0) as either argument -> DEGENERATE_METRIC with no register change; boundary cases
at int32 max/min for D and N (just-fits and just-overflows, each coefficient lane) -> OVERFLOW
with R[d], R[d+1] unchanged (including the R25->R0 wrap of d+1). Legacy tests unchanged:
spu_vm_test.py:307-308, test_verification.py::test_spread_8_9, cross_validate.py,
spu_quadray_test.cpp:132-134. Cross-validation: Python vs C++ agree under each profile.

## 6. Recorded: `examples/02_quadray_orbit/quadray_orbit.sas` working-tree diff
Pre-existing, uncommitted, not by SIM-CAP1; not overwritten, reverted or attributed here.
Content (git diff): header comment and instruction forms change `ADD Rn,Ra,Rb` ->
`ADD Rn,Rs` (Rn <- Rn+Rs), `MUL` likewise, `QROT QRd,QRs` -> `QROT QRd`, and
`ADD R3,1,2` / `MUL R4,1,1` become `LD R3,2,1; ADD R3,R2` / `LD R4,2,1; MUL R4,R1`.
It does not touch the SPREAD line (line 92) or its comment. SIM-CAP1 neither depends on nor
validates it; the example's SPREAD output is legacy_dot unless the file requests gram_v1.

## 7. Boundaries (from owner)
In: Python VM, C++ headers + C++ VM, tests, proof output, manifest field, versioned ISA
clarification. Out: QROT/rotate(), RTL, GPU, AGS-0, baseline regeneration, broad regression
campaigns, hardware, silicon claims. Targeted tests only when implementation is authorized.

## 8. Stop point
Contract above is a DRAFT. Open before code: (a) freeze §4 overflow mechanics (item
flagged), (b) confirm whether Python gets an optional int32 mode, (c) confirm fault
name `DEGENERATE_METRIC`, (d) whether the C++ constructor option name is acceptable.
