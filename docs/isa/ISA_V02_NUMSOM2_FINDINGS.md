# ISA-V02-NUM-SOM-2 — Experimental signed-P comparator fixture

**Status:** a two-line signed-P change to the SOM serial comparator, applied to a **scratch fixture only**, fixes the reproduced winner mismatch in directed RTL simulation of `spu_som_bmu`, but it is **not behavior-preserving** for callers that use P-weight 1 with keys in [2³¹, 2³²). Finite-width arithmetic discrepancies remain. The H0 SOM and RPLU2 are **not qualified**. Production implementation, the numerical-domain decision and ratification **HOLD**. No production RTL, algorithm, VM, ISA, assembler or SPI change.
**Source identity:** `dev/next` at `65331020664293b5095693aab4729294bd808d82`. Production `hardware/rtl/core/spu13/spu_som_bmu.v` SHA-256 `61bd3eed541feb1d14ce95bd9cbd6d20aa723a9fbbe50346a6bae89809172cd1` (recorded in the fixture header and checked by the runner). Preserved evidence is added by the commit containing this file (`git log -1 -- docs/isa/ISA_V02_NUMSOM2_FINDINGS.md`).
**Toolchain:** Icarus Verilog 11.0 (stable), four-state, `-g2012`; Python 3.10.12.
**Evidence classes:** *RTL observation* = simulation of production or fixture RTL; *host model* = Python reference (exact signed/unsigned comparator, fixed-width keys, unbounded exact winner, cross-checked against `software/lib/rational_som.py` through the NUM-SOM-1 models); *host-derived bound* = arithmetic on the fixed weights, not RTL. Nothing here is a physical-hardware result. Follows [`ISA_V02_NUMSOM1_FINDINGS.md`](ISA_V02_NUMSOM1_FINDINGS.md), whose fixtures are reused unchanged.

## 1. Scratch patch

The fixture `spu_som_bmu_expsgn.v` is **an experimental test fixture, not production RTL and not an adopted design**. It is production `spu_som_bmu.v` with both modules renamed `*_expsgn` (so they compile beside the production modules) and one functional change in `spu_surd_lt_serial`:

```
-    wire signed [32:0] da = $signed({1'b0, lhs[63:32]})
-                                  - $signed({1'b0, rhs[63:32]});
+    wire signed [32:0] da = $signed({lhs[63], lhs[63:32]})
+                                  - $signed({rhs[63], rhs[63:32]});
```

The runner regenerates the expected fixture text from the current production file and the patch above and fails if the committed fixture differs (drift check; verified by editing the fixture). Weight wiring is unchanged.

## 2. Preserved evidence

`hardware/tests/spu13/num_som_2/`:

| File | Role |
|---|---|
| `spu_som_bmu_expsgn.v` | experimental fixture (header labels it as such and records the production hash) |
| `fixture_build.py` | derives the fixture text from production (single source of truth for the patch) |
| `cmp_probe.v`, `cmp_vectors.py` | comparator probe (production and fixture modules in lockstep) and its deterministic vector set |
| `numsom2_probe.v`, `cases2.py` | BMU probe (DUT module chosen by `` `BMU_MOD ``) and 33 cases: the 19 unchanged NUM-SOM-1 cases (imported from `../num_som_1/cases.py`), 11 boundary cases, 3 legacy large-key witnesses |
| `som2_models.py` | host references and result matrix; reuses `../num_som_1/som_models.py` |
| `run_num_som_2.py` | builds and runs everything in a temporary directory and compares with the fixed expectations; **no option to regenerate** them; `--expected DIR` selects another expectation directory |
| `expected/` | `vectors.sha256`, `cmp_codes.txt` (one code per vector: 2×production + experimental decision), `bmu_{orig,new}_{wired,control}.txt` (CASE/RES/CMP lines), `summary.txt` |

```bash
python3 -I hardware/tests/spu13/num_som_2/run_num_som_2.py     # about 15 s
```

Expected: `PASS` for each of the seven expectation files and `RESULT: PASS`. The file names avoid the substring `tb`, and the directory is not among the runner's scanned source directories, so `run_all_tests.py` does not discover or compile them (checked); they are **not** part of the regression gate. The runner was checked to fail when one RTL log line, one comparator code, one summary line, or the fixture text is altered (on copies of the expectation directory or a restored fixture; the preserved files are unchanged).

**Hashes (SHA-256):** `cmp_vectors.py` `69773d2a11f16bc574b3bc6c67f51054aebfa494898040df3303c9db17f7edd5`; `cases2.py` `a994a4d8f9a5edd72773de447efd911d96d3085bf0ece40ef17ac81d4e086d27`; `fixture_build.py` `f28dde2e0c4081a6d6d8c735bc789fc2a5cf1929b762d397c995138a52b00b42`; `som2_models.py` `9bc8457d6aabee6d1ef00befed6e3e0751a3308f254b8f71aef6a78898c06cd5`; `run_num_som_2.py` `d850067bc40bcd9e8ca187d7ea584af826adb7afd4b8f6f71fc04456c648b6a5`; `cmp_probe.v` `c151855d77d5c99ed8b4321be12b5cf6c4e88d9a0fa1b8cc528632f1c15b8a72`; `numsom2_probe.v` `cc019a8c920b9be489b72e1a963121593bd62b65fe029b8866f73c14481b69a1`; `spu_som_bmu_expsgn.v` `5c7efe7cf2dac4e0b468d41514c16bb3e5c7326bdb5d2af15dc11f405c9cd92c`; `expected/cmp_codes.txt` `c447deb242e39e7a820fb72c91593d9f597afcdb4510410f7a040ef2be9a6983`; `expected/bmu_orig_wired.txt` `7e6774d9bf08e46e54207629ab8320fff03cfc87d9c5eff6e6931c01bb58453f`; `expected/bmu_new_wired.txt` `c68cff009abc35092fe6cc97735eb094ee014deefb41b7ef5834cd789b7730c3`; `expected/bmu_orig_control.txt` `54f3559208cc984606d141eac0c5a39f45217a726632793cc74b94020d646996`; `expected/bmu_new_control.txt` `f00bce2239b76e065093f5facb6bd4285be1538f76a78075f73c65f71a594ee1`; `expected/summary.txt` `f80cdbe8d005c85e002fce147bd4ecb14d8a9f83300a6ff4e3cf69528405c02d`; `expected/vectors.sha256` `004ac002af43a22d9edccdbdb58e39350d5308c3ab61baab92569201345a5970`.

## 3. Comparator comparison (34,641 vectors)

All 14,641 pairs of the 121 combinations of 11 edge values for P and for Q (±2³¹ boundaries, ±1, ±2, ±65536, 0), plus 20,000 pseudo-random pairs (xorshift64, seed `0x2026102700000001`, uniform, small-magnitude and edge-neighbourhood components). The vector hash is in `expected/vectors.sha256`; `cmp_codes.txt` preserves both decisions for every vector.

* comparator vectors: 34641
* production != unsigned-P exact model: 0
* experimental != signed-P exact model: 0
* production != experimental: 9811 (a P operand has bit 31 set: 9811; both P < 2^31: 0)
* latency (production, experimental) cycles seen: [(35, 35)]

The production comparator equals an exact reading of P as unsigned 32-bit; the fixture equals an exact reading of P as signed. They differ only when a P operand has bit 31 set. Unchanged 35-cycle latency for both.

## 4. BMU comparison: the 19 NUM-SOM-1 cases

"exact" is the unbounded exact winner on the narrowed inputs, ties to the lowest index. Wired = P-weight 0, Q-weight 1 (as `rplu_pipeline.v:162`); control = P-weight 1, Q-weight 0.

| Case | wired orig→patched | wired exact | wired outcome | control orig→patched | control exact | control outcome |
|---|---|---|---|---|---|---|
| W_witness | 4→6 | 6 | FIXED-by-patch | 6→6 | 6 | ok-both |
| Z_zero | 0→0 | 0 | ok-both | 0→0 | 0 | ok-both |
| NP_D3 | 0→6 | 6 | FIXED-by-patch | 6→6 | 6 | ok-both |
| PP_C-2 | 0→0 | 0 | ok-both | 0→0 | 0 | ok-both |
| N6_exact0 | 6→6 | 6 | ok-both | 6→6 | 6 | ok-both |
| TIE_A1B1 | 0→0 | 0 | ok-both | 0→0 | 0 | ok-both |
| QR0_reset | 0→1 | 1 | FIXED-by-patch | 1→1 | 1 | ok-both |
| NPq_A-1,1 | 4→0 | 0 | FIXED-by-patch | 0→0 | 0 | ok-both |
| PPq_A2,1 | 1→1 | 1 | ok-both | 1→1 | 1 | ok-both |
| PPq_A-3,-1 | 4→4 | 4 | ok-both | 4→4 | 4 | ok-both |
| NPq_A3,-1 | 1→1 | 1 | ok-both | 1→1 | 1 | ok-both |
| ALIAS_P | 1→1 | 1 | ok-both | 1→1 | 1 | ok-both |
| ALIAS_Q | 1→1 | 1 | ok-both | 1→1 | 1 | ok-both |
| MAXP | 1→1 | 1 | ok-both | 1→1 | 1 | ok-both |
| MINP | 1→1 | 4 | residual-arithmetic | 0→1 | 4 | residual-arithmetic (winner changed) |
| ALIAS_MIN | 1→1 | 4 | residual-arithmetic | 0→1 | 4 | residual-arithmetic (winner changed) |
| SQ_WRAP | 0→4 | 4 | FIXED-by-patch | 0→4 | 4 | FIXED-by-patch |
| ACC_2x2^16 | 1→1 | 1 | ok-both | 0→1 | 1 | FIXED-by-patch |
| ACC_4xMIN | 1→6 | 4 | residual-arithmetic (winner changed) | 0→6 | 4 | residual-arithmetic (winner changed) |

**Residual arithmetic discrepancies (three, wired and control):** MINP and ALIAS_MIN (the 18-bit feature-minus-weight difference wraps for node 1) and ACC_4xMIN (36-bit product and 32-bit accumulator wrap). In these the fixed-width keys differ from the exact keys, so a correct comparator cannot restore the exact winner. Under wired weights the patch fixes five of the eight production disagreements (W_witness 4→6, NP_D3 0→6, QR0_reset 0→1, NPq 4→0, SQ_WRAP 0→4); under control weights it fixes SQ_WRAP and ACC_2x2^16.

## 5. Numerical-boundary cases (11)

Four equal features at (±P,±Q) with P,Q of magnitude 9457, 9458, 9459 and 9500, plus one mixed-sign case:

| Case | wired orig→patched | exact | wired key32Diff | wired outcome | control orig→patched | control outcome |
|---|---|---|---|---|---|---|
| B_+9457,+9457 | 1→1 | 1 | 0 | ok-both | 1→1 | ok-both |
| B_-9457,+9457 | 1→1 | 1 | 0 | ok-both | 1→1 | ok-both |
| B_+9457,-9457 | 4→4 | 4 | 0 | ok-both | 4→4 | ok-both |
| B_-9457,-9457 | 4→4 | 4 | 0 | ok-both | 4→4 | ok-both |
| B_+9458,+9458 | 1→1 | 1 | 0 | ok-both | 1→1 | ok-both |
| B_-9458,+9458 | 1→1 | 1 | 0 | ok-both | 1→1 | ok-both |
| B_+9459,+9459 | 1→1 | 1 | 0 | ok-both | 1→1 | ok-both |
| B_-9459,+9459 | 1→1 | 1 | 0 | ok-both | 1→1 | ok-both |
| B_+9500,+9500 | 1→1 | 1 | 7 | ok-both | 1→1 | ok-both |
| B_-9500,+9500 | 1→1 | 1 | 7 | ok-both | 1→1 | ok-both |
| B_mixed | 0→3 | 3 | 0 | FIXED-by-patch | 3→3 | ok-both |

`key32Diff` is the number of nodes whose 32-bit accumulated key differs from the exact key. At 9457–9459 all keys are exact. At 9500 every node's key differs under wired weights although the winner still matches. **B_mixed lies inside the provisional bound and the production RTL selects the wrong node (0 instead of 3); the patch corrects it**, i.e. the signed/unsigned defect is not confined to extreme inputs.

## 6. Legacy large-key compatibility witnesses (3)

| Case (control weights) | production | experimental | exact | outcome |
|---|---|---|---|---|
| BIG_A46341 | 1 | 0 | 1 | REGRESSED-by-patch |
| BIG_A46340 | 1 | 4 | 1 | REGRESSED-by-patch |
| BIG_A-46341 | 4 | 0 | 4 | REGRESSED-by-patch |

With P-weight 1 the P slot is a sum of non-negative terms that can legitimately lie in [2³¹, 2³²) (for example 46341² = 2 147 488 281). The production comparator reads these exactly; the experimental signed reading treats them as negative and selects the wrong node in all three witnesses. The legacy core SOM uses P-weight-1-style weights (`som_fw` in `spu13_core.v`); the Tang and Artix SOM probe tops were not reviewed; whether any caller's operating range reaches [2³¹, 2³²) is **not reviewed**. The same inputs under wired weights fall outside the provisional bound (rows are in `expected/summary.txt`).

## 7. Legacy regression outcomes and tests not run

* spu13_som_bmu_tb production: PASS lines=1 FAIL lines=0
* spu13_som_bmu_tb experimental: PASS lines=1 FAIL lines=0
* spu13_som_bmu_tb: outputs identical between variants: True
* spu_som_train_tb production: PASS lines=5 FAIL lines=0
* spu_som_train_tb experimental: PASS lines=5 FAIL lines=0
* spu_som_train_tb: outputs identical between variants: True

Each existing testbench was compiled against the production module and against the fixture (the fixture run uses a temporary copy of the testbench with the BMU module name replaced). **Not run:** `software/tests/test_som_bmu_rtl_trace.py` (compiles from the production path, WIDTH 32), the Tang 25K and Artix-7 SOM probe tops, the core with `ENABLE_CORE_SOM` or the RPLU2 pipeline (`rplu_pipeline.v`), BTU and Padé, `run_all_tests.py`, synthesis, timing and any physical hardware.

## 8. Provisional numerical bound

* host-derived box bound (wired, provisional): |P|,|Q| <= 9458; worst accumulated key 2147117334 at B, 2147571366 at B+1
* host-derived box bound (control, provisional): |P|,|Q| <= 11584; worst accumulated key 2147163912 at B, 2147534628 at B+1

With the fixed node weights and each narrowed feature component independently anywhere in [−B, B], the host-derived bound keeping every accumulated key within signed 32 bits is 9458 (wired) and 11584 (control). **±9,457 is recorded as a provisional bound** (conservative by one against this derivation), **not a qualified numerical guarantee**: it assumes the fixed weights, four features, the box domain and a correct signed comparator; RTL evidence covers the sampled points above only; the enforcement mechanism is undecided.

## 9. Why range enforcement must precede narrowing

The core hands the BMU only the low 18 bits of each 32-bit P and Q half (`spu13_core.v:582-587`). Values that differ by a multiple of 2¹⁸ become identical BMU inputs (ALIAS_P: P = 2 + 2¹⁸ gives the same result as P = 2; ALIAS_Q likewise; ALIAS_MIN shows the effect on the narrowed winner). A bound checked on the narrowed fields would accept a 32-bit value far outside the bound. The check must therefore be applied to the original 32-bit halves before narrowing (and must also guard the 18-bit difference wrap seen in MINP). Hardware guards, wider arithmetic or a restricted profile remain open decisions.

## 10. Interpretation and open decisions

1. The experimental signed-P comparator resolves the demonstrated defect for the wired H0 weights but introduces a regression for P-weight-1 callers with keys in [2³¹, 2³²); neither reading is exact everywhere (unsigned: [0, 2³²); signed: [−2³¹, 2³¹)).
2. A preferred direction, **not authorized for implementation**, is a compile-time signedness choice (default unchanged for legacy callers; signed only for the RPLU2 pipeline instance) or an isolated signed variant, followed by synthesis and timing assessment.
3. Open: the adopted domain bound and its enforcement, review of the legacy callers' key range, BTU/Padé behavior, and any hardware result. The SOM remains unqualified.
