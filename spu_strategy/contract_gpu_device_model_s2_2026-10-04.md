# Engineering Contract: T1d Functional GPU Device Model S2

- **Date:** 2026-10-04
- **Contract ID:** `contract_gpu_device_model_s2_2026-10-04.md`
- **Status:** CLOSED — S2 software model and required repository gates complete; full-top pixel parity remains unverified.
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Codex, after §0 review
- **Integration Auditor:** `software/tests/test_gpu_device_model_s2.py` and repository gates

## 0. Pre-execution review

Run from the repository root:

```bash
git rev-parse HEAD
git status --short
python3 --version
python3 -c 'import json,hashlib,pathlib; root=pathlib.Path("."); inv=json.load(open("build/gpu_evaluation/q0_profile_audit_20261004/profile_inventory_01.json")); paths=[p for p in inv["offline_report_source_hashes"] if p.startswith("hardware/rtl/gpu/") or p in ("hardware/rtl/arch/gpu_reciprocal_lut_q15.mem","hardware/rtl/hal/hal_vga.v")]; bad=[(p,inv["offline_report_source_hashes"][p],hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths if hashlib.sha256((root/p).read_bytes()).hexdigest()!=inv["offline_report_source_hashes"][p]]; print("checked",len(paths),"profile files; mismatches",bad); raise SystemExit(bool(bad))'
sha256sum fixtures/gpu_t1d_scene_wire_64b.bin fixtures/gpu_t1d_scene_reference.json hardware/rtl/arch/gpu_reciprocal_lut_q15.mem
sed -n '1,260p' spu_strategy/GPU_EVALUATION_PROFILE_AUDIT_2026-10-03.md
sed -n '1,260p' spu_strategy/contract_gpu_scene_compiler_preview_s1_2026-10-04.md
```

Halt if any listed profile source differs from the Q0 inventory, the frozen
packet identity differs, or the selected T1d top-level configuration enables
four primitives, UV/scalar attributes, runtime materials, or packet validation.
The audited working tree is dirty; bind the current bytes by SHA-256 and do not
restore, stage, or overwrite unrelated changes.

**Verification scope revision 2:** the changed-scene full-top Icarus probe and
the existing T1e baseline top oracle both reached their frozen 55-second
subprocess limits without a result. Do not extend or relaunch either frame
scan. Compare baseline diagnostics and a changed packet against the T1d depth,
edge-stepper, attribute-stepper, and compare RTL modules at selected pixel
coordinates. Do not claim full-top S2 parity.

## 1. Objective and files

Add a deterministic software model for the selected T1d two-triangle prepared
scene. Decode its wire packet, reproduce its finite-width edge/depth arithmetic,
model raw-bank loading and prepared-scene frame activation, render a settled
640×480 RGB444 frame, and compare the result with S1's independent ideal
reference and the scoped RTL observations.

Target files:

```text
software/spu_gpu_eval/device_packet.py
software/spu_gpu_eval/device_arithmetic.py
software/spu_gpu_eval/device_model.py
software/spu_gpu_eval/device_loader.py
software/spu_gpu_eval/device_preview.py
software/spu_gpu_eval/cli.py
software/tests/test_gpu_device_model_s2.py
software/tests/test_gpu_t1e_prepared_scene_oracle.py
docs/gpu_scene_preview.md
```

Do not modify RTL, board files, generated files, fixtures, historical evidence,
`docs/index.md`, S1 output, or any UART/JTAG/programming/power tool. Use Python
3.10+ standard library only. Use integer operations only in the device model;
do not call the floating-point LUT generator or `software/lib/gpu_depth_v2_oracle.py`.
The existing T1e oracle may only be edited to add a missing current top-level
RTL source to its simulation source list.

## 2. Frozen device contract

Decode exactly 64 bytes: `A5` plus a 63-byte little-endian payload containing
two 252-bit records. Decode the signed/unsigned widths from
`hardware/rtl/gpu/spu_scene_unpack.v`; preserve the wire depth order
`z0=z(V2), z1=z(V0), z2=z(V1)`. Reject a wrong length or start byte. The raw
cycle loader accepts `A5` only while idle; subsequent bytes, including `A5`, are
payload. It accepts exactly 63 valid payload-byte cycles, ignores bytes while
commit is pending, and changes the active raw bank only on a later activation
cycle. Incomplete packets remain receiving without timeout.

For each decoded record, implement the T1d RTL widths and slices:

1. `D` is the signed 34-bit sum `c0+c1+c2`; take its unsigned magnitude.
2. Each dot-product term uses the low 37 bits of the unsigned magnitude product.
   Apply coefficient signs, then wrap `Sa`, `Sb`, and `Sc` after every add/subtract
   to signed 40 bits.
3. Normalize nonzero `abs(D)` to a 16-bit mantissa using its highest set bit;
   preserve discarded low bits by right-shift truncation. Set `exp=(31+shift) mod
   128`. Index the checked-in Q15 ROM with `mantissa[14:7]`.
4. Reciprocal NR0 stores product bits `[32:0]`; compute the 33-bit modular
   `2**32-prod`. NR1 stores bits `[48:0]`; output reciprocal bits `[46:31]` and
   the 7-bit exponent. For `D=0`, use reciprocal and exponent zero.
5. Scale each signed sum by the 16-bit reciprocal using the shared product;
   negate iff the sum sign differs from `D`'s sign. Keep the low 56 bits as
   signed `A_z`, `B_z`, and `C_z`. Retain `frac_bits=exp`.
6. Edge values use signed 32-bit wrap and coverage is `edge>=0`. Per-pixel depth
   accumulation wraps signed 56 bits; arithmetic-right-shift by `frac_bits`,
   then compare signed depths. Smaller depth wins; ties select primitive 0.
   Uncovered pixels are black. T1d material behavior is flat per-primitive RGB444.

The loader's byte-cycle state and prepared-control ready-generation/frame-start
gate are modeled. Do not claim cycle-accurate dispatcher latency, UART timing,
VGA sync, clock behavior, or a hardware emulator. `device-preview` starts from a
complete valid S1 scene/packet and models it as loaded, prepared, and activated;
the event API separately exposes incomplete load, commit-pending, ready, and
frame-start behavior. Render at integer active-pixel coordinates, anchored at
`(0,0)`, with no half-pixel offset or display pipeline delay.

Report the ideal exact-reference result and finite-width device-model result as
separate outputs. S2 models flat RGB444 only. Defer UV, programmable materials,
shaders, four-primitive mode, physical color truncation and board timing.

## 3. Command and artifacts

Add this command:

```bash
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/s2_t1d_device_model_20261004/run_01
```

Write exactly these files to a new child of `build/gpu_evaluation/`:

```text
scene_packet.bin
ideal_preview.ppm
device_preview.ppm
pixel_comparison.json
manifest.json
```

Refuse an existing target; validate and finish all artifact generation in a
temporary sibling directory, then atomically rename. Remove the temporary
directory on failure. JSON is sorted, compact, and newline-terminated. Do not
include timestamps or absolute paths. The manifest records input, packet,
artifact, Python module, selected RTL/ROM SHA-256 values, repository HEAD and
dirty/clean state, `device_model=true`, `physical_observation=false`, and
`cycle_timing_model=false`. Pixel comparison contains the frozen six baseline
diagnostic coordinates plus `(320,0)`, each with baseline expectation, actual
ideal result, and actual device-model result, and full-frame exact-match and
different-pixel counts.

## 4. Implementation order

1. Run §0 and verify all selected profile hashes against Q0.
2. Implement packet decoding independently of the S1 encoder.
3. Implement reciprocal and depth preparation directly from the RTL widths,
   slices, and checked-in ROM.
4. Implement the settled-frame per-pixel model and the raw loader/prepared
   control event model.
5. Add `device-preview`; retain the S1 ideal preview and packet encoder.
6. Add falsifiable tests for packet mapping, signed widths, every reciprocal
   truncation point, prepared depth coefficients against Icarus RTL, edge/depth
   wrap, near/tie/color decisions, loader byte-cycle transitions, prepared
   generation and frame-start gating, and deterministic output hashes.
7. Compare the baseline diagnostic coordinates and edited-V2 scene against
   directly instantiated T1d depth, edge-stepper, attribute-stepper, and compare
   RTL modules. The T1e full-top baseline oracle was attempted and timed out;
   do not launch another full-top frame scan.
8. Update `docs/gpu_scene_preview.md` with the exact command and scope boundary.

## 5. Acceptance commands

Run from the repository root:

```bash
python3 software/tests/test_gpu_device_model_s2.py
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/s2_t1d_device_model_20261004/run_01
git diff --check -- software/spu_gpu_eval software/tests/test_gpu_device_model_s2.py docs/gpu_scene_preview.md spu_strategy/contract_gpu_device_model_s2_2026-10-04.md
```

`python3 software/tests/test_gpu_t1e_prepared_scene_oracle.py` was attempted
with its frozen 55-second subprocess limit and timed out. Do not rerun it in S2.

The S2 test must compare the baseline packet's prepared coefficients and
selected-pixel RGB444 values with actual RTL observations. It must check at
least one changed-vertex packet through directly instantiated datapath RTL; the
unchanged T1e test remains the full-top baseline observation. It must falsifiably test
embedded `A5`, short and exact-length loads, bytes ignored while pending,
activation edge behavior, ready-generation matching, frame-start gating, signed
arithmetic shifts, modulo widths, and tie-to-primitive-0. Check deterministic
manifest and image hashes by running artifact generation twice to separate new
temporary output directories and comparing file bytes.

Then run the mandatory repository gates in the order specified by the root
`AGENTS.md`: repository verifier; ROTC and IROTC traces; rational robotics and
SOM; Lucas MAC; Padé batch inversion; detached Artix-7 Padé synthesis. S2 changes
no RTL, so record `TB_FILTER` as not applicable. Use a unique detached output
directory below `build/gpu_evaluation/s2_t1d_device_model_20261004/`; after the
runner reports `LAUNCHED`, record its unit and evidence path and end the agent
turn. Do not wait in the same turn.

## 6. Stop conditions

- Stop if Q0 source hashes differ or T1d profile settings are ambiguous.
- Stop and flag any RTL width, signedness, truncation, packet mapping, or
  activation behavior that cannot be resolved from the frozen sources.
- Stop if the software result disagrees with the named RTL probes; do not alter
  frozen fixtures or RTL to force parity.
- Stop if output generation can leave partial artifacts, output bytes vary
  across identical runs, or the model uses floating point.
- Stop before any hardware access, programming, wiring, power, UART, or JTAG.
- Do not claim cycle accuracy, shader execution, complete SPU emulation, or
  physical GPU/display acceptance.

## 7. Execution record

| Gate | Result | Evidence |
|---|---|---|
| Q0 profile preflight | PASS; all 16 inventoried RTL/ROM/display source hashes match Q0; HEAD `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`; working tree already dirty | `profile_inventory_01.json` and command in §0 |
| S2 depth arithmetic RTL parity | PASS; 7 vectors, including baseline, changed scene, normalization truncation, zero denominator and signed extrema | `python3 software/tests/test_gpu_device_model_s2.py` |
| S2 loader/control RTL parity | PASS; start/payload/pending/activation and ready/frame-start events | Same S2 test |
| S2 stepper boundary RTL parity | PASS; 32/56-bit wrap, row re-anchor, negative arithmetic shift | Same S2 test |
| S2 selected-pixel RTL parity | PASS; 7 baseline points and 2 changed-scene points against depth, edge, attribute and compare RTL | Same S2 test |
| Changed-scene full-top probe | TIMEOUT at the frozen 55-second subprocess limit; no pixel result | First S2 full-top probe; no retry authorized |
| T1e baseline full-top oracle | TIMEOUT at the frozen 55-second subprocess limit after adding the omitted `spu_depth_compare4.v` source; no pixel result | `python3 software/tests/test_gpu_t1e_prepared_scene_oracle.py`; no retry authorized |
| S2 device preview | PASS; exact five artifacts; 307,200/307,200 baseline pixels match the ideal reference; software-only | [`run_01/`](../build/gpu_evaluation/s2_t1d_device_model_20261004/run_01/) |
| S2 deterministic artifacts | PASS; two independently generated artifact dictionaries byte-identical; output hashes match manifest | Same S2 test |
| S1 scene compiler regression | PASS; 6 tests | `python3 software/tests/test_gpu_scene_compiler_s1.py` |
| Whitespace checks | PASS; `git diff --check` and new-file trailing-whitespace scan | Commands run before repository gate |
| Repository verifier | COMPLETE; exit 0; 238 passed, 0 failed | Unit `spu-repo_gate_01-20261004T105044Z-86031`; [`repo_gate_01/`](../build/gpu_evaluation/s2_t1d_device_model_20261004/repo_gate_01/); exactly one `COMPLETE` marker |
| ROTC VM/RTL trace | PASS; 336 checks | `python3 software/tests/test_rotc_vm_rtl_trace.py` |
| IROTC VM trace | PASS; 9 passed, 0 failed | `python3 software/tests/test_irotc_vm_trace.py` |
| Rational robotics | PASS; 104 checks | `python3 software/tests/test_rational_robotics.py` |
| Rational SOM | PASS; 24 checks | `python3 software/tests/test_rational_som.py` |
| Lucas MAC oracle | PASS; 166,666 identity macros and 999,996 primitive operations | `python3 software/tests/test_lucas_mac_oracle.py` |
| Padé batch inversion | PASS; 25 checks | `python3 software/tests/test_pade_batch_inversion.py` |
| Artix-7 100T Padé synthesis | COMPLETE; exit 0; separate Padé target, not GPU evidence | Unit `spu-a7_pade_01-20261004T190934Z-93808`; [`a7_pade_01/`](../build/gpu_evaluation/s2_t1d_device_model_20261004/a7_pade_01/); exactly one `COMPLETE` marker |

The scoped module datapath probes establish only the tested T1d arithmetic and
selected-pixel behavior. Neither full-top timeout produced a parity result.
No UART, JTAG, programming, wiring, power, or physical GPU operation was
performed in S2. The required Artix-7 synthesis was for the separate Padé
target and is not GPU build or silicon evidence.
