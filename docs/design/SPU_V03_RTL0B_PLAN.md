# SPU v0.3 RTL-0B plan: runtime loading and observation

**Status: IMPLEMENTED — gates B1–B6 PASS (2026-11-12; record in §7–§8). Plan revision 2, D1–D5 approved 2026-11-11 with corrections A–D. Simulation and out-of-context routed evidence only; no board or silicon claim.**

**Specification:** the frozen [v0.3 contract](SPU_V03_CONTRACT_CANDIDATE.md): §9 START and BUSY, §10 the
SPUI image and image-valid, §11 the 213-byte record.

**Builds on:** RTL-0A (simulation PASS), RTL-0S (synthesis PASS) and RTL-0P (routed PASS at 40 ns,
out-of-context).

## 1. Objective and boundaries

RTL-0B adds the hardware that lets a host load a program, START it with a budget, poll status and read
the 213-byte result record, over UART. It ends with simulation-verified RTL plus an out-of-context
synthesis and route of the complete system top.

**Not in RTL-0B:**
- board pins, bitstream and programming (RTL-0C);
- any ISA or arithmetic change;
- any edit to frozen Gen-1 files.

The H0 experimental UART work (`research/h0_uart_1*`, ledger §3.46) is a **reference**, not qualified
infrastructure.

## 2. Architecture (new modules, 50–150 lines each, `hardware/rtl/core/psurd/`)

| Module | Function |
|---|---|
| UART RX/TX | 8N1 at 115,200 baud, 217 clocks per bit at 25 MHz, as Gen-1. RX uses a two-flop synchronizer. Candidate reuse: `hardware/rtl/peripherals/whisper/spu_uart_{rx,tx}.v`, after their own fixtures (D2) |
| `psurd_link` | Frame parser and response builder (protocol §3). Checks the checksum and length, enforces an inter-byte timeout, and drains on error |
| `psurd_loader` | SPUI header check (magic, profile `0x01`, revision `0x03`, 1 ≤ L ≤ 256), **in-order word count**, streaming CRC-32/ISO-HDLC over the words, writes through the core's `imem` port, and owns **image-valid** |
| `psurd_runctl` | Accepts START only when image-valid = 1, busy = 0 and B ≥ 1. Owns busy and drives `psurd_core` `start`/`budget`/`img_len`. Gives BUSY to LOAD or START during a run |
| `psurd_record` | Builds the 213-byte record from core state and a **register dump** (D4), with zero-fill for uninitialized registers and CRC-32 over bytes 0–208. Owns **record-valid**, which is distinct from the core's `done` (correction C) |
| `psurd_sys_top` | Integrates these with `psurd_core`, single clock domain |

**Load transaction (correction A).** `LOAD_END` is the only commit point.
1. `LOAD_BEGIN` checks the header, clears image-valid and opens a load transaction.
2. `LOAD_WORD` accepts only the next expected index and updates the running CRC.
3. After word L−1 the image is **complete but not executable**.
4. `LOAD_END` checks the word count = L and the final CRC, then sets image-valid = 1 **atomically**.

This is consistent with contract §10: image-valid becomes 1 only on a successful LOAD, and a LOAD
attempt clears it when it begins. **No ISA or SPUI change.**

**State effects (correction B):**

| Situation | image-valid | Load transaction |
|---|---|---|
| LOAD_BEGIN accepted (idle) | cleared | opened |
| LOAD_BEGIN refused while idle (bad header) | **cleared** (a refused LOAD, contract §10) | none |
| LOAD_BEGIN during an open transaction | cleared | old one aborted, new one opened if the header is valid |
| LOAD_WORD error (order, duplicate, index ≥ L) | stays 0 | aborted |
| LOAD_END with a wrong count or CRC | stays 0 | aborted |
| A malformed frame (bad checksum or length, timeout) **while a load is open** | stays 0 | aborted |
| A malformed frame **while no load is open** | **unchanged** (not a LOAD attempt) | — |
| LOAD or START refused as BUSY | **unchanged** | unchanged |
| STATUS, RESULT | unchanged | unchanged |

An interrupted transfer can never leave a runnable image: until a successful LOAD_END, image-valid is 0.

**Run and result states (correction C):**
- **IDLE / READY:** no run in flight. `record-valid` says whether a completed record exists.
- **RUNNING:** from an accepted START until the core's `done`. RESULT gives BUSY.
- **FINALIZING:** from `done` until the record builder has written all 213 bytes and the CRC. RESULT
  still gives BUSY. LOAD and START give BUSY (the register dump uses read port A).
- **READY:** record-valid = 1, published **atomically** only after the CRC is complete.

An **accepted** START clears record-valid. A refused or BUSY START leaves the existing record intact.
A failed LOAD never touches the record. All commands, and RESULT transmission, go through **one link
FSM**, so a record can never change while it is being sent.

## 3. Host protocol: H0-UART-1B v2 (candidate)

- **Frame:** `A5 02 cmd len_lo len_hi payload checksum`. The checksum is an 8-bit XOR over every
  preceding byte, as in 1B; v2 adds a 16-bit length.
- **Response:** `A5 02 (cmd | 80) status len_lo len_hi payload checksum`.
- **Status codes:** OK, REFUSED (with a reason byte), BUSY, BAD_FRAME, TIMEOUT.

| cmd | Name | Payload | Response |
|---|---|---|---|
| 01 | LOAD_BEGIN | the 12-byte SPUI header | OK, or REFUSED with a reason (framing, identity, revision, length). Image-valid is cleared in both cases |
| 02 | LOAD_WORD | index (u16) followed by the 8-byte word (big-endian, as in SPUI) | OK, or REFUSED (order) |
| 03 | LOAD_END | — | OK, meaning the CRC matched and image-valid = 1; or REFUSED (CRC or count) |
| 04 | START | budget B (u32) | OK, or REFUSED (no image, B = 0), or BUSY |
| 05 | STATUS | — | image-valid, load-open, run state (IDLE / RUNNING / FINALIZING / READY), record-valid, last cause, run id |
| 06 | RESULT | — | the 213-byte record, or REFUSED (no completed run) or BUSY |

**Bounded recovery (correction D).**
- **Maximum payload per command:** LOAD_BEGIN 12, LOAD_WORD 10, START 4, and 0 for the rest. A length
  field that disagrees with the command is BAD_FRAME, and the parser then drains only the declared
  length, which is at most 12. No command can make the receiver wait for up to 65,535 bytes.
- **Timeout:** measured **between bytes** (proposed: 8 byte-times). It fires inside any frame; on
  expiry the parser drops the partial frame and returns to waiting for `A5`.
- **Requirement:** after every transport error, the parser is ready for a fresh valid frame within a
  bounded number of cycles, and B2 checks this for each error class.

The frame checksum protects commands; the SPUI CRC protects the image. Neither is authentication
(contract §10). Refusals are responses, never execution records (contract §10, "load rejection is not
an execution result").

## 4. Verification gates

| Gate | Content |
|---|---|
| B1 transport | RX/TX fixtures at the bit level: framing, noise or break on idle, and the two-flop synchronizer |
| B2 link | Frames, checksum errors, length overruns and mismatches, inter-byte timeout and the drain path, with planted mutants. For **every** error class, a fresh valid frame must be accepted afterwards within a bounded number of cycles (correction D) |
| B3 loader | Every refusal kind (framing, identity, revision 0x02, length, CRC, order, duplicate, truncated, timeout, new LOAD_BEGIN mid-load) is checked to leave image-valid = 0. **LOAD_END is the only commit point**: START between the last word and LOAD_END is refused. A malformed non-load frame leaves a valid image intact. BUSY causes no state change. The SIM-0 session sequences are mirrored and compared, response for response, with `spu_vm --do` |
| B4 system | The full RTL-0A program set is loaded **over the simulated UART**: every 213-byte record is byte-identical to the oracle and to the C++ simulator. Also: BUSY during a run and during finalizing; RESULT before, during and after a run; repeated START; a refused START keeping the old record. **Directed case: a failed LOAD after a completed run invalidates the image but leaves the retained record intact and readable** |
| B5 physical | Out-of-context synthesis and route of `psurd_sys_top` with the RTL-0P flow; setup and hold positive. **The `imem` write path is registered inside the loader** to address RTL-0P's thin hold margin (+0.033 ns, at the instruction memory's write-data inputs) |
| B6 boundary | Shared-module hashes match the baseline; Gen-1 conformance 80/80; the integrated gate passes |

## 5. Decisions requested

| # | Decision | Recommendation |
|---|---|---|
| D1 | Protocol | H0-UART-1B v2 as in §3 (familiar framing; only the length grows) |
| D2 | UART primitives | Qualify the existing `spu_uart_{rx,tx}` in B1; write new ones only if they fail |
| D3 | Clocking | One 25 MHz domain for core, loader and UART, as Gen-1's cpu_clk. The board PLL and clock generation are RTL-0C |
| D4 | Register dump | A small `psurd_core` port: after `done`, the record builder drives bank read port A (the core is idle). No third port. Works with either register bank (RF-A or RF-B) |
| D5 | Record ownership | One record. Only an **accepted** START clears record-valid, and publication is atomic after the CRC (correction C) |

## 6. Risks

- **The hold margin at the instruction-memory inputs** was +0.033 ns with the synthesis wrapper. B5
  must re-measure it with the real loader; a register stage is planned.
- **UART receive is asynchronous.** It is covered by the synchronizer and the B1 fixtures. Board-level
  signal integrity is RTL-0C.
- **The H0 endpoint's REVISE history.** It is used only as a design reference; RTL-0B's link is
  qualified on its own.

## 7. Implementation record (protocol values fixed at implementation)

Implementation baseline: commit `7920437c` (B2–B4 RTL and benches). Owner review 2026-11-12: status codes
approved provisionally; the stray-load policy approved subject to contract consistency (contract §10: "Refused
LOAD, for any reason" gives image-valid = 0, so there is no conflict); accelerated simulation bit time approved.

These are **transport protocol codes**. They are not ISA opcodes and not execution causes (contract §8.2).

| Status | Meaning | Payload |
|---|---|---|
| `0x00` | OK | none; 7 bytes for STATUS; the 213-byte record for RESULT |
| `0x20` | REFUSED | one reason byte |
| `0x22` | BUSY (a run is in flight or its record is being built) | none |
| `0x01` | BAD_FRAME (version, unknown command, length, checksum, UART framing error) | none |
| `0x04` | TIMEOUT (more than 8 byte-times between two bytes of a frame) | none |

| Reason | Command | Meaning | image-valid |
|---|---|---|---|
| 1 | LOAD_BEGIN | framing: magic is not `SPUI` | cleared |
| 2 | LOAD_BEGIN | identity: profile is not `0x01` or revision is not `0x03` | cleared |
| 3 | LOAD_BEGIN | length: L is 0 or above 256 | cleared |
| 4 | LOAD_END | CRC mismatch | stays 0 |
| 5 | LOAD_WORD | order: not the next expected index (skipped, duplicate, or index ≥ L) | stays 0 |
| 6 | LOAD_END | count: fewer than L words received | stays 0 |
| 7 | LOAD_WORD, LOAD_END | no load open. Treated as a refused LOAD | **cleared** |
| 8 | START | no valid image | unchanged |
| 9 | START | B = 0 | unchanged |
| 10 | RESULT | no completed run | unchanged |

A validly framed load command that is refused (reasons 1–7) is a LOAD attempt and leaves image-valid = 0. A
malformed frame is not a LOAD attempt: it aborts an open load and otherwise changes nothing. A load command
answered BUSY changes nothing. No load refusal touches the retained record.

**STATUS payload (7 bytes):** flags (bit 0 image-valid, bit 1 load-open, bit 2 record-valid); run state (0 IDLE,
1 RUNNING, 2 FINALIZING, 3 READY); cause of the retained record, or `0xFF` if there is none; run id (u32
little-endian, incremented by each accepted START). The bytes are a snapshot taken when the command is answered.

**LOAD_WORD index** is u16 little-endian; the word follows in SPUI byte order (big-endian). **START budget** is
u32 little-endian. A parser error before the command byte is answered with response command `0x80`.

**Stop-and-wait.** The host sends one frame and waits for the complete response. Bytes that arrive while a
request is pending or a response is being sent are ignored.

**Simulation bit time.** `psurd_sys_top` defaults to 25 MHz, 115,200 baud and a 17,360-cycle inter-byte limit;
these are the only synthesized values. The B3 and full B4 benches override the parameters in the testbench
instance (4 cycles per bit) to bound simulation time. UART timing at 217 cycles per bit is covered by B1, B2 and
the B4 quick set, not by the accelerated runs.

## 8. Qualification record

Evidence directories are under `build/psurd-rtl0b/` (detached-runner jobs; each holds its command, source
revision, logs and terminal marker). The RTL is identical in `7920437c`, `fde7e57e` and `733acb28`; the later
commits change benches, the regression runner and this document only. Simulation, routed timing and physical
FPGA qualification are reported separately; nothing below is a silicon claim.

| Gate | Evidence | Revision | Result |
|---|---|---|---|
| B1 transport | `b1-06-psurd-rx` (and the failing shared receiver, `b1-07-legacy-rx`) | `a0e762ea` | PASS, 5 mutants detected |
| B2 link | `b2-01` | `7920437c` | PASS: 98 cases at 217 and at 16 cycles/bit, 19 of 19 mutants detected |
| B3 loader | `b3-01` | `7920437c` | PASS: 100 cases (1,630 frames) equal to the reference model, 12 SIM-0 sessions equal to `spu_vm --do`, 19 of 19 mutants detected |
| B4 system, full set | `b4-05` | `733acb28` | PASS: 649 programs loaded over UART, every 213-byte record equal to the oracle and to the C++ simulator; 72 directed and BUSY-sweep cases (5,206 frames); 18 of 18 mutants detected |
| B4 system, 217 cycles/bit | `b4-04-bit217-quick` | `fde7e57e` | PASS: 22 programs, 102 directed and sweep cases (1,047 frames) |
| B5 physical | `b5-01` | `733acb28` | PASS: routed, setup +5.869 ns, hold +0.032 ns, 0 routing errors (out-of-context, 40 ns) |
| B6 boundary | `b6-gate-01` | `733acb28` | PASS: `bash tools/verify_repo.sh` COMPLETE, exit 0, 273 passed / 0 failed |

**Superseded attempts (no verdict; kept as development history).** `b2-b4-00-scratch-history` holds the
pre-commit scratch failures (a B2 mutant the bench missed, two B3 bench expectation errors).
`b4-02-bit217-quick` FAILED: every frame matched the reference model, but the BUSY sweep never sampled READY at
217 cycles/bit (bench sweep range; fixed in `fde7e57e`). `b4-01` (TIMEOUT) and `b4-03` (stopped, no terminal
marker) stalled on the stale-`done` mutant because the bench polled a run that never ends without a bound
(fixed in `733acb28`); each has a `SUPERSEDED.txt`. None of these exposed a defect in the unmodified RTL.

**Bench poll bound.** A poll step ends the simulation after 3,000 STATUS exchanges without END. For the
unmodified RTL that is a qualification failure; for a planted mutant it is a detection; an external job
deadline is TIMEOUT and never a pass. The longest legitimate poll sequence observed is 7 (`b4-05`).

**B3 evidence identity.** `b3-01` ran on the bench host of `7920437c`. The host later gained X-byte handling
and the poll bound; the B3 cases, the reference model and the RTL are unchanged. B3 runs without mutants on
the current host in the required RTL-0B entry of `run_all_tests.py`.

### 8.1 B5 routed result (`b5-01`)

Out-of-context route of `psurd_sys_top`, xc7a100tfgg676-1, 40.000 ns, default flow (`rtl0b_synth.tcl`, then the
unchanged `rtl0p_impl.tcl`). Scope: internal register-to-register paths. It does not establish board-level
timing, UART signal integrity or metastability performance.

| Item | Full system | Core only (`e43759cd`) |
|---|---|---|
| Setup slack | +5.869 ns | +6.875 ns |
| Hold slack | +0.032 ns | +0.034 ns |
| Routing errors | 0 | 0 |
| LUTs / flip-flops | 11,600 / 5,318 | 10,989 / 4,831 |
| LUTRAM LUTs / DSPs | 256 / 112 | 256 / 112 |
| Block RAM | RAMB36 (instruction memory) + RAMB18 (record) | RAMB36 |
| Latches / black boxes | 0 / 0 | 0 / 0 |

All 17,928 endpoints are constrained and met; the only unconstrained items are the six top-level ports. DRC
and methodology report warnings only, of the same types as the core-only route.

| Block | Worst setup slack | Worst hold slack |
|---|---|---|
| UART RX / TX | +31.3 / +34.0 ns | +0.174 / +0.186 ns |
| Link | +31.3 ns | +0.139 ns |
| Loader | +28.3 ns | +0.035 ns (to the instruction-memory data inputs) |
| Record builder, CRC included | +8.1 ns | +0.138 ns |
| Run control | +32.8 ns | +0.196 ns |

**Limitations recorded at B5.**
- **Hold margin is thin and the loader register did not widen it.** The registered `imem` write path has
  +0.035 ns; the design-wide worst hold path (+0.032 ns) is inside the arithmetic normalizer. The router fixes
  hold to just above zero. The register stage must not be described as having solved the §6 hold risk. Hold is
  a fresh qualification item on the RTL-0C board top; these figures are not a physical margin.
- **Setup slack fell by about 1 ns** because the D4 register-dump mux sits ahead of the LUTRAM read on the
  path instruction memory → decode → register read → sign unit → flags. No pipeline stage is added.
- **The UART receive synchronizer has no `ASYNC_REG` attribute.** The two flops exist (hold +0.222 ns between
  them) but Vivado does not treat them as a synchronizer. Owner ruling 2026-11-12: adding the attribute to
  `psurd_uart_rx.v` is a **prerequisite for board programming**, done at the start of RTL-0C preparation with
  B1, B2, B5 and the compact regression re-run; a full B4 mutation campaign is not required for an
  attribute-only change.

### 8.2 B6 integrated gate (`b6-gate-01`)

`bash tools/verify_repo.sh` on `733acb28`: COMPLETE, exit 0, **273 passed, 0 failed**, none skipped. The previous
gate (`build/psurd-rtl0a/rfb-gate-01`, `e43759cd`) had 272; the per-test result lists differ only by the one new
entry. Within it: shared-module hashes equal the recorded Gen-1 baseline (RTL-0A G6); Gen-1 simulator
conformance 80 of 80; RTL-0A G1 (8,720 vectors) and G2–G6 with mutants PASS; the new required RTL-0B entry ran
B1, B2 (16 cycles/bit), B3 and the B4 quick set with its two planted-mutant controls, all PASS, counted once.

**RTL-0B disposition: B1–B6 PASS within the scopes above** (simulation; out-of-context routed timing). Board
pins, clocking, bitstream and programming are RTL-0C and remain on HOLD until its plan is approved.

### 8.3 Synchronizer attribute correction (RTL-0C preparation, `98c85afd`)

`psurd_uart_rx.v` now marks the two receive-synchronizer flops `ASYNC_REG = "TRUE"` (attribute only, no logic
change). Focused re-qualification on `98c85afd`:

| Evidence | Content | Result |
|---|---|---|
| `c0-asyncreg-sim-01` | B1 with 5 mutants; B2 at 217 and 16 cycles/bit with 19 mutants; B3 (no mutants); B4 quick set with 2 controls | COMPLETE, exit 0, all PASS |
| `c0-asyncreg-b5-01` | Synthesis and route of `psurd_sys_top`, same flow as B5 | COMPLETE, exit 0 |

Routed result: setup **+6.986 ns**, hold **+0.056 ns**, 0 routing errors; 11,600 LUTs, 5,318 flip-flops, 256
LUTRAM LUTs, 112 DSPs, RAMB36 + RAMB18, no latches or black boxes; all 17,928 endpoints constrained and met;
the same warning types as `b5-01`. Vivado reports `ASYNC_REG` on both flops and placed them in one slice
(SLICE_X74Y0, AFF and A5FF); hold between them is +0.144 ns. The worst hold path is now the loader's registered
write to the instruction memory (+0.056 ns); the worst setup path is inside the arithmetic unit.

The differences from `b5-01` (setup +5.869, hold +0.032) come from a different placement, not from a logic
change. They show how much these figures move between runs: the hold margin is still thin and remains a fresh
qualification item on the RTL-0C board top. The attribute supports placement and metastability analysis; it
does not guarantee reliable asynchronous reception. The full B3 and B4 mutation campaigns were not repeated
(owner ruling: not required for an attribute-only change).
