# ISA-V02-H0-V1 — Directed instruction acceptance, overlap and completion verification

**Status:** directed simulation PASS; core-level transport defects **reproduced in simulation**. Real Artix-7 SPI reachability **UNRESOLVED**. RTL repair and the normative H0 contract **HOLD**. No production RTL, VM, assembler, opcode, SPI protocol or algorithm change.
**Source identity:** `dev/next` at `33d4be25ed2363012c84e07e1a1afdf5abc76528` (existing VM, assembler and RTL sources unchanged from public RC2 `b063280`; analysis tools, tests and documentation added in `dev/next`). Preserved evidence is added by the commit containing this file (`git log -1 -- docs/isa/ISA_V02_H0V1_FINDINGS.md`).
**Toolchain:** Icarus Verilog 11.0 (stable), four-state, `-g2012`.
**Evidence classes used below:** *simulation* = observed in the preserved probes; *source* = reading of the RTL, not demonstrated by simulation; *proposed* = not implemented.
**Supporting independent review:** `/tmp/H0-PROTOCOL-R1-independent-review-836ca5b3.md` (outside the repository; its stated baseline is the earlier `836ca5b3a700cb162a49635e93af21ce0bfa638d`, which predates the H0 transport findings; no other revision identifier exists). Its source-derived points (no instruction queue or backpressure, `inst_seen` only suppresses re-acceptance of a held level, a possible SCK-sampling-margin question) were not independently reproduced here except where stated. Its SCK sampling question was **not** tested.

## 1. Preserved evidence

`hardware/tests/spu13/h0_v1/`:

| File | Role |
|---|---|
| `h0v1_core_probe.v` | `spu13_core` driven with one-cycle `inst_valid` strobes (core-level stimulus) |
| `h0v1_sidecar_probe.v` | `spu13_rplu2_pade_sidecar` busy handling |
| `run_h0_v1.py` | builds each probe in a temporary directory, runs it, compares normalized output with the fixed expectations; reports mismatches and **has no option to regenerate expectations** |
| `expected/core.txt`, `expected/sidecar.txt` | fixed expected outputs (165 and 38 lines of normalized output) |

The probe names avoid the substring `tb`, so `run_all_tests.py` (patterns `*_tb.v`, `*tb*.v`, `testbench*.v`) does not discover them (checked); they are **not** part of the regression gate.

```bash
python3 -I hardware/tests/spu13/h0_v1/run_h0_v1.py               # about 75 s (core probe about 70 s)
python3 -I hardware/tests/spu13/h0_v1/run_h0_v1.py --skip-core   # sidecar only, under 1 s
```

Expected: `PASS core (165 lines)`, `PASS sidecar (38 lines)`, `RESULT: PASS`.

**Core configuration:** `ENABLE_MATH=1`, `ENABLE_CORE_RPLU_V2=1`, `ENABLE_CORE_RPLU_V2_PIPELINE=1`, `ENABLE_CORE_SOM=0`, `ENABLE_IROTC=0`, `ENABLE_SURD_CPU=0` (default), `ENABLE_CORE_RPLU_V2_EXTENSIONS=0`, `SHARE_RPLU_PADE_INV_MULT=1`, reference inverter, `boot_done=1` (scenario S7b holds it 0). **Stimulus:** `inst_valid` is high for exactly one clock cycle per instruction, as `spu_spi_slave.v` produces it (registered output). "Gap *g*" is the number of clock cycles between the two sampling edges; the first strobe is sampled at cycle index `c=1`. Each scenario starts from a reset.

**Hashes (SHA-256).** Original scratch probes: `h0v1_core_probe.v` `93c44e0daf01eb2130b389b33a0b52c77fd4ae868f34abd0c6e35e9241079730`; `h0v1_sidecar_probe.v` `b5976ccfcbf065714fa1638a52a47bbad1f1b584ef32fd17ea4ee5fa0cbf7835`. Preserved: `h0v1_core_probe.v` `46aac56cd6c28ca8f0014c3750f210fe09c5d2256b7677449a7dfd7fb1fa9cfd`; `h0v1_sidecar_probe.v` `4c3d5c997d2136fa5d4c9905fe667443de6fc851057e2b315272c124135844e9`; `run_h0_v1.py` `a9f0e990185a239fd76e775b393c7131720f1a67c03fcb82afb02d30b561c4d7`; `expected/core.txt` `b3d45c6abdf28150f5e3cf4ad8ec9f71ac57645cb305aa99023a7226146963ae`; `expected/sidecar.txt` `1f6257c3278ce76763fefae46c8363c05934d2df78af42493d291f99e039f28b`. Changes from the originals: a four-line header comment and a print-only `NOTE` line when a scenario uses gap 1 (§6). **Verification:** the original scratch logs and the preserved outputs agree line for line (excluding the added `NOTE` lines) in both probes. The runner was checked to fail when one expected line is altered (and the file restored; `cmp` confirmed the expectations unchanged). Trailing whitespace was stripped from the stored expected files (formatting only; the runner compares right-stripped lines). The core probe compiles with the extra behavioral model `hardware/tests/common/sim_spu_gowin_mult32.v` (a multi-module file iverilog cannot find by module name).

## 2. Baselines and unsupported opcodes (simulation)

| Instruction | Accept | Completion | State effect |
|---|---|---|---|
| QLDI `QR9=(7,8,9,10)` | c=1 | `inst_done` c=2 | one commit; `QR9` correct |
| ROTC `QR6<-QR0` angle 1 | c=1 | `rote_done_tdm` c=5, `inst_done` c=6 | one commit; `QR6=(1,3,2,4)` |
| QSUB `QR5=QR0-QR1` | c=1 | `qsub_active` from c=2, `inst_done` c=4 | one commit; correct |
| Padé `0x2A` (lane 4) | c=1 | `rplu2_result_valid` c=555, `inst_done` c=556 | one commit; result 2 |

**Unsupported opcodes (40 tested, not 39 as stated in an earlier summary):** `00 01 02 03 04 05 06 07 08 10 11 12 13 14 15 17 18 19 1a 1f 20 21 22 ff 2b d6 d7 d8 70 76 77 48 4c 5a a0 30 31 60 61 e0`, including opcodes whose feature is off (`2b`, `d6-d8`, `70/76/77`, `48`, `4c`). **Every one** was accepted, produced exactly one `inst_done`, no commit, and no change in the Quadray register state. The core therefore acknowledges unsupported opcodes without executing them or reporting refusal (consistent with STATE-1, source).

## 3. Overlap cases (simulation)

Pairs are listed first instruction, then second ("intruder") at gap *g*; the second is sampled at `c=1+g`. "Anomaly" means a missing result, a missing completion or a misreport relative to the independent baseline. Gap 1 is excluded from the anomaly counts (§6).

| Ordering | Gap | Observation |
|---|---|---|
| ROTC, then QLDI (`QR9`) | 2, 3, 5-9 | both complete, both results correct, `done=2` |
| | **4** (QLDI on the `rote_done_tdm` cycle) | **ROTC result lost** (`QR6` wrong), ROTC never reports done, QLDI completes (`done=1`) |
| QLDI, then ROTC | 2-4 | both complete |
| ROTC, then ROTC | 5-7 | both complete |
| | **2** | `done=2` but the **first ROTC's result is missing** (misreport); second correct |
| | **3, 4** | first ROTC lost, `done=1` |
| QSUB, then QLDI | 3-5 | both complete |
| | **2** (QLDI while `qsub_active`) | **QLDI swallowed**: accepted, not executed, no done (`done=1`); QSUB correct |
| ROTC, then QSUB | 5-7 | both complete |
| | **2, 3** | **ROTC result lost**, QSUB executes (`done=1`) |
| | **4** (QSUB on the `rote_done_tdm` cycle) | **QSUB swallowed**, ROTC correct (`done=1`) |

After the ROTC/QLDI gap-4 collision the core is **not wedged**: a follow-up ROTC completes correctly. `rotc_debug_busy` stays 1 and `QR6` stays unwritten until a later completion.

## 4. Padé window collisions (simulation; separate because of the long latency)

The Padé instruction completes at c=555/556, so a second instruction from a single serial host would have to arrive hundreds of core cycles later (§7). Second instruction at gap *g* (sampled at `c=1+g`):

| Second instruction | Gap | Observation |
|---|---|---|
| QLDI | 100, 551-553, 555-557 | both complete, `done=2`, two commits |
| | **554** (sampled at c=555, the `rplu2_result_valid` cycle) | **QLDI swallowed**: `done=1`, one commit, `QR9` unwritten |
| ROTC | 553, 555, 556 | both complete |
| | **554** | **ROTC swallowed** (`rote_done_tdm` count 0), `done=1` |
| QSUB | 553, 555, 556 | both complete, `QR5` correct |
| | **554** | **QSUB swallowed**, `done=1`, `QR5` unwritten |

Mid-operation (gap 100) the second instruction executes normally while the first is still in flight.

## 5. Repeated identical instructions, boot and sidecar

- **Repeated identical (simulation):** the same QLDI at gaps 3 and 20, and the same Padé at gap 700, give two accepts, two `inst_done` and two commits. The commit events carry the same lane and data and differ only in timing. The core exposes no transaction identity, so two completions cannot be told apart by content.
- **Boot-not-ready (simulation):** with `boot_done=1`, READY is first seen around c=14. A QLDI strobe at c=1, 4, 7 or 10 after reset release is **lost without trace** (no accept, no done, no flag); at c=13 or later it is accepted. With `boot_done` held low a strobe is never replayed after READY.
- **Padé sidecar busy handling (simulation; positive control):** single `0x2A` completes at c=116, commit c=117. A second `0x2A` at the tested gaps 2-7, 10, 105 and 112-114 is rejected with exactly one `error` pulse and the first operation completes (one commit); at the tested gaps 115-122 and 200 both execute (two commits). The boundary between 114 and 115 is clean, with no swallow (gaps between the sampled values were not run). A second `0x2A` at gap 1 is ignored without an error pulse (§6).

## 6. Gap 1: continuous-valid limitation

At gap 1 the two strobes occupy consecutive cycles, so `inst_valid` is held high across them with different words. `inst_seen` treats a held level as one request and the second instruction is silently ignored (accept count 1, no error). This is a property of the level-based acceptance for any driver that holds the valid line; it is **not** an independent instruction-swallow collision and is not counted in §3-§4. The probes print a `NOTE` line in those scenarios. The anomalies at gap 1 in the expected outputs are marked `<-- ANOMALY` by the probe's generic check and are artifacts of this limitation.

## 7. Reachability from the actual SPI transport: UNRESOLVED

The cases above are **core-level** results under supplied one-cycle strobes. A `0xB1` frame is 80 SCK bit periods (command, 64-bit word, CRC), so strobes from one SPI master are at least that far apart. Converting to core cycles needs the actual relationship between SCK and the core clock (`clk_fast`, `A7_CLK_DIV_LOG2`, the spin's divider default, and the SPI slave's three-sample synchronizer limit). That relationship was **not established** and no ratio is assumed here. Consequently:

- the short-gap collisions (gaps 2-9 for ROTC/QSUB) are not shown to be reachable from a single SPI master, and remain relevant to any other driver of `inst_valid`;
- whether the Padé-window collision (gap 554) is reachable depends on that ratio and is **unverified**;
- the independent review's SCK-sampling-margin question is open.

## 8. Proposed single-outstanding H0 transaction contract (not implemented; no encodings)

Central invariant (proposed): every accepted instruction produces exactly one identifiable terminal outcome, and no invalid result is published as successful. Elements: a single outstanding instruction; explicit acceptance versus rejection; defined busy behavior; completion distinct from result-valid; terminal outcome of success, refusal or unsupported; freshness information for host readback (so repeated identical results are distinguishable); defined handling of commands during boot; no change to mathematical datapaths unless independently required. A host-side one-outstanding rule is insufficient unless the hardware makes completion observable. This document does not define the contract or any encoding.

## 9. Limitations

Four-state simulation of one core configuration; ordering and opcodes limited to those listed; stimulus bypasses SPI, CRC, the sidecar claim arbiter and the Artix-7 top; no timing, synthesis or board activity; the follow-up-ROTC check is one data point; the independent review's baseline differs from this one; the O6 inventory is a non-exhaustive census.
