# Session Handover — 2026-09-05

## 0. One-line state

**FIRST RASTERIZED GEOMETRY.** A red triangle, correct to within measurement
on a handheld photo, on a physical monitor — see `hardware_evidence.md` §3.9.
`spu_gpu_top` went from **never instantiated by any top on any board** to
silicon in one session. Six defects were fixed to get there, five of them in
code that had never been built or never been able to fail.

---

## 1. THE BIG ONE: the verification gate could not fail on a test

`run_all_tests.py` had **no `sys.exit` call anywhere**. It printed
`Total FAIL: 2` and returned **0**.

That one omission disarmed everything downstream:

- `tools/verify_repo.sh` runs it under `set -e`, so there was nothing to
  catch. The gate printed `✅ All verification checks completed successfully`
  on the line directly below `Total FAIL: 2`.
- `.github/workflows/ci.yml:20` invokes it directly. **CI has been green
  regardless of test failures for as long as both have existed.**

The gate AGENTS.md §2.3 designates as the Integration Auditor's automated
gatekeeper could only ever fail on an uncited silicon claim in a changed
markdown file. Nothing else could stop it.

Fixed at both ends (`e06aa58`): the runner returns 1 when `total_fail > 0`,
and `verify_repo.sh` checks the exit code explicitly rather than trusting
`set -e`, so a future regression in the runner cannot disarm the gate again.

Root hygiene also checked `tmp_*`, `scratch_*`, `*.bak` and `*~` but **not
`*.vcd`**, despite AGENTS.md §2.3 naming "root `.vcd` dumps" and the script's
own header claiming it checked waveforms. Added.

**Negative controls, all passing** — a gate fix without one is worth nothing:

| control | expected | result |
|---|---|---|
| runner with induced failure | exit 1 | 1 |
| gate with a non-zero suite | exit 1, error, no false success | 1, printed, absent |
| gate with a stray `.vcd` | exit 1, file named | 1, named |
| clean tree, tests skipped | exit 0 | 0 |

**OPEN: six `.vcd` dumps sit in the repo root** (`autonomy_dream` 12 MB,
`sentinel_sqr` 3.5 MB, `precession_trace`, `i2s_trace`, `fold_trace`,
`spu13_regen_tb`; ~16 MB). Untracked and gitignored, so nothing was committed,
but **the gate now fails until they are swept**. That is intended. They were
left in place deliberately — they are the operator's to delete.

**OPEN: what, if anything, to say publicly.** The README's fresh-clone-verified
test count was true when measured; the automation behind it was not real. No
decision taken.

---

## 2. First rasterized geometry — §3.9

`spu_a7_gpu_vga_top` swaps `spu_video_pattern` for `spu_gpu_top` and changes
nothing else about the §3.8 display path: 50 MHz / 2, no MMCM, same reset
debounce, same `hal_vga`, same three-resistor DAC, same MEASURED
`spu_a7_vga_fix.xdc` mapping. One hardcoded triangle, no host link — if the
shape appears the rasterizer works, and if it does not the fault cannot be in
a link that would otherwise need debugging simultaneously.

```
commit    dfbefd3
bitstream build/spu_a7_100t_GPUVGA.bit
          SHA-256 b6045458d149e0ad90d87dfa19c3f89b9a05dcb7613af8722d5ca82ce13e2e1e
build     bash hardware/boards/artix7/build_a7.sh 100t gpuvga all
load      openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_GPUVGA.bit
          -> Load SRAM 100%, isc_done 1, init 1, done 1
```

Post-route 7,890/126,800 SLICE_LUTX (6%), 2,417 SLICE_FFX (1%), 2/240 DSP48E1,
`clk_pixel` 40.28 MHz against 25 MHz required.

**The shape is verified, not merely present.** Measured off the photograph:
base width 55% of screen against 53% predicted, height 60% against 58%, apex
centred over the base. That establishes the edge coefficients, stepper
arithmetic and coverage test all agree with the *intended* geometry.

**Aliasing is as designed, and was predicted before it was seen.** The two
slanted edges stair-step at ~0.607 px/row; the horizontal edge (`A = 0`) is
straight. A jagged horizontal edge would have indicated a defect.

**Bench caveat.** The display was initially black and came up after prodding
the hand-wired harness. The result stands; the bench does not. A marginal lead
will eventually fail in a way that resembles an RTL bug. Not re-confirmed
after a deliberate reseat or power cycle. This promotes the harness adapter
board (~£10) in `contract_graphics_first_priority_2026-09-04.md` §7.

---

## 3. Six defects, and what they have in common

1. **`spu_gpu_top` instantiated `hal_hdmi` unconditionally** → 4 OBUFDS →
   the openXC7 placer-hang class (issue #66). The GPU could not reach the VGA
   path at all while dragging a TMDS output along. `ENABLE_HDMI` added,
   default 1 preserves Gowin/Vivado behaviour (`9c5d4e0`).
2. **`DEVICE` defaulted to `"GW5A"`**, so an A7 top that forgot it died inside
   a Gowin primitive with nothing naming the parameter. No valid default now;
   an elaboration guard names the problem (`65ec1ef`).
3. **Frame drift.** `step_y` derives from the horizontal wrap alone, firing on
   all 525 lines while only 480 are displayed, and nothing re-anchored the
   accumulators after `setup`. **Measured: `f_row` at successive frame starts
   -17520, 71730, 160980 — a constant 89250 = 525×170 step.** A triangle set
   up once left the screen almost immediately (`dfbefd3`).
4. **`spu_depth_dispatch` never reset its coefficient outputs.** On an FPGA
   they come up at 0; in simulation they are X, an X depth reaches
   `spu_depth_compare`, and every pixel goes X. **This is why `spu_gpu_top`
   had never been simulated — it could not be** (`dfbefd3`).
5. **An un-set-up raster unit covered the whole screen.** Accumulators reset
   to 0 and `inside` is `(f >= 0)`, so all three edges reported inside. Masked
   only by unit 1's colour happening to be zero (`dfbefd3`).
6. **The verification gate** — §1 above (`e06aa58`).

**What they have in common: none was found by reading the code.** Every one
surfaced from trying to *build*, *simulate* or *fail* something. Defects 3–5
were found because the fix for 3 could not be verified without fixing 4 and 5.

**A correction worth keeping.** The drift was first reported as 45·B per frame
— reasoned from the 45 blanking lines. It is **525·B**, the full frame's
accumulation, because nothing re-anchors at all. The measured figure replaced
the reasoned one. `1c4476c` carries the wrong number in its message.

---

## 4. First testbench `spu_gpu_top` has ever had

`hardware/tests/common/spu_gpu_top_frame_anchor_tb.v`. Three frames from one
setup must be identical, by lit-pixel count **and** a position-weighted
checksum so equal area in a different place is still caught.

It timed out in the suite while passing standalone: three 640×480 frames is
1.26 M cycles, ~28 s against the harness's 15 s limit. Both entries in the
hidden `Total FAIL: 2` were this one bench, counted once as a failure and once
as a timeout. Fixed by parameterising `spu_gpu_top`'s video timing
(`3c241b9`) — defaults unchanged, bench uses 80×60. Now <1 s.

**The vacuous-pass guard was load-bearing.** Without the re-anchor the
triangle leaves the screen before measurement starts, so all three frames are
identically EMPTY and would have compared equal. The bench would have PASSED
on broken RTL without its "a triangle must actually be drawn" check.

Full suite: **225 PASS, 0 FAIL**, no timeouts.

---

## 5. THE PATTERN TO CHASE NEXT

Twice in two days, both by accident, both harbouring real defects:

- `hal_hdmi.v` — never instantiated by any top on any board (2026-09-04).
- `spu_gpu_top.v` — never instantiated by any top on any board (today).

With `board-builds-are-never-rebuilt` already on record, this looks systemic
rather than coincidental: RTL written, unit-tested or untested, never
integrated, quietly rotting.

**Proposed: audit for it deliberately.** "Which modules are instantiated by
zero tops and zero testbenches?" is an afternoon's grep. Today's hit rate on
that question was three defects for one module.

---

## 6. Non-GPU work this session

- **30 INA226 SOM captures rescued** from `build/ina226_capture/captures/`,
  which `.gitignore:23` excludes — `git ls-files` returned 0. Two hours of
  hand-loaded, **unreproducible** bench work in the directory every convention
  treats as disposable. Now at `docs/bench_captures/2026-09-03-ina226-som/`
  with `SHA256SUMS` and a provenance README (`88e9819`).
- **Handover 09-04 §5 amended**: temporal voting struck as **already
  implemented** (`ina226_capture_pipeline.py:128` scores `plurality()` across
  four windows, so 60–70% `elevated_load` is the post-vote number); two
  zero-bench pre-steps added — an `--order-seed` sweep (the pipeline is
  deterministic, so repeating identical runs is a no-op; training-order
  sensitivity has never been measured) and a drift-invariance check framed as
  physics so it cannot burn the retest by tuning on held-out scores.
- **SU3 paper**: §1.3 still claimed the standalone spin read "three selected
  result elements", which §4.4 supersedes with all nine — the paper understated
  its own silicon result in the section reviewers read for claim discipline.
  Fixed, plus two TikZ figures (`237649d`). `papers-arxiv-track` memory said
  "SU3 markdown only, LaTeX conversion is the biggest open piece" — stale since
  2026-08-07. Remaining: **no DOI**.
- **Blog**: `docs/blog/first_pixels_on_glass.md`, artifact-led, first post
  since the outreach hold lifted (`34e576e`). The older
  `zero_drift_phi_arithmetic.md` has four problems — claims an arXiv paper that
  does not exist, cites `github.com/spu13` which was never real, an unsourced
  200 MHz figure, and "silicon-proven SOM classification" post-shelving.
  **Recommended: cut it.** No decision taken.

---

## 7. Next session

1. **Sweep the six root `.vcd` files.** The gate fails until they are gone.
2. **Re-confirm §3.9 after a deliberate reseat and a power cycle.** The
   marginal harness makes the result single-observation in a stronger sense
   than usual.
3. **The zero-instantiation audit** (§5). Highest expected yield.
4. **CRT control**, now with a real subject — genuine diagonal geometry with a
   predicted stair-step, rather than an axis-aligned marker that could not
   spatially alias. **Keep the GPU raw and unsmoothed until this runs**:
   coverage antialiasing would blur exactly the artifact the experiment
   exists to observe. Operator will not cut the VGA cable; the harness plug
   should already omit pins 9/12/15 by construction — verify with continuity
   rather than assuming.
5. **Then**, if wanted, analytic coverage AA. `f = Ax+By+C` is proportional to
   signed distance; `1/|(A,B)|` is constant per edge and belongs in setup,
   where `spu_reciprocal_core` already sits with ~11 ns of slack. Forces the
   R-2R ladder, so it is hardware work, not an RTL afternoon.

**Not queued, but named.** The graphics RTL contains no surd, Quadray, A₃₁ or
φ types — plain integers throughout. The exact-arithmetic thesis lives in the
papers, the Lithic programs and the software oracles, not in the rasterizer.
Today's milestone is "we have a rasterizer", not "we have a synergetic
rasterizer". The distinctive machine is still ahead.

## References

- `docs/hardware_evidence.md` §3.9 · §3.8
- `docs/SESSION_HANDOVER_2026-09-04.md` (previous)
- `docs/bench_captures/2026-09-05_first_triangle_gpu_vga.jpeg`
- `spu_strategy/contract_graphics_first_priority_2026-09-04.md` §7
