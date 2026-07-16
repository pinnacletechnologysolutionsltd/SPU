# SPU Spin Catalog

A **spin** is a named, reproducible bitstream configuration — a specific
subset of SPU modules synthesized for a specific board (normative
definition: `knowledge/SPU_LEXICON.md`). A **probe** is a spin whose
purpose is one piece of silicon evidence, not end-user function.

**Catalog rules:**
- The *Status* column must agree with `AGENTS.md` and
  `docs/hardware_evidence.md`. Silicon claims not traceable there are
  wrong; fix the claim, not the evidence doc.
- Every product-candidate spin must have a **first-hour story**: what a
  stranger with the board and a Pico does in their first hour. If the
  story can't be written, the spin is a probe and belongs in §2.
- Status vocabulary: `silicon` (verified on the named board), `TB`
  (testbench-verified only), `built` (bitstream exists, board run
  pending), `blocked` (does not fit / missing dependency), `direction`
  (no RTL yet).

---

## 1. Product-candidate spins

These are the spins that could plausibly be flashed onto an evaluation
board for someone else. None of them yet meet the full ecosystem checklist
in §4 — "product-candidate" describes intent, not readiness.

| Spin | Board | Modules | Resources | Status |
|---|---|---|---|---|
| ROBOTICS | Wukong A7 100T | QLDI/QSUB/ROTC 0–5, six-step closure, J11 SPI | see build log | silicon (13/13, `ARITHMETIC_BLAZE: PASS`) |
| LUCAS | Wukong A7 100T | Lucas Phinary MAC + CE-paced SPI sidecar | 5,073 LC, 120 DSP, 4.41 MHz | silicon (PSCALE/PCHIRAL/PMUL/PINV over J11) |
| RPLU2PADE | Wukong A7 100T | A₃₁ inverter, SOM/BMU, BTU, Padé [4/4] | 72 DSP, 34% LUT | silicon (`RPLU2PADE_J11: PASS`) |
| SU3SHARE | Wukong A7 100T | SU3 sidecar + RPLU2 config/QR, one shared M31 multiplier | see build log | silicon (both paths pass on one bitstream) |
| SOM-SIDECAR | Tang 25K → smaller fabrics | standalone SOM edge classifier (`build_25k_spu13_som_sidecar.sh`, top module `spu13_tang25k_som_sidecar_top.v`) | 12,865 LUT4 (55%), 8 BSRAM, 0 DSP; 79.38 MHz Fmax @ 50 MHz target | silicon: writable SPI path, fixed-434-clock exact BMU, and C3 UART proven. Reproducible Iris demo passes 150/150 FPGA/oracle winners and 147/150 semantic labels (98.0%); checked map and one-command runner are `software/models/iris_som_v1.json` and `tools/iris_som_demo.py`. |
| SPU4-SENTINEL | Tang 25K → smallest fabrics | SPU-4 core, Davis gate, whisper v0 | ~400 LUT | silicon (2026-07-08, `SPU4:P A=0000 B=0155 C=0155 D=0155`) |

**First-hour stories:**

- **ROBOTICS** — from a Pico/RP2350 over SPI, drive exact rotor chains
  (ROTC 0–5) and verify the six-step closure returns the bit-identical
  start state. The hook: forward kinematics with *zero* accumulated error,
  demonstrable in an afternoon with a logic analyzer.
- **LUCAS** — run a million-step φ-scaling loop and read back zero drift;
  run the same loop in `double` on the host and watch it drift. The hook
  is the side-by-side.
- **RPLU2PADE** — evaluate Padé [4/4] approximants over A₃₁ and check
  results bit-for-bit against `software/lib/a31_field.py`. Weakest
  first-hour story of the six — it needs a killer input table (this is
  where the sound-module idea would land, see §3).
- **SU3SHARE** — resource-sharing demo: two engines, one multiplier, both
  pass on the same bitstream. Story is for FPGA engineers, not end users.
- **SOM-SIDECAR** — hydrate weights over the southbridge, stream feature
  vectors, get deterministic BMU classes with index-ordered tie-breaking:
  the same answer every run, every board, forever. Per the 2026-07-08
  decision this is the flagship small-fabric spin — no manifold, no RPLU,
  targets fabrics below the 25K.
- **SPU4-SENTINEL** — the ~400-LUT edge node: Davis-gate telemetry and
  the whisper `SANE` beacon on the smallest fabrics. Pairs with
  SOM-SIDECAR as the edge tier of the Arlinghaus constellation
  (`knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7 and `knowledge/SPU4_ARCHITECTURE.md`).

## 2. Evidence probes (not products)

Tang Primer 25K, one root-level script each:

| Script | Proves | Status |
|---|---|---|
| `build_25k_blinky_uart.sh` | bench sanity: bitstream load, clock, LEDs, BL616 USB-CDC UART leg | silicon |
| `build_25k_spu13_math_probe.sh` | QLDI/QSUB, QR regfile, hex projection over UART | silicon |
| `build_25k_spu13_southbridge_link.sh` | RP2350↔FPGA SPI link, no compute (~350 LUT) | silicon |
| `build_25k_spu13_rplu2_arith_probe.sh` | QLDI/QSUB + RPLU2 config over SPI (6,282 LUT, 27%) | silicon |
| `build_25k_spu13_rplu2_consume_probe.sh` | 149-record table consumption, checksum `0x0AA480E7` | silicon |
| `build_25k_spu13_lucas_mac_probe.sh` | Lucas MAC zero-drift standalone (~200 LUT) | silicon |
| `build_25k_spu13_rotc_probe.sh` | ROTC 0–5 standalone | silicon (via A7 ROBOTICS; Tang run per evidence doc) |
| `build_25k_spu13_six_step_probe.sh` | six-step robotics closure | silicon (via A7 ROBOTICS; Tang run per evidence doc) |
| `build_25k_spu13_som_probe.sh` / `som_bmu` / `som_hydrate` / `som_southbridge` | SOM classification, BMU array, BRAM hydration, hydrate+classify over SPI | silicon (SOM/BMU Tang-proven; see evidence doc for per-script runs) |
| `build_25k_spu4_probe.sh` | SPU-4 Sentinel first silicon | silicon (2026-07-08) |
| `build_25k_series_stream_probe.sh` | eps³ hyper-Catalan series eval, 8 golden vectors, one shared multiplier | **blocked** — combinational M31 multiplier ≈305% LUT on GW5A; needs sequential variant or Gowin DSP wrapper |
| `build_25k_sdram_min_probe.sh` | SDRAM controller | retired — external module DQ[10] fault, board healthy |
| `build_25k_southbridge_spi_probe.sh` | SPI-only southbridge telemetry | see script header — reconcile with AGENTS.md |
| `build_25k_spu13_lucas_phslk_probe.sh` | Lucas PHSLK | **untracked** — reconcile with AGENTS.md or retire |
| `build_25k_spu13_neuro_guard_probe.sh` / `neuro_sidecar_probe.sh` | neuro-safe guard / sidecar adapter | **untracked** — reconcile with AGENTS.md or retire |

Wukong Artix-7:

| Spin | Proves | Status |
|---|---|---|
| SOMPROBE (`build_a7.sh 100t somprobe`) | Tang-proven SOM fixture on A7 — same golden line `SOM:P T:2 B:6 E:00` on both vendors = cross-vendor determinism proof | built, awaiting board run (~2.6k LUT, 84 DSP, 4 BRAM) |
| TENSEGRITYPROBE (`build_a7.sh 100t tensegrityprobe`) | seven frozen TGR1 admission fixtures, including exact strut intersection and type-uniform Z[phi] equilibrium | silicon PASS 2026-07-14: `TGR:P V:7 E:00` |
| TENSEGRITYLINK (`build_a7.sh 100t tensegritylink`) | B2 transactional TGR1 BRAM hydration, synchronous guard replay, coherent B3 status, and rollback | Partial silicon 2026-07-16: J11/SD/B2/B3/parser proven and canonical commits with intersection-only or equilibrium-only images; full combined image remains `verify_busy` after all 468 bytes, so atomic combined admission/rollback are not yet proven. Refactor into explicit stages before another full build. |

**A7 spin names not in the product/probe tables above** (`multimedia`,
`intelligence`, `full`, `sensor`, `rplucfg`, `rplu2core`, `rplu2`,
`rplu2live`, `som`, `custom`, plus `su3`): already reconciled in
`AGENTS.md`'s "A7 spin reconciliation" table (2026-07-08) — `full`/
`multimedia`/`intelligence`/`sensor` are direction-only aspirational
spins, `som`/`su3`/`rplucfg`/`rplu2core`/`rplu2`/`rplu2live` are all
superseded by named spins already in this catalog, `custom` is a
build-time meta option. This note previously called that reconciliation
an open action item; it wasn't, as of 2026-07-08.

## 3. Future spins (direction only — no status claims)

| Spin | Board | Idea | Dependency |
|---|---|---|---|
| CLUSTER-GOV | Wukong A7 | SPU-13 governor + cluster bridge (Tang = satellite, per 2026-07-08 decision) | whisper v1 frame spec first |
| CLUSTER-SAT | Tang 25K / smaller | SPU-4 + cluster bridge + whisper | `spu_node_link` on silicon (needs two boards) |
| SOUND | A7 or 25K | Padé/RPLU2 rational synthesis → `spu_i2s_out.v` (exists, peripherals tree) | RPLU2PADE + an audio demo program; would give RPLU2PADE its first-hour story |
| VECTOR-GPU | A7 | rasterizer + fragment pipe (TB-verified) + IVM visualization | display HAL bring-up; large scope |
| SERIES-STREAM | Tang 25K | eps³ series evaluator probe → spin | sequential M31 multiplier or Gowin DSP wrapper |

## 4. What "flashable to an eval board" requires

A spin becomes a product when all four exist. Current gap table:

| Requirement | State today |
|---|---|
| Southbridge host path (RP2350 or any SPI master) | exists for A7 J11 + Tang spins; protocol versioned as v1 with a compatibility promise, `docs/SOUTHBRIDGE_SPI_PROTOCOL.md` (done 2026-07-08) |
| Host library (Python wrapper over the 8 SPI opcodes) | **done**: `software/spu_host/`, installable with `python3 -m pip install -e .`; typed client + `spu-host` CLI |
| Per-spin example program with expected output | ROBOTICS, LUCAS, TENSEGRITY, and SOM-SIDECAR examples exist under `tools/`; other product candidates remain open |
| Doc page per spin (flash command, wiring, first-hour walkthrough) | SOM-SIDECAR page complete (`docs/SOM_SIDECAR_QUICKSTART.md`); remaining spins open |

Remaining highest-leverage evaluator item is the physical-sensor SOM path:
INA226 acquisition, deterministic temporal features, and the versioned `SOM1`
decision-evidence frame.

---

*CC0 1.0 Universal, like the rest of `docs/`.*
