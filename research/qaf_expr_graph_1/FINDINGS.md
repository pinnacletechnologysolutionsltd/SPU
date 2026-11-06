# QAF-EXPR-GRAPH-1: graph interpretations and observers

**Result: PASS — bounded observer-model exploration.** The same mathematical
normal form can accompany different finite-width state and event traces under
explicit model assumptions. The three requested fixtures separate mathematical
identity, one final-state observation and a stricter trace observation. This is
software evidence about a toy interpretation, not a qualified SPU compiler,
instruction rewrite, ISA semantics or new hardware observation.

## Model and observers

The original GRAPH-0 expression nodes and normalizer are imported unchanged.
Each fixture pairs a root graph with a **hand-written**, ordered toy instruction
sequence; it is not an automatic lowerer and does not check that arbitrary user-
supplied instructions implement their associated graph. The interpreter models
initialized signed-64-bit coefficient pairs with implicit denominator 1;
constants U=(2,1), V=(2,-1), preloaded registers and a status. Scratch integer
arithmetic is unbounded. Each issued toy operation calculates exact output,
commits a representable pair with status 0 or refuses with status 2 and no write,
then emits one retirement. The experiment's toy controller stops at first
refusal. Invalid input raises a Python exception; other exception classes,
normalization, source-language rules, arithmetic scratch limits, cycles,
concurrency and Gen-1 frontend rules are not modeled.

`MUL` fixtures are compared with the repository's exact tuple reference on the
same denominator-one cases. The separately coded reference supports raw-fit and
normalization but is not an independently verified hardware oracle; no new RTL
is run here. The assumed one retirement per issued operation and the stop-on-
refusal controller are model choices; the prior MATHSTATE-0 trace provides
limited related dispatch evidence, not proof of this toy model. **CONJ and NORM
are hypothetical operations in this experiment:** `NORM` is algebraic field
norm, not Gen-1 `SNORM`, and neither is claimed as an implemented Gen-1
instruction. No SPU instruction encoding is assigned to them.

Three observer decisions are made **for each concrete fixture**, not across an
entire input domain:

1. **Mathematical:** whether GRAPH-0's exact symbolic normal forms match. This
   ignores all execution effects and inherits that normalizer's limits.
2. **Final value/status:** mathematical match plus equal final result register
   and status. Other registers, intermediate reads, writes and retirements are
   deliberately ignored. The decision also depends on the stated initial state.
3. **Strict toy trace:** mathematical match plus equal final register bank and
   status and an equal ordered sequence of status, writes, retirements and
   register snapshots. It is an explicit strong observer, not a claim about the
   full Gen-1 architectural boundary. Exact scratch values and operation names
   are printed for diagnosis but are not themselves part of strict comparison.

A `True` decision means only that the **chosen observer** cannot distinguish
these specific model traces and mathematical forms. It is not permission to
substitute real instructions or a domain-wide proof. A mathematical language may
choose a mathematical observer before lowering; whether a real language permits
that is a separate specification decision.

## Fixtures and observations

| Fixture and compared expressions | Normal form | Original exact intermediate and ordered effects | Alternative | Math / final / strict |
|---|---|---|---|---|
| Small `(3,-2)`, `x U V` vs `x`, initial status 0 | `(xa,xb)` on both | `(0,-1)`, widths (1,1): write r0, retire, status 0; then `(3,-2)`, widths (3,2): write r0, retire, status 0 | No operation; final `(3,-2)`, status 0 | yes / yes / **no** |
| `(2⁶³−1,0)`, `x U V` vs `x`, initial status 0 | `(xa,xb)` on both | First exact `(2(2⁶³−1),2⁶³−1)`, widths (65,64); status 2, no write, retire; stop | No operation; original tuple, status 0 | yes / **no** / **no** |
| `(1,2)`, `x conj(x)` vs `N(x)`, initial status 0 | `(xa²−3xb²,0)` on both | Toy CONJ `(1,-2)`, write r1, retire; toy MUL `(-11,0)`, write r0, retire | Toy NORM `(-11,0)`, write r0, retire; r1 remains uninitialized | yes / yes / **no** |

The first and third fixtures differ in observable toy writes and retirements,
not because either mathematical computation is incorrect. In the overflow
fixture the left preserves the initial destination and reports refusal; the
identity has no refusal. A further negative control starts with status 2:
successful MULs clear it to 0 in this model while an empty identity keeps 2,
so even the final observer rejects the substitution. A same-program control
passes strict comparison, and two different polynomials which happen to return
the same result at one point do not pass the mathematical observer.

Five focused tests passed. Small cancellation and norm fixtures each cover all
25 points in `[-2,2]²`; cancellation final values also agree with the existing
GRAPH-0 direct evaluator. The 25 cancellation inputs and the overflow witness
were compared operation-by-operation against `software/experiments/
surd_cpu_stream.py` for modeled status, write occurrence and destination value.
No independent external implementation, new RTL trace, mathematical proof of
the Python implementation or claim about arbitrary inputs follows. Exactly
which real system observers can see the relevant dispatch signals remains an
architectural integration question.

## Reproduce

Observed HEAD `1934197` with unrelated pre-existing dirty/untracked changes.
Python 3.10.12; each invocation uses a 30-second external timeout and a 1 GiB
virtual-address limit. Software only; no performance benchmark, network,
production code edits, FPGA tools or devices.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_expr_graph_1.test_model -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_expr_graph_1.experiment)
```

Both commands exited 0. All five tests passed; the experiment prints the exact
normal forms, widths, statuses, writes and retirement accounting summarized
above. No independent review or architectural qualification is implied.
