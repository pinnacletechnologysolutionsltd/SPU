# SPU-SYMREG-1 — relational composition findings

**PASS — BOUNDED DISCOVERY.** The specified relationships, versioned identities,
branch joins and tested refusal behavior work in the defined experimental
domain. This is evidence for a small software research model, not a proof of
general relational soundness, an ISA implementation or a hardware proposal.
The [mathematical specification](SPECIFICATION.md) defines the exact domain,
rules, capacities and assumptions. The predecessor's
[REVISE finding](../qaf_symreg_0/FINDINGS.md) and negative timing result remain
unchanged.

## Discovery and correctness

The model admits concrete-checked value and norm facts and records immutable
derivation provenance. In E1, `y=conj(x)` and `z=2y` compose to
`z=2conj(x)`; projection yields `N(z)=4N(x)`. Neither composition, projection
nor the corresponding symbolic queries rereads numerical values. The evidence
uses `(1,2)`, `(1,-2)`, `(2,-4)` and an independent `Fraction` calculation.
The query returns a proof path; fact validity is explicit. Trusted store
admission is an API property, not a defense against hostile Python reflection.

Eleven test groups passed. They include 900 systematic small-domain
compositions, repeated conjugation, positive/negative/zero scaling, 1,530
three-valued query checks against independent exact values, invalid claims and
fabricated provenance. No false `PROVEN` or `DISPROVEN` was observed in those
checks. A deliberately defective register-number map continued to claim an old
conjugation after overwrite; the versioned model returned `UNKNOWN` and a
concrete counterexample returned `DISPROVEN`. Equal norms did not imply equal
values. These tests do not establish correctness outside their finite cases.

The branch experiment creates both paths for an unknown condition and joins
their common facts; facts present on only one path are unavailable after join.
Different current bindings become unknown, while old immutable identities and
facts remain historical. A caller-supplied definite condition chooses one path;
conditions are trusted inputs, not solver-proven feasible paths. The tested
W=8 integer-denominator subset of SMUL preserves destination and existing facts
on overflow while setting status to `OVERFLOW`; success sets `OK`. Invalid
input is also tested. This is not general SPU instruction refusal behavior or
64-bit architectural conformance.

## Verification record

Z3 4.15.5, QF_BV, was invoked with `-T:25` under the 30-second/1-GiB invocation
limits below. `UNSAT` means no counterexample in the encoded model and
assumptions; `SAT` means the shown formula has a witness; timeout or `UNKNOWN`
would be inconclusive. Neither solver file encodes the Python implementation.

| Property and domain | Assumptions and outcome | Negative control and scope |
|---|---|---|
| `N(k·conj(x))=k²N(x)` for 4-bit signed coefficients and `k∈{-2,-1,0,1,2}`, widened to 32 bits. | `UNSAT` for a counterexample; intermediate integer products fit the widened representation for this domain. | Replacing `k²` with `k` is `SAT`: `a=1,b=0,k=2`. A separate `SAT` check shows equal norms do not imply value equality. This checks a mathematical rule, not cache behavior or the ISA. |
| After one overwrite, a relation keyed by the old version cannot match the new version; 2-bit version counter, 4-bit signed coefficients. | Feasibility `SAT`, then stale identity match `UNSAT`, assuming one increment and a changed value. | A deliberately register-number-only lookup is `SAT`: old version 0, new 1, old `(-2,-1)`, new `(1,0)`. This checks an abstract binding model, not Python code, multiple wraps or machine reset. |

The implementation's separate exact tests exercise provenance, overwrite,
branch and refusal behavior. Formal proof of their full implementation, arbitrary
widths, branch feasibility and finite-width RTL is not claimed. A failed solver
query, timeout or different solver result must not be reclassified as a pass.

## Representation complexity and descriptive cost

The store permits at most 64 identities and 256 distinct facts per path; it
refuses additions at capacity instead of silently evicting facts. Paths retain
all historical values, so this is a bounded exploratory policy, not a practical
garbage collector. Combinations outside the allowed scales, reverse edges and
many true facts return `UNKNOWN`. Merge can discard path-specific facts
explicitly. Provenance is a DAG of parent fact references; a merge references
each incoming proof. Composition depth grows with chain length.

One deterministic Python 3.10.12 run, concurrent with tests and solver checks:

| Input | Observed facts | Derivation depth | Peak Python allocation |
|---|---:|---:|---:|
| 4/8/12/16 equal identities, all ordered pairs asserted | 16/64/144/256 | 1 each | 12,732 / 24,404 / 51,744 / 90,632 bytes |
| 1/4/8/16 composed chain edges | 1/7/15/31 | 1/4/8/16 | not measured separately |

The all-pairs workload is deliberately constructed to show quadratic growth;
it does not establish an asymptotic bound for every workload. `tracemalloc`
includes model and Python object allocations, not just provenance. All chain
composition steps made zero numerical reads after their respective base facts
were checked. Fact admission itself reads and validates numerical values.

For 10,000 identical norm-equality queries after setup, symbolic search took
0.099496 s, inspected 20,000 facts and made zero numerical reads; direct
numerical comparison took 0.009806 s and performed 20,000 norm evaluations;
manual precomputed truth took 0.000603 s. The direct formula uses three
multiplications and one subtraction per norm, so those queries avoided 60,000
counted integer multiplications and 20,000 subtractions after fact admission.
These are one-sample Python observations with allocation and scheduling noise,
not a speed, energy or architecture comparison. The symbolic query's setup,
proof bookkeeping and memory are real costs. Performance is separate from the
bounded discovery result.

## Architectural questions

1. Equality, conjugation and norm projection were useful for deriving the E1
   chain; zero and negative scaling were representable without numerical rereads.
2. Rational coefficients, general arithmetic, arbitrary scales, reversed or
   conditional relations and full ISA state are not represented.
3. Supported directed chains compose cleanly; out-of-set intermediate scales
   and unsupported inference return `UNKNOWN`, even for some true facts.
4. Facts about immutable old identities survive register overwrite, but do not
   automatically describe the new register contents.
5. Provenance makes each derivation inspectable, but parent graphs and duplicated
   merge evidence consume space; explicit all-pairs facts grow quadratically in
   the measured construction. A bounded store needs a future retention design.
6. A compiler or research VM is the appropriate first setting; these results do
   not justify architectural register metadata.
7. The smallest follow-up would compare a small real instruction/branch trace
   against a compiler's ordinary dataflow analysis, including provenance and
   retention costs. It is a proposal only and is not started here.

## Reproduction

Repository baseline `87833c7`, with unrelated untracked work preserved. Python
3.10.12 and OSS CAD Suite 20261027 Z3 4.15.5 were used; no random seed. Each
command has a 30-second wall limit and a 1-GiB virtual-address-space limit.
Outputs are terminal-only. The solver path is local to this workstation.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_symreg_1.test_model -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_symreg_1.measure)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/qaf_symreg_1/relations.smt2)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/qaf_symreg_1/overwrite.smt2)
```

Expected solver outcomes are `unsat, sat, sat` and `sat, unsat, sat`,
respectively, plus the counterexample values. No solver timeout occurred.
