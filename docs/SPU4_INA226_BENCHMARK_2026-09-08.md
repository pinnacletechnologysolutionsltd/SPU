# SPU-4 / RP2350 performance-only benchmark

Status: HALTED at timing preflight; **no comparative hardware timing result**.
Original application and hardware-promotion gates remain failed. Owner approved
performance-only replay and, subsequently, deterministic reconstruction of the
four-node weights which the historical pipeline did not save.

## Reconstructed workload

Artifact: [frozen data](bench_captures/2026-09-08_spu4_ina226_freeze.json).
SHA256: `6dcbb8e73597e0172531eca15baf3c2d666827e056c1eede45e59ab019188de6`.

`tools/freeze_spu4_ina226_benchmark.py` observes the unchanged trainer during the
original full pipeline execution, captures all five four-node models, and
requires the complete result hash to equal the historical
`3a801cd9f54ef36328cb9f07fc0e2ffa676eccd859e8f7012ad3f5fb0ea53bc1`.
Two independent executions produced byte-identical freezes. All 30 archived
capture hashes match the sealed manifest. The artifact includes source hashes,
five scalers, node labels and 120 held-out raw/feature/scaled/output records.

This establishes reproducible reconstruction from the inspected working tree,
not historical identity of unsaved weight bytes. It does not repair or promote
the failed application result (four-node balanced accuracy remains 76.67%).

## C baseline preflight

`software/benchmarks/spu4_ina226_kernel.c` implements the approved Q=0 profile:
exact integer half-even feature extraction, train-fold scaling/clipping, and
four-node squared-distance classification with lowest-node ties. No original
trainer, oracle, classifier RTL or capture contract changed.

| Check | Result | Scope |
| --- | --- | --- |
| Frozen windows | 120/120 | Features, scaling, winner, distance and label match |
| Feature controls | 1,005 pass | Half-even signs, extreme int32 samples and deterministic random windows |
| Distance controls | 1,000 pass | Independent existing edge oracle comparison |
| Unsigned bound / tie | Pass | 3,600,000,000 distance, lowest node wins |
| Undefined-behaviour sanitizer | Pass | Host C, halt-on-error enabled |
| Cortex-M33 `-O3` object compilation | Pass | Not linked firmware or measured execution |
| Existing full-chain RTL bench | 17/17 | Flash/loader/wrapper, existing discriminating oracle fixture |
| Existing interactive RTL bench | 36/36 | Actual UART consumer, existing oracle fixture and malformed inputs |

ARM object reports 2,384 text bytes, zero data/BSS; static function stack reports
48/32/24 bytes for features/scaling/classifier. These exclude linker/runtime
helpers, input/model state, interrupt stack and scheduling: they are **not**
whole-system memory measurements. No host runtime is used as a hardware claim.

The `TB_FILTER=spu4` runner was terminated after escaping into an unrelated
`test_regen_equivalence.py` simulation for almost five minutes. No aggregate
PASS claim is made. The two relevant RTL benches above were instead explicitly
compiled and executed with their actual consumer sources; their logs are in
`build/spu4_ina226_benchmark/`. They do not yet replay the frozen INA226 models.
Global `git diff --check` also reports pre-existing generated RP2040-build
whitespace changes; these were not cleaned up.

## Hardware preflight

Read-only JTAG detection identifies Tang GW5A-25 (IDCODE `0x1281b`) through
Sipeed debugger serial `2025030317`. Passive UART reads produced no data, so
neither loaded bitstream identity nor physical frequency is established.

Pico serial `9537d50959f3be46` reports Raspberry Pi Pico2 with RP2350,
MicroPython 1.28.0 and `machine.freq() = 150000000`. Its only listed root file,
`main.py`, was backed up to `build/spu4_ina226_benchmark/pico_backup/main.py`,
SHA256 `3746195c9c633bda281fb59d0e97f007d813ec85d738d8bc7651ccb9ca3af562`.
MicroPython execution was interrupted for inspection; no flash was changed.
This is a script backup, not yet a full firmware/flash backup.

The separate `tools/check_spu4_benchmark_timing.sh` rebuilds the actual unchanged
interactive top and edge wrapper into `build/spu4_ina226_benchmark/timing/`,
constraining the documented 50 MHz source rather than the old script's 12 MHz.
Final routed estimate: **44.32 MHz, FAIL at 50 MHz**, process exit 1.
Critical path reaches `u_som.u_som.best_idx`: 13.48 ns logic plus 9.08 ns routing,
22.56 ns total including setup. This is a timing-model result, not an observed
silicon misclassification or a physical oscillator measurement. No failed
bitstream was packed/programmed and no timing override was used.
Physical frequency and safe pin ownership still require confirmation. Do not
flash or accept timing from a failed route. J4 model flash presence and actual
Pico-to-Tang wiring have been requested; B3 must not have two TX drivers.

## Next boundary

Recommended minimal correction: a bench-only 25 MHz clock profile with matching
UART divisor and correctly constrained source/generated clocks, leaving the
classifier unchanged. This is a proposal, not an implemented or proven fix.

Resolve timing and physical preflight, preserve full Pico flash, implement the
matched firmware harness, then execute approved 1/4/16/64-stream measurements.
Retain raw distributions independently of the experimental 10 ms threshold.
No performance winner, product advantage, energy result or WCET claim yet.
Current classification: **INCONCLUSIVE**, benchmark not executed. The failed
50 MHz timing check prevents acceptance of measurements from that build; it
does not establish comparative weakness of the underlying SPU architecture.
Full implementation-completion gates remain pending; this is not a completed
benchmark. See the scoped contract in
`spu_strategy/spu4_ina226_performance_contract_2026-09-08.md`.

## Authorised 25 MHz continuation and MCU kernel preflight

Owner confirms external J4 flash fitted and wiring correct; this is owner
confirmation, not independent continuity verification. Owner authorised the
25 MHz bench-only profile. `spu4_ina226_bench25_top.v` divides the documented
50 MHz source by two and instantiates the unchanged interactive consumer with
CLK_FREQ=25000000 / CLKS_PER_BIT=217. Both clock nets are explicitly constrained
by `tools/spu4_bench25_clocks.py`. Routing is pending at this entry.

Existing interactive bench now supports BENCH25=1, including real UART wire
timing and a 40 ns divided-clock period assertion. Original profile passes
36/36; new profile passes 36/36. First new-profile attempt failed because the
old 60,000-source-cycle receive timeout was shorter than the 173,600 cycles
required by a 40-byte reply. Corrected timeout derives from that wire duration
plus twice the old startup allowance; expected response/oracle values unchanged.
Both failed and corrected logs remain in `build/spu4_ina226_benchmark/`.

Pico2 full 4 MB flash saved and verified before RAM execution:
`build/spu4_ina226_benchmark/pico_backup/full_flash.bin`, SHA256
`ab17b6a9c8d4205b4c911b2dab1c96b232ec5abe79037fa5aca65b720d1eca34`.
BOOTSEL confirms RP2350 A2 chipid 9537d50959f3be46. GPIO-free firmware executes
from SRAM (binary start 0x20000000); original MicroPython flash was not rewritten.
ELF SHA256 `324d1427d07446c791421d874c440fc213416b914f786e08a30e957a4dd12bbd`.
Build: GCC 16.2.0, Pico SDK 2.2.0, Release/-O3, one active core at configured
150 MHz. SysTick measures processor cycles with no SysTick interrupt; other
interrupts remain enabled. Serial output is emitted after each measured batch.

Raw evidence: [three MCU batches](bench_captures/2026-09-08_spu4_rp2350_kernel_preflight.json),
SHA256 `9b8296b5d505ccbd7bb7a7f072125406b97e36d1844bb0f52cc2b327824a734a`.

| Measured interval | Min | Median | p99 | Max |
| --- | ---: | ---: | ---: | ---: |
| Feature extraction + scaling (cycles) | 2412 | 2436 | 2440 | 2440 |
| Classifier call (cycles) | 111 | 111 | 111 | 111 |
| Prepared raw-window processing through label lookup (cycles) | 2527 | 2551 | 2555 | 2555 |

Each of three same-boot batches produces the same intervals and 120/120 exact
output matches. Back-to-back timer reads cost one cycle (not subtracted).
At configured 150 MHz, classifier interval is 0.740 us and median prepared-window
pipeline 17.007 us. These exclude model/window copy, acquisition, stream queues,
transport and session voting; NOT complete last-sample-to-label measurements.
120-case batch including setup/checking took 2262 us. Repeated batches are not
independent cold-start trials or new accuracy samples. No jitter/WCET conclusion
under interference, no throughput/scaling or FPGA comparison result yet.

Firmware ELF: text 56,392 B, data 224 B, BSS 5,968 B. SRAM execution also stores
code and frozen corpus in RAM; these figures are a diagnostic harness footprint,
not deployable classifier state or measured stack high-water.

Next hardware prerequisite: exact Pico GPIO assignments for UART and any flash
programmer connections. Existing documented UART GP4/GP5 overlaps the flash
programmer GP2–GP5; never infer that both can drive simultaneously. A precise
pin-definition question is pending. No external GPIO was driven by MCU preflight.

### Final bench25 timing: setup passes, HOLD FAILS — halted

Final routed setup estimate **36.29 MHz PASS at 25 MHz**, but nextpnr exits 1
for one **hold/min-time violation of approximately -0.14 ns**. Path starts at
`u_probe.tx_bits[0]`; reported clock skew is -0.78 ns. The routing log explicitly
reports only the source clock as globally routed, not `clk_25`. A generated-clock
distribution issue is the next hypothesis, not a proven physical failure.
Simply reducing the clock rate further is not a hold-time remedy.

Log `build/spu4_ina226_benchmark/bench25/pnr.log`, SHA256
`ab1499a9729df4a76a957f059d110207bdc2cb69d28f108f170001ac58ac469e`.
Synthesis JSON SHA256
`a0bfffccff9e75e033fa0e4220a96715a25968ae117ec0059535af6c6ad071cb`.
Script stopped before packing. No Tang image programmed; external weights
unchanged. `capture_spu4_bench25_boot.py` exists but was NOT executed.

Recommended smallest correction: explicit dedicated global-clock buffering for
the divided bench clock, using the existing board clock-buffer pattern, followed
by simulation and a fresh route in a separate directory retaining this failure.
No classifier or protocol semantics change. Halted for review before correction.
The checked test script `tools/test_spu4_bench25.sh` passes 36/36 in both profiles
and explicitly rejects FAIL/FATAL markers even if a simulator exits zero.

Overall comparison remains **INCONCLUSIVE / incomplete**. RP2350 kernel parity
and timing are observed; no FPGA frozen-model timing, transport measurement,
1/4/16/64-stream scaling, sustainable capacity, CPU utilisation or energy result
exists yet. The Pico currently runs the GPIO-free SRAM preflight waiting for R;
normal reset restores the unchanged MicroPython flash image.
### Authorised clock-distribution correction — passes

Question: can the single bench25 hold failure be removed solely by distributing
the divided clock through the Tang/Gowin global-clock resource?

Changed only `spu4_ina226_bench25_top.v`: added the Gowin nextpnr `CLOCK` net
attribute to `clk_25`. The divider, 25 MHz/217 UART parameters, interactive
consumer, classifier RTL, fixtures and expected responses are unchanged. The
backend inserted one BUFG at `X0Y21/BUFG0`. The routed net uses global clock
spines. It warns that the local divider-output-to-BUFG entry could not use a
dedicated route; it then routes that entry and completes with zero timing errors.

Fresh independent build directory:
`build/spu4_ina226_benchmark/bench25_global/`. Command:
`bash tools/build_spu4_bench25_global.sh`. Final route completed normally with
one warning and zero errors. No timing override, seed search, second workaround,
packing or hardware programming.

| Check | Result |
| --- | --- |
| Original consumer simulation | 36/36 pass |
| 25 MHz adapted consumer simulation | 36/36 pass |
| Repository verification gate | 227 PASS / 0 FAIL |
| BUFG usage | 1/18, `X0Y21/BUFG0` |
| Worst setup path | 27.675 ns |
| Setup slack at 25 MHz | **+12.325 ns** |
| Final setup Fmax | 36.13 MHz, PASS at 25 MHz |
| Hold timing | **PASS: zero hold/min violations; slack strictly >0 ns** |

The installed nextpnr `0.9-99-g4ace8952` prints exact negative hold slack on a
failure but does not emit the numeric minimum positive hold slack on a passing
route or in its JSON report. Therefore the honest reportable hold margin is
`>0 ns`, not a fabricated decimal. A read-only SDF extraction attempt from the
routed JSON failed an internal nextpnr bounds assertion and changed no design or
evidence; no second place-and-route or timing workaround was attempted.

Evidence hashes: `pnr.log`
`1bddd5faf97e0501e57f253a581b585f3fdb125e7716a8374d7dfb667726a21f`;
`timing.json`
`eb115de3668152957c9dd1be3020f4ce071df34411e100f746e974c7fcfd3ee1`;
routed JSON
`edc58a84f229e05539061ecabdd05ff73f7ccfa399863159fa3f8415d73c5354`.
Classifier and wrapper hashes remain `a9247007...` and `70b38a02...`.

Classification for this bounded ticket: the clock-distribution defect is fixed
for the routed timing model. This establishes timing closure for the bench25
profile and conformity with the repository's internal regression system, not
silicon operation or comparative SPU advantage. Stop after
reporting as instructed; do not advance to packing/hardware replay without owner
review.

### UART physical-path correction

The benchmark does not require a direct Pico GPIO UART connection. The existing
interactive consumer's `uart_rx=B3` and `uart_tx=C3` use the Tang dock's proven
bidirectional BL616 USB-CDC channel; the Sipeed debugger exposes JTAG on interface
0 and this UART on interface 1, normally the stable `...-if01-port0` device, at
115200 8N1. This avoids adding a second TX driver to B3.

The Tang onboard FPGA configuration flash/debugger, the external J4 model flash,
and the optional Pico bench adapter are distinct. The J4 model flash remains
fitted and is owned by FPGA pins G10/D10/B10/C10 during hydration. Pico GP4/GP5
overlap exists only in the optional adapter: GP4/GP5 select either its flash
programmer MISO/CS role or its UART TX/RX role. With no Pico UART wiring and no
programmer attached to the fitted model flash, there is no GP4/GP5 conflict.

Safe replay topology: Tang debugger USB provides SRAM programming and UART;
Pico USB CDC independently controls the GPIO-free RP2350 baseline. No direct
Pico-to-Tang wire is required. This resolves the physical-path blocker but does
not itself execute or validate the benchmark replay.

### Frozen replay attempt — halted at first parity gate

Packed only the timing-closed `bench25_global` routed image (SHA256
`6b7022f236813695931464e2be946724a0d1775c1633f30c5540d861f3f8e8f6`) and
SRAM-loaded it successfully. A fresh BL616 UART capture returned the required
`SOM:H N=0 Q=00000000 S=04 L=000 I=1020` hydration record.

The first frozen fold-0 window then failed exact parity: expected node 2,
distance `0x03C58E94` (63,278,740), label 0; hardware returned node 0,
distance `0x42FF6EEB` (1,124,036,331), with status `0x06` and reported latency
7 clocks. Host write/flush-to-complete-line observation was 11.364638 ms, but
is not an accepted latency distribution because the parity gate failed.

Stopped immediately: no second query, flash programming, 1/4/16/64 scaling,
RP2350 comparison or benchmark classification. Hydration establishes successful
loading of *some* 64-byte model, not its identity; repository state had not
established that the fitted flash contained frozen fold 0. Raw evidence:
`docs/bench_captures/2026-09-09_spu4_ina226_bench25_halt.json`.

Classification: **E — INCONCLUSIVE**. This is a model-identity/parity preflight
failure, not evidence for or against SPU performance.

### Pico 2 model-flash reader prepared

With the model module still disconnected, built the existing
`rp2040_flash_pmod.c` source for `PICO_BOARD=pico2` using Pico SDK 2.2.0 and
flashed/verified it on RP2350 A2 chip ID `9537d50959f3be46`. UF2 SHA256:
`7a3bb6fcece03df0431ba427a15b58add593e9628e21325ef6748f0c24fe0149`.
The prior full 4 MiB MicroPython backup remains at
`build/spu4_ina226_benchmark/pico_backup/full_flash.bin`, SHA256
`ab17b6a9c8d4205b4c911b2dab1c96b232ec5abe79037fa5aca65b720d1eca34`.

USB diagnostic after boot: `OK PONG`; pins `MISO=GP4 CS=GP5 SCK=GP2
MOSI=GP3 baud=100000`; `JEDEC=FFFFFF`, expected because no flash was attached.
Next boundary is physical attachment of the unpowered J4 model module to those
pins, followed by read-only 64-byte capture at `0x120000`. No model bytes have
been read or written yet.

### J4 model identity and frozen fold-0 programming

Read-only capture identified the attached flash as JEDEC `EF4018`. Its original
64-byte slot at `0x120000` had SHA256 `6e0bee113930d9ed...d406e3cd` and matched
the repository `oracle_fixture` bit-for-bit. It was not the remembered
tensegrity model. It differed from frozen fold 0 in 32 of 64 bytes (first:
`0x00 00->63`; last: `0x3F 32->00`).

Before erase, the complete 4 KiB sector was preserved (SHA256
`90d66d0e3ca97828c...991ad4ae`); every byte after the 64-byte model slot was
`0xFF`, so no adjacent data was at risk. Under the existing frozen-benchmark
authorization, programmed only the exact generated fold-0 image at `0x120000`.
The programmer verify passed, and a separate 64-byte readback matched the source
bit-for-bit at SHA256 `7cd242bf445a9cf0...e0b0e52`.

Evidence: `docs/bench_captures/2026-09-09_spu4_j4_model_identity.json`. This
establishes model-flash identity only. No classifier query or benchmark replay
was performed after programming; the earlier comparison remains **E —
INCONCLUSIVE** until a separately authorised replay.

### Fold-0 consumer-path parity preflight

After returning the model module to Tang J4, SRAM-loaded only the timing-closed
`bench25_global` image. Loading succeeded and the actual BL616 UART consumer
emitted fresh hydration `SOM:H N=0 Q=00000000 S=04 L=000 I=1020`.

Repeated the exact frozen fold-0 case that had exposed the wrong flash model.
Expected node 2 / quadrance `0x03C58E94`; Tang returned
`SOM:D N=2 Q=03C58E94 S=06 L=007 I=1020`. Exact node/distance parity therefore
passes for this one window through the real flash hydration and classifier
consumer path. Evidence:
`docs/bench_captures/2026-09-09_spu4_ina226_fold0_parity_preflight.json`.

The observed single host round-trip was 17.879220 ms, but it is explicitly not
an accepted latency distribution. No wider replay or 1/4/16/64 scaling case was
run. Comparative classification remains **E — INCONCLUSIVE**.

### Complete fold-0 parity sweep; performance contract halt

The complete 24-window frozen fold-0 sweep passed 24/24 exact node and distance
comparisons through the real flash-hydrated Tang consumer, with zero malformed
responses. Raw compact evidence:
`docs/bench_captures/2026-09-09_spu4_ina226_fold0_window_sweep.json`.

The consumer's first post-hydration query reported `L=007`; every later valid
query reported `L=000`. Targeted RTL inspection explains this as a real
integration race: the wrapper holds `done` until an accepted start, while the
interactive dispatcher samples that stale level as it enters `S_RUN`. UART is
slow enough that the newly computed node/distance updates before those fields
are serialized for the exercised cases, so parity passes, but `L` is not a
valid repeated classifier-latency measurement. Production RTL was not changed.

Halted before folds 1-4 or performance interpretation. The active contract
requires 1/4/16/64 aligned/staggered bounded-queue measurements but does not
freeze queue depth, exact arrival schedule, repetitions, timestamp boundaries,
CPU-utilisation method, or numeric A/B/C/D/E decision gates. No complete stream
harness exists; the RP2350 artifact is explicitly a GPIO-free kernel preflight.
Choosing these values now could change capacity/deadline outcomes and would not
be executing a predefined benchmark. The Pico is also not presently enumerated
after its flash-programmer role. Comparative status remains **E —
INCONCLUSIVE** pending a minimal contract amendment and RP2350 USB reconnection.

### Completion-arm correction — timing pass, physical parity halt

The single authorised probe-only correction added one completion-arm bit to the
bench25 consumer. A request can complete only after the wrapper has accepted it
and exposed `busy && !done`, preventing the prior query's level-held `done` from
satisfying the new request. Classifier, wrapper, weights, clocking, fixtures and
UART format were unchanged.

Both consumer profiles passed 50/50 simulation checks. The regression covers
11 accepted queries without reset, including at least three stale-held-`done`
boundaries; every query preserves exact result parity, produces exactly one
fresh completion, and reports six accepted-to-completion clocks.

The complete registered repository gate passed before hardware use: Verilog
163/163, C++ 12/12 and Python 52/52 (227 PASS / 0 FAIL). A fresh Tang route in
`build/spu4_ina226_benchmark/bench25_completion_arm/` completed normally:
35.02 MHz routed Fmax, 28.55 ns worst setup path, +11.45 ns setup slack at
25 MHz, no hold/min violation, zero timing errors and the one already accepted
divider-to-BUFG dedicated-entry warning. Packed image SHA-256:
`7a57be49d6164d838cd9ba49b9e13a1feb64f250312378a425bf237622dc448b`.

SRAM load succeeded and fresh boot output contained
`SOM:H N=0 Q=00000000 S=04 L=000 I=1020`. The first frozen fold-0 query then
returned `SOM:D N=3 Q=04433EA4 S=06 L=006 I=1020`; expected was node 2 and
`Q=03C58E94`. Thus the correction produced a fresh, credible latency field but
physical classifier parity failed. Per the frozen stop condition, no second
query, diagnostic workaround, RP2350 run or performance measurement followed.

Raw evidence:
`docs/bench_captures/2026-09-09_spu4_completion_arm_boot.json` and
`docs/bench_captures/2026-09-09_spu4_completion_arm_fold0_acceptance.json`.
Classification remains **E — INCONCLUSIVE**. The mismatch cause is unresolved.
