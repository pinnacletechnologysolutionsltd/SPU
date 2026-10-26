# Engineering Contract: VGAFIX Display Signal Diagnostic

**Date:** 2026-10-02  
**Contract ID:** `GPU-T1R-VGAFIX-SIGNAL-DIAGNOSTIC-2026-10-02`  
**Status:** DRAFT DEFERRED — owner prioritized bitstream diagnosis; digital diagnostic remains unexecuted and not executable  
**Owner:** John Curley  
**Spec Author / Halt-and-Flag Implementer / Integration Auditor:** Codex

The owner subsequently requested diagnosis of recent bitstreams, reporting
confidence in the signal and physical setup. Prioritize the
[offline bitstream audit](diagnosis_gpu_bitstream_integrity_2026-10-02.md).
Preserve this narrower analyzer draft for possible later use; its missing
mapping/identity/command prerequisites and execution authorization remain pending.

## 1. Read the existing evidence before defining captures

```bash
cat build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/repository_closeout_01.json
cat build/gpu/t1r_vgafix_control_20261002/control_01/hardware_result_01.json
cat build/gpu/t1r_vgafix_control_20261002/control_01/program_01/result.json
cat build/gpu/t1r_vgafix_control_20261002/control_01/startup_stat_01.stdout
sha256sum build/spu_a7_100t_VGAFIX.bit
```

Preserve repository closeout PASS for the exact frozen campaign_02 snapshot,
manifest SHA-256 `1044941c30d6703afe34f6871f669d116e893ef1c411102796a6719928fe736d`.
No repository rerun is indicated by the existing results. This new draft and
later evidence reports were not inputs to those gates.

Preserve programming/startup PASS and visual HOLD from
[hardware evidence §3.33](../docs/hardware_evidence.md#333--vgafix-display-control-programmingstartup-pass-visual-hold-2026-10-02).
The historical loaded VGAFIX file hash is
`a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379`.
Rehashing that file does not identify the present volatile FPGA configuration.
Before a future observation, obtain current power/configuration/setup continuity
and observer readiness. If continuity is lost or unknown, HALT this campaign;
draft a separate reload proposal rather than consuming another old load/query slot.

## 2. Objective and scoped files

Capture one full-display photograph and one original ten-second video in a
single thirty-second observation interval. Then measure digital HSYNC/VSYNC at
both ends and RGB logic on the FPGA side of the series resistors, with the
monitor connected. The owner has no oscilloscope and has a Saleae clone;
analog RGB amplitude, edge shape, and monitor-side RGB remain UNMEASURED.
Record the state before and during probe connection, endpoint, channel mapping,
settings, raw traces, and changes in display behavior.

Only this draft may be changed during preparation. Store future capture helpers
and evidence under a new `build/gpu/t1r_vgafix_signal_diagnostic_20261002/`
campaign destination. After execution, update this contract and the hardware
evidence ledger. Modify no RTL, XDC, wiring specification, generated catalog,
bitstream, or frozen verification input. No synthesis, repository gate, FPGA
programming/query, UART, reset, power-cycle, cable replacement, monitor adjustment,
or persistent flash operation belongs to this proposed diagnostic.

## 3. Resolve the physical probe map before instrument connection

```bash
sed -n '1,82p' hardware/boards/artix7/spu_a7_vga_fix.xdc
sed -n '21,65p' docs/SPIpinout.txt
```

Use these recorded signal identities as historical context:

| Signal | FPGA package pad | Monitor DE-15 contact | Harness context |
|---|---|---:|---|
| Red | G8 | 1 | Series RGB resistor |
| Green | G7 | 2 | Series RGB resistor |
| Blue | G5 | 3 | Series RGB resistor |
| HSYNC | D5 | 13 | Direct signal conductor |
| VSYNC | E5 | 14 | Direct signal conductor |
| Returns | Board ground | RGB 6/7/8; sync 10 | Identify actual connected return points |

HALT probe placement from J10 numbering alone. The XDC's early comment calls
top-row hole 1 D5, while its later table calls J10 pin 1 G8. The recorded
package-pad-to-DE-15 signal identities agree; current physical contact identity
has not been independently established here. Freeze an annotated photograph or
equivalent physical map identifying orientation, each accessible contact, each
resistor side, and ground before execution review. Do not silently correct the
XDC or treat an uncertain hole number as a verified probe point.

If contact identification requires disconnecting the monitor, power removal,
continuity testing, or insertion of a breakout adapter, HALT and amend the setup
and continuity contract before authorizing that operation. The current draft
does not authorize continuity testing on a powered circuit.

## 4. Saleae-clone acquisition prerequisites

```bash
lsusb
sigrok-cli --version
sed -n '553,597p' spu_strategy/contract_gpu_prepared_scene_t1d_repeatability_diagnostic_2026-09-20.md
```

The historical bench device is USB `0925:3881`, Saleae Logic-compatible,
eight-channel `fx2lafw`; its recorded stack uses
`/usr/share/sigrok-firmware/fx2lafw-saleae-logic.fw`. The current USB listing
does not include that device. Do not reuse historical bus/device numbers or
assume the owner's clone is that same device. The sandbox invocation of
`sigrok-cli --version` reported `libusb_init() returned LIBUSB_ERROR_OTHER`;
the host invocation succeeded with sigrok-cli 0.7.2, runtime libsigrok
0.5.2-git-9ffa3638, and libusb 1.0.30.12037. Use the host namespace for the
eventual instrument workflow. Version output does not qualify actual acquisition.
Resolve current host/device identity before finalizing capture commands.

The historical driver produced truncated multi-million-sample records despite
exit zero. Use bounded sample requests and validate actual raw sample count,
sample rate, channel packing, enabled channels, and absence of capture errors.
Do not infer adequate record length from requested samples or displayed duration.
Preserve an undersized acquisition as infrastructure HOLD; no silent retry.

Freeze model/identity, current USB connection, firmware, software versions,
lead mapping, input compatibility, fixed/adjustable digital threshold, ground,
and actual monitor load. A digital trace establishes threshold crossings only.
Keep the monitor connected and probe RGB before its series resistors. Exclude
monitor-side analog RGB from the analyzer connection plan; those traces would
not establish analog signal quality. No oscilloscope purchase is a prerequisite
for this narrower diagnostic.

Freeze channels as D0=HSYNC, D1=VSYNC, D2=R, D3=G, D4=B at the FPGA-side
capture; D0=HSYNC and D1=VSYNC at the monitor-side capture. Physical endpoints
and return attachment remain pending §3 confirmation. The unused analyzer
inputs are excluded from interpretation. Preserve display behavior before and
during lead connection. Do not disconnect or modify the harness to obtain access
without an explicit contract amendment.

Replace this draft's pending execution section with exact `sigrok-cli` arguments
using the observed connection and reviewed recording/validation helper before
execution review. An unconnected analyzer does not justify inventing a device
path, running a generic discovery/acquisition workaround, or using a stale
connection. No capture helper or acquisition was executed during preparation.

## 5. Proposed bounded digital sequence — not yet authorized

| Operation | Proposed maximum | Required evidence |
|---|---:|---|
| Continuity/setup/readiness preflight | 1 | Current operator report, instrument settings, annotated probe map |
| Unprobed display observation | 1 × 30 seconds | One original full-display photo and one original 10-second video |
| FPGA-side digital acquisition | 1 × 1,200,000 samples at 24 MHz | D0–D4: sync and pre-resistor RGB on one time reference |
| Monitor-side digital sync acquisition | 1 × 1,200,000 samples at 24 MHz | D0–D1: sync; RGB analog UNMEASURED |

Each proposed record is nominally 50 milliseconds: it spans multiple lines and
about three frame periods. The 24 MHz sampling does not resolve each 25 MHz
pixel-clock cycle; interpret line/frame timing and the much longer bar intervals,
not pixel-clock integrity or narrow glitches. Require the full requested sample
count and at least two complete VSYNC intervals; insufficient edge coverage is
INCONCLUSIVE even when the sample-count guard passes.

Propose one acquisition per endpoint, a thirty-second external wall-clock limit
per acquisition, sixty seconds for one preflight, one thirty-second observation,
and a maximum fifteen-minute interactive campaign including lead placement and
export. Freeze these limits and exact timeout/abort/export behavior in the
instrument-specific executable revision. Display and instrument operations
remain NOT RUN. No attempt or cumulative budget is authorized by this draft.
Each acquisition consumes its slot at launch, including failure, timeout,
invalid data, or unavailable export. No automatic retries or streaming substitutes.

Measure digital sync periods, active-low pulse widths, and stability. Compare
pre-resistor RGB bar intervals and blanking relative to sync. Identify
marker-contaminated lines instead of treating their red signal as a bar-pattern
failure. Capture records must resolve the events being reported; insufficient
resolution is INCONCLUSIVE. Voltage, rise/fall time, ringing, and monitor-side
RGB are UNMEASURED with this equipment.
Record display changes caused by probing as a load-sensitive observation; do
not equate sequential endpoint captures with simultaneous transmission evidence.

Use managed foreground execution for interactive hardware operations. A future
deterministic analysis job expected to exceed sixty seconds requires its own
new detached-runner destination and frozen timeout; no such job is authorized
or necessary to draft this contract.

## 6. Source-derived expectations and independent classifications

```bash
cat hardware/boards/artix7/spu_a7_vga_top.v
cat hardware/rtl/gpu/spu_video_timing.v
cat hardware/rtl/gpu/spu_video_pattern.v
cat hardware/rtl/hal/hal_vga.v
```

Use the archived source context, not the unrelated Padé timing, for expectations:
25 MHz pixel clock; 800 pixels per line; 525 lines per frame; HSYNC period
32 microseconds (31.25 kHz), low width 3.84 microseconds; VSYNC period
16.8 milliseconds (about 59.524 Hz), low width 64 microseconds. Active area is
640 × 480; eight eighty-pixel bars are white/yellow/cyan/green/magenta/red/blue/black,
with a moving red marker. These are source-derived values, currently unmeasured;
the source files are context rather than a fresh source-to-bitstream proof.
Propose nominal digital acceptance ranges: HSYNC period 32 microseconds ±1%,
low width 3.84 ±0.15 microseconds; VSYNC period 16.8 milliseconds ±1%, low width
64 microseconds ±1 microsecond. Require active-low sync and repeating line/frame
structure. These are diagnostic comparison ranges, not calibrated frequency
accuracy claims. Record unknown analyzer clock/threshold uncertainty explicitly.
Confirm the ranges during instrument review before freezing execution.
Report measured numbers even when classification is HOLD.

| Observation | Permitted interpretation |
|---|---|
| Missing/incorrect FPGA-side digital sync or RGB pattern | Source-end digital output HOLD; internal clock/reset/configuration cause remains unresolved |
| Consistent source sync; monitor-end digital sync deviation | Downstream sync path or measurement-loading interaction supported; no specific conductor fault established |
| Expected digital sync at both ends and source RGB; corrupt display | Display HOLD persists; analog RGB, monitor behavior, and unsampled events remain unresolved |
| Probe connection changes the pattern | Load-sensitive interaction observed; preserve settings and before/during reports |
| Inadequate media, uncertain mapping, missing traces, or insufficient resolution | INCONCLUSIVE for the affected dimension |

Report visual, source-side digital sync/RGB, monitor-side digital sync, unmeasured
analog RGB, and provenance
independently. File hashes identify captured evidence, not current SRAM contents.
Never infer display correctness or a GPU arithmetic fault from repository PASS.
The owner's assessment that wiring and FPGA are healthy is recorded as an
operator assessment, not a new measured exclusion of those causes. This
diagnostic tests current output behavior without assigning a physical fault.

## 7. Evidence review and stop conditions

Preserve original photo/video, raw waveform exports, instrument settings,
timestamps, operator association/continuity reports, actual probe map, commands,
return codes, and hashes in the new campaign. Retain missing/failed acquisitions
as such; do not regenerate originals from screenshots. Cite the hardware ledger
for every new physical observation. Preserve the old exhausted control campaign.

HALT on uncertain physical mapping, unknown power/configuration continuity,
unavailable live observer, unidentified equipment, incompatible probing/loading,
missing exact capture operations/budgets, setup change outside scope, or exhausted
slot. Drafting authorization does not authorize instrument connection or capture.
Finish the instrument-specific revision and implementation review before asking
the owner to authorize a concrete bounded hardware sequence. The existing
repository closeout remains PASS for its original frozen snapshot; this diagnostic
and any later source changes require their own stated verification scope.
