# Engineering Contract: VGAFIX Control Repository Verification

**Date:** 2026-10-02  
**Contract ID:** `GPU-T1R-VGAFIX-REPOSITORY-VERIFICATION-2026-10-02`  
**Status:** HALT — snapshot FAILED; snapshot budget exhausted; successor gates NOT RUN; closeout PENDING  
**Owner:** John Curley  
**Spec Author / Halt-and-Flag Implementer / Integration Auditor:** Codex

## 1. Phase boundary and frozen budget

Run the mandatory `AGENTS.md` closeout gates for the [hardware control contract](contract_gpu_t1r_vgafix_display_control_2026-10-02.md) in an isolated snapshot. Require explicit authorization for this phase and its budget; hardware authorization alone is insufficient. Start after the hardware result and evidence updates are recorded. Report the hardware result while repository closeout remains PENDING.

| Job | Maximum attempts | Timeout / maximum budget | Evidence directory |
|---|---:|---:|---|
| Source snapshot | 1 | 300 seconds | `build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/snapshot_01/` |
| Regression/triage/traces/math | 1 | 3600 seconds | sibling `gates_01/` |
| Padé synthesis/place-and-route/pack | 1 | 1800 seconds | sibling `pade_01/` |
| Entire phase | 3 total job launches | 5700 seconds cumulative | `campaign_01/` |

Consume each slot at launch for every outcome. Run sequentially; do not launch a successor unless the prior job passes in a later invocation. No retry, timeout extension, substitute command, automatic budget renewal, or hardware activity is authorized. Persist job markers, results, commands, stdout/stderr, provenance, and desktop notification attempts through the detached runner. End the turn after each `LAUNCHED`; do not poll in that turn.

## 2. Snapshot identity and isolated outputs

Require primary-repository HEAD `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f` before preparation. Record the current dirty/untracked state, tracked binary diff, and hashes of all copied source files and symlink targets immediately before and after snapshotting. Freeze the source manifest at this preparation attempt; require before/after/checkout manifests identical. Halt on concurrent edits, missing inputs, unsafe symlinks, or copy mismatch. Do not substitute a clean HEAD checkout for the dirty working tree.

Create an independent clone without shared/hard-linked Git objects; overlay the complete working-tree source, including ignored source files and deletions, while excluding `.git`, the primary `build/`, local virtual environments, and interpreter/test caches. Record the exclusions. Reject source symlinks resolving outside the checkout; do not allow test/build outputs to escape isolation. Treat external installed tools/databases as recorded read-only toolchain inputs. Copy the chip database into the checkout, never share a writable `build/` link.

Immediately after Git checkout and before rsync or chipdb directory creation, require `checkout/build` absent: reject an existing directory, file, valid symlink, or dangling symlink. Do not clean, reuse, or delete inherited build paths/outputs. Call `require_build_directory(CHECKOUT, create=True)` to enforce absence, create a real directory exclusively, and validate its resolved path stays inside the checkout. Recheck it before chipdb directory creation and before the copy. The helper also checks the chipdb parent resolves inside the checkout. Record the resolved isolated build path in `snapshot_identity.json`.

Excluding `build/` from source hashes does not exempt it from destination validation. Require `require_build_directory(checkout)` before every gate job and for final identity checks; reject every build symlink, including one pointing inside the checkout. `manifest(checkout, True)` must perform that check before pruning `build/`. Gate-produced files inside an already validated real build directory may remain excluded from source identity; inherited paths after Git checkout must halt preparation.

Use only this chip-database input:

```text
build/chipdb/xc7a100tfgg676.bin
SHA-256 9d79e339c19fc3b42a5c409c47e58175ee199c2852d9096ea31c226e34398543
```

Use the prepared evidence-only helper at `build/gpu/t1r_vgafix_control_verification_20261002/prepare_snapshot.py`. Preserve its hash and reviewed command sequence. Require `campaign_01/` absent before the launcher creates `snapshot_01/`; the helper allows only that runner-created job child and refuses an existing checkout or source manifest. Keep the helper out of the copied source tree under the excluded primary `build/`. Execute the following copy operations inside it, with the manifest/identity checks above around them:

Declare `/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/prepare_snapshot.py` an **immutable external verification input**, deliberately excluded from the source snapshot. Freeze SHA-256 `0e266023d72f0a174480863b0dd85d8e835783d55855bca591421b202c680da7`. Keep that exact path available and prohibit editing, replacement, renaming, or deletion from snapshot launch through verification interpretation. A changed or missing helper halts the phase; do not substitute another helper or silently revise its hash.

Verify the frozen hash before snapshot launch. Inside each §3/§4 gate job, record the absolute helper path and actual SHA-256 in the durable stdout immediately before loading it for the initial source check. Reject a mismatch before `runpy.run_path`; validate and log the resolved build directory before any gate command. Repeat the same guards for the final source check. These jobs depend on that explicitly declared external input, not an unchecked primary-tree source file. Call only `require_build_directory` and `manifest` for checkout checks; do not invoke snapshot-preparation `main()` in either gate job. Keep all generated outputs isolated as specified above. Preserve each preparation subprocess's exact arguments, exit status, stdout, and stderr as `snapshot_01/command_*.json`, `.stdout`, and `.stderr`.

```bash
git clone --no-hardlinks --no-checkout /home/user/Projects/hardware/SPU \
  build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout
git -C build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout \
  checkout --detach 4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f
rsync -a --delete --exclude='/.git/' --exclude='/build/' \
  --exclude='/.venv/' --exclude='/venv/' --exclude='__pycache__/' \
  --exclude='.pytest_cache/' --exclude='.mypy_cache/' --exclude='*.pyc' \
  --exclude='*.pyo' /home/user/Projects/hardware/SPU/ \
  /home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout/
mkdir -p build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout/build/chipdb
cp --reflink=auto build/chipdb/xc7a100tfgg676.bin \
  build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout/build/chipdb/xc7a100tfgg676.bin
```

Require all campaign destinations absent before the initial launch; record source revision, dirty status, clone revision, source/symlink manifests, chipdb hash, and helper hash. Review the helper against §2 before execution authorization. A missing or changed helper does not authorize a substitute snapshot method.

Launch snapshot preparation from the primary root only after that prerequisite and phase authorization:

```bash
set -euo pipefail
printf '%s  %s\n' \
  0e266023d72f0a174480863b0dd85d8e835783d55855bca591421b202c680da7 \
  build/gpu/t1r_vgafix_control_verification_20261002/prepare_snapshot.py \
  | sha256sum -c -
tools/run_detached_job.sh \
  --output build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/snapshot_01 \
  --timeout 300 --unit spu-vgafix-verification-snapshot-20261002-01 --notify-desktop \
  -- python3 build/gpu/t1r_vgafix_control_verification_20261002/prepare_snapshot.py
```

In a later invocation require exactly one `COMPLETE`, exit 0, and all §2 manifest/identity checks PASS. Do not interpret partial copy logs as success. Preserve failed/timed-out snapshots without resuming or recopying. Freeze the successful snapshot for both gate jobs; check the source manifest immediately before each launch. Do not edit, stage, commit, clean, or fetch within it. Allow generated test/build outputs only under its own `build/`; record any gate-produced source-file mutation and leave closeout PENDING rather than silently updating the manifest.

## 3. One regression/triage/trace/math attempt

Require `SKIP_TESTS`, `TB_FILTER`, and `PYTHONOPTIMIZE` unset for the full gate; scope only the explicit triage invocation. Reject `PYTHONPATH` entries into the primary working tree; use the snapshot or installed dependency paths. Run the exact mandatory commands sequentially with fail-fast behavior. Launch from the primary root, but enter the isolated checkout before any gate so `verify_repo.sh`, `run_all_tests.py`, Git checks, generated outputs, and test subprocesses resolve to that checkout:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/gates_01 \
  --timeout 3600 --unit spu-vgafix-verification-gates-20261002-01 --notify-desktop \
  -- env -u SKIP_TESTS -u TB_FILTER -u PYTHONOPTIMIZE bash -euo pipefail -c '
cd /home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout
python3 -c '"'"'import hashlib, json, runpy, sys; from pathlib import Path; helper = Path("/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/prepare_snapshot.py"); print("external_verification_helper=" + str(helper), flush=True); digest = hashlib.sha256(helper.read_bytes()).hexdigest(); print("helper_sha256=" + digest, flush=True); digest == "0e266023d72f0a174480863b0dd85d8e835783d55855bca591421b202c680da7" or sys.exit("HALT: external helper hash mismatch"); m = runpy.run_path(str(helper)); build = m["require_build_directory"](Path.cwd()); print("isolated_build=" + str(build.resolve(strict=True)), flush=True); raise SystemExit(0 if m["manifest"](Path.cwd(), True) == json.loads(Path("../snapshot_01/source_before.json").read_text()) else "HALT: snapshot source mismatch")'"'"'
bash tools/verify_repo.sh
TB_FILTER=spu_video python3 run_all_tests.py
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
python3 -c '"'"'import hashlib, json, runpy, sys; from pathlib import Path; helper = Path("/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/prepare_snapshot.py"); print("external_verification_helper=" + str(helper), flush=True); digest = hashlib.sha256(helper.read_bytes()).hexdigest(); print("helper_sha256=" + digest, flush=True); digest == "0e266023d72f0a174480863b0dd85d8e835783d55855bca591421b202c680da7" or sys.exit("HALT: external helper hash mismatch"); m = runpy.run_path(str(helper)); build = m["require_build_directory"](Path.cwd()); print("isolated_build=" + str(build.resolve(strict=True)), flush=True); raise SystemExit(0 if m["manifest"](Path.cwd(), True) == json.loads(Path("../snapshot_01/source_before.json").read_text()) else "HALT: snapshot source mismatch")'"'"'
'
```

Record the source-manifest identity and checkout Git revision/dirty state in this job's preflight record; the outer runner's primary-repository provenance is not sufficient. Require exactly one `COMPLETE`, exit 0, all eight commands executed successfully in order, and no unexpected source mutations. Do not count unexecuted commands after an earlier failure as passes. Record unrun successors NOT RUN.

## 4. One isolated mandatory Padé build attempt

Require the same frozen source snapshot; copied chipdb hash; absent Padé fixed-path outputs under the isolated `build/`; recorded toolchain versions; and unset optional build-profile overrides. Require script defaults `A7_SEED=1`, `FP4_STRUCTURED=1`, `FP4_BACKEND_SEQUENTIAL=0`, `A7_SYNTH_ABC9=0`, `PADE_DEBUG_TRACE=0`, `PADE_PIPELINED=0`, and `PIPELINED_RNS_CHECK=0`. Halt on an inherited override/profile mismatch rather than silently changing the command. Do not run in the primary working directory.

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/pade_01 \
  --timeout 1800 --unit spu-vgafix-verification-pade-20261002-01 --notify-desktop \
  -- bash -euo pipefail -c '
cd /home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout
python3 -c '"'"'import hashlib, json, runpy, sys; from pathlib import Path; helper = Path("/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/prepare_snapshot.py"); print("external_verification_helper=" + str(helper), flush=True); digest = hashlib.sha256(helper.read_bytes()).hexdigest(); print("helper_sha256=" + digest, flush=True); digest == "0e266023d72f0a174480863b0dd85d8e835783d55855bca591421b202c680da7" or sys.exit("HALT: external helper hash mismatch"); m = runpy.run_path(str(helper)); build = m["require_build_directory"](Path.cwd()); print("isolated_build=" + str(build.resolve(strict=True)), flush=True); raise SystemExit(0 if m["manifest"](Path.cwd(), True) == json.loads(Path("../snapshot_01/source_before.json").read_text()) else "HALT: snapshot source mismatch")'"'"'
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
python3 -c '"'"'import hashlib, json, runpy, sys; from pathlib import Path; helper = Path("/home/user/Projects/hardware/SPU/build/gpu/t1r_vgafix_control_verification_20261002/prepare_snapshot.py"); print("external_verification_helper=" + str(helper), flush=True); digest = hashlib.sha256(helper.read_bytes()).hexdigest(); print("helper_sha256=" + digest, flush=True); digest == "0e266023d72f0a174480863b0dd85d8e835783d55855bca591421b202c680da7" or sys.exit("HALT: external helper hash mismatch"); m = runpy.run_path(str(helper)); build = m["require_build_directory"](Path.cwd()); print("isolated_build=" + str(build.resolve(strict=True)), flush=True); raise SystemExit(0 if m["manifest"](Path.cwd(), True) == json.loads(Path("../snapshot_01/source_before.json").read_text()) else "HALT: snapshot source mismatch")'"'"'
'
```

Require exactly one `COMPLETE`, exit 0, the expected Artix-7 100T/Padé/25 MHz profile, successful synthesis/place-and-route/packing, and nonempty `build/spu_a7_100t_RPLU2PADE.bit` plus synthesized JSON, routed JSON/FASM/frames/log under the isolated checkout. Record their hashes and reported clock results; halt on reported timing failure. Never copy these outputs over primary artifacts or load them into a device.

## 5. Independent outcomes and repository closeout

Report **hardware outcome recorded; repository closeout PENDING** while any prerequisite or gate is unrun/unavailable/failed/timed out or budget-exhausted. Preserve the physical result and its classification independently. A timeout is an infrastructure outcome, not a functional test failure; it still consumes the slot and cannot authorize another attempt.

Mark repository closeout PASS only after both gate jobs and source-identity checks pass. Name the manifest and exact snapshot covered; do not claim a later source revision passed. Evidence-report-only updates may record results without pretending they were inputs to the finished gate. Functional/source changes after snapshotting require new authorization and gates before overall completion. Do not commit or declare the overall engineering task complete while repository closeout is pending. The supplied scope review authorizes neither this verification phase nor hardware execution.

## 6. Draft checks; execution pending

The owner independently reproduced the prior supplied fixture passes and matched the prior frozen helper hash, then found an untested excluded-path escape: `checkout/build` could be an external symlink pruned before validation. Record that as an implementation isolation blocker. Preserve `review_01/` unchanged as historical review evidence; its passing fixtures did not establish build-destination safety.

The corrected 146-line helper adds exclusive build-directory creation after Git checkout and explicit validation before source pruning, chipdb writes, and gate commands. Its corrected hash is frozen in §2 and every execution/import guard. The preserved `review_02/` packet supplies the corrected code and additional excluded-build/inherited-output fixtures. The owner reports implementation review PASS and independent reproduction of all 20 fixture checks, including rejection of inherited build paths before copying and external/dangling build symlinks in all four gate checks. The build-path blocker is resolved. Preserve the packet's original HOLD wording as historical evidence of its review-time status.

The frozen hash covers the actual `prepare_snapshot.py` file bytes with one final newline. The Markdown code block in the historical packet adds an extra blank line; hash the supplied file, or extract the code with exactly one final newline. The primary helper and supplied file copy both match the frozen hash.

After that implementation review, the owner stated "Authorized". Record authorization for this reviewed verification phase with the unchanged maximum attempt counts and 300/3600/1800-second timeouts (5700 seconds cumulative). No verification slot has been consumed. Start only after the hardware result and evidence updates required by §1 are recorded. The owner subsequently stated "Authorized for vgafix" and confirmed unchanged physical setup and current observer readiness. Hardware execution follows its separate contract; actual snapshot preparation, repository gates, and synthesis remain NOT RUN.

The hardware result is now recorded in hardware evidence §3.33 and `control_01/hardware_result_01.json`: programming/startup PASS, control visual HOLD from the owner's report that the same diagonal/crosshatch as T1r persists, original photo/video support pending. The owner missed the first interval and explicitly requested the single observation repeat, now consumed. Hardware execution has stopped. Freeze the source snapshot only after these contract/ledger updates; original media may be preserved under the excluded hardware `build/` evidence directory without source mutation. Current helper and chipdb hashes match §2, and the campaign destination is absent. Launch the single 300-second snapshot slot next. Repository gates and Padé synthesis remain NOT RUN; repository closeout remains PENDING.

## 7. Terminal snapshot outcome; no successor launch

The authorized snapshot slot launched under unit `spu-vgafix-verification-snapshot-20261002-01` into `campaign_01/snapshot_01/`. In the later invocation exactly one terminal marker `FAILED` was present, exit 1, duration 9 seconds, start `2026-10-02T01:20:22Z`, end `01:20:31Z`. Git clone/checkout and rsync exited 0; destination manifest validation then halted with `RuntimeError: external source symlink: .venv_plot/bin/python`. No successful snapshot identity was produced. The frozen helper remains unchanged.

The isolated checkout contains the local `.venv_plot` environment, omitted from the frozen root/rsync exclusions; its Python symlink resolves outside the checkout. The guard correctly rejected it. `checkout/build` remains a real directory; chipdb was not copied. Gates and Padé output directories are absent, and both successor jobs remain NOT RUN because their successful-snapshot prerequisite failed. Preserve the failed checkout and all command logs; do not resume, recopy, clean, or reuse this attempt. `campaign_01/snapshot_interpretation_01.json` records the exact target, terminal result, evidence hashes, and consumed slots.

The snapshot slot is consumed and its one-attempt budget exhausted. Overall repository closeout remains PENDING; the hardware programming/startup PASS and control visual HOLD in hardware evidence §3.33 are unchanged. The minimal proposed correction is to explicitly exclude the confirmed local `.venv_plot` environment in both `ROOT_EXCLUDES` and the rsync exclusions, add fixtures for that exclusion, and freeze/review the corrected helper and contract. That correction has not been implemented and this outcome authorizes no retry; obtain owner authorization for a new snapshot attempt/budget before relaunching. Do not run any regression or synthesis gate from this rejected checkout.

The owner subsequently authorized renewed work while requiring diagnosis before redesign. Preserve this original failed phase and helper unchanged. The [diagnosis](diagnosis_gpu_t1r_vgafix_and_snapshot_2026-10-02.md) establishes the incomplete environment exclusions, and the [recovery contract](contract_gpu_t1r_vgafix_repository_recovery_2026-10-02.md) freezes the corrected helper, new campaign destinations, and renewed snapshot slot with the unconsumed gate limits. Its 27 local fixtures passed; corrected-helper review is pending and no new campaign launched. This follow-up record does not change the original FAILED marker or restore its consumed slot.
