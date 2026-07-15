# SPU-13 Documentation Index

Date: 2026-07-05

This directory contains current source-of-truth documents, paper drafts,
hardware evidence logs, and older tactical roadmaps. Prefer updating current
documents instead of deleting historical logs; many older files preserve useful
bring-up context.

## Current Source Of Truth

| File | Purpose |
|---|---|
| `CURRENT_STATUS.md` | Short current board status, proof level, and priority list |
| `hardware_evidence.md` | Detailed silicon/RTL evidence ledger |
| `build_and_bringup_guide.md` | Commands, wiring, and board bring-up procedures |
| `fpga_board_scaling_strategy.md` | Board acquisition and scaling ladder |
| `SPU13_IDENTITY_AND_BOUNDARIES.md` | Claim boundaries and public language |

## Active Paper Drafts

| File | Purpose |
|---|---|
| `spu13_central_paper.tex` | Foundation SPU-13 architecture paper |
| `rplu_paper.tex` | RPLU v2 paper draft |
| `LUCAS_MAC_PAPER.md` / `LUCAS_MAC_PAPER.tex` | Lucas phinary MAC paper |
| `SU3_COPROCESSOR_PAPER.md` | SU3 coprocessor paper |
| `SU3_PAPER_OUTLINE.md` | SU3 paper outline |

## Current Board / Target Docs

These six now live under `docs/archive/ecp5/`, not at the docs root — paths
below are relative to `docs/`.

| File | Status |
|---|---|
| `archive/ecp5/COLORLIGHT_I9_PINOUT_VERIFIED.md` | Current i9 pinout audit; open-flow P&R passes, hardware smoke pending |
| `archive/ecp5/COLORLIGHT_I9_SETUP_SUMMARY.md` | i9 setup summary with measured RPLU2 synthesis/P&R/bitstream results |
| `archive/ecp5/colorlight_i9_feasibility.md` | i9 feasibility decision; build proof yes, hardware proof no |
| `archive/ecp5/ecp5_vs_artix7_gap_analysis.md` | Missing ECP5 southbridge/result wiring versus Artix |
| `archive/ecp5/ecp5_85k_curated_source_strategy.md` | Curated-source approach for ECP5-85F synthesis/P&R |
| `archive/ecp5/ecp5_evaluator_ee_handoff.md` | EE handoff for future custom ECP5 evaluator |
| `oshwa_application.md` | Pre-certification draft only; not ready to submit |

## Historical / Planning Docs

These are useful but not current sources of truth:

| File | Note |
|---|---|
| `strategic_roadmap.md` | Early bring-up roadmap; stale funding/board assumptions are fenced |
| `publication_and_promotion_strategy.md` | Historical publication tactics; use current index first |
| `publication_roadmap_12week.txt` | Historical tactical plan; do not quote metrics without current evidence |
| `SD_HYDRATION_AUDIT_JUNE28_2026.md` | Point-in-time SD/RP2350/Tang audit |
| `archive/tang25k/tang25k_replacement_bringup_plan.md` | Closed-regression ladder; useful for retest order |
| `rp_mcu_bringup_plan.md` | RP2040/RP2350 bring-up history |

## Update Rules

1. Keep paper, grant, and public claims aligned with `CURRENT_STATUS.md` and
   `hardware_evidence.md`.
2. Mark old tactical plans as historical instead of silently editing the record.
3. Do not claim OSHWA certification until certification is actually granted.
4. Do not quote speed, power, energy, or cost advantages without measured data.
5. When a board target changes, update `CURRENT_STATUS.md`,
   `build_and_bringup_guide.md`, and `fpga_board_scaling_strategy.md` together.
