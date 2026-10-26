# SOM-RP0a — exact portable C99 BMU over the full SOM v1 domain (COMPLETE, host-only)

2026-10-20. Class A, owner option 3, amended: the confirmed RTL width defect no longer blocks continuing with oracle-correct host
software. The original width audit is preserved **unchanged** in [HALT_RECORD.md](HALT_RECORD.md); the defect is tracked in
[RTL_REPAIR_BACKLOG.md](RTL_REPAIR_BACKLOG.md). No RTL, uploader, firmware, simulator, oracle or product-contract file was touched. Nothing
was flashed or run on hardware; SOM-RP0b stays HOLD. All results are `simulation-only` / `host-only`.

```bash
mkdir -p build/som_rp0
timeout 60 bash -c 'ulimit -v 1048576; cc -std=c99 -O2 -Wall -Wextra -Werror -fno-fast-math research/som_rp0/bmu.c research/som_rp0/bmu_rtl.c research/som_rp0/harness.c -o build/som_rp0/harness'
timeout 60 bash -c 'ulimit -v 1048576; python3 -B -I research/som_rp0/oracle_compare.py --harness build/som_rp0/harness'
timeout 60 bash -c 'ulimit -v 1048576; python3 -B -I research/som_rp0/rtl_compare.py --harness build/som_rp0/harness --n 600'   # host iverilog
timeout 60 arm-none-eabi-gcc -std=c99 -O2 -mcpu=cortex-m33 -mthumb -Wall -Wextra -Werror -pedantic -c research/som_rp0/bmu.c -o build/som_rp0/bmu_m33.o
```

## Exact arithmetic bounds (full signed 18-bit domain; asserted at compile time in `bmu.c`)
Coefficients of features, prototypes and the four feature weights: c ∈ [−2¹⁷, 2¹⁷−1]. D = 2¹⁸−1.

| Quantity | Exact bound | Fits |
|---|---|---|
| Δ = x − w | \|Δ\| ≤ D (19-bit) | int64 |
| s_p = Δp² + 3Δq² ; s_q = 2ΔpΔq | s_p ≤ 4D² < 2³⁸ ; \|s_q\| ≤ 2D² < 2³⁷ | int64 |
| term_p = r_p s_p + 3 r_q s_q ; term_q = r_p s_q + r_q s_p | ≤ 10·2¹⁷·D² < 2⁵⁷ ; ≤ 6·2¹⁷·D² < 2⁵⁶ | int64 |
| distance (4 terms) | \|P\| ≤ 40·2¹⁷·D² < 2⁵⁹ ; \|Q\| ≤ 24·2¹⁷·D² < 2⁵⁸ | int64 |
| gap = second − best | \|gap_p\| < 2⁶⁰, \|gap_q\| < 2⁵⁹ | int64 |
| ordering: da, db (coefficient differences) | \|da\| < 2⁶⁰, \|db\| < 2⁵⁹; test needs da² vs 3db² (< 2¹²⁰ and < 3·2¹¹⁸) | **128-bit** |

64-bit arithmetic therefore suffices everywhere except the surd ordering test, which needs an exact 128-bit unsigned compare. It is built from
32×32→64 partial products (`mul_u64`, `add_u128`, `cmp_u128`), with absolute values taken without overflow; no `__int128`, no signed overflow, no shift of a
negative value, no implementation-defined truncation. Out-of-domain input is refused, never wrapped.

## Semantics and refusals
Winner, runner-up, label, exact best/second distances, gap = second − best, ambiguity (gap ≤ threshold, default 0), and ties to the lowest node id
(compared by id, so array order is irrelevant) follow `rational_som.py`. `som_bmu` returns `OK`, `OVERFLOW` (a feature coefficient outside the 18-bit range, including the
int32 extremes), `INVALID_MAP` (null pointers, node count ≠ 7, duplicate/out-of-range id, label ≥ 7, any node or weight coefficient outside the range) or `NO_NODES` (count 0);
on any refusal the result is zeroed (no partial output). The checksum is an artifact property validated by `tools/som_map.py`, not by this in-memory API.

## Equivalence with the Python oracle (executed)
1,489 accepted cases, every output field bit-exact: the 7-node `tiny_hex_fixture`; the checked Iris v1 map over all 150 samples; exact ties, zero gaps and thresholds;
surd-valued features; 300 random whole-domain cases; 400 corner cases (every coefficient at both ends of every range); cases around the RTL-safe boundaries; the four counterexamples
(control 14412+480√3, diffwrap 68,718,952,449, prodwrap 68,719,476,736, sumflag 14,400,000,000 exactly as the oracle gives). 14 refusal fixtures (5 overflow, 8 malformed map, no nodes)
all return the declared status with no partial output. 12,015 comparator pairs match `rs_lt`/`rs_le`, including da² − 3db² = ±1 Pell-style near ties scaled to 2⁴⁰ and random operands up to 2⁵⁹.
**Mutants killed:** 64-bit wrapping compare, later-node tie, lexicographic order, √3² = 2 (each fails the oracle comparison); dropping the DIFF check is killed by the independent reason check.

## RTL_UNSAFE: the proven equivalence domain of the CURRENT RTL (`bmu_rtl.c`, separately derived)
`som_bmu_rtl_safe` returns the exact result with `OK` only if the current `spu_som_bmu.v` reproduces it; otherwise `SOM_RTL_UNSAFE` plus the first failing reason (result zeroed).
The RTL is never the reference. For every node (not only the winner): **DIFF** each x−w in [−2¹⁷, 2¹⁷−1]; **TERM** each exact weighted term in [−2³⁵, 2³⁵−1] (36-bit ring: intermediate s_p, s_q wraps are harmless);
**SUM** exact P in [0, 2³²−1] (unsigned field) and Q in [−2³¹, 2³¹−1]; then **GAP** gap_p ∈ [0, 2³²−1], gap_q ∈ [−2³¹, 2³¹−1] (the SOM1 packing); **THRESH** threshold p ≥ 0. These are exact-value predicates, so sufficient for equality, not claimed necessary.
Validation: an arithmetic emulator of the RTL equals the **real RTL** (unmodified, iverilog) on 616 vectors; all 109 `RTL_OK` vectors equal the exact oracle in the real RTL with no flag; the real RTL differs from the oracle on 507 vectors,
**all** classified `RTL_UNSAFE`. Conservativeness is real: 20 vectors with an out-of-range difference but zero weights are unsafe by DIFF although the RTL happens to agree.

**Map-level certificate (general weights, not the unit-weight result).** With A = max|r_p|, B = max|r_q| over the four weights, every input with |x−w| ≤ D ≤ 2¹⁷−1 and `weight_p_nonneg(r)` (r_p ≥ 0 and r_p² ≥ 3r_q², needed because P is unsigned in the RTL) has
P ≤ (16A+24B)D² ≤ 2³²−1 and |Q| ≤ (8A+16B)D² ≤ 2³¹−1, hence no DIFF/TERM/SUM failure (gap fields remain data-dependent). It is tight, checked on the real RTL at D and D+1:
maximal D for (A,B) = (1,0): 16,383; (1,1): 9,459; (5,2): 5,461; (100,3): 1,591; (1000,0): 518; (37,21): 1,843; the real RTL is exact at D and fails at D+1 for each.
The earlier note's "|coefficient| ≤ 5,181" (D ≤ 10,362) was a crude sufficient bound for unit weights only; the exact unit-weight region is D ≤ 16,383. Two refinements of the original audit's mechanism text, both leaving its evidence intact: terms wrap only if the *final* term leaves 36 bits, and negative-valued signed weights are unsafe for a different reason (unsigned P).
Existing Iris silicon evidence (features ×1000, unit weights, |Δ| well below 16,383) lies inside the certificate.

## Portability evidence
Host gcc `-std=c99 -pedantic` at -O0/-Os/-O2/-O3 and clang `-Weverything` (only `-Wunsafe-buffer-usage` advisories on array indexing); **32-bit host (`-m32`) passes the full oracle suite**; the full suite is clean under UBSan (signed-integer-overflow, shift, bounds; 1 GiB limit) and under ASan+UBSan (run without the address-space limit, which ASan cannot honour).
Cortex-M33 compile-only (`arm-none-eabi-gcc 16.2.0`, -O0/-Os/-O2, `-Wall -Wextra -Werror -pedantic`): OK; -O2 text 1,732 B (`bmu.o`) + 856 B (`bmu_rtl.o`); undefined symbols only `memcpy`/`memset` (and `som_bmu`), no libgcc arithmetic helper.

## Static cost (analytic, from the structure and the M33 object; no timing claim — RP0b)
Per feature 7 int64 multiplies (3 in s, 4 in the weighted terms); the -O2 M33 object shows 19 multiply-class instructions per feature iteration, i.e. 76 per node. Each ordering test with mixed-sign differences costs 2 `mul_u64` = 8 UMULL, and a node needs at most 2 tests (best, runner-up): ≤ 16. So ≤ 92 multiply instructions per node, ≤ 644 per 7-node classification, plus 8 for the ambiguity test.

## Limits
The harness takes integers, not JSON maps. Label bound (< 7) and exactly-7-node maps follow `som_map.py`. The RTL checks use the ring semantics read from the RTL text and are validated on 616 sampled vectors, not proved exhaustively.
Measured timing, SRAM/XIP placement and any RP2350 execution remain RP0b (unauthorized).
