# Integer baseline capability specification for the retained Surd kernel

Date: 2026-10-07. Status: offline preparation; executable canonical baseline
UNSUPPORTED. ISA implementation and hardware campaigns are outside this scope.

## Inspect and verify preparation

```bash
cat build/spu_surd_register/main_cpu_integration_20261007/implementation_freeze_01/snapshots/knowledge/isa_reference.md
cat build/spu_surd_register/main_cpu_integration_20261007/annex_draft_02/normalization_accounting.json
cat software/experiments/surd_cpu_kernel_schedule.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/spec_surd_integer_baseline_capabilities_2026-10-07.md docs/blog/exact_surd_progress_2026-10-07.md
```

Read the [frozen integration annex](../build/spu_surd_register/main_cpu_integration_20261007/annex_draft_02/annex.md)
and [implementation manifest](../build/spu_surd_register/main_cpu_integration_20261007/implementation_freeze_01/manifest.json).
Preserve their identities and historical results. Use the canonical dispatch
port, not the WF adapter or its instruction table. Allocate no new opcodes.

## Fix the comparison boundary

Use all 32 retained records at chain lengths N=1,3,6,12 from
`build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json`.
Keep rational-only joint coefficients separate from radical diagnostics.
Compute inverse coefficients on the baseline CPU: F'=F*F-G*H,
G'=H*H-F*G, H'=G*G-F*H. Execute forward transforms, then reversed inverse
transforms. Preserve A and normalize all four components after every joint.
Retain zero, repeated and identity terms. Include coefficient transfers,
inverse-result spills/reloads, complete result readback and issue/retirement
control. Exclude boot/reset consistently with the retained Surd measurement.

Require per-record algebraic operation counts `24*N MUL`, `12*N ADD`,
`3*N SUB`, `8*N boundary reductions`: `47*N` before transfers and control.
These are tuple operations; do not label them integer instruction counts.
Count the actual baseline integer retirements only after an executable
implementation exists. Count equal-data commits and the unchanged A reduction.

## Map every required operation to capabilities

| Required work | Exact integer algorithm and width at W=64 | Missing established canonical capability |
|---|---|---|
| Tuple load/store/readback | Three 64-bit fields; six 32-bit slices; signed a,b and unsigned positive d | General integer register/storage addressing, full-width transfer and deterministic readback |
| Snapshot and temporary storage | Snapshot both operands before writes; store exact intermediate limbs and status | Independent integer operands, temporary limbs, atomic tuple commit and initialized-state tracking |
| Surd MUL | Five products ac,be,ae,bc,df; `ac+3be`, `ae+bc`, `df`; signed real 130 bits, radical 129 bits, denominator unsigned 128 bits | Full-width signed and unsigned products, product high limbs, carry/borrow propagation and wide accumulation |
| ADD/SUB alignment | `G=gcd(d,f)`, `u=f/G`, `v=d/G`; factors unsigned 64 bits | Unsigned comparison, shifts/subtracts and bounded exact GCD/quotient sequencing |
| ADD/SUB products and sums | `a*u ± c*v`, `b*u ± e*v`, `d*u`; signed products 128 bits, sums 129 bits, denominator unsigned 128 bits | Mixed signed/unsigned full-width products and wide carry/borrow arithmetic |
| Raw destination fit | Check signed 64-bit coefficients and `1<=D<=2^64-1` without narrowing | Width/range tests and predicate-controlled commit preserving all destination fields |
| Overflow rescue | Reduce exact raw tuple once, retry fit, otherwise preserve destination | Exact normalization sequence, conditional result selection and terminal overflow reporting |
| Scheduled reduction/copy | `G=gcd(abs(A),abs(B),D)`; divide all three exactly; preserve signs | Unsigned magnitude including signed minimum, bounded three-input GCD, exact quotient with verified zero remainder |
| Zero semantics | Raw fitting zero retains `(0,0,D)`; SNORM/rescue canonicalizes valid zero to `(0,0,1)` | Explicit predicates and representation-preserving copy/commit semantics |
| Status and failure | Invalid, overflow, engine fault and encoding fault; no partial writes | Distinct status/readback and failure-preserving atomic tuple update |
| Execution control | CPU performs all arithmetic; host transports unchanged packets/results | Programmable bounded sequencing with predicates/selection or a verified conditional loop path |

Use bounded shift/compare/subtract GCD and restoring quotient algorithms from
the [normalizer contract](contract_surd_normalizer_2026-10-07.md) when designing
a future RTL baseline. Check exact remainders before commit. Supply a reviewed
sequence before implementation; do not infer runtime divider/modulo hardware.
Implement hot-path selection with multiplexer Boolean polynomials under the
root contract. A fixed bounded predicated sequence may replace a loop if its
instruction count and termination semantics are explicitly verified.

Existing LD/ADD/SUB/MUL names, QSUB, JMP/CALL/RET and experimental Surd
instructions do not establish the missing general integer execution path.
Do not use Surd microengine work as integer baseline work or substitute host
Fraction timing, ARM estimates, or one integer multiply for the full kernel.

## Require a concrete future baseline before comparison

Freeze an executable schedule, operand/limb widths, register/spill inventory,
source hashes and clock/configuration identity under separate authorization.
Verify ADD/SUB alignment with unsigned factors above `2^63-1`, minimum signed
magnitudes, fitting zero, rescued overflow, source/destination aliases,
invalid inputs, exact-remainder faults and failure preservation. Compare
complete forward/recovered tuples at every scheduled boundary against an
independent exact oracle. Measure cycles, integer retirements, alignment work,
rescues, reductions and transfers under the same scope as the Surd path.

Keep baseline status UNSUPPORTED and speedup/instruction elimination/energy
UNMEASURED until those capabilities execute and pass in canonical core RTL.
This capability inventory supplies no implementation or campaign authorization.
