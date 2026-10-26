# SSM and SG-0 continuation

Date: 2026-10-19. Scope: saved-evidence reconciliation and next interface design.
No qualification retry, simulator integration or hardware work launched.

## Current evidence

The research READMEs contain historical preparation states. Use dated evidence
alongside them rather than treating those states as the latest campaign result.

| Component | Saved observation | Limit |
|---|---|---|
| SG-0 | `build/sg0/certified_geometry_20261018_01` has exactly one terminal marker, COMPLETE; result records exit 0 and duration 240 seconds | Focused software campaign, not whole-repository or hardware qualification |
| SG-0 bundles | All 30 manifest-listed payload hashes match; both saved qualification bundles contain 31 files and are byte-identical | Hash and byte checks performed during this reconciliation; semantic reconstruction was not rerun |
| SSM-4 original campaign | `build/ssm4/certified_state_20261018_01` has FAILED and result exit 1 | Preserve the failed attempt |
| SSM-4 recovery campaign | `build/ssm4/certified_state_r1_20261018_01` has no COMPLETE, FAILED or TIMEOUT marker | Result unavailable under AGENTS.md §4.2; do not infer qualification |
| SSM-4 recovery metadata | result.json reports TIMEOUT, exit 124, limit 1800 seconds and duration 32335 seconds | Incomplete terminal protocol and duration discrepancy require diagnosis; no cause established |
| SSM-4 subordinate record | `verification/determinism.json` reports cross-seed PASS over 18 files | Does not replace campaign completion or establish all regression gates |

No marker was synthesized or repaired. Neither recovery metadata nor elapsed
time authorizes another attempt. Preserve the existing source freezes and raw
logs. Diagnose terminal publication separately from mathematical behavior;
inspect runner/service evidence before proposing any correction or new budget.

## Next research interface: selective observations

Build on the existing [SSM-4 design](SSM4_CERTIFIED_GEOMETRIC_STATE_DESIGN_2026-10-18.md)
and [SG-0 bridge](SG0_SYMBOLIC_GPU_INTERFACE_DESIGN_2026-10-18.md). The next
implementation contract should describe a separate research executable, with
these explicit semantics:

1. A request names an immutable SSM state content identity, a frozen geometry
   recipe and an ordered, duplicate-free subset of vertex identifiers. Verify
   ancestry and recipe binding before using derived coordinates.
2. Report resource exhaustion, empty state, unresolved observation or exact
   observation using SSM-4's existing precedence. Invalid requests reject before
   evaluation. Freeze parsing and error order in the execution contract.
3. Preserve the latent parameter family and its correlations. An unresolved
   request produces no arbitrary witness. A later observation is an explicit
   added assumption producing a new state, not a correction of certified truth.
4. An exact subset may be returned with provenance but cannot be passed off as
   a complete renderable mesh. Only the complete frozen recipe may proceed to
   SG-0's existing geometry checks and finite-width conversion.
5. A receipt binds state identity, recipe, request, exact outcome and any
   conversion result. Conversion refusal preserves the exact state and result;
   successful conversion does not transfer exact invariants to rounded output.
6. Start without a persistent cache. If caching is later introduced, key it by
   the full immutable state identity, recipe and request. A request against a
   child state must never reuse an ancestor receipt as its own observation.

This interface is a proposed extension. Existing SG-0 admits pinned unique
SSM-3 inputs; do not broaden that admission silently or claim arbitrary SSM-4
handoff already works. Reuse conversion helpers only where their preconditions
are met, keeping the new admission and provenance checks explicit.

## First implementation contract requirements

Limit the first fixture to the existing Q3 family, four vertices, frozen recipes
and bounded ancestry. Include correlated, resolved, empty and exhausted states;
an exact subset with unresolved remainder; parent/child receipt substitution;
wrong recipe; modified proof; and exact geometry refused by conversion.
Specify independent expected coordinates and family-direction annihilation
checks, not merely producer/replayer agreement. Retain conventional exact affine
evaluation as a baseline with the same family information and deferred queries.

Record object commands and expanded rational work separately. The milestone is
composable state-to-observation semantics with falsifiable provenance checks,
not a Python timing victory. Freeze source identities, commands, finite bounds,
fresh outputs and a small correctness budget before execution. Existing consumed
qualification allocations are not reused.

The [QSG-3 model](QSG3_GEOMETRIC_MACHINE_SPECIFICATION.md) is a parallel semantics
investigation. It need not become a dependency of SSM or SG-0. RP0 execution,
experimental simulator integration, production ISA changes and new RTL remain
separate decisions. RET-4 cleanup is not required to specify this interface and
no cleanup is performed here.
