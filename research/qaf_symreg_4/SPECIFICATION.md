# SYMREG-4 — portable mathematical proof certificates

**PROPOSED bounded software experiment.** No ISA, RTL, production VM or
v0.2 qualification change. The preserved [research summary](../SYMREG_RESEARCH_SUMMARY.md)
and predecessor findings describe earlier bounded evidence.

The question is whether a small independent verifier can check a deterministic
certificate without importing the SYMREG inference engine. The domain is
integer coefficients in Q(√3). Value facts mean `target=k·conj^f(source)`,
`k∈{-2,-1,0,1,2}`; norm facts mean `N(target)=k·N(source)`,
`k∈{-4,-2,-1,0,1,2,4}`. Algebraic norm is distinct from ISA `SNORM`.
The checker uses exact Python integers, not finite-width machine arithmetic.

## Trust boundary

A separately supplied trusted context fixes format/domain, immutable IDs and
their concrete coefficient pairs, the declared-feasible branch IDs, each
branch's trusted premise IDs and current register bindings, plus a scope ID
that the context owner must not reuse across identity epochs. The verifier
independently checks every context premise against its concrete values. The
context's declared feasibility is an assumption, not a proven property; its
provenance/authentication belongs to the caller. A certificate embeds a SHA-256
digest of the deterministic canonical context encoding and the scope ID. A changed context,
including changed bindings or branch set, invalidates the certificate. A hash
is an integrity binding, not authentication or a defense against a malicious
party controlling or rewriting the trusted context or certificate. An
identical replay with a reused scope is indistinguishable and must be prevented
by an external scope-allocation/authorization policy; this experiment does not
implement one.

## Format and rules

Use canonical UTF-8 JSON with sorted keys, compact separators and no duplicate
keys. All objects have exact schemas; unsupported fields, versions, descriptors
or non-integer/Boolean aliases fail closed. A certificate names the context
digest and declared branch set, has ordered proof steps and names a final
conclusion. `PREMISE` references one authorized premise in the step's branch;
`COMPOSE` references two earlier steps in that same branch with matching
intermediate identity and supported product scale; `NORM` projects one earlier
value step to a norm step. Each step explicitly states its derived descriptor,
which must match the independently recomputed rule result. A final
`ALL_FEASIBLE_PATHS` conclusion binds the exact descriptor and exactly one
earlier witness for every context branch. A witness must be from its named
branch and establish the same conclusion. An optional current-register binding
is valid only if both endpoints match in every declared branch.

Value IDs are local to a trusted context; reuse across contexts is not assumed.
The checker rejects unknown premise IDs, false premises, forward or malformed
references, wrong branch, stale context or binding, missing/extra witnesses,
unsupported scale/rule and mismatched derived/final propositions. It does not
infer an omitted premise or prove arbitrary mathematical statements. Normalized
zero scaling has `flip=false`; norm descriptors have `flip=false`.

## Bounds and evidence

Use explicit limits: 64 values, three branches, 256 total trusted premises,
128 steps, maximum proof depth 32, and 65,536 bytes per serialized certificate.
Reject resource exhaustion with a distinct refusal; do not silently truncate.
Experiments will include predecessor-style examples, path-coverage controls,
mutations, independent exact arithmetic, bounded Z3 checks and a negative
control for every stated solver property. Report certificate bytes, step and
premise counts, depth, check time and Python memory, with no performance claim.
The checker must not import SYMREG inference or proof-validation code. Proofs
are conditional on the supplied trusted context and its branch assumptions.
