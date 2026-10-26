**Roles:** Claude (single-pass — no new arithmetic beyond one multiplier
and a free-running counter/accumulator; same scope class as the raster
synth probe, not the halted depth-v2/reciprocal RTL)

---

# Engineering Contract: Shared-Multiplier Isolation Probe (Tang 25K)
**Date:** 2026-08-25
**Contract ID:** `contract_gpu_mult42_isolation_probe_2026-08-25.md`
**Status:** COMPLETE — measured 2026-08-25. **STOP CONDITION TRIGGERED.**

## RESULT
`bash build_25k_spu13_mult42_probe.sh` — completed clean (`Program
finished normally`), but the number itself halts the two-instance
design from `contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md` §2:

| Resource | Used | Total | % |
|---|---|---|---|
| LUT4 | **11,259** | 23,040 | **48.9%** |
| ALU | 134 | 17,280 | 0.8% |
| DFF | 179 | 23,040 | 0.8% |
| MULTALU27X18 / MULTADDALU12X12 (DSP) | 0 | 28 each | 0% |

Max frequency (final line): **47.95 MHz** — still passes the 12 MHz test
constraint by a wide margin, but notably lower than the coverage path's
109.82 MHz, confirming a long combinational critical path through the
multiplier tree, consistent with the router taking noticeably longer to
converge than the raster probe did.

**A single 42×42 signed multiplier alone is ~8.5× the size of the
entire existing rasterizer coverage path (1,317 LUT4).** Zero DSP used,
as the earlier pattern predicted (this toolchain isn't inferring
`MULTALU27X18`/`MULTADDALU12X12` for a plain `*` here either).

**Stop condition from §4 is triggered:** raster (1,317) + **two**
42×42 multiplier instances (2 × 11,259 = 22,518) = 23,835 LUT4 —
**exceeds the entire 23,040 LUT4 budget before any FSM control logic,
accumulators, or the second rasterizer unit's share are even counted.**
The architecture contract's §2 "two independent instances, simpler than
arbitrating one" decision is now shown wrong by measurement, not
superseded by preference — see the correction in that contract.

**One shared instance is tighter but plausible:** raster (1,317) + one
42×42 multiplier (11,259) = 12,576 LUT4 = 54.6%, leaving **10,464 LUT4
(45.4%) for FSM control, accumulators, and the reciprocal's LUT ROM** —
real headroom, but no longer the comfortable "94.3% free" picture the
raster probe alone suggested.

## 0. Why this exists
`contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md` §6 named
the one untested risk left before authorizing `spu_reciprocal_core.v`/
`spu_depth_setup.v`/`spu_attr_stepper.v`: the raster coverage-path probe
used zero multiplies (pure incremental add), so it says nothing about
whether a single wide combinational multiplier synthesizes reasonably
on this exact Tang 25K/nextpnr-himbaechel flow — the flow that produced
`series_stream_probe`'s proven 305% blowup from one combinational M31
multiplier. This probe isolates that one question.

## 1. What's being measured
The architecture contract's §2/§4 propose a **single shared 42×42
signed multiplier**, uniform-width for simplicity (both operands
sign-extended to 42 bits regardless of the narrower dot-product/NR
operands), reused serially across ~14 FSM states. This probe
instantiates exactly that: one 42×42 signed multiply, combinational,
feeding a registered accumulator every cycle — the same shape one FSM
state (`M_SCALE_A` etc.) would need.

## 2. Files
- `hardware/boards/tang_primer_25k/spu13_tang25k_mult42_probe.v` — two
  free-running, non-constant 42-bit operands (so Yosys can't
  constant-fold the multiply away), one combinational `*`, registered
  accumulator, folded into `led[2:0]` every cycle (same anti-
  optimization pattern as the raster probe).
- `hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_mult42_probe.ys`
- `build_25k_spu13_mult42_probe.sh`

## 3. Verification
```bash
bash build_25k_spu13_mult42_probe.sh
```
Report LUT4/ALU/DFF and, critically, `MULTALU27X18`/`MULTADDALU12X12`
(DSP) usage against the 23,040 LUT4 / 28-each-DSP Tang 25K totals
(`docs/hardware_evidence.md` §3.6g), and whether it routes clean or
congests. Synthesis/PNR only — no flash, no silicon claim.

## 4. Stop Conditions
- If this single multiplier alone costs a large fraction of the 21,723
  LUT4 headroom the raster probe measured, HALT and flag before writing
  any of the three depth-v2/reciprocal modules — narrower per-operation
  multiplier widths (revisit the architecture contract §1's uniform-42
  simplification) or an A7 100T target become the live options, not a
  Tang 25K implementation as currently shaped.
- This result feeds directly back into
  `contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md` §6/§7 —
  update it with the real number, don't leave two contracts
  disagreeing about whether the risk is still open.
