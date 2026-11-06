# QAF-OBS-0: observer-sensitive rewrite legality

**Result: PASS for one defined pure-expression rule; NO GENERAL MACHINE
REWRITE.** Under the mathematical language below, replacing `(xU)U⁻¹` by `x`
is semantics-preserving for every rational coefficient pair. The same
replacement is distinguishable in the selected finite-width toy fixtures. The
result is not an optimizer, ISA rule, CPU qualification or hardware finding.
The existing separate [SPU-OBS-0](../obs_0/FINDINGS.md) concerns an inspected
Gen-1 dispatch boundary and is not superseded or modified.

## The pure context and its proof

Values are pairs `(a,b)` in Q², representing `a+b√3`. Inputs are any rational
pairs. Evaluation uses unbounded exact rational addition and multiplication;
`U=(2,1)` and `V=(2,-1)` are fixed constants. The expression language consists
of these pure total operations and observes only the final exact pair. There are
no widths, allocation failures, instructions, status, side effects, writes,
retirements, intermediate reads, timing or exceptions within this model. Under
these explicitly chosen semantics, contextual equality for this rule follows
because every surrounding expression uses the same deterministic pure operations.
It does not follow for an unspecified real implementation with memory or time
limits, errors or external observations.

For an arbitrary pair `(a,b)`, multiplication by U gives
`c=2a+3b, d=a+2b`. Multiplication by V gives
`(2c−3d, −c+2d)=(a,b)`. This is an algebraic proof over Q. The independent
SMT formula `proof.smt2` searches for a counterexample over all **real** `a,b`
(QF_LRA, a superset of rational pairs): Z3 returned `unsat`. A deliberately
wrong inverse returned `sat`, with witness `a=0, b=−1/6`. This solver result
checks the encoded formulas, not the Python implementation, memory limits,
normalizer or an implementation's status/events.

`assessment` recognizes only the specifically named original and identity
programs as eligible for this pure-context rule. Other pairs return `UNKNOWN`
even if they happen to agree at one point. This is a demonstration of a named
rule and its assumptions, not an independent proof-checking compiler; it does
not validate arbitrary hand-written mappings from graph roots to instructions.

## Other observers and negative controls

The finite-width comparisons reuse [GRAPH-1](../qaf_expr_graph_1/FINDINGS.md):
initialized signed-64-bit coefficient pairs, denominator one, unbounded scratch,
status 0/2, atomic writes, one assumed retirement per issued operation, and a
toy controller that stops at the first refusal. `CONJ` and `NORM` in that model
are hypothetical; the latter is field norm, not Gen-1 SNORM. The model does not
claim that every dispatch signal is architecturally observable in every SPU
context. This revision names the three policies O1, O2 and O3. O1 compares
mathematical normal forms. O2 compares the final result tuple, final status,
and whether any modeled operation refused; the refusal flag is derived from
issued events, not from the initial status. O3 includes O2 plus the entire
final modeled register bank and each ordered event's PC, operation label,
status, refusal, write, retirement and register snapshot. This is a deliberately
strong toy observer, not a determination of which Gen-1 signals a program can
observe. Results apply to each stated fixture, not all inputs.

| Fixture | O1: mathematical form | O2: final value, status, refusal | O3: ordered toy trace |
|---|---|---|---|
| Small `(3,-2)`, status 0: `x U V` vs `x` | equal `(xa,xb)`; named pure rule proved | equal: `(3,-2)`, status 0, no refusal | **different**: `MUL` writes `(0,-1)` then `(3,-2)`, both retire; identity has no events |
| `(2⁶³−1,0)`, status 0 | equal `(xa,xb)`; named pure rule proved | **different**: original status 2 and refusal; identity status 0 and no refusal, same tuple | **different**: one refusing `MUL`, no write, one retirement; identity has no events |
| `(1,0)`, initial status 2 | equal `(xa,xb)`; named pure rule proved | **different**: successful operations clear status to 0; identity retains 2; neither trace refuses | **different**: two `MUL` writes/retirements vs no events |
| `(1,2)`, `x conj(x)` vs `norm(x)` | equal `(xa²−3xb²,0)`; named cancellation rule returns `UNKNOWN` | equal: `(-11,0)`, status 0, no refusal | **different**: hypothetical `CONJ` writes r1 and `MUL` writes r0, both retire; hypothetical `NORM` writes r0 and retires once |

The first three pure decisions refer to a separate unbounded mathematical
language, not to permitted elimination of modeled instructions. In both the
overflow and initial-status cases the result tuple alone agrees, so a value-only
observer hides a status difference. In the small case, final value plus status
hides the ordered writes and retirements. For the norm case the result is only
an observed normal-form match in this implementation, not a newly proved
universal rewrite in this experiment. Both expressions are mathematically
legitimate under their own semantics; the strict observer distinguishes their
modeled histories.

Six test groups passed: 81 small integer inputs and three rational/large-value
controls for the pure evaluator; all four observer fixtures; same-program
strict equality; and a coincident-output but different-polynomial negative
control. A deliberately changed retirement in an otherwise identical trace
passes O2 but fails O3. Separate mutations of the final status or a refusal event
fail O2, including a refusal-event mutation with final status held unchanged.
These synthetic mutations test observation, not a hardware failure. The O3
strict result does not automatically mean
an ISA forbids a transformation: a real observer contract and a relation between
source and machine operations would need independent definition and evidence.
A sound effect-constrained machine rule remains **unestablished**. This meets
the stopping condition for one pure rule without implementing an optimizer.

## Reproduction and provenance

Observed HEAD `469cb9e`; shared checkout had unrelated pre-existing changes.
Python 3.10.12 and Z3 4.15.5. GRAPH-0 and GRAPH-1 source files were untracked;
Git HEAD alone does not identify them. Their SHA-256 values at this run were:

```text
a1fc12ed9e4a7e84b7157fa8e94c69f582a6684f790d94b5e898d2fa25927f2c  research/qaf_expr_graph_0/model.py
4c5d8273a06f264a7fe443b8b218ba6cd81a2f31835a1538fdb01917e96a655b  research/qaf_expr_graph_1/model.py
```

Each invocation used a 30-second external wall timeout and 1 GiB virtual-memory
limit; Z3 additionally had a 25-second solver limit. Outputs were terminal only.
No RTL, ISA, production software, synthesis, devices or network were used.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_obs_0.test_experiment -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_obs_0.experiment)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/qaf_obs_0/proof.smt2)
```

All six tests passed; all commands exited 0; Z3 produced `unsat` then `sat`.
No independent review, performance assessment or release qualification is
claimed.
