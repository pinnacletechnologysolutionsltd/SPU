# GPU-G1C — Frozen T1G physical measurement readiness

**Disposition: HOLD.** Read-only feasibility assessment, 2026-10-19. No
instrument interrogation, board operation, connection, capture, flashing,
build, UART or routing. The analyzer stop remains active. No measurement
contract is proposed because technical readiness is not established.
CPU I4 and exhausted campaigns are untouched.

## Frozen target and physical signals

Use the [GPU-G1B findings](../research/gpu_g1b/FINDINGS.md) and its saved
[result](../build/gpu_evaluation/gpu_g1b_20261019_01/result.json),
[samples](../build/gpu_evaluation/gpu_g1b_20261019_01/samples.json) and
[identities](../build/gpu_evaluation/gpu_g1b_20261019_01/input_identities.json).
The three saved output hashes match the result record on read-only recheck.
No reference regeneration or qualification retry was performed. Preserve
the T1G image `e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5`
and A/B wire identities; preparation remains governed by the
[GPU-G1 plan](GPU_G1_EXECUTION_PLAN_2026-10-19.md).

Five simultaneous digital signals are sufficient in principle for sync-based
RGB111 reconstruction; a source-synchronous method would additionally need
an independently established pixel-clock reference. The frozen wrapper
does not expose a pixel-clock output. This table identifies signals, **not
permission to connect probes**:

| Signal | Retained FPGA pin / documented header | Role |
|---|---|---|
| Red MSB | G8 / J10-1 | Digital RGB111 red, before the resistor DAC |
| Green MSB | G7 / J10-2 | Digital RGB111 green |
| Blue MSB | G5 / J10-3 | Digital RGB111 blue |
| HSYNC | D5 / J10-4 | Active-low line timing |
| VSYNC | E5 / J10-10 | Active-low frame/row origin |
| Reference ground | Documented J10-5 or J10-11 | Instrument reference; actual connection remains unverified |

The retained [XDC](../build/t1f_clean_qualification_20260922/hardware/boards/artix7/spu_a7_gpu_vga_t1d.xdc)
and [wrapper](../build/t1f_clean_qualification_20260922/hardware/boards/artix7/spu_a7_gpu_vga_top.v)
bind the FPGA signals; historical header evidence is in the
[ghost-line record](contract_gpu_t1h_ghost_vertex_line_2026-09-23.md)
and [bring-up runbook](../docs/GPU_BRINGUP_RUNBOOK.md).
J10-7/G6 is unused in the frozen T1G image, not a clock or activation output.
J10-6/12 are documented power pins. GPIO-level sampling before the DAC and
analog sampling at VGA color pins are different measurements; digital input
thresholds cannot be assumed valid on the attenuated VGA signal.

## Alignment, timing and acquisition requirements

Nominal source timing: 25 MHz, **40 ns/pixel**, 800 clocks/line (**32 μs**),
525 lines/frame (**16.8 ms**). Active raster is 640×480. HSYNC is low at
x=656..751; VSYNC at y=490..491. G1B defines coordinates at the pre-edge timing
counter, with RGB and one-register-delayed sync representing that sample after
settling; the post-edge counter is one position ahead. This is source-derived
alignment, not measured FPGA pin timing or a fresh RTL timing-trace result.

| Target | A RGB111 | B RGB111 | Offset from output frame sample (0,0) | Nominal offset from preceding VSYNC falling edge |
|---|---|---|---:|---:|
| Discriminator (40,30) | (1,0,0) | (0,0,0) | 961.600 μs | 2081.600 μs |
| Interior (15,15) | (1,0,0) | (1,0,0) | 480.600 μs | 1600.600 μs |
| Background (0,0) | (0,0,0) | (0,0,0) | 0 | 1120.000 μs |

Offsets identify pixel-slot starts, not safe sampling instants. Relative to the
preceding line's HSYNC falling edge, the slot starts are respectively 7.360,
6.360 and 5.760 μs later. VSYNC establishes row identity; HSYNC alone repeats
every line. Count rows and reconstruct horizontal phase from captured sync,
not a host sleep or nominal time since UART transmission.

A's discriminator ties lanes 0/1: lower ID gives red. The independent affine
rules give green at adjacent (41,30), so one-pixel horizontal ambiguity is
material. Averaging over a red region or recognizing the whole image does
not establish the nominated pixel. B and the two controls are not substitutes
for precise phase alignment at A's discriminator.

An acceptable method must establish simultaneous-channel sampling, trigger
arming and position, valid HSYNC/VSYNC counts, timebase error, interchannel
skew, threshold uncertainty, output settling and a sample lying inside the
correct 40 ns slot with a positive measured timing margin. A nominal
samplerate alone proves none of these. At 24 MS/s the 41.667 ns sample spacing
can miss an entire pixel. At a declared 48 MS/s the spacing is 20.833 ns;
this may support a qualified asynchronous reconstruction, but does not by
itself prove which sample belongs to the pixel or its stable level. There is
no established external-clock or calibrated phase-recovery path here.

For a VSYNC-triggered contiguous capture covering all three slots, retain at
least 2.081640 ms through the discriminator's end, plus trigger/settling guard.
That is at least 99,919 sample instants at 48 MS/s or 49,960 at 24 MS/s
(nominal arithmetic, before guard). A full frame is 806,400 or 403,200 samples.
With the saved device's one-byte sample format, continuous raw transfer would
be 48 or 24 MB/s respectively, before overhead. These are requirements, not
established host/device throughput. A correctly qualified delayed/line-count
trigger could reduce storage; its availability has not been established.

## Established equipment and uncertainty

| Resource | Existing evidence | Readiness limit |
|---|---|---|
| Eight-channel FX2/fx2lafw analyzer | Listed as owned in [bench BOM §1](../docs/BENCH_BOM.md); historical sync/duty measurements in [ledger §3.8](../docs/hardware_evidence.md). Saved T1H capture metadata declares 48 MHz, unitsize=1, D0–D3 | Hardware model/serial, input threshold/capacitance/bandwidth, all-channel rate accuracy, trigger support and complete acquisition are not qualified for this task |
| Saved RGB/HSYNC acquisition | Requested 1,000,000 samples; only 10,240 bytes/samples retained (213.333 μs), no VSYNC. Read-only archive inspection confirms metadata and hash `41f35997cbf7882d467643bf6df3f87d6aebaf500ba03b1f379bab3a257177bb` | Blank fragment missed geometry. Cannot reconstruct the required frame origin or demonstrate reliable capture length |
| Existing segmented T1d tool | [Capture script](../tools/capture_gpu_t1d_diag_segments.py) requests 24 MHz, D0 only, twelve separate segments | Diagnostic-UART capture, not five-channel RGB/sync; gaps between segments and no proven pixel trigger. Do not run or adapt it by assumption |
| Monitor/camera | Existing visual switching and photographs | Analog sampling/scaling/exposure and camera/display mapping are not bit-exact raster evidence |
| Oscilloscope or other capture device | No owned, qualified instrument identified in the reviewed equipment records; EE handoff's scope/test-point text is a design proposal | Availability/specification/calibration not established. Installed FX2 firmware names are not evidence of additional owned instruments |
| Probe/harness interface | Frozen working VGA harness and historical pin map exist | No input-loading/settling/skew qualification for an added probe; “passive” cannot be asserted to have zero effect. Preserve existing monitor/harness and determine admissible loading before a future connection |

Historical frequency measurements establish useful low-frequency timing, not
single-pixel phase or a stable sampling aperture for the current frozen GPU.
No published maximum sample rate is inferred from a requested rate or firmware
filename. No new equipment availability was inferred from device enumeration;
none was performed.

## HOLD and smallest missing capability

**Missing:** an established, low-loading, five-signal RGB/HSYNC/VSYNC acquisition
path with complete frame-referenced data and demonstrated subpixel phase/level
uncertainty adequate to assign the (40,30) slot. This could be a qualified
buffered/triggered asynchronous instrument or a source-synchronous sampling
path, but neither is established with the documented equipment and frozen
connections. A higher advertised sample rate alone is not the missing proof.

The smallest next readiness input is the exact instrument model and documented
simultaneous rate, acquisition depth/trigger behavior, timebase/skew accuracy
and input-loading/threshold specifications for such a method. No purchase,
replacement instrument, diagnostic image or probe connection is requested by
this assessment. Without that evidence, do not issue a speculative capture
command or reopen the underfilled FX2 attempt.

The [September 23 owner stop](contract_gpu_t1h_ghost_vertex_line_2026-09-23.md#7-q3--classification-and-h1-gate)
explicitly ended further logic-analyzer captures; the later runbook preserves
it. Technical feasibility and authorization are separate: even if equipment
evidence later clears readiness, physical execution requires explicit resolution
of that stop and a separately authorized exact method, wiring, commands,
attempt/time budget, stop criteria and frozen-image rollback scope. No such
authorization is implied here. G1B remains software PASS; physical pixel and
internal receipt/activation claims remain NOT MEASURED. Simulator integration
or independently authorized QSG-3 research need not wait on this HOLD.
