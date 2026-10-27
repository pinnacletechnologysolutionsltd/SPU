# ISA-V02-NUM-SOM-1 — Directed SOM comparator verification

**Status:** directed simulation of `spu_som_bmu` **reproduces** a winner mismatch caused by a signed/unsigned disagreement between the accumulator and the serial comparator. A separate finite-width arithmetic and narrowing discrepancy is also reproduced. Only the BMU module was simulated; the downstream BTU and Padé stages, the full core and Artix-7 hardware were not. Comparator repair, the numerical domain decision and ratification **HOLD**. No production RTL, VM, assembler, ISA or algorithm change.
**Source identity:** `dev/next` at `891d5db180b9875c724402a73ef57f6cb07a8586`; `spu_som_bmu.v` and `spu_som_weight_bram.v` are byte-identical to `cc25783`, where the mismatch was first reported. Preserved evidence is added by the commit containing this file (`git log -1 -- docs/isa/ISA_V02_NUMSOM1_FINDINGS.md`).
**Toolchain:** Icarus Verilog 11.0 (stable), four-state, `-g2012`; Python 3.10.12 for the host models.
**Evidence classes:** *RTL observation* = preserved simulation log; *host emulation* = Python model of the RTL formulas, validated against the log below; *mathematical reference* = unbounded exact arithmetic (and `software/lib/rational_som.py::find_bmu`). None is a physical-hardware result.

## 1. Preserved evidence

`hardware/tests/spu13/num_som_1/`:

| File | Role |
|---|---|
| `numsom1_probe.v` | Drives `spu_som_bmu` (`WIDTH=18`, 4 features, 7 nodes) as `rplu_pipeline.v` does; logs per-feature products, accumulator values and every comparator input/decision |
| `cases.py` | The 19 directed cases (64-bit QR components as `(P,Q)`) |
| `som_models.py` | Host emulation, signed-P hypothetical comparator, exact reference, matrix builder; asserts the host model equals the RTL log internally |
| `run_num_som_1.py` | Builds and runs both configurations in a temporary directory, compares with the fixed expectations; reports mismatches and **has no option to regenerate** them; `--expected DIR` selects an alternative expectation directory |
| `expected/rtl_wired.txt`, `rtl_control.txt`, `matrix.txt` | Fixed expected outputs (913, 913 and 123 lines) |

```bash
python3 -I hardware/tests/spu13/num_som_1/run_num_som_1.py     # under 1 s
```

Expected: `PASS rtl_wired`, `PASS rtl_control`, `PASS matrix`, `RESULT: PASS`. The file names avoid the substring `tb`, and the directory is not among the runner's scanned source directories, so `run_all_tests.py` does not discover or compile them (checked); they are **not** part of the regression gate. The runner was checked to fail when one expected RTL line, or one matrix line, is altered (on copies of the expectation directory; the preserved files are unchanged).

**Hashes (SHA-256):** `numsom1_probe.v` `9290cae4538e4dffcf35eb1896d7f8426d12a46c50b818ebbe979dc9d30a8761`; `cases.py` `0e8a7db4b9f9726e9c4a781eccb5fb0a1e4a5db34a54bc3bcc3dae7955198c31`; `som_models.py` `6286e8c3d769defdff37ec09bc925184bf96fa796668603bc213f5352ff42489`; `run_num_som_1.py` `548ff892e0725b8b92f1ab981a24aea186e2a7d6fe5fb8de90221455cfd4070f`; `expected/rtl_wired.txt` `586d2af1f5fbd247f76bd91b5ccfe57545d98390a7f7062def77ae0901d807f8`; `expected/rtl_control.txt` `84646c4f26a396c316708a7e91187e2feae94eb6b389ee994084d03c4d48a1c9`; `expected/matrix.txt` `73c51da44438396eb1f9a9b837cfe3fcabf16cea5fa8dfb9b5be60c28e18e848`.

## 2. Configuration

* **Fixed node weights** (`spu_som_weight_bram.v`, `initial` block, `(P,Q)` per feature): node 0 zero; node 1 f0 `(2,0)`; node 2 f1 `(2,0)`; node 3 f2 `(2,0)`; node 4 f0 `(-2,0)`; node 5 f1 `(-2,0)`; node 6 f2 `(-2,0)` and f3 `(1,1)`. The pipeline ties off the training port.
* **Wired feature weights** (default run): `{ONE,ZERO}` per feature, verbatim from `rplu_pipeline.v:162`. The RTL log shows `fw=0x40000`, i.e. **P-weight 0, Q-weight 1**. The BMU passes the low field as `wp` and the high field as `wq` (`spu_som_bmu.v`), and the weight RAM and testbench pack `{q,p}`. Each node key is therefore √3 times the quadrance: P slot `3·sq_q = 6Σdp·dq` (signed), Q slot `Σ(dp²+3dq²)`.
* **Control** (`-DCTRL`): P-weight 1, Q-weight 0 (the convention of `spu13_som_bmu_tb.v`), P slot `Σ(dp²+3dq²)`.
* **Input narrowing:** the probe copies `spu13_core.v:582-587` (`{rs[32+:18], rs[0+:18]}`); the core itself is not simulated.
* **Comparator** (`spu_surd_lt_serial`, in `spu_som_bmu.v`): `da = $signed({1'b0, lhs[63:32]}) − $signed({1'b0, rhs[63:32]})` zero-extends the upper (P) half; `db` sign-extends the lower (Q) half. The accumulator emits `q_accum_p` as a 32-bit truncation of a signed sum.
* **Not connected:** `accum_overflow` is not wired out of the BMU in `rplu_pipeline.v`.

## 3. Primary witness (wired weights)

Input A=B=C=−3, D=2, Q=0 (all four features, narrowing no effect):

| Node | Mathematical key (P′,Q′) | Value | Encoded P32 / Q32 |
|---|---|---|---|
| 0 | (0,31) | 53.69 | `00000000` / `0000001f` |
| 1, 2, 3 | (0,47) | 81.41 | `00000000` / `0000002f` |
| 4, 5 | (0,23) | 39.84 | `00000000` / `00000017` |
| 6 | (−6,23) | 33.84 | `fffffffa` / `00000017` |

**RTL selects node 4; the mathematical nearest node is 6.** Per-feature products and accumulators equal the mathematical keys exactly for all seven nodes (no finite-width effect). For node 6 the comparator receives lhs P `0xFFFFFFFA` (−6 signed) and returns `lt=0` against the current best `(0x00000000, 0x17)`, both against best and against second best; a comparator reading P as signed returns `lt=1` for both. With P-weight 1 (control), the same input selects node 6.

## 4. Result matrix

Columns: **RTL** observed winner; **emu** host emulation (equals RTL in all 38 runs); **fwSgn** fixed-width keys under a hypothetical signed-P comparator; **idNarr** exact winner on the narrowed 18-bit inputs; **idRaw** exact winner on the original 32-bit inputs; **cmpBad** number of logged comparator decisions that differ from the signed-P reading of the same encoded inputs; **keyDiff** number of nodes whose fixed-width key differs from the exact key. Class: *comparator* = RTL ≠ fwSgn; *arithmetic* = fwSgn ≠ idNarr; *narrowing* = idNarr ≠ idRaw. Ties resolve to the lowest node index in all models.

**Wired (P-weight 0, Q-weight 1):**

| Case | RTL | emu | fwSgn | idNarr | idRaw | cmpBad | keyDiff | Class |
|---|---|---|---|---|---|---|---|---|
| W_witness (−3,−3,−3,2) | 4 | 4 | 6 | 6 | 6 | 2 | 0 | comparator |
| Z_zero | 0 | 0 | 0 | 0 | 0 | 0 | 0 | agree |
| NP_D3 (0,0,0,D=3) | 0 | 0 | 6 | 6 | 6 | 2 | 0 | comparator |
| PP_C-2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | agree |
| N6_exact0 (C=−2, D=(1,1)) | 6 | 6 | 6 | 6 | 6 | 0 | 0 | agree |
| TIE_A1B1 (nodes 0, 1, 2 tie) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | agree |
| QR0_reset (A=(P0,Q1), B=C=D=0) | 0 | 0 | 1 | 1 | 1 | 2 | 0 | comparator |
| NPq A=(−1,1) | 4 | 4 | 0 | 0 | 0 | 4 | 0 | comparator |
| PPq A=(2,1) | 1 | 1 | 1 | 1 | 1 | 0 | 0 | agree |
| PPq A=(−3,−1) | 4 | 4 | 4 | 4 | 4 | 0 | 0 | agree |
| NPq A=(3,−1) | 1 | 1 | 1 | 1 | 1 | 0 | 0 | agree |
| ALIAS_P (P=2+2¹⁸) | 1 | 1 | 1 | 1 | 1 | 0 | 0 | agree |
| ALIAS_Q (Q=2¹⁸) | 1 | 1 | 1 | 1 | 1 | 0 | 0 | agree |
| MAXP (P=2¹⁷−1) | 1 | 1 | 1 | 1 | 1 | 0 | 1 | agree |
| MINP (P=−2¹⁷) | 1 | 1 | 1 | 4 | 4 | 0 | 1 | arithmetic |
| ALIAS_MIN (P=2¹⁷) | 1 | 1 | 1 | 4 | 1 | 0 | 1 | arithmetic, narrowing |
| SQ_WRAP (P=Q=−2¹⁷) | 0 | 0 | 4 | 4 | 4 | 2 | 7 | comparator |
| ACC_2x2^16 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | agree |
| ACC_4xMIN (four features P=−2¹⁷) | 1 | 1 | 6 | 4 | 4 | 2 | 4 | arithmetic, comparator |

RTL differs from the narrowed mathematical winner in 8 of 19 cases: six have a wrong comparator decision (one of them, ACC_4xMIN, also has an arithmetic component) and two (MINP, ALIAS_MIN) are arithmetic only. SQ_WRAP changes the fixed-width key of every node yet the signed-P winner still equals the mathematical winner, so its error is the comparator's. In MINP the 18-bit difference wraps for node 1 (`−131072 − 2` wraps to `+131070`), which makes the fixed-width distance wrong before any comparison. ALIAS_MIN equals the exact winner for the raw (un-narrowed) input only by coincidence of that wrap.

**Control (P-weight 1, Q-weight 0):** 14 of 19 cases agree. The ordinary cases (W_witness, NP_D3, QR0_reset, NPq A=(−1,1)) agree. The five that differ from the narrowed mathematical winner — MINP, ALIAS_MIN, SQ_WRAP, ACC_2x2^16, ACC_4xMIN — are all wrap, truncation or boundary cases. The full per-case table, and per-node keys with the comparator inputs for W_witness and QR0_reset in both configurations, are in `expected/matrix.txt`.

## 5. Interpretation

1. **Signed/unsigned interface mismatch (RTL-reproduced).** The comparator is internally exact for its encoded inputs: every logged decision equals the model that reads P as unsigned. The mismatch is between producer (a signed, truncated P slot) and consumer (P zero-extended). With the wired weights the P slot is `6Σdp·dq`, which is negative for ordinary inputs (witness, NP_D3, QR0_reset, NPq). With P-weight 1 the slot is a sum of non-negative terms except where the 36-bit or 32-bit arithmetic wraps, which is why the control cases differ only at the boundaries.
2. **QR0 at READY.** The READY value of QR0 (A=(P0,Q1), B=C=D=0, see H0-NUM-1 §1) as the `0x2A` source selects node 0 in RTL; the mathematical winner is node 1.
3. **Finite-width arithmetic and narrowing** (18-bit differences, 36-bit products, 32-bit accumulator, 18-bit input narrowing) change the distance itself independently of the comparator (MINP, ALIAS_MIN, ACC_4xMIN, SQ_WRAP). A signed comparator would not correct these.
4. **Weights.** Switching to P-weight 1 removes the ordinary-input failures in these cases but would conceal rather than establish comparator correctness (the boundary cases still fail under the unsigned reading). Weight wiring is left unchanged.

## 6. Limitations

Nineteen directed cases per configuration do not characterize the SOM domain. Only `spu_som_bmu` and `spu_som_weight_bram` were simulated, with a copy of the pipeline's weight constants and the core's narrowing expression; `rplu_pipeline.v`, BTU, Padé and the core were not. Four-state simulation; no synthesis, timing or physical result. The tie case exercises one tie (nodes 0, 1, 2).

## 7. Preferred correction direction and decisions (not implemented)

* **Preferred, not authorized for implementation:** interpret the comparator's P coefficient as signed (sign-extend the upper half instead of zero-extending). Regression requirements: these 19 cases in both configurations, the existing SOM testbench and trace test, ties, and the downstream pipeline.
* **Open decision:** a provably safe, enforceable input domain for the 18-bit subtraction, squaring and cross-products, per-feature accumulation, final P/Q representation and tie-breaking, versus hardware guards or wider arithmetic. Connecting `accum_overflow` alone would not detect the earlier wraps.
* **Two oracles are needed:** a mathematical oracle (the intended nearest node, lowest index on an exact tie) and a bit-exact model of the current RTL, kept as the regression reference that shows a repair changes the defective behavior.
