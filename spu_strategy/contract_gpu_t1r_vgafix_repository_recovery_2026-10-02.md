# Engineering Contract: VGAFIX Repository Snapshot Recovery

**Date:** 2026-10-02  
**Contract ID:** `GPU-T1R-VGAFIX-REPOSITORY-RECOVERY-2026-10-02`  
**Status:** REPOSITORY CLOSEOUT PASS — exact frozen campaign_02 snapshot; all authorized jobs and final identity checks PASS; hardware visual HOLD remains independent  
**Owner:** John Curley  
**Spec Author / Halt-and-Flag Implementer / Integration Auditor:** Codex

## 1. Phase boundary and frozen budget

Preserve the failed `campaign_01/` and its reviewed helper unchanged. The original snapshot slot is consumed (FAILED, exit 1, 9 seconds); its old successor jobs remain NOT RUN and are superseded by the new phase below, not available for independent launch. After the failed snapshot and proposed exclusion correction were reported, the owner stated "Authorized, let's redesign the contract but first we should diagnose what happened." Record renewed authorization for the correction and one new snapshot slot with the same 300-second limit, retaining the previously authorized, unconsumed 3600/1800-second gate limits in new destinations. Carry out diagnosis and redesign first, then require corrected-helper implementation review PASS before launching. No execution command is launched by drafting; do not request duplicate phase authorization for these same frozen limits.

Run the mandatory `AGENTS.md` closeout gates for the [hardware control contract](contract_gpu_t1r_vgafix_display_control_2026-10-02.md) in an isolated snapshot. Require explicit authorization for this phase and its budget; hardware authorization alone is insufficient. Start after the hardware result and evidence updates are recorded. Report the hardware result while repository closeout remains PENDING.

| Job | Maximum attempts | Timeout / maximum budget | Evidence directory |
|---|---:|---:|---|
| Source snapshot | 1 | 300 seconds | `build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/snapshot_01/` |
| Regression/triage/traces/math | 1 | 3600 seconds | sibling `gates_01/` |
| Padé synthesis/place-and-route/pack | 1 | 1800 seconds | sibling `pade_01/` |
| Entire phase | 3 total job launches | 5700 seconds cumulative | `campaign_02/` |

Consume each slot at launch for every outcome. Run sequentially; do not launch a successor unless the prior job passes in a later invocation. No retry, timeout extension, substitute command, automatic budget renewal, or hardware activity is authorized. Persist job markers, results, commands, stdout/stderr, provenance, and desktop notification attempts through the detached runner. End the turn after each `LAUNCHED`; do not poll in that turn.

## 2. Snapshot identity and isolated outputs

Before cloning, inspect the root virtual-environment inventory. Freeze `VENV_EXCLUDES={".venv", ".venv_plot", "venv"}` and `ROOT_EXCLUDES={".git", "build"} | VENV_EXCLUDES`. Derive root rsync exclusion patterns from that same set; do not maintain a second root list. A root directory containing `pyvenv.cfg` outside that frozen set halts before clone/rsync/chipdb copying. Do not auto-exclude arbitrary ignored files, directories with a `.venv` prefix, or similarly named nested source directories.

After producing the source manifest and before cloning, call `check_source_inventory(ROOT, before)` and preserve `source_inventory.json` with the discovered environment names and root exclusions. Every included symlink must be relative and resolve inside the primary root; reject absolute or escaping links before cloning instead of rewriting them. Recheck containment after copying through `manifest(CHECKOUT, True)`. The inventory preflight does not replace the destination/build guards.

Require primary-repository HEAD `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f` before preparation. Record the current dirty/untracked state, tracked binary diff, and hashes of all copied source files and symlink targets immediately before and after snapshotting. Freeze the source manifest at this preparation attempt; require before/after/checkout manifests identical. Halt on concurrent edits, missing inputs, unsafe symlinks, or copy mismatch. Do not substitute a clean HEAD checkout for the dirty working tree.

Create an independent clone without shared/hard-linked Git objects; overlay the complete working-tree source, including ignored source files and deletions, while excluding `.git`, the primary `build/`, local virtual environments, and interpreter/test caches. Record the exclusions. Reject source symlinks resolving outside the checkout; do not allow test/build outputs to escape isolation. Treat external installed tools/databases as recorded read-only toolchain inputs. Copy the chip database into the checkout, never share a writable `build/` link.

Immediately after Git checkout and before rsync or chipdb directory creation, require `checkout/build` absent: reject an existing directory, file, valid symlink, or dangling symlink. Do not clean, reuse, or delete inherited build paths/outputs. Call `require_build_directory(CHECKOUT, create=True)` to enforce absence, create a real directory exclusively, and validate its resolved path stays inside the checkout. Recheck it before chipdb directory creation and before the copy. The helper also checks the chipdb parent resolves inside the checkout. Record the resolved isolated build path in `snapshot_identity.json`.

Excluding `build/` from source hashes does not exempt it from destination validation. Require `require_build_directory(checkout)` before every gate job and for final identity checks; reject every build symlink, including one pointing inside the checkout. `manifest(checkout, True)` must perform that check before pruning `build/`. Gate-produced files inside an already validated real build directory may remain excluded from source identity; inherited paths after Git checkout must halt preparation.

Use only this chip-database input:

```text
build/chipdb/xc7a100tfgg676.bin
SHA-256 9d79e339c19fc3b42a5c409c47e58175ee199c2852d9096ea31c226e34398543
```

Use the prepared evidence-only helper at `build/gpu/t1r_vgafix_control_verification_20261002/recovery_02/prepare_snapshot.py`. Preserve its hash and reviewed command sequence. Require `campaign_02/` absent before the launcher creates `snapshot_01/`; the helper allows only that runner-created job child and refuses an existing checkout or source manifest. Keep the helper out of the copied source tree under the excluded primary `build/`. Execute the following copy operations inside it, with the manifest/identity checks above around them:

Declare `/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/recovery_02/prepare_snapshot.py` an **immutable external verification input**, deliberately excluded from the source snapshot. Freeze SHA-256 `c483c153c0f4bdacd1309e9308dd6e25722c0df6807a331c3597326d6d66486a`. Keep that exact path available and prohibit editing, replacement, renaming, or deletion from snapshot launch through verification interpretation. A changed or missing helper halts the phase; do not substitute another helper or silently revise its hash.

Verify the frozen hash before snapshot launch. Inside each §3/§4 gate job, record the absolute helper path and actual SHA-256 in the durable stdout immediately before loading it for the initial source check. Reject a mismatch before `runpy.run_path`; validate and log the resolved build directory before any gate command. Repeat the same guards for the final source check. These jobs depend on that explicitly declared external input, not an unchecked primary-tree source file. Call only `require_build_directory` and `manifest` for checkout checks; do not invoke snapshot-preparation `main()` in either gate job. Keep all generated outputs isolated as specified above. Preserve each preparation subprocess's exact arguments, exit status, stdout, and stderr as `snapshot_01/command_*.json`, `.stdout`, and `.stderr`.

```bash
git clone --no-hardlinks --no-checkout /home/user/Projects/hardware/SPU \
  build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/checkout
git -C build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/checkout \
  checkout --detach 4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f
rsync -a --delete --exclude='/.git/' --exclude='/.venv/' --exclude='/.venv_plot/' \
  --exclude='/build/' --exclude='/venv/' --exclude='__pycache__/' \
  --exclude='.pytest_cache/' --exclude='.mypy_cache/' --exclude='*.pyc' \
  --exclude='*.pyo' /home/user/Projects/hardware/SPU/ \
  /home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/checkout/
mkdir -p build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/checkout/build/chipdb
cp --reflink=auto build/chipdb/xc7a100tfgg676.bin \
  build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/checkout/build/chipdb/xc7a100tfgg676.bin
```

Require all campaign destinations absent before the initial launch; record source revision, dirty status, clone revision, source/symlink manifests, chipdb hash, and helper hash. Review the helper against §2 before execution authorization. A missing or changed helper does not authorize a substitute snapshot method.

Launch snapshot preparation from the primary root only after that prerequisite and phase authorization:

```bash
set -euo pipefail
printf '%s  %s\n' \
  c483c153c0f4bdacd1309e9308dd6e25722c0df6807a331c3597326d6d66486a \
  build/gpu/t1r_vgafix_control_verification_20261002/recovery_02/prepare_snapshot.py \
  | sha256sum -c -
tools/run_detached_job.sh \
  --output build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/snapshot_01 \
  --timeout 300 --unit spu-vgafix-verification-snapshot-20261002-02 --notify-desktop \
  -- python3 build/gpu/t1r_vgafix_control_verification_20261002/recovery_02/prepare_snapshot.py
```

In a later invocation require exactly one `COMPLETE`, exit 0, and all §2 manifest/identity checks PASS. Do not interpret partial copy logs as success. Preserve failed/timed-out snapshots without resuming or recopying. Freeze the successful snapshot for both gate jobs; check the source manifest immediately before each launch. Do not edit, stage, commit, clean, or fetch within it. Allow generated test/build outputs only under its own `build/`; record any gate-produced source-file mutation and leave closeout PENDING rather than silently updating the manifest.

## 3. One regression/triage/trace/math attempt

Require `SKIP_TESTS`, `TB_FILTER`, and `PYTHONOPTIMIZE` unset for the full gate; scope only the explicit triage invocation. Reject `PYTHONPATH` entries into the primary working tree; use the snapshot or installed dependency paths. Run the exact mandatory commands sequentially with fail-fast behavior. Launch from the primary root, but enter the isolated checkout before any gate so `verify_repo.sh`, `run_all_tests.py`, Git checks, generated outputs, and test subprocesses resolve to that checkout:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/gates_01 \
  --timeout 3600 --unit spu-vgafix-verification-gates-20261002-02 --notify-desktop \
  -- env -u SKIP_TESTS -u TB_FILTER -u PYTHONOPTIMIZE bash -euo pipefail -c '
cd /home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/checkout
python3 -c '"'"'import hashlib, json, runpy, sys; from pathlib import Path; helper = Path("/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/recovery_02/prepare_snapshot.py"); print("external_verification_helper=" + str(helper), flush=True); digest = hashlib.sha256(helper.read_bytes()).hexdigest(); print("helper_sha256=" + digest, flush=True); digest == "c483c153c0f4bdacd1309e9308dd6e25722c0df6807a331c3597326d6d66486a" or sys.exit("HALT: external helper hash mismatch"); m = runpy.run_path(str(helper)); build = m["require_build_directory"](Path.cwd()); print("isolated_build=" + str(build.resolve(strict=True)), flush=True); raise SystemExit(0 if m["manifest"](Path.cwd(), True) == json.loads(Path("../snapshot_01/source_before.json").read_text()) else "HALT: snapshot source mismatch")'"'"'
bash tools/verify_repo.sh
TB_FILTER=spu_video python3 run_all_tests.py
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
python3 -c '"'"'import hashlib, json, runpy, sys; from pathlib import Path; helper = Path("/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/recovery_02/prepare_snapshot.py"); print("external_verification_helper=" + str(helper), flush=True); digest = hashlib.sha256(helper.read_bytes()).hexdigest(); print("helper_sha256=" + digest, flush=True); digest == "c483c153c0f4bdacd1309e9308dd6e25722c0df6807a331c3597326d6d66486a" or sys.exit("HALT: external helper hash mismatch"); m = runpy.run_path(str(helper)); build = m["require_build_directory"](Path.cwd()); print("isolated_build=" + str(build.resolve(strict=True)), flush=True); raise SystemExit(0 if m["manifest"](Path.cwd(), True) == json.loads(Path("../snapshot_01/source_before.json").read_text()) else "HALT: snapshot source mismatch")'"'"'
'
```

Record the source-manifest identity and checkout Git revision/dirty state in this job's preflight record; the outer runner's primary-repository provenance is not sufficient. Require exactly one `COMPLETE`, exit 0, all eight commands executed successfully in order, and no unexpected source mutations. Do not count unexecuted commands after an earlier failure as passes. Record unrun successors NOT RUN.

## 4. One isolated mandatory Padé build attempt

Require the same frozen source snapshot; copied chipdb hash; absent Padé fixed-path outputs under the isolated `build/`; recorded toolchain versions; and unset optional build-profile overrides. Require script defaults `A7_SEED=1`, `FP4_STRUCTURED=1`, `FP4_BACKEND_SEQUENTIAL=0`, `A7_SYNTH_ABC9=0`, `PADE_DEBUG_TRACE=0`, `PADE_PIPELINED=0`, and `PIPELINED_RNS_CHECK=0`. Halt on an inherited override/profile mismatch rather than silently changing the command. Do not run in the primary working directory.

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/pade_01 \
  --timeout 1800 --unit spu-vgafix-verification-pade-20261002-02 --notify-desktop \
  -- bash -euo pipefail -c '
cd /home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/checkout
python3 -c '"'"'import hashlib, json, runpy, sys; from pathlib import Path; helper = Path("/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/recovery_02/prepare_snapshot.py"); print("external_verification_helper=" + str(helper), flush=True); digest = hashlib.sha256(helper.read_bytes()).hexdigest(); print("helper_sha256=" + digest, flush=True); digest == "c483c153c0f4bdacd1309e9308dd6e25722c0df6807a331c3597326d6d66486a" or sys.exit("HALT: external helper hash mismatch"); m = runpy.run_path(str(helper)); build = m["require_build_directory"](Path.cwd()); print("isolated_build=" + str(build.resolve(strict=True)), flush=True); raise SystemExit(0 if m["manifest"](Path.cwd(), True) == json.loads(Path("../snapshot_01/source_before.json").read_text()) else "HALT: snapshot source mismatch")'"'"'
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
python3 -c '"'"'import hashlib, json, runpy, sys; from pathlib import Path; helper = Path("/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/recovery_02/prepare_snapshot.py"); print("external_verification_helper=" + str(helper), flush=True); digest = hashlib.sha256(helper.read_bytes()).hexdigest(); print("helper_sha256=" + digest, flush=True); digest == "c483c153c0f4bdacd1309e9308dd6e25722c0df6807a331c3597326d6d66486a" or sys.exit("HALT: external helper hash mismatch"); m = runpy.run_path(str(helper)); build = m["require_build_directory"](Path.cwd()); print("isolated_build=" + str(build.resolve(strict=True)), flush=True); raise SystemExit(0 if m["manifest"](Path.cwd(), True) == json.loads(Path("../snapshot_01/source_before.json").read_text()) else "HALT: snapshot source mismatch")'"'"'
'
```

Require exactly one `COMPLETE`, exit 0, the expected Artix-7 100T/Padé/25 MHz profile, successful synthesis/place-and-route/packing, and nonempty `build/spu_a7_100t_RPLU2PADE.bit` plus synthesized JSON, routed JSON/FASM/frames/log under the isolated checkout. Record their hashes and reported clock results; halt on reported timing failure. Never copy these outputs over primary artifacts or load them into a device.

## 5. Independent outcomes and repository closeout

Report **hardware outcome recorded; repository closeout PENDING** while any prerequisite or gate is unrun/unavailable/failed/timed out or budget-exhausted. Preserve the physical result and its classification independently. A timeout is an infrastructure outcome, not a functional test failure; it still consumes the slot and cannot authorize another attempt.

Mark repository closeout PASS only after both gate jobs and source-identity checks pass. Name the manifest and exact snapshot covered; do not claim a later source revision passed. Evidence-report-only updates may record results without pretending they were inputs to the finished gate. Functional/source changes after snapshotting require new authorization and gates before overall completion. Do not commit or declare the overall engineering task complete while repository closeout is pending. The supplied scope review authorizes neither this verification phase nor hardware execution.

## 6. Diagnosis, implementation review, and phase boundary

Diagnosed failure: the old source manifest contained 5,878 entries, including 3,029 from `.venv_plot`. `.venv` was excluded; `.venv_plot` was not. Its `bin/python` points to `python3`, then `/usr/bin/python3` (currently `/usr/bin/python3.14`). Rsync copied the ignored environment as requested by its literal exclusions; the checkout manifest correctly rejected that external chain before chipdb copying. This was an incomplete source-exclusion policy, not a regression or synthesis failure. Diagnosis evidence: `build/gpu/t1r_vgafix_control_verification_20261002/diagnosis_01/`.

The new phase permits only one snapshot (300 seconds), one sequential regression/triage/trace/math job (3600 seconds), and one sequential Padé job (1800 seconds), in new `campaign_02/` destinations. Its maximum budget is 5700 seconds. Across both phases there may be at most two snapshot launches (one already consumed), one regression launch, and one Padé launch: at most 6000 seconds of assigned wall-clock limits including the original 300-second slot. Do not count unused old gate allocations twice. Renewed authority comes from the owner's subsequent instruction, not from the failed attempt; require corrected-helper implementation review PASS before execution.

The corrected 150-line helper retains all reviewed build-directory and chipdb-destination guards, adds explicit `.venv_plot` exclusion, derives rsync roots from the same manifest exclusion set, and rejects unknown root environments/nonrelocatable source symlinks before cloning. `review_03/` supplies its source, previous negative controls, temporary filesystem/rsync fixtures, exact gate guards, and recorded results. Review these before execution; no production `main()`, Git clone, repository gate, synthesis, or hardware operation is run by those fixtures.

Hardware evidence §3.33 remains independently programming/startup PASS and visual HOLD: the owner reports unchanged diagonal/crosshatch after loading the historical VGAFIX hash and confirms the VGA harness connects the same Wukong board/J10/monitor as DirtyJTAG. That confirmation is operator association, not a measured current electrical path. Current pin waveforms and post-load media remain unavailable. This contract authorizes no programming, reset, power-cycle, UART, monitor adjustment, instrument connection, or signal capture. A new hardware diagnostic requires its own measured-signal contract and frozen inputs/budget.

After exactly one snapshot COMPLETE/exit 0 and all identity guards pass, launch only the successor named in this revision, in a later invocation. Any new failure/time-out/unavailable outcome is terminal for its slot. Leave repository closeout PENDING and preserve the hardware report independently; never alter a frozen manifest to make the gate pass.

## 7. Corrected-helper review accepted; launch prerequisites

The owner reports corrected-helper implementation review PASS, independently matches frozen hash `c483c153c0f4bdacd1309e9308dd6e25722c0df6807a331c3597326d6d66486a`, and reproduces all 27 checks, including temporary rsync, shared exclusions, early rejection of unknown environments/unsafe source links, retained build-path guards, and all four current contract gate checks. The correction resolves the recorded `.venv_plot` omission without weakening source-link isolation. Preserve the supplied `review_03/` and ZIP unchanged.

The owner explicitly confirms renewed authorization is already recorded, no duplicate approval is needed, and the executor may perform the one `campaign_02/snapshot_01` launch after required preflight. Record review acceptance and preflight under `recovery_02/`; verify HEAD, unchanged helper/review-copy identity, chipdb hash, preserved prior FAILED result, absent new campaign destinations, source/environment/link inventory, installed copy/runner tools, and available user systemd manager before launch. Do not run production preparation in preflight. Finish these source-document updates before the snapshot freezes its manifest. The prior snapshot slot remains consumed; new snapshot and successor slots remain unconsumed until their respective launches. Hardware programming/startup PASS and visual HOLD remain unchanged, with no new hardware operation authorized.

Recovery preflight PASS is preserved in `recovery_02/launch_preflight_01.json`: frozen HEAD/helper/chipdb match; prior snapshot FAILED is preserved; `campaign_02/` is absent; required copy/runner tools and the host user systemd manager are available. The read-only source preview contains 2851 entries and no included symlinks; root virtual environments `.venv` and `.venv_plot` match the explicit exclusion policy. This preview precedes this result-report update and does not freeze a campaign manifest. The production helper will record and compare the final source manifests itself. Launch the one snapshot slot next; regression and Padé jobs remain NOT RUN until a later invocation establishes snapshot COMPLETE and identity PASS.

## 8. Recovery snapshot result; scoped gate launch next

In the later status invocation, `campaign_02/snapshot_01/` contained exactly one terminal marker `COMPLETE`, exit 0, duration 9 seconds, start `2026-10-02T03:22:07Z`, end `03:22:16Z`, unit `spu-vgafix-verification-snapshot-20261002-02`. The helper produced snapshot identity PASS with 2851 source entries; manifest SHA-256 `1044941c30d6703afe34f6871f669d116e893ef1c411102796a6719928fe736d`. Before/after/copied manifests agree. Independent rereading confirmed the current checkout still matches that manifest, HEAD/helper/chipdb match their frozen values, the build directory is real/contained, Git objects have no alternates, and both successor output destinations are absent. `campaign_02/snapshot_interpretation_01.json` preserves interpretation and evidence hashes.

The recovery snapshot slot is consumed. Run the §3 preflight and single 3600-second gate attempt next under existing authorization; Padé remains NOT RUN until a later invocation establishes that gate PASS. Record checkout identity/dirty state and relevant environment validation before launch. These primary documentation result updates are evidence-only and were not inputs to the completed snapshot; do not mutate the isolated source or its frozen manifest. Hardware programming/startup PASS and visual HOLD remain independent and unchanged.

## 9. Regression/triage/trace/math result; Padé launch next

The reviewed gate command launched under unit `spu-vgafix-verification-gates-20261002-02` after frozen checkout/environment preflight PASS. Launch preparation initially halted on a local shell-continuation parsing assertion; no slot was consumed then. The adapter was corrected without changing the reviewed script body. Preserve both preflight records, the original adapter, and the user-manager environment validation; this was not a regression retry.

In the later status invocation exactly one terminal marker `COMPLETE` was present in `campaign_02/gates_01/`, exit 0, duration 1558 seconds (`2026-10-02T03:37:44Z` to `04:03:42Z`). Full suite: 238 PASS, 0 FAIL (174 Verilog tests, plus software/host/oracle suites). Explicit video triage: 65 PASS, 0 FAIL including one video Verilog test. Both trace commands and all four named math/oracle commands passed in the reviewed order. Final helper/build/source guard passed; independent rereading confirms the current checkout still equals the frozen manifest. Stderr is empty. `campaign_02/gates_interpretation_01.json` preserves ordered evidence, result, source identity, and log hashes.

Snapshot and regression slots are consumed. The remaining single Padé slot is authorized under §4 at 1800 seconds; verify frozen source/chipdb, absent build outputs, default profile, environment, and recorded external toolchain before launch. Do not alter commands or profiles to bypass a failed preflight. Repository closeout remains PENDING until Padé terminal outcome and final identity checks pass. VGAFIX visual HOLD is unchanged, and no hardware activity occurred during these jobs.

## 10. Padé result and exact-snapshot repository closeout

The single Padé job passed its frozen source/chipdb/profile/toolchain preflight and launched under unit `spu-vgafix-verification-pade-20261002-02`. In the later status invocation `campaign_02/pade_01/` contained exactly one terminal marker `COMPLETE`, exit 0, duration 412 seconds, start `2026-10-02T05:24:49Z`, end `05:31:41Z`. The exact §4 command completed synthesis, place-and-route, and packing with the required Artix-7 100T/RPLU2PADE/25 MHz/default profile. Final reported clock results: `$iopadmap$clk_100mhz` 307.41 MHz and `clk_fast` 39.86 MHz, both PASS at 25 MHz; no reported timing failure. Yosys memory-lowering warnings and the fasm fast-parser warning were retained; packing succeeded through the pure-Python parser fallback.

`campaign_02/pade_interpretation_01.json` records hashes and sizes of the nonempty bitstream, synthesized/routed JSON, FASM, frames, routing log, and metrics, plus job/log/command hashes. The initial/final job helper/build/source guards passed. Independent interpretation rechecked the unchanged helper, real contained build directory, HEAD, copied chipdb, identical before/after/copied/current source manifests, and absent Git alternates. The produced bitstream remains in the isolated checkout and was neither copied over primary artifacts nor programmed.

**Repository closeout PASS** covers only `campaign_02/checkout`, HEAD `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f` plus its frozen dirty-tree snapshot, 2851 source entries, manifest SHA-256 `1044941c30d6703afe34f6871f669d116e893ef1c411102796a6719928fe736d`. `campaign_02/repository_closeout_01.json` preserves the independent outcome and all three terminal results. Recovery jobs used 1979 seconds total (9 + 1558 + 412), within the frozen limits; all three single-attempt slots are consumed. No retry or hardware operation is authorized by closeout.

These primary result-report updates were not inputs to the completed gates and do not modify the isolated snapshot. VGAFIX remains programming/startup PASS and visual HOLD by operator report, with original post-load photo/video and RGB/sync measurements pending. The physical display diagnosis remains unresolved; repository PASS establishes no new silicon or display-correctness claim.
