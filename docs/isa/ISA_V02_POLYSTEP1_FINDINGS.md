# ISA-V02-POLYSTEP-1 — What "`POLY_STEP`" names in the sources

**Status:** read-only source characterization plus one bounded host-side experiment; normative `POLY_STEP` semantics **HOLD**. No VM, assembler, opcode, RTL, test or hardware change; no instruction renamed; no opcode table rewritten.
**Starting identity:** `dev/next` at `fe6365da69f6615ae4e050bc2f269998f9fb0237` (AR1 corrections, clean). Existing VM, assembler and RTL sources are unchanged from public RC2 `b063280` (`b0632806621ed6fe44c9c72f4e0adbd8ee8df776`); analysis tools and tests were added in `dev/next`. Line numbers are at `fe6365d`.
**Method:** source reading; one scratch run of the Python VM from a temporary directory (see §3). Nothing was synthesized or simulated in RTL.

## 1. Seven things called `POLY_STEP`

| # | Where | What it is |
|---|---|---|
| 1 | Spec `knowledge/isa_reference.md:178` | `0x60 POLY_STEP Rd,Rx`, "Horner step via RPLU (legacy Morse potential)". The note above it (`:172`) calls `POLY_STEP`/`RATIO_CMP` "older extension-space definitions rather than the interface used by the silicon-tested `RPLU2PADE` spin". |
| 2 | Python VM `software/spu_vm.py:2373` (table `:629-631`) | One full [4/4] Padé evaluation. `x` is read as a signed Q32 integer from `R[r2].a`; two coefficient files are read; a 128-bit-truncating Q32 Horner pass runs on each; numerator goes to `R[r1]`, denominator to `R[(r1+1) mod 26]`, both as `RationalSurd(value, 0)`; `p1_a` selects a coefficient set (only an in-memory cache key; both files are fixed). Effective opcode `0xE0` (the dict also binds `0x60` earlier; the later binding wins). |
| 3 | `software/spu4_intrinsics.h:56-72` | Documents `POLY_STEP Rbase, Rx` as the same Padé evaluation "in hardware" (`Rbase` = P, `Rbase+1` = Q, `x` as Q32 in `.a`), and separately `spu_rplu_poly_step(idx)`, "a single Horner step command". |
| 4 | Lithic-L `software/common/include/spu_lithic_l.h:56-57` | `L_OP_POLY_STEP = 0xE0` ("Horner single-step to RPLU") and `L_OP_RATIO_CMP = 0xE1`. |
| 5 | SPU-13 RTL core `hardware/rtl/core/spu13/spu13_core.v:1899-1907` | On an accepted `0xE0`: `artery_wr_en <= 1`, `artery_wr_data <= {8'hA5, 8'd7, 1'b0, inst[33:24], 1'b1, 36'd0}`. No scalar result and no register write. The same chord shape is emitted autonomously by the hydration/torus sequencer (`:1964-1975`, comment "Emit a POLY_STEP Artery chord"). |
| 6 | Datapath helpers `hardware/rtl/gpu/rplu_poly_step.v:1-12`, local chains in `pade_eval_4_4.v:55-65`, `rplu_exp.v:112,172` | A combinational single Horner step (`acc_out = (acc_in·x_q32)>>>32 + coef_q32`), instantiated under `USE_LOCAL_POLY`-style parameters. A module, not an instruction decode. |
| 7 | Host tool `tools/rplu_loader.py:27-40` | `--poly-step` sets selector 7 and emits the config chord. |

These are not one instruction with several implementations. Items 2/3 define a result-producing evaluation; item 5 a control write; item 6 an arithmetic module; item 1 a different, legacy, Horner step.

## 2. Python VM: coefficient path and silent zero fallback

- The handler loads `hardware/common/rtl/gpu/pade_num_4_4_q32.mem` and `pade_den_4_4_q32.mem` (`spu_vm.py:2383-2384`), relative to the working directory.
- That directory does not exist in the tree. The files are at `hardware/rtl/arch/pade_num_4_4_q32.mem` and `pade_den_4_4_q32.mem`.
- On any read failure the loader falls back to five zero coefficients without a warning (`:2386`, `:2395-2398`).
- Consequence in the repository as committed: `POLY_STEP` returns numerator 0 and denominator 0 for every `x`. Observed from the repository root at `eaabd9f`/`fe6365d`: `x` low 16 bits 0 and 1 both gave `R0=(0,0)`, `R1=(0,0)`, with a cache of all-zero coefficients.
- The repository's own test `software/spu_vm_polystep_ratiocmp_test.py` **fails** in that state (`python3 software/spu_vm_polystep_ratiocmp_test.py` prints `POLY_STEP+RATIO_CMP tests: FAIL`, exit 2, "inequality test failed"; the equality case passes only because `0/0` compares equal to itself). It is not listed in `run_all_tests.py` (no `polystep` match), so no gate catches it.

## 3. Bounded experiment: intended VM semantics with the path supplied

Run from a temporary directory outside the repository containing a symlink `hardware/common/rtl/gpu → <repo>/hardware/rtl/arch` (nothing was written under the repository). With a register `R2 = RationalSurd(x_q32, 0)` and `POLY_STEP R0, R2`:

| x | numerator (Q32) | denominator (Q32) | ratio |
|---|---|---|---|
| 0 | 4294967296 | 4294967296 | 1.000000 |
| 0.5 | 3330037701 | 5490303990 | 0.606531 |
| 1.0 | 2559084680 | 6956313102 | 0.367879 |
| −1.0 | 6956313102 | 2559084680 | 2.718282 |

The ratios match `e^(−x)` to six digits: the intended VM operation is a [4/4] Padé evaluation of `e^(−x)` in Q32. This is a separate observation from the repository-default behavior in §2. It was not compared with any RTL datapath (`pade_eval_4_4.v` or the silicon-tested RPLU2 Padé unit); the VM comment's claim to match hardware widths and truncation is unverified.

## 4. RTL handler and its observability

- The `0xE0` handler writes no register and returns no value; its only effect is the Artery chord on `artery_wr_en`/`artery_wr_data`.
- On the Artix-7 top the core's `artery_wr_en` and `artery_wr_data` outputs are unconnected (`hardware/boards/artix7/spu_a7_top.v:791`: `.artery_wr_en(), .artery_wr_data()`), so the chord is discarded there.
- Other tops (`spu_a7_math_top.v`, Colorlight RPLU2 top, three Tang tops, `spu_system.v`) reference these signals; their consumers were **not traced**.
- No testbench issues a `0xE0` word to `spu13_core` (`grep` of `hardware/tests` finds `8'hE0` only in the Neuro adapter testbench, as `NEURO_CFG`, and the module-level `pade_eval_4_4_tb_localpoly.v`). The handler is therefore not exercised as an instruction by any testbench found. `docs/hardware_evidence.md` has no `POLY_STEP` entry.
- **Selector 7 ownership is unverified.** The core's own config decode treats `dec_fast_cfg_sel == 3'd7` as torus control (`spu13_core.v:1867`), while the loader and the `0xE0` handler describe selector 7 as "poly_step". The chord's consumers, and whether the two uses are the same path, were not traced.
- The core also exposes `ratio_cmp_res`/`ratio_cmp_valid` outputs (`spu13_core.v:90-91`, tied to 0 in one generate branch, `:1734-1735`). Their relation to `RATIO_CMP` as an instruction was not traced.

## 5. `RATIO_CMP` and the Neuro collision

- Spec and Python VM: `RATIO_CMP = 0x61` (`isa_reference.md:179`, `spu_vm.py:629`); VM handler `:2437` cross-multiplies and writes `-1/0/1` into `R[r1]`.
- Lithic-L: `L_OP_RATIO_CMP = 0xE1` (`spu_lithic_l.h:57`).
- `0xE1` is `NEURO_START` in the Neuro sidecar (`spu13_neuro_sidecar_adapter.v:79`), exercised on the Tang probe (`docs/hardware_evidence.md` §3.2d, around `:520-526`).
- The Python VM table mixes profiles: `POLY_STEP` takes the Lithic-L value `0xE0`, `RATIO_CMP` keeps the legacy `0x61`. The pair is no longer adjacent in encoding.

## 6. Silicon-tested Padé versus an instruction-triggered `POLY_STEP`

The Padé functionality with silicon evidence (RPLU2 Padé spin; `docs/hardware_evidence.md` §3.2f and related entries) is reached through the SPI/config control path, not through an `0xE0` instruction; `isa_reference.md:172` says so. No evidence in the repository shows a core executing an instruction-triggered Padé `POLY_STEP`. Neither the VM operation (§1 item 2) nor the Artery write (item 5) has a silicon entry.

## 7. Proposed disposition (documentation level; ratification HOLD)

- **Padé evaluation:** a candidate typed extension, provisional encoding `0xE0`, semantic qualification HOLD. A definition would have to fix the coefficient source (identity and hash, not a working-directory-relative path), the Q32 `x` domain in `.a`, the exact truncating Horner algorithm, the result-register contract and refusal or missing-coefficient behavior.
- **Artery chord emission:** a separate, implementation-specific operation, not asserted equivalent to the VM operation, no register result, discarded on the Artix-7 top.
- **Historical `0x60`:** legacy documentation only; not a newly assigned encoding.
- **`RATIO_CMP`:** encoding and profile reconciliation HOLD (`0x61` versus `0xE1`; Neuro collision).
- **Common core:** `POLY_STEP` is removed from the proposed common-core candidates. Existing RTL is not deleted or changed by this scope decision.

## 8. Blockers and limitations

1. The Python VM's stale coefficient path and silent zero fallback (a defect in existing code; no repair authorized) and the failing, ungated test.
2. No equivalence evidence between the VM Horner and any RTL Padé datapath.
3. Selector 7 ownership and the chord consumers in non-Artix-7 tops.
4. The `0xE0` collision with `NEURO_CFG` and the `0xE1` collision with `NEURO_START`, resolved today only by the absence of any in-tree top that combines them.
5. Limitations: source reading plus one VM run; no elaboration, simulation or synthesis; SPU-4 not examined; the O6 inventory is a non-exhaustive census (see `ISA_V02_O6_FINDINGS.md`).
