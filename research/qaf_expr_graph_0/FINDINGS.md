# QAF-EXPR-GRAPH-0: symbolic mathematical representation

**Result: PASS — bounded mathematical representation experiment.** For the
specified expressions, an immutable expression graph retains the original
operations while an expanded exact polynomial form identifies several algebraic
relationships. The model is not an SPU instruction stream, compiler or finite-
width machine, and does not authorize instruction elimination. This study uses
a distinct name because `research/qaf_symreg_1/` already records SPU-SYMREG-1;
it does not replace that work or change SPU-BOUND-2's PARTIAL disposition.

## Question and representations

Hypothesis: retaining an expression DAG and separately deriving exact symbolic
coefficients can expose cancellation, conjugation and norm relationships while
preserving the original expression for later interpretation. This is a
mathematical experiment, not a claim of architectural equivalence or speed.

- **Eager:** `eval_graph` recursively evaluates every occurrence with exact
  `Fraction` coefficient pairs. It is the concrete software baseline, not a
  model of the Gen-1 bank, status, normalization or refusal.
- **Expression graph:** immutable nodes record `x`, `y`, rational constants,
  addition, multiplication, conjugation and field norm. The untouched original
  graph remains available after normalization. Node identity is structural;
  identical subexpressions share identity, so unique-node counts are not counts
  of operations executed or events. There are no source locations, mutable
  state, evaluation order guarantees, event IDs or instruction history.
- **Canonical mathematical form:** separate sparse multivariate rational
  polynomials for the two coefficients, expanded and combined by exact integer
  exponents. For the supported ring expressions and these variable meanings,
  identical forms establish the same formal polynomial; this implementation is
  not an independently proved complete equivalence procedure for arbitrary
  mathematics. It preserves no original instruction-event semantics by itself.

Constants and concrete inputs can use rational coefficients; general symbolic
division, symbolic denominators, invalid/zero-denominator inputs and arbitrary
quadratic-field inverse expressions are unsupported. There is no defined resource
cap, parser, security boundary, optimizer, overflow model or lowerer. Polynomial
and DAG sizes can grow; no scalability or runtime advantage is claimed.

## Bounded results

| Relationship | Original graph / comparison | Observed result |
|---|---|---|
| `x U U⁻¹`, U = `2+√3` | 5 structurally unique graph nodes; `x` has 1 | Both canonicalize to `(xa, xb)`; original multiplication nodes remain in the graph. |
| `x conj(x)` vs `norm(x)` | 3 vs 2 nodes | Both yield `(xa²−3xb², 0)`; the radical coefficient is exactly zero. |
| `(x y) conj(y)` vs `x norm(y)` | 5 vs 4 nodes | Exact polynomial pairs agree, with two terms in each coefficient. |
| Finite coefficient boxes | Four independent integer inputs in `[-2,2]` | Exhaustive graph evaluation gives `[-2,2]²` for cancellation and `[-24,24]²` for the norm-factor fixture; these are enumerated bounds, not a scalable bounds certificate. |
| Pell growth | `U³⁴` applied to `(1,0)` | Exact rational coefficient `13,969,685,227,624,439,047` exceeds signed 64-bit maximum, despite norm one. |

Five test groups pass. Seven supported expression forms were checked at all
625 input points against separately implemented direct concrete arithmetic and
one additional rational-coefficient input. The concrete and polynomial paths
are separate functions in the same file, not an independent external audit.
The tests retain negative controls: `x` differs from `conj(x)` although their
norms agree; replacing arbitrary `y` with `conj(y)` is not generally valid;
unsupported division is refused rather than silently interpreted.

For `x=(2⁶³−1,0)`, the graph preserves an intermediate coefficient requiring
65 signed bits, even though its final mathematical canonical form is `x`.
Prior [SPU-BOUND-2](../spu_bound_2/FINDINGS.md) and
[MATHSTATE-0](../mathstate_0/FINDINGS.md) document the separately modeled
finite-width refusal and observable-event boundary. This experiment performs no
new RTL trace or refusal-equivalence proof. Keeping the DAG makes a later
architectural interpretation possible in principle; it does **not** provide
one or establish which transformations a future source language permits.

The conceptual analogy to relational memory is limited to retention of
relationships and provenance. These are different domains, and no Soul memory
semantics or performance result follows from this experiment.

## Reproduction

Observed Git HEAD `9fe2cee`; the shared checkout had unrelated pre-existing
changes. Python 3.10.12. Each invocation has a 30-second wall limit and a
1 GiB virtual-memory limit; no network, devices, hardware tools, RTL or
production software are used. Exact arithmetic uses `Fraction`; no randomness.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_expr_graph_0.test_model -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_expr_graph_0.experiment)
```

Recorded output: all five tests passed; the experiment prints the node counts,
canonical coefficients, enumerated bounds and overflow witness above. These
are preliminary software findings, not independent acceptance or qualification.
