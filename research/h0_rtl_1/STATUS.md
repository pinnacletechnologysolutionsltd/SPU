# H0-RTL-1 partial experiment — REVISE

Baseline `e90bef1`. The only implementation here is an isolated two-bank
program-storage experiment. It is **not** a CPU frontend, execution controller,
reset barrier or production implementation. The frozen Gen-1 core and production
RTL are unchanged. No instruction can be issued by these files.

The experiment accepts ordered writes to an inactive 14-word bank, scans the
stored words for the fixed six-SLI/SLD/SMUL/six-SRD S0 layout and nonzero
denominator, and promotes only after the full scan. Incomplete and invalid
replacement leave the prior active selection and validity intact. `run_owned`
blocks new load actions; physical reset invalidates bank validity. `fetch_data`
uses a registered read. The interface and validation are illustrative, not a
frozen contract: there is no independent received-image integrity comparison,
run identity, externally observable reset protocol, write/verify provenance,
or qualified simultaneous-event policy. A read output can retain prior bits
until a clock after reset; any future consumer must qualify it using valid and
an independently established reset barrier. No claim of safe core connection.

Reproduce the focused bank test and its temporary mutants from the worktree:

```bash
python3 research/h0_rtl_1/run_banks.py --output build/h0-rtl-1/<new-run>
```

The test checks two promotions, incomplete and malformed replacements,
preservation of the active word, owned-load refusal, interrupted staging and
physical-reset validity invalidation. The runner requires two designated
negative controls to compile and fail at their intended checks: wrong bank
selection and premature promotion. This does not cover CPU execution, full
image integrity, stopped clocks, normalization or stale completion.

## Blocking boundary and remaining work

H0-RESET-2 established only bounded physical-reset simulation of the frozen
program, not controller-owned reset through all arithmetic states. The core's
`surd_retire_valid` is untagged, and the frozen supervisor has no controlled
per-run initialization port. In particular, no verified controlled-reset
composition or evidence covers the executor → arithmetic → normalizer → GCD/
quotient → done → retirement path when a run is interrupted in normalization.
An old untagged retirement coincident with a new issue cannot be identified as
old from the existing retirement signal alone. A quiet interval is not proof
that the event cannot occur. This is a missing barrier proof, not a finding that
the frozen arithmetic core necessarily requires modification.

Before connecting a writable frontend, specify and independently establish
clocked reset coverage of every producer, issue/retire priority, stopped-clock
behavior, physical-reset dominance and retained-bank isolation. Then implement
the owned-start/reset/completion controller and run A/B with all six results
against independent oracles, including normalization interruption, reset and
stale-completion mutation controls. If that barrier cannot be shown using the
existing core interfaces, return to review rather than introducing tags or
changing the frozen core silently.
