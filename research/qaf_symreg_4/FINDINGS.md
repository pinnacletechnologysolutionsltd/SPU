# SYMREG-4 — portable proof-certificate experiment

**PASS — BOUNDED DISCOVERY.** A standard-library-only checker independently
verified deterministic certificates emitted from the SYMREG-1, SYMREG-2 and
SYMREG-3 proof examples. This is a software experiment, not a general theorem
prover, ISA or RTL verification, production security mechanism, or v0.2
qualification. The [specification](SPECIFICATION.md) defines the format,
resource bounds and trusted-context assumptions.

## Correctness and portability

Nine focused test groups passed. The generator adapts real predecessor fact,
sparse-path and two-branch join objects to canonical JSON. The independent
checker imports no SYMREG inference or proof-validation module. A test writes
the resulting context and certificate to a disposable directory and invokes
`checker.py` in a separate isolated Python interpreter; the valid example is
accepted and a non-canonical mutation is refused. This shows replay across
process boundaries under the **same supplied trusted context**, not an
authenticated identity service.

The checker validates every context premise against exact concrete integer
values, validates earlier-step references and branch ownership, recomputes
supported composition and norm rules, and requires one matching witness for
every declared branch. It distinguishes a resource-limit refusal from invalid
input and refuses duplicate JSON keys and non-canonical encodings. Ninety
systematic small-domain value examples and their 90 norm projections passed
an independent `Fraction` oracle. Tests also reject unknown and false premises
(including an unused false context premise), cross-branch references, wrong norm
scales, unsupported rules/scales, malformed references, missing or swapped
witnesses, changed context/scope, stale current bindings, excessive size, value
and premise counts, step count and proof depth. They do not prove all possible
JSON inputs or the full checker implementation.

The context owner must supply authentic values, an authentic declared-feasible
branch set and a scope ID that is not reused across identity epochs. The SHA-256
digest binds the certificate to the supplied canonical context and detects an
unchanged certificate presented with a changed context; it is **not** a
signature or authentication. A party able to rewrite both context and
certificate can rebind the digest. An identical replay under a reused scope is
indistinguishable. Branch feasibility is assumed, not independently proved.
The verifier checks mathematical relations, not authorization to run code or
fixed-width machine execution.

## Formal verification record

Z3 4.15.5, QF_BV, checked [verification.smt2](verification.smt2) under a
25-second solver limit, 30-second external timeout and 1-GiB address-space
limit. Coefficients/scales are signed 3-bit, widened to 16 bits; the checked
products fit that wider range. Boolean branch guards and proof soundness are
assumptions of the abstract model. `UNSAT` means no counterexample in the
encoded scope, `SAT` gives a witness, and `UNKNOWN`/timeout is inconclusive.

| Property | Result | Deliberate negative control |
|---|---|---|
| Norm projection after scaling/conjugation uses `k²`. | `UNSAT` counterexample | Using `k` is `SAT` at `a=1,b=0,k=2`. |
| All declared-feasible, sound branch witnesses imply no false covered path. | `UNSAT` counterexample | Any-branch coverage is `SAT` with A proven and feasible B false/unproven. |
| One 2-bit identity increment cannot equal its previous value. | `UNSAT` equality | Register-only matching is `SAT` for old `0`, new `1`. |

These formulas do not encode or prove the Python checker, context authenticity,
branch feasibility, arbitrary identity wrap, or 64-bit ISA behavior. Independent
tests provide separate finite implementation evidence. No timeout occurred.

## Size and cost

One run of 30 checks per example on Python 3.10.12 produced the following
median verifier times. Allocation peaks are `tracemalloc` measurements of a
separately traced verification, including parser/checker allocations, not
total process memory. Context sizes are separate from certificate sizes.

| Source example | Certificate / context bytes | Steps | Used premises | Maximum depth | Branches | Median check | Peak Python bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| SYMREG-1 norm projection | 877 / 329 | 4 | 2 | 3 | 1 | 0.000253 s | 22,739 |
| SYMREG-2 sparse composition | 749 / 329 | 3 | 2 | 2 | 1 | 0.000433 s | 20,698 |
| SYMREG-3 semantic join | 1,153 / 529 | 6 | 4 | 2 | 2 | 0.000306 s | 29,282 |

These small Python observations are descriptive, include JSON parsing, hashing
and checking all context premises, and do not establish performance, memory or
energy properties of an eventual hardware or production implementation.

## Reproduction

The preservation commit is `c002164`; SYMREG-4 is a separate uncommitted
experiment. Python 3.10.12 and OSS CAD Suite 20261027 Z3 4.15.5 were used.
No random seed was used. From the repository root, each command has a
30-second external wall limit and 1-GiB per-process virtual-address limit:

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_symreg_4.test_checker -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_symreg_4.examples)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_symreg_4.measure)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/qaf_symreg_4/verification.smt2)
```

Expected solver outcomes: `unsat, sat, unsat, sat, unsat, sat`, with the
negative-control witnesses. The checker also supports standalone invocation as
`python3 -I research/qaf_symreg_4/checker.py CERTIFICATE TRUSTED_CONTEXT`; both
files must contain canonical JSON as defined in the specification.

## Remaining questions

The format supports only `PREMISE`, `COMPOSE`, `NORM` and a final universal
branch conclusion. It does not serialize all predecessor proof forms, prove
external premises or feasibility, authenticate participants, allocate durable
epochs, or handle general rational coefficients. A later independently scoped
study could explore independently provisioned trusted contexts and explicit
epoch lifecycle, including replay and implementation hardening; no such work
is started here.
