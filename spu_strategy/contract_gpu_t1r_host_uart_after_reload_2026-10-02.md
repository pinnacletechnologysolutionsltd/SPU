# Engineering Contract: T1r Host UART Sequence After SRAM Reload

**Date:** 2026-10-02  
**Contract ID:** `GPU-T1R-HOST-UART-AFTER-RELOAD-2026-10-02`  
**Status:** ACTIVE — one sender invocation consumed; host writes/drains PASS; visual HOLD with operator-confirmed flickering snow; state details pending  
**Owner:** John Curley  
**Spec Author / Implementer / Auditor:** Codex

## 0. Scope and authorization

The owner replied "Authorized." to the proposal for one A → B → C → return-A sequence following the successful SRAM reload. This authorizes exactly one frozen sender invocation after the confirmations and host preflight below. The old host-namespace contract remains halted against its invalidated load.

Current load evidence: `docs/hardware_evidence.md` §3.30 and `build/gpu/t1r_palette_pair_20261002/power_cycle_reload_01/program_01/`: exactly one `COMPLETE`, exit 0, `Load SRAM` 100%, `isc_done 1`, `init 1`, and `done 1`. The operator reports sync with no image before transmission.

## 1. Frozen inputs and limits

| Item | Frozen value |
|---|---|
| Bitstream | `build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit` |
| Bitstream SHA-256 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` |
| Sender | `tools/send_gpu_t1r_scaled_visibility.py` |
| Sender SHA-256 | `b53d567e254790da7e35269159752523b8a1226b6b646693d5377291008a77f9` |
| Fixture | `fixtures/gpu_t1i_scene_a_wire_175b.hex` |
| Fixture SHA-256 | `079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143` |
| Host endpoint | `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` → `/dev/ttyUSB0`; USB `1a86:7523`, driver `ch341` |
| UART / dwell | 115200 8N1; four 187-byte packets; 5 seconds between packets |
| Packet A / return-A SHA-256 | `3719a5925da386fbd14e1ad1ca38139e5f4b68defdbce3e22a9fc8a5daa8ab58` |
| Packet B SHA-256 | `43dd87f2bdfd0de0aeaaed13693f446099b6c21688c208659992efdbf6a03bd2` |
| Packet C SHA-256 | `71c04abf252893262b7eaed6a2649fd1e3a9abe52a6e008eb3d95dfed7e81f37` |
| Sender invocations / timeout / cumulative budget | 1 / 60 seconds / 60 seconds |
| Evidence directory | `build/gpu/t1r_palette_pair_20261002/host_uart_01/` |
| Transcript | `build/gpu/t1r_palette_pair_20261002/host_uart_01/sequence_01.json` |

Before sender launch, record operator confirmation that the board has remained powered and its SRAM configuration preserved since the §0 reload. Uncertain or lost continuity requires a halt. The operator confirmed: "Yes—still powered and ready now" on 2026-10-02 (local date).

## 2. Host-context preflight

Create the evidence directory only if absent. Preserve commands, stdout/stderr, and statuses in `preflight.txt`. Run the evidence helper once in the approved host context, without opening the serial port:

```bash
python3 build/gpu/t1r_palette_pair_20261002/host_uart_01/preflight.py
```

The helper records UTC time, mount namespace, by-id resolution, and tty character-device identity, and executes:

```bash
udevadm info --query=property --name=/dev/ttyUSB0
sha256sum build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit
sha256sum tools/send_gpu_t1r_scaled_visibility.py
sha256sum fixtures/gpu_t1i_scene_a_wire_175b.hex
python3 tools/send_gpu_t1r_scaled_visibility.py --dry-run
```

Require host mount namespace `4026531832`, exact endpoint and USB/driver identity, all §1 hashes, exactly one successful terminal marker for the new SRAM load, and the frozen scaled-scene oracle/packet dry-run. Any mismatch halts before sender launch. The prior functional/repository/Padé/route gates remain historical evidence; this contract changes no RTL or sender.

## 3. One sender launch

Only after §1 continuity, §2 preflight, and §4 observer readiness are confirmed and recorded, require the transcript destination absent and run this command once in the same approved host execution context:

```bash
timeout 60s python3 tools/send_gpu_t1r_scaled_visibility.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1r_palette_pair_20261002/host_uart_01/sequence_01.json
```

The invocation is consumed on launch regardless of outcome or bytes transmitted. Capture complete output and exit status. Require exit 0, four ordered full 187-byte writes, four successful `tcdrain` completions, all packet hashes, and identical A/return-A bytes. Record transcript SHA-256. Stop after any outcome; no retry, FPGA reload, board reset/power-cycle, USB reset/reconnect, source change, endpoint substitution, or increased timeout is included.

## 4. Observation and closeout

Before sender launch, confirm the operator is ready to observe the complete A → B → C → return-A sequence and record each state separately. Collect the report afterward. If any state was missed or uncertain, record visibility as inconclusive; do not retry under this contract.

A shows the four lane-specific outcome-0 colors; B shows their outcome-1 colors; C shows the per-lane XOR mixture; return-A should match initial A by observation. A visual pass requires all four broad states observed. Record host write/drain success separately from operator observations. Neither establishes exact physical pixel equality or byte-level FPGA acceptance.

Update this contract and `docs/hardware_evidence.md` from the durable sender transcript and operator report, then stop. D4 P1b remains deferred. Operator readiness is confirmed by the §1 reply; the single sender invocation has now run and is consumed.

Host preflight PASS at `2026-10-01T20:42:08Z`, in mount namespace `4026531832`: expected endpoint, CH341 identity, all frozen hashes, successful reload marker/result, and scaled-scene oracle/packet dry-run matched. `preflight.txt` SHA-256: `2a6c75270e09affc4978be06420d7c4f62db6ef946e104177b76df4abe5cb3be`. The evidence-only `run_sequence.py` helper preserves the exact §3 command, operator confirmation, launch timestamp, full stdout/stderr, and exit status; it refuses a second invocation using an exclusive launch record.

## 5. Sender result; partial operator observation

The exact §3 command exited 0 at `2026-10-01T20:45:20.596440Z`. The durable transcript records exactly four ordered A/B/C/return-A writes of 187 bytes each, four completed `tcdrain` calls, all frozen packet hashes, and identical A/return-A packet bytes. Independent transcript checks passed. Host write/drain result: PASS. The single invocation is consumed; no repeat is authorized.

Evidence is in `build/gpu/t1r_palette_pair_20261002/host_uart_01/`. SHA-256 values:

| File | SHA-256 |
|---|---|
| `sequence_01.json` | `50cbc9b6591122adca466cda904d9449bc1f6789d9fe3486178a459f9ec8aaf8` |
| `sender_launch.json` | `396649de400685367085b7cde99b0fee556074a71a907ea5080839e431401118` |
| `sender.stdout.log` | `8bd972b2cf88e21002060c924009de4a8e7c223e11f56ad4676892d37d20a958` |
| `sender.stderr.log` (empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The operator reported: "Crosshatch patterns with interference. Should I take a picture?" Record this as a partial visual observation after the sequence. The report does not identify individual A/B/C/return-A states, establish color transitions, or establish return-A equivalence. The four-state visual result is inconclusive; exact physical pixel equality and FPGA byte-level acceptance are unproven. A full-display photo and crosshatch close-up were requested while preserving the powered return-A state. Evidence ledger: `docs/hardware_evidence.md` §3.31. No RTL, sender, fixture, or bitstream changed; prior functional/repository/Padé/route gates remain historical evidence. Closeout awaits state-specific details.

The supplied `IMG_1790.jpeg` (640×480 photograph) is preserved unchanged in the evidence directory, SHA-256 `86b6e4a9924c741310755ed8a211753fdaf536f445c4c75f242a3f081e16ba9f`. It shows repeated green-and-white diagonal blocks over the visible display area, with fine bands/fringes. The photo was supplied after return-A was requested, but physical state attribution is not independently confirmed. `photo_01.json` preserves the description and limits. An oracle-derived `expected_return_A.png` shows a bounded downward triangle with flat red/green upper regions and blue/white lower regions on black (covered bounds x=40..280, y=40..360). The photographed repeated pattern is inconsistent with that expected output if this is return-A. Classification: visual HOLD; four-state visibility inconclusive. The photograph alone does not establish whether the fine interference originates in the hardware/display or camera. No further hardware action has been taken.

The operator clarified that the diagonal blocks are stationary, vertical blue lines are visible, and visual "snow" flickers constantly. `operator_observation_02.json` preserves the exact report. This establishes live display instability visible to the operator, independent of camera capture; it does not assign the cause to the FPGA, wiring, or monitor. Separate temporal behavior of the blue lines and the A/B/C/return-A transitions remain unreported. The historical final route log reports `clk_pixel` 35.73 MHz against the 25.00 MHz requirement and `sys_clk` 171.35 MHz (global constraint 25.00 MHz); this is tool timing evidence, not a measurement of the present electrical display path. No new sender, reset, reload, or wiring action was taken. Visual HOLD remains.

The operator subsequently reported: "Patterns changed, let's rerun and I'll take a photo." This confirms broad pattern changes in the first sequence, without state-specific detail or return-A equivalence. It renews authorization for one separate photographic replay under `contract_gpu_t1r_photo_replay_2026-10-02.md`; this contract's original invocation remains consumed and its visual HOLD remains recorded.
