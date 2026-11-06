# QAF-IR-0: mathematical and observational representation

**Result: bounded expressiveness PASS; no optimizer or machine rewrite.** A small
immutable record can hold an original expression graph, exact mathematical
normal form, two dependency views, optional finite-box coefficient bounds and
explicit observer/effect assumptions at the same time. The tests establish this
for selected software fixtures; they do not establish that the record correctly
models any real ISA, language, or execution history.

The question is whether these meanings can coexist without choosing an execution
strategy. `Record` retains the original GRAPH-0 immutable node, a pair of sorted
polynomial forms, syntactic and mathematical variable dependencies, an explicit
constraint object and optional bound evidence. A constraint is a **caller-supplied
annotation**, not a verified claim about the target or proof that effects are
unobservable. `unknown` is supported. The enum fields constrain spelling only;
not every combination is semantically consistent. Comparison reports mathematical
form equality and provenance identity, but returns `NOT_DECIDED` rather than
permitting a rewrite. Different annotations return `UNKNOWN_CONSTRAINT_MISMATCH`.
Neither result is a machine optimization or a proof of semantic equivalence.

## Fixtures

- For `x U U⁻¹` and `x`, the canonical pairs are equal while the original
  expression nodes differ. The record can describe either an unknown observer or
  an assumed strict, toy-signed64 observer without deleting the original nodes.
  Both comparisons leave rewrite legality undecided.
- `x conj(x)` and `norm(x)` retain distinct origins and equal polynomial forms;
  the radical polynomial is empty. `(xy)conj(y)` and `x norm(y)` also have the
  same form. These are mathematical relationships, not assertions that CONJ or
  NORM are Gen-1 instructions.
- `x * 0` retains a syntactic dependency on x while its canonical zero value has
  no mathematical dependency. Dependencies refer only to the four supported
  polynomial coefficient variables; they are not a complete dataflow, control,
  effect or information-flow analysis.
- For an independent integer box `x∈[-2,2]²`, `y=(0,0)`, an attached bound
  record contains domain, 25 enumerated inputs, exact extrema `[-2,2]²`, and
  minimum signed widths `(3,3)`. Those extrema are exact for the finite
  enumerated box, not a general symbolic certificate. Widths describe output
  coefficients only; products, scratch arithmetic and storage costs are not
  covered. Unsupported rational outputs and boxes exceeding 625 combinations
  raise `ValueError`; they are not silently labeled safe.
- At `x=(2⁶³−1,0)`, separate records for the first multiplication and final
  expression yield sampled coefficient widths `(65,64)` and `(64,1)`
  respectively. The original graph provides access to the intermediate, but
  intermediates are **not automatically annotated**: the caller selects the
  node and domain. The earlier [QAF-OBS-0](../qaf_obs_0/FINDINGS.md) documents
  why mathematical cancellation alone cannot preserve modeled refusal/events.

Five focused test groups passed, including a false inference control (do not
remove original x dependency just because `x*0` is mathematically zero),
constraint mismatch, immutable record mutation, unsupported operation, and
oversized-domain refusal. These are bounded software tests, not independent
formal verification. GRAPH-0's direct evaluator and normalizer are reused;
errors in those dependencies could affect the result. General symbolic division,
arbitrary denominators, undefined input behavior, verifier for supplied effects,
instruction lowering, liveness, control flow, status transitions, safe
finite-width substitution, a real architectural observer and performance are
outside scope. No reduction in execution cost or hardware follows.

## Preservation and reproduction

Before this exploration, the three earlier GRAPH-0, GRAPH-1 and QAF-OBS-0
experiments and their Python runtime dependencies were archived under
`build/qaf-preservation/graph-obs-20261106-01/`. All 15 archived file hashes
were checked against the embedded manifest; the archive and manifest hashes
passed `sha256sum -c`. An extracted copy passed 16 focused tests; the archived
SMT formula returned `unsat`, then `sat`. See the archive's `README.txt` and
`manifest.json` for exclusions. This is **one local copy**, not a verified
independent or off-machine backup; linked historical SPU-BOUND-2/SPU-OBS-0
reports and the Z3 executable are not included. No files were committed or pushed.

Observed HEAD `f35d03c`; checkout contained unrelated pre-existing changes.
Python 3.10.12. The untracked GRAPH-0 `model.py` used for this experiment had
SHA-256 `a1fc12ed9e4a7e84b7157fa8e94c69f582a6684f790d94b5e898d2fa25927f2c`;
Git HEAD alone does not bind it. Each invocation uses a 30-second wall timeout
and 1 GiB virtual-address limit; no network, hardware, RTL, ISA or production
software changes.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_ir_0.test_model -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_ir_0.experiment)
```

Both exited 0; all five test groups passed. An initial archive checksum command
was accidentally run outside the checksum file's directory and failed to find
relative filenames; rerunning inside the archive directory passed both checks.
No independent acceptance or architectural qualification is implied.
