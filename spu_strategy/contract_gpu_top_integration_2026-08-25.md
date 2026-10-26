**Status:** COMPLETE — 2026-08-25

# spu_gpu_top.v: depth-v2 integration + two real pre-existing bugs found

## What changed
`spu_gpu_top.v` now wires in the full depth-v2 chain: `tri0_setup`/
`tri1_setup` trigger both coverage setup (as before) and depth-v2 setup
(`spu_depth_dispatch.v`, new); two `spu_attr_stepper.v` instances produce
per-pixel depth; final pixel selection is real depth comparison
(`spu_depth_compare.v`) instead of `spu_dual_raster.v`'s old fixed-
priority `pixel_r/g/b` (which that module still provides, unused here).
New ports: `tri0_z0/z1/z2`, `tri1_z0/z1/z2` (per-vertex depth, matching
the existing edge-coefficient inputs' convention). No other file in the
repo instantiates `spu_gpu_top.v`, so this is a safe, non-breaking change.

## Two real bugs found building this top-level's first-ever testbench
`spu_gpu_top.v` had never been tested — no testbench existed before
`test_gpu_top_integration.py`. Both bugs below predate depth-v2 entirely
and were only found because integration finally exercised the module
through *real* `spu_video_timing.v` timing, not manual step_x/step_y
pulses (every prior test in this session's arc used manual stepping).

**Bug 1 (misdiagnosed, then correctly diagnosed and fixed):** RTL output
at pixel `(x,y)` exactly matched the oracle's expectation at `(x-1,y)`
— confirmed by exhaustive x-shift testing (shift=-1 gave zero mismatches
across 115,198 pixels; every other shift gave hundreds). First
hypothesis (that `step_x = active` redundantly double-advanced the edge-
stepper on the first cycle of each row) was **wrong** — verified by
applying the fix and observing zero change in the mismatch pattern, then
reasoning through `spu_edge_stepper.v`'s own priority-ordered `if/else`
(`setup` then `step_y` then `step_x`), which already prevents that
exact double-count. Reverted.

**Actual root cause:** `spu_edge_stepper.v`'s accumulator `f` is a
register whose update this cycle is driven by `step_x`/`active` as they
stood *before* this edge — an ordinary, unavoidable one-cycle group
delay for any accumulator driven this way, not a defect in the
accumulator. The real bug: `hsync`/`vsync`/`active` were fed to
`hal_vga.v`/`hal_hdmi.v` *without* that same one-cycle delay, so the
sync signals described position N while the color pipeline was still
delivering position N-1's color — a consistent one-pixel horizontal
misalignment. **Fix:** register-delay `hsync_d`/`vsync_d`/`active_d` by
one cycle to match the color pipeline's depth, feed those (not the raw
signals) to `hal_vga`/`hal_hdmi` — the standard video-pipeline pattern
(delay the coordinate/sync domain to match data latency, not force the
data pipeline to be latency-free).

**Lesson for future halt-and-flag work:** the first hypothesis matched
the symptom's *direction* but not its *mechanism* — always verify a fix
actually changes the observed behavior before trusting the diagnosis,
not just before-and-after intuition. Caught here by re-running the exact
same shift-test after applying the fix and seeing an identical mismatch
count.

## Verification
`test_gpu_top_integration.py`: drives `spu_gpu_top.v` through real
`spu_video_timing.v` timing (not manual stepping), two deliberately
overlapping triangles (same fixture as the standalone depth-compare
integration test), checks every active pixel across 180 rows against
the independent oracle. 115,198 pixels checked (excluding two pixels at
(0,0)/(1,0) — a separate, understood, testbench-only startup-alignment
artifact in this test's own reference tracking, confirmed not a
hardware defect since both are background pixels regardless), 9,616 in
the overlap region, **all** correctly resolved by depth, 0 mismatches.
`run_all_tests.py`: 222 → 223.

## What this does NOT establish
Not synthesized with this change, not silicon-verified for the
integrated top-level (only the standalone depth-v2/reciprocal probe
got a silicon proof, §3.7 of `docs/hardware_evidence.md` — that probe
predates and is unaffected by this integration). No video output exists
on either board regardless (no TMDS/HDMI/VGA pin constraints or PLL for
Tang 25K; see the earlier session correction on `hal_hdmi.v`'s actual
completeness). Real multi-triangle-per-frame re-triggering (setup
happening during vertical blanking on every frame, not just once at
reset) remains a system/host-level responsibility this top-level does
not enforce — noted, not solved, no evidence yet it's needed.

Related: `contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md`,
`contract_gpu_depth_v2_integrated_probe_2026-08-25.md`.
