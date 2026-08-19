# ROTC 0–35 Angle Catalog & Reference

This document serves as the normative reference table for the 36 ROTC angles (0–35), their invariant axes, circulant parameters ($F, G, H$), periods, and inverse relationships.

## Corrected ROTC 0–35 Angle Catalog

| ROTC angle | Name | Invariant axis | F | G | H | Period | Inverse |
|---:|---|---|---:|---:|---:|---:|---:|
| 0 | identity | — | 1 | 0 | 0 | 1 | 0 |
| 1 | thirds period-6 | A | 2/3 | 2/3 | -1/3 | 6 | 4 |
| 2 | P5 forward cycle | A | 0 | 1 | 0 | 3 | 5 |
| 3 | thirds period-2 | A | -1/3 | 2/3 | 2/3 | 2 | 3 |
| 4 | thirds period-6 inverse | A | 2/3 | -1/3 | 2/3 | 6 | 1 |
| 5 | P5 inverse cycle | A | 0 | 0 | 1 | 3 | 2 |
| 6 | conjugate of angle 4 about B | B | 2/3 | -1/3 | 2/3 | 6 | 7 |
| 7 | conjugate of angle 1 about B | B | 2/3 | 2/3 | -1/3 | 6 | 6 |
| 8 | conjugate of angle 3 about C | C | -1/3 | 2/3 | 2/3 | 2 | 8 |
| 9 | conjugate of angle 1 about C | C | 2/3 | 2/3 | -1/3 | 6 | 13 |
| 10 | conjugate of angle 4 about D | D | 2/3 | -1/3 | 2/3 | 6 | 14 |
| 11 | conjugate of angle 3 about D | D | -1/3 | 2/3 | 2/3 | 2 | 11 |
| 12 | 180° about B | B | -1/3 | 2/3 | 2/3 | 2 | 12 |
| 13 | 240° about C | C | 2/3 | -1/3 | 2/3 | 6 | 9 |
| 14 | 60° about D | D | 2/3 | 2/3 | -1/3 | 6 | 10 |
| 15 | P5 fwd about B | B | — | — | — | 3 | 16 |
| 16 | P5 inv about B | B | — | — | — | 3 | 15 |
| 17 | P5 fwd about C | C | — | — | — | 3 | 18 |
| 18 | P5 inv about C | C | — | — | — | 3 | 17 |
| 19 | P5 fwd about D | D | — | — | — | 3 | 20 |
| 20 | P5 inv about D | D | — | — | — | 3 | 19 |
| 21 | (AB)(CD) | — | — | — | — | 2 | 21 |
| 22 | (AC)(BD) | — | — | — | — | 2 | 22 |
| 23 | (AD)(BC) | — | — | — | — | 2 | 23 |
| 24 | 180° edge (CD) | — | — | — | — | 2 | 24 |
| 25 | 180° edge (AB) | — | — | — | — | 2 | 25 |
| 26 | 90° face (x) | — | — | — | — | 4 | 27 |
| 27 | 270° face (x) | — | — | — | — | 4 | 26 |
| 28 | 180° edge (BC) | — | — | — | — | 2 | 28 |
| 29 | 90° face (z) | — | — | — | — | 4 | 30 |
| 30 | 270° face (z) | — | — | — | — | 4 | 29 |
| 31 | 180° edge (AD) | — | — | — | — | 2 | 31 |
| 32 | 180° edge (BD) | — | — | — | — | 2 | 32 |
| 33 | 270° face (y) | — | — | — | — | 4 | 35 |
| 34 | 180° edge (AC) | — | — | — | — | 2 | 34 |
| 35 | 90° face (y) | — | — | — | — | 4 | 33 |

## Group Structure & Tranches

* **Tranche 1 (Angles 12–14):** Missing thirds conjugates supplying inverses ($13 \leftrightarrow 9$, $14 \leftrightarrow 10$).
* **Tranche 2 (Angles 15–23):** $A_4$ pure-permutation subgroup (12 elements total including identity and angles 2/5). These are pure coordinate permutations with zero multiplies (bypass path). Angles 21–23 are double transpositions using dedicated bypass signals (`bypass_ab_cd`, `bypass_ac_bd`, `bypass_ad_bc`).
* **Tranche 3 (Angles 24–35):** 12 remaining cube rotations ($S_4 \setminus A_4$). Integer $3 \times 3$ matrices on $(B,C,D)$ with entries $0, \pm 1$ (no $\mathbb{Q}(\sqrt{2})$) hardwired in `spu13_rotor_core_tdm.v` with $A$ recomputed from zero-sum (`recompute_A`).
* **Edge Labels:** Swapped cube diagonals (each 180° edge rotation is negation $\circ$ that transposition). Face axes $x/y/z$ are shared with double transpositions ($26^2 = 27^2 = 21$, $29^2 = 30^2 = 23$, $33^2 = 35^2 = 22$).

## RTL & Datapath Encoding

1. **Thirds Angles (1, 3, 4, 6–14):** Use the TDM circulant path ($F,G,H$ surd multiplies $+ /3$). Note: the $/3$ divisibility caveat (`knowledge/SPU_LEXICON.md`) applies.
2. **Bypass Angles (2, 5, 15–20):** Hardware bypass (`bypass_p5`, `bypass_p5_inv`) with zero multiplies, combined with axis permutation (`perm_sel`) for 15–20.
3. **Double Transposition Angles (21–23):** Dedicated double-transposition bypass signals.
4. **Axis Permutation Wrapper (6–23):** Wrapped in `spu_quadray_permute` (`u_perm_fwd` / `u_perm_inv` in `spu13_core.v`). The target invariant axis is rotated into the circulant's A slot and back.
5. **Consistency Invariant:** $F/G/H$ for 0–14 must stay bit-identical across:
   - Python VM: `_ROTC_TABLE` in `software/spu_vm.py`
   - RTL core decode: `rote_F/G/H` lookup in `hardware/rtl/core/spu13/spu13_core.v`
   - RTL rotor core: `angle_scalar_*_sum` functions in `hardware/rtl/core/spu13/spu13_rotor_core_tdm.v`

## Verification

Trace equivalence is validated by:
```bash
python3 software/tests/test_rotc_vm_rtl_trace.py
```
This checks all 36 angles (336 bit-exact checks) against both rotor datapaths.
