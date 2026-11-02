# H0-SW-1 software lifecycle reference

**Status:** executable software model; not a production H0 contract, SPI client,
arithmetic implementation or hardware qualification. Implemented at baseline
`86a9274` and integrated on `6f9ad7b`. The model uses only the standard library
and is independent of a device. It does not alter the existing `SPUHostClient`
or its wire protocol. References to H0-C1, H0-CONFIG and H0-C4/C5 documents below
are to untracked review material in `spu_strategy/` that is not part of this commit.

## Evidence (recorded separately)
| Item | Result |
|---|---|
| Focused tests (`software/tests/test_h0_model.py`, 13 tests) and host parser (46 checks) | PASS |
| Independent reviews of the model and its tests | PASS |
| Full regression with this change (`run_all_tests.py`, OSS CAD Suite 20261027) | **FAILED: 264 PASS / 9 FAIL** |
| Attribution of the 9 failures | all nine reproduce on a clean `6f9ad7b` with the same failure signatures |

The nine failures are untracked research benches under `spu_strategy/` (seven
compile errors from modules or includes the runner does not find, two ROTC
simulation failures); none is related to this model. The attribution compared them
against a clean `6f9ad7b` checkout into which copies of the then-current untracked
benches were placed, so it reflects those files as they were then. The nine
benches were not waived, excluded, deleted or modified, and this note asserts no
clean release-gate total. Evidence is under `build/regress/h0-sw-1-full-01/` and
`build/regress/h0-sw-1-baseline-01/` (untracked).

## Limitations
- The ECHO operation is synthetic; no CPU instruction or arithmetic semantics are implied.
- Event identities are trusted tags. Completion events are not authenticated.
- A transaction missing its terminal or commit event stays ACTIVE (later submits return BUSY); only `reset()` clears it. There is no timeout.
- No physical hardware endpoint exists behind the model: no transport, configuration path or reset observation.
- No production H0 qualification is claimed.

## Usage
Run from the repository root:

```bash
python3 -m unittest discover -s software/tests -p test_h0_model.py -v
python3 software/tests/test_spu_host_parser.py
```

From the repository root the API is `software.spu_host.h0_model`; with the
`software/` directory on `PYTHONPATH` it is `spu_host.h0_model` (as used by the
test). Submit `Request("ECHO", integer)`,
retain its returned `Identity`, then deliver `terminal(id, Outcome.SUCCESS,
integer)` and `effect_committed(id)` in either order. `record` remains ACTIVE
until both are present, and then binds identity, success and result atomically.
ECHO is a synthetic endpoint: the supplied result must equal the operand; no
CPU instruction, arithmetic semantics, execution engine or wire encoding is
implied. A well-formed unknown operation is accepted and immediately completes
UNSUPPORTED without a result. Busy and malformed requests are rejected without
an identity or change to the current record; busy takes precedence. A matching
REFUSED terminal has no result and must precede any effect commit. Invalid,
duplicate and stale events return false and leave the current record unchanged.
Event identities must be exactly `Identity` objects whose epoch and sequence
are exactly `int` values; booleans, floats and subclasses are rejected before
comparison. Malformed identities follow the same inert false-return behavior.
The model can reject a late commit *notification* after refusal, but cannot
prevent an external engine from committing. No external effect after refusal is
a trusted engine obligation, not a guarantee established by this model or test.

The model starts ready by assumption; it does not implement configuration,
manifest selection, engine issue/acknowledgement, a separate rejection record,
snapshot capabilities, timeout/UNKNOWN handling or transport framing. It does
not establish readiness or exact canonical masks for the proposed H0 profile.
The last record is replaced at the next acceptance; clients retain identities
and must not read a prior completion as the new transaction's result.

If a SUCCESS terminal arrives without its matching effect-commit event, or an
effect-commit event arrives without its matching terminal, the record remains
ACTIVE and subsequent submissions return BUSY. The missing event can still
complete the model transaction; if it never arrives, only `reset()` clears
that state in this model. Reset-only recovery is not a ratified production
timeout policy. A missing event or timeout leaves a real transaction's outcome
uncertain; it is not evidence of a confirmed hardware refusal.

`reset()` models a **known synthetic reset**: it drops active work and records,
increments an in-memory epoch and starts the next sequence at one. This is not
a standalone cancel command, a claim of physical reset observation, a rollback
of a committed effect, or proof that an engine stops. Tokens are unique only
within one continuously running model instance; independent instances, process
restart, persistence, counter widths and wrap are outside scope. Truthful event
identity is assumed: a stale event falsely tagged as the current identity is
indistinguishable. The API is sequential and not thread-safe.

The design follows the proposed H0-C1 distinctions between busy rejection and
accepted UNSUPPORTED, transaction-associated results, and success publication
after commit and terminal. H0-C1-T1/T2 identify unresolved masks, fault handling,
identity, reset observability and commit timing; production remains HOLD. The
H0-CONFIG-2 R3 and H0-C4/C5-I1 documents describe configuration staging,
storage-edge and reset ambiguities; this model implements none of those and
does not infer physical rollback. Synthetic H0-C1 trace results do not qualify
the production SPI interface. The model's inert invalid-event handling is a
software API choice, not the R10 synthetic harness's sticky-fault semantics or
a proposed production fault policy. All actual hardware mappings, event
authenticity, transport, reset and numerical semantics require separate design
and verification.

