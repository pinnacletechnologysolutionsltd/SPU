# QAF-IR-1: evidence checks for selected IR properties

**Result: bounded software PASS for the requested controls; execution
assumptions UNVERIFIED and machine rewrite UNKNOWN.** An independently coded
checker recalculates selected mathematical claims from an expected expression
and finite input domain, detects the requested altered claims, and makes no
architectural optimization decision. This is an experimental representation
and checker, not a verified compiler, authenticated proof system or ISA rule.

## Scope, authority and implementation

The producer is the existing `research/qaf_ir_0/model.py`; its input nodes come
from GRAPH-0. The separate `checker.py` imports neither the producer nor its
normalizer/evaluator. It traverses the supplied node structure independently,
constructs sparse rational polynomials, checks syntactic and mathematical
variable dependencies, and separately evaluates each integer point in a finite
box to check exact extrema and minimum signed output widths. The same quadratic
multiplication identities are implemented in both, so common conceptual
errors remain possible. The checker's code is not formally verified or
independently audited; no external mathematical proof assistant was run here.

The checker requires an **expected origin** supplied independently of the
record, and requires an **expected domain** before accepting a bound. Those are
trusted inputs for this experiment: they are structurally compared, not
cryptographically authenticated, identity-bound to an external authority, or
proved to be the program the caller intended. Missing origin yields
`UNKNOWN_ORIGIN_SCOPE`; missing domain yields `UNKNOWN_DOMAIN_SCOPE`; mismatch
is reported separately. Changing both a record and the caller's trusted expected
inputs can change the conclusion. Python object reflection, hostile objects,
denial of service, trusted-input substitution, source identities, dynamic
state, authorization and replay are outside scope. A depth cap of 32 and
finite-box cap of 625 are small experiment limits, not a security sandbox.

The supported mathematical expressions are GRAPH-0's x/y variables, rational
constants, addition, multiplication, conjugation and algebraic norm. Polynomial
form equality is checked over formal independent coefficient variables.
`check_equal` recalculates both expressions from the trusted origins; it does
not rely on the stored canonical claims. `check` separately verifies a stored
normal form, structural dependencies, mathematical dependencies, and, when
present, exact extrema and minimum signed output-coefficient widths over the
specified integer box. Bounds require integer outputs; unsupported expression,
domain, or output raises the report `UNKNOWN_UNSUPPORTED`, not a proof of
falsehood. No bound is extrapolated beyond its domain. Scratch products,
denominators, timing and a full finite-width execution path are not certified.

Execution annotations such as `observer=strict`, `arithmetic=toy-signed64`,
`status=observable` and `events=observable` remain **UNVERIFIED**: there is no
matching independently established execution contract or effect proof here.
`rewrite_eligibility` always remains **UNKNOWN**, even when all mathematical
checks pass. This is a deliberate boundary, not evidence that every rewrite
is illegal.

## Results and negative controls

For `x U U⁻¹` over `x∈[-2,2]²`, `y=(0,0)`, the checker independently
recomputed the producer's polynomial and found the stated structural and
mathematical dependencies, 25-point extrema `[-2,2]²`, and signed widths
`(3,3)`. It reports `PASS` for these **scoped checker tests**, and matches the
recomputed form to `x`; it also matches `x conj(x)` with `norm(x)` as formal
polynomials. These findings do not certify an executable instruction sequence.

Five test groups passed. The requested falsification controls gave:

| Mutation | Checker result |
|---|---|
| Change a bound to `[-1,1]` while keeping the trusted `[-2,2]` box | bounds `FAIL` |
| Remove structural dependency `x` | structural dependencies `FAIL` |
| Substitute x's stored normal form for `conj(x)` and claim equality | stored form `FAIL`; independently recomputed equality `FAIL_NOT_EQUAL_FORM` |
| Change reported sample count or signed width | bounds `FAIL` |
| Change a record's domain while trusted domain stays fixed | `FAIL_DOMAIN_MISMATCH` |
| Change expression origin while trusted origin stays fixed | `FAIL_ORIGIN_MISMATCH` |
| Omit trusted origin/domain, exceed finite domain cap, or use symbolic division | `UNKNOWN` in the respective category |
| Supply an apparently permissive execution annotation | execution assumptions `UNVERIFIED`; rewrite eligibility `UNKNOWN` |

A distinct control checks `x*0`: x is structurally present but absent from its
mathematical value dependencies. No general proof of the checker or of all
possible malformed records follows from these tests. The concrete negative
controls and exact commands are in the accompanying code.

## Preservation and reproducibility

Before IR-1, QAF-EXPR-GRAPH-0, GRAPH-1, QAF-OBS-0 and QAF-IR-0 plus their
focused-test Python dependencies were archived and checked as 19 files. An
extracted copy passed 21 tests, and the QAF-OBS-0 solver returned `unsat` and
`sat`. Two separately stored copies were hash-verified:

- `build/qaf-preservation/ir0-foundation-20261106-01/`
- `/home/john/spu-archive/qaf-ir0-foundation-20261106-01/`

Both directories are on the same filesystem and machine; they are **not an
independent failure-domain or off-machine backup**. Each manifest explicitly
excludes linked historical evidence (including SPU-BOUND-2/SPU-OBS-0), the
solver binary and the full runtime environment. The archive predates IR-1 and
does not contain this experiment. No staging, commit or push was performed.

Observed HEAD `f35d03c`, with unrelated dirty and untracked work. Python
3.10.12. The untracked producer dependencies used here have SHA-256:

```text
a1fc12ed9e4a7e84b7157fa8e94c69f582a6684f790d94b5e898d2fa25927f2c  research/qaf_expr_graph_0/model.py
b12ca89bb5131c818d10592a68edc4063e6dcaa6b32c35e3555b551da58abfc7  research/qaf_ir_0/model.py
```

Each command has a 30-second external timeout and 1 GiB virtual-memory limit;
no network, devices, hardware tools, RTL, ISA or production source changes.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_ir_1.test_checker -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_ir_1.experiment)
```

Both exited 0; all five tests passed. No runtime benchmark, independent
qualification, or performance claim was made. Pause before considering a
practical compiler prototype: its source-language contract, trusted evidence
boundary and target-effect semantics remain open.
