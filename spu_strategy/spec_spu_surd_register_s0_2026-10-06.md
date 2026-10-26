# SPU Surd Register S0 — executable software semantics

Date: 2026-10-06 (Pacific/Auckland)
Status: software-only study; no ISA encoding or production-path change.

## Commands

```bash
timeout --kill-after=5s 60s python3 software/tests/test_surd_register_s0.py
timeout --kill-after=5s 60s python3 software/experiments/surd_register_s0_runner.py
git diff --check -- spu_strategy/spec_spu_surd_register_s0_2026-10-06.md software/experiments/surd_register_exact.py software/experiments/surd_register_model.py software/experiments/surd_register_candidates.py software/experiments/surd_register_rotation.py software/experiments/surd_register_workload.py software/experiments/surd_register_s0_runner.py software/experiments/surd_register_s0_report.py software/tests/test_surd_register_s0.py
```

## Value and operation contract

Represent `R(a,b,d)=(a+b√3)/d`. For lane width W, `a,b` are signed W-bit
integers and `d` is unsigned W-bit with `1 <= d <= 2^W-1`. Architectural load
rejects booleans, non-integers, zero or negative denominators and out-of-range
fields without modifying the destination. Signed import is a distinct helper:
it normalizes the sign and common GCD with wide integers, then checks fit.
Unreduced nonzero triples are valid. Canonicalization divides all fields by
`gcd(|a|,|b|,d)`; zero is `(0,0,1)`. Mathematical equality compares both
cross-products using wide integers; raw triple equality is separate.

Exact operations before policy checks are:

* `ADD/SUB`: let `g=gcd(d1,d2)`, `u=d2/g`, `v=d1/g`; return
  `(a1*u ± a2*v, b1*u ± b2*v, d1*u)`.
* `MUL`: `(a1*a2+3*b1*b2, a1*b2+b1*a2, d1*d2)`.
* `NEG`: `(-a,-b,d)`; `CONJ`: `(a,-b,d)`; `NORM`: common-GCD reduction.
* `EQ`: `(a1*d2==a2*d1) and (b1*d2==b2*d1)`.

Three policies are compared: EAGER normalizes before destination fit;
FIT_RESCUE preserves a fitting unreduced value, otherwise normalizes once and
retries; BOUNDARY preserves unreduced results and reports destination overflow
without implicit rescue. All policies canonicalize zero. Intermediate capacity
is checked before normalization. Results report `OK`, `INVALID_INPUT`,
`INTERMEDIATE_OVERFLOW`, or `DESTINATION_OVERFLOW`, operation, required widths
and named intermediate failures. Failed operations preserve destination
state. Wide fallback is explicit and records re-entry; nonresident wide values
are not labeled as registers.

The full-range sufficient widths are parameterized as follows:

| Operation intermediate/result | Sufficient width |
|---|---:|
| ADD/SUB scaled numerator products | signed `2W` |
| ADD/SUB accumulators | signed `2W+1` |
| ADD/SUB denominator LCM product | unsigned `2W` |
| MUL products, including `3*b1*b2` | signed `2W+1` |
| MUL a accumulator | signed `2W+2` |
| MUL b accumulator | signed `2W+1` |
| MUL denominator product | unsigned `2W` |
| Rotation products and numerators | signed `2W+2` |
| Rotation denominator `2D` | unsigned `2W+1` |
| EQ signed component × denominator | signed `2W` |
| NORM magnitude and quotients | unsigned `W`, result lanes W |

These cover one operation on valid lane inputs, not an unbounded chain. At
W=64 the MUL a witness `a1=a2=b1=b2=-2^63` produces `2^128`; NEG of
`INT64_MIN` needs a wider intermediate. GCD magnitude uses unsigned handling.

The optional paired rotation macro computes both outputs from operand
snapshots, rejects destination alias overlap, permits source/destination
aliasing, and commits neither output unless both fit. It is a software-tested
macro only. Division, ordering, fused multiply-add, inverse instructions,
opcode allocation and physical register selection are excluded.

`surd_register_exact.py` is the unbounded integer algebra;
`surd_register_model.py` applies lane and policy checks;
`surd_register_candidates.py` models fixed/shared storage;
`surd_register_rotation.py` models the atomic paired macro.

## Frozen workload and evidence

The retained cohort is all 32 inputs from
`build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/inputs.json`
(SHA-256 recorded in the S0 plan). It uses the maintained joint catalog at
chain lengths 1, 3, 6 and 12. Its joints have rational-only coefficients
(`b=0`). The unchanged maintained `fk_chain`/`inverse_fk_chain`, the existing
fused unshared kernel and an independent Fraction coefficient-pair oracle are
compared. Synthetic cases with both Surd coefficients nonzero are kept in the
focused operation tests and reported separately.

Fixed scale is derived by LCM over the frozen retained coefficient
denominators; shared blocks use N=4 for vector coefficients and N=3 for joint
coefficients. The explicit candidate uses (a,b,d), with positive unsigned
denominator and canonical zero. Full-range formula limits are parameterized
from W; observations from the retained chain are not proofs of those bounds.
The output boundary is after each completed joint in the forward and reverse
chain stages. Timings are not part of S0.

Each command is capped at 60 seconds, with SIGTERM at the deadline and SIGKILL
after a five-second grace period. This preserves timeout's 124 exit code for
the terminal record. The focused test's import failure,
accumulator-control failure and FIT_RESCUE expectation failure are preserved
under `build/spu_surd_register/s0_20261006/focused/`. The two repair cycles
for that command are exhausted; post-failure edits therefore have no passing
focused-test terminal record. Corpus status and focused-test status remain
separate in the report.

No RTL, synthesis, board, firmware, serial, ISA encoding, hardware or device
equivalence operation is authorized. Hardware operations = 0;
device_equivalence_tested = false.
