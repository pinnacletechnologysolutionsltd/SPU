# QCG-0 W31 interpreter R2 — technical review (supporting evidence only)

Author: Claude (repository custodian). Date: 2026-10-23.
Reviewed commit: `982d121ece7a508ce84debb2b134983857cf058d` (Codex-authored R2 repair).
Frozen inventory: `SOURCE_INPUTS_R2.sha256`, SHA-256 `2269d198859785d21e50bdf3957c41b769f89f4b024593f86a4993222c1e4f8c`.

## Status of this record

**Technical PASS. This is NOT a formal independent acceptance certificate.** The author of this review also wrote the
QCG-0 P0 candidate (`research/qcg_0/p0/`). No candidate output was used in the review, but the formal-independence
qualification stands. It supplies supporting evidence only and authorizes nothing. Interpreter acceptance still needs a
reviewer without candidate-implementation involvement, or a documented owner decision accepting this qualified review.

## Checks and outcomes

| # | Check | Outcome |
|---|---|---|
| 1 | 32 inventory entries against committed bytes; inventory hash | 32/32 OK, tree clean, hash as above |
| 2 | `/usr/bin/python3 -I -S -B` required before verifier imports | Old command exits `HOLD: outer launcher requires /usr/bin/python3 -I -S -B` |
| 3 | Import path not replaceable (env, cwd, site hooks, startup customization) | Code reading: `check_startup()` uses only `sys`; only the script directory is appended, after standard-library paths. Startup test: non-isolated control hijacked, isolated run rejected |
| 4 | Invalid inventories fail closed incl. under `-O` | Explicit `require()` raises; 29/29 tests pass normally and under `-O`; preflight passes with `PYTHONOPTIMIZE=2` |
| 5 | Certified numerical-row checks mandatory, independently certified inputs | `load_reference` checks hash and shape, `check_certified` precedes artifacts and `RUNNER_DONE`; refused/unissued rows get no reference values. `QUINTIC_FIXTURE_VALUES.json` was not re-derived (pinned contract file) |
| 6 | S3 next-interval export | `export_s3` relabels only; no ops, ledger or events; refusal attributed to the ending request; q16 null and `increment_available` as specified |
| 7 | Resource limits, network isolation, exclusive attempts, authorization accounting | Preflight probe covers 1 GiB AS, 4 MiB file limit, loopback-only network. Slot exclusivity, authorization text binding and single terminal marker confirmed by code reading only; no attempt created |

Commands run (bounded by `timeout 30` and `prlimit` 1 GiB / 4 MiB): unittest discovery `test_w31_*.py` normal and `-O`
(29 tests each, OK); `PYTHONOPTIMIZE=2 python3 -I -S -B launch_w31.py --preflight` (PASS); launcher without authorization
(HOLD, no attempt directory created).

## Advisory conditions

1. Verifier circularity: `w31_verify.py` and `w31_certified.py` are imported before the inventory check, so a tampered
   verifier could vouch for itself. Before authorization run an external `sha256sum -c SOURCE_INPUTS_R2.sha256`, confirm
   `git rev-parse HEAD` and a clean relevant tree.
2. Use only the R2 `-I -S -B` entry command; earlier entry commands in older records are superseded.

## Not done

No derivation attempt consumed (0/3). No authorization file created. No tables generated. No source or inventory modified.
The registered derivation, P0, candidate freeze and interpreter acceptance remain HOLD.
