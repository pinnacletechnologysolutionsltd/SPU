# ROTC Angles & Rational Robotics Bring-Up Plan

Date: 2026-07-01

This plan covers proving all six corrected ROTC angles in silicon and rebuilding
the rational robotics kinematics harness — from simulation oracle through RTL
trace equivalence to FPGA hardware. The ROTC angle catalog was corrected in June
2026 (three legacy defects fixed), and all six angles pass the TDM rotor
testbench. The corrected ROTC primitive layer and the period-6 six-step
kinematics harness are now Tang 25K silicon-verified; the remaining work in this
plan is broader trace-pack production, generalized FK/IK hardware, and RPLU
trajectory correction.

## What's Already Proven

| Layer | Status | Evidence |
|---|---|---|
| Corrected ROTC angle catalog (0–5) | Validated — all determinants = 1, inverses closed | `knowledge/RATIONAL_CURVES_SPEC.md` |
| RTL rotor core (`spu13_rotor_core_tdm.v`) | PASS — all 5 ROTC cases in testbench | `hardware/tests/spu13/spu13_rotc_tdm_tb.v` |
| VM-vs-RTL trace equivalence | PASS — bit-exact for all 6 angles | `software/tests/test_rotc_vm_rtl_trace.py` |
| Tang 25K ROTC silicon probe | PASS — UART `ROTC:P A:5 E:00` | `build_25k_spu13_rotc_probe.sh` |
| Six-step VM-vs-RTL trace | PASS — angle-1 period-6 forward/inverse closure | `software/tests/test_rotc_six_step_rtl_trace.py` |
| Tang 25K six-step robotics probe | PASS — UART `KIN:P P:5 E:00` | `build_25k_spu13_six_step_probe.sh` |
| Rational robotics oracle (Python) | PASS — 104 checks | `software/tests/test_rational_robotics.py` |
| Rational robotics oracle (C++) | PASS — parity with Python | `software/common/tests/spu_rational_robotics_test.cpp` |
| Math probe synthesis (rotor + Davis + RPLU) | Synthesises on 25K | `build_25k_spu13_math_probe.sh` |
| ROTC opcode in VM | Opcode 0x1D `ROTC` | `software/spu_vm.py` |
| `rotc_proof.lith` program | A₄ orbit closure proof | `software/programs/rotc_proof.lith` |
| Pell inverse closure | r × r_inv = 1 (exact) | `test_rational_robotics.py:57` |
| F/G/H circulant inverse closure | joint → inverse → recovered | `test_rational_robotics.py` (104 checks) |

## Corrected ROTC Angle Catalog

The legacy table had three defects: angle 2 was documented with thirds
coefficients while hardware bypassed it as P5 permutation; angle 3 was singular
(det=0); angle 5 duplicated angle 1. The corrected catalog:

| ROTC angle | Name | F | G | H | Period | Inverse | RTL path |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | identity | 1 | 0 | 0 | 1 | 0 | bypass — A_out=A_in |
| 1 | thirds period-6 | 2/3 | 2/3 | -1/3 | 6 | 4 | TDM: 9 surd mults + /3 |
| 2 | P5 forward cycle | 0 | 1 | 0 | 3 | 5 | bypass_p5 — pure bit permute |
| 3 | thirds period-2 | -1/3 | 2/3 | 2/3 | 2 | 3 | TDM: 9 surd mults + /3 |
| 4 | thirds period-6 inverse | 2/3 | -1/3 | 2/3 | 6 | 1 | TDM: 9 surd mults + /3 |
| 5 | P5 inverse cycle | 0 | 0 | 1 | 3 | 2 | bypass_p5_inv — pure bit permute |

**RTL encoding:** Angles 0–3 use the TDM circulant path (F,G,H surd multiplies
+ optional /3). Angles 2 and 5 use hardware bypass (zero multiplies). Angle 0
is identity (A passes through unchanged).

## Phase 0: Simulation Baseline (Now — No FPGA Required)

Goal: establish the golden trace pack against which every subsequent silicon
test will be compared.

### 0.1 Run Oracle Tests

```sh
python3 software/tests/test_rational_robotics.py
# Expected: PASS (104 checks)

python3 software/tests/test_rotc_vm_rtl_trace.py
# Expected: PASS — all 6 angles bit-exact between VM and RTL
```

The 104 robotics checks cover:
- Pell inverse closure (scalar and vector)
- F/G/H circulant determinant = 1 for all joints
- Circulant inverse closure (5 joints)
- Circulant period matches expected values
- FK chain identity
- FK/inverse-FK round-trip closure
- Six-step kinematics trace: every phase inverse-balanced, orbit closes at phase 5
- Legacy table audit: all three known defects confirmed

### 0.2 Generate Golden Trace Files

```sh
# ROTC trace: all 6 angles on a canonical test vector
python3 software/tests/test_rotc_vm_rtl_trace.py --dump build/rotc_golden.vcd

# Six-step robotics trace: forward/inverse closure per phase
python3 software/tests/test_rotc_six_step_rtl_trace.py --dump build/rotc_six_step_golden.vcd
```

These VCD files are the regression reference. Any future change to the rotor
core, the F/G/H coefficient tables, or the Pell vault must reproduce these
traces bit-exact.

### 0.3 Robotics Trace Pack

Build a JSON trace pack containing the robotics demo artifact set:

```sh
python3 tools/rational_robotics_trace.py --output build/robotics_trace_pack.json
```

The pack should contain:

1. **Six-step trace** for angle 1 (thirds period-6): phases 0–5, each with
   commanded vector, recovered vector, closure error, inverse balance flag.
2. **Pell orbit closure**: 12 Pell steps on a unit vertex, returning to within
   1 LSB of start.
3. **FK/IK round-trip**: 3-joint chain, forward to end-effector, inverse back
   to base, closure error zero.
4. **Full orbit table**: all 12 A₄ rotations applied to a VE seed vertex,
   proving orbit spans all 12 tetrahedral vertices.

These traces are the public demo artifacts and the RTL test vectors for
hardware verification. Keep under `build/`, not in the repo.

### 0.4 Host Visual Renderer for Robotics

Extend the Phase 0 host renderer (from `docs/som_bringup_plan.md` and
`docs/visual_som_devboard_plan.md`) to include the Rotor/Kinematics map view
(type 0x04):

1. Plot the ABCD components of the commanded trajectory as a tetrahedral
   projection.
2. Overlay recovery vectors (commanded → recovered).
3. Color-code by inverse balance: green = balanced, red = unbalanced
   (should never happen with corrected angles).
4. Animate the Pell orbit and the six-step trace as frame sequences.

## Phase 1: Synthesis Integration (Now — Dry Run)

Goal: confirm the existing math probe synthesis works with all ROTC test
vectors and determine whether a ROTC-only probe is needed.

### 1.1 Verify Math Probe Synthesis

The existing `build_25k_spu13_math_probe.sh` already synthesises the rotor
core + Davis + RPLU path. Verify it passes synthesis and resource check:

```sh
bash build_25k_spu13_math_probe.sh
```

Record Yosys resource report:
```
LUTs:  [record here]
FFs:   [record here]
BRAMs: [record here]
DSPs:  [record here]
```

### 1.2 ROTC-Only Blaze Probe

The dedicated ROTC probe is the hardware acceptance image for the corrected
angle catalog:

```sh
bash build_25k_spu13_rotc_probe.sh
```

It instantiates `spu13_rotor_core_tdm` directly, feeds the canonical VM/RTL
trace vector through all six corrected angles, then repeats closure loops for
all non-identity periods. The 2026-06-30 Tang 25K route reports 13,352 LUT4 /
1,036 DFF / 1,044 ALU, 0 BRAM, 0 DSP, and 73.07 MHz max frequency at the
12 MHz target.

## Phase 2: ROTC Silicon Blaze

Goal: prove all six corrected ROTC angles in hardware, capturing deterministic
UART telemetry.

2026-06-30 status: complete on Tang Primer 25K. SRAM load of
`build/tang_primer_25k_spu13_rotc_probe.fs` repeatedly reports:

```text
ROTC:P A:5 E:00
```

`A:5` confirms the final corrected angle was reached; `E:00` confirms no trace
or closure mismatch.

### 2.1 Load the Bitstream

```sh
openFPGALoader -b tangprimer25k \
    build/tang_primer_25k_spu13_rotc_probe.fs
```

### 2.2 Probe-Internal Per-Angle Check

The dedicated Tang probe does not stream every intermediate vector over UART.
Instead, it compares each hardware result against the canonical VM/RTL trace
inside the FPGA and emits one compact status line. Lanes are packed as
`{sqrt3_part[31:0], rational_part[31:0]}`. The canonical test vector is:

```
QR[0] = (
  A = 64'h0000000000000001,
  B = 64'h0000000200000002,
  C = 64'h0000000300000003,
  D = 64'h0000000400000004
)
```

Expected internal trace results:

| Angle | Expected B/C/D lane order | Notes |
|---:|---|---|
| 0 | B=(2,2), C=(3,3), D=(4,4) | Identity |
| 1 | B=(3,3), C=(2,2), D=(4,4) | Period-6 thirds step |
| 2 | B=(4,4), C=(2,2), D=(3,3) | P5 forward bypass |
| 3 | B=(4,4), C=(3,3), D=(2,2) | Period-2 thirds step |
| 4 | B=(2,2), C=(4,4), D=(3,3) | Period-6 inverse thirds step |
| 5 | B=(3,3), C=(4,4), D=(2,2) | P5 inverse bypass |

The accepted UART result is `ROTC:P A:5 E:00`. Any mismatch emits
`ROTC:F A:<angle> E:<code>`.

### 2.3 Period Closure Check

For each angle with period > 1:

```asm
QLDI  R0, 1, 0, 2, 0, 3, 0, 4, 0    ; canonical test vector
ROTC  R1, R0, 1                       ; apply angle
ROTC  R2, R1, 1                       ; re-apply (phase 2)
ROTC  R3, R2, 1                       ; re-apply (phase 3)
ROTC  R4, R3, 1                       ; re-apply (phase 4)
ROTC  R5, R4, 1                       ; re-apply (phase 5)
ROTC  R6, R5, 1                       ; re-apply (phase 6)
; After period applications, R[N] should equal R0
QSUB  R7, R6, R0                      ; R7 should be (0,0,0,0)
QLOG  R7                              ; emit to UART
```

Expected hardware proof in the dedicated probe: `ROTC:P A:5 E:00` (zero
closure mismatch across the self-check loops).

### 2.4 Inverse Pair Check

For each angle and its documented inverse, prove round-trip closure:

```asm
ROTC  R1, R0, 1     ; forward: angle 1
ROTC  R2, R1, 4     ; inverse: angle 4
QSUB  R3, R2, R0    ; should be zero
```

Check all three inverse pairs: (1↔4), (2↔5), (3↔3).

### 2.5 P5 Bypass Specifics

Angles 2 and 5 use hardware bypass — the rotor core detects `bypass_p5` or
`bypass_p5_inv` and skips all 9 surd multipliers. Verify that:

1. The dedicated probe routes with 0 DSPs.
2. Angle 2 uses the P5 forward bypass and matches the VM trace.
3. Angle 5 uses the P5 inverse bypass and matches the VM trace.

## Phase 3: Six-Step Robotics Kinematics Harness Rebuild

Goal: rebuild the six-step rational robotics kinematics harness that was
mentioned as an immediate action in the commercialization roadmap.

### 3.1 Python Harness

The oracle already has `six_step_kinematics_trace()` in
`rational_robotics.py:340`. The harness wraps this into a runnable command-line
tool:

```sh
# Run the six-step trace and emit JSON
python3 tools/rational_robotics_trace.py --angle 1 --output build/robotics_six_step.json

# Run all six angles
for angle in 0 1 2 3 4 5; do
    python3 tools/rational_robotics_trace.py --angle $angle --output build/robotics_six_step_angle${angle}.json
done
```

### 3.2 RTL Fixture for Six-Step Trace

`software/tests/test_rotc_six_step_rtl_trace.py` exists and passes for the
angle-1 period-6 six-step orbit. This test:

1. Generates a Verilog testbench that runs the six-step trace for a given angle.
2. Each phase: apply forward angle, apply inverse angle, assert recovery.
3. Phase 5: assert orbit closure.
4. All phases: assert inverse_balanced flag.

```sh
python3 software/tests/test_rotc_six_step_rtl_trace.py
# Expected: ROTC SIX-STEP RTL TRACE: PASS
```

### 3.2a Tang 25K Six-Step Silicon Probe

`build_25k_spu13_six_step_probe.sh` is the dedicated Tang 25K hardware proof
for the current six-step harness. It instantiates the same TDM rotor datapath
used by the ROTC probe, then checks:

1. Six forward phases using corrected ROTC angle 1.
2. Angle-4 inverse recovery after every commanded phase.
3. No premature return to the root vector on phases 0-4.
4. Exact return to the root vector on phase 5.

Hardware-verified result:

```text
KIN:P P:5 E:00
```

2026-07-01 routed footprint: 13,576 LUT4 / 1,518 DFF / 1,024 ALU / 0 BRAM /
0 DSP. Post-route max frequency is 77.25 MHz at the 12 MHz target.

### 3.3 Robotics Trace Pack Production

Combine all artifacts into a single trace pack:

```
build/robotics_trace_pack/
├── rotc_golden.vcd                  # All 6 angles, canonical vector
├── rotc_six_step_golden.vcd         # Six-step forward/inverse per angle
├── robotics_six_step_angle0.json    # Identity (trivial)
├── robotics_six_step_angle1.json    # Period-6 forward
├── robotics_six_step_angle2.json    # P5 forward
├── robotics_six_step_angle3.json    # Period-2
├── robotics_six_step_angle4.json    # Period-6 inverse
├── robotics_six_step_angle5.json    # P5 inverse
├── pell_orbit_closure.json          # 12 Pell steps → closure
├── fk_ik_roundtrip.json             # 3-joint FK/IK → closure
└── README.txt                       # How to regenerate from source
```

This is the deliverable for the `commercialization_and_development_roadmap.md`
Phase 0 item: "Create a robotics trace pack: commanded path, injected error,
RPLU correction, corrected path."

## Phase 4: RTL Robotics Primitives (New Hardware)

The `knowledge/RATIONAL_CURVES_SPEC.md` RTL Handoff Order lists seven steps
for new robotics hardware. Phase 4 implements steps 1–4 (inverse closure)
before touching RPLU trajectory correction.

### 4.1 Pell Inverse Path

```verilog
// In spu_rotor_vault.v: add inverse path
// Forward: multiply by r = (2, 1)   // Pell forward
// Inverse: multiply by r_inv = (2, -1)  // Pell inverse
// Both use the same vault entry, but negate surd coefficient for inverse
```

Module: extend `spu_rotor_vault.v` with an `inverse` input port. When asserted,
use conjugate coefficients for the Pell step.

### 4.2 F/G/H Inverse Coefficient Generator

```verilog
// In new spu_robotics_inverse.v
// Given F, G, H as input:
//   F_inv = F*F - G*H
//   G_inv = H*H - F*G
//   H_inv = G*G - F*H
// Cost: 6 surd multiplies (can share with rotor core TDM)
```

This module generates inverse circulant coefficients from forward coefficients.
It can be instantiated alongside `spu13_rotor_core_tdm.v` or share its TDM
multiplier.

### 4.3 Single-Joint Forward/Inverse Closure

Create `spu_robotics_fk.v` — a module that:

1. Accepts a QuadrayVector and a joint (axis_id, F, G, H).
2. Applies forward rotation.
3. Applies inverse rotation.
4. Computes closure error.
5. Asserts inverse_balanced flag.

Testbench: `spu_robotics_fk_tb.v` — exercises all six corrected angles and
asserts bit-exact closure.

### 4.4 FK Chain Execution

Extend `spu_robotics_fk.v` to support chained joints:

```verilog
// FK chain: base → joint[0] → joint[1] → ... → end_effector
// Inverse FK: end_effector → joint[n]⁻¹ → ... → joint[0]⁻¹ → base
// Assert: closure_error == 0
```

Testbench exercises 2-joint, 3-joint, and 6-joint chains with all corrected
angles.

### 4.5 Synthesis Budget

The new modules add surd multiplier reuse (TDM path) rather than new DSPs.
Estimated resource cost:

| Module | LUTs | FFs | DSPs | BRAMs |
|---|---|---|---|---|
| `spu_robotics_inverse.v` | ~50 | ~100 | 0 (reuses TDM) | 0 |
| `spu_robotics_fk.v` | ~80 | ~200 | 0 (reuses TDM) | 0 |
| **Total** | ~130 | ~300 | 0 | 0 |

With the existing full probe at ~96% LUT utilization on the 25K, the new
robotics modules may need a dedicated robotics-only bitstream that drops
GPU, audio, and bio stubs.

## Phase 5: RPLU Trajectory Correction (Post Silicon Blaze)

Once generalized inverse-closure hardware passes testbenches:

### 5.1 Trajectory Error → RPLU Address

```verilog
// spu_rplu_trajectory.v
// error = commanded - actual                    // QuadrayVector
// error_quadrance = quadrance(error)            // scalar
// rplu_addr = hash_to_rplu(error_quadrance)      // index
// correction = rplu_lookup(rplu_addr)            // correction vector
// corrected = commanded + correction             // output
```

The RPLU trajectory correction table is pre-computed from simulation data and
loaded at boot alongside the material RPLU table.

### 5.2 Robotics Demo Program

```asm
;; rational_robotics_demo.lith
;; Full robotics pipeline: command → sense error → RPLU correct → verify

;; Hydrate QR register file with VE seed vertices
QLDI  QR0, 0, 0, -1, 1      ; VE vertex
QLDI  QR1, 1, 0, 0, 0       ; basis axis

;; Six-step kinematics
ROTC  QR2, QR0, 1            ; forward step
ROTC  QR3, QR2, 1            ; step 2
ROTC  QR4, QR3, 1            ; step 3
ROTC  QR5, QR4, 1            ; step 4
ROTC  QR6, QR5, 1            ; step 5
ROTC  QR7, QR6, 1            ; step 6 — orbit closes

;; Verify closure
QSUB  QR8, QR7, QR0          ; should be zero
QLOG  QR8                    ; emit → H:0000 0000

;; Inverse closure
ROTC  QR9, QR1, 1            ; forward: angle 1
ROTC  QR10, QR9, 4           ; inverse: angle 4
QSUB  QR11, QR10, QR1        ; should be zero
QLOG  QR11                   ; emit → H:0000 0000
```

## Telemetry ABI: Rotor/Kinematics Frame (type 0x04)

```
byte  0      magic 0x53
byte  1      magic 0x56
byte  2      version 0
byte  3      frame_type = 0x04
byte  4..7   sequence
byte  8..11  cycle_count
byte 12..13  flags
byte 14..15  payload_len
byte 16      rotor_phase (0–5 for six-step, 0–7 for Pell)
byte 17      forward_angle (0–5)
byte 18      inverse_angle (0–5)
byte 19      flags: [0]=forward_active, [1]=inverse_balanced, [2]=orbit_closed
byte 20..21  axis_pair (active axis ID)
byte 22..25  quadrance_error (32-bit surd)
last 4       crc32
```

## Proof Checklist

- [x] Phase 0.1: Oracle tests pass (104 robotics + ROTC trace)
- [ ] Phase 0.2: Golden VCD traces generated (ROTC + six-step)
- [ ] Phase 0.3: Robotics trace pack built (all 6 angles, Pell, FK/IK)
- [ ] Phase 0.4: Host visual renderer for Rotor/Kinematics map
- [x] Phase 1.1: Math probe synthesis passes
- [x] Phase 1.2: Dedicated ROTC probe builds and routes
- [x] Phase 2.1: Bitstream loads on Tang 25K
- [x] Phase 2.2: All 6 angles match the canonical trace in silicon
- [x] Phase 2.3: Period closure verified for angles 1, 2, 3, 4, 5
- [x] Phase 2.4: Inverse pair round-trips verified for the angle-1/angle-4 six-step harness
- [x] Phase 2.5: P5 bypass angles route with 0 DSP in the dedicated probe
- [x] Phase 3.2: Period-6 angle-1 six-step RTL trace passes
- [x] Phase 3.2a: Tang 25K six-step silicon probe passes with UART `KIN:P P:5 E:00`
- [ ] Phase 3.2b: Extend six-step RTL trace pack to all non-identity periods
- [ ] Phase 3.3: Complete trace pack produced
- [ ] Phase 4.1: Pell inverse path testbench passes
- [ ] Phase 4.2: F/G/H inverse generator testbench passes
- [ ] Phase 4.3: Single-joint closure testbench passes
- [ ] Phase 4.4: FK chain closure testbench passes
- [ ] Phase 5.2: Full robotics demo program assembles and simulates

## References

- Corrected angle catalog: `knowledge/RATIONAL_CURVES_SPEC.md` lines 114–153
- Robot core RTL: `hardware/rtl/core/spu13/spu13_rotor_core_tdm.v`
- Rotor vault RTL: `hardware/rtl/core/shared/spu_rotor_vault.v`
- TDM rotor testbench: `hardware/tests/spu13/spu13_rotc_tdm_tb.v`
- VM-vs-RTL trace test: `software/tests/test_rotc_vm_rtl_trace.py`
- Six-step RTL trace test: `software/tests/test_rotc_six_step_rtl_trace.py`
- Robotics oracle: `software/lib/rational_robotics.py`
- Robotics tests: `software/tests/test_rational_robotics.py`
- C++ robotics: `software/common/include/spu_rational_robotics.h`
- C++ robotics tests: `software/common/tests/spu_rational_robotics_test.cpp`
- ROTC proof program: `software/programs/rotc_proof.lith`
- RPLU bring-up guard: `docs/rplu_bringup_guard.md`
- SOM bring-up plan: `docs/som_bringup_plan.md`
- Commercialization roadmap: `docs/commercialization_and_development_roadmap.md`
