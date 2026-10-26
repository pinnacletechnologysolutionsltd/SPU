# SPU-4 SOM Research Closure

Date: 2026-09-11  
Status: **CLOSED**

## Terminal classification

**SOM research tranche: CLOSED. Application advantage not demonstrated.
Hardware offload comparison incomplete because artifact B has an unresolved
same-input parity divergence. Artifact A retains exact oracle agreement on the
frozen reference case. Further Tang-specific diagnosis is not warranted at
current priority.**

## Durable state

Artifact A (`6b7022f2...f8e8f6`) is the known-good reference. For
`Q1B2500003EB80000520800004BD40000`, it returned node 2 / `03C58E94`, exactly
matching the trusted oracle.

Artifact B (`7a57be49...448b`) is the divergent reference. For the identical
query and verified frozen model, it returned node 0 / `42FF6EEB`. This is a
build-correlated physical observation, not a localized mechanism.

The earlier node 3 / `04433EA4` result used raw features `[109,39,21,11]` and
exactly matches the oracle for those transmitted bytes. The raw/scaled fixture
mismatch is resolved; it neither invalidates nor explains the later same-input
A/B divergence.

Observer validation and the bounded four-run formal campaign did not establish
non-perturbation, equivalence, non-equivalence, or causation. Static L1 selected
raw `som_best_node[1]` as a useful D3/D4 boundary only.

The corrected board mapping is D7 active-high DONE, with diagnostic relation
`D7 = ~som_best_node[1]`. The electrical tranche was partially executed, but
the single query failed to reproduce B and therefore stopped before the
post-query electrical readout. Final J4 readback also differed from its initial
capture. No P1/P2 or D0-D5 localization was obtained.

## Closure gate

`bash tools/verify_repo.sh` ran once through the detached runner and completed
with exit 0: 227 PASS / 0 FAIL. No synthesis, formal, hardware, observer,
repair, or RP benchmark was run during closure.

## Future policy

There is no authorized SOM next action. Reopening requires a new
owner-authorized contract and a new priority decision; the closed campaign does
not imply permission to repair B or resume Tang-specific localization.

Raw index:
`build/spu4_ina226_benchmark/som_research_closure_20260911/evidence_index.md`.
