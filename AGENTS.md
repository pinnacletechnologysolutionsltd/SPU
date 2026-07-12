# Repository Guidelines

## Strategic Context

The SPU-13 is a **deterministic rational-field processor** — its architecture is exact arithmetic over Q(√3) and Z[φ]/L_p, zero floating-point, zero branches in hot paths, deterministic cycle counts. This makes it a general-purpose geometry engine suitable for any application that demands bit-exact results and predictable timing:

- **Rational robotics and kinematics** — Pell forward/inverse chains, exact FK/IK without transcendental approximation
- **Rational SOM/BMU clustering** — field-squared quadrance BMU, no floating-point distance metrics
- **RPLU v2 rational approximants** — [4/4] Padé evaluation over A₃₁ with Mersenne prime arithmetic
- **Lucas Phinary MAC** — exact Z[φ]/L_p arithmetic for Fibonacci-phase systems

The quantum classical-control application (Fibonacci anyon braid-word compilation, syndrome decoding) is a natural downstream use of the same deterministic Z[φ]/L_p arithmetic — the architecture does not change whether the target is robotics, clustering, or quantum control.

Development strategy: Tang Primer 25K for probe/bring-up, Wukong Artix-7 100T for safety-critical full builds with ECC SECDED, RNS parity, and CRC-8 integrity layers. Funding strategy: dual-track NLnet (open-infrastructure) + MBIE (NZ deployment). ArXiv papers first, then grant applications, then Kintex-7 full-stack, then OSHWA ECP5-85K reference design.

## Project Structure & Module Organization

```
hardware/               FPGA RTL (Verilog)
  rtl/core/shared/      Shared cores — ALU, sequencer, register files, Davis gate, ISA decoder
  rtl/core/spu13/       SPU-13 Cortex: M31/A31 arithmetic, unit inverter, SOM, BTU, register file
  rtl/core/spu4/        SPU-4 Sentinel (Quadray satellite): Euclidean ALU, boot master, sovereign bus
  boards/               Per-target synthesis scripts & board tops
  tests/                Verilog testbenches (*_tb.v)
software/               Host-side tooling
  spu_vm.py             Soft-CPU emulator
  spu_forge.py          Unified CLI — simulate, assemble, test, build
  programs/             .sas demonstration programs
  lib/                  Sovereign Geometry Library (Q(√3,√5,√15))
tools/                  ROM generators, RPLU loaders, visualizer
hardware/rp2040/        RP2040 bench utilities, including SPI flash PMOD programmer
knowledge/              Architecture specs, ISA reference, math foundations
docs/                   Design guides and bring-up runbooks
```

## Build, Test, and Development Commands

| Command | Purpose |
|---|---|
| `python3 run_all_tests.py` | Discover and run all Verilog `*_tb.v` testbenches via `iverilog`/`vvp`, plus C++ `*_test.cpp` and Python VM tests |
| `TB_FILTER=spu13 python3 run_all_tests.py` | Run only testbenches matching a prefix for faster triage |
| `bash build_25k.sh` | Synthesise, place-and-route, and generate bitstream for Tang Primer 25K |
| `bash build_gw1n1.sh` | Full bitstream for Tang Nano 1K |
| `python3 software/spu_forge.py simulate <program.sas>` | Simulate a .sas program on the Python VM |
| `bash build_25k_spu13_math_probe.sh` | Synthesise, P&R, bitstream for SPU-13 math probe on Tang 25K |
| `bash build_25k_spu13_southbridge.sh` | Full southbridge build (MATH=1 + RPLU_V2=1 — too large for 25K at 89% LUT) |
| `bash build_25k_spu13_southbridge_link.sh` | SPI link-only probe (~350 LUTs) — validates RP2350↔FPGA SPI |
| `bash build_25k_spu13_rplu2_arith_probe.sh` | RPLU2 arithmetic probe (6,282 LUTs, 27%) — QLDI/QSUB/RPLU2 config |
| `bash build_25k_spu13_lucas_mac_probe.sh` | Lucas Phinary MAC standalone probe (~200 LUTs) — zero-drift proof |
| `bash build_25k_spu13_rplu2_consume_probe.sh` | RPLU2 flash consume-probe (149-record table verification) |
| `bash build_25k_spu13_satellite_aggregator_probe.sh` | 13-satellite whisper aggregator probe (7,855 LUTs, 34%) — 4 driven emitters + 9 deadman-idle lines, self-checking, `SAGG:P W:2 I:9 E:00` on UART |
| `openFPGALoader -b tangprimer25k -f build/tang_primer_25k_spu13_math_probe.fs` | Flash bitstream to Tang Primer 25K |
| `python3 tools/flash_layout.py` | Generate SPI flash image from .bin files (Wildberger library) |
| `minipro -p W25Q128JV -r build/flash_backup.bin` | Read SPI flash backup (preserve bootloader) |
| `cmake --build build/rp2040_flash_pmod --target rp2040_flash_pmod -j` | Build RP2040 USB-to-SPI flash PMOD programmer |
| `picotool load -f build/rp2040_flash_pmod/rp2040_flash_pmod.uf2 && picotool reboot` | Load RP2040 flash PMOD programmer |
| `tools/rp2040_flash_pmod.py --port /dev/ttyACM3 id` | Read PMOD SPI flash JEDEC through RP2040; must report `EF4018` before writes |
| `python3 tools/gen_rplu2_tables.py --profile default --output tools/build/rplu2_boot_tables.bin` | Generate corrected 149-record RPLU2 default table blob |
| `tools/rp2040_flash_pmod.py --port /dev/ttyACM3 write tools/build/rplu2_boot_tables.bin --offset 0x110000` | Program corrected RPLU2 table blob to PMOD SPI flash at the bootloader offset |
| `bash build_25k_spu13_rplu2_consume_probe.sh` | Build Tang 25K RPLU2 flash consume-probe bitstream and corrected consume-profile table |
| `python3 software/tests/test_rational_robotics.py` | Run rational robotics oracle tests (56 checks) |
| `python3 software/tests/test_rational_som.py` | Run rational SOM/BMU oracle tests (24 checks) |
| `python3 software/tests/test_rotc_vm_rtl_trace.py` | VM-vs-RTL trace equivalence for all 36 ROTC angles (0-35), 336 bit-exact checks across both rotor datapaths |
| `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` | Set up Python environment |
| `A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade synth/pnr/pack` | Synthesise RPLU2PADE pipeline for Wukong Artix-7 |
|| `openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_RPLU2PADE.bit` | SRAM-load RPLU2PADE bitstream via DirtyJTAG |
| `A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade synth/pnr/pack` | Build RPLU2PADE Padé pipeline for Wukong Artix-7 (72 DSP, 34% LUT) |
|| `python3 software/tests/test_lucas_mac_oracle.py` | Run Lucas Phinary MAC oracle (PSCALE/PCHIRAL/PMUL/PINV + 1M-step zero-drift) |
| `iverilog -I hardware/rtl/arch -o build/lucas_mac_tb.vvp hardware/rtl/core/spu13/spu13_lucas_mac.v hardware/tests/spu13/spu13_lucas_mac_tb.v && vvp build/lucas_mac_tb.vvp` | Run Lucas MAC RTL testbench (11 ops + 100-period zero-drift) |
| `python3 software/tests/test_pade_batch_inversion.py` | Run Montgomery batch inversion oracle (25 checks, tower/MAC cost tables) |
| `python3 software/tests/test_hyper_catalan_oracle.py` | Run hyper-Catalan series + jet-ring oracle (21 checks vs Wildberger-Rubine 2025) |
| `python3 software/tests/test_icosahedral_catalog.py --emit-vm` | Regenerate the checksummed IROTC VM catalog (`software/lib/irotc_catalog.py`) after oracle changes |
| `python3 software/tests/test_irotc_vm_trace.py` | IROTC VM-vs-exact-Fraction trace equivalence (60 indices × both catalogs + A₄ alias interop) |
| `python3 software/tests/test_irotc_poison.py` | IROTC dispatch-fault poison proofs (UNTAGGED/BADIDX/CATMIX) |
| `python3 software/tests/test_irotc_chains.py` | IROTC 10-step chain tests + typestate transitions (thirds/octahedral/QADD lattice) |
| `python3 software/tests/test_icosahedral_catalog.py --emit-rtl` | Regenerate IROTC RTL code ROM + golden vectors (`spu13_irotc_codes.mem`, `spu13_irotc_golden.mem`) |
| `iverilog -g2012 -I hardware/rtl/arch -o build/irotc_tb.vvp hardware/rtl/core/spu13/spu13_irotc_engine.v hardware/tests/spu13/spu13_irotc_engine_tb.v && vvp build/irotc_tb.vvp` | Run IROTC engine RTL testbench (120 golden cases + chain + fault matrix) |

Synthesis uses the [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) (Yosys + nextpnr-himbaechel). No vendor IDE required.

## Hardware Test Status (July 2026)

**Proven in silicon on Tang Primer 25K:**
- FPGA configuration via openFPGALoader
- Laminar boot (SPI flash read, RPLU table hydration)
- Fibonacci-synchronized manifold (phi_8/13/21 pulses)
- Davis Gate quadrance monitoring (Q: UART telemetry)
- VE (Vector Equilibrium) QR init hydration (12 vertices)
- QR register file read path (6 distinct hex values verified)
- **QLDI opcode** — immediate Quadray load → writes correctly to QR regfile
- **QSUB opcode** — QR subtraction (QLDI operands → QSUB → QR commit readback)
- Hex coordinate projection → UART output (H: FFFE 0002)
- Instruction sequencer with inter-instruction delay
- RP2040 USB-to-SPI flash PMOD programmer — JEDEC, pin diagnostics, sector erase, page program, verify
- RPLU v2 PMOD J4 flash boot-table hydration proof — Tang Primer 25K reads external W25Q128-class flash over J4
- **RPLU2 consume proof over southbridge** — 149 records consumed via RP2350 SPI, count verified, checksum 0x0AA480E7
- **Southbridge SPI protocol** — 0xAC status, 0xA0 manifold, 0xAE QR commit, 0xB1 instruction write, 0xA5 config write
- RP2350 southbridge diag firmware — USB CDC console for SPI bring-up
- **RP2350 arithmetic test driver** — QLDI+QSUB 6-test suite via SPI, byte-swap fix applied

**Proven in silicon on Wukong Artix-7 100T:**
- JTAG detection via RP2040 DirtyJTAG (IDCODE `0x03631093`)
- J11 SPI southbridge via RP2350 — LUCAS, SU3, ROBOTICS, SU3SHARE all PASS
- **ROBOTICS main core** — QLDI/QSUB/ROTC 0-5/six-step closure (`13/13 PASSED`, `ARITHMETIC_BLAZE: PASS`)
- **SU3SHARE shared multiplier** — one M31 multiplier shared between SU3 sidecar and RPLU2 config/QR path, both passing on same bitstream
- **RPLU2PADE Thimble-Padé pipeline** — full A₃₁ inverter, SOM/BMU, BTU, Padé [4/4] over J11 SPI. 72 DSP, 34% LUT, route closed iteration 5 (`RPLU2PADE_J11: PASS`)
- **LUCAS sidecar** — PSCALE/PCHIRAL/PMUL/PINV all verified over J11

**A7 spin reconciliation (2026-07-08):** `build_a7.sh` accepts 16 spin names;
`docs/SPIN_CATALOG.md` catalogues all. The following appear in
`spu_a7_top.v`'s parameter table but not in the status lists above:

| Spin | Modules | Status |
|---|---|---|
| `FULL` | MATH+SOM+GATEKEEPER+GPU+RPLU_V2+pipeline+CORE+I2S+TORUS | direction (exceeds 100T, aspirational) |
| `MULTIMEDIA` | MATH+GATEKEEPER+GPU+RPLU_V2+pipeline+CORE+I2S | direction (aspirational product spin) |
| `INTELLIGENCE` | SOM+GATEKEEPER+RPLU_V2+pipeline+CORE | direction (aspirational product spin) |
| `SENSOR` | MATH+CORE | direction (minimal sensor-only spin) |
| `SOM` | MATH+SOM+GATEKEEPER+CORE | superseded by SOMPROBE/SOM-SIDECAR |
| `SU3` | SU3 sidecar, coreless | superseded by SU3SHARE |
| `RPLUCFG` | nothing enabled, coreless stub | superseded |
| `RPLU2CORE` | RPLU_V2+CORE | superseded by RPLU2 |
| `RPLU2` | RPLU_V2+pipeline+SHARED_RPLU2_MULT+CORE | superseded by RPLU2PADE |
| `RPLU2LIVE` | RPLU2LIVE flag only, coreless | superseded |
| `CUSTOM` | user-configured via `ENABLE_*` variables | meta (build-time only) |

**No longer "awaiting silicon test":** ROTC, SOM/BMU, RPLU2 Padé, Lucas MAC,
the SPU-4 Sentinel standalone core (first silicon 2026-07-08, Tang 25K,
`SPU4:P A=0000 B=0155 C=0155 D=0155` — see `docs/hardware_evidence.md` §3.2j),
and the IROTC icosahedral engine (first A₅ silicon 2026-07-10, Tang 25K,
repeating `IROTC:P E=00` — §3.2k) are all silicon-verified on either
Tang 25K or Artix-7.

**RTL testbench-verified (remaining):**
- **ROTC opcode** — all 12 verified ROTC angles (0-11) pass (TDM rotor
  core) on the tested vectors; 0-5 are the silicon-evidenced subset,
  6-11 (axis-permutation conjugates, added 2026-07-10) are
  testbench/trace-equivalence verified only so far. **Caveat found 2026-07-08, RTL fix implemented 2026-07-09:**
  the thirds angles (1, 3, 4) divide by 3 via a true floor-division
  magic-constant (`div3` in `spu13_rotor_core_tdm.v`) that silently
  truncates with no fault flag — see `knowledge/SPU_LEXICON.md` Davis
  Gate entry. A deferred-reduction exponent-tagged ROTC core
  (`spu13_rotor_core_tagged.v`, 314 lines) with explicit fault flags
  (MISALIGNED/OVERFLOW/INEXACT) now exists as the verified fix — 8/8
  testbench acceptance tests PASS (was 7/7; a real bug found 2026-07-09
  while auditing REDUCE for synthesis viability — `reduce_val64` was
  loaded via zero-extension instead of sign-extension, so any negative
  lane value, even one that divides evenly, either false-faulted
  INEXACT or silently missed the reduction. `-9` at exp=1 previously
  returned unchanged with a false INEXACT fault instead of reducing to
  `-3`. The prior single negative-value test (`-5`, T3) didn't catch it
  because `-5`'s zero-extended residue happens to also be nonzero mod
  3 — masking the bug for that value specifically. Fixed by
  sign-extending on load; Test 8 added as the regression case. The
  Python oracle (`reduce_tagged_exact`) was never affected — it uses
  native arbitrary-precision integers with no fixed-width extension
  step, so RTL and oracle had silently diverged on this exact scenario
  until now). The original TDM core (`spu13_rotor_core_tdm.v`)
  with silent `div3` remains the silicon-proven baseline; the tagged
  core has not yet been synthesised or run on hardware.
  **Second gap found and fixed 2026-07-09:** the ROTC angle field is
  6 bits (0-63), but only angles 0-5 were ever cross-verified against
  the VM oracle. Angles 6-11 apply a real axis permutation in RTL
  (`spu_quadray_permute`) with no matching logic in the VM — a genuine
  VM/RTL divergence risk. Angles 12-33 were VM placeholder table
  entries with F=G=H=0, which would have silently zeroed the
  destination's B/C/D on dispatch. Both were gated 2026-07-09 behind
  `spu13_core.v`'s `ROTC_MAX_VERIFIED_ANGLE` localparam and the VM's
  matching `RotcUnverifiedAngleError`.
  **Angles 6-11 verified and re-enabled 2026-07-10:** `spu_vm.py` now
  implements the axis permutation (rotate the component tuple so the
  invariant axis lands in the circulant's A slot, rotate, rotate back —
  mirrors `u_perm_fwd`/`u_perm_inv` in `spu13_core.v`), verified
  against an independent exact-Fraction oracle (periods, inverse pairs
  6↔7 / 8 / 11 self-inverse, det=+1, all 12 matrices distinct, Davis
  zero-sum preserved) and cross-verified against RTL two ways:
  `test_rotc_vm_rtl_trace.py` (all 12 angles through the real permuter
  module around BOTH rotor datapaths — the F/G/H scalar-fast path and
  the hardwired `angle_scalar_*_sum` path spu13_core uses — 144
  bit-exact checks) and `spu13_core_rotc_opcode_tb.v` (through the real
  core decode/permute/writeback, including a 6-then-7 inverse-closure
  round trip). `ROTC_MAX_VERIFIED_ANGLE` is now 35 on both sides;
  **Tranche 1 (12-14, missing thirds conjugates)**, **Tranche 2
  (15-23, remaining A₄ pure permutations)**, and **Tranche 3 (24-35,
  octahedral S₄ \ A₄)** were verified 2026-07-10 against an independent
  exact-Fraction oracle: 36 distinct matrices, det +1, inverse-closed
  (12→12, 9↔13, 10↔14 supply the previously missing thirds inverse
  pairs; 15-23 add 6 permuted 3-cycles + 3 double-transpositions;
  24-35 add six self-inverse 180° edge rotations {24,25,28,31,32,34}
  and three 90°/270° face inverse pairs 26↔27, 29↔30, 33↔35), Davis
  zero-sum preserved. The octahedral 12 are integer 3×3 matrices on
  (B,C,D) with entries 0,±1 — zero multiplies, no Q(√2); they recompute
  A = −(B+C+D) via the rotor core's `recompute_A` port, so closure
  requires zero-sum input. Cross-verified via `test_rotc_vm_rtl_trace.py`
  (336 bit-exact checks; both datapaths for 0-23, DUT1 hardwired path
  only for 24-35 — the F/G/H scalar path cannot express non-circulants)
  and `spu13_core_rotc_opcode_tb.v` (core-level decode/permute/writeback
  including inverse round-trips for 9↔13, 10↔14, 15↔16, 33↔35, and
  12/24 self-inverse). The fault boundary proof (poison values survive
  untouched + `rotc_debug_status[15]`) moved to angles 36 and 63. Note
  the /3 exactness caveat applies to all 12 thirds angles (1,3,4,6-14).
  Silicon status: angles 0-5 are silicon-verified on Artix-7; 6-35 are
  testbench-verified only.
- **IROTC — icosahedral A₅ φ-plane rotations (VM + RTL + core-integrated;
  A₅ silicon 2026-07-10, details below).** Opcodes 0xD6-0xD8
  (`IROTC`/`LOAD2X`/`SCALE2`) implemented in
  `spu_vm.py` + both assemblers per `docs/IROTC_SPEC.md` v0.2. Register
  plane decision: Z[φ] pairs overlay the QR register file (same component
  slots as the (P,Q) surd packing). The 60-entry catalog is GENERATED
  (`test_icosahedral_catalog.py --emit-vm` → `software/lib/irotc_catalog.py`)
  and checksum-verified at first dispatch (`aabef37c9c8b0317`) — never
  hand-edit it. **v0.2 finding: the 1-bit DOUBLED tag of spec v0.1 was
  unsound** — the doubling theorem does not compose across the main and
  conjugate (Galois-dual) catalogs; mixed products leave ½Z[φ] (oracle
  check, denominator 4) and 101/200 random main→conj VM chains would have
  silently truncated. Repaired as a 4-state typestate per QR register
  (UNTAGGED/FRESH/MAIN/CONJ, 2 bits in RTL) with a third dispatch fault
  IROTC_ERR_CATMIX; SCALE2 re-conditions to FRESH. Octahedral ROTC
  (24-35) demotes MAIN/CONJ→UNTAGGED (not in A₅); the 12 A₄ bypass
  angles preserve state (alias interop proven). Tests: trace equivalence
  all 60 × both catalogs (`test_irotc_vm_trace.py`, 9 checks), poison
  proofs all 3 faults (`test_irotc_poison.py`, 14), chain tests incl.
  thirds-mid-chain fault (`test_irotc_chains.py`, 12). Derivation oracle
  now 22 checks. **RTL engine landed 2026-07-10**
  (`spu13_irotc_engine.v`, testbench-verified): term-serial
  coefficient-select datapath, fixed 13-cycle slot (φ₁₃ gate) for all
  60 indices × both catalogs, signed exact Z[φ] (NOT mod-L_p), 0 DSP;
  conjugate catalog = 4-bit code remap, no second ROM. Code ROM + golden
  vectors are GENERATED (`test_icosahedral_catalog.py --emit-rtl` →
  `spu13_irotc_codes.mem` / `spu13_irotc_golden.mem`). TB pins: 120
  oracle golden cases bit-exact, 12-clock latency on every case,
  10-step back-to-back chain, BADIDX/UNTAGGED/CATMIX fault matrix with
  poison holds. **Tang 25K probe built 2026-07-10**
  (`spu13_tang25k_irotc_probe.v` + `build_25k_spu13_irotc_probe.sh`,
  DeepSeek authored / Claude verified): self-checking FSM (idx 16
  period-3, idx 36 period-5 — constants verified against the oracle —
  plus the three-fault matrix), Lucas-probe UART on C3, expected line
  `IROTC:P E=00`. LEDs are diagnostics only ([1]=engine idle,
  [2]=off=test finished) — read the verdict from UART. The engine's code
  ROM is an initialized memory with a registered, prefetch-hidden BSRAM
  read (converted 2026-07-12: the earlier combinational case-function
  form synthesized into a wide-mux forest that livelocked GW5A routing
  on the SPI spin at 53% LUT — two independent runs plateaued at the
  same congestion figure). Values bit-identical; oracle check 23 diffs
  all 540 entries against the derivation every suite run, so it cannot
  drift; the 13-cycle slot is unchanged and testbench-pinned. Probe TB decodes the real UART line in
  sim (CLK_FREQ parameter shrunk). **SILICON 2026-07-10 NZT**: bench run
  on the Tang 25K printed repeating `IROTC:P E=00` (bare dock, BL616
  USB-CDC on C3) — first icosahedral A₅ rotation silicon, including a
  genuine period-5 φ-arithmetic rotation and all three typestate
  dispatch faults firing with exact codes. Full evidence:
  `docs/hardware_evidence.md` §3.2k. Silicon scope = probe vectors
  (idx 16, 36 main catalog + fault matrix); full 60×2 surface is
  TB-verified. **Core integration landed 2026-07-11**: `ENABLE_IROTC`
  generate in `spu13_core.v` decodes 0xD6-0xD8 in the dispatch FSM;
  the engine reads/writes the core's own QR file; a 13×2-bit typestate
  tag file applies the full spec §3 transition algebra at every QR
  write site (QSUB lattice join, ROTC thirds/bypass/octahedral classes,
  raw-load clears; unknown writers default to UNTAGGED). Faults report
  via `rotc_debug_status` bit 15 + code [13:12], destination and tag
  held. SPI dispatch = existing 0xB1 fall-through (no sidecar; decision
  recorded in the roadmap). Proof: `spu13_core_irotc_opcode_tb.v`
  (25 checks). **SPI spin built 2026-07-11**
  (`build_25k_spu13_irotc_spi.sh`, southbridge pins): lean MATH=0 +
  IROTC=1 — `gen_qrf` enables on ENABLE_IROTC alone; do NOT issue ROTC
  on MATH=0 spins (hangs the inst handshake). Hydration interlock in
  the core: instructions held until VE hydration is not
  pending/in-flight (structural, fixes a latent sequencer race).
  SPI-level proof `spu13_spi_core_irotc_tb.v` (CRC'd 0xB1 + 0xAE
  through the real slave: LOAD2X, idx36 main + CONJUGATE, CATMIX
  no-commit over the link, SCALE2 recondition). Bench firmware
  `hardware/rp2350/rp2350_spu_irotc_test.c` (cmake target
  rp2350_spu_irotc_test, same 6 vectors; RP2350 spi0 wired GP0-3, not
  GP16-19 — build with `-DSPU_RP2350_ZERO_HEADER_SPI=ON`). **SILICON
  2026-07-12**: bench run over the real SPI link, 6/6 PASS, including
  the conjugate-catalog rotation (case 3) and CATMIX no-commit
  (case 4) — first conjugate-icosahedron silicon. Full evidence:
  `docs/hardware_evidence.md` §3.2k.1. Then Artix-7.
- **SOM/BMU pipeline** — 7-node parallel array with WTA comparator
- **RPLU v2 — Thimble-Padé Engine** — A31 arithmetic, Padé evaluator, BTU collision resolver
- **Lucas Phinary MAC** — PSCALE (1c, 0 DSP), PCHIRAL (1c, 0 DSP), PMUL (3c), PINV (O(log L_p) Euclidean GCD). 100-period zero-drift marathon PASS. ~200 LUTs, ready for Wukong Artix-7 synthesis.
- **Montgomery batch inverter** — 1 tower + 3(k-1) mults for k≤16, deferred
  zero-divisor check, singular-lane isolation + unit-subset re-batch; 52
  golden lanes verified against the Python oracle (committed .mem)
- **Series stream evaluator** (`spu13_series_stream.v`) — eps^3
  Hyper-Catalan series root, static 26-product schedule ROM, shared
  mult/tower handshake, done-coupled busy. Golden vectors oracle-verified;
  tb asserts exact resource counts (1 tower + 26 mults per eval, 1 tower +
  0 mults on singular input). Golden vectors are a COMMITTED .mem
  (`hardware/tests/spu13/spu13_series_stream_golden.mem`, regenerate via
  `digon_recursive.py --emit-series-mem`; singular cases mid-run AND last).
  Tang probe (`spu13_tang25k_series_stream_probe.v`) is sim-verified —
  walks all 8 vectors from a BSRAM ROM with ONE multiplier muxed between
  tower and stream, golden line `SSTR:P V=8 M=1A E=00` — but does NOT yet
  fit the 25K: `spu13_m31_multiplier` is 16 combinational 32x32 products
  (fine as DSP48E1 on Artix-7; ~70k LUT4 = 305% on GW5A-25 in the OSS
  flow). Blocker for Tang silicon: sequential M31 multiplier variant or
  Gowin DSP primitive wrapper. Contract: `docs/SERIES_STREAM_CONTROLLER.md`
- **13-satellite whisper aggregator** (`spu13_satellite_aggregator.v`) —
  Arlinghaus meso-tier governor component: 13 whisper v1 listeners,
  per-satellite 16-bit status table, worst-axis/dissonance scan,
  incoherent count, shared command bus. Module TB PASS
  (`spu13_satellite_aggregator_tb.v`) and, since 2026-07-10, a Tang 25K
  probe top (`spu13_tang25k_satellite_aggregator_probe.v`): 4 on-fabric
  emitters with distinct identities + 9 idle lines proving the 3-miss
  deadman, self-checking FSM incl. command-bus MSB-first shift proof,
  golden UART line `SAGG:P W:2 I:9 E:00`. Probe TB PASS, full
  synth/PnR/pack clean (7,855 LUT4 = 34%, Fmax 59.2 MHz @ 50 MHz clk,
  single clock domain — a divided whisper clock fails hold at 17-actor
  spread, see comment in the probe top). Awaiting board run
  (`bash build_25k_spu13_satellite_aggregator_probe.sh`).
- **A7 SOM/BMU probe** (`spu_a7_som_probe_top`) — port of the Tang-25K-proven
  fixture to the Wukong Artix-7 100T; identical scenarios + golden UART line
  (`SOM:P T:2 B:6 E:00`), tb decodes the UART stream bit-for-bit
  (`spu_a7_som_probe_tb.v`). Synth clean via
  `bash hardware/boards/artix7/build_a7.sh 100t somprobe synth`
  (~2.6k LUT, 84 DSP, 4 BRAM). Awaiting board run — same line on both
  boards is the cross-vendor determinism proof
- GPU rasterizer + fragment pipe (testbench passes)
- **Bio stack — claim corrected 2026-07-08, was overstated:** only
  `spu_annealer.v` (`hardware/rtl/peripherals/bio/`) and
  `spu_proprioception.v` (`hardware/rtl/core/shared/`) are in the active
  tree, and **neither has a testbench** — "TB-verified" was wrong for
  both. `spu_active_inference.v` and `spu_soul_metabolism.v` exist only
  in `archive/recovered/`, both `` `include "soul_map.vh"` `` — a header
  that does not exist anywhere in the repo, so they do not currently
  compile. Status is: dormant/archived concept code, not verified.
  Architectural framing (why this matters, not just what's missing —
  and note the Jitterbug transformation is a real, tested counter-example
  to "synergetics is only geometry here"):
  `knowledge/SYNERGETICS_BEYOND_GEOMETRY.md`.

**Rational Robotics & SOM Oracles (software-verified):**
- Rational robotics oracle — 56 checks
- Rational SOM/BMU oracle — 24 checks
- C++ parity for both oracles
- Lucas Phinary MAC oracle — 1M-step zero-drift, all 4 ops verified
- A31 field + Montgomery batch inversion oracle — 25 checks; bit-exact tower
  model (`spu13_fp4_inverter` semantics incl. FLAGS.V), k inversions →
  1 tower + 3(k-1) mults, 2.5x at k=13. RTL contract:
  `docs/MONTGOMERY_BATCH_INVERSION.md`. RTL landed and testbench-verified:
  `spu13_batch_inverter.v` (shared-multiplier mux, unit-subset re-batch,
  done-coupled busy). Golden vectors are a COMMITTED file
  (`hardware/tests/spu13/spu13_batch_inv_golden.mem`) regenerated via
  `test_pade_batch_inversion.py --emit-mem` — includes ordering-adversarial
  unit-LAST cases that caught a stale-read isolation bug (fixed 2d8658b);
  keep those orderings when adding vectors. Remaining: board `.ys` wiring,
  and external mult/tower handshake ports before sidecar integration
- Hyper-Catalan series + jet ring oracle — 21 checks vs the published
  Wildberger-Rubine tables (Bi-Tri array, Geode factorization, layerings);
  exact jet-perturbed root-tracking in A31[eps]/(eps^3) proven by
  back-substitution; gives `spu13_jet_mac`/`spu13_jet_inv` their Python
  oracle. Cost verdict REVISED 2026-07-08 (`software/lib/digon_recursive.py`):
  the earlier "Newton beats series at eps^3 (548c vs 724c), do NOT build an
  SRU" conclusion came from the naive dense-jet cost model. With digon-lattice
  traversal + mixed-sparsity jet arithmetic (c0 = O(eps), face coefficients
  eps^0-only scalars, c1^-1 dense), the series stream wins at shallow depth:
  eps^3 211c vs Newton 506c (0.42x), eps^5 904c vs 1569c (0.58x); Newton
  wins eps^7 (1.12x) and eps^9 (1.50x). The residual bottleneck is
  the one dense c1^-1 jet_mul per term — c1^-1 populates all eps channels,
  so no sparsity to exploit there. RTL implication: a sparse `spu13_jet_mac`
  variant with nilpotency-window operand tags is worth building for the
  eps^3/eps^5 regime — contract in `docs/SPARSE_JET_MAC.md`

**Known board limitations:**
- **`build_25k_spu13_southbridge.sh` (MATH=1 fpga_top spin) no longer
  fits at HEAD** (found 2026-07-11): post-synth 25.5k LUT4 vs 23k
  device; the last successful placement (2026-06-29) was already 90%.
  Core growth since June 29 (ROTC tranches 2-3, RPLU2/M31 additions)
  is the cause. The June 29 southbridge bitstream still works but
  cannot be rebuilt from HEAD. Lean spins (rplu2_arith at MATH=0,
  irotc_spi at MATH=0) are unaffected.
- SDRAM module (W9825G6KH) retired — DQ[10] fault confirmed, not an FPGA issue
- Tang 25K FPGA board is healthy; SDRAM fault was on the external module
- RPLU2 full pipeline (MATH=1 + RPLU_V2=1) too large for 25K (89% LUT) — needs Wukong Artix-7
- Split-build strategy: 4 independent probes fit on 25K (southbridge_link, math_probe, rplu2_arith_probe, lucas_mac_probe)
- USB 3.0 port on BL616 bridge unreliable — use USB 2.0 only

**RP2040 SPI Flash PMOD Programmer (bench-proven):**
- Purpose: reliable replacement for bad SOIC clips / ambiguous XGECU ICSP wiring. Use it to program and verify W25Q-style PMOD flash before FPGA-side J4 probes.
- Default wiring: `PMOD SLK -> Pico GP2`, `PMOD D1 -> Pico GP3`, `PMOD DO -> Pico GP4`, `PMOD CS -> Pico GP5`, `PMOD VCC -> Pico 3V3 OUT`, `PMOD GND -> Pico GND`.
- Safety rule: never erase or program unless repeated `id` reads return `JEDEC: EF4018`. `000000` means no valid flash response; `171717` usually indicates bad CS framing.
- Useful diagnostics: `tools/rp2040_flash_pmod.py --port <tty> diag`, `... drive --cs 1 --sck 0 --mosi 0`, and `... wren`. `WREN` should report `RDSR=02` before program/erase.
- Common wiring failure found in bring-up: cracked `/CS` solder joint. Meter W25Q pin 1 while using the `drive` command; it must switch between 0 V and 3.3 V. Add pullups on `/CS`, `/WP`, and `/HOLD` for custom PCBs.
- Corrected RPLU2 table programming command: generate with `python3 tools/gen_rplu2_tables.py --profile default --output tools/build/rplu2_boot_tables.bin`, then program with `tools/rp2040_flash_pmod.py --port <tty> write tools/build/rplu2_boot_tables.bin --offset 0x110000`. Corrected default/consume-profile blobs are 149 records / 2384 bytes.
- Legacy note: the first J4 hydration proof used an obsolete 81-record blob (`count=0x51`, checksum `0x35DE2068`) before the Padé high-lane and BTU row packing bugs were fixed. Do not use that blob for RPLU2 consumption tests.

**Wildberger Rational Trigonometry Library (7 files, 30+ primitives):**
- `wildberger_spread.lith` — spread + collinearity via Delta opcode
- `wildberger_geometry.lith` — 5 geometry primitives
- `wildberger_calculus.lith` — tangents + Faulhaber areas
- `wildberger_layer2.lith` — quadrance_between, normalize, Pell polynomials
- `wildberger_chromogeometry.lith` — blue/red/green triple, Pell-quintic connection
- `wildberger_higher_dim.lith` — cross matrix, diagonal rule, 2-subspaces
- `call_demo.lith` — CALL/RET subroutine test

## ISA Reference

Full ISA documentation: `knowledge/isa_reference.md` (26 opcodes, 19 hardware-verified)
VM opcode table: `software/spu_vm.py` lines 493–515
Assembler opcode table: `software/tools/spu13_asm.py`

### Corrected ROTC 0–11 Angle Catalog (June 2026; 6–11 verified July 2026)

The legacy ROTC table had three defects: angle 2 was documented with thirds coefficients
while hardware bypassed it as P5 permutation; angle 3 was singular (`det=0`); angle 5
duplicated angle 1. The corrected catalog is:

| ROTC angle | Name | Invariant axis | F | G | H | Period | Inverse |
|---:|---|---|---:|---:|---:|---:|---:|
| 0 | identity | — | 1 | 0 | 0 | 1 | 0 |
| 1 | thirds period-6 | A | 2/3 | 2/3 | -1/3 | 6 | 4 |
| 2 | P5 forward cycle | A | 0 | 1 | 0 | 3 | 5 |
| 3 | thirds period-2 | A | -1/3 | 2/3 | 2/3 | 2 | 3 |
| 4 | thirds period-6 inverse | A | 2/3 | -1/3 | 2/3 | 6 | 1 |
| 5 | P5 inverse cycle | A | 0 | 0 | 1 | 3 | 2 |
| 6 | conjugate of angle 4 about B | B | 2/3 | -1/3 | 2/3 | 6 | 7 |
| 7 | conjugate of angle 1 about B | B | 2/3 | 2/3 | -1/3 | 6 | 6 |
| 8 | conjugate of angle 3 about C | C | -1/3 | 2/3 | 2/3 | 2 | 8 |
| 9 | conjugate of angle 1 about C | C | 2/3 | 2/3 | -1/3 | 6 | 13 |
| 10 | conjugate of angle 4 about D | D | 2/3 | -1/3 | 2/3 | 6 | 14 |
| 11 | conjugate of angle 3 about D | D | -1/3 | 2/3 | 2/3 | 2 | 11 |
| 12 | 180° about B | B | -1/3 | 2/3 | 2/3 | 2 | 12 |
| 13 | 240° about C | C | 2/3 | -1/3 | 2/3 | 6 | 9 |
| 14 | 60° about D | D | 2/3 | 2/3 | -1/3 | 6 | 10 |
| 15 | P5 fwd about B | B | — | — | — | 3 | 16 |
| 16 | P5 inv about B | B | — | — | — | 3 | 15 |
| 17 | P5 fwd about C | C | — | — | — | 3 | 18 |
| 18 | P5 inv about C | C | — | — | — | 3 | 17 |
| 19 | P5 fwd about D | D | — | — | — | 3 | 20 |
| 20 | P5 inv about D | D | — | — | — | 3 | 19 |
| 21 | (AB)(CD) | — | — | — | — | 2 | 21 |
| 22 | (AC)(BD) | — | — | — | — | 2 | 22 |
| 23 | (AD)(BC) | — | — | — | — | 2 | 23 |
| 24 | 180° edge (CD) | — | — | — | — | 2 | 24 |
| 25 | 180° edge (AB) | — | — | — | — | 2 | 25 |
| 26 | 90° face (x) | — | — | — | — | 4 | 27 |
| 27 | 270° face (x) | — | — | — | — | 4 | 26 |
| 28 | 180° edge (BC) | — | — | — | — | 2 | 28 |
| 29 | 90° face (z) | — | — | — | — | 4 | 30 |
| 30 | 270° face (z) | — | — | — | — | 4 | 29 |
| 31 | 180° edge (AD) | — | — | — | — | 2 | 31 |
| 32 | 180° edge (BD) | — | — | — | — | 2 | 32 |
| 33 | 270° face (y) | — | — | — | — | 4 | 35 |
| 34 | 180° edge (AC) | — | — | — | — | 2 | 34 |
| 35 | 90° face (y) | — | — | — | — | 4 | 33 |

Angles 12-14 (Tranche 1) supply the previously missing inverses: 13↔9 and 14↔10.
Angles 15-23 (Tranche 2) complete the A₄ pure-permutation subgroup (12 elements
including identity and angles 2/5). Angles 15-23 are pure coordinate permutations
with zero multiplies (bypass path). Angles 21-23 are double transpositions using
dedicated bypass signals (`bypass_ab_cd`, `bypass_ac_bd`, `bypass_ad_bc`).
Angles 24-35 (Tranche 3) are the 12 remaining cube rotations (S₄ \ A₄): integer
3×3 matrices on (B,C,D) with entries 0,±1 — no Q(√2) — hardwired in
`spu13_rotor_core_tdm.v` with A recomputed from zero-sum (`recompute_A`).
Edge labels name the swapped cube diagonals (each 180° edge rotation is
negation ∘ that transposition); face axes x/y/z are shared with the double
transpositions — 26²=27²=21, 29²=30²=23, 33²=35²=22 (verified exactly).

**RTL encoding:** Thirds angles use the TDM circulant path (`F,G,H` surd multiplies + `/3`).
Angles 2,5,15-20 use hardware bypass (`bypass_p5`, `bypass_p5_inv`) — pure bit permutation,
zero multiplies, combined with axis permutation (`perm_sel`) for 15-20. Angles 21-23 use
dedicated double-transposition bypass signals. Angles 6-23 wrap the rotor core in
`spu_quadray_permute` (`u_perm_fwd`/`u_perm_inv` in `spu13_core.v`): the target
invariant axis is rotated into the circulant's A slot and back, so unlike 0-5 they
rewrite all four components of the destination lane. F/G/H for 0-14 must stay
bit-identical in three places: the VM `_ROTC_TABLE`, the `rote_F/G/H` lookup in
`spu13_core.v`, and the hardwired `angle_scalar_*_sum` functions in
`spu13_rotor_core_tdm.v`. Bypass angles (2,5,15-23) bypass the arithmetic path entirely.

**VM-vs-RTL trace equivalence:** `python3 software/tests/test_rotc_vm_rtl_trace.py` — exercises
all 36 angles (336 bit-exact checks) through the real permuter module against both rotor
datapaths (`ENABLE_TDM_FALLBACK` 1 and 0) for angles 0-23; octahedral angles 24-35 run on
DUT1 (hardwired path) only, since the F/G/H scalar path cannot express non-circulant
matrices. Thirds-division exactness is required for equivalence (VM rounds, RTL `div3`
truncates), so the 6-11 vectors use all-multiples-of-3 components; the /3 divisibility
caveat (`knowledge/SPU_LEXICON.md`, Davis Gate entry) applies to 6-11 exactly as to 1/3/4.

### Rational Robotics & SOM Oracles

| Layer | File | Purpose |
|---|---|---|
| Python robotics oracle | `software/lib/rational_robotics.py` | Exact Q(√3) robotics: Pell, F/G/H circulant, FK chains, inverse closure |
| Python robotics tests | `software/tests/test_rational_robotics.py` | 56 checks — determinant, period, inverse, closure, no-float audit |
| C++ robotics oracle | `software/common/include/spu_rational_robotics.h` | C++17 parity for all robotics primitives |
| C++ robotics tests | `software/common/tests/spu_rational_robotics_test.cpp` | C++ parity for closure tests |
| Python SOM oracle | `software/lib/rational_som.py` | Weighted quadrance BMU, surd-field path, stable tie-breaking |
| Python SOM tests | `software/tests/test_rational_som.py` | 24 checks — integer/surd BMU, field-square, tie-breaking |
| C++ SOM oracle | `software/common/include/spu_rational_som.h` | C++17 parity for SOM BMU classifier |
| C++ SOM tests | `software/common/tests/spu_rational_som_test.cpp` | C++ parity for BMU scenarios |
| Rational curves spec | `knowledge/RATIONAL_CURVES_SPEC.md` | Type 1–6 curve primitives, kinematics, correction |
| Nguyen weight partitioning | `knowledge/NGUYEN_WEIGHT_PARTITIONING.md` | Laminar weight → IVM wedge allocation → BRAM tiering |
| SOM Nguyen cluster notes | `knowledge/RATIONAL_SOM_NGUYEN_CLUSTER_NOTES.md` | Kohonen/SOM direction, BMU RTL staging, hex topology |
| Lucas Phinary MAC oracle | `software/tests/test_lucas_mac_oracle.py` | PSCALE/PCHIRAL/PMUL/PINV, 1M-step zero-drift over L_521 |
| Lucas MAC architecture | `knowledge/LUCAS_PHINARY_MAC.md` | Ring separation, Barrett bridge, BTU integration, opcode map |
| Lucas MAC paper | `docs/LUCAS_MAC_PAPER.md` | 7-section paper draft with empirical results |
| ROTC kinematics paper | `docs/ROTC_KINEMATICS_PAPER.md` | Draft v0.1 (markdown, pre-TeX): 36-angle catalog (0-35, incl. octahedral S₄) + group structure, /3 exactness theorem + counterexample, Evgeny Yanenko state-machine harness (§6; see `Theory/EvolvingCategories.pdf`), claim-discipline table (§10) |
| A31 field oracle | `software/lib/a31_field.py` | A31 mult table, Conjugate Reduction Tower (FLAGS.V), Montgomery batch inversion, Padé eval, op counting |
| Batch inversion tests | `software/tests/test_pade_batch_inversion.py` | 25 checks — bit-exact batch vs per-element towers, singular isolation, cycle/MAC tables |
| Batch inversion RTL contract | `docs/MONTGOMERY_BATCH_INVERSION.md` | Semantics, interface, singular-lane tiers, acceptance checklist for the RTL block |
| Hyper-Catalan oracle | `software/lib/hyper_catalan.py` | Exact C_m (Wildberger-Rubine Thm 5), ring-generic soft polynomial formula (Thm 4) |
| Jet ring oracle | `software/lib/jet_ring.py` | A31[eps]/(eps^3) matching `spu13_jet_mac`/`spu13_jet_inv` multiply-for-multiply |
| Hyper-Catalan tests | `software/tests/test_hyper_catalan_oracle.py` | 21 checks — paper tables, Geode factorization, exact jet root-tracking, Newton comparison |
| SPU Lexicon | `knowledge/SPU_LEXICON.md` | Normative vocabulary: definitions, exact SPU conventions, literature mapping + divergence flags (Urner/SQR etc.), OPEN formalization worklist |
| Arlinghaus constellation architecture | `knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7 | Deployment tiers: SPU-4-only edge node (~400 LUT, silicon-verified), SPU-13 + per-axis SPU-4 cluster (bridge frames carry Davis dissonance), whisper-networked constellation; status honesty table + next steps |
| Digon-recursive cost model | `software/lib/digon_recursive.py` | Series-vs-Newton cycle tables at eps^3..eps^9 (4 strategies + sparse-jet model); source of the revised SRU verdict |
| Sparse jet MAC contract | `docs/SPARSE_JET_MAC.md` | Nilpotency-window-tagged Cauchy product: skip rule, tag algebra, interface, acceptance checklist |
| Spin catalog | `docs/SPIN_CATALOG.md` | Every named bitstream configuration: purpose, resources, silicon status, first-hour story; product-vs-probe discipline ("spin" is defined in `knowledge/SPU_LEXICON.md`) |
| Whisper v1 contract | `docs/WHISPER_V1_SPEC.md` | Coherence-plane frame spec (18-byte ASCII line, fail-silent, 3-miss rule, governor relay) — written before RTL per Arlinghaus §7 step 3; acceptance checklist included |
| Host library | `software/spu_host/` | Python client over the 8-opcode Southbridge SPI console (`status`, `manifold`, `qr_commit`, `write_chord`, `write_rplu_cfg`, ...); hardware-free parser test wired into `run_all_tests.py`; CLI via `python3 -m software.spu_host` |
| Cartesian bridge | `docs/CARTESIAN_BRIDGE_SPEC.md`, `software/lib/cartesian_bridge.py` | Sensor(float)↔RationalSurd boundary oracle: round-half-even quantization, explicit-not-silent saturation, direct `rational_som.find_bmu` compatibility; 30-check TB in `software/tests/test_cartesian_bridge.py` |
| ROTC exponent-tagged fix | `docs/ROTC_THIRDS_EXACTNESS_FIX.md`, `docs/ROTC_EXPONENT_STATE_MACHINE.md`, `software/lib/rotc_thirds_native.py` | Fixes silent truncation in thirds-angle ROTC (`div3`): deferred-reduction state machine (CLEAN/PENDING/FAULT.{MISALIGNED,OVERFLOW,INEXACT}), verified against exact ground truth, 69-check TB in `software/tests/test_rotc_thirds_native.py`. A prior "global rescale" fix attempt is retained as a documented dead end (`rotate_no_div_DEAD_END`). Oracle complete; RTL not started. |
| State-machine harness plan | `docs/STATE_MACHINE_HARNESS.md` | Yanenko categorical framework applied across the SPU stack: per-subsystem state machines (ROTC, SOM/BMU, BTU, Padé, Lucas MAC, Batch inverter), invariants, verification methodology, implementation order. ROTC is the reference implementation (done); others are planned. |
| Hobbyist glossary | `docs/glossary.md` | Plain-English on-ramp: terms, angle↔spread / distance↔quadrance / Q12 conversions, reading list; SPU_LEXICON.md stays normative |
| Interconnect architecture | `knowledge/INTERCONNECT_ARCHITECTURE.md` | Tier model (T0 bare pins → T1 southbridge → T2 cluster links → T3 network bridge), southbridge homogeneity contract, determinism boundary, radio/LAN feasibility, multi-compute prep order |

## Coding Style & Naming Conventions

- **Verilog RTL:** 4-space indentation. Modules use `snake_case`. Testbenches end in `_tb.v`. Top-level headers in `hardware/common/rtl/include/` (e.g., `spu_arch_defines.vh`).
- **Python:** Follow PEP 8. Use `snake_case` for functions and variables. Scripts under `software/` and `tools/`.
- **C++:** C++17. Test files named `*_test.cpp`. Include path: `software/common/include/`.

## Testing Guidelines

- **Hardware:** Icarus Verilog (`iverilog`/`vvp`) is the primary simulator; Verilator serves as fallback for GPU sources containing SystemVerilog constructs. Every testbench must print `PASS` or `FAIL`. Use `$finish` to prevent timeout.
- **Python VM:** Run `python3 software/spu_vm_test.py` and `python3 software/cross_validate.py` to verify VM correctness against the C++ reference.
- **C++:** Tests discovered automatically from `*_test.cpp` files. Compile with `g++ -std=c++17`.
- **Coverage:** All 95+ Verilog testbenches must pass before merging.

## Commit & Pull Request Guidelines

- **Commit style:** Use lowercase, imperative-mood summaries. Prefix with area when helpful: `spu13:`, `tang25k:`, `feat:`, `fix:`.
- **PR requirements:** All tests must pass (`run_all_tests.py`). Include a description of what changed and why. Link related issues. For hardware changes, note which board targets were tested.
- **Constraints:** The architecture prohibits floating-point, division, and branches in hot paths. Changes violating these are rejected.
