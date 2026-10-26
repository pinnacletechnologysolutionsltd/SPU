# Engineering Contract: Wukong GPU Baseline Recovery
**Date:** 2026-10-06  
**Contract ID:** `gpu_wukong_baseline_recovery_2026-10-06`  
**Status:** ACTIVE — historical baseline replay and scene-update recovery

## 1. Objective

Restore a physically demonstrated GPU image on the original Wukong Artix-7
100T and its VGA setup. First replay the earliest retained static GPU image.
If it works, replay the earliest retained scene-updatable image and its
original update procedure. Establish stable display output and repeatable
visible scene changes before returning later features to the build.

Acceptance is a stable expected display plus two repeatable A/B/C scene
sequences. An analyzer or diagnostic pass alone is not acceptance.

## 2. Evidence-based baseline selection

### 2.1 Static renderer/VGA control

Use the retained September 6 two-triangle depth image:

```text
artifact = build/spu_a7_100t_GPUVGA.bit
sha256   = ce5bdc70753fc88d1a6e91bc1e573dff2c40756f66e9d689f9880139285e25e2
board    = QMTech Wukong Artix-7 100T, XC7A100T-FGG676
clock    = 50 MHz oscillator; divide by two for 25 MHz pixel clock
display  = original 640x480 VGA monitor, three-resistor DAC and J10 harness
pins     = R G8, G G7, B G5, HSYNC D5, VSYNC E5; G6/J10-7 unused
expected = overlapping full-height red/green triangles; vertical depth
           boundary at screen center, ending where the triangles separate
evidence = docs/hardware_evidence.md §3.10 and the two retained photographs
```

The recorded evidence includes a second observation after a confirmed board
power cycle and physical harness reseat. The exact historical artifact is
retained. Do not rebuild or edit this image for the first replay.

### 2.2 Earliest retained repeatable scene-update control

After the static display control passes, use the September 23 T1G image. It is
the earliest retained Wukong image with a recorded visible A/B/C scene-change
sequence:

```text
artifact = build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
sha256   = e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5
source   = a64d87c7ae0d96b44d8178c20f2421376a975ac0
board    = QMTech Wukong Artix-7 100T; original VGA display setup
protocol = 127 bytes, 115200 baud, 8N1; 20 ms post-drain delay;
           >=31.1 ms start-to-start; historical run used 3 s scene dwell
sender   = build/t1f_clean_qualification_20260922/build/t1g_h1_20260923/send_sequence.py
sha256   = f3f4d8c4eabaed5e149689cd84dea25771ffbdd7cc2db9058aecc1b5f3cbee60
single   = build/t1f_clean_qualification_20260922/build/t1g_h1_20260923/send_single_scene.py
sha256   = a201a16d94f425d8cb1d6c5927b5068b5a346103180afbac2172e435afc04d9e
scene A  = fixtures/gpu_t1f_scene_wire_127b.hex; text SHA-256
           abf881178c4384f9210575aa2992c784cb6e19fcd10f149b81631e39591c8fda
scene B  = fixtures/gpu_t1f_coverage_scene_wire_127b.hex; text SHA-256
           80bb103e43e1fc06a98e1d03166a673b35ea4e70c1c2b5fd34ff2caf177fb607
scene C  = fixtures/gpu_t1g_scene_c_wire_127b.hex; text SHA-256
           5aad8b1b1954875ea78fb11192d94a19652e027aea8f33e1656ec950b50abca5
evidence = dated September 23 T1G record in docs/hardware_evidence.md;
           transcript build/t1f_clean_qualification_20260922/build/t1g_h1_20260923/uart_sequence_attempt_03.json
```

The historical operator reported both A→B and B→C changes visible. The record
also says a wrong-PMOD analyzer connection was found during troubleshooting;
correcting it restored VGA. That is a reason to preserve and verify the
original display wiring. This result is visual-only and does not establish
captured-pixel equality or internal receipt CRC. Repeat the exact A/B/C
sequence twice with 3-second inter-scene dwell; use the retained sender source
and fixtures without changing protocol or pacing. The senders write to fixed
historical transcript paths, so do not invoke their `main()` unmodified.
Prepare a small recovery wrapper that imports the exact sender source, changes
only the transcript destination to the current attempt directory, verifies the
frozen source/fixture hashes, and records each invocation separately.
Focused-check the wrapper before hardware execution.

The September 21 T1D 64-byte A/A visual repeat is retained as supporting
history, but it did not demonstrate a scene change and is not the scene-update
acceptance target for this contract.

## 3. Preserve and supersede the diagnostic campaign

Stop extending `contract_gpu_t1d_scene_b_transport_trace_2026-10-06.md`.
Preserve its draft, logs, raw captures and failures under
`build/gpu_evaluation/t1d_scene_b_transport_trace_20261006/`.
The most recent candidate-load attempt is recorded in
`attempt_03_candidate_load/`; it loaded the retained later candidate
`9563031456cec0135eccb0f16bdc9a7ab5fe88b7d07d23ab5cf46d5590166bd2`, then
observed two 64-us low pulses on J10-7 separated by about 16.8 ms. That did
not qualify an idle-high diagnostic UART and no Scene B packet was sent.
Keep this result separate from the historical display evidence.

The current bitstream is the later diagnostic candidate. The first recovery
load must restore §2.1's exact static control. Preserve the old candidate and
all failed attempts; do not delete or rewrite them.

## 4. Work authorization and allowed repairs

This contract authorizes offline source/history analysis, host USB/serial and
analyzer discovery, helper/contract corrections, evidence tooling, focused
software checks, builds, and the hardware budget in §5 without seeking
separate approval for routine repairs. Preserve each command, input hash,
output, failure and correction in durable files under `build/`.

Do not alter renderer RTL, scene semantics, constraints, board pins, clocks,
packet bytes or acceptance criteria while replaying the two frozen controls.
If either historical artifact cannot be replayed, diagnose programming,
device identity, power, clock, pin mapping, VGA harness and monitor input
before proposing renderer changes. Rebuilds are allowed only after the
unchanged retained artifact replay has been attempted and the source snapshot
is pinned. Label rebuilt images `RECONSTRUCTION`; never present them as the
historical flashed artifact.

Once §2.1 and §2.2 pass, restore their unchanged source/packet procedures.
Reintroduce later changes one at a time, with a frozen source and bitstream
hash per change. Stop at the first reproducible regression and preserve the
last passing image and the first failing image.

## 5. Frozen physical recovery budget

One attempt is one bounded physical session. The campaign is limited to:

```text
maximum attempts:                  6
maximum elapsed time per attempt:  15 minutes
maximum cumulative hardware time:  90 minutes
maximum SRAM bitstream loads:       6 total, one per attempt
maximum analyzer captures:         18 total, each <= 2 seconds or 750,000 samples
maximum UART scene sends:          36 total; T1G sends are exactly 127 bytes
maximum UART scene sends/attempt:  6
maximum FPGA resets:                3 total
maximum board power cycles:         2 total
maximum wiring changes:             2 total
```

Resets, power cycles and wiring changes are explicitly included in this
authorization, subject to the listed caps. The board remains SRAM-only:
never write configuration flash. Wiring changes are limited to the existing
J10 VGA/analyzer leads and existing USB UART/JTAG leads; do not connect a
3.3-V output to another driven signal. Record the before/after connection map.
The operator performs physical power and wiring actions; the agent may direct
them within this authorization and records each completion.

Every attempt consumes its slot when its first physical action starts,
regardless of result. Do not carry unused actions into a seventh attempt.
Before each new attempt, first state the diagnosis and specific correction;
no blind retries. Confirm current powered/wired state when it has changed or
is uncertain. No renewed approval is required for an in-budget correction.

Stop and report immediately on smoke, unusual heat, unstable supply, exposed
or unknown pin identity, repeated loss of the expected JTAG device, any need
to write flash, exhausted time/action budget, or a need to change the frozen
image, packet, RTL, pins, clocks or acceptance criteria. Do not continue
hardware work after a stop condition without a new owner contract.

## 6. Execution sequence

1. Record the current board/display/wiring state and create a new attempt
   evidence directory. Verify the retained static bitstream SHA-256 and the
   FPGA IDCODE `0x3631093`.
2. Load §2.1 unchanged to SRAM:

   ```bash
   timeout 60s openFPGALoader -c dirtyJtag --freq 1000000 \
     build/spu_a7_100t_GPUVGA.bit
   ```

   Save the complete command output, start/end time and exit status. Require
   `isc_done=1`, `init=1`, and `done=1`. Do not issue UART traffic.
3. Observe the monitor directly. Record signal lock and the static expected
   image. A failure means diagnose the display path before loading §2.2.
   Use the analyzer only for a specific discriminator (pixel clock, HSync or
   VSync) and only if it does not interrupt the monitor connection.
4. If the static control passes, verify hashes for the historical T1G image,
   both retained sender modules and all three 127-byte scene fixtures. Load
   §2.2 unchanged to SRAM. Require successful programming before sending a
   packet:

   ```bash
   sha256sum build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
   timeout 60s openFPGALoader -c dirtyJtag --freq 1000000 \
     build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
   ```

5. Send A, B, C in order at 115200 8N1 with the original 20 ms post-drain
   delay, at least 31.1 ms start-to-start and 3-second inter-scene dwell.
   Observe and record the visible state after each packet. Repeat A, B, C once
   with separate transcript paths and the same pacing. Prepare a new cycle
   directory before each run and invoke:

   ```bash
   python3 build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/run_t1g_sequence.py \
     --evidence-dir build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_NN/cycle_NN \
     --execute
   ```

   Stop at the first unexpected image or lost signal lock; diagnose before
   using a further in-budget attempt.
6. Record final acceptance, remaining budget, current loaded image, and links
   to every attempt's raw evidence. No synthesis or repository-wide regression
   gate is needed for unchanged-image replay. Run focused checks only when a
   helper or software source changes.

## 7. Acceptance and stop classification

`STATIC_BASELINE_PASS` requires the unchanged §2.1 image to load successfully,
stable monitor lock, and the expected two-triangle depth image across at least
two observations, one after a distinct load or authorized reset/power cycle.

`SCENE_UPDATE_PASS` requires successful §2.2 load and two ordered A/B/C
sequences, with stable monitor lock and the same expected visible state for A,
B and C on both passes. This is an operator-observed demonstration; do not
claim captured-pixel equality or internal CRC/activation without separate
valid evidence.

On a failed attempt, classify the first broken boundary as device/programming,
clock/reset, VGA wiring/display, UART host send, FPGA receipt/activation, or
rendered image. State which evidence supports that classification and which
boundaries remain unmeasured.

## 8. Evidence and handoff

Write one immutable record per attempt under
`build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_NN/`.
Retain command JSON, raw stdout/stderr, timestamps, artifact/source/packet
hashes, device IDs, wiring map, operator readiness and observation reports,
captures, decoded data and classification. Never overwrite a failed attempt.
The prior analyzer campaign is archived by reference in §3; it is not a
qualification prerequisite for restoring the known image.
