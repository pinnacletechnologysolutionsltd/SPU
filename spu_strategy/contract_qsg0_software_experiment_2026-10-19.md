# QSG-0 isolated software experiment

Date: 2026-10-19. Status: executed; QSG-0 FROZEN after software fixture PASS.
Owner authorization: “Authorized”. Research acceptance remains 0/5 pending
independent result review; see [results](../docs/QSG0_SOFTWARE_RESULTS.md).
Roles: spec author and implementer: Codex; independent specification reviewer:
owner; integration auditor: deterministic isolated checks and owner result review.

## Execute from the repository root

```bash
timeout 30s python3 research/qsg0/run.py --output build/qsg0/rectangle_fan_03
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- research/qsg0 docs/QSG0_MATHEMATICAL_SPECIFICATION.md docs/QSG0_GENERATIVE_GEOMETRY_RESEARCH.md docs/QSG0_SOFTWARE_RESULTS.md spu_strategy/contract_qsg0_software_experiment_2026-10-19.md
```

Use foreground execution: this fixed tiny experiment is expected to take less
than 30 seconds. Output must be new; refuse overwrite. Preserve command, source
hashes, git identity/dirty status, Python/platform, checks and JSON measurements.
Run correctness before benchmarks; stop on any failed assertion. Use three
timing samples of 100 iterations over the same three targets per baseline,
with one untimed warm-up. Report individual samples and medians, without a
speedup claim. No repeated expensive campaign or hardware job is authorized.

Run 01 passed the initial fixture. Run 02 added bounded end-to-end timing and
source snapshots. Run 03 strengthens endpoint checks to compare every accepted
value and every refusal with the independent Fraction oracle; it supersedes
earlier runs for the final report. These are tiny local invocations, not
expensive campaign attempts.

## Implement only the frozen specification

Create single-purpose Python modules in `research/qsg0/` for independent Fraction
geometry, QSG-R32 arithmetic/model, filtered robust predicates, correctness
checks, measurements and runner. Add this contract and a results note; update
the two existing QSG-0 notes. No production arithmetic kernel, shared regression
infrastructure, RTL, ISA, FPGA tool invocation or timing input may change.
These are isolated research programs; run the scoped checks above rather than
production-kernel/hardware gates. Acceptance remains 0/5 pending result review.

Use no external dependencies. Implement a local robust orientation baseline
with outward-rounded binary64 interval filtering and exact Fraction fallback
on the original finite binary64 inputs. Identify it as a local baseline, not
Shewchuk's implementation. Test uncertain, collinear and near-degenerate cases.
Record filter/fallback counts and explicitly limit input range to this experiment.

Measure descriptor, expanded metric, rational Cartesian and binary64 Cartesian
paths under identical requested outputs. Separately measure conversion paths,
bounded primitives/checks, integer sizes, storage accounting and exact residuals.
Do not compare Python object heap size to packed-format size as a speed/storage
advantage. Include the required refusal fixtures and rational rigid controls.

## Halt conditions

If an unhandled contradiction is found, halt and flag a minimal correction.
If checks fail, fix only the isolated implementation within this scope; never
weaken a mathematical assertion or silently change the transform family.
If the fixed invocation times out, record TIMEOUT and stop; no longer timeout
or automatic rerun is authorized. If results require a different domain or
production/hardware changes, record the limitation and freeze.

The specification's corrected rectangle invariant, all four spoke quadrances,
diagonals, topology, deterministic reconstruction and atomic refusal remain
mandatory. T_t replaces a target descriptor; it is not a general deformation
solver or transformation group. Freeze QSG-0 after recording these results.
