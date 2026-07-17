# Tensegrity Balancer Handover — 2026-07-15/16/18

## Stopping point

The seven-fixture Artix guard probe is silicon-proven with
`TGR:P V:7 E:00`. The standalone `TENSEGRITYLINK` transport is implemented and
regression-tested, and its SPI/SD/table path has now run on the board. The full
combined admission path is **not** silicon-proven: a complete canonical B2 load
reaches guard verification but the original combined intersection+equilibrium
image remains `verify_busy` indefinitely and never commits the staging bank.

The 2026-07-18 tranche removes indefinite busy as an allowed outcome and
structurally fixes the monolithic implementation pressure. The coordinator
publishes a stable verifier-service stage in B3, applies a bounded watchdog,
and atomically rolls back with loader error 10 if a service does not return.
Intersection and equilibrium now use explicit term-serial Z[phi] multiplier
services. This cuts the combined image from 108 to 66 DSPs and turns a
non-closing route into a clean implementation while preserving exact results.

Two reduced diagnostic images establish the boundary:

- full transport/parser/replay + intersection, equilibrium bypassed: canonical
  vector 100 commits `BALANCED/F_NONE` with 12 nodes and 30 edges;
- full transport/parser/replay + equilibrium, intersection bypassed: canonical
  vectors 100 and 101 commit the same verdict;
- full transport/parser/replay + both engines: canonical data is received and
  length-checked (`received=expected=468`) but verification does not terminate.

This isolates the open issue to the combined implementation. It does not
invalidate either exact predicate or the transactional loader, but it blocks a
claim that B2/B3 plus the complete guard are proven atomically in silicon.

`TENSEGRITYLINK` provides:

- B2 transactional, length-delimited TGR1 table hydration;
- synchronous replay through the real tensegrity guard;
- commit on complete success and rollback on parse/guard failure;
- B3 coherent status readback;
- a status-hold/pending-result interlock, so a guard completion coincident
  with a long B3 transaction cannot mix vector and verdict generations.
- stage-coded verifier telemetry and a bounded timeout that preserves the
  previous active bank/verdict rather than leaving `verify_busy` asserted.

The RTL contract supports an atomic host-proposed full-table load, reverify,
and commit/rollback cycle. The current board evidence proves that contract only
with one exact engine enabled at a time. It is not an autonomous motion
controller: proposal generation and actuator mapping still require an explicit
control law.

## Verification snapshot

- `TB_FILTER=tensegrity python3 run_all_tests.py`: all six tensegrity RTL
  benches pass; 47 total focused-suite categories/tests and 0 failures.
- Full `python3 run_all_tests.py`: 170/170 total, including 129/129 Verilog.
- Base `spu_spi_slave_tb`: T1a through T8b pass, preserving legacy commands.
- Tensegrity ABI: 7/7.
- Frozen-vector suite: 7/7.
- Exact balancer oracle: 44/44.
- Protocol oracle: 9/9.
- Host parser: 46 checks, 0 failures.
- First-hour tensegrity demo: 16 checks, including explicit stuck-stage
  reporting.
- RP firmware target compiled cleanly.
- `bash -n hardware/boards/artix7/build_a7.sh`: pass.
- `git diff --check`: pass at handover.

The sidecar regression explicitly holds B3 active across `guard_done`, proves
that the prior status remains coherent, then releases B3 and proves that the
pending result commits.
It also mechanically holds the intersection service's completion low, proves
watchdog error 10 and stage `0x85`, proves the previous transaction remains
active, then proves a clean canonical reload recovers.

## Historical combined Artix build

Build command:

```sh
A7_FREQ=25 A7_SEED=1 bash hardware/boards/artix7/build_a7.sh 100t tensegritylink all
```

Seed-1 result used for the first board attempt:

- route closed at iteration 38 with zero overuse;
- 24,675 `SLICE_LUTX` (19%);
- 7,655 `SLICE_FFX` (6%);
- 108 `DSP48E1` (45%);
- one `RAMB18E1`;
- guard-domain Fmax 40.16 MHz;
- system-domain Fmax 318.78 MHz.

Bitstream at that point: `build/spu_a7_100t_TENSEGRITYLINK.bit`
(3,825,928 bytes). Diagnostic builds subsequently overwrote this path; do not
assume the current file has the historical hash below.

SHA-256:
`a515381a8b90ceba836da83c7fe80bf719033717d72458cfb8297d7753d63463`

## Bench evidence — 2026-07-16

The remapped J11 link initially read all `0xFF`. After reseating the connector,
the standalone loopback image produced repeated 16/16 exact passes, including
runs 186 through 192. The physical link is therefore healthy.

The RP2350 SD path initializes successfully and loads
`00_canonical_balanced.tgr` (468 bytes). With the equilibrium-only diagnostic
image, the observed console sequence was:

```text
OK tgrload bytes=468 vector=101
OK tgrstatus version=1 state=2 fault=0 vector=101 flags=0x08 \
  error=0 nodes=12 edges=30 received=468 expected=468
```

The intersection-only image returned the same terminal shape for vector 100.
The full combined image instead remained at `state=0 fault=0 vector=0`, with
`flags=0x04` (`verify_busy`), no active nodes/edges, and
`received=expected=468`. Repeating immediately after FPGA reset and lowering
the guard-domain build constraint did not change that outcome.

## Bounded verifier diagnostic — 2026-07-18

B3 byte 3 is no longer reserved. It reports the current coarse service:
parser/replay (1), topology (2), connectivity (3), local guards (4), exact
intersection (5), exact equilibrium (6), decision (7), or terminal result (8).
If the one-million guard-clock watchdog expires, bit 7 is added to the last
service and loader error 10 is latched. At the 25 MHz guard cadence this is a
40 ms bound; valid regression vectors complete with more than a 10x margin.

The timeout path clears the guard, releases `verify_busy`, and preserves the
active bank, vector, verdict, node count, and edge count. It therefore turns
the previous unbounded board symptom into falsifiable evidence: for example,
`stage=133` (`0x85`) means the exact intersection service failed to return.
The host library, RP2350 `tgrstatus`, protocol document, and first-hour demo
all carry the new field while remaining compatible with older console lines.

The first stage/watchdog monolithic rebuild was deliberately stopped at router
iteration 38 with 392 overused resources: reproducing an hours-long seed hunt
was no longer useful evidence. `spu13_zphi_mul_serial.v` now evaluates the four
exact field-product terms over four cycles behind captured inputs and an
explicit `start/busy/done` contract. Both intersection and equilibrium retain
their former exact coefficient widths and terminal semantics. A dedicated
signed-arithmetic/latency bench and all pre-existing guard fixtures pass.

The refactored seed-1 image routes cleanly at iteration 41 with:

- 25,120 `SLICE_LUTX` (19%);
- 8,972 `SLICE_FFX` (7%);
- 66 `DSP48E1` (27%; down from 108/45%);
- one `RAMB18E1`;
- guard-domain Fmax 42.23 MHz at the 25 MHz operating cadence;
- system-domain Fmax 336.25 MHz.

Packed bitstream SHA-256:
`478e206c65fa5f18c44e7604ca27139e5d65f551ac91a170d8beb78baa4c7c57`.

The fresh image and RP2350 firmware were loaded on 2026-07-18. A live B3 read
returned `stage=0`, proving the updated SPI/status/firmware field in silicon.
The canonical combined verdict is still pending because the currently attached
SD interface reports `ERR no SD card`; `sdprobe` sees GP12 MISO floating. Until
the card/module is reseated and a real combined-image run either commits or
reports a bounded stage-coded timeout, do not claim the full atomic verifier as
silicon-proven.

## Wiring retained for future bench work

| Signal | Wukong J11 / package pin | RP2350 |
|---|---|---|
| CS# | J11-7 / J4 | GP1 |
| SCK | J11-8 / G4 | GP2 |
| MOSI | J11-9 / B4 | GP3 |
| MISO | J11-10 / B5 | GP0 |

Fit 100-ohm series resistors in all four SPI wires. Share ground, but do not
join independently powered 3.3 V rails. Never leave the RP2350 powered and
driving while the Wukong is unpowered.

## Engineering decision

Do not return to blind place-and-route seed hunting on the monolithic combined
image. Term-serial exact multiplication is now the baseline: it preserved the
field contract and removed 42 DSP placements. Retain these explicit
components:

1. transport/table store;
2. parser/schema validator;
3. topology/connectivity guard;
4. local edge guard;
5. intersection service;
6. equilibrium service;
7. admission coordinator and atomic commit/rollback.

Keep unit/probe builds for each service, but deliver the verifier as one
integrated bitstream over one inactive snapshot. Preserve explicit
`start/busy/done`, result/fault, vector ID, and watchdog boundaries. Further
cross-service multiplier sharing is optional optimization, not a blocker.

The immediate product-development priority is the already-proven rational SOM
classifier/sidecar. Tensegrity componentization should resume after the SOM v1
checkpoint rather than consuming more time in combined diagnostic builds.

## After the componentized link proof

The next major balancer task is the active proposal/actuation controller. Do
not infer its semantics from the admission guard. First specify:

- the controlled coordinates and physical actuator mapping;
- the candidate-motion primitive (for example direct TGR coordinate updates,
  ROTC/IROTC-derived moves, or both);
- step-size, convergence, and deterministic cycle-budget rules;
- how failed proposals roll back and how no-progress/fault states surface;
- the oracle fixtures that define successful balancing trajectories.

Other deferred guard work includes slenderness, precession detection, and
continuous two-shell/jitterbug behaviour.

## Source landmarks

- `hardware/rtl/core/spu13/spu13_tensegrity_sidecar.v`
- `hardware/rtl/peripherals/io/spu_spi_slave.v`
- `hardware/boards/artix7/spu_a7_tensegrity_link_top.v`
- `hardware/boards/artix7/spu_a7_tensegrity_link.xdc`
- `hardware/tests/spu13/spu13_tensegrity_sidecar_tb.v`
- `hardware/tests/spu13/spu13_tensegrity_transport_tb.v`
- `docs/TENSEGRITY_BALANCER_FEASIBILITY.md`
- `docs/SOUTHBRIDGE_SPI_PROTOCOL.md`
- `docs/hardware_evidence.md`

This tranche is intended to be checkpointed independently from unrelated RPLU
paper, experimental-ISA, SOM-study, and boot-diagnostic edits that remain in
the working tree. Preserve those unrelated edits; do not clean or reset the
tree when resuming.
