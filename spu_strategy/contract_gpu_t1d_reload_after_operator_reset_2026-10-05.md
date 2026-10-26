# T1d SRAM reload after operator reset

- Status: monitor lock restored; renewed B diagnostic produced a visible red vertex response. Operator confirms real red/green striping with stable lock. Rendering acceptance remains unestablished; all authorized packet allowances consumed.
- Prospective recovery authorization: up to three hardware attempts, with
  iterative contract/helper corrections and host repairs permitted without
  separate approval for routine fixes. Earlier attempts remain unchanged.
- Recovery ledger: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/recovery_2026-10-05.json`.
- Evidence: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_08/`.
- Inputs and reused completed software gates: §§2 and 7 of
  `contract_gpu_t1d_vertex_ab_2026-10-04.md`. Image, sender and packet digests
  were rechecked and match. No tested software, RTL or synthesis input changed.
- Correction: hardware_07's original-image report preceded the operator
  reset; it was not a failed-reset observation. That attempt is closed.

## 1. Frozen scope and budget

At most three hardware attempts, 300 seconds each from the first physical
execution command, with a cumulative reserved budget of 900 seconds. Read-only
checks and host repairs do not start the clock or consume attempts. One SRAM
load per attempt with a 60-second limit; zero additional resets or power cycles;
A once and B once, each with a 10-second limit, only after the baseline gates.
No retries, alternate ports, timeout extensions or persistent flash writes.
Any failed command, failed visual gate or expired deadline ends the attempt.
Before another attempt, diagnose the failure, correct its cause and run focused
checks. Each physical launch consumes an attempt regardless of result. Pause
for current operator readiness before every physical attempt. Stop at three
attempts or if progress requires wiring, RTL, bitstream identity or A/B
acceptance changes. Routine helper and host-environment repairs are permitted;
serial discovery must still establish the pinned adapter identity.

Attempt 1 (hardware_08): 6 sender tests and 9 mocked recorder guard checks
PASS. Host sysfs, serial identity and programmer access checks PASS. SRAM
load exited 0 at `2026-10-04T20:40:07Z`, with 100% progress and
`ISC_DONE=1`, `INIT=1`, `DONE=1`. Deadline `2026-10-04T20:44:36Z`.
Operator post-load report: "No signal lock." Attempt 1 is closed. A and B
were not sent. Two authorized attempts remain; diagnose and correct the cause
before retrying. No physical A/B result is established.

The first evidence directory is hardware_08; subsequent attempts must have
separate new directories. Preserve the pre-amendment contract and all older
failures. Passed gates are reused only while their relevant inputs match.

## 2. Preflight and load

Run in the host execution context outside the filesystem sandbox:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_08/preflight.py
```

Require DirtyJTAG `1209:c0ca`, serial `CB81353DCE678119`, CH340 `1a86:7523`,
udev serial identity `1a86_USB_Serial`, pinned serial endpoint and exactly one
Artix-7 100T IDCODE `0x03631093`. Separately require programmer-access detect
exit 0. Record identity confirmation before running the single SRAM load:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_08/run_stage.py program
```

Require SRAM completion and `ISC_DONE=1`, `INIT=1`, `DONE=1`. Obtain the
operator's current display report. Historical black/unarmed evidence followed
a warm reset; SRAM-load success alone does not establish black/unarmed state.
Proceed only if the operator reports black with stable monitor lock. Otherwise
stop and preserve the specific display observation; do not reset again.

## 3. Gated A/B

After recording the black/locked baseline, run A once:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_08/run_stage.py A
```

Require a 64-byte write and drain transcript, then the expected red/green
triangles with monitor lock within 30 seconds. Record the report before B:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_08/run_stage.py B
```

Require the 64-byte write and drain transcript and, within 30 seconds, the red
triangle shortened to y=240 while green remains unchanged and the monitor
stays locked. Any absent or ambiguous report stops the attempt. Host write
and drain do not prove FPGA receipt. Only matching A/B observations support
A/B VISUAL PASS; all other visual results are VISUAL HOLD.

Preserve commands, timestamps, exit codes, logs, transcripts and verbatim
operator reports. The recorder refuses repeated stages, expired budgets and
missing baseline gates. No physical acceptance is claimed before observation.

## 4. Corrected power-state interpretation

The operator later reported: "I pulled the power plug and stuck it back in."
The earlier description of the reset as a physical user-reset operation is
unsupported. Timing relative to the SRAM load remains unconfirmed. Preserve
both the initial no-lock classification and this later correction. A power
cycle after SRAM programming would clear the volatile test configuration;
absence of monitor lock would then not establish failure of the loaded image.
No status query or further load runs until timing and current readiness are
clarified. Keep power on. Attempt 1 remains consumed; two attempts remain.

The actual host ELF is `/opt/oss-cad-suite/libexec/openFPGALoader`, SHA-256
`2956f63e5afbedf0747ec880e3b17c316fef311f4710d6f71bc23abea7821ed9`, matching
the previously audited loader. Its shell wrapper has a separate identity.
The known discarded transport-return-code defect does not establish that
transport failed in this attempt. No cause has been established or corrected;
no blind reload is authorized. Details are in hardware_08/recovery_diagnosis.json.

## 5. Timing resolved and read-only status amendment

The operator clarified: "Before the reload of course. I thought I mentioned
this." Power cycling preceded the latest load. Record the reset method as a
power cycle and the pre-load display report without treating it as a verified
user-reset procedure. No post-load power cycle is reported. The post-load
no-lock observation remains the failed baseline for consumed attempt 1.

Use one checked read-only bracket in a new evidence directory, reusing the
frozen native USB, protocol and sequence modules without changing their bytes:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_status_01/check_sequence.py
timeout 20s python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_status_01/read_status.py
```

The first command is offline and passed 124 falsifiable sequence checks.
Run the second command once in the verified host mount namespace with board
power maintained. The existing NativeUSB guard bounds USB operations to
18 seconds, checks every native result and byte count, pins DirtyJTAG serial,
and permits one connection without USB reset or recovery. The external cap
is 20 seconds. Record its managed command, exit and stdout/stderr alongside
the raw transport journal and status_result.json. If capped or partial,
classify unavailable/unknown and preserve the partial journal; do not retry.

Allow only the existing single-target ID scan, BYPASS/CFG_IN/CFG_OUT IRs and
the five-word STAT-read request. Do not issue JPROGRAM, JSTART, RCRC,
ISC_ENABLE, SHUTDOWN, frame-data writes, board resets, reloads, flash or UART.
TAP state transitions are part of the read operation. This diagnosis consumes
no load/A/B slot under the prospective recovery authorization. Shared status
agreement is a status observation; it does not establish frame delivery,
clock liveness or monitor acceptance. No automatic reload follows.

## 6. Read-only helper identity correction

read_only_status_01 stopped before STAT: raw IDCODE `0x13631093` with one
32-bit target and the expected all-ones shifted tail was rejected by its
revision-less equality check. Every issued USB transfer returned complete
checked counts. The retained loader source `jtag.v1.1.0.cpp:283` masks
`tmp & 0x0fffffff` for device lookup. This identifies a helper guard defect,
without identifying the monitor-lock failure.

Preserve read_only_status_01. In new read_only_status_02, require normalized
ID `0x03631093`, pin the observed revision nibble to 1, and record the raw
ID. The only production change is that identity guard/logging; the mock
target changes to version 1. Bitstream, RTL, wiring and A/B criteria are
unchanged. 124 sequence checks, 4 entrypoint checks and 3 wrong-identity
controls pass offline. The native USB and wire modules remain byte-identical.

Run one corrected read-only query with the same 20-second cap and side-effect
allowlist; no configuration load/reset or UART and no hardware slot consumed:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_status_02/run_checked_status.py
```

Stop on any transfer, chain, IR or deadline error; retain partial evidence.
No load retry is implied by this helper correction.

## 7. Checked status observation

Corrected read_only_status_02 completed at `2026-10-04T20:48:53Z`, exit 0.
Raw IR before/after `0x35`, STAT `0x401079fc`; shared DONE/INIT flags agree
and startup flags report complete. 79 native bulk transfers are checked in
the journal. No payload identity, clock liveness or VGA acceptance follows
from these samples. Operator still reports no monitor signal. No second
load or UART sequence ran. Record the physical observation in hardware
ledger §3.35. Two recovery load/A/B slots remain; no blind retry is permitted.

## 8. Scope stop before signal measurement

The operator confirms the monitor still reports no signal. Host sysfs USB
inventory is preserved in read_only_status_02/host_usb_devices.json; no signal
analyzer is visible. The available status samples do not isolate clock,
reset, sync-output or configuration-payload behavior. No correction supporting
another load is established. Stop before connecting measurement equipment or
changing wiring under the owner's explicit scope limit. Keep current power
and wiring unchanged. One physical attempt is consumed, two remain; no second
load, scene A or scene B has run. The recovery objective remains incomplete.

## 9. Regression diagnosis without additional wiring or loads

Latest owner request: "Diagnose the regression." Offline frame reconstruction
matches all 955864 frame words in the loaded historical image. The primary
T1d file differs only in seven header timestamp bytes; the complete 3825788-byte
configuration payload is identical. Startup control packets match VGAFIX.
Retained clock nets are input IBUF to BUFG to divider FF, then pixel BUFG;
reset H7 has a packed pull-up. No newly changed file payload explains this
historical-image failure. Live SRAM identity remains unmeasured.

Owner readiness for the next measurement: "Powered, unchanged, ready now."
Record current timestamp in read_only_pins_01/operator_readiness.json. The
entrypoint requires its age <=300 seconds and the verified host namespace.

One read-only-with-respect-to-configuration-and-pad-drive SAMPLE measurement,
using the existing JTAG wiring, is permitted as this recovery amendment:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_pins_01/run_checked_pins.py
```

Frozen bounds: one USB connection, one raw revision-1 IDCODE chain check,
three six-bit IR captures selecting BYPASS/SAMPLE/BYPASS, 32 parallel boundary
captures of 989 bits each, with 16-bit shifted markers checking register extent
and alignment. Each capture enters SHIFT_DR once and uses <=64-bit chunks.
The entrypoint caps USB operations at 18 seconds; the outer command has a
25-second limit. Partial/expired evidence is UNKNOWN; stop without retry.
Preserve managed command/exit, full raw USB journal, every decoded sample,
model provenance/hashes and pin_result.json. No hardware load slot consumed.

The allowlist is SAMPLE (0x01) and BYPASS (0x3f), plus the default IDCODE after
TAP reset. Never EXTEST, HIGHZ, JPROGRAM, JSTART, ISC_ENABLE, configuration bus
writes, UART, USB reset, board reset or load. Require DONE/INIT high and ISC
not enabled before sampling. SAMPLE fills boundary preload latches; EXTEST is
never selected, so the preload is not applied as an output-drive override.
AMD UG470 documents SAMPLE opcode and invariant scan bit ordering; it also
notes input-buffer behavior. Existing board signals use LVCMOS33.
Source: https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content.

Use the pinned vendor-authored XC7A100T FGG676 BSDL model from a public mirror;
verify its Git blob and hash, record mirror provenance, and check actual chain
extent with every marker. It is not represented as a vendor-signed download.
Mapping: clock M21/input612, reset H7/input335, UART F3/input245,
HSYNC D5/output271/input272/control270, VSYNC E5/output274/input275/control273;
RGB/diagnostic pins are also recorded. 25 sequence/alignment/fail-stop checks
and 5 entrypoint/readiness checks PASS offline. Native USB/Wire code is reused
unchanged. Frequency, electrical continuity and exact pixel acceptance cannot
be inferred from these sparse pin snapshots. A concrete pin-state discrepancy
may guide diagnosis; do not assign cause from an absent sampled edge alone.

### 9.1 Recorded SAMPLE result

The command completed at 2026-10-04T21:20:26.639739Z, exit 0. All 32
extent/alignment markers passed. Native journal has 1259 checked bulk transfers.
Capture timestamps span 5.192409431 seconds. Clock input sampled 0 and 1;
reset and UART input sampled 1 throughout. HSYNC and VSYNC pad input and
output cells sampled 0 throughout. Red and diagnostic control cells sampled 1,
where retained netlist outputs are always driven; interpretation is qualified
by the vendor BSDL's post-configuration annotation warning. No frequency or
live SRAM identity is established. Root cause remains unresolved. Evidence:
read_only_pins_01/{pin_result.json,managed_result.json,transport.jsonl,evidence_check.json}.
No load or UART was issued; one recovery attempt consumed, two remain.

## 10. Selected live I/O configuration readback

Run the offline preparation and focused checks first:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_frames_01/prepare_expected.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_frames_01/check_frames.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_frames_01/check_entrypoint.py
```

Preparation has executed once and refuses overwriting expected_io.json. The
76-bit projection covers eight static drive/pull features from the retained
historical frames, FASM and X-Ray database. FARs 0x1ca6 and 0x1ca7 are two
consecutive CLB_IO_CLK frames in the same column/row; exclude ECC and all other
bits from acceptance. Six output drive settings and reset/UART pull-ups are
covered. Retained frame reconstruction already matches the image FDRI payload.

After fresh operator readiness, run exactly one connection and one bounded
measurement command; the two planned reads are consistency observations, not
failure retries:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_frames_01/run_checked_frames.py
```

Require host namespace, pinned runtime/projection hashes and readiness age
<=300 seconds. Pin DirtyJTAG serial and raw FPGA IDCODE 0x13631093. Capture
STAT before any RCRC and CTL0; require ready startup flags, no configuration
errors, DEC/SBITS zero and GTS_USR_B one. Never alter security settings.
Read two frames twice, each 303 words including one discarded dummy frame;
preserve all raw words/USB operations. Compare only the 76 declared static bits.
Classify stable mismatches separately from unstable readback; neither outcome
alone establishes the delivery mechanism or full live image identity.

This extends the earlier read-only instruction allowlist only for this
configuration-data read. IR remains CFG_IN(5), CFG_OUT(4), BYPASS(63), plus
default IDCODE after TAP reset. Configuration control writes are limited to
CMD RCRC(7), RCFG(4), DESYNC(13), and FAR=0x1ca6. RCRC changes the checksum
accumulator; preserve pre-read STAT and do not treat post-read CRC absence as
delivery evidence. No FDRI writes, WCFG, JSHUTDOWN, GRESTORE, GCAPTURE, JSTART,
program/reset, UART, load, output override or wiring change is permitted.
No hardware load attempt consumed. Cap native operations at 18 seconds and
outer command at 25 seconds. Stop on any failure, no retry or recovery command.

Technical review: UG470 describes CFG_IN as forwarding packets to the same
configuration processor as SelectMAP, MSB-first words, and a dummy first FDRO
frame. Its full JTAG procedure uses shutdown and is not applied here. AMD's
7-series XHwIcap_DeviceReadFrame uses RCRC/RCFG/FAR/FDRO, 32 additional NOOPs,
and DESYNC without shutdown. Translating that static-frame request through
CFG_IN/CFG_OUT is an explicit interface inference, validated for serialization
by the independent bit-level TAP/packet mock; actual alignment remains an
experimental uncertainty until recorded. Static I/O bits avoid active BRAM,
RAM/SRL and captured register locations. Do not extrapolate to internal FF
capture or a full image verify. Primary references:
https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content
https://raw.githubusercontent.com/Xilinx/embeddedsw/master/XilinxProcessorIPLib/drivers/hwicap/src/xhwicap_device_read_frame.c

### 10.1 Preparation status

31 offline sequence/packet/projection/fail-stop checks and 5 entrypoint/readiness
checks PASS. Runtime and projection source hashes agree. No native USB opened
during these focused checks. read_only_frames_01 has no operator readiness or
managed launch/result yet; await the current readiness requested for this
measurement. Section 9 pin samples remain the latest physical evidence.

### 10.2 Execution result

Following current owner readiness "Powered, unchanged, ready now," the
measurement completed 2026-10-04T22:30:45.607660Z–22:30:50.121906Z, exit 0.
1091 native bulk transfers passed checked results/counts. IR before/after 0x35,
STAT before/after 0x401079fc, CTL0=0x501. Both complete 303-word reads are
identical. Both returned frame ECC values independently recompute correctly.
13 of the 76 static I/O bits mismatch the historical image: diagnostic G6 and
red G8 drive settings, and selected reset/UART pull-up bits. This correlates
with the preceding SAMPLE discrepancies; actual I/O configuration is inconsistent
with the intended image under the retained readback/alignment model. Full live
image identity and the mechanism producing the mismatch remain unresolved.

Neither two-frame signature matches any of 45 retained frame sets. Searching
the historical T1d's other retained frame addresses finds no exact alternate
alignment. Preserve this offline comparison without treating it as a complete
inventory of possible images. Evidence in read_only_frames_01:
frame_result.json, transport.jsonl, managed_result.json, evidence_check.json,
retained_io_frame_comparison.json, all_retained_frame_candidates.json and
t1d_all_frame_alignment_comparison.json. One load attempt consumed, two remain;
no further load or UART sent. Section 10.1 preparation status is historical.

## 11. Local programmer error-handling repair and build

Prepare a local DirtyJTAG2-only loader from pinned v1.1.0 commit
a33b53873be7bc8f28c0ac73bd3c88c88b27aa91; do not replace system tools.
The active prospective iterative host/helper repair authorization covers this
correction. Preserve originals and patch. No physical command is authorized by
the build below; fresh operator readiness remains required for a later load.

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/loader_repair_01/apply_repair.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/loader_repair_01/check_repair.py
tools/run_detached_job.sh --output build/gpu_evaluation/t1d_vertex_ab_2026-10-04/loader_build_job_01 --timeout 600 --notify-desktop -- python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/loader_repair_01/build_local_loader.py
```

Patch application and 25 focused source-extracted checks already PASS; never
repeat patch application. Scope is src/jtag.cpp and src/dirtyJtag.cpp only.
Known swallowed-return-code defect: data failure must throw before state
advances; TMS count mismatch or flush failure must throw. Each native USB result
and count is logged. Reject nonzero USB results, incomplete writes, invalid/empty
reads, incorrect DJTAG2 information extent/content and scan response extent.
No retries or implicit recovery on failure. Local build disables other cables
and vendor backends; DirtyJTAG's result/count conventions are explicitly pinned.
Serialization, 1 MHz requested frequency, FPGA image and A/B criteria remain
frozen for future hardware execution. The patch adds error checking, not a new
bitstream or adapter firmware. Its involvement in the historical mismatch is
unproven; this repairs an established host observability defect before retry.

One build launch, external 600-second cap; no automatic relaunch, timeout
extension or substitute build. The detached runner owns execution. Record unit
and evidence, then end the turn. Interpret only exactly one COMPLETE/FAILED/
TIMEOUT marker in a later invocation. COMPLETE requires a nonempty binary,
recorded SHA-256 and --help exit 0; --help opens no USB. A later bounded load
procedure must pin this binary and preserve transport diagnostics, checked
post-load I/O readback and operator display observations before any A/B.
Reuse completed repository/sender/scene/Padé gates for unchanged relevant inputs.

### 11.1 Detached build launch

LAUNCHED 2026-10-04T22:46:19Z; unit spu-loader_build_job_01-20261004T224619Z-132219. Evidence: build/gpu_evaluation/t1d_vertex_ab_2026-10-04/loader_build_job_01. External cap 600 seconds. No terminal result interpreted in the launching turn; no hardware command or new load slot consumed. End this turn; interpret exactly one terminal marker in a later invocation.

### 11.2 Build and executable checks

In a later invocation, exactly one COMPLETE marker and result exit 0 were
recorded; build ended 2026-10-04T22:47:25Z after 66 seconds. Local executable
SHA-256: b7a184491a7e0c8dca9676473c2507d2c047821cc4cfb72db22831c071b66f46.
Six failure controls against the actual compiled binary PASS using mocked
libusb with no physical adapter open. Evidence: loader_repair_01/
binary_focused_checks.json. Historical cause remains unproven.

## 12. Prospective corrected-loader attempt 2

Use hardware_09 as a new evidence directory. Apply the established host
error-propagation correction before this instrumented trial. This amendment
permits a trial despite the unresolved historical mismatch mechanism; it
does not assert that the host correction fixed that mechanism. The existing
iterative host/helper recovery authorization covers this procedure. Budget
remains three attempts total, 300 seconds each, 900 cumulative; one used.
No RTL, wiring, bitstream, adapter firmware or A/B criteria change.

Freeze the local executable digest in §11.2 and the original image/sender/
packet digests in hardware_09/frozen_gate.py. Require all runtime helpers to
match hardware_09/runtime_hashes.json. Retain the unchanged frame-read helper
hash manifest and 76-bit projection from §10. Reuse passed software gates
only for unchanged relevant inputs. Preserve focused checks for source (25),
actual binary failure behavior (6), recorder/preflight (20) and observation
gates. These checks open no physical USB.

Obtain current powered/unchanged operator readiness before execution, recording
the verbatim report and UTC in hardware_09/operator_readiness.json and
hardware_09/postload_io/operator_readiness.json. The latter additionally pins
measurement=two_io_frames_without_shutdown. Require readiness age <=300 s.
Run each command in the host namespace; preflight does not consume an attempt:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_09/preflight.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_09/run_stage.py program
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_09/run_stage.py readback
```

Preflight uses the actual corrected binary to detect the pinned single target
and records native USB diagnostics. The program stage reserves attempt 2
before launch, caps one SRAM load at 60 seconds, and requires exit 0, 100%
progress, ISC_DONE/INIT/DONE=1 and valid logged USB results/counts. Any failure
closes the attempt; no further stage follows. Readback immediately follows
successful programming, once, with §10's allowlist, 18-second native and
25-second external bounds. Require both planned static I/O reads stable and
all 76 selected bits matching. Mismatch, partial read or error closes the
attempt before UART. Full live image identity remains unmeasured.

After successful readback, obtain the current black/stable-monitor-lock report.
Use observe.py baseline pass '<verbatim report>' only if that criterion is met;
otherwise use baseline hold. Proceed with A, then B, only after each report
meets §3. Record reports using the following exact invocation forms:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_09/observe.py baseline pass '<verbatim black/locked report>'
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_09/run_stage.py A
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_09/observe.py A pass '<verbatim expected A/locked report>'
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_09/run_stage.py B
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_09/observe.py B pass '<verbatim shortened red/unchanged green/locked report>'
```

Substitute the actual report as a correctly shell-quoted argument. For failed
or ambiguous observations substitute hold for pass. A/B reports must be
recorded within 30 seconds of the corresponding successful command, and all
stages/reports within the frozen 300-second attempt. Missing reports cannot
authorize further commands. Close expired attempts and preserve evidence.
Only a passing B observation closes with A_B_VISUAL_PASS. No general GPU
acceptance follows. Stop after any failure and diagnose before another trial;
one additional slot would remain after attempt 2.

### 12.1 Progress-format helper correction within attempt 2

The physical program command exited 0 with 63767 valid checked USB transfers,
100.00% progress and ISC_DONE/INIT/DONE=1. Recorder incorrectly required the
literal substring 100%, recording HALT_PROGRAM_EVIDENCE_INCOMPLETE. Preserve
that original result and classification. Correct the progress parser to accept
100 or 100 followed only by decimal zeroes; reject 99.99 and 1100. The augmented
23 mocked recorder checks PASS. This is a helper defect, not a failed physical
program command. Under the prospective iterative-helper authorization, permit
reassessment of that existing successful command and continuation of the same
attempt within its original deadline, with no additional load or slot. Recheck
all logged USB and startup evidence before clearing the false stop. Freeze
the updated runtime hash and preserve the previous manifest. Only the original
deadline applies; readback and all visual gates remain mandatory.

## 13. Final authorized attempt without another load

Record the owner's post-load report verbatim: "Stable signal achieved, we're
back!" The attempt-2 deadline was 2026-10-04T23:43:17.441646Z; the report was
recorded afterward. Close attempt 2 as SIGNAL_RECOVERED_AB_NOT_RUN_DEADLINE_EXPIRED,
preserving its successful physical load, I/O match and false-parser-stop history.
No deadline extension, A/B transmission or second load occurred. Stable lock
is a report; a black/unarmed display is not yet explicitly confirmed.

Use the remaining already-authorized attempt in new directory hardware_10,
with zero loads and at most one A and one B. The owner's governing limit is
at most one load per attempt; omit a load to preserve the matching configuration.
This prospective helper amendment supersedes the earlier per-attempt load
instruction only for this final attempt. Reuse attempt 2's frozen successful
programming/readback evidence, image/sender/packet digests and unchanged-input
software gates. Require current operator confirmation of maintained power,
unchanged wiring, black display with stable lock and readiness to observe A/B.
If power or configuration has changed, stop; no automatic reload is permitted.

Freeze hardware_10's helpers and the reused hardware_09/command_results.json
in hardware_10/runtime_hashes.json. Thirteen mocked final-attempt controls PASS:
no programming stage, A-first, one A/B, observed-A gate, missing baseline,
exhausted/expired budget and failed UART stop. Observation helper is unchanged
from hardware_09's seven passing controls. Require the pinned serial adapter's
host sysfs identity before sending A. No physical execution occurs during checks.

Record current readiness and verbatim black/locked baseline before launching
A. Start the final 300-second clock on A's physical launch, with the original
900-second cumulative reserved budget and third-attempt slot; observation wait
before launch consumes no hardware slot. No more attempts are authorized.

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_10/sysfs_identity_check.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_10/run_stage.py A
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_10/observe.py A pass '<verbatim expected A/locked report>'
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_10/run_stage.py B
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_10/observe.py B pass '<verbatim shortened red/unchanged green/locked report>'
```

Run host checks/UART in the verified host namespace. A/B remain capped at
10 seconds each; operator reports must meet the unchanged §3 criteria within
30 seconds of each command. Use hold for failed/ambiguous reports. Any failure,
missing observation or deadline ends this final attempt. Record all evidence;
no additional program, reset, alternate port or physical command is permitted.

### 13.1 Sender transcript binding correction before execution

Pre-execution review found that the unchanged sender rejects transcript paths
outside hardware_01. No UART or attempt-3 launch occurred. Use hardware_10/
send_scene.py to import the unchanged frozen sender and bind only its two
transcript destinations to hardware_10/uart_a.json and uart_b.json. Packets,
digests, serial endpoint, write/drain implementation and acceptance criteria
remain unchanged. Eight offline adapter scope/preparation checks and thirteen
mocked campaign controls PASS. Freeze adapter and updated recorder digests,
preserving the prior helper manifest. Existing current operator confirmation
"Confirmed." answers the black/locked, powered/unchanged readiness question.

## 14. Withdrawn B-only proposal — corrected A baseline fails

Owner subsequently corrected the A report: "Green triangle is deformed/interlaced
into red triangle." Preserve all earlier reports. The proposal below is withdrawn;
do not authorize or execute it on the prior positive-A premise. Scene A is
VISUAL_HOLD_A_GREEN_DEFORMED_OR_INTERLACED, B remains unsent, and all three
original slots are consumed. Only offline/read-only diagnosis continues under
existing authorization; no new physical command, load or UART follows.

Scene A command exited 0 with a 64-byte write and completed drain. Operator
reported "Expected red and green triangles; stable lock." Recording occurred
33.316 seconds after the command, exceeding the frozen 30-second reporting
window. Attempt 3 closed VISUAL_HOLD_A; its B command was refused before any
serial access. All three original slots are consumed. This is a timing stop,
not a reported rendering failure. Preserve the original closure and report.

Do not transmit until the owner explicitly authorizes this prospective phase:
accept the recorded positive A observation despite its late recording; permit
one B-only completion with zero loads, resets or repeat A transmissions, a
10-second UART cap, 180-second phase cap from B launch, and 120 seconds for
the B report. Packet, image, wiring, serial identity and visual criterion stay
unchanged: shortened red to y=240, unchanged green, stable monitor lock. This
phase extends the original authorization prospectively without erasing its
three consumed slots or failures. No further retry is permitted.

After explicit authorization and confirmation the board is still powered and
unchanged, preserve hardware_10/command_results.json as the pre-completion
record, record verbatim authorization and bounds in a separate completion
authorization record and recovery ledger, and rearm only B with A's recorded
observation accepted under that new authorization. Freeze the updated helper
manifest. Set b_completion_authorized=true and a new 180-second completion
deadline; retain the original 300-second deadline separately. Existing repeat
guards prohibit another A and more than one B. Execute only:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_10/run_stage.py B
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_10/observe.py B pass '<verbatim shortened red/unchanged green/locked report>'
```

Use hold for an incorrect/ambiguous report. For this explicitly authorized
B completion alone, observe.py permits 120 seconds; all earlier report bounds
remain 30 seconds. A failed B command, failed/missing observation or expiry
ends the completion. Record the physical result in docs/hardware_evidence.md.

## 15. Single B diagnostic — renewed owner authorization recorded

Owner asks "Scene B?" B remains unsent. Prepare hardware_11_b_diagnostic as
a separate, prospective diagnostic phase; do not reopen the failed A/B campaign
or erase its consumed budget. The A baseline has malformed green geometry.
This phase can test whether the red vertex edit changes the current display;
it cannot establish the original A/B VISUAL PASS.

Require explicit renewed authorization for ONE_B_ONLY_DIAGNOSTIC and current
readiness: the same Scene A still displayed, board powered and setup unchanged.
Record the owner's exact response, UTC, scope and approved=true in
completion_authorization.json and normalized readiness with exact response
in operator_readiness.json. Freeze copied helper hashes and unchanged physical
inputs. Use the same pinned sender/packets and exact local transcript binding.

Permit one B transaction, zero reloads, zero resets, zero repeat A and no retry.
UART cap 10 seconds, phase cap 180 seconds from launch, observation window
120 seconds from successful command completion. No physical execution before
the renewed authorization; prior three attempt slots and failures remain.

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_11_b_diagnostic/run_b.py
```

Run in the verified host namespace. The helper checks renewed authorization,
current readiness, frozen input/runtime hashes and pinned adapter identities;
records launch before sending, consumes its sole packet slot, and refuses
repeated execution. Preserve 64-byte write/drain transcript and command result.
Record the subsequent display report verbatim: whether red shortens, whether
green changes, and whether monitor lock remains stable. Compare with the
pre-B photo. A failed command or missing/ambiguous report ends the diagnostic;
do not send again or infer FPGA receipt from host drain.

### 15.1 Renewed authorization and transmission

Owner replied "Authorized." to the combined renewed B-only authorization and
current powered/unchanged Scene A readiness question. Exact response and
normalized readiness are preserved in hardware_11_b_diagnostic. Original
three-slot campaign and failures remain unchanged. Five offline authorization/
scoped-packet preparation checks PASS; sender and packets are unchanged.

B-only command ran 2026-10-05T03:51:15.948611Z–03:51:16.129782Z, exit 0.
The transcript records 64 bytes written and completed tcdrain, with the frozen
B SHA-256. No load, reset or repeat A. Its sole packet slot is consumed. Display
observation is pending; reporting limit ends 03:53:16.129782Z, phase deadline
03:54:15.948611Z. Host write/drain alone does not establish FPGA receipt or
rendering. No automatic second transaction follows.

### 15.2 B photo result and closure

Owner supplied IMG_1816.jpeg. Red visibly shortened compared with A; green's
lower/right triangle became visible despite identical 252-bit green records.
The overlap photograph has horizontal red/green bands; ask whether these are
visible directly or only photographic. Classification:
PHOTO_RED_VERTEX_RESPONSE_GREEN_CHANGED_BANDING, original A/B acceptance
NOT ESTABLISHED. Preserve photo and hashes, operator message, mtime and later
agent review time; do not equate mtime with a measured operator timestamp.
The single diagnostic phase is closed with its packet consumed. No further
UART, load/reset, repeated A or automatic follow-up is authorized by §15.
Offline model predicts raw bank order 1 then 0 from reset; hardware bank state
is unmeasured. Keep bank/initialization/data-integrity explanations as hypotheses.

### 15.3 Direct display confirmation

Owner confirms "Stripes visible on monitor; stable lock." Record the actual
display artifact and maintained lock. Classification:
RED_VERTEX_RESPONSE_WITH_REAL_STRIPING_STABLE_LOCK. Physical vertex response
is established by the paired photos, but correct rendering and original A/B
acceptance are not. No further transaction is authorized by this phase.
Potential controlled next diagnostic is identical A twice without reload,
comparing output across model-predicted alternate banks; this remains an
unexecuted proposal requiring a separate bounded authorization and readiness.

## 16. Renewed identical-packet comparisons and iterative repairs

Owner authorizes "Authorized. Multiple attempts and repairs authorized." and
selects "Up to two comparisons; board powered, unchanged and ready." Record
both verbatim in hardware_12_identical_pairs/authorization.json. Permit routine
contract/helper/host corrections without separate approvals; validate corrections
with focused controls. Reuse unchanged-input completed software gates. Preserve
all previous campaigns, budgets, terminal results, reports and authorizations.

Frozen budget: at most two comparisons, at most two packets per comparison,
360 seconds per comparison, 720 cumulative reserved seconds. Each UART command
is capped at 10 seconds; each observation window is 120 seconds from successful
command completion. Failed launched commands consume a slot. Read-only preflight
and host repairs do not consume packet slots. No reload, reset, power cycle,
wiring, RTL, bitstream identity, sender/packet changes or retries beyond this
budget. Current readiness is required before a comparison's first launch.
Record full commands, timestamps, exits, write/drain transcripts and reports.

Freeze helpers and authorization in hardware_12_identical_pairs/runtime_hashes.json;
the original loader/image/sender/packet digests remain pinned. Thirty-one mocked
campaign and sender-binding controls PASS without physical USB. Actual serial
preflight checks host namespace, sysfs USB IDs/DirtyJTAG serial, CH340 by-id
udev identity, resolved serial endpoint and permissions. No programmer operation.

First comparison sends the exact same frozen A packet twice, with observation
between them. Execute in the verified host namespace:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/run_packet.py 1 1 A
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/record_report.py 1 1 STRIPED '<verbatim report>'
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/run_packet.py 1 2 A
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/record_report.py 1 2 STRIPED '<verbatim report>'
```

Replace STRIPED with the actual observed category: EXPECTED, GREEN_MISSING,
STRIPED, OTHER_LOCKED or SIGNAL_LOST. These are diagnostic descriptions, not
acceptance criteria. Stable wrong geometry/striping is a useful observation
and permits the second identical packet. Signal loss, failed UART, expired
comparison or late/missing report stops that comparison. Preserve late evidence;
never reinterpret missing data as a passing gate. Host write/drain is not proof
of FPGA receipt. Do not infer exact image equality from matching categories.

Before comparison 2, record comparison_2_reason.json with the diagnosed reason
and chosen frozen scene A or B. A completed first comparison or a diagnosed
and corrected failure must precede it; no blind retry. Default second comparison
is identical B twice to check whether the behavior follows the scene contents
or predicted alternate banks; use identical A after a repaired first-comparison
host failure only with the cause and correction recorded. Obtain current ready
status before its first packet if the initial readiness is no longer current.

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/run_packet.py 2 1 B
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/record_report.py 2 1 STRIPED '<verbatim report>'
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/run_packet.py 2 2 B
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/record_report.py 2 2 STRIPED '<verbatim report>'
```

No fifth packet, third comparison or timeout extension is authorized. Model
bank toggles are an inference, not measured hardware state. Packet-correlated
or repeat-correlated appearance must remain an observation until bank/register
or received-data evidence isolates the mechanism. Report results in the hardware
evidence ledger; correct rendering/original A/B acceptance remains unestablished.

### 16.1 Photo-path repair and remaining comparison selection

Owner corrected photo delivery: "My bad, it's in the folder now. I put it into
the software/ folder by mistake." IMG_1817.jpeg is now in the project root.
Preserve it and its hash as late evidence without reopening comparison 1 or
extending its deadline. It shows full-height red and an upper green band,
returning to the original A fault after B. First-scene-only initialization is
therefore less consistent with the observation; bank/state or geometry-dependent
setup effects remain hypotheses, not isolated causes.

Routine prospective contract/helper repair authorization permits choosing A
for the remaining comparison on this recorded evidence, also after this photo-
delivery/reporting failure. No software code, packet or budget changes. Record
comparison_2_reason.json. Use current readiness, brief text reports inside
120 seconds, and preserve photos afterward as supplementary evidence. Execute:

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/run_packet.py 2 1 A
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/record_report.py 2 1 STRIPED '<verbatim report>'
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/run_packet.py 2 2 A
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_12_identical_pairs/record_report.py 2 2 STRIPED '<verbatim report>'
```

Replace STRIPED with the actual category as in §16. Frozen six-minute comparison
and two-minute report windows remain unchanged. No second readiness/authorization
question is needed within the comparison while its original setup remains current.
The remaining comparison allows only these two identical A packets; no retry
after its budget ends. Actual scene-bank state remains unmeasured.

## 17. Renewed current-bank and prepared-coefficient capture

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/bank_capture_01/check_capture.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/bank_capture_01/check_entrypoint.py
# Only after current powered/unchanged readiness, run once in host namespace:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/bank_capture_01/run_checked_capture.py
# Only after a durable COMPLETE/exit-0 result:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/bank_capture_01/decode_capture.py
```

Owner response to actual bank/green-coefficient measurement proposal:
"Authorized. Definitely it looks like some type of bank error, timing or
malformed vertices/descriptors." Record this as renewed authorization for
one current-state measurement only; no earlier allowance is reopened. Freeze
one connection, one GCAPTURE, 60 addressed frames each read once, 140-second
native limit and 150-second outer/cumulative limit. A launched measurement
consumes the one slot regardless of terminal result. No blind retry, further
packet, reload, shutdown, reset, wiring change or timeout extension follows.
Routine prospective helper/host corrections remain authorized.

Projection covers 1373 logical register bits: both 504-bit raw scenes, loader
selector/receive/pending/count, prepared-scene generation state and both
prepared depth triples/scale. Map retained synthesized Q drivers to retained
routed SLICE_FFX BELs, then pinned local X-Ray ZINI locations. Verify initial
locations against retained frame/FASM data; pin all projection sources.
Compare 2591 declared static FF-control bits as a partial identity/alignment
control. Exclude every captured ZINI bit from those static checks. Each FDRO
request returns exactly 202 words; discard the first 101 dummy words. FARs
are exactly projection.json's 60 addresses; reject any other packet/address.

This prospective amendment supersedes §10's GCAPTURE prohibition solely for
CMD=12 once. Preserve its earlier no-capture measurements. IR allowlist stays
CFG_IN(5), CFG_OUT(4), BYPASS(63), default IDCODE after TAP reset. CMD writes
allow RCRC(7), RCFG(4), DESYNC(13), and the single GCAPTURE(12). Register reads
allow CTL0(5), STAT(7), COR0(9); no register/security/clock-setting writes.
No FDRI, WCFG, RCAP, GRESTORE, JSHUTDOWN, JSTART, program or output overrides.
Reject encrypted/secured/readback-disabled targets, startup/error changes and
COR0.SINGLE=1 before capture. Require exact pinned adapter serial, revision-1
FPGA chain, host mount namespace, unchanged runtime/source hashes and current
readiness age <=300 seconds. Record readiness verbatim plus powered, wiring
unchanged and configuration unchanged. Preflight runs before reserving launch.

GCAPTURE stores current FF state in initial-state configuration cells; it
does not establish timing or make capture synchronous to the pixel clock.
GRESTORE after capture could restore sampled values and remains forbidden.
Startup clock may be CCLK, with capture clock availability unmeasured; record
COR0 rather than rewriting it. Decode ZINI with inversion derived from the
FASM emitter and preserve the opposite-polarity result. Validate interpretation
using static controls, complete raw-packet matches and expected derived depth
state; mismatches alone do not prove malformed data if capture/alignment is
unestablished. No full live bitstream identity or atomic cross-clock claim.
Primary references: AMD UG470 v1.17, pp.103,108,132:
https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content
and nextpnr FASM emitter (ZINI is asserted for INIT != 1):
https://github.com/openXC7/nextpnr-xilinx/blob/master/xilinx/fasm.cc

Expected both raw banks equal the frozen A payload after comparison 2, assuming
all prior commits completed. This is an inference until measured. Keep both
full raw words and both polarity decodes, per-bit differences, selector and
prepared coefficients. Compare derived depth with pinned S2 finite-width
arithmetic, not an ideal or timing oracle. No rendering acceptance follows.
Reuse passed software gates only for unchanged image/sender/packet/source inputs;
no RTL or bitstream changes, synthesis rerun or full repository completion claim.
Stop after error, timeout, incomplete readback, static-control mismatch or
ambiguous capture. Preserve all issued transport operations; no recovery
command is sent on failure. On success interpret and record evidence before
any further proposal. Operator display/lock report after the capture is useful
for checking disruption but does not replace raw-state controls.

### 17.1 Recorded terminal result

The one authorized measurement has terminal COMPLETE/exit 0, 2026-10-05
04:52:28.123108Z–04:53:59.494091Z. All 60 frames were read once and all 2591
static controls match. No additional measurement remains. Physical capture
decodes active_bank=1, bank 0 equal to A and bank 1 differing only at scene
bit 346 (green edge-1 B -480 -> -16864). That captured geometry covers only
rows 0..15. Six prepared depth coefficients mismatch predictions from the
captured descriptor; both scale values equal 33. Opposite-polarity decode,
all raw words and source hashes are preserved. Operator confirms stable
lock and unchanged image afterward. See hardware evidence §3.35.9 and
bank_capture_01/diagnosis.json. Root cause and rendering acceptance remain
unestablished. A further selected static write-path read is a proposal only;
no additional packet/load/read or timeout extension is implied.

## 18. Three-attempt diagnostic campaign authorized by owner

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_01/check_config.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_01/check_entrypoint.py
# After current readiness, run once in host namespace:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_01/run_checked.py
```

Record owner authorization verbatim: "Okay, authorize diagnosis. 3 attempts."
Freeze maximum three diagnostic attempts, 180 seconds each, 540 seconds
cumulative reserved; native USB cap 160 seconds. A launched attempt consumes
one slot regardless of terminal outcome. Preserve all earlier authorizations,
failures and consumed budgets. Hardware probes use foreground managed sessions.
Read-only host discovery/offline preparation does not consume a diagnostic slot.
Routine helper/host repairs remain authorized prospectively with focused checks.
No FPGA load, UART, reset, wiring, RTL, bitstream or acceptance-criteria change
is included. Diagnostic frame reads permit the existing pinned CFG_IN/CFG_OUT/
BYPASS and RCRC/RCFG/DESYNC sequence; later register-capture attempts may use at
most one GCAPTURE each under §17 semantics. No GRESTORE, RCAP, JSHUTDOWN, WCFG,
FDRI, register/security/clock-setting write or implicit recovery is permitted.

Attempt 1: freeze attempt_01/projection.json's 204 static bits over 13 FARs.
Read every FAR in two planned passes, 202 words each including 101 discarded
dummy words. These are consistency observations in one connection, not failure
retries. Compare only the declared static LUT INIT and slice/FF control bits.
Exclude captured ZINI, ECC and all unprojected bits. Data, enable and reset
LUT tables for bank-1 scene bit 346 are included. Require pinned source/runtime
hashes, exact adapter serial and revision-1 FPGA chain, host namespace and
healthy startup/security brackets. Stop on any transport or extent error.
Classify stable mismatches separately from unstable reads; a static MATCH
does not establish complete routing or timing. Pin the prior snapshot, defect
location and unchanged bitstream/sender/packet inputs. Reuse prior software
gates only while their relevant inputs remain unchanged.

Before physical execution, record current powered/unchanged campaign readiness
verbatim in diagnosis_campaign_01/operator_readiness.json. Require age <=300
seconds at every launch and no intervening power/configuration/wiring change.
Readiness may cover successive measurements while those conditions hold;
request renewed readiness when it expires or setup changes, without requesting
another routine diagnostic authorization. Campaign lock, per-attempt start
marker and expected slot index must prevent concurrent, duplicate or exhausted
launches. Persist terminal marker/status, raw words, native USB journal and
comparison before interpreting or preparing the next physical command.

Attempts 2 and 3 are adaptive diagnostic allowances. Record a concrete reason
and freeze each exact command, projection, helper hashes and focused checks
before launch. Select a narrower or additional state/configuration measurement
from the preceding finding; never repeat an unresolved measurement blindly.
Transport failure requires diagnosis/correction before another launch. Stop
at three slots, a 180-second limit, an unrepairable infrastructure issue, or
any requirement for load/UART/RTL/bitstream/wiring changes. Budget and timeouts
are not extended by failure. A successful diagnosis does not require spending
every slot. Record findings in the recovery ledger and hardware evidence;
GPU rendering acceptance and root-cause repair are separate, still open claims.

### 18.1 Direct-worker reservation guard before any execution

Pre-execution review found read_config.py could be called directly without
run_checked.py's budget reservation. No physical command has executed. Add
require_reserved_launch before importing/opening native USB: require the
current attempt-1 managed start record, RUNNING campaign state, exactly one
used/two remaining slots and 180 reserved seconds. Preserve the earlier
runtime manifest and freeze the corrected helper/check digests. Twenty-three
protocol/projection/stop checks and eighteen readiness/reservation controls
PASS with no native USB opened. No budget, hardware scope or acceptance change.

### 18.2 Attempt 1 MATCH; prepared attempt-2 arithmetic-state capture

Attempt 1 ran 2026-10-05T05:13:35.277122Z–05:14:16.178658Z, terminal
COMPLETE/exit 0. All 204 selected static bits match, neither pass is unstable
and all full frame reads are identical. Review is recorded; one slot used,
two remain. Immediate D/CE/reset LUT corruption is not observed. Upstream
write data/routing, physical timing and arithmetic corruption remain open.

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_02/check_capture.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_02/check_entrypoint.py
# After the reviewed attempt-1 result and fresh campaign readiness:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_02/run_checked.py
# Only following terminal COMPLETE/exit 0:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_02/decode_capture.py
```

Freeze attempt_02/projection.json: 2017 logical register bits, 55 named groups,
60 FARs and 3324 selected static controls. Add shared math Sa/Sb/Sc, reciprocal
y/exp, encoded FSM state, both latched dispatcher edge/depth descriptors and
dispatcher pending/active-unit state to the earlier raw-bank/prepared-state
projection. One GCAPTURE and one pass, 202 words per FAR; no UART/load.
Preserve opposite-polarity decode and interpret with the complete raw-bank
and static controls from §17. Guard direct worker launches as in §18.1.
Reserve exactly attempt 2 (180 seconds; 360 cumulative reserved), requiring
reviewed attempt 1 and unchanged runtime hashes. Require readiness <=300 s.
The same current campaign readiness covers this measurement if it remains
fresh and setup is unchanged; no separate routine authorization is requested.
Store exact reasons and terminal review; third attempt cannot launch blindly.

### 18.3 Attempt 2 COMPLETE: captured inputs and arithmetic state

Attempt 2 ran 2026-10-05T05:17:52.969956Z–05:19:24.245768Z, terminal
COMPLETE/exit 0. All 3324 selected static controls match. All groups shared
with the earlier bank capture are unchanged: bank 0 equals A, bank 1 differs
only at bit 346 and active_bank=1. All 24 latched dispatcher descriptor
fields equal the captured raw descriptor. Reciprocal y=33346, exponent=33.
Shared Sa/Sb/Sc capture -1488384/-274968271552/-16193629184; green inputs
predict -1472000/-6641600/986240000. Six prepared depth coefficients remain
incorrect. Capture does not establish the corruption's cause or timing.

```bash
# Completed offline interpretation, not another physical command:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/analyze_second_capture.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/audit_lut_permutation.py
```

analysis.json additionally records an offline extension of the existing raw
read comparison: all 145200 bits outside database ZINI locations and word-50
ECC match retained frames. This was not a predeclared acceptance gate and
does not cover unread frames or prove FASM generation/routing/timing correct.
An apparent LUT permutation discrepancy is rejected after distinguishing
temporary SITEWIRE sink names from physical CLB input pins. The retained
target FASM matches all 32 physical truth cases; no pin-mapping cause is
established. Preserve that initial interpretation and correction in
lut_permutation_audit.json. Analysis helper initially rejected its own
incorrect field offsets before writing results or touching hardware; corrected
offsets follow spu_scene_unpack (64-bit edges, z at bit 204 plus 16*vertex).
Both physical attempts reviewed; two slots used, one remains, 360 seconds
reserved. No further authorization is required within the remaining allowance.

### 18.4 Frozen final attempt: previously unread upstream static logic

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_03/check_config.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_03/check_entrypoint.py
# After fresh powered/unchanged readiness; host namespace, once:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_03/run_checked.py
```

Freeze attempt_03/projection.json: 864 static bits, 33 FARs, two planned
passes of 202 words each. Thirty FARs were absent from attempt 2. Inspect
the malformed bank register's three immediate upstream LUTs, its counter
carry output and preceding carry slice/input LUTs, and the Sa bit-14 direct
D LUT with associated configured mux/control bits. Twenty-two mapped cells
support twelve distinct physical LUT tables. No GCAPTURE, UART or load.
Use unchanged checked transport and static packet allowlist from attempt 1.
Require hashes, exact chain/adapter, startup/security brackets, fresh readiness
and both predecessors COMPLETE/reviewed. Twenty-three protocol/projection/stop
checks and 21 readiness/reservation controls PASS without native USB opened.
Prelaunch selection failures (wrong retained carry pin name CI; corrected CIN)
do not consume physical slots. Preserve earlier results.

Reserve attempt 3 before native USB opens: used=3, remaining=0, cumulative
reserved=540, state ATTEMPT_3_RUNNING and last launch record exact. Native
160-second cap and external 180-second cap remain frozen. Compare selected
static bits only; report stable mismatch separately from unstable observations.
Static MATCH cannot establish timing, complete routing, correct emitted logic,
silicon health or rendering acceptance. At terminal result stop hardware work,
record outcome and exhausted budget; no fourth attempt or changed identity is
authorized. If readiness expires before launch, renew readiness only.

### 18.5 Final attempt recorded; readback anomaly and operator change

Attempt 3 ran 2026-10-05T05:46:39.208917Z–05:48:23.373170Z,
terminal COMPLETE/exit 0. Owner reply "Authorized." to the current readiness
request was interpreted as confirmation to proceed with the requested powered,
unchanged setup; that interpretation and the exact reply are recorded at
05:46:38.718447Z. Preserve the earlier readiness file separately.

The command completed all 66 reads and 23927 successful checked native bulk
operations, but the comparison is STATIC_READBACK_UNSTABLE, not PASS. First
pass matches every one of 864 selected bits. Thirty-one complete frames match
across passes. Second pass FAR 0x20b9f returns 101 all-ones data words and FAR
0x2141b returns 101 all-zero data words; both first-pass payloads are mixed.
These account for all 19 differing projected bits (11 FF-mux controls, eight
LUT INIT bits). Remaining 845 projected bits match both times; stable mismatches
zero. Startup STAT before/after stays 0x401079fc; no GCAPTURE, UART/load/reset
was commanded. Complete USB transfers and healthy brackets do not validate
these two payloads or establish changing configuration. Classify final
measurement INCONCLUSIVE_READBACK_DATA_ANOMALY; preserve the frozen comparison.

Owner afterward reports "Image or signal changed." Record this separately,
request the exact change and any operator intervention, and do not assume
probe noninterference. Causality is unestablished. All three physical slots
are consumed, 540 seconds reserved. Set BUDGET_EXHAUSTED_HARDWARE_STOPPED;
no further JTAG/UART/load/reset is authorized by this campaign.

Owner clarifies: "Display change is that the green is no longer overlayed
but interlaced. Green is once again truncated." Append that exact report to
operator_after_measurement.json, preserving the earlier generic report. Record
picture change without inventing current signal-lock or intervention status.
Compare qualitatively with the prior captured-state reconstruction; do not
infer a new bank selector measurement or that the probe caused the change.
Keep the hardware stop and exhausted budget unchanged.

```bash
# Completed offline result analysis, no USB:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/attempt_03/analyze_result.py
# Prospective guard checks only; original worker remains frozen:
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/readback_guard_repair_01/check_replay.py
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/readback_guard_repair_01/check_integration_replay.py
```

Pre-execution guard gap was not detected by the previous focused checks:
complete-length constant payloads were classified by comparison but did not
halt the sequence. Preserve the executed helper unchanged. Prepare a separate
prospective validate_frame guard and literal integration.patch: reject invalid
word/extent/FAR and all-zero/all-one data contradicted by declared static bits.
Persist raw candidate after DESYNC, before validation; halt before another
frame on rejection. Seventy-nine offline replay/fault-injection checks PASS;
64 recorded frames accepted, exactly two anomalous frames rejected. Integrated
recorded-command replay (six controls) stops at 0x20b9f before the later bad
frame. No native USB or extra physical attempt. This guard does not diagnose
why TDO payloads were invalid or establish physical noninterference. A further
physical campaign requires a new bounded scope and current readiness.

### 18.6 Owner overflow hypothesis reviewed against retained widths

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/audit_depth_widths.py
```

Review finite-width integer overflow before any width edit. Pin retained
synthesis SHA and frozen/captured descriptors. Retained term magnitude path
has 37 bits; Sa/Sb/Sc have 40, shared multiplier operands 40/17, full product
57 and coefficient outputs 56. Largest actual magnitude term 993600000 fits
the positive 37-bit term range; all partial sums fit signed 40 bits. Largest
expected scaled coefficient 32887159040000 fits signed 56 bits. Exact sums
and coefficients equal the finite-width Python device oracle; no term/accumulator/
output truncation for frozen A or the captured malformed descriptors.

For the documented closed screen domain, conservative |c|<=612162 gives
|c*z|<=40118036670, three-term magnitude <=120354110010 and scaled magnitude
<=7887406599505350, all within those widths. Arbitrary full-range signed
32-bit c ports are outside that sizing assumption and can truncate; no claim
of full-port-domain safety. This T1d path has no M31 modular reduction.
Ordinary specified-width overflow does not explain this scene. Transient bad
operands, physical multiplier/adder/timing faults and readback validity remain
open. No RTL, bitstream identity or acceptance change follows on this audit.

### 18.7 Halt-and-flag review of proposed reciprocal/SPI/Z validation patch

```bash
python3 -B build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_01/proposal_review_01/review_proposal.py
```

HALT proposed validator implementation: z0/z1/z2 are masked with 0xffff
before comparison to 65535, so the rejection condition is unreachable.
Offline replay of the exact recorded fault (packet byte 44 XOR 0x04, scene
bit 346, green B1 -480 -> -16864) reports packet_complete and activates the
corrupt bank under the proposed subclass. Green depths remain 700/400/3600.
Preserve that falsifiable counterexample; no model/RTL repair is applied.

Correct proposal context: physical sender is CH340 115200-baud 8N1 UART,
not RP2350 SPI; no 20us SPI guard is established. Packet is one A5 token
plus 63 payload bytes, with two 252-bit records sharing packet byte 32's
low/high nibbles. Fault byte 44 is not in the green depth fields (packet
bytes 58..63). Retained loader is indexed byte insertion; current Python
model shifts storage, with prior retained bank audit establishing byte-position
equivalence only. A Python subclass does not alter the configured FPGA.

The referenced daedef2 reciprocal RTL contains signed normalization shift,
left/right selection, mantissa[14:7] addressing, 33-bit product/error,
49-bit Newton product and y1full[46:31] extraction. For frozen/captured
descriptor denominator 257600, expected shift=2, mantissa=64400, index=247,
y=33346, exp=33. Current captured y/exp match; sums are already incorrect.
No reciprocal-only scaling or missing-shift root cause is established.
Retained synthesized unused Newton bits may be optimized away; only product
bits 31..46 feed the output, so unused-bit removal alone is not a defect.

Minimal correction: discard unreachable Z guard. General in-range corruption
detection requires independent integrity evidence, such as a specified checksum
at the selected sender/receiver boundary; range checks alone cannot ensure
integrity. Any checksum/protocol/RTL/bitstream change needs separately reviewed
scope. Keep diagnosis aimed at the failing raw bit, dot-product path and
readback validity, preserving all captures and the exhausted hardware stop.
