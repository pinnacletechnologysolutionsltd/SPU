# QCG-0 W31 independent interpreter — preparation status

Date: 2026-10-23. Author: ChatGPT (GPT-6).

## Decision
Independent interpreter author is ChatGPT, not Claude. Development/preparation is authorized by the owner discussion; **the bounded derivation campaign has not launched**. Attempts consumed: **0/3**. Formal P0 acceptance/freeze HOLD.

## Inputs
The supplied `handoff_w31.tar.gz` was extracted into a work directory. All 12 entries in the packet's `SHA256SUMS` verified. No candidate implementation or candidate results are in the packet or were consulted.

## New source
`w31_arithmetic.py` SHA-256: `45b2a3363d3cc665bdd1b9b24e81e809fdc4d0080f8da9f527262d82980e23b0`.
This independently implements the W31 exact rational representation and M/A/D/S/K operations with §3 raw/reduced refusal ordering, basic event traces, and counts. Ten foundation unit assertions passed when run as a normal preparation test. An initial unit test mistakenly used a W31-refusing rational addition/division, which was corrected in the test itself. Those unit-test invocations were **not** sequential or Cell B stage derivation attempts.

## Not yet implemented or qualified
- Contract §5 polynomial primitives, preparation and all arm-specific execution programs.
- Sequential dependency scheduler, Cell B route evaluator and event-ID/context production.
- Complete §2 ledger costs, G_bits, W_bits, live/retained state, and independent table/reference checks.
- Deterministic stage campaign entrypoint, preflight, resource enforcement and append-only attempt journal.
- Frozen derivation-source identity or final command (the source hash above identifies the current *partial* arithmetic component only).

## Release condition
Do not invoke any of the three bounded derivation attempts until the remaining implementation has been independently authored, statically checked and frozen; record its complete source hashes, exact command, environment, enforcement method, and append-only attempt log. A failed preflight should produce HOLD without consuming an attempt.
