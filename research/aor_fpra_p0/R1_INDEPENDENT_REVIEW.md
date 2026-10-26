# AOR × FPRA P0 — R1 independent source/command review

2026-10-23. Reviewer: Claude (independent of the R1 author). **No registered derivation was run.**
No registered case, control microcase, registered fixture or registered request list was constructed or
executed; the proposed launch command was not executed; nothing was written under `build/`. This
review is not launch authorization and not acceptance promotion. Frozen Revision 3
(`8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb`), the derivation packet and the
reference source were not modified.

Reviewed: [R1_COMPLETION.md](R1_COMPLETION.md), [R1_SOURCE_SHA256.json](R1_SOURCE_SHA256.json)
(file SHA-256 `8883adcfdfdda4083658bb203b30b85ef703ea91328dcf34f0c2fb2bf590c657`),
[REFERENCE_ENCODINGS.md](REFERENCE_ENCODINGS.md), [R1_PROPOSED_COMMAND.txt](R1_PROPOSED_COMMAND.txt).

**Verdict:** no blocking defect found in the reference source or the proposed command. Proceeding to a
dynamic-preflight gate is supported after F1 is clarified and F2/F3 are decided by the owner. See the
[readiness addendum](R1_PREFLIGHT_READINESS_ADDENDUM.md).

## 1. Independently inspected source (read, not executed)

- `derive.py`, `accounting.py`, `semantics.py`, `controls.py`, `pell.py` read in full;
  `REFERENCE_ENCODINGS.md` read in full; `tools/run_detached_job.sh` read; `REFERENCE_DERIVATION_PACKET.md`
  (allowance, launch procedure, blockers) read. Not reviewed: `run_detached_job_worker.sh` and
  `run_elapsed_deadline.py` internals (hash identity only), the Revision 3 review documents.
- **Oracle math (`pell.py`):** the signed step `(a,b)·(2±√3)`, product `(ac+3bd, ad+bc)` and norm `a²−3b²` are
  correct by hand derivation.
- **Independence:** `semantics.py` imports only `accounting`; it does not import `pell.py`. Model and oracle
  share the `decimal` serializer and `Refusal` only.
- **Rollback/atomicity:** all publication events (rung/cache INSTALL, COMMIT) are reserved before state is
  assigned; nothing after assignment can raise a refusal; refusals run `private_cleanup` and assert committed
  state unchanged; failed work remains charged.
- **Writer:** exclusive `xb` pending files, fsync, per-file 2 MiB / total 4 MiB checks, manifest last,
  manifest/summary disposition checks, source and provenance re-hash before the manifest.
- **Command:** exact argv and cwd check, absolute binaries, limits assertion, `printf '%q'`→`shlex.split`
  reproduction of the expected argv, evidence files written before `systemd-run`, registered destination absent.

## 2. Executed checks (all unregistered; none touched `build/` or the repository)

- Hash verification of all 13 manifest entries, `/usr/bin/python3` and `/usr/bin/prlimit`
  (versions and SHA-256 equal the report). Re-checked after the runs below: unchanged.
- The report's own synthetic suite, with its exact command: 31 tests OK in 7.1 s.
- **Review-conduct disclosure (see §4):** a scratch micro-benchmark of `Ledger.event` throughput
  (100,000 iterations, with and without `tracemalloc`); a size probe (`State` construction and one STEP in
  arms A and C); and a model-only run of a *mirrored*, nominal-shaped, unregistered tape (cell 1 first, then
  cell 0 with opposite signs) in arms A, C, D at rho 1/8/64 under `tracemalloc`. Scripts lived in the session
  scratchpad. These were not registered cases but they are timing measurements.

Measured values (unregistered, informational only): worst model-only event count 54,384 (arms C/D, rho=1)
against the 100,000 per-case cap; STEP about 340 (A) / 240 (C) events after setup; terminal inventory
about 4.7 KB; STEP evidence row about 1 KB; `Ledger.event` about 71k/s plain and 24k/s under `tracemalloc`;
model-only wall time summed over the 12 nominal shapes about 18 s under `tracemalloc`.

## 3. Findings

- **F1 — nondeterministic fields in artifacts (medium, must clarify before launch).** `nominal.json` and
  `controls.json` rows embed `modeled_ns` and `reference_ns` (`derive.py:177`), case records embed
  `setup_replay_ns` and `reference_setup_ns` (`:192`), and `summary.json` embeds elapsed, heap and RSS
  (`:265-267`). File and manifest SHA-256 values are therefore not reproducible. The per-case ledger `digest`
  is deterministic. Acceptance needs a stated deterministic projection.
- **F2 — runtime margin unmeasured (medium).** The 60-second limit is frozen and a TIMEOUT consumes the
  single invocation. My rough estimate of 30–45 s total is uncertain; oracle, validation, identity hashing,
  serialization and the 80 control cases were not measured. `tracemalloc` slows the event loop about 3×.
- **F3 — source preservation (low–medium).** `research/aor_fpra_p0/` is untracked, so the reviewed sources
  are pinned only by SHA-256. (Follow-up inspection found additional git hazards; see the addendum.)
- **F4 — control 4 is not fully independent (low).** `controls.py:118-119` overrides the oracle's expected
  snapshot using the fault name, and `:147` skips the receipt comparison for every non-OBSERVE request in
  that control. The STALE verdict itself is still checked.
- **F5 — unexplained diagnostic constants (low).** `semantics.py:419-420` charges 12 READ and 16 COPY per
  refusal into `diagnostics` with no derivation. They do not affect the work caps.
- **F6 — import-before-verify (low).** Reference modules execute (`derive.py:18-22`) before their hashes are
  checked (`:238-242`). A change between import and check would not be caught for that run; the post-run
  re-hash (`:268`) covers later changes.
- **F7 — fail-closed hazards (info).** The milestone list is capped at the last 64 (`accounting.py:105`) and
  control 13's conjugation-order check depends on it (estimated about 26 per OBSERVE, fits). The 512-slot and
  64-pair capacity refusals, any `AssertionError`, and a `MemoryError` under the 1 GiB address-space limit abort
  the derivation without a complete artifact. Safe against false acceptance, but each consumes the attempt.
- **F8 — provenance content (info).** `git_status.txt` is copied into the manifest and records the entire
  shared dirty tree (about 30 KB); it is nondeterministic and falls under F1.

Scope notes: `SET_EQUAL` that changes state is not modeled in `Oracle.advance` (the registered tape only uses a
no-op); the estimated six-file total of 2.4–3 MB against the 4 MiB cap is unmeasured.

## 4. Conduct disclosure

`REFERENCE_DERIVATION_PACKET.md` states: "No timing trial is authorized." I read that sentence only after the
measurements in §2 had been run. Those measurements were taken on unregistered tapes and scratch scripts, and
nothing registered was executed, but they are timing trials of the reference code and were not authorized.
Treat their numbers as non-evidential context for this review, not as launch-readiness evidence, and not as a
basis for the registered allowance. The owner may regard the measurements as a deviation.
