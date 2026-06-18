# ROTC Angles & Rational Robotics Bring-Up Plan

Date: 2026-06-17

This plan covers proving all six corrected ROTC angles in silicon and rebuilding
the rational robotics kinematics harness — from simulation oracle through RTL
trace equivalence to FPGA hardware. The ROTC angle catalog was corrected in June
2026 (three legacy defects fixed), and all six angles pass the TDM rotor
testbench. The path to silicon is shorter than for SOM because ROTC shares the
existing math probe infrastructure.

## What's Already Proven

| Layer | Status | Evidence |
|---|---|---|
| Corrected ROTC angle catalog (0–5) | Validated — all determinants = 1, inverses closed | `knowledge/RATIONAL_CURVES_SPEC.md` |
| RTL rotor core (`spu13_rotor_core_tdm.v`) | PASS — all 5 ROTC cases in testbench | `hardware/tests/spu13/spu13_rotc_tdm_tb.v` |
| VM-vs-RTL trace equivalence | PASS — bit-exact for all 6 angles | `software/tests/test_rotc_vm_rtl_trace.py` |
| Rational robotics oracle (Python) | PASS — 56 checks | `software/tests/test_rational_robotics.py` |
| Rational robotics oracle (C++) | PASS — parity with Python | `software/common/tests/spu_rational_robotics_test.cpp` |
| Math probe synthesis (rotor + Davis + RPLU) | Synthesises on 25K | `build_25k_spu13_math_probe.sh` |
| ROTC opcode in VM | Opcode 0x1D `ROTC` | `software/spu_vm.py` |
| `rotc_proof.lith` program | A₄ orbit closure proof | `software/programs/rotc_proof.lith` |
| Pell inverse closure | r × r_inv = 1 (exact) | `test_rational_robotics.py:57` |
| F/G/H circulant inverse closure | joint → inverse → recovered | `test_rational_robotics.py` (56 checks) |

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
# Expected: 56 passed, 0 failed

python3 software/tests/test_rotc_vm_rtl_trace.py
# Expected: PASS — all 6 angles bit-exact between VM and RTL
```

The 56 robotics checks cover:
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

### 1.2 ROTC-Only Blaze Probe (Optional)

If the full math probe is too large for the damaged 25K, or if we want a
smaller bitstream for fast iteration, create a ROTC-only probe that drops
RPLU, SDRAM, and lattice:

```sh
cp hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_math_probe.ys \
   hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_rotc_probe.ys
```

Change chparam:

```tcl
chparam -set ENABLE_SDRAM 0 \
        -set ENABLE_CORE_RPLU 0 \
        -set ENABLE_CORE_LATTICE 0 \
        -set ENABLE_CORE_MATH 1 \
        -set ENABLE_CORE_SOM 0 \
        spu13_tang25k_top
```

This keeps the rotor core (spu13_rotor_core_tdm.v), rotor vault, and Davis
Gate, but drops all large subsystems. The bitstream should be well under 50%
LUT utilization.

## Phase 2: ROTC Silicon Blaze (Replacement Tang 25K Arrives)

Goal: prove all six corrected ROTC angles in hardware, capturing deterministic
UART telemetry.

### 2.1 Load the Bitstream

```sh
openFPGALoader -b tangprimer25k \
    build/tang_primer_25k_spu13_rotc_probe.fs
```

### 2.2 Per-Angle UART Telemetry Check

For each angle 0–5, execute a `ROTC` instruction and capture the hex output.
The canonical test vector is:

```
QR[0] = (A=1+0√3, B=2+0√3, C=3+0√3, D=4+0√3)
```

Expected UART hex output per angle:

| Angle | Expected hex_q (label) | Expected hex_r (flags) | Notes |
|---:|---|---|---|
| 0 | FFFE 0002 | 0000 0000 | Identity: A=(1,0), B=(2,0), C=(3,0), D=(4,0) |
| 1 | 0000 0005 | (check trace) | Period-6 step: B rotated by thirds |
| 2 | 0000 0004 | (check trace) | P5 forward: B'=D, C'=B, D'=C |
| 3 | (check trace) | (check trace) | Period-2: B/C/D reflect |
| 4 | (check trace) | (check trace) | Period-6 inverse of angle 1 |
| 5 | 0000 0003 | (check trace) | P5 inverse: B'=C, C'=D, D'=B |

Exact expected hex values are generated by `test_rotc_vm_rtl_trace.py` and
its auto-generated Verilog header. Run the trace test with `--dump` to capture
the exact expected values, then compare against silicon UART output.

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

Expected UART: `H:0000 0000` (zero quadray = closure proven).

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

1. Angle 2 does not toggling the multiplier DSPs (power/thermal proxy).
2. Angle 5 does not toggle the multiplier DSPs.
3. Both produce bit-exact matches to the VM trace.

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

Create `software/tests/test_rotc_six_step_rtl_trace.py` if it doesn't exist yet,
or extend it to cover all six angles. This test:

1. Generates a Verilog testbench that runs the six-step trace for a given angle.
2. Each phase: apply forward angle, apply inverse angle, assert recovery.
3. Phase 5: assert orbit closure.
4. All phases: assert inverse_balanced flag.

```sh
python3 software/tests/test_rotc_six_step_rtl_trace.py
# Expected: PASS — all 6 angles, all 6 phases, all inverse-balanced
```

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

Once the six-step trace is proven in silicon and the inverse-closure hardware
passes testbenches:

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

- [ ] Phase 0.1: Oracle tests pass (56 robotics + ROTC trace)
- [ ] Phase 0.2: Golden VCD traces generated (ROTC + six-step)
- [ ] Phase 0.3: Robotics trace pack built (all 6 angles, Pell, FK/IK)
- [ ] Phase 0.4: Host visual renderer for Rotor/Kinematics map
- [ ] Phase 1.1: Math probe synthesis passes
- [ ] Phase 2.1: Bitstream loads on replacement 25K
- [ ] Phase 2.2: All 6 angles produce correct UART hex output
- [ ] Phase 2.3: Period closure verified for angles 1, 2, 3, 5
- [ ] Phase 2.4: Inverse pair round-trips verified (1↔4, 2↔5, 3↔3)
- [ ] Phase 2.5: P5 bypass angles produce zero DSP activity
- [ ] Phase 3.2: Six-step RTL trace test passes all angles
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
