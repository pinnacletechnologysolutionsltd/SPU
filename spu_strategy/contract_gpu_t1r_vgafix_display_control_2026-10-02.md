# Engineering Contract: T1r VGAFIX Display-Path Control

**Date:** 2026-10-02  
**Contract ID:** `GPU-T1R-VGAFIX-DISPLAY-CONTROL-2026-10-02`  
**Status:** HARDWARE RESULT RECORDED — programming/startup PASS; control visual HOLD by operator report; photo/video support pending; repository closeout PASS for the frozen campaign_02 snapshot  
**Owner:** John Curley  
**Spec Author / Halt-and-Flag Implementer / Integration Auditor:** Codex

## 1. Objective and scope

Load the exact historical VGAFIX color-bar artifact once into Wukong XC7A100T SRAM. Observe the same monitor and VGA harness used for the T1r photographic replay. Preserve the T1r stationary diagonal blocks, vertical blue lines, flickering snow, and state changes as the baseline in [hardware evidence §3.31–3.32](../docs/hardware_evidence.md#331--t1r-host-uart-sequence-after-reload-partial-visual-observation-2026-10-02).

Treat "Let's draft the contract" and the subsequent scope review as drafting/revision authorization only. Obtain explicit hardware-phase execution authorization for the frozen budget below, then record operator readiness and unchanged board/monitor/harness/settings before preflight. Halt if the physical configuration has changed or its continuity is uncertain; record the changed condition before revising this comparison. Hardware authorization does not authorize the separate repository-verification phase in §8.

Change only the volatile FPGA configuration during the hardware phase. Limit that campaign to preflight, one SRAM load, one STAT query, and one observation interval. Preserve source, sender, fixtures, wiring, monitor settings, power connections, and all prior evidence. Send no UART bytes. Rebuild nothing in the hardware phase. Do not write persistent flash, reset/power-cycle the board, reconnect/reset USB, or change cables. Loading VGAFIX replaces the current volatile T1r configuration; do not restore T1r under this contract. Defer D4 P1b. Allow repository tests and the mandatory Padé build only in the separately authorized, isolated verification phase defined in §8.

During the hardware phase, modify only this contract and, after execution, `docs/hardware_evidence.md`. Store execution helpers, command logs, results, photographs, and video under the new evidence directory. No RTL, port, arithmetic, or generated-file edits are included in that phase. Record separate verification outcomes in the companion contract.

## 2. Frozen identity and budget

| Item | Frozen value |
|---|---|
| Board | QMTech Wukong XC7A100T-FGG676 |
| Bitstream | `build/spu_a7_100t_VGAFIX.bit` |
| Bitstream bytes / SHA-256 | `3825920` / `a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379` |
| Historical source anchor | `bf00be07e74911755727f80adba7672dcab5668b`, recorded in hardware evidence §3.8 |
| Historical build command | `bash hardware/boards/artix7/build_a7.sh 100t vgafix all` — provenance only; DO NOT EXECUTE |
| Programmer | DirtyJTAG `1209:c0ca`, serial `CB81353DCE678119`, 1 MHz |
| FPGA detection | exactly one Xilinx `xc7a100`, IDCODE `0x03631093`, IR length 6 |
| Approved host mount namespace | `4026531832` |
| SRAM attempts / timeout / cumulative programming budget | `1` / `120 seconds` / `120 seconds` |
| Post-load read-only STAT queries / timeout | `1` / `20 seconds` |
| Operator observation | one `30-second` interval; one full-screen photo and one `10-second` video within that interval |
| Evidence root | `build/gpu/t1r_vgafix_control_20261002/control_01/` — require absent before creation |
| Programming job | child `program_01/`, unit `spu-t1r-vgafix-control-20261002-01` |

Consume the programming slot on launch for every outcome. Do not retry, extend any frozen timeout, substitute an artifact, or use another programming method. Preserve unavailable, failed, and timed-out outcomes as terminal for this attempt.

Use the historically measured FPGA-pad-to-VGA-plug mapping: G8 → red pin 1; G7 → green pin 2; G5 → blue pin 3; D5 → HSYNC pin 13; E5 → VSYNC pin 14. Treat connector-hole descriptions as historical documentation, not permission to alter wiring.

## 3. Evidence basis and pre-execution review

Require the exact bitstream hash and size in §2. Cite [hardware evidence §3.8](../docs/hardware_evidence.md#38-first-video-output--640x480-vga-on-a-monitor-2026-09-04) for the historical correct color bars and moving marker. Do not infer a current display pass from that historical result or from a successful SRAM write.

Preserve these distinct prior outcomes:

- `build/t1e_depth_arbitration_qualification_20260922/vgafix_program_attempt_01_halt.md`: transfer reached 100%, but GWE/EOS/Release Done/Done were zero; display interpretation halted.
- `build/t1e_depth_arbitration_qualification_20260922/power_cycle_vgafix_attempt_02.md`: separately authorized power-cycle recovery passed programming/startup; display observation was not performed. This does not authorize another power cycle here.

Require clean startup in §5 before judging the monitor. Do not silently relax that gate after a programming result. Treat the archived bitstream hash as artifact identity; current dirty-tree sources are not a rebuild identity. During drafting, the artifact size/hash matched §2; no new hardware checks or regression/build gates were run.

## 4. Host preflight, then one detached SRAM load

After execution authorization and operator confirmation, create the evidence root exactly once:

```bash
mkdir -p build/gpu/t1r_vgafix_control_20261002
mkdir build/gpu/t1r_vgafix_control_20261002/control_01
```

Record authorization, unchanged physical conditions, readiness, UTC timestamp, and host mount namespace in `operator_preflight.json`. Preserve complete stdout/stderr, exact commands, and exit statuses from the following checks in `preflight.txt`, using an evidence helper that does not open the UART or invoke programming:

```bash
readlink /proc/self/ns/mnt
stat -c '%s' build/spu_a7_100t_VGAFIX.bit
sha256sum build/spu_a7_100t_VGAFIX.bit
git rev-parse HEAD
git status --short
openFPGALoader -V
timeout 20s openFPGALoader --scan-usb
timeout 20s openFPGALoader -c dirtyJtag --freq 1000000 --detect -v
```

Require every command exit 0; namespace `mnt:[4026531832]`; frozen size/hash; exactly one expected programmer; and exactly one matching FPGA. Halt before programming on any mismatch. Record the live loader version and current repository revision/dirty status without presenting them as historical build provenance. Record `preflight.txt` SHA-256. Require `program_01/` absent. Recheck the frozen bitstream hash immediately before launch.

Launch once in the same approved host context:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_vgafix_control_20261002/control_01/program_01 \
  --timeout 120 --unit spu-t1r-vgafix-control-20261002-01 --notify-desktop \
  -- openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_VGAFIX.bit
```

Record the reported unit and evidence directory after `LAUNCHED`, then end the turn. Do not poll or wait in that turn. Let Linux own execution and notification. Notification delivery is not evidence of programming success.

## 5. Later programming/startup interpretation

In a later invocation, require exactly one of `COMPLETE`, `FAILED`, or `TIMEOUT` in `program_01/`. Absence means unavailable; stop without interpreting partial logs. Require `COMPLETE`, `result.json` exit 0, `Load SRAM` 100%, `isc_done 1`, `init 1`, and `done 1`. On failure or timeout, preserve the outcome and stop without display interpretation or retry.

After programming PASS, run the following read-only query once in the approved host context; preserve the exact command, timestamp, full stdout/stderr, exit status, and hashes in `startup_stat_01.*`:

```bash
timeout 20s openFPGALoader -c dirtyJtag --freq 1000000 --read-register STAT
```

Require exit 0; no CRC error; no ID error; DEC Error 0; and INIT Complete, EOS, GWE, Release Done, and Done all 1. Record raw STAT. Do not require an MMCM lock condition for this divide-by-two design. A missing/ambiguous field, nonzero exit, timeout, or incomplete startup means HALT / PROGRAMMING-STARTUP ANOMALY; do not attribute the monitor output to a running control image. No query retry or recovery is authorized.

## 6. One observation interval and classification

After startup PASS, confirm the operator is ready and power/configuration continuity remains intact. Observe the display for 30 seconds without adjusting controls or connections. Capture one whole-display photo and a 10-second video showing the marker and any flicker. Record operator-visible behavior separately from camera artifacts; preserve original media bytes, SHA-256, capture/state attribution, and any missed observation under `observation_01/`.

Require eight stable vertical bars, left to right: white, yellow, cyan, green, magenta, red, blue, black. Require an axis-aligned red marker moving downward. The marker is four rows tall and its 9-bit frame counter visits 0..511; temporary absence during rows 480..511 is expected. Record stationary diagonal blocks, blue lines, snow, tearing, roll, missing colors, or lost sync as anomalies outside this intentional marker behavior. Record any marker halo separately; a historical slight halo does not authorize accepting constantly flickering snow.

| Observed outcome | Required interpretation |
|---|---|
| Stable correct bars, moving marker, no reported snow or diagonal repetition | Control visual PASS for this low-resource image on this setup; supports a T1r-dependent fault or load-sensitive interaction. Does not prove GPU arithmetic faulty or clear the harness under every load. |
| Clean startup, but repeated blocks, snow, wrong colors, or unstable/lost sync persist | Control visual HOLD; a comparable fault occurs without the GPU/UART scene path. Leave FPGA output/configuration behavior, electrical harness, power, and monitor causes unresolved. Do not declare wiring faulty. |
| Observation missed, media/state uncertain, or marker liveness unobserved | Control visibility inconclusive; do not retry under this contract. |
| Programming/startup gate fails | Programming/startup HALT; control display result unavailable. |

Record programming, startup/interface checks, operator visibility, photographic support, and interpretation separately. Physical pixel equality, current scope/logic-analyzer timing, cross-build/device reproducibility, and GPU correctness remain NOT MEASURED. Reuse historical simulation/route evidence only as historical evidence. Authorize no new synthesis or simulation within the hardware campaign; apply the separate verification-phase boundary in §8.

## 7. Hardware reporting and stop conditions

Update this contract and `docs/hardware_evidence.md` with the exact bitstream hash, commands, terminal marker/result, log/media hashes, operator report, classification, and limits. Report that hardware result immediately after interpretation, independently of repository verification. Cite the new ledger entry for any current hardware claim. Report **hardware outcome recorded; repository closeout PENDING** until the separate phase in §8 passes. Do not withhold or reclassify the physical observation merely because repository gates are unrun, failed, or timed out; report those dimensions separately.

Preserve all T1r evidence and report its SRAM configuration as replaced only after the new load outcome establishes that replacement; after a failed load, treat active configuration as unknown. Stop hardware work after the single control outcome. Hardware-phase completion cannot authorize verification, restoration, UART replay, wiring changes, monitor adjustment, instrumented capture, or additional diagnosis.

## 8. Separate repository-verification phase

Execute the mandatory `AGENTS.md` gates only under the [companion verification contract](contract_gpu_t1r_vgafix_repository_verification_2026-10-02.md), after explicit authorization for its frozen budget. Keep this phase outside the hardware campaign. Use a source snapshot in an independent checkout under `build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/checkout/`; place all test and synthesis outputs in that checkout's own `build/`. Do not overwrite primary-repository artifacts, program hardware, or load the verification-produced Padé bitstream.

| Verification operation | Maximum attempts | Per-attempt timeout | Maximum budget |
|---|---:|---:|---:|
| Isolated snapshot preparation | 1 | 300 seconds | 300 seconds |
| Repository regression, scoped triage, trace and math gates | 1 | 3600 seconds | 3600 seconds |
| Mandatory Padé synthesis/place-and-route/pack | 1 | 1800 seconds | 1800 seconds |
| Entire verification phase | 3 total job launches | Frozen bounds above | 5700 seconds |

Run the jobs sequentially, through the detached runner, and only after the prior job passes. Consume a slot on launch regardless of outcome. Record the unit/evidence path and end the turn after each launch. No retry, longer timeout, alternative build, or larger budget is authorized by a pass/failure/timeout or by this review.

Leave repository closeout PENDING until all mandatory commands pass for the identified snapshot. A failed gate, timeout, unavailable result, snapshot mismatch, or exhausted budget leaves closeout PENDING with that reason recorded. Preserve the independently reported hardware outcome. Do not commit or declare overall engineering completion while closeout is pending.

If a prerequisite/spec defect is found, halt and record the minimal correction before implementation.

## 9. Draft validation; execution pending

Draft checks passed: bitstream size and SHA-256; unchanged pattern/top/timing/HAL/synthesis-source bytes relative to the historical source anchor; local Markdown link targets; fenced-command formatting; absent execution destination; and `git diff --check`. `SKIP_TESTS=1 bash tools/verify_repo.sh` passed its hygiene/citation checks with regression explicitly skipped. Full regression, trace/math gates, synthesis, USB/JTAG preflight, SRAM load, STAT query, and control observation are NOT RUN for this draft. Preserve DRAFT status until execution is authorized; do not present these document checks as engineering-gate completion.

Record the supplied review as a scope review only: it identified the §7 conflict and approved the startup/observer/marker/interpretation design, but did not independently verify repository evidence or authorize execution. This revision separates hardware reporting from repository closeout and freezes the companion verification budgets and output isolation.

After implementation review PASS for the companion helper, the owner authorized its frozen verification phase, then stated "Authorized for vgafix" for this hardware phase. The owner confirmed the board, monitor, VGA harness, settings, and power configuration are unchanged since the T1r replay and the observer is ready to capture the specified photo/video. Record these statements in `operator_preflight.json`; neither phase has consumed a programming/job slot at this authorization record. Execute only the frozen commands and budget. The verification phase must still wait for the recorded hardware result and evidence updates.

Host preflight PASS at `2026-10-02T00:48:56.870233+00:00`: every command exited 0; namespace `mnt:[4026531832]`; frozen bitstream size/hash matched; loader `v1.1.0`; exactly one DirtyJTAG serial `CB81353DCE678119`; exactly one Xilinx `xc7a100`, IDCODE `0x03631093`, IR length 6. Evidence: `control_01/preflight.txt`, SHA-256 `5b07ce97f861445dbc016357109aafffb86f1ff71038ec3030838fd31eb1df29`; machine-readable `preflight_result.json`; authorization/readiness `operator_preflight.json` and host timestamp/namespace `operator_preflight_host.json`. No programming/startup/display pass is established by preflight. Launch the one programming attempt next and interpret its terminal marker only in a later invocation.

In the later continuation, the programming evidence had exactly one terminal marker, `COMPLETE`, with exit 0 and duration 31 seconds (`2026-10-02T00:49:34Z` to `00:50:05Z`). Unit `spu-t1r-vgafix-control-20261002-01`; command exactly as §4; SRAM transfer 100%; `isc_done 1`, `init 1`, `done 1`. The single programming slot is consumed. The running SRAM configuration is now VGAFIX, replacing T1r.

The single authorized read-only STAT query exited 0 in the approved host namespace. Raw STAT `0x401079fc`: no CRC/ID error, DEC Error 0, and INIT Complete/EOS/GWE/Release Done/Done all 1. Startup PASS. `programming_startup_check_01.json` records the independent checks and hashes; `startup_stat_01.launch.json`, `.result.json`, `.stdout`, and `.stderr` preserve exact command, timestamps, result, and raw decode. The single query is consumed. The owner confirmed continued power, unchanged setup, and readiness after startup; `observation_01/interval_start.json` records the single 30-second interval. Observation report and original photo/video are pending. No retry, reload, recovery, or additional query is authorized. Repository closeout remains PENDING.

The single observation interval ran from `2026-10-02T01:09:52.251083+00:00` to its scheduled end `01:10:22.251083+00:00`; the end cue is recorded in `observation_01/interval_end.json`. No hardware commands were issued during it. Its slot is consumed; physical observation/capture success cannot be inferred from elapsed time. Await the operator report and original media for classification, without another observation attempt.

The owner subsequently stated "Can you run that again? I didn't see it." Classify `observation_01` INCONCLUSIVE because the observer missed the interval. Treat that request as renewed authorization for exactly one additional 30-second observation of the continuously running VGAFIX display, with one full-display photo and one 10-second video, recorded under a new `observation_02/`. This narrowly supersedes the previous prohibition on another observation interval; it authorizes no further SRAM load, STAT query, UART activity, reset, power-cycle, or setup change. Require current power/setup continuity and observer readiness before cueing the repeat. Preserve all first-interval evidence and `observation_repeat_authorization_01.json`. Hardware command budgets remain exhausted; repository closeout remains PENDING until the final hardware report and evidence updates.

The owner replied "Ready." to the continuity/readiness question. Cue the repeat at `2026-10-02T01:17:02.294916+00:00`, with scheduled end `01:17:32.294916+00:00`; preserve `observation_02/interval_start.json` and `interval_end.json`. During the interval the owner reported "Nothing has changed." Preserve that literal report in `operator_report_01.json`; clarification is pending whether the earlier T1r diagonal/crosshatch pattern remains or expected VGAFIX bars are stable, and whether the red marker moves. The wait was interrupted by the report, but the original deadline was preserved and no new interval was started. No hardware commands were issued. The renewed observation slot is consumed. Do not infer a visual classification from this ambiguous statement or elapsed time; original photo/video are pending.

The owner clarified "Same diagonal/crosshatch pattern as T1r." Record **control visual HOLD** from this live operator report: a comparable crosshatch persists after clean startup of the frozen non-GPU VGAFIX image, instead of the expected bars. Preserve `observation_02/operator_report_02.json` and `hardware_result_01.json`; cite hardware evidence §3.33. Leave the shared display path and configuration behavior unresolved, including FPGA output, electrical harness, power, and monitor causes. Do not assign an arithmetic fault, wiring fault, or current blue-line/snow behavior that the clarification did not report. Photo/video support remains PENDING because original captures have not been supplied. Hardware result is recorded; no further hardware activity is authorized. The independently authorized repository-verification phase may now start with this hardware record and evidence updates included in its snapshot; repository closeout remains PENDING.

The owner subsequently reinforced the physical report with "No change.", preserved in `observation_02/operator_report_03.json`. Control visual HOLD is unchanged. The separate repository snapshot attempt then terminated FAILED, exit 1 after 9 seconds, on external `.venv_plot/bin/python`; its single preparation slot is consumed and successor regressions/synthesis were NOT RUN. See companion verification contract §7. This repository preparation failure does not reclassify the independent hardware result; repository closeout remains PENDING.

The separately authorized, implementation-reviewed recovery phase subsequently achieved repository closeout PASS: snapshot COMPLETE, full regression 238 PASS/0 FAIL, video triage 65 PASS/0 FAIL, both trace and all four math/oracle commands PASS, and mandatory isolated Padé synthesis/place-and-route/packing COMPLETE with timing PASS at 25 MHz. See [recovery contract §10](contract_gpu_t1r_vgafix_repository_recovery_2026-10-02.md#10-padé-result-and-exact-snapshot-repository-closeout) and `build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/repository_closeout_01.json`. This PASS covers only the 2851-entry frozen dirty-tree snapshot with manifest SHA-256 `1044941c30d6703afe34f6871f669d116e893ef1c411102796a6719928fe736d`; later primary evidence reports were not gate inputs. Hardware visual HOLD, pending original photo/video and unmeasured RGB/sync, and the unresolved physical diagnosis remain independent. No verification-produced bitstream was programmed, and no further hardware action is authorized here.
