# ISA-V02-O6 — Source Inventory and Consistency Findings

**Date:** 2026-10-26 · **Status:** findings for review; no opcode, RTL, VM or ISA document changed.
**Inventory:** [`isa_v02_o6_inventory.json`](isa_v02_o6_inventory.json) (frozen, source-derived)
**Regenerate:** `python3 tools/isa_inventory.py --out docs/isa/isa_v02_o6_inventory.json`
**Test:** `python3 software/tests/test_isa_inventory.py` (fails if the inventory or the known CONFLICT set changes)

## Scope and limits of the inventory (adversarial review AR1)

- **The inventory is a non-exhaustive, regex-based opcode census.** The RTL extractor scans `spu13_core.v` and five named sidecar files for `[63:56] == 8'hXX` comparisons and `localparam OP_*`. A missing row does not mean the RTL lacks the opcode.
- **Known miss:** `hardware/rtl/core/spu13/spu13_surd_exec.v:59` decodes the Surd extension (`0x70–0x77`) with `case(op)` over relative indices `0..7`; the core routes the extension opcodes to it. The inventory therefore has no RTL rows for the Surd instructions. The draft's statement that the Surd opcodes are present in RTL is supported by the core dispatch and this executor; the inventory omission is an extractor coverage defect, not a contradiction. The extractor and JSON are unchanged (HOLD).
- **Other decoders reviewed, not counted:** `spu_instr_decode.v` (untyped `localparam OP_*` and `case(saved_opcode)`; legacy or profile-uncertain, no current top instantiation found), `spu13_lucas_mac.v` (local 3-bit micro-op `case`; its outer ISA decode is the Lucas sidecar, already included), `spu_isa_decoder.v` (v1.0 / ISA-B namespace, out of scope). No exhaustive proof of every alternative decode form exists; SPU-4 is outside the extractor entirely.
- **The frozen-JSON test is a staleness guard.** `test_isa_inventory.py` regenerates the JSON with the same extractor and classifier and compares. It detects drift from the checked-in file, not common-mode omissions or misclassification. It is not an independent completeness check.
- **Shadowed `POLY_STEP`.** In `software/spu_vm.py:629-631` the dict binds `0x60` then `0xE0`, so the effective table value is `0xE0`. The inventory keeps both records (intended) but counts both as Python VM support, so support at `0x60` is overstated. Effective support should be derived from the last binding; the tool is unchanged (HOLD).
- **Class labels are evidence-limited.** "Missing in a claimed profile" rests on the assembler header comment (`software/tools/spu13_asm.py:56`) or an explicit matrix cell; it is not an owner-ratified profile boundary. "Documented profile extension" is generated only from a spec opcode being absent in some software source with no claim found; it does not establish that the gap is documented as intentional. Read it as "implementation coverage gap, no claim found". No rename or regeneration is performed (HOLD).
- **D1 reachability is source and configuration inference.** No row is backed by elaboration, simulation, synthesis or hardware observation. "Ungated" for `0xE0` means no feature parameter gates the accepted-instruction handler at `spu13_core.v:1899-1907`; it is not active during reset or without an accepted `0xE0`. The `CUSTOM` spin of `spu_a7_top.v` can set `ENABLE_RPLU_V2_EXTENSIONS` (`:119`) and was not evaluated. Scope remains in-tree tops, scripts and testbenches.

Sources read: `knowledge/isa_reference.md`, `software/spu_vm.py`, `software/tools/spu13_asm.py` (+ `surd_cpu_encoding.py`), `software/vm/spu_vm.cpp`, `spu13_core.v` and five opcode-bearing sidecars, `spu_isa_defines.vh`, `ISA_IMPLEMENTATION_MATRIX.md`. Duplicates are preserved (AST/line scan, not dict load). ISA-B/WF is a separate namespace; 27 of its values numerically overlap ISA-A and no conflict is asserted.

## Findings by class (live counts: 3 / 7 / 19 / 0 / 20)

### Confirmed encoding conflict (3 records, 1 underlying issue)
`POLY_STEP`: spec `0x60` (`isa_reference.md:178`); Python VM defines both `0x60` and `0xE0` in one dict literal, so `0xE0` silently wins (`spu_vm.py`); `spu13_core.v:1903` decodes `0xE0`. Spec disagrees with the VM and the core RTL.
**Proposed resolution (owner decision):** declare `0xE0` canonical (VM and RTL agree) and amend the spec row, or move both to `0x60`. Either way remove the duplicate dict key. Not done here.

### Missing in a claimed profile (7)
The assembler header says its table "must stay in sync with spu_vm.py". The assembler lacks `SOM 0x2A`, `SOM_TRAIN 0x2B`, `PHADD 0x30`, `PHCFG 0x31`, `RATIO_CMP 0x61` and both `POLY_STEP` values. The matrix already records the SOM assembler gap. **Resolution:** either add them or weaken the header claim to a stated subset.
No matrix row (105 mnemonic×column cells checked) contradicts the sources.

### Documented profile extension (19; not defects)
In the spec, not in some software implementation, no contract claiming otherwise: C++ VM lacks `REGEN`, `MIN4`, `SOM`, `SOM_TRAIN`, `PHADD`, `PHCFG`, `POLY_STEP`, `RATIO_CMP`, `IROTC`, `LOAD2X`, `SCALE2`; neither Python VM nor C++ VM has the Surd extension `0x70–0x77` (the assembler does). Correction to my earlier note: the assembler *does* include 0x70–0x77 via `**SURD_OPCODES`.

### Undocumented implementation (0 strictly)
Every VM/assembler/C++ opcode is in the spec. The RTL-only cases below are classified as unresolved ownership.

### Unresolved profile ownership (20)
- `spu13_core.v`: `0x48`, `0x4C`, `0x4D` (JSCR/NSA decode); `SPU13_ARCHITECTURE.md:208` calls them "feature-specific", no encoding or semantics are documented.
- Sidecars with no spec entry: Lucas `0xD0–0xD5`, Neuro `0xE1–0xE3`, SU3 `0xE8–0xEB`.
- **Candidate overlaps** (same value, different name, optional modules): `0x2A` = `SOM` (spec/VM/core) vs `RPLU2_START` (two RPLU2 sidecars); `0xE0` = `POLY_STEP` (VM/core) vs `NEURO_CFG` (Neuro sidecar). Whether these modules can coexist in one build is not established here.
- ISA-B/WF namespace note.

## Architectural state (see `state` in the JSON)
- Scalar `R0–R25` (both VMs), `QR0–QR12` (spec), Surd `S0–S7` (spec, `ENABLE_SURD_CPU`).
- **Spec FLAGS (6 bits) read via `SNAP` — UNRESOLVED in both VMs:** their `SNAP` is a Davis-gate scan with no FLAGS word.
- Faults: VMs `UNSUPPORTED`, `INVALID_REGISTER`, `DEGENERATE_METRIC`, `OVERFLOW`; Python exceptions for ROTC/IROTC; spec `SSTAT` codes `OK=0..BAD_ENCODING=4`.
- Per-opcode fault precedence and refusal post-state, RTL register organisation, and the fetch/PC/stack transition table: **UNRESOLVED**.

## Recorded qualification blockers (no work done on them)
1. **QROT operand class.** Spec (`isa_reference.md:112`): `QROT Rd, Rs, n`, `R[d]=R[s]×(2+√3)ⁿ` (scalar form). Both VMs (`spu_vm.py:1622`, `spu_vm.cpp:822`) and the assembler treat it as `QROT QRn`, one in-place rotor step on a Quadray register with no exponent; the Python VM also marks the register `PHI_UNTAGGED`. Spec and implementation describe different operations.
2. **A31 inverse has no opcode.** `FLAGS.V` is documented, but no ISA-A table encodes an A31 inverse. The inverter (`spu13_fp4_inverter.v`) raises `flags_v` and `done` on zero norm and does not write `inv0..3`, so the outputs hold stale values; consumer behavior differs by path (traced in `ISA_V02_SNAP1_FINDINGS.md` §5: the ordinary RPLU pipeline latches the result without checking the flag; the RPLU2 Padé sidecar uses it to gate `qr_commit_valid`); actual stale-result publication is unverified.
3. **A31 zero-divisor coverage (HOLD).** The inverter tests one norm, `w0²−3·w1²`. A31 ≅ F_p² × F_p², so whether one check catches every non-invertible element needs a mathematical audit. Not opened, per O6 scope.

## D1 active-decode and reachability evidence (2026-10-26, read-only audit)

Baseline: `2cbfa6f` on `dev/next` in `/home/john/spu-public-v0.2-rc2` (created from public RC2 snapshot `b063280`; distinct from any private integration history). The frozen inventory JSON is unchanged; D1 findings are recorded here only.

**Decode structure.** `spu13_core.v` decodes its own opcodes under `ENABLE_*` parameters. The Lucas, SU3 and RPLU2 sidecars are separate modules instantiated in `hardware/boards/artix7/spu_a7_top.v`; a sidecar's `inst_claimed` masks the instruction from the core (`spu_a7_top.v:427`). The Neuro adapter is instantiated only in `hardware/boards/tang_primer_25k/spu13_tang25k_neuro_sidecar_probe.v` (no `spu13_core` there) and its testbench.

| Opcode | Decoder (file:line) | Enable condition | Competing decoder | Reachable? |
|---|---|---|---|---|
| `0x2A` RPLU2 start | `spu13_core.v:1586` | `ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_PIPELINE` | SOM at `:1593` | Yes: Artix-7 `INTELLIGENCE`, `FULL`, `RPLU2`, `MULTIMEDIA`; Colorlight RPLU2 top |
| `0x2A` SOM | `spu13_core.v:1593`, launch `:2193` | `ENABLE_CORE_SOM` and not RPLU2 pipeline | RPLU2 at `:1586` | Yes: SOM-only tops (e.g. Tang SOM top) |
| `0x2A` sidecar | `spu13_rplu2_sidecar.v:47,56`; `spu13_rplu2_pade_sidecar.v:54,61` | `SPIN="RPLU2LIVE"`, `"RPLU2PADE"` (coreless) | none (no core) | Yes |
| `0x2B` SOM_TRAIN | `spu13_core.v:1676,2201` | `ENABLE_CORE_SOM` | none | Yes, including `INTELLIGENCE`/`FULL` where `0x2A` is RPLU2 |
| `0xE0` POLY_STEP | `spu13_core.v:1903` (inside the `inst_accept` block, no `ENABLE_*` condition) | always | none in core | Yes, every core build |
| `0xE0` NEURO_CFG | `spu13_neuro_sidecar_adapter.v:78,84` | probe top only | POLY_STEP only if co-instantiated | Not with any in-tree core |
| `0x48` JSCR | `spu13_core.v:725,1606,2400` | effect needs `ENABLE_CORE_RPLU_V2 && ..._EXTENSIONS` (`gen_nsa_core`, `:2378`); acknowledged otherwise | none | Effect only in `spu13_core_jscr_tb.v` |
| `0x4C`,`0x4D` NSA | `spu13_core.v:726,1672,2469` | same | none | Effect only in `spu13_core_nsa_handshake_tb.v` |
| `0xD0–0xD5` Lucas | `spu13_lucas_sidecar.v:53-58,68` | `SPIN="LUCAS"` | none | Yes (sidecar) |
| `0xE8–0xEB` SU3 | `spu13_su3_sidecar.v:57-60,67` | `SPIN="SU3"`, `"SU3SHARE"` | none | Yes (sidecar) |

All synthesis targets found set `ENABLE_CORE_RPLU_V2_EXTENSIONS` to 0 (`spu_a7_top.v:119` forces 0 outside `CUSTOM`; Tang scripts set 0). The audit covered in-tree tops and testbenches only; board qualification and external configurations were not evaluated. `docs/hardware_evidence.md` has no entry for `JSCR`, `NSA` or `POLY_STEP`; entries for Lucas, SU3, Neuro, RPLU2 and SOM exist and are unaffected by classification.

**POLY_STEP semantic discrepancy.** VM (`spu_vm.py`, `OPCODES.get("POLY_STEP")` branch): Padé P(x)/Q(x) evaluation into `R[r1]`, `R[r1+1]`. Core RTL (`spu13_core.v:1903`): RPLU Artery write `sel=7`, no scalar result.

**Proposed classification (no encoding changed).** `CORE_CANDIDATE`: `POLY_STEP 0xE0` (encoding only, semantics blocked). `IMPLEMENTATION_EXTENSION`: RPLU2 `0x2A`, `JSCR`, `NSA`. `LEGACY_EXPERIMENTAL`: Lucas, Neuro, SU3. `UNRESOLVED`: SOM `0x2A`/`0x2B` core membership, `PHADD`, `PHCFG`, `RATIO_CMP`.

**Proposed ownership of the amendment items.** Amendment text: `ISA_V0_2_REVIEW_DRAFT.md` §6.2–§6.5, §9 (O9–O13).

## Adversarial-review outcome (AR1)

Independent adversarial review report `/tmp/isa-v02-adversarial-review-eaabd9f.md` (stored outside the repository; reviewed tree: `dev/next` HEAD `eaabd9f`, full `eaabd9fcc3ff40ceb73ec7931f391c1a115fa840`; produced by the Codex reviewer at the owner's direction. No other review revision identifier exists, and none is invented here). Items attributed to it were not independently reproduced by the author unless stated. Accepted findings applied above: O6-1 to O6-4 and D1-1 to D1-5 as wording and scope corrections. Generator, classifier labels and frozen JSON were not changed (HOLD).
