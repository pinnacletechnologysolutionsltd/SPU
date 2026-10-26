# D4 qualification logging repair and restart campaign

```bash
python3 -B build/d4_canonical_decision_p1b/qualification_preparation_02/verify_sources.py
python3 -B build/d4_canonical_decision_p1b/qualification_preparation_02/launch_qualification.py
```

Date: 2026-10-10. Status: COMPLETE; successful first attempt ends the restart campaign.
Owner instruction: "Diagnose, repair and restart, 3 attempts authorized."
Scope: D4 qualification orchestration only. Preserve all experiment sources,
noise profiles, learner semantics and retained results. No integrated
Surd/REGEN mapping, transport change, board operation or hardware promotion.

## Diagnosis and cancellation

The original qualification had eleven successful computational gates and
a successful initial source check. Scoped regression was advancing through
child tests; no deadlock or functional failure was established. Redirected
Python output remained buffered, leaving its log empty during execution.
The positive/negative buffering fixture reproduces that observation and
demonstrates live output with `PYTHONUNBUFFERED=1`.

The verified command process group 231560 was sent SIGTERM under the owner
restart instruction. Its supervisor and worker remained alive to record
exactly one FAILED marker, exit 143, after 455 seconds. This is an
owner-requested cancellation, not a failing functional assertion.
Original evidence remains in `build/d4_canonical_decision_p1b/qualification_01`.

## Minimal repair and evidence reuse

The new gate wrapper exports `PYTHONUNBUFFERED=1`, emits START/END records,
and writes each gate's UTC start/end time. Gate exit propagation remains
strict. An actual-wrapper self-test checks both output streams and an
intentional exit 7; no subsequent gate may run after failure.

Reuse eleven successful computational gates only after matching all 2,034
snapshot source hashes, original gate command/log/exit hashes and retained
artifact hashes. Record each reused result's original location explicitly.
Do not fabricate fresh exit files or label reused checks newly executed.
Fresh source guards run before and after the resumed qualification.
The restart begins at scoped core regression, then runs ROTC/IROTC traces,
mathematical oracles, documentation, full repository verification and the
separate requested-25-MHz Artix-7 Padé build. P1b is not retrained.

Controls reject corrupted reuse evidence, a failed source check, an active
previous attempt, a completed campaign and exhausted attempt budget.
All test evidence is in `build/d4_canonical_decision_p1b/restart_diagnosis_01`.

## Frozen campaign

Three newly authorized attempts, each with the existing 7,200-second
wall-clock limit; cumulative maximum 21,600 seconds. The canceled original
attempt belongs to its prior budget. New output directories are
`qualification_02`, `qualification_03`, and `qualification_04`; each launched
attempt consumes one slot regardless of outcome. No timeout extension,
concurrent attempt, or fourth launch is permitted. Successful completion
ends the campaign. Further retries require diagnosis in a later invocation,
within the unused authorized slots; no unattended retry loop is added.

The launcher locks the campaign, verifies frozen sources and dependencies,
and records durable launch accounting in `restart_campaign_01.json`.
After LAUNCHED end the agent turn. Interpret only exactly one terminal marker
in a later invocation. Qualification acceptance combines explicit hash-bound
reused gates with fresh gate results, including final source identity.

## Verification

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_d4_qualification_restart_2026-10-10.md
```

The restarted qualification supplies all mandatory scoped, repository, trace,
mathematical and Artix-7 gates. Do not declare this repair or D4 qualification
complete before those results are available. No test expectation is relaxed.

## Recorded result

`qualification_02` has exactly one COMPLETE marker, exit 0 and duration
2,037/7,200 seconds. All 13 fresh gate records pass; eleven computational
gates are reused under their frozen bindings. Full repository 243/0, scoped
core 75/0 and the separate requested-25-MHz Padé build pass. Final source
identity passes. The repair and bounded D4 qualification are complete for
this snapshot; two unused campaign slots are closed after success.
Evidence: `qualification_02/qualification_review.json`.
