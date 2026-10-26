# SPU Platform Library and Interface Audit

**Date:** 2026-10-15
**Status:** Read-only source audit; no extraction, implementation, or hardware work
**Repository basis:** `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f` plus a dirty working tree

This is the current inventory of software, specifications, devices, and
evidence that could contribute to an SPU platform. It is based on files in the
Git checkout, not on an independent review of every item in the file library.
The checkout contains extensive unrelated modifications and untracked files;
paths below identify the observed sources, not a clean release snapshot.

This audit does not change the accepted `spu13-soft-v1` profile. SIM-0 is
owner-accepted with pinned inputs in
[`SPU13_SOFT_V1_SIM0_ARTIFACTS_2026-10-15.json`](isa/SPU13_SOFT_V1_SIM0_ARTIFACTS_2026-10-15.json).
SIM-1 remains a separate implementation decision under the draft contract
[`contract_spu_sim_sim1_2026-10-15.md`](../spu_strategy/contract_spu_sim_sim1_2026-10-15.md).

## Maturity labels

| Label | Meaning in this inventory |
|---|---|
| `accepted specification` | Owner-accepted, versioned behavior with a pinned source or fixture. It does not imply implementation. |
| `implemented surface` | Source code exists. It may still be partial, experimental, or unqualified. |
| `software tested` | A named software test or fixture covers the stated scope. |
| `RTL tested` | Named testbench evidence exists; this is not physical evidence. |
| `silicon evidence` | A narrow board/image/result is recorded in `docs/hardware_evidence.md`. |
| `proposal` | Described in documentation but not established as an executable interface. |
| `historical` | Retained for provenance; not the authority for current behavior. |

Build status below is determined from checked-in build files and documented
commands only. No build or test was run for this read-only audit.

## Component inventory

| Component and public surface | Sources and authority | Maturity, dependencies, and independent-build status |
|---|---|---|
| **ISA-A and software machine profiles** | Canonical encoding reference: [`knowledge/isa_reference.md`](../knowledge/isa_reference.md). Profile reconciliation and compatibility notes: [`ISA_PROFILE_PROVENANCE.md`](isa/ISA_PROFILE_PROVENANCE.md), [`ISA_IMPLEMENTATION_MATRIX.md`](isa/ISA_IMPLEMENTATION_MATRIX.md), and [`ISA_CONFORMANCE_2026-10-10.md`](isa/ISA_CONFORMANCE_2026-10-10.md). | Broader ISA-A remains a multi-implementation research surface with documented gaps. The SIM-0 accepted software machine profile, `spu13-soft-v1`, admits 14 opcodes and defines strict register checks, fetch-time validation, no flags/data memory/MMIO, and a separate T1d capability. No C++ implementation of that accepted profile exists yet. The current SIM-0 input pin, not a live checkout, governs its ISA source. |
| **ISA-B / Wheeler–Feynman and experimental profiles** | [`docs/spu13_isa_spec.md`](spu13_isa_spec.md), [`hardware/rtl/arch/spu_isa_defines.vh`](../hardware/rtl/arch/spu_isa_defines.vh), and the `OPCODES_WF` table in [`software/tools/spu13_asm.py`](../software/tools/spu13_asm.py). | `proposal` / profile-specific implementation. The word layout and opcode namespace differ from ISA-A. The assembler has an opt-in `--arch wf` path; the main Python VM and C++ VM are not a complete matching ISA-B toolchain. Do not treat it as a compatible extension of `spu13-soft-v1`. |
| **SAS assembler and binary emission** | [`software/tools/spu13_asm.py`](../software/tools/spu13_asm.py), [`software/lib/assembly_operands.py`](../software/lib/assembly_operands.py), and [`software/tools/surd_cpu_encoding.py`](../software/tools/surd_cpu_encoding.py). | `implemented surface`, Python entry point with ISA-A default plus opt-in WF and Surd encoders. It can emit words that are outside the SIM-0 subset; successful assembly is not proof that a VM or RTL target executes them. Depends on Python and local source modules. No standalone packaged SDK build is defined. |
| **Lithic-L / Laminar Lang** | [`knowledge/LITHIC_L_LANGUAGE_SPEC.md`](../knowledge/LITHIC_L_LANGUAGE_SPEC.md), [`knowledge/LITHIC_L_DEEP_DIVE.md`](../knowledge/LITHIC_L_DEEP_DIVE.md), [`software/spu_compiler.py`](../software/spu_compiler.py), [`software/spu_forge.py`](../software/spu_forge.py), and the header [`spu_lithic_l.h`](../software/common/include/spu_lithic_l.h). | The language specification describes a larger language and machine model than the accepted soft profile. Its own status table says the full Laminar parser/type checker is planned. The existing Python compiler is a narrower `.lith` curve/geometry expansion pass to SAS; it is not a general implementation of the specified language. C++ constructors are another source surface and do not establish compiler compatibility. Python/compiler plus assembler can be invoked locally; there is no maintained independent language SDK build or end-to-end target-profile qualification. |
| **Python VM** | [`software/spu_vm.py`](../software/spu_vm.py), [`software/spu_vm_test.py`](../software/spu_vm_test.py), [`software/tests/test_isa_conformance.py`](../software/tests/test_isa_conformance.py), and the focused ISA tests. | `implemented surface`, broad and actively used by Python programs, with targeted software tests. It supports more experimental operations than `spu13-soft-v1`; it uses Python integer behavior and must not be assumed to match finite-width C++ or RTL semantics. Depends on Python and local generated/reference modules for some instruction families. Not a profile-conformant replacement for the future SIM-1 executable. |
| **C++ VM** | [`software/vm/spu_vm.cpp`](../software/vm/spu_vm.cpp), [`software/vm/Makefile`](../software/vm/Makefile), and [`software/tests/isa_conformance_cpp.cpp`](../software/tests/isa_conformance_cpp.cpp). | `implemented surface`, partial ISA-A/legacy ISA-C with a self-contained C++17 build target (`make -C software/vm`). Its arithmetic narrows to `int32_t`; the architecture map documents semantic differences from the Python VM and RTL. It is independently buildable as this candidate VM, but not as an implementation of the accepted SIM-0 profile and not full ISA parity. |
| **Exact C++ mathematics and robotics** | [`software/common/include/`](../software/common/include/) contains `spu_surd.h`, `spu_quadray.h`, `spu_rational_robotics.h`, `spu_ivm.h`, `spu_physics.h`, `spu_wildberger.h`, `spu_rational_som.h`, and related headers. Tests include `software/common/tests/`. | `implemented surface` with focused C++ tests and several exact integer/rational algorithms. This is a collection of headers, not yet a versioned standalone library: no common package manifest or root build target was found. Individual arithmetic domains have distinct widths and failure rules; do not combine them under a universal “exact number” API. |
| **RPLU / Padé / A₃₁** | RTL: [`rplu_thimble_pade.v`](../hardware/rtl/gpu/rplu_thimble_pade.v), [`spu13_rplu2_pade_sidecar.v`](../hardware/rtl/core/spu13/spu13_rplu2_pade_sidecar.v), A₃₁ arithmetic under `hardware/rtl/math/` and `hardware/rtl/core/spu13/`. Software references and generators include [`tools/rplu_python_ref.py`](../tools/rplu_python_ref.py), `tools/generate_pade_44.py`, and the `hardware/rtl/arch/pade_*` coefficient tables. | `implemented surface`; separate arithmetic, evaluator, sidecar, boot/configuration, and host-transport APIs exist. A narrow Wukong RPLU2PADE/J11 result is recorded in [`hardware_evidence.md`](hardware_evidence.md) §3.2f; it does not establish every RPLU mode, full-speed operation, or shared-fabric integration. Tang and Artix resource boundaries are target-specific. The supported builds require FPGA/vendor-flow dependencies; no portable C++ RPLU/Padé library was identified. |
| **GPU** | Accepted Level 1: the T1d contract and complete-frame fixture in the SIM-0 review/vector manifest. Python sources: `software/spu_gpu_eval/`, [`gpu_raster_oracle.py`](../software/lib/gpu_raster_oracle.py), and [`gpu_depth_v2_oracle.py`](../software/lib/gpu_depth_v2_oracle.py). Later packet and feature families are under `fixtures/gpu_t1*`, `software/tests/test_gpu_t1*`, and `hardware/rtl/gpu/`. | T1d is a separately specified, single-fixture capability with a Python finite-width model and a full-frame exact-rational cross-check. It has no accepted C++ implementation yet. Later T1f–T1r work consists of separately versioned experiments, tests, device protocols, and hardware observations; it is not one general GPU API and is not part of T1d SIM-0. Python tooling depends on Python; hardware targets depend on board flows. |
| **SOM and classification** | Exact software authority: [`software/lib/rational_som.py`](../software/lib/rational_som.py). Hardware/model surfaces include `hardware/rtl/core/spu13/spu_som_bmu.v`, `spu_som_weight_bram.v`, [`spu4_som_edge.v`](../hardware/rtl/core/spu4/spu4_som_edge.v), and [`SOM1_RESULT_FRAME.md`](SOM1_RESULT_FRAME.md). Sensor path documents: [`SOM_SENSOR_REPLAY.md`](SOM_SENSOR_REPLAY.md), [`INA226_COARSE_MONITOR_CONTRACT.md`](INA226_COARSE_MONITOR_CONTRACT.md), and [`INA226_CAPTURE_RUNBOOK.md`](INA226_CAPTURE_RUNBOOK.md). | `implemented surface` with exact Python BMU, training/map tools, a C++ header oracle, RTL and specific recorded silicon results (see `hardware_evidence.md` §§3.2g and 3.2g.3). Synthetic replay is not physical validation. The newer INA226 contract defines a held-out physical study; its pending gates must not be represented as a completed end-to-end result. SOM labels/classification do not by themselves establish predictive sensorimotor learning. |
| **Soul / persistent adaptive state** | Current software experiment: [`software/research/soul0/`](../software/research/soul0/), [`contract_soul0_2026-10-14.md`](../spu_strategy/contract_soul0_2026-10-14.md), and `software/tests/test_soul0*.py`. Legacy RTL names include `archive/recovered/spu_soul_metabolism.v` and `archive/recovered/spu_proprioception.v`. | Soul-0 is a bounded Python synthetic regime-memory experiment with serialization/replay tests. It is not a C++ runtime component and is not connected to INA226, SOM, RPLU, or actuator output. The archived Soul metabolism RTL is historical. `hardware/rtl/core/shared/spu_proprioception.v` consumes internal Davis/RPLU health signals and has no matching `hardware/tests` testbench; it is not an external sensor interface or a persistent Soul. No source found that implements the full action-plus-prior-state to predicted-sensation loop described in the research direction. |
| **Sensor acquisition and representation boundaries** | Physical current capture: `tools/bench_metrics/ina226_logger_v2.py`, [`software/lib/ina226_capture.py`](../software/lib/ina226_capture.py), `tools/ina226_capture_pipeline.py`, and the dated `docs/bench_captures/2026-09-03-ina226-som/` dataset. Conceptual conversion contract: [`CARTESIAN_BRIDGE_SPEC.md`](CARTESIAN_BRIDGE_SPEC.md). Encoder pulses are captured as a covariate in the INA226 contract. The bench BOM lists an accelerometer as a future candidate. | An INA226 current-sampling and replay path exists; checked-in captures and a synthetic feature-to-SOM replay are distinct evidence. No accelerometer, microphone, or general RP2350 sensor-acquisition adapter feeding Soul was found. `CARTESIAN_BRIDGE_SPEC.md` is a proposal, not an implemented shared API; its float-to-fixed quantization text and signed-width assumptions must not override the later integer-microamp/SOM boundary. Preserve explicit units, sample timestamps, scale, rounding, saturation, and domain conversions at each sensor boundary. |
| **Audio output and PCM5102** | Generic host model: [`software/lib/audio_sink.py`](../software/lib/audio_sink.py) and [`software/tests/test_rplu2_audio.py`](../software/tests/test_rplu2_audio.py). RTL: [`spu_i2s_out.v`](../hardware/rtl/peripherals/io/spu_i2s_out.v), instantiated by `hardware/rtl/top/spu_system.v`; unit testbench `hardware/tests/common/tb_spu_i2s.v`. | `implemented surface` for a generic 24-bit stereo sample model and an RTL I²S transmitter. The Python sink's `gain` and phase increment use floating point, and it has no WAV writer or frozen PCM hash. Its `AudioToken` interface is not directly connected to the Padé evaluator in these sources. The test is software-only; the I²S RTL testbench is not proof of PCM5102 board output. The evidence ledger records sound-card/PDM audio as simulated and no PCM5102 physical result. PCM5102 is an output DAC; it cannot provide microphone/vibration ADC input. Treat it as an efferent line-level path into powered audio equipment, not as a speaker amplifier. |
| **RP2350 / SPI / UART / storage / ROCK64** | RP2350 firmware and projects: `hardware/rp2350/`, `hardware/rp_common/`, `docs/SOUTHBRIDGE_SPI_PROTOCOL.md`, and board evidence. | RP2350 is used as a host/transport and sensor-logger target in bounded projects; board-specific build files exist under `hardware/rp2350/`. No ROCK64-specific source, build target, or recorded qualification was found. Repository presence of RP2350 support does not qualify arbitrary ADC, I²S, or sensor wiring. |
| **Verification and build packaging** | Repository gate: [`tools/verify_repo.sh`](../tools/verify_repo.sh); Python tests and fixtures under `software/tests/`; hardware evidence ledger [`hardware_evidence.md`](hardware_evidence.md). | The engineering repository has many targeted tests and explicit silicon provenance, but no root CMake SDK build or single package describing optional components and public APIs. Existing standalone build targets include the legacy C++ VM Makefile and RP2040/RP2350 CMake projects. The full repository gate is not an end-user SDK build. Fixture sources, generators, and expected outputs are not uniformly packaged or pinned outside SIM-0. |

## Sensorimotor path found in the checkout

The existing work maps to separate pieces of the proposed sensing and response
loop:

| Stage | Existing source evidence | Current boundary |
|---|---|---|
| Physical measurement | INA226 logger, encoder pulse capture, and retained current CSV sessions | Measures current and pulses on a specific bench. Accelerometer, microphone, and general sensor buses are not integrated here. |
| Sampling and encoding | `current_uA` at a documented 100 Hz; 32-sample windows in sensor replay | Timestamp/cadence/units and feature conversion are defined per experiment, not by a common sensor API. |
| Feature extraction | `tools/som_sensor_replay.py` and the coarse-monitor pipeline | Temporal current features feed the rational SOM. The replay fixture is synthetic; hardware acquisition evidence is separate. |
| Adaptive memory | Soul-0 deterministic regime prototypes and checkpoint/replay | Synthetic software experiment; not connected to captured physical observations or actuator commands. |
| Prediction error | Archived/legacy `spu_active_inference` references and named internal health signals | No current, qualified integrated predictor was found. No biological or consciousness claim follows from these names. |
| Physical response | I²S transmitter and audio sample model | Digital output surfaces exist, but no Padé-to-PCM contract, WAV conformance artifact, or PCM5102 board observation was found. Motor control remains a separate interface and safety boundary. |

Thus the repository already has acquisition, feature, classifier, persistent
state, and output experiments, but not one joined sensorimotor product path.
The gaps are interface/evidence gaps between existing components, not a reason
to infer a new universal data type. Keep physical samples, exact algebraic
values, M31 residues, quantized pixels, and PCM samples as distinct typed
domains with explicit conversions.

## Duplicate, stale, and non-authoritative alternatives

| Source set | Audit disposition |
|---|---|
| `knowledge/LITHIC_L_DEEP_DIVE.md` versus `knowledge/LITHIC_L_LANGUAGE_SPEC.md` | Preserve both for provenance. The deep dive describes a 16-bit Chord and speculative mechanisms; it is not compatible authority for the 64-bit ISA-A assembler or accepted `spu13-soft-v1`. The language spec itself contains planned features and historical implementation claims. |
| `docs/spu13_isa_spec.md` versus `knowledge/isa_reference.md` | Treat the former's Wheeler–Feynman/ISA-B layout as a separate experimental profile. Use the accepted SIM-0 pin for `spu13-soft-v1`; do not combine opcode tables. |
| Python VM, C++ VM, RTL | Retain as distinct candidates and evidence sources. Their existence does not imply parity. The C++ VM is the closest existing standalone build, but the accepted profile is narrower and has different atomic fault/width requirements. |
| `tools/rplu_morse_update.py`, Morse LUTs, and RPLU2/Padé | Retain legacy Morse potential generators and RPLU2/Padé as separate generations. The Morse table update path uses Decimal/exponential generation and quantization; the newer A₃₁ Padé evaluator is not thereby a Morse-projection audio algorithm. |
| T1d, later T1 GPU profiles, Vulkan compute | Keep each versioned and independently evidenced. A T1d result is not a general GPU/API guarantee. |
| SOM, Soul-0, archived Soul/proprioception RTL | Do not merge their names or semantics. SOM performs bounded classification; Soul-0 explores persistent synthetic regimes; internal RTL proprioception aggregates machine health signals. |
| Historical status and provenance docs | Keep dated audits as history. Some ISA documents still say repairs are pending even though later annotations report focused repairs; use the accepted SIM-0 review for the bounded profile and inspect the evidence ledger for hardware claims. |

## Consolidation status

The existing checkout supports a modular direction only in the limited sense
that several components already have local source boundaries and tests. It
does not yet have a stable package/API layer that makes CPU-only builds and
optional GPU, Soul, or audio builds independently selectable. Do not extract
repositories from this inventory alone. First preserve the source provenance,
profile versions, and dependency/build facts above; then review each candidate
boundary as its own implementation decision.

No files were moved, deleted, built, or executed as part of this audit.
