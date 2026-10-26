# Selective observation software fixture

Date: 2026-10-19. Status: ACTIVE under the owner's instruction to implement
and test the isolated interface. Roles: Codex drafts, implements and checks;
no independent acceptance reviewer is claimed.

## Execute the bounded fixture

```bash
python3 -B -m research.selective_observation --out build/selective_observation/fixture_01
```

Use one fresh output, one correctness invocation capped at 30 seconds. No
automatic retry, timing campaign, qualification campaign or timeout extension.
Before dispatch, preserve source bytes and hashes, command and interpreter;
after dispatch, record source drift, stdout/stderr, result and one terminal
marker. A failed test is a finding; halt and propose a minimal correction.

## Scope and semantics

Create only research/selective_observation/{interface,baseline,test_interface,
__main__}.py plus research documentation. Reuse SSM-4 and SG-0 read-only.
Preserve Q3, four frozen recipe vertices, eight-operation ancestry and existing
4096-bit completed coefficient bounds. Host arithmetic temporaries remain
host-managed. No cache, renderer invocation, publication, simulator or RTL edit.

Validate request schema, indices, recipe/state binding, then materialize. Requests
preserve caller order; inherited receipts use sorted indices and the observation
accessor restores caller order. Replay binds the receipt to the consumer's
expected immutable state and query. Existing SSM-4 outcome precedence is retained.
Only a complete four-vertex request may undergo inherited SG-0 conversion.
Conversion refusal leaves exact state and coordinates valid. No witness sampling.

The conventional Fraction baseline retains the same family, recipes and deferred
queries. It computes affine origins and direction annihilation directly without
calling materialize/evaluate. Shared proof replay and recipes remain trusted
dependencies, so agreement is not an independent proof. Check literal expected
coordinates and deliberately modified proof/recipe identities separately.

Include unresolved, empty, exhausted, exact subset, reversed request order,
parent/child substitution, retained parent state, correlation identity and exact
conversion refusal. This run establishes no arbitrary-length composition,
general mesh support, comparative speed, SSM-4 campaign acceptance or hardware
claim. Inspect terminal runner discrepancy read-only; do not repair markers.
