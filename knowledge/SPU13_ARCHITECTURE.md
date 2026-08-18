# SPU-13 Cortex Architecture

**Status: mixed, by subsystem.** The core scalar/Quadray arithmetic pipeline
(QLDI/QSUB/ROTC 0-5, six-step kinematics closure) is silicon-proven on both
Tang Primer 25K and Wukong Artix-7 100T. The RPLU2/Padé pipeline (A₃₁
inverter, SOM/BMU, BTU, [4/4] Padé) is silicon-proven on the Wukong
Artix-7 100T over the J11 SPI southbridge, but only at a reduced `clk_fast`
(781.25 kHz via `A7_CLK_DIV_LOG2=6`) — 50 MHz operation was a measured
*negative* result, so the functional claim is backed and the full-speed
claim is not. ROTC angles 6-35, the Lucas Phinary MAC, the SOM 7-node BMU,
and the IROTC icosahedral engine each have their own evidence level; see
§6 and `AGENTS.md` for the current per-subsystem breakdown before citing
any of them as "silicon-proven." The full concurrent RPLU2 southbridge
build (`MATH=1 + RPLU_V2=1`) does **not** fit the Tang 25K — it was
retired as a Tang target 2026-08-16 after measuring 267% of the GW5A-25A's
LUT4 budget (an earlier "89% LUT" figure was a stale synthesis-era
estimate; see `AGENTS.md` and `docs/hardware_evidence.md` §3.6g). Full
concurrent integration is a Wukong Artix-7 100T goal, not yet fully
realized there either — see §6.

This document is a map, not a source of truth for any individual claim.
Every specialized topic below has its own document; read this first to
find the right one, then trust that one over this summary if they ever
disagree. Always check `AGENTS.md` for the current silicon-vs-testbench
status of a specific spin before repeating a claim from here.

---

## 1. Overview

The SPU-13 Cortex is a 13-axis (cuboctahedral / Isotropic Vector Matrix)
deterministic rational-field manifold engine. It is the main compute core
of the SPU platform: exact arithmetic over `Q(√3)`, extended to `A₃₁`
(Mersenne-prime field arithmetic, basis `[1,√3,√5,√15]`) and `Z[φ]/L_p`
(Lucas-prime modulus) for the RPLU2/Padé and Lucas MAC subsystems
respectively. Thirteen manifold axes are processed each sovereign cycle in
a time-division-multiplexed (TDM) burst, each axis holding a Quadray
(`a,b,c,d`) vector over the scalar field.

SPU-13 is a large-fabric core (Tang Primer 25K and up, primary target
Wukong Artix-7 100T) — see §9 for how this differs from the SPU-4
Sentinel's budget-fabric role. The current product-shaped, proven
deliverable built on SPU-13 is the seven-node SOM classification sidecar
described in the repo `README.md` ("labeled CSV in, checksummed rational
SOM map out, bit-exact hardware inference"); that framing is authoritative
for what SPU-13 currently *ships* as, and this document should be read as
the architecture underneath that product, not a claim that every
subsystem described below is equally production-ready.

---

## 2. Data representation and field arithmetic

Scalar registers hold rational surds `(P, Q)` meaning `P + Q·√3`, packed
as a 32-bit `RationalSurd` (`[31:16] = P`, `[15:0] = Q`, both signed). The
field is closed under add/sub/mul with no division ever performed:

```
add : (P1+P2, Q1+Q2)
sub : (P1-P2, Q1-Q2)
mul : (P1P2 + 3Q1Q2, P1Q2 + Q1P2)     ; since √3·√3 = 3
```

`RationalSurd` constants are never encoded as raw signed decimal literals
in RTL — bit-packing is explicit (identity = `{32'd0, 32'd1}`, negative =
`{32'd0, 32'hFFFFFFFF}`), because Verilog's implicit sign-extension rules
on `-` literals across concatenation are a real source of bugs in this
codebase (see the `spu13_rotor_core_tagged.v` sign-extension fix logged in
`AGENTS.md`).

Two extensions layer on top of the base `Q(√3)` field:

- **`A₃₁`** — arithmetic over the Mersenne prime `p = 2³¹−1`, basis
  `[1, √3, √5, √15]`, used by the RPLU2/Padé pipeline
  (`spu13_m31_multiplier.v`, `spu13_m31_inverter.v`, `spu13_fp4_inverter.v`).
- **`Z[φ]/L_p`** — a Lucas-prime modulus ring (`φ² = φ + 1`), used by the
  Lucas Phinary MAC (`spu13_lucas_mac.v`).

Ratios (spreads, comparisons) are never computed by division — they are
carried as `(numerator, denominator)` pairs and compared by
cross-multiplication (`SPREAD` opcode, `knowledge/ISA_QUICKSTART.md`).
Geometric questions reduce to integer comparisons: perpendicular is
`numer == denom`, the 60° IVM angle is `4×numer == 3×denom`, parallel is
`numer == 0`.

The full derivation — why `Q(√3)` specifically, the Fuller/Wildberger
lineage, and why this is a mathematical consequence of isotropic geometry
rather than a stylistic choice — is `knowledge/MATHEMATICAL_FOUNDATIONS.md`.
The canonical register/field packing reference is
`knowledge/ISA_QUICKSTART.md`.

---

## 3. Dispatch and timing model

SPU-13 runs two clock domains: a fast TDM domain (`clk_fast`, 24 MHz on
the Tang Primer 25K's PLLA-derived clock) that does all computation, and a
slow "sovereign" domain (`clk_piranha`, target 61.44 kHz, actual measured
rate on Tang is ≈61.4 kHz per the Sierpinski divider chain) that marks
external frame boundaries — SD/RP2350 hydration, Artery FIFO drains,
Whisper TX frame starts. The Piranha Pulse is a vertical-sync analog: it
defines when a manifold frame is complete, not how fast the core runs.

Instruction dispatch inside each fast-domain burst is Fibonacci-gated: the
Sierpinski clock (`spu_sierpinski_clk.v`) counts a 34-cycle frame (34 =
F(9)) and fires three single-cycle pulses at positions 8, 13, and 21 —
`phi_8` (fetch), `phi_13` (compute), `phi_21` (commit) — the three inputs
`spu13_core.v` takes directly as its Fibonacci Timing Pulses. This is a
deliberate design constraint (per `CLAUDE.md`), not an artifact to
optimize away: dispatch positions divide the frame at golden-ratio
proportions, and the ratios 13/8, 21/13 converge toward φ.

Key numbers (Tang Primer 25K, 24 MHz `clk_fast`):

| Quantity | Value |
|---|---|
| Fast clock | 24 MHz |
| Sequencer burst | 15 cycles (13-axis fetch/compute/commit) = 0.625 µs |
| Idle per 34-cycle frame | 19 cycles = 0.792 µs |
| Burst duty cycle | 15/34 ≈ 44.1% |
| Sovereign frame target | 61.44 kHz (≈16.3 µs between bursts) |

The sequencer (`spu13_sequencer.v` — pipelined TDM controller; older
`spu_sequencer.v` also present) wakes on each piranha tick and walks all
13 axes at fast-clock speed within one burst, well inside the 16.3 µs
sovereign period. The exact 61.44 kHz divider is not yet fixed in RTL
(three resolution options are documented, first-board-bring-up decides
it) — see `knowledge/CLOCK_ARCHITECTURE.md` for the full derivation,
clock-domain-crossing protocol (`spu_system.v`'s 4-phase CDC gate), and
why 61.44 kHz = 60 × 1024 Hz was chosen. Do not re-derive any of that
here; that document is the source of truth for timing.

---

## 4. Stability — the Davis Gate

Every cycle, the hardware checks `ΣABCD = 0` across each axis's four
Quadray components (`davis_gate_dsp.v`, shared RTL). This is an *exact*
zero test on integer sums, not an epsilon comparison against a threshold.
The gasket sum feeds Henosis — a one-cycle soft-recovery pulse — rather
than a hard reset when a nonzero sum ("cubic leak") is detected. The core
also derives an IVM quadrance (`Σᵢ<ⱼ(cᵢ−cⱼ)²`) and a "stiffness" figure
(`ivm_quadrance + gasket_sum²`) from the same datapath. The normative
formula and correctness analysis live in `knowledge/SPU_LEXICON.md`
("Davis Gate" entry) — read that before touching the gate's arithmetic,
not this summary.

---

## 5. Register file and ISA summary

- **Scalar registers `R0`-`R25`** — each a `Q(√3)` surd, 32-bit packed.
  R1-R12 mirror the 13 IVM axes; R13-R25 are extended/scratch.
- **Quadray registers `QR0`-`QR12`** — each a 4-component `(a,b,c,d)`
  vector over `Q(√3)`, backing the 13-axis manifold.

Instructions are 64-bit words: `[63:56] opcode | [55:48] R1 | [47:40] R2
| [39:24] P1_A | [23:8] P1_B` (8 reserved bits). Opcode categories, by
count (see `knowledge/isa_reference.md` for the full per-opcode table —
this is a summary only):

| Category | Examples | Silicon evidence level (see AGENTS.md before citing) |
|---|---|---|
| Scalar `Q(√3)` arithmetic | LD, ADD, SUB, MUL, ROT | core ops silicon-proven |
| Control flow | JMP, CALL, RET, SNAP, HALT | JMP/CALL/RET/NOP silicon-proven |
| Quadray/IVM ops | QADD, QROT, QNORM, QLOAD, ROTC, IROTC | QLDI/QSUB/ROTC 0-5 silicon-proven; ROTC 6-35 and IROTC testbench/trace-verified |
| Geometry output | SPREAD, HEX | HEX silicon-proven |
| Vector Equilibrium / Janus | IDNT, JINV, ANNE, EQUIL | IDNT silicon-proven |
| RPLU / polynomial extensions | POLY_STEP, RATIO_CMP (legacy) | superseded by the RPLU2 sidecar control path, not opcode-driven |
| Classification | SOM, SOM_TRAIN | silicon-proven (SOM sidecar path) |

The instruction-decode datapath is split across `spu_instr_decode.v`
(QLDI/ROTC/QSUB/DELTA/HEX/QLOG/IDNT/HALT dispatch against the QR file) and
the register files themselves: `spu_quadray_regfile_ecc.v` (ECC-protected
QR file) and `spu13_multi_port_regfile.v` (4-read/2-write scalar file,
dual-cluster ALU support for streaming ops plus the `F_{p^4}` conjugate
reduction tower). `knowledge/isa_reference.md` is the canonical, current
encoding — cite it, not this table, for anything opcode-specific.
`docs/spu13_isa_spec.md` describes a separate experimental Wheeler-Feynman
twin-register adapter ISA; it is not the active core ISA.

---

## 6. Extended pipelines and sidecars

Each of these sits beside the core scalar/Quadray pipeline, most reachable
through the southbridge SPI control path rather than dedicated opcodes.

- **RPLU2 / Thimble-Padé** — `[4/4]` rational approximant over `A₃₁`,
  Horner evaluation plus conjugate-reduction-tower inversion
  (`spu13_rplu2_pade_sidecar.v`, `spu13_fp4_inverter.v`,
  `spu13_m31_multiplier.v`, `rplu_pipeline.v`). Silicon-proven on Wukong
  Artix-7 100T over J11 SPI at reduced clock (see status header); does not
  fit the Tang 25K as a full concurrent build.
- **Lucas Phinary MAC** — `Z[φ]/L_p` multiply-accumulate co-processor
  (`spu13_lucas_mac.v`, SPI-visible via `spu13_lucas_sidecar.v`).
  Silicon-proven on Wukong Artix-7 100T (PSCALE/PCHIRAL/PMUL/PINV, plus a
  200-step zero-drift proof). Full spec: `knowledge/LUCAS_PHINARY_MAC.md`.
- **SOM / BMU classification** — writable, exact-order seven-node
  best-matching-unit classifier (`spu_som_bmu.v`, weight storage
  `spu_som_weight_bram.v`, training `spu_som_train.v`, decision-evidence
  framing `spu13_som1_frame.v`). This is the core's current proven product
  path (README.md), cross-vendor silicon-proven on both Tang 25K and
  Wukong Artix-7. Product contract: `docs/SOM_V1_PRODUCT_CONTRACT.md`.
  Do not confuse this with the unrelated SPU-4 `spu4_som_edge.v` 4-node
  classifier, a structurally different module with no silicon evidence of
  its own.
- **IROTC (icosahedral `A₅` rotation)** — φ-plane rotation engine
  (`spu13_irotc_engine.v`), typestate-guarded at dispatch
  (`spu13_typestate_guard.v` / `spu13_sva_guard.v`). First `A₅` silicon
  2026-07-10 on Tang 25K; spec `docs/IROTC_SPEC.md`.
- **Tensegrity / Janus / topology sidecars** — exact closed-segment
  contact over `Z[φ]` (`spu13_tensegrity_intersection.v`), bounded
  admission guard (`spu13_tensegrity_guard.v`), transactional TGR1 table
  store (`spu13_tensegrity_sidecar.v`), and the Janus mirror/dual-mode/
  screw-line topology permuters (`spu13_janus_*.v`,
  `spu13_topology6_state.v`) that back the `JINV`/`ANNE`/`EQUIL` opcodes.
  Silicon-proven admission-guard proof on Wukong Artix-7
  (`docs/hardware_evidence.md` §3.2l).
- **SU3 matrix multiply** — 3×3 dense product over the degree-8 extension
  `A₃₁[i]` (`spu13_su3_mult.v`), SPI-visible via `spu13_su3_sidecar.v`.
  Independently silicon-proven on Wukong Artix-7 (§3.2e.6), and again
  sharing one M31 multiplier with the RPLU2 config/QR path (SU3SHARE,
  §3.2e.5).
- **Hyper-Catalan series stream** — series root over `J₂ = A₃₁[ε]/(ε³)`
  (`spu13_series_stream.v`); Tang probe is simulation-verified only, not
  silicon.
- **Neuro epoch sidecar** — deterministic leaky-integrate-and-fire digital
  field (`spu13_neuro_epoch_sidecar.v`), SPI-visible via
  `spu13_neuro_sidecar_adapter.v`; check `AGENTS.md` before citing a
  silicon status for this one specifically.

For anything not listed here with a status claim, treat it as sim/TB-only
until `AGENTS.md` says otherwise.

---

## 7. Module map

Organized by subsystem, `hardware/rtl/core/spu13/` unless noted. This is
a navigation aid, not exhaustive documentation of every port.

**Core sequencing / dispatch / top-level**
`spu13_core.v` (main integration, all `ENABLE_*` feature parameters),
`spu13_top.v` (older/simpler standalone top, legacy SPU-4 link, distinct
from `spu13_core.v`'s feature set), `spu13_sequencer.v` / `spu_sequencer.v`
(TDM burst controller), `spu_instr_decode.v` (QR-path instruction
dispatch), `spu13_multi_port_regfile.v` / `spu_quadray_regfile_ecc.v` /
`spu_quadray_regfile.v` / `spu_register_file.v` (register files, in
`shared/` and `spu13/`), `spu13_scoreboard.v` / `spu13_scoreboard_v2.v`
(register-readiness hazard tracking, v2 supersedes the unverified v1
timer-based prototype).

**Stability / guards**
`shared/davis_gate_dsp.v` / `shared/spu_davis_gate.v` (Davis Gate),
`spu13_axiomatic_gatekeeper.v` (reverse-math assertion engine on the SOM
quadrance pipeline), `spu13_typestate_guard.v` / `spu13_sva_guard.v`
(φ-plane typestate lattice, two independent implementations for
cross-check), `spu13_composition_policy.v` (accept/hold/escalate policy).

**Field arithmetic — `A₃₁` / M31**
`spu13_m31_multiplier.v` (+ `_seq`, `_structured` variants),
`spu13_m31_inverter.v` (binary extended Euclidean over M31),
`spu13_fp4_inverter.v` / `_structured` / `_structured_arithmetic`
(conjugate reduction tower for `F_{p^4}` inversion), `spu13_batch_inverter.v`
(Montgomery batch inversion), `spu13_jet_mac.v` / `spu13_jet_inv.v` (jet
ring MAC/inverse over `F_{p^4}[ε]/(ε^(n+1))`), `spu13_nsa_core.v` /
`spu13_nsa_dual_alu.v` (dual-number arithmetic for FSDG).

**Field arithmetic — `Z[φ]`**
`spu13_lucas_mac.v`, `spu13_lucas_sidecar.v`, `spu13_zphi_mul_serial.v` /
`_karatsuba` (term-serial exact multiplication, Karatsuba candidate not
yet the verified default).

**Rotor / ROTC / IROTC**
`spu13_rotor_core.v` (original), `spu13_rotor_core_tdm.v` (current
silicon baseline, shared-multiplier TDM version, has the known silent
`div3` truncation on thirds angles), `spu13_rotor_core_tagged.v`
(exponent-tagged deferred-reduction fix, testbench-verified, not yet
synthesized/silicon), `spu13_permute_13.v` / `shared/spu_quadray_permute.v`
(axis permutation for non-A-invariant ROTC angles), `spu13_irotc_engine.v`
(A₅ icosahedral engine), `spu13_rotary_gate.v` (coordinate-invariant
switching primitive).

**RPLU2 / Padé pipeline**
`rplu_pipeline.v` (4-stage top), `spu13_rplu2_sidecar.v` /
`spu13_rplu2_pade_sidecar.v` (SPI-visible adapters), `spu13_btu_core_top.v`
/ `spu_btu_collision_resolver.v` (BTU), `spu13_series_stream.v`.

**SOM / classification**
`spu_som_bmu.v`, `spu_som_train.v`, `spu_som_weight_bram.v`,
`spu_quadrance_accum.v`, `spu_cluster_reduce.v`, `spu13_som_classify.v`
(PHSLK fast path), `spu13_som1_frame.v` (decision-evidence frame encoder).

**Tensegrity / Janus / topology**
`spu13_tensegrity_guard.v`, `spu13_tensegrity_intersection.v`,
`spu13_tensegrity_sidecar.v`, `spu13_janus_mirror.v`,
`spu13_janus_dual_mode.v`, `spu13_janus_screw_lines.v`,
`spu13_topology6_state.v`, `spu13_phslk_core.v` (Wheeler-Feynman
phase-lock predicate), `spu13_quadray_variety.v`.

**Other sidecars**
`spu13_su3_mult.v` / `spu13_su3_sidecar.v`, `spu13_neuro_epoch_sidecar.v` /
`spu13_neuro_sidecar_adapter.v`, `laminar_node.v` (Janus-bit / Phinary
multiplier primitive), `spu13_lattice.v` (13× `laminar_node` instantiation
scaffold, minimal by design).

**Cluster / southbridge interface**
`spu13_cluster_controller.v` (SPU-4 satellite arbitrator),
`spu13_satellite_aggregator.v` (13-satellite whisper/bus aggregator, meso
tier), `spu13_southbridge_token_parser.v` (CRC-gated 0xA5 config parser),
`spu13_berry_gate.v` (topological twist tracker), `spu_bram_32x64_array.v`.

---

## 8. External interconnect

SPU-13 talks to the outside world through the tiered interconnect model
in `knowledge/INTERCONNECT_ARCHITECTURE.md`: a command plane (southbridge
SPI, 8 opcodes — `0xAC` status, `0xA0` manifold, `0xAE` QR commit, `0xB1`
instruction write, `0xA5` config write, per `CLAUDE.md`) and a coherence
plane (one-way Whisper frames). The bring-up stack is `SD card → RP2350
(RISC-V southbridge, SPI @ ~2 MHz) → FPGA SPU-13 core`: RP2350 owns boot,
filesystem, chord streaming, and USB CDC telemetry, while the FPGA does
rational arithmetic, the QR register file, and RPLU2 pipeline control.
SPU-13-class fabrics (Tang 25K and larger) are always "T1 — southbridge"
in that tier model; only the smallest SPU-4 fabrics are exempted down to
bare-pin "T0." Determinism is a pin-boundary guarantee — the SPU's timing
claims end at the FPGA pins, and every hop beyond them (MCU, USB, radio)
carries frames unchanged in content but adds nondeterministic latency.
Full tier definitions, the homogeneity contract, and radio/LAN feasibility
are in `INTERCONNECT_ARCHITECTURE.md`; don't re-derive them here.

---

## 9. Positioning: determinism vs. "no floating point," and market segment

"No floating point" and SPU-13's determinism are not the same claim, and
conflating them undersells what's actually different here. Plenty of
embedded silicon has no FPU — 8051, AVR, RV32I builds without the `F`
extension, low-end Cortex-M0. All of them fall back to fixed-point
arithmetic in software, which still accumulates rounding/truncation error
across operations; it's approximate in a different number format than
IEEE-754, not exact. They also still have real branch-induced pipeline
hazards (branch prediction misses, control-flow-dependent timing jitter)
and variable-latency division — either a multi-cycle `DIV`/`REM`
instruction (RV32M) or a software division loop, neither with a fixed
cycle count.

SPU-13's determinism is a stronger, separate claim: exact closed-field
arithmetic (zero error, not just no floating-point hardware — see §2),
zero branches in hot paths (control flow compiles to `MUX` Boolean
polynomials per `CLAUDE.md`, so there is no branch-prediction or hazard
jitter to begin with, not just hazards that happen to resolve correctly),
and zero division anywhere in the core ALU. The closer analogs to this
property are DO-178C/avionics WCET-bounded branchless coding standards
and constant-time cryptographic implementations (branchless for
side-channel resistance) — not mainstream embedded MCUs, which solve a
different problem (cost and power) with different tools.

That distinction also maps onto where each core is aimed. **SPU-13 is not
a budget-segment part.** It targets Tang Primer 25K and larger fabrics,
with Wukong Artix-7 100T as the primary integration target for full
concurrent operation (§6) — that's a deliberate fit, not a stopgap; the
RPLU2/Padé and Lucas MAC pipelines need the DSP and slice budget those
fabrics provide. **SPU-4 Sentinel is the budget-accessible path** —
currently proven at 835 LUT4 / 390 ALU / 336 DFF on Tang 25K (measured
2026-08-14, includes the UART probe fixture), with fit on smaller/cheaper
fabrics than Tang 25K explicitly **open, not yet proven** — an aspiration
tracked as a real goal, not a shipped result. See
`knowledge/SPU4_ARCHITECTURE.md` for that core's architecture and current
status; don't cite SPU-4's LUT numbers as SPU-13 evidence or vice versa,
they answer different questions about different fabrics.

---

## 10. Where to go next

| Topic | Document |
|---|---|
| Canonical ISA / opcode encoding | `knowledge/isa_reference.md` |
| Register/opcode quickstart, worked examples | `knowledge/ISA_QUICKSTART.md` |
| Clock domains, Fibonacci dispatch derivation | `knowledge/CLOCK_ARCHITECTURE.md` |
| Field-arithmetic mathematical lineage | `knowledge/MATHEMATICAL_FOUNDATIONS.md` |
| Davis Gate normative formula | `knowledge/SPU_LEXICON.md` |
| Lucas Phinary MAC | `knowledge/LUCAS_PHINARY_MAC.md` |
| SOM product contract | `docs/SOM_V1_PRODUCT_CONTRACT.md` |
| IROTC spec | `docs/IROTC_SPEC.md` |
| Interconnect tiers / southbridge protocol | `knowledge/INTERCONNECT_ARCHITECTURE.md` |
| Current silicon-vs-testbench status (authoritative) | `AGENTS.md` |
| Raw hardware evidence, per-probe | `docs/hardware_evidence.md` |
| SPU-4 Sentinel architecture | `knowledge/SPU4_ARCHITECTURE.md` |
