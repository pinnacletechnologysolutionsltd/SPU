# Engineering Contract: T1d Vertex A/B Control on Historical Image

- **Date:** 2026-10-04
- **Contract ID:** `GPU-T1D-VERTEX-AB-2026-10-04`
- **Status:** `HALT — hardware_06 SRAM load reported PASS; campaign expired before A/B; operator later reported unchanged original image`
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Codex
- **Integration Auditor:** contract evidence review

## 0. Pre-execution review and limits

The baseline T1d transaction is pinned to the existing 64-byte fixture. S1's
independent compiler produces the same bytes. Scene B changes only triangle
0's V2 y-coordinate from 460 to 240; the exact CPU preview changes sample
`(100,300)` from triangle 0 red to background. The packet remains a valid
64-byte T1d transaction.

The historical T1d diagnostic image below displayed the baseline scene in the
2026-09-21 visual-only observation. It is used here as a known control image;
it is not built from the current dirty RTL tree. A pass will show that the
historical T1d path visibly responds to this vertex change. It will not
identify a regression in the current RTL or establish UART byte acceptance.

The 2026-09-21 visual contract prohibits reprogramming under that contract;
the 2026-10-02 T1r/VGAFIX hardware slots are consumed. This is a separate,
proposed one-campaign contract. No hardware command is authorized until the
owner explicitly authorizes the frozen hardware phase in §6.

## 1. Objective and scope

On the Wukong Artix-7 100T, perform one visible A/B scene replacement using
the historical T1d diagnostic image:

1. Load the pinned image once into FPGA SRAM.
2. Send baseline packet A once and observe the known dual-triangle image.
3. Send edited-vertex packet B once and observe triangle 0 shortened to
   `y=240`, while triangle 1 still extends to `y=460`.

Use the same board, VGA cable, monitor input, resolution, refresh mode, and
lighting for both observations. A photograph is not required. Record the
operator's A and B visual reports verbatim.

Target files for the software preparation phase:

```text
examples/gpu/t1d_two_triangle_vertex_b.json
tools/send_gpu_t1d_vertex_ab.py
software/tests/test_gpu_t1d_vertex_ab_sender.py
spu_strategy/contract_gpu_t1d_vertex_ab_2026-10-04.md
```

Do not modify RTL, constraints, frozen fixtures, existing UART tools, or
historical evidence. The sender helper must select only A or B, verify the
corresponding packet's frozen SHA-256 before opening the port, write one
64-byte transaction once, call `tcdrain`, and write a transcript. It must
accept only the frozen by-id port, refuse an existing transcript path, and
not retry or send any other packet.

## 2. Frozen software inputs and predictions

| Input | Path | SHA-256 |
|---|---|---|
| Historical T1d diagnostic image | `build/d3_physical_diag_20260921/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit` | `52d45da0743c326f1700b4efa7fa0187523ea6e456948f274e2cc276ccd7b914` |
| Scene A input | `examples/gpu/t1d_two_triangle.json` | `fbe44dd9f21e05a51e544ef88c0cee47c060fd36b7eeb309e38b846bab0566ef` |
| Scene A packet | `build/gpu_evaluation/s1_t1d_scene_20261004/run_01/scene_packet.bin` | `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` |
| Scene B input | `examples/gpu/t1d_two_triangle_vertex_b.json` | `f0b6be3ccb39c919af5c4eb8cb9ab12f4ccd37b6e7bc5eae90365a489c7e17f5` |
| Scene B packet | `build/gpu_evaluation/t1d_vertex_ab_20261004/scene_b_01/scene_packet.bin` | `156ab65f14559c350bc602d4a48ee441cc2b145bfaee1a7775cde067e395a61d` |
| Scene B preview | `build/gpu_evaluation/t1d_vertex_ab_20261004/scene_b_01/preview.ppm` | `05b3f2c32ac5d92e07c3b43677756418de980e43ad00e8d442116641e0a4e4fe` |
| Frozen baseline fixture | `fixtures/gpu_t1d_scene_wire_64b.bin` | `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` |
| Historical baseline sender | `tools/send_gpu_t1d_scene.py` | `7310a1a9f505a215a26082f1928963a96054a1e4552b96d0dba72a777fd110a1` |
| A/B sender | `tools/send_gpu_t1d_vertex_ab.py` | `621dcbec34c5ca09f34302a03dd26c1ec1d992dd64f450d946f7de26810b0859` |

Both packet files are 64 bytes and begin with `A5`. Scene A is the frozen
fixture. Scene B changes only triangle 0 V2 from `[120,460,700]` to
`[120,240,700]`. The exact software preview predicts `(100,300)` is background
for B; it predicts triangle 1 remains present through y=460. These are
software predictions, not device-model or physical-pixel claims.

Historical physical identity: QMTech Wukong XC7A100T-FGG676, Xilinx IDCODE
`0x03631093`; DirtyJTAG USB `1209:c0ca`, serial `CB81353DCE678119`; CH340 USB
`1a86:7523`, serial identity `1a86_USB_Serial`. At execution, require the
current read-only preflight to confirm these identities and the endpoint
`/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`. Do not guess a `/dev/ttyUSB*`
name or substitute another adapter.

## 3. Software preparation and acceptance

1. Preserve the already generated Scene B input, packet, and preview artifact.
   Do not overwrite either S1 output directory.
2. Implement `tools/send_gpu_t1d_vertex_ab.py` as the fixed A/B sender described
   in §1. Pin A and B to the packet hashes in §2. Keep it single-purpose and
   reject any other scene label, packet size, start byte, or digest before
   opening the serial port.
3. Add falsifiable checks in `software/tests/test_gpu_t1d_vertex_ab_sender.py`
   proving A and B resolve to their pinned 64-byte packets and malformed
   labels, lengths, start bytes, digests, ports, and transcript paths are
   rejected before the serial port open call or any file overwrite.
4. Run these read-only identity checks from the repository root:

   ```bash
   sha256sum build/d3_physical_diag_20260921/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit
   sha256sum build/gpu_evaluation/s1_t1d_scene_20261004/run_01/scene_packet.bin
   sha256sum build/gpu_evaluation/t1d_vertex_ab_20261004/scene_b_01/scene_packet.bin
   sha256sum tools/send_gpu_t1d_vertex_ab.py
   ```

5. Halt if any frozen digest differs, if the B preview does not show
   `(100,300)` as background, or if the helper can open the port before packet
   validation or can transmit more than one transaction per invocation.

## 4. Hardware preflight and frozen command sequence

The evidence directory must be new:

```text
build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_06/
```

Create it once, refusing an existing directory, before the preflight commands:

```bash
python3 -c 'from pathlib import Path; Path("build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_06").mkdir(parents=True, exist_ok=False)'
```

Before starting, obtain fresh owner authorization and current operator
readiness for one paired campaign with the frozen §5 budget. Run the
sequenced preflight driver below once. It first checks USB vendor, product,
and DirtyJTAG serial through read-only sysfs attributes, then launches each
remaining read-only command separately and in order. It records invocations,
stdout, stderr, exit status, and UTC start/end, and stops on the first
nonzero exit. The first sysfs check starts the 300-second campaign. Do not
program unless each identity matches §2.

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_06/preflight.py
```

Confirm that the sysfs check reports exactly one DirtyJTAG device with
`idVendor=1209`, `idProduct=c0ca`, and serial `CB81353DCE678119`; also confirm
the CH340, serial endpoint and identity, and current Wukong IDCODE. Halt
before programming unless every identity and the readiness check match §2.
The final preflight step, `openFPGALoader -c dirtyJtag --freq 1000000
--detect -v`, separately establishes that the programmer can access the
adapter in this execution context; require exactly one Artix A7 100T with
IDCODE `0x03631093`.
Run the one SRAM
load:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_06/run_stage.py program
```

Require the loader's SRAM completion and `ISC_DONE`, `INIT`, and `DONE`
success report. Require the operator to confirm the black/unarmed image and
stable monitor lock before sending A. Then send A exactly once:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_06/run_stage.py A
```

After A's `tcdrain`, wait 100 ms and allow one observation interval of at
most 30 seconds. Record the A report. If A is not the expected two-triangle
image, stop; do not send B. If A is as expected, send B exactly once:

```bash
python3 build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_06/run_stage.py B
```

After B's `tcdrain`, wait 100 ms and allow one observation interval of at
most 30 seconds. Record the B report. Do not reset between A and B; the second
transaction tests whether the active scene accepts the changed vertex set.

## 5. Budget, classification, and stop conditions

Owner-authorized frozen budget:

```text
campaign attempts: 1 paired A/B campaign
FPGA SRAM loads: 1, maximum 60 seconds
UART sends: 2 total (A once, B once), maximum 10 seconds each
visual observations: 2, maximum 30 seconds each
overall hardware campaign wall-clock budget: 300 seconds
retries, resets, alternate ports, and changed setup: 0
```

The budget begins before the first hardware command. A preflight mismatch,
command error, short write, missing transcript, absent monitor lock, or
ambiguous observation consumes the campaign and halts it. Do not retry or
extend any timeout under this contract.

Classify only the visual result:

- **A/B VISUAL PASS:** A shows the expected two triangles; B visibly shortens
  the red triangle to y=240 while the green triangle remains unchanged; the
  monitor remains locked.
- **VISUAL HOLD:** either scene is blank, stale, malformed, unchanged when B
  should replace A, inconsistent, or cannot be judged.

Host `write` and `tcdrain` records establish host-side transmission only.
Neither classification proves FPGA byte acceptance, CRC, loader completion,
frame-boundary activation, pixel equality, or behavior of a current-source
bitstream. If A/B passes, the next contract may target a current-source T1d
build. If it holds, preserve the evidence and diagnose from that record; do
not issue another hardware attempt under this contract.

## 6. Authorization and required gates

The owner explicitly replied "Authorized and confirmed" for `hardware_06/`.
Readiness and authorization are established. Its scope is one
300-second campaign using the sysfs serial check and the separate
`openFPGALoader --detect` access check, followed—only if both and all other
preflight conditions pass—by one historical SRAM load and one A-then-B
sequence. Execute device commands in the host context outside the filesystem
sandbox. The stage recorder preserves the frozen underlying commands, refuses
repeats, and checks the remaining campaign budget before each stage.

Record each hardware command's exact invocation, UTC start and end, and exit
status in `hardware_06/command_results.json`; the adjacent `.txt` and `.log`
files retain its stdout and stderr.

The command list below defines the required software gates. Their completed
PASS results are recorded in §7. For `hardware_06`, reuse those results: the
sender, packet fixtures, RTL, and synthesis inputs have not changed since the
gates ran. Do not rerun them for this physical comparison.

```bash
python3 software/tests/test_gpu_t1d_vertex_ab_sender.py
bash tools/verify_repo.sh
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
```

Run the full repository gate through this exact detached command because it
exceeds 60 seconds:

```bash
tools/run_detached_job.sh --output build/gpu_evaluation/t1d_vertex_ab_20261004/repo_gate_01 --timeout 1800 --notify-desktop -- /usr/bin/bash -lc 'bash tools/verify_repo.sh'
```

After `LAUNCHED`, record the unit and evidence path and end the agent turn.
Interpret a later result only when exactly one terminal marker exists. Do not
retry or extend the timeout.

Reuse the already completed S1 Padé-target synthesis gate at
`build/gpu_evaluation/s1_t1d_scene_20261004/a7_pade_gate_01/`: exactly one
terminal marker `COMPLETE`, exit 0, unit
`spu-a7_pade_gate_01-20261003T224519Z-54338`. This contract changes no RTL or
build inputs; verify the eight profile RTL hashes recorded in the S1
`run_01/manifest.json` still match before using that result. Do not relaunch
the same synthesis for this software-only sender change.

Hardware visual status remains independent of repository and synthesis
results. Do not describe this historical-image control as current-source or
silicon-verified regression closure.

## 7. Execution record

- Owner authorized the §4–§5 hardware campaign on 2026-10-04.
- Scene B packet and preview generated under `build/gpu_evaluation/t1d_vertex_ab_20261004/scene_b_01/`; frozen hashes match §2.
- S1 manifest profile RTL hashes match all eight current profile RTL files.
- `python3 software/tests/test_gpu_t1d_vertex_ab_sender.py`: PASS, 6 tests.
- Full repository gate: COMPLETE, exit 0, 896 seconds; unit `spu-repo_gate_01-20261004T091744Z-63923`; evidence `build/gpu_evaluation/t1d_vertex_ab_20261004/repo_gate_01/`.
- ROTC trace: PASS, 336 checks; log `build/gpu_evaluation/t1d_vertex_ab_20261004/remaining_gates_01/rotc_trace.log`.
- IROTC trace: PASS, 9 tests; log `build/gpu_evaluation/t1d_vertex_ab_20261004/remaining_gates_01/irotc_trace.log`.
- Rational robotics: PASS, 104 checks; log `build/gpu_evaluation/t1d_vertex_ab_20261004/remaining_gates_01/rational_robotics.log`.
- Rational SOM: PASS, 24 checks; log `build/gpu_evaluation/t1d_vertex_ab_20261004/remaining_gates_01/rational_som.log`.
- Lucas MAC oracle: PASS, 166,666 identity macros / 999,996 mixed primitive operations; log `build/gpu_evaluation/t1d_vertex_ab_20261004/remaining_gates_01/lucas_mac.log`.
- Preflight halted at `2026-10-04T10:06:49Z` because the pinned DirtyJTAG serial was not established; §5 makes any preflight mismatch consume this campaign. The owner later approved adding the read-only `lsusb -v -d 1209:c0ca` descriptor check, but that command was not run. The original 300-second window began at `2026-10-04T10:06:17Z` and expired at `2026-10-04T10:11:17Z`; no programming or UART sends occurred. A fresh owner-authorized campaign is required before further hardware commands.
- Padé batch inversion: PASS, 25 checks; log `build/gpu_evaluation/t1d_vertex_ab_20261004/remaining_gates_01/pade_batch.log`.
- S1 Padé-target synthesis reused: COMPLETE, exit 0, 403 seconds; unit `spu-a7_pade_gate_01-20261003T224519Z-54338`. The eight profile RTL hashes still match.
- Operator readiness confirmed on 2026-10-04. Read-only preflight found the CH340 identity and Wukong XC7A100T IDCODE correct, but did not establish DirtyJTAG serial `CB81353DCE678119`.
- Preflight results and command timestamps: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_01/command_results.json`; individual outputs are in the same directory. Campaign halted before SRAM programming or UART transmission.
- Fresh owner authorization for `hardware_02/` received on 2026-10-04. Its 300-second campaign starts at the first preflight hardware command; the read-only DirtyJTAG descriptor query is required before any programming.
- `hardware_02` preflight halted at `2026-10-04T10:21:00Z`: `lsusb -v -d 1209:c0ca` exited 0 but wrote only the short USB device inventory, without descriptors or the pinned `iSerialNumber`. Per §5 the preflight mismatch consumes the campaign. No further device command, FPGA load, or A/B send was run; evidence is in `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_02/`.
- The `hardware_02` command-resolution diagnosis found that `PATH` selects `/opt/oss-cad-suite/bin/lsusb`, a shell script that emits the short inventory. The §4 correction now invokes `/usr/bin/lsusb` explicitly; it produced the required verbose descriptor in `hardware_03`.
- `hardware_03` used `/usr/bin/lsusb` and established all recorded identities, including DirtyJTAG serial `CB81353DCE678119` and Wukong IDCODE `0x3631093`. The required current operator-readiness confirmation did not arrive before the 300-second deadline (`2026-10-04T10:47:02Z`), so this campaign expired without programming or UART sends. Evidence is in `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_03/`.
- For `hardware_04`, the owner reconfirmed readiness and authorized a new 300-second campaign. DirtyJTAG serial, USB identities, CH340 serial target, and udev identity matched. Slow command turnaround left fewer than 50 seconds before the `2026-10-04T19:14:03Z` deadline, so current FPGA detection and the load/A/B sequence were not started. The campaign expired without programming or UART sends; evidence is in `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_04/`.
- `hardware_05` showed that `/usr/bin/lsusb` can fail at libusb initialization. The prepared §4 flow replaces that dependency with a sysfs identity check and separately tests programmer access using `openFPGALoader --detect`. Any hardware attempt still requires a fresh owner-authorized, frozen campaign budget; campaigns `hardware_01` through `hardware_05` are consumed or expired.
- `hardware_05` was authorized as a fresh 300-second campaign with readiness confirmed. Its first preflight command, `/usr/bin/lsusb -v -d 1209:c0ca`, exited 1 with `unable to initialize libusb: -99`; the stop-on-error rule halted the sequence at `2026-10-04T19:21:07Z`. The remaining preflight checks, programming, and UART sends did not run. Evidence is in `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_05/`.
- `hardware_06`: owner authorization and readiness confirmed. Host preflight passed; DirtyJTAG serial, CH340 identity/endpoint, and Wukong IDCODE matched. Campaign started `2026-10-04T20:14:04Z`, deadline `2026-10-04T20:19:04Z`. SRAM load exited 0 after 31 seconds, ending `2026-10-04T20:14:54Z`; loader reported `ISC_DONE=1`, `INIT=1`, `DONE=1`. The campaign expired before the required baseline confirmation; UART A/B did not run.
- Operator report received after the deadline at `2026-10-04T20:25:03Z`, verbatim: "No image change, still the original. Should I power cycle the fpga?" No power cycle or reset was performed by the agent. This establishes an unchanged-display observation, not a physical A/B result or proof that programming failed.
- Halt-and-Flag finding: the historical visual evidence (`contract_gpu_t1d_visual_observation_2026-09-21.md` §5 and `docs/hardware_evidence.md`, 2026-09-21 T1d entry) establishes the black/unarmed baseline after a physical warm reset. It does not establish that SRAM configuration alone produces that baseline. This contract assumed configuration-only black startup while freezing resets at zero. A reset procedure needs an explicit amendment and new bounded authorization before execution.
