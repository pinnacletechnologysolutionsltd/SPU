# T1d warm reset and vertex A/B amendment

- Status: CLOSED WITHOUT A/B; corrected operator report establishes the original-image observation was before reset.
- Attempt window: `2026-10-04T20:29:28Z` through `2026-10-04T20:34:28Z`.
- Owner authorization: latest reply "Authorized" to one fresh 300-second
  warm-reset → A → B attempt, with no image reload and no retries.
- Evidence: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_07/`.
- Frozen image, sender, packets and software predictions: §2 of
  `contract_gpu_t1d_vertex_ab_2026-10-04.md`.
- Image provenance: hardware_06 SRAM load exit 0, pinned image SHA-256
  `52d45da0743c326f1700b4efa7fa0187523ea6e456948f274e2cc276ccd7b914`;
  `ISC_DONE=1`, `INIT=1`, `DONE=1`. Keep the board powered throughout.
- Reuse completed software gates; this amendment changes no tested sender,
  packet, RTL, or synthesis input.

## 1. Frozen budget

One attempt; cumulative and per-attempt wall-clock limit 300 seconds from
the first preflight command. One physical warm reset, zero power cycles,
zero image loads, A once and B once (10 seconds maximum per send), two
post-send observation intervals (30 seconds maximum each). No alternate
ports, repeated resets, sends, or retries. Failure or expiry consumes the
attempt. Do not continue under an expired deadline.

## 2. Preflight

Run once in the host execution context outside the filesystem sandbox:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_07/preflight.py
```

Require exact DirtyJTAG VID:PID `1209:c0ca`, serial `CB81353DCE678119`,
CH340 VID:PID `1a86:7523`, `ID_SERIAL=1a86_USB_Serial`, pinned by-id
endpoint, and one FPGA IDCODE `0x03631093`. The separate programmer-access
step is `timeout 15s openFPGALoader -c dirtyJtag --freq 1000000 --detect -v`.
Stop on any nonzero exit or identity mismatch.

## 3. Single physical warm reset

With UART idle, the operator asserts the existing FPGA user-reset control
(`rst_n`, H7) continuously for at least 10 ms, releases it, and waits at
least 20 ms. This is the prior T1d warm-reset procedure. Keep power on and
preserve the loaded configuration. Record the operator's report verbatim.
Require black/unarmed display with stable monitor lock before sending A.
If the original picture remains or monitor lock fails, stop.

## 4. A then B

After the confirmed reset baseline, run A once in the host context:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_07/run_stage.py A
```

The pinned sender writes 64 bytes once, drains, and waits 100 ms. Obtain
the operator's report within one observation interval of at most 30 seconds.
Require the expected red and green triangles with stable monitor lock;
otherwise stop. After the A report is recorded, run B once:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_07/run_stage.py B
```

After drain and the sender's 100 ms wait, obtain the B report within the
30-second observation interval. Expected result: red triangle shortened
from V2 y=460 to y=240, green triangle unchanged. Record reports verbatim.

## 5. Evidence and classification

Preserve all command invocations, timestamps, exit codes, logs, transcripts,
reset and visual reports in hardware_07. The stage recorder refuses repeated
sends and checks the campaign deadline and required observation gates.
Classify A/B VISUAL PASS only if both reports match; otherwise VISUAL HOLD.
An unchanged image after reset is a specific reset/display failure, without
assigning a physical or RTL cause. Host writes and drain records establish
host transmission; they do not prove FPGA byte acceptance or exact pixels.

## 6. hardware_07 observation

Host-context identity and programmer-access preflight passed. The operator
reported: "Original image. I think the fpga is frozen, will reset."
This wording does not confirm that the authorized user reset was performed.
The operator subsequently clarified: "Before the reset, reset has been
pressed now. Ready for flashing." The original-image report therefore
provides no evidence of reset failure. The later reset report was recorded
after the campaign deadline; post-reset display and control identity remain
unconfirmed. A and B were not sent. The attempt is closed without identifying
a physical or RTL cause.
