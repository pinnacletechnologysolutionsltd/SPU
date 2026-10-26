# AOR-1 Phase A draft review — 2026-10-11

**Disposition:** freeze the review draft; retain PROPOSED status. No implementation
or execution is authorized. This records the accepted architectural clarifications,
not acceptance of an executable software or hardware profile.

## Preserved proposals

- [Architectural AOR-1 proposal](../spu_strategy/contract_spu13_algebraic_octave_aor1_2026-10-11.md)
- [Phase A software draft](../spu_strategy/contract_spu13_aor1_phase_a_2026-10-11.md)

The five accepted amendments are an explicit initial mantissa domain, zero-step
exception, preferred rather than universally canonical identity, separate bounded
and mathematical models, and expansion effort limits distinct from overflow.
I3 applies to valid normalized representations; I4 requires mathematical identity
and canonical tuple identity for the mantissa-one workload only.

## 2026-10-12 numerical amendment

The owner agreed signed64 coefficients, signed32 exponents, sufficiently wide
exact intermediates and signed128 norm output or explicit overflow. Requested
limits are 1,000,000 bits per oracle expanded coefficient, 100,000 counted oracle
operations per case, 128 bounded exponentiation-loop iterations and signed64
bounded expansion outputs. Temporary-size guards remain necessary.

The [accounting and precheck proposal](../spu_strategy/contract_spu13_aor1_accounting_review_2026-10-12.md)
defines candidate units, bit guards, a cancellation-aware monotone proof walk,
and guarded exponentiation by squaring. Its new temporary caps, exact accounting
schedule and remaining operand/failure rules require review. No AOR code or
execution is authorized. Arithmetic widths are no longer open at the initial
profile level; the execution details below remain open.

Required baseline: ordinary Surd coefficients plus a signed exponent counter with
the same checks and operations. The mixed-mantissa product (5,2,1000) times its
conjugate (5,-2,-1000) must return (13,0,0) without expansion. This experiment must
identify practical benefits rather than treating a renamed tuple as an ISA case.

## Remaining ratification items

| Item | Boundary example | Decision required before implementation |
|---|---|---|
| Intermediate arithmetic | A signed64 product plus three times another product can exceed signed128 | Sufficiently wide temporaries agreed; verify signed130 multiply accumulators and signed129 norm temporary |
| Increment operand | step(0,n) ignores numerical scale, but malformed n must still fail | Exact accepted types, increment domain and validation order |
| Zero-result multiplication | Zero times a valid operand with overflowing exponent sum | Apply exponent failure precedence or special-case zero before that check |
| Conjugation | b=-2^63 or k=-2^31 cannot be negated in the proposed widths | Check both fields; preserve destination; apply exponent-first precedence |
| Norm output | a=0,b=-2^63 gives -3*2^126, below signed128 minimum | Ratify signed128 output and explicit norm-result overflow category |
| Expansion limits | Signed32 k can request billions of coefficient bits | Numeric operation, temporary-bit and output-bit limits; independent oracle budget |
| Overflow proof | (2,-1,1) expands to identity despite positive exponent | Sound prechecks accounting for residual cancellation; no exponent-only overflow rule |
| Software validation | No binary encoding is assigned | Define malformed-input checks without inventing hardware layouts or opcodes |

These are flagged choices, not silent amendments to an executable contract.
Numerical direction is recorded; exact accounting, prechecks and remaining
precedence details remain unratified. Arbitrary-precision
mathematics avoids truncation but does not provide unlimited executable resources.

## Evidence and priorities

Existing [Lorentz CPU research evidence](SURD_LORENTZ_RESEARCH_MILESTONE_2026-10-11.md)
belongs to ordinary Surd instruction execution, not AOR. Alternating bounded
transformations do not establish that 1,000 same-direction boosts fit signed64.
AOR's proposed symbolic representation tests precisely that distinction.

| Dimension | AOR-1 status |
|---|---|
| Mathematical identities | Contract definitions and review; no Phase A executable qualification |
| Software reference/oracle/negative controls | NOT IMPLEMENTED / NOT RUN |
| RTL and ISA/state allocation | NOT AUTHORIZED |
| Synthesis, routing and timing | NOT RUN |
| Silicon and energy | UNMEASURED |

Existing CPU/ISA evidence remains scoped to its original sources and workloads.
This documentation makes no new claim about Artix-7 campaign status. Existing
physical integration remains the priority; no AOR job joins that campaign.

## Review-only commands

```bash
sed -n '1,200p' spu_strategy/contract_spu13_algebraic_octave_aor1_2026-10-11.md
sed -n '1,200p' spu_strategy/contract_spu13_aor1_phase_a_2026-10-11.md
python3 tools/doc_audit.py --actual-pass 243
git diff --check -- docs/README.md docs/AOR1_PHASE_A_DRAFT_REVIEW_2026-10-11.md spu_strategy/contract_spu13_algebraic_octave_aor1_2026-10-11.md spu_strategy/contract_spu13_aor1_phase_a_2026-10-11.md
```

243 is the previously verified repository regression count recorded in the
[software ISA semantics evidence](isa/ISA_SOFTWARE_SEMANTICS_2026-10-10.md), not
a new full-regression run or a fixed expected count for future qualification.
