# AOR × FPRA P0 — R1 preflight-readiness addendum (PROPOSED)

2026-10-23. Prepared for owner review. **Not executed. Not authorization.** Does not change frozen Revision 3
(`8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb`), the reference algorithms, the registered
fixtures, `R1_SOURCE_SHA256.json` or `derive.py`. No registered derivation has been run. Companion:
[R1_INDEPENDENT_REVIEW.md](R1_INDEPENDENT_REVIEW.md) (findings F1–F8).

## Disposition (owner decision, 2026-10-23)

**F2's synthetic timing preflight (section B) is REJECTED.** The frozen 60-second allowance, the 1 GiB limit,
zero retries and "no timing trial is authorized" in `REFERENCE_DERIVATION_PACKET.md` remain unchanged. Section B
and the reviewer's conduct disclosure in `R1_INDEPENDENT_REVIEW.md` §4 are retained below as historical
evidence only; the proposed driver and command must not be written or run. Registered execution remains HOLD.
Sections A, C–E and G otherwise stand as written, except that blocker G.1 is resolved by this rejection and
the two shared runner tools in section C item 2 are an unresolved, separately tracked prerequisite
(not part of this preservation set).

## A. F1 — reproducibility by deterministic semantic projection

Two hashes are kept, with different roles:
- **Run-specific provenance:** the full-file SHA-256 of each of the six JSON artifacts and of `manifest.json`
  (recorded in the manifest `files` map and the external manifest hash). Never expected to repeat across runs.
- **Semantic reproducibility:** SHA-256 of the canonical projection below.

Projection `P(file)`: parse the JSON, delete the excluded fields, serialize with sorted keys, compact separators,
`ensure_ascii=False`, `allow_nan=False`, one final LF, then SHA-256. The suite digest is SHA-256 of the six lines
`name:hex\n` in the order `nominal, controls, accounting, faults, summary, manifest`.

Excluded fields, exactly:
| File | Excluded |
|---|---|
| `nominal.json`, `controls.json` | per-record `modeled_ns`, `reference_ns`; per-case `setup_replay_ns`, `reference_setup_ns` |
| `accounting.json`, `faults.json` | none (no timing fields) |
| `summary.json` | `elapsed_ns_after_preflight`, `heap_peak_bytes_through_payload_write`, `rss_kib` |
| `manifest.json` | `files`, `executable` (path, sha256, version), `launcher_evidence`, `launcher_evidence_sha256` |

Retained in the projection: all event counts, ledger `digest` values, peak-bit counters, receipts, outputs,
state hashes, refusal stages, `spec_sha256`, `sources`, `limits`, `argv`, `source_manifest_sha256`, `acceptance`.
The per-case ledger digest is the primary deterministic anchor. A projection checker is a separate, stdlib-only
post-run tool; it is not written yet and would be reviewed before use.

## B. F2 — proposed bounded synthetic preflight (NOT authorized by the frozen contract)

**Contract status, stated plainly:** the derivation packet says "No timing trial is authorized," and its launch
procedure lists only identity/callability/limit/destination rechecks as preflight checks. This proposal therefore
requires an explicit owner amendment. Proposed amendment text: *"One disposable synthetic full-path preflight is
authorized to bound runtime and output size. It uses no registered request, consumes no registered slot, and its
output is never evidence."* Without that amendment the F2 risk stays open, or is accepted by the owner.

Why it cannot consume or masquerade as the registered attempt (if authorized):
- Different command, driver, output root and unit name: output under `build/aor_fpra_preflight/synthetic_01`,
  never `build/aor_fpra_p0/`. The registered path stays absent and is rechecked before registered launch.
- The registered `derive.py` pins its exact argv, spec output name `fixtures` and the registered evidence parent;
  the preflight driver does none of that and is not `derive.py`.
- The driver writes `SYNTHETIC_NOT_EVIDENCE.txt` first and sets `"synthetic_preflight":true,"registered":false`
  in its summary and manifest. Acceptance rules count only the registered directory.
- It calls no registered constructor (`controls.cases()`, `nominal_tape()`), uses no registered request list,
  and its result cannot change the frozen allowance (60 s, 1 GiB, 4 MiB, zero retries) or any registered bound.

Driver design (a NEW file `research/aor_fpra_p0/preflight/synthetic_preflight.py`, outside the gitignored
`reference/` directory; not yet written; to be reviewed, hashed and pinned before any run):
- Verify the six reference modules against `R1_SOURCE_SHA256.json`, then load them by path.
- Import `execute_case` and `Writer` from the reviewed `derive.py`. Importing does not run `main`.
- Cases: mirrored nominal-shaped tapes (cell 1 first, then cell 0 with opposite signs) for arms A–D at rho
  1/8/64 (12 cases), plus 20 non-registered, fault-free, 1–3-request control-shaped tapes with ids ≥ 101 in
  each arm, to approximate fixed per-case overhead and `controls.json` size.
- Write all six files through the reviewed `Writer` (2 MiB/4 MiB checks, fsync, link, manifest last).
- Print elapsed, RSS, heap peak, per-file bytes, total bytes, total modeled/reference events.

Coverage: serialization (OBSERVE `serialize`, BYTE32 events), `tracemalloc` overhead, the 1 GiB address-space
limit, the output writer end to end. Not covered: registered controls' fault, work-limit and bad-proof paths,
and any registered-tape-specific behavior. The result bounds risk; it cannot certify the registered run.

Proposed command (not executed; the driver does not exist yet):
```bash
tools/run_detached_job.sh \
  --output build/aor_fpra_preflight/synthetic_01 \
  --timeout 60 --notify-desktop -- \
  /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- \
  /usr/bin/python3 -I -B research/aor_fpra_p0/preflight/synthetic_preflight.py \
  --reference-manifest research/aor_fpra_p0/R1_SOURCE_SHA256.json \
  --output build/aor_fpra_preflight/synthetic_01/fixtures
```
Resource bounds equal the registered ones: 60 s external deadline, 1 GiB address space, 4 MiB per file, 16 MiB
evidence total, zero retries. A TIMEOUT or cap hit here is informative and consumes nothing registered; the
launcher refuses to reuse the directory, so a repeat needs a new unique name and new owner authorization.
Expected outputs: exactly one terminal marker (COMPLETE/FAILED/TIMEOUT), six JSON files under `fixtures/`,
`deadline.json`, stdout lines for elapsed, heap, RSS, bytes, events; summary status
`DERIVED_PENDING_INDEPENDENT_ACCEPTANCE` with `synthetic_preflight:true`.

## C. F3 — preserving the exact reviewed tree in Git

Findings from the pre-check, before any staging:
1. **`.gitignore` line 80 (`reference/`) ignores `research/aor_fpra_p0/reference/` entirely.** A plain
   `git add research/aor_fpra_p0` would silently omit all six reference sources. Stage them by explicit path
   with `git add -f`. Do not edit `.gitignore`.
2. **The pinned tool hashes describe uncommitted state.** `tools/run_detached_job_worker.sh` is modified in
   the working tree (it now delegates the deadline to `run_elapsed_deadline.py`; the manifest hash
   `bf2f299a…` matches the modified file). `tools/run_elapsed_deadline.py` is untracked. Preserving the
   reviewed tree exactly requires committing those two paths; they are shared tools, so this needs owner
   confirmation, and the committed worker would differ from the previous HEAD version.
   `tools/run_detached_job.sh` is tracked and unmodified.
3. Everything else under `research/aor_fpra_p0/` is untracked (18 files at inspection).

Proposed explicit staging (nothing staged yet): the 12 non-reference files, the 6 reference sources with
`-f`, the 2 tool paths above, plus the two new documents. Commit hash is then recorded *separately* by a
follow-up record (for example `R1_PRESERVATION_RECORD.md` holding the commit id, `git ls-tree -r` hash of
`research/aor_fpra_p0`, and `R1_SOURCE_SHA256.json` SHA-256), because a commit cannot contain its own hash and
`R1_SOURCE_SHA256.json` must stay byte-identical. The launcher's `git_commit` evidence file will separately
record HEAD at launch.

## D. F4–F8 — qualifications (no change to validator or accounting semantics)

- **F4:** Control 4's receipt and snapshot check is partly circular by construction (fault-name override,
  receipt comparison skipped). Treat its evidence as "the mutant reports the injected stale value and the model
  refuses STALE", not as an independent receipt proof. Controls 1–3, 6 and 20 retain independent comparison.
- **F5:** The 12 READ / 16 COPY refusal diagnostics are nominal bookkeeping, not derived counts, and are
  excluded from work-cap and comparison conclusions. A derivation would be a separate encoding decision.
- **F7:** Any `AssertionError`, capacity refusal or `MemoryError` is a FAIL/HOLD of the invocation, never an
  inequality or a pass. Milestone truncation fails closed.
- **F8:** Launcher evidence in the manifest is provenance, not an input to semantic reproducibility (section A).
- **SET_EQUAL scope:** the oracle does not model a state-changing `SET_EQUAL`; the registered tape uses only the
  no-op.

## E. F6 — external hash verification before Python

Yes, F6 can be addressed without modifying the reviewed reference. Immediately before launch, as a separate
operator step (a wrapper inside the pinned command is not possible, because `derive.py` requires the first
argv elements to be exactly `prlimit … python3 -I -B …`):
```bash
python3 -I -B -c 'import json;[print(h+"  "+p) for p,h in json.load(open("research/aor_fpra_p0/R1_SOURCE_SHA256.json")).items()]' \
  | sha256sum -c -
sha256sum research/aor_fpra_p0/R1_SOURCE_SHA256.json   # expect 8883adcf…0c657
git diff --quiet HEAD -- research/aor_fpra_p0 tools/run_detached_job.sh \
  tools/run_detached_job_worker.sh tools/run_elapsed_deadline.py   # after the F3 commit
```
Verified now: all 13 entries print OK. The remaining window (between this check and Python importing the
modules) cannot be removed without changing the reviewed command; `derive.py`'s own check (after import) and
post-run re-hash narrow it, and a committed tree plus a clean `git diff` makes accidental drift detectable.
The residual risk is a deliberate swap within that interval, which is out of the failure model here.

## F. Source identities (unchanged)

| Path | SHA-256 |
|---|---|
| `PREPARATION.md` | `8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb` |
| `R1_SOURCE_SHA256.json` | `8883adcfdfdda4083658bb203b30b85ef703ea91328dcf34f0c2fb2bf590c657` |
| `/usr/bin/python3` (3.14.8) | `375532f83be620283ab780c14ca6bcc5907dc379d2b621de0c5d0a112cf5458b` |
| `/usr/bin/prlimit` (util-linux 2.42.4) | `092bb6db10a743ecccfc7d6e72055007064abf8910c85d736832fb53697fff96` |
All other entries are in `R1_SOURCE_SHA256.json` and were verified equal.

## G. Remaining blockers

1. **Owner decision on F2:** amend "no timing trial is authorized" or accept the runtime risk. Without it the
   synthetic preflight must not run.
2. The preflight driver does not exist; it must be written, reviewed and pinned.
3. **F3:** owner confirmation to commit the two shared tool paths; forced add of the gitignored `reference/` files.
4. Adopt section A as the acceptance reproducibility rule before launch.
5. Registered-launch gates still unperformed (and only under a later GO): user-manager availability, PATH and
   tool identities, destination exclusivity, conflicting-source-change check, section E verification.
6. Independent acceptance of the saved fixtures remains a separate later gate; nothing here promotes it.
