# AOR programme: compact symbolic processor roadmap

**Date:** 2026-10-13  
**Status:** OPEN RESEARCH PROGRAMME; future tranches PROPOSED  
**Owner direction:** Continue AOR toward a compact symbolic processor. Preserve
completed AOR-1 evidence; do not interpret its baseline comparison as programme closure.

## Review commands and authority

```bash
sed -n '1,200p' build/aor1/phase_a_closeout_20261012_01/REPORT.md
sed -n '1,200p' spu_strategy/AOR_SYMBOLIC_PROCESSOR_ROADMAP_2026-10-13.md
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/README.md spu_strategy/AOR_SYMBOLIC_PROCESSOR_ROADMAP_2026-10-13.md
```

These commands inspect evidence and documentation. The audit count follows the
root engineering contract; it is not a new regression result. This roadmap
authorizes documentation only. Implementation, experiments, budgets, ISA changes
and hardware promotion need their own contracts and owner authorization.

Roles follow the [engineering contract template](contract_template.md): draft
the bounded contract; halt and flag contradictions before implementation; audit
independent evidence against the frozen contract before promotion.

## Preserved starting point

The [AOR-1 architectural proposal](contract_spu13_algebraic_octave_aor1_2026-10-11.md)
represents an integer residual as `(a + b sqrt(3)) U^k`, with `U = 2 + sqrt(3)`.
Its [Phase A contract](contract_spu13_aor1_phase_a_2026-10-11.md) and subsequent
amendments define the qualified bounded software profile.

The retained [Phase A closeout report](../build/aor1/phase_a_closeout_20261012_01/REPORT.md)
and [machine-readable closeout](../build/aor1/phase_a_closeout_20261012_01/closeout.json)
record CLOSED PASS for that software tranche. The report records exact compact
composition, checked expansion and negative controls. Its paired comparison
establishes matching behavior and accounting with the conventional checked
mantissa-plus-exponent baseline; it establishes no architectural storage or
performance advantage. Single host samples do not support a statistical speedup claim.

Keep these contracts, snapshots, hashes, results and limitations unchanged.
**The Phase A evidence is closed; the AOR research programme remains open.**
No AOR RTL, instruction allocation or hardware benefit follows from that PASS.

## Destination and measurable meaning of compactness

Develop a small processor model that retains exact algebraic expressions and
composable transformations as machine state, materializing coefficients only
when an operation requires it. General Surd mantissas remain part of the domain;
this is broader than an exponent counter for the pure Pell subgroup.

Define compactness per workload and finite profile: live expression nodes,
stored bits/bytes, peak temporary storage, normalization work, materialization
work and executed operations. Record growth with sequence length, including
adversarial inputs. Do not require every algebraic expression to stay compact.
Unavoidable growth must produce a specified resource refusal, preserving state.

Arithmetic accuracy, symbolic compactness, useful capability and measured cost
are separate claims. Immediate speedup is not a prerequisite for research;
hardware promotion still needs a measured reason to prefer hardware support.

## Proposed successive tranches

| Tranche | Deliverable | Promotion evidence |
|---|---|---|
| AOR-S1: bounded symbolic state | Software contract, expression grammar and independent semantic oracle | Defined domains, equality outcomes, resource accounting and falsifiable fixtures reviewed before coding |
| AOR-S2: symbolic computation | Isolated software state machine with registers and finite instruction sequences | Exact composition, mixed-exponent expressions, aliasing and atomic failure agree with independent expectations |
| AOR-S3: useful workloads | Workload catalogue and scaling comparison | Useful sequences retain bounded structure; costs and growth compared with strong conventional baselines |
| AOR-S4: processor interface | Proposed architectural state, operations and microarchitecture | State lifecycle, completion, reset/cancellation and materialization boundaries explicitly reviewed |
| AOR-S5: hardware candidate | Separately authorized isolated RTL and physical evaluation | Independent functional checks, measured resources, legal routing and timing; board evidence reported separately |

These names describe future work, not ratified AOR-2/AOR-3 specifications.
Each tranche freezes its own scope, sources, fixtures, commands, attempt count,
wall-clock and cumulative budget. Passing one does not authorize the next.

## Next deliverable: AOR-S1 contract draft

The [canonical integer product-fragment draft](contract_aor_s1_product_fragment_2026-10-13.md)
now separates exact canonical equality and one-adjustment local rebalancing from
budgeted general canonicalization. The [S3 workload preparation draft](contract_aor_s3_workload_preparation_2026-10-13.md)
records rational-matrix, axis/exponent, run-length-word and hybrid comparisons.
Both remain review drafts with implementation and execution gated.

Draft a software-only contract resolving the following before implementation:

1. Freeze a minimal grammar for integer Surd literals, unit powers, product and
   sum expressions, conjugation and explicit materialization. Select the first
   supported subset; classify other operations as unsupported.
2. Define immutable expression ownership, sharing, register updates and alias
   behavior. Separate representation identity from mathematical value equality.
3. Specify terminating rewrite rules and their ordering. Charge normalization,
   allocation, equality proofs and materialization; set explicit node, bit and
   work limits. A resource refusal is not mathematical inequality or overflow.
4. For validated canonical integer product-fragment descriptors, define decisive
   tuple equality. For general expression DAGs, distinguish proved equal, proved
   unequal and undecided within budget. Freeze comparison/control behavior before
   dependent programs. Do not extend fragment canonicalization to arbitrary DAGs
   or claim constant bit complexity.
5. Specify atomic writes and deterministic failure precedence. Destination and
   shared expressions survive every failed operation unchanged.
6. Freeze independent labels and oracle algorithms. Do not derive expected
   answers solely from the implementation's rewrite engine. Expansion-backed
   oracle checks must declare their own resource bounds.
7. Include negative controls for wrong exponent, coefficient, rewrite, equality
   verdict, budget counter and partial write. Each must trigger a named rejection.

## Initial workload questions

| Workload | Question to establish |
|---|---|
| Long boost/inverse sequences | Can composition and cancellation remain compact without coefficient expansion? |
| Mixed residuals | Does `(5,2,1000)` times its conjugate produce `(13,0,0)` without expansion? |
| Unequal-exponent sums | Which exact expressions can be retained, simplified or materialized within bounds? |
| Repeated composition with shared subexpressions | Is sharing safe and useful after its management costs are included? |
| Equality and dependent control | Can the machine make required decisions with explicit proof/resource outcomes? |
| Adversarial addition and cancellation | Where does structure grow, and does refusal preserve complete machine state? |

Compare with the qualified checked tuple baseline where its operation domain
matches, arbitrary-precision expanded Surds, and conventional symbolic DAG
bookkeeping with equivalent semantics and limits. Include validation, sharing,
normalization, equality and output conversion costs. Separate symbolic results
from fully materialized outputs; a transformation descriptor is not an expanded
coordinate result. No Lorentz-specific instruction is required by this roadmap.

## Engineering priority and stop conditions

Existing Surd CPU physical implementation remains the immediate hardware priority.
This programme does not change the active Artix-7 inputs, placement attempt,
aligned-decode gate or timing acceptance. Future AOR hardware stays isolated until
separately authorized; existing ISA, Surd, REGEN and GPU semantics remain intact.

Halt and flag unsound rewrites, ambiguous failure/equality semantics or a checker
that accepts its injected fault. Treat learner/workload limitations and rejected
optimization candidates as research results when their classifications are correct.
Revise the proposed approach when evidence requires it; retain the goal of a
compact symbolic processor without promising compactness for arbitrary computation.
