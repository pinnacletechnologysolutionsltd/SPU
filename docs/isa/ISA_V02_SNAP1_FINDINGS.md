# ISA-V02-SNAP-1 — `SNAP` (0x07) and the status/FLAGS mechanisms

**Status:** source characterization PASS (read-only); normative `SNAP`/FLAGS semantics **HOLD**. No VM, assembler, opcode, RTL, test or hardware change.
**Starting identity:** `dev/next` at `6deab30edbfaf080dfde4b6919dc5100a14208cc` (clean). Executable sources are identical to public RC2 `b063280` (`b0632806621ed6fe44c9c72f4e0adbd8ee8df776`); earlier `dev/next` commits `2cbfa6f`, `19d652a`, `f61fee0` changed only documentation, O6 tools/tests and the QROT-1 tool. Conclusions apply to the tree at the identity above; the commit containing this file is found with `git log -1 -- docs/isa/ISA_V02_SNAP1_FINDINGS.md`.
**Method:** source reading with `grep`/`sed` only; nothing was executed or synthesized. Line numbers are at `6deab30`.

## 1. `SNAP` (0x07) per implementation

| | Python VM (`software/spu_vm.py`) | C++ VM (`software/vm/spu_vm.cpp`) | SPU-13 RTL (`hardware/rtl/core/spu13/spu13_core.v`) |
|---|---|---|---|
| Decode | `OPCODES["SNAP"]` branch, `:1469` | `case 0x07`, `:694` | No `0x07` decode found (consistent with `docs/isa/ISA_CONFORMANCE_2026-10-10.md`, core row) |
| Scalar condition | each of `R0–R25` with `a≠0 or b≠0` and not `is_laminar()`; `is_laminar` = `a²−3b² > 0` (`RationalSurd.quadrance` `:245`, `is_laminar` `:260`) | each of `R0–R25` with non-zero and not `is_laminar()` (`quadrance() > 0`, `:80`) | none |
| Counter | `snap_failures += 1` once if any register fails (`:1480`) | `snap_failures++` once if any register fails (`:701`) | none |
| Reporting | failure line printed unconditionally (`:1481`); "✓ Manifold stable" only if verbose (`:1495`) | failure line printed unconditionally; ✓ only if verbose | none |
| SDF layer | `self.sdf.evaluate(self.qregs, ...)` runs on every `SNAP`, regardless of the scalar result (`:1504`); it updates SDF internal state (`nearest_axis`, `min_q`, `snap_conflict`, `:1096-1198`) | none | none |
| SDF failure precedence | if `snap_conflict` and the scalar scan found **no** failures, `snap_failures += 1` and "SDF CONFLICT" is printed (`:1505-1510`). If the scalar scan already failed, the SDF result adds nothing. So at most one increment per `SNAP`. | not applicable | not applicable |
| Registers written | none | none | none |
| Process exit | `sys.exit(2)` if `snap_failures != 0` at end (`:2612-2614`) | `return 2` if `snap_failures != 0` (precedes the step-budget return 3) (`:1186-1191`) | not applicable |
| Failure effect on execution | nonhalting | nonhalting | not applicable |

`docs/isa/ISA_SOFTWARE_SEMANTICS_2026-10-10.md:21` already records the common part ("nonhalting, preserves registers, counts one failing check and retires") and that Python SDF checks and periodic recovery are unsupported in C++.

**`snap_failures` is not `SNAP`-only.** `EQUIL` also increments it on a manifold-tension failure (Python `:2098`, C++ `:966`). The counter is therefore a shared diagnostic counter whose exit-code effect (rc 2) is reached by either instruction.

**Side effects, stated plainly.** `SNAP` does not mutate scalar or Quadray registers. It does mutate diagnostic state: the `snap_failures` counter (both VMs), stdout, and, in the Python VM, SDF internal state. The Python VM additionally runs a periodic φ-gate "henosis" recovery between steps that can rewrite registers (observed in QROT-1); that is not part of `SNAP` but changes states observed after it.

## 2. RTL autonomous stability network (not `SNAP`)

`spu13_core.v` keeps `stability_bits[12:0]` (`:192`), set per axis from `axis_stable = (quadrance > 0) && !rplu_dissoc` (`:1795`, `:1953`), and drives the output `is_janus_point = &stability_bits` (`:97`, `:1962`). It advances on the TDM axis pointer with no instruction trigger. It shares the "quadrance > 0" idea with the VM scan but differs in domain (13 axes of the manifold, not `R0–R25`), trigger (autonomous, not instruction), and result (a sticky-per-sweep output, not a counter or text). It is **not** an implementation of `SNAP`.

## 3. Status mechanisms identified

| # | Mechanism | Owner | Semantics | Observability |
|---|---|---|---|---|
| 1 | Spec FLAGS (6 bits: Z, C, V, MISALIGNED, OVERFLOW, INEXACT) | `knowledge/isa_reference.md:99,249-262` | "Status word read via `SNAP`"; bits sticky within an instruction, cleared at the next | **No implementation**: neither VM has a FLAGS word (`SNAP` produces none); no SPU-13 RTL `SNAP`/FLAGS register found |
| 2 | VM diagnostics | both VMs | `snap_failures` counter (shared by `SNAP`/`EQUIL`); halting `fault_kind` (`UNSUPPORTED`, `INVALID_REGISTER`, `OVERFLOW`, `DEGENERATE_METRIC`) | host-side only (stdout, exit code 2, `fault_kind`) |
| 3 | Surd bank `SSTAT` | `isa_reference.md:57,65`; `spu13_surd_exec.v` | codes `OK=0, INVALID=1, OVERFLOW=2, ENGINE_FAULT=3, BAD_ENCODING=4`; last status held, read by `SSTAT` | architectural within the Surd extension (`ENABLE_SURD_CPU`) |
| 4 | `rotc_debug_status` | `spu13_core.v:1250-1255`; flag bits at `:1030`, `1280`, `1326`, `1415-1507` | debug word `{flags[7], busy, flags[5:0], state, angle}`: bit 0 latched, bit 7 BAD_ANGLE fault, bits `[5:4]` fault code (ROTC/IROTC), bits 1–3 progress markers | implementation debug: exposed over SPI status on the Artix-7 top (`spu_a7_top.v:1072-1082`) |
| 5 | Pins and unit outputs | A31 inverter `spu13_fp4_inverter.v:32` (`flags_v`); tagged rotor `spu13_rotor_core_tagged.v:63` (`fault[2:0]` = `{INEXACT, OVERFLOW, MISALIGNED}`) | `flags_v` on zero norm; tagged rotor fault bits | see §4 and §5 |

Related naming collision on the Artix-7 top: the SPI status fields named `spi_status_snaps` and `spi_status_janus` are driven from `core_rotc_debug_status[0]` and `[1]` (`spu_a7_top.v:1078-1082`) when no sidecar status is selected. The label "snaps" there does not refer to the `SNAP` instruction.

## 4. FLAGS bit-position collision

The spec assigns FLAGS bits 3, 4 and 5 to MISALIGNED, OVERFLOW and INEXACT (`isa_reference.md:257-262`). In `spu13_core.v` the six-bit field `rotc_debug_flags[5:0]` that the debug word exposes uses the same positions differently: `[3]`, `[4]` and `[5]` are set together as "rotation done" markers when the TDM rotor completes (`:1445-1447`, also `:1326`), bits 1–2 mark the rotation as started (`:1430-1431`), and bits `[5:4]` carry the fault code in the guarded paths (`:1453-1507`). Same positions, different meanings. A single host or test that interprets `rotc_debug_status` by the spec FLAGS table would misread it.

## 5. Tagged rotor and A31 `flags_v`

- **Tagged rotor faults are not part of the SPU-13 core.** `spu13_rotor_core_tagged.v` (the only source of MISALIGNED/OVERFLOW/INEXACT) is instantiated in `hardware/boards/tang_primer_25k/spu13_tang25k_rotc_tagged_probe.v:48` and in `hardware/tests/spu13/spu13_rotor_core_tagged_tb.v`; `spu13_core.v` does not instantiate it.
- **A31 `flags_v` architectural visibility is UNRESOLVED.** `spu13_core.v` contains the token `flags_v` only inside a comment (`:2229`). In `rplu_pipeline.v` the signal exists as wires (`inv_flags_v` `:110`, `pade_flags_v` `:111`), is driven by the inverter instances (`:427`, `:445`) and passed to a submodule port (`:240`). The consumer path beyond those lines was **not traced**, so no downstream behavior is inferred. No ISA-A opcode is tied to it (O6).

## 6. Recommended v0.2 treatment (ratification HOLD)

- `SNAP` `0x07`: a VM-specific diagnostic instruction. Document the C++ scalar scan as the common behavior; document Python's scalar scan plus SDF evaluation as an extended diagnostic profile. `snap_failures` is an explicit diagnostic-state side effect; do not describe `SNAP` as free of observable side effects.
- Treat the historical six-bit FLAGS table as an **unresolved architectural proposal**, not an implemented v0.2 register.
- Keep `SSTAT` as an independent, implemented status interface of the Surd extension; keep `rotc_debug_status` as an implementation-specific debug interface; keep `flags_v` and the tagged rotor outputs internal/experimental until a consumer path and conformance exist.
- Separate three classes in future documentation: **architectural state** (registers, PC and other state a named profile defines), **architectural status** (faults/results observable through specified mechanisms) and **implementation diagnostics** (debug registers, counters, SPI reporting, pins).
- Do not reuse the spec FLAGS bit positions for any new architectural status word without resolving §4.

## 7. Remaining blockers

1. Whether the Python SDF evaluation belongs to any normative profile (it has no C++ counterpart).
2. Whether `snap_failures` is architectural or purely diagnostic, and whether `EQUIL` sharing it is intended.
3. Exit-code (rc 2) and stdout reporting are host-harness behavior, not ISA behavior; their conformance role is undecided.
4. FLAGS: existence, bit assignment, read mechanism, clearing rule; includes the collision in §4.
5. A31 `flags_v` consumer path (trace needed) and refusal post-state (separate HOLD).
6. Isolation of the Python periodic recovery in conformance fixtures (QROT-1 observation).
7. No silicon claim: `docs/hardware_evidence.md` was not consulted for `SNAP`/FLAGS entries in this pass.

## Limitations

Source reading only; nothing was run. RTL conclusions cover `spu13_core.v`, `spu_a7_top.v`, `rplu_pipeline.v` (partially), `spu13_rotor_core_tagged.v` and its probe, and the A31 inverter's port declaration. SPU-4 has its own status mechanisms and is out of scope here.
