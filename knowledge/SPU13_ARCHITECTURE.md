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

The representation depends on the implementation surface; there is no universal
32-bit `RationalSurd` register format across this repository.

| Surface | Representation | Bounds / failure scope |
|---|---|---|
| Python VM `RationalSurd` | Integer coefficients `a,b`, representing `a+b√3`; additional rotor metadata | Python integer arithmetic; not a finite-width hardware oracle by itself |
| C++ VM `RationalSurd` | Two `int32_t` coefficients plus rotor metadata | Existing arithmetic narrows results; it does not implement the CPU tuple overflow contract |
| Legacy Quadray RTL | Default 64-bit component: `[63:32]=Q`, `[31:0]=P` | Four components per QR entry; finite-width arithmetic and scale are module-specific |
| Main manifold lane | 64 bits, with packing/scale interpreted by its selected arithmetic path | Not an alias of a software scalar register |
| Opt-in CPU Surd bank | Eight independent 192-bit tuples: signed 64-bit `a,b`, unsigned positive 64-bit `d` | `(a+b√3)/d`; exact checks, normalization and failure-preserving retirement |

Sources: `software/spu_vm.py`, `software/vm/spu_vm.cpp`,
`hardware/rtl/core/shared/spu_quadray_regfile.v`, and
`hardware/rtl/core/spu13/spu13_surd_exec.v`. The older 16+16-bit description
in this map did not describe the active QR component ports. Do not infer a
layout from the name `RationalSurd` alone.

Integer coefficient pairs are closed under add/sub/mul in `Z[√3]`:

```
add : (P1+P2, Q1+Q2)
sub : (P1-P2, Q1-Q2)
mul : (P1P2 + 3Q1Q2, P1Q2 + Q1P2)
```

Finite-width storage is not closed under arbitrary products. In the legacy
QR packing, `{32'd0,32'd1}` encodes real one; it is a 64-bit literal.
Packing, coefficient order, scale and truncation/overflow behavior must be
read from the actual module.

The CPU extension preserves full intermediates, commits fitting raw results
unreduced (including zero), and invokes exact normalization on overflow.
Scheduled `SNORM` always canonicalizes, including zero to `(0,0,1)`.
Unrescued overflow or invalid input preserves the destination. Bounded
shift/compare/subtract quotient generation implements mathematical division;
it avoids runtime RTL `/` and `%` operators, not division as a mathematical
operation. Historical S0 zero-canonicalization evidence remains separate.

Two extensions layer on top of the base `Q(√3)` field:

- **`A₃₁`** — arithmetic over the Mersenne prime `p = 2³¹−1`, basis
  `[1, √3, √5, √15]`, used by the RPLU2/Padé pipeline
  (`spu13_m31_multiplier.v`, `spu13_m31_inverter.v`, `spu13_fp4_inverter.v`).
- **`Z[φ]/L_p`** — a Lucas-prime modulus ring (`φ² = φ + 1`), used by the
  Lucas Phinary MAC (`spu13_lucas_mac.v`).

Legacy spread/comparison paths avoid quotient evaluation: ratios are
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

Clock topology is build-specific. The opt-in CPU benchmark uses a direct
25 MHz clock; the following describes the historical Tang timing model, not
Surd instruction latency.

The historical Tang integration uses two clock domains: a fast TDM domain (`clk_fast`, 24 MHz on
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

The software register namespace and physical storage are distinct:

| Storage / namespace | Layout | Integration scope |
|---|---|---|
| Python/C++ VM scalars | `R0`–`R25`, 26 entries | Software model; no physical 26-entry scalar bank established in the inspected main core |
| Main manifold | 13 × 64-bit lanes | `spu13_core.v`; indexed axes 0–12 |
| Main Quadray bank | `QR0`–`QR12`, each 4 × 64-bit components | ECC or non-ECC implementation selected by the core |
| CPU Surd bank | `S0`–`S7`, each 192-bit tuple | Opt-in `ENABLE_SURD_CPU`; separate from R/QR state |
| `spu13_multi_port_regfile.v` | 16 × 32 bits; R0 hardwired zero; 4 read / 2 write ports | Separate module, not instantiated by the inspected `spu13_core.v` |
| Older `spu_register_file.v` | 8 × 18 bits; slot-gated falling-edge writes | Separate implementation, not the canonical scalar namespace |

The previous claim that R1–R12 mirror 13 axes was unsupported: that range has
12 indices. No physical scalar-to-axis mirroring is asserted here.

Instructions retain the canonical 64-bit layout:
`[63:56] Op | [55:48] R1 | [47:40] R2 | [39:24] P1_A | [23:8] P1_B`,
with bits `[7:0]` reserved. `knowledge/isa_reference.md` owns the encoding;
`docs/spu13_isa_spec.md` describes the separate experimental WF adapter.

The canonical control boundary is `CALL=0x20`, `RET=0x21`, `QREAD=0x22`.
`COND` has no allocated canonical encoding. October 10 repairs resolve the Python/assembler collision and align C++
control values in focused checks; full qualification remains pending. See
[control reconciliation](../docs/isa/CANONICAL_CONTROL_RECONCILIATION.md).
These software repairs do not implement missing core fetch/PC/stack behavior.

| Current core handler | Scope |
|---|---|
| QLDI, QSUB, ROTC, DELTA, HEX | Explicit handlers in `spu13_core.v`; semantics and limits remain operation-specific |
| IROTC, LOAD2X, SCALE2 | Feature-gated IROTC path |
| REGEN | Explicit boundary module; preserve state on rejection |
| SLI/SLD/SRD/SMUL/SADD/SSUB/SNORM/SSTAT | Opt-in CPU Surd extension, opcodes 0x70–0x77 |
| SOM/SOM_TRAIN, JSCR, NSA, legacy polynomial control | Feature-specific paths; not universal core capabilities |
| Other accepted words | Includes catch-all completion; completion alone does not prove execution of a documented opcode |

No JMP/CALL/RET execution handler or full scalar VM instruction interpreter
was established in the inspected `spu13_core.v`. `spu_instr_decode.v` is a
separate QR-dispatch helper with its own ports; it is not instantiated by that
core. A common instruction layout does not imply complete VM/RTL parity or
an implemented program-fetch path. Evidence must identify the exact top,
feature configuration and operation.

CPU Surd status: retained focused CPU simulation and regression/Padé records
passed; the selective REGEN candidate has directed mapped arithmetic PASS,
overall qualification FAILED, and integrated timing unresolved. No CPU tuple
extension silicon claim is made. See
[the failure diagnosis](../docs/isa/SURD_QUALIFICATION_DIAGNOSIS.md).

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

**Exact modular arithmetic — `A₃₁` / M31**  
(M31 is a prime field; `A₃₁` over it is a split algebra with zero divisors — see `knowledge/SPU_LEXICON.md`.)
`spu13_m31_multiplier.v` (+ `_seq`, `_structured` variants),
`spu13_m31_inverter.v` (binary extended Euclidean over M31),
`spu13_fp4_inverter.v` / `_structured` / `_structured_arithmetic`
(conjugate reduction tower for units of the split `A₃₁` algebra), `spu13_batch_inverter.v`
(Montgomery batch inversion), `spu13_jet_mac.v` / `spu13_jet_inv.v` (jet
ring MAC/inverse over `A₃₁[ε]/(ε^(n+1))`), `spu13_nsa_core.v` /
`spu13_nsa_dual_alu.v` (dual-number arithmetic for FSDG).

**Ring arithmetic — `Z[φ]`**
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

The current southbridge command plane is SPI, with the live decoder in
`hardware/rtl/peripherals/io/spu_spi_slave.v`. It carries status, manifold,
QR telemetry, instruction words and configuration transactions.
`spu13_southbridge_token_parser.v` is a narrow CRC helper, not that live
decoder. RP2350 firmware supplies board-specific SPI, SD boot and USB paths;
its Tang 2 MHz setting must not be copied to a divided Artix clock.

GPU UART scene packets are a separate versioned interface. Their start byte
may also be 0xA5, but packet lengths, payload order and commit behavior are
not the southbridge configuration protocol. See
[transport boundaries](../docs/TRANSPORT_BOUNDARIES.md) and the existing
southbridge protocol / GPU runbooks for the exact profile.

A future Kintex PCIe northbridge would coexist with the RP2350 southbridge.
PCIe program/data/configuration/completion transport does not create another
ISA. Card-specific PCIe configuration, DMA/MMIO/queue semantics, clocks,
reset, ownership and backpressure remain future specification work; no
PCIe implementation or CPU/GPU concurrent fit is claimed here.

---

## 9. Positioning: determinism vs. "no floating point," and market segment

Exactness is an operation contract, not a consequence of lacking an FPU.
Integer and fixed-scale arithmetic can be exact when the supported domain
closes at the chosen scale. Each SPU path must state its representation,
widths, reduction policy and representability boundary; legacy narrowing or
rotor-third truncation cannot inherit the CPU Surd failure contract.

The opt-in CPU Surd extension preserves its exact represented result when
it fits, or reports failure without committing the destination. Normalization
uses integer GCD and exact quotient algorithms with input-dependent bounded
latency. Fit-path latency is not complete instruction/kernel latency.

Branchless Boolean/mux forms are a policy for selected kernels. They do not
make an ISA with JMP/CALL/RET universally branchless, nor prove the current
main core implements those control instructions. Timing and determinism
claims must name the actual clock, operation, outcome and evidence surface.

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
| Governance and verification rules | `AGENTS.md` |
| Raw hardware evidence, per-probe | `docs/hardware_evidence.md` |
| SPU-4 Sentinel architecture | `knowledge/SPU4_ARCHITECTURE.md` |
