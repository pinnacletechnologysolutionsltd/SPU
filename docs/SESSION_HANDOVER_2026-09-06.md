# Session Handover — 2026-09-06

## 0. One-line state

The zero-instantiation audit from 09-05 §5 was run. It is now a committed
tool, not an afternoon's grep. It immediately paid for itself: **the depth-v2
attribute field was never anchored at (0,0)** — one full scanline of wrong
depth, every frame, in the module that reached silicon yesterday.

Running the gate twice then turned up a **second** gate defect, of the same
family as 09-05 §1: `verify_repo.sh` was never idempotent, because the suite
it runs at step 3 recreated the root `.vcd` files it prohibits at step 1 (§3).

No bench work this session. §3.9 is **still single-observation** — item 1 of
09-05 §7 is untouched and still the first thing to do at the bench.

---

## 1. The zero-instantiation audit — `tools/rtl_instantiation_audit.py`

Roots are taken from the build scripts themselves (`-top X`, `TOP=X`), so a
board top no build script names is correctly reported as unreachable. Three
classes over 426 modules:

| class | meaning | count |
|---|---|---|
| DEAD | no board top, no testbench | 54 |
| TB-ONLY | simulated, never integrated into any top | 39 |
| NO-TB | reaches silicon, never simulated | 36 |

**It is a regex parser, not an elaborator**, and the docstring says so. It
resolves by module name, ignores `` `ifdef ``, and cannot see through a
generate branch it fails to parse. A hit means "go and look". `yosys
hierarchy -check -top <top>` remains the authority for any single top; this is
the sweep across all of them, which is what no existing check did.

Validated against known ground truth before being trusted: `hal_hdmi` and
`spu_gpu_top` both resolve to their post-fix parents, and the root set was
diffed against a hand sweep. That diff caught two genuinely missing tops —
`tang25k_blinky_uart` and `tang25k_blinky_uart_div2`, whose build scripts sit
in the **repository root** (`build_25k_blinky_uart*.sh`, both tracked). Fixed
by searching `.` too. Worth noting separately that AGENTS.md §3.6 prohibits
root clutter and `verify_repo.sh` does not check for stray root `.sh` files.

---

## 2. THE FINDING: the depth field was anchored a quarter-scanline late

`spu_attr_stepper.v` accumulates exactly like `spu_edge_stepper.v` — seed on
`setup`, `+= B` per `step_y`, `+= A` per `step_x` — so it needs the same
per-frame re-anchor the coverage path got on 09-05. It could not be given the
same `setup0` pulse: its coefficients do not exist until
`spu_depth_dispatch` has run a reciprocal. So it was anchored on `ready0`.

`setup0` pulsing at (0,0) therefore made `ready0` land wherever the setup
latency happened to end.

**Measured, not reasoned:**

```
unit0 depth anchored at pixel (vx=25, vy=0)
unit1 depth anchored at pixel (vx=48, vy=0)
  -> the two units are anchored 23 pixels apart
```

The two differ because `spu_depth_dispatch` dispatches them sequentially
through one shared multiplier. `spu_attr_stepper`'s `setup` loads
`acc <= c_coef`, the depth **at (0,0)** — so each unit declared "I am at x=0"
a quarter of a scanline in, and the two units disagreed about where they were
by 23 pixels while their depths were compared against each other pixel by
pixel.

**The damage is bounded, and the bound was measured too.** `acc_row` is
re-seeded from the row wrap, so the field self-corrects from row 1 and only
row 0 is wrong:

```
depth0 vs oracle over the active area: 80/4800 pixels wrong (1 row of 60)
```

**A correction, kept rather than quietly fixed.** Commit `8c2d2cc`'s message
says the row is "off by a constant 2000 (about 11 pixels of A_z)". That was
generalised from the first six mismatches the probe happened to print, all of
which fell in one regime. Profiling the whole row afterwards shows **two**:

| x | measured error | in pixels of `A_z` |
|---|---|---|
| 0 – 23 | +2000 | ~10 |
| 24 – 79 | +4363 | ~23 |

`x=0..23` are pixels the scan had already passed before the anchor landed, so
they carry the previous frame's over-accumulated value; `x=24..79` are stepped
correctly but from an origin 24 pixels late. The count (80/4800, one full
scanline) was right; the magnitude was one regime reported as the whole row.
Same failure mode as 09-05's `1c4476c`: a reasoned number where a measured one
belonged.

**Latent, not observed — stated precisely.** §3.9 draws ONE triangle, and with
only unit 0 armed `spu_depth_compare`'s `unit0_wins` reduces to `cov0` and
never reads a depth. **Nothing on silicon was ever wrong.** It would have
appeared on the first two-triangle scene.

### The fix (`spu_gpu_top.v`)

Give the depth path the coverage path's shape rather than a compensating
offset:

- `depth_setup0/1` are now `tri0_setup`/`tri1_setup`, not `setup0`/`setup1`.
  The depth coefficients are a pure function of the triangle, so the math runs
  **once per triangle** instead of re-running a reciprocal every frame for a
  result that cannot change.
- `attr_setup0 = ready0 | (frame_start & depth_armed0)`, mirroring the
  coverage path's `armed0` gate for the same reason: a unit whose coefficients
  have never been computed must not load them.

The frame in which a triangle is first set up still anchors mid-row — the
coefficients do not exist before then — so that one frame has one wrong
scanline. Every frame after it is exact.

### Why nothing caught it — and this is the interesting part

`software/tests/test_gpu_depth_compare_integration.py` **already tested this
exact assembly with two overlapping triangles and an independent oracle.** It
passes, and it always did. Look at what it does:

```verilog
while (!(seen_ready0 && seen_ready1)) @(negedge clk);
attr_setup0 = 1; attr_setup1 = 1;    // both, together, THEN scan from (0,0)
```

The test hand-wired the **correct** sequencing. `spu_gpu_top` wired it
differently, and the test never instantiated `spu_gpu_top`. The subsystem was
proven correct in a harness that reassembled it properly, while the real top
assembled it wrongly.

That is the same disease as §5 of the 09-05 handover, one level up: not
"module never instantiated" but **"test builds its own top instead of testing
the real one"**. An integration test that constructs its own DUT proves the
parts compose, not that they *were* composed.

### The bench — `spu_gpu_top_depth_anchor_tb.v`

First testbench to read a depth value out of `spu_gpu_top`. Both units armed,
both with depth sloped in x and y, every active pixel of a steady-state frame
checked against the affine oracle.

**Negative control run, as required:**

| RTL | expected | result |
|---|---|---|
| post-fix | 0 wrong, PASS | `unit0 0 wrong, unit1 0 wrong` → PASS |
| pre-fix | 80/4800 per unit, FAIL | `unit0 80 wrong, unit1 80 wrong` → FAILED with 2 errors |

Vacuous-pass guards, because a constant depth field matches *any* anchor and
would pass on the broken RTL: all four gradients `A_z0/B_z0/A_z1/B_z1` must be
non-zero, both units must be armed, and the checked-pixel count must equal the
active area.

**Scope stated in the header so it is not overread:** the oracle is built from
the DUT's own `A_z/B_z/C_z/frac_bits`, so this proves the accumulator is
anchored and stepped consistently with the coefficients the setup stage
produced. It does **not** check that those coefficients are right.

Runs in 0.57 s. Suite: **226 PASS, 0 FAIL** (was 225).

---

## 3. SECOND GATE DEFECT: `verify_repo.sh` failed on its own side effects

Found by running the gate twice. It is not idempotent, and never was.

`verify_repo.sh` runs hygiene at step 1 and the test suite at step 3. Six
testbenches called `$dumpfile("...vcd")` **unconditionally, with a relative
path**, so they wrote into the current directory — the repository root when
`run_all_tests.py` drives them. Those are exactly the root `.vcd` dumps
AGENTS.md §3.6 prohibits and step 1 checks for.

So: step 1 passes on a clean tree, step 3 recreates the prohibited files, the
gate exits 0, and the **next** invocation fails at step 1.

Observed directly this session, not inferred:

```
gate run 1  -> exit 0
gate run 2  -> ❌ ERROR: Root directory contains temporary/scratch files:
               ./spu13_regen_tb.vcd ./autonomy_dream.vcd ./sentinel_sqr.vcd
               ./fold_trace.vcd ./precession_trace.vcd ./i2s_trace.vcd
```

**These are the same six files 09-05 §1 swept.** That sweep removed the files;
it did not remove the cause, so they came back on the first suite run. The
09-05 handover records the sweep as "RESOLVED same session" — accurate about
the files, not about the mechanism.

**Fix.** Waveform dumping is now opt-in in all six benches:

```verilog
if ($test$plusargs("dump")) begin
    $dumpfile("autonomy_dream.vcd");
    $dumpvars(0, spu4_autonomy_tb);
end
```

A regression run does not need waveforms; a developer debugging one runs
`vvp <bench>.vvp +dump`. Verified both ways on `tb_spu_i2s`: no file without
the plusarg, the same 226,384-byte file with it. It also stops the suite
writing ~16 MB per run, of which `autonomy_dream.vcd` alone is 12 MB.

**Confirmed by running the gate twice back to back after the fix** — the
control this finding demands, since one pass is exactly what the broken
version also produced:

```
GATE RUN 1 -> 226 PASS, 0 FAIL, RUN1_EXIT=0
root .vcd after run 1: (none)
GATE RUN 2 -> hygiene ✅, 226 PASS, 0 FAIL, RUN2_EXIT=0
```

**Rejected alternative:** prefixing the paths with `build/`. A `$dumpfile`
into a directory that does not exist makes `vvp` **exit 1** (measured), which
would break any of these benches run from a directory without a `build/`.

**Why this keeps happening.** Both gate defects — 09-05's missing `sys.exit`
and this one — are the gate failing to constrain the thing it names. Neither
was found by reading it. Both were found by *running* it in a way it had not
been run before: once with a failing test, once twice in a row. Running the
gate twice is now worth doing after any change to the suite.

---

## 4. Also fixed: `tools/env_openxc7.fish` had no Boost shim

`env_openxc7.sh` has a `lib/boost-<version>` `LD_LIBRARY_PATH` block for the
recorded openXC7 Boost-ABI breakage. **The fish version never had one.**
Sourcing it in fish left `LD_LIBRARY_PATH` empty, so `nextpnr-xilinx` and
`bbasm` stayed broken and every A7 bitstream build with them — in the shell
this project is actually driven from.

Verified before and after: empty → `/home/john/.local/openxc7/lib/boost-1.91`,
and `nextpnr-xilinx --version` answers. The repopulation recipe (take the
`.so` files from the OLD package in the pacman cache; symlinking the new
version does **not** work) is now a comment in the script rather than only in
someone's memory.

**A correction worth recording.** I first read a bare `ldd` as the toolchain
being broken again and installed a second shim directory. It was not broken —
the working `lib/boost-1.91` from 09-04 was there all along and my `ldd` simply
had no env sourced. Duplicate removed. The fish gap was real and separate.

---

## 5. The GPUVGA spin was rebuilt — but NOT loaded

Per `board-builds-are-never-rebuilt`, simulation-green says nothing about a
spin, so the RTL change was carried through a full rebuild.

```
build     bash hardware/boards/artix7/build_a7.sh 100t gpuvga all   (A7_FREQ=25)
bitstream build/spu_a7_100t_GPUVGA.bit
          SHA-256 5975b17d267633e9adb4d52646cbec299dc65f848d79d22fef1aa4721c398c0e
```

|  | 09-05 (`dfbefd3`) | today |
|---|---|---|
| SLICE_LUTX | 7,890 (6%) | 7,896 (6%) |
| SLICE_FFX | 2,417 (1%) | **2,419** (1%) |
| DSP48E1 | 2/240 | 2/240 |
| `clk_pixel` | 40.28 MHz | 40.73 MHz |

**+2 flip-flops is exactly `depth_armed0` and `depth_armed1`** — the cost of
the fix, confirmed rather than assumed. `clk_pixel` passes at 25 MHz required.
(Both figures are the **last** "Max frequency" line: nextpnr prints two and
the earlier pair — 32.96 MHz here — is the pre-route estimate.)

**Superseded by §8.** `x_span` was removed after this build, so the tree no
longer produces this bitstream, and §8 also establishes that the A7 `.bit`
hash is not reproducible across builds anyway. The utilisation and Fmax
comparison above still stands; treat the hash as a record of what was built at
that moment, not as something to reproduce.

**This bitstream has NOT been loaded onto hardware.** No silicon claim is made
for it and `hardware_evidence.md` is untouched. §3.9 still refers to
`dfbefd3`'s bitstream, which is the one that was actually observed on a
monitor. Loading this one and re-confirming the triangle is the natural way to
combine next session's items 1 and 2 into a single bench trip.

---

## 6. Audit findings NOT acted on — decisions for you

**`x_span` — DONE, see §8.** Was left as a decision; the call came back to
remove it, and it is removed.

**`spu_texture_dma.v`** — the only fully dead module under `rtl/gpu/`. Read it:
it is a clean SDRAM-burst template, correctly reset, not rotting code. Delete
or keep deliberately, but it should not sit in the "nobody knows" state.

**The DEAD list is mostly one story.** Of the 54, a large block is an entire
SPU-13 core generation — `spu13_top`, `spu13_sequencer`, `spu13_scoreboard`,
`spu13_cluster_controller`, `spu_core`, `spu_execution_unit`,
`spu_instruction_decoder`, `spu_register_file`, `spu_folded_alu`,
`spu_system` — reachable only through `spu_colorlight_i9_top` and
`spu_ecp5_top`, which are themselves in no build script. A dead core behind
dead boards. Vendor primitives (`SB_HFOSC`, `gowin_bsram`, `PLLA`) are
expected here and are not findings.

**TB-ONLY includes the SPU-4 core proper** — `spu4_core`, `spu4_top`,
`spu4_sentinel` are reached only by testbenches. The SPU-4 silicon in §3.2j
runs `spu4_som_edge_wrapper`, a different module. Not a defect; worth knowing
before anyone cites "SPU-4 is in silicon" as covering `spu4_core`.

**The depth-v2 subsystem has no unit bench of its own.** `spu_depth_math`,
`spu_depth_dispatch`, `spu_attr_stepper`, `spu_depth_compare` and
`spu_reciprocal_core` have no `*_tb.v`. Coverage is the Python parity tests
plus, as of today, this one. `spu_attr_stepper.v`'s own header refers to "a
real bug this module's own testbench caught" — that bench is not in the tree.

---

## 7. Next session

1. **Still item 1 from 09-05.** Re-confirm §3.9 after a deliberate reseat and
   a power cycle. Nothing this session touched the bench, and the result is
   still single-observation against a harness that needed prodding.
2. **Load the rebuilt GPUVGA spin and re-confirm.** The RTL changed and the
   spin was rebuilt (§5) but never loaded; per `board-builds-are-never-rebuilt`
   simulation-green says nothing about a spin. Fold this into the same bench
   trip as item 1.
3. **Decide the remaining §6 items** — `spu_texture_dma`, and whether the
   dead SPU-13 core generation behind the dead Colorlight/ECP5 tops is kept
   deliberately or retired. (`x_span` is done, §8.)
4. Then 09-05 §7's CRT control, unchanged and still wanting the GPU raw and
   unsmoothed.

**Not done, named so it is not lost:** the audit answers "is it reachable",
not "is it exercised". `NO-TB` (36) contains modules that reach silicon with
no simulation at all. Board tops belong there legitimately; `spu_video_pattern`
— which produced the §3.8 first-video result — does not, and still has no
bench.

---


## 8. `x_span` removed — and what the rebuild turned up

The dead port is gone from all four levels: `spu_edge_stepper` (which declared
and never read it), `spu_raster_unit` (three POSITIONAL connections, so the
port-list change had to be matched there), `spu_dual_raster`, `spu_gpu_top`,
`spu_raster_tb`, and the three Tang GPU probes. A comment in
`spu_edge_stepper` now says why no row width is needed — `f` is re-seeded from
`f_row` rather than unwound by the number of x steps — so nobody re-adds it.

With it went the wrong value it was carrying: two Tang probes passed
`10'sd640` into a 16-bit signed port, and **`10'sd640` sign-extends to −384**
(measured). Harmless only because nothing read it.

**Two tests broke, and a grep taught me something.** `grep -rn x_span
hardware/` was the wrong scope. `test_gpu_raster_oracle_rtl_parity.py` and
`test_gpu_depth_compare_integration.py` both **generate their testbench as a
Python string**, so their `.x_span(...)` connections are invisible to any
grep of the RTL tree. The gate caught them:

```
Total PASS:  224
Total FAIL:  2
❌ ERROR: test suite reported failures (run_all_tests.py exit 1).
```

That is 09-05 §1's fix doing exactly its job on its first real regression —
before that commit this would have printed a green tick. Fixed, and the two
now pass with full 640x480 exact pixel-set parity and 6,155/6,155 overlap
pixels correctly won. Final: **226 PASS, 0 FAIL**, gate exit 0.

**Verified a no-op, not assumed.** Simulation is bit-identical
(`lit=794 csum=229874`, 0 wrong depth pixels), and all **40 post-route
resource rows** are unchanged: 7,896 LUT / 2,419 FF / 2 DSP. All three Tang
GPU probes rebuild (exit 0) — they are in **no** build manifest, so nothing
was checking them.

### A7 bitstreams are not byte-reproducible

Chasing whether the hash change meant a logic change turned up something
worth recording on its own. Four builds:

| build | source | SHA-256 (first 8) | clk_pixel |
|---|---|---|---|
| pre-removal | with `x_span` | `5975b17d` | 40.73 MHz |
| post-removal | without | `2d99716e` | 38.69 MHz |
| control | **identical to post-removal** | `0cc3eaef` | 38.69 MHz |
| control 2 | **identical again** | `cc0d0f2a` | — |

Two builds from byte-identical source give different hashes. `cmp -l` on the
last pair: **exactly 3 bytes differ, at offsets 122–125**, ASCII digits in the
header — a build timestamp (`10:38` vs `10:40`). All 3.8 MB of configuration
data is identical.

So the **logic** is reproducible; the **file hash** is not. That matters
because `docs/hardware_evidence.md` records A7 bitstream SHA-256s as evidence:
those hashes identify the exact artifact that was flashed, and are correct for
that, but **they cannot be regenerated by rebuilding** — a mismatch on a
rebuild proves nothing on its own. This is why `board_build_manifest.json`
lists Gowin targets only; the comment there says A7 was excluded for chipdb
build time, which is true but not the whole reason.

The Fmax difference (40.73 → 38.69, both far above the 25 MHz required) is
reproducible across the two identical-source builds, so it is placement
ordering changing with port-list ordering, not a logic change — and the
40-row resource diff confirms that independently.

**Not chased:** whether `xc7frames2bit` can be made to emit a fixed timestamp.
If it can, A7 targets could join the build manifest and get the same
rebuild-and-compare protection the Gowin ones have. That is the real prize
here and it is not queued.


---

## 9. THE FIX IN §2 WAS INCOMPLETE — caught by the "should I flash it?" question

Asked whether the bench was ready, I went to check what
`spu_a7_gpu_vga_top.v` actually draws. Line 105:

```verilog
.tri0_setup(frame_start),
```

**The board top re-pulses setup at (0,0) of every frame.** My bench pulsed it
once. They are not equivalent, and the difference is exactly the bug:

- `depth_setup0 = tri0_setup` (§2's change) then fires every frame,
- so the dispatcher re-runs and `ready0` pulses again mid-scanline every frame,
- and `attr_setup0 = ready0 | (frame_start & depth_armed0)` re-anchors on it,
  **after** the correct frame-start anchor.

Measured on `60f3b40`'s RTL under the board's drive pattern: **55 pixels wrong
for unit 0, 32 for unit 1.** The commit that claimed to fix this shipped a
version still broken on the only top that instantiates it.

**Fix:** the `ready` term is the initial load only.

```verilog
wire attr_setup0 = (ready0 & ~depth_armed0) | (frame_start & depth_armed0);
```

`depth_armed0` is still low on the cycle its own `ready0` is high, so the first
pulse arms and anchors and every later one is suppressed. A triangle whose
coefficients change now takes effect at the next frame boundary rather than
part-way down the screen, which is also the behaviour you want.

**The bench now runs BOTH drive patterns**, and the controls discriminate:

| RTL under test | phase A (one-shot) | phase B (per-frame) |
|---|---|---|
| original, pre-fix | 80 / 80 wrong | 80 / 80 wrong |
| §2's fix, `ready` unguarded | **0 / 0 wrong** | **55 / 32 wrong** |
| current | 0 / 0 wrong | 0 / 0 wrong |

**That middle row is the whole lesson, and it is mine, not inherited.** §2 of
this very handover diagnoses "the test hand-wired the correct sequencing and
never instantiated the real top" — and then I wrote a bench that drove
`spu_gpu_top` in a way the real top does not, and shipped it. One iteration
later, same mistake, in a session whose headline finding was that mistake.

**How it was actually caught:** not by a test, not by review. By being asked
whether the thing was ready to flash, and going to read what the board top
does before answering. Reading the *consumer* is what closed it, both times.

Suite 226 PASS, 0 FAIL. Rebuilt:

```
bitstream build/spu_a7_100t_GPUVGA.bit
          SHA-256 2e972b5d40a44f88391d4c97b5f823216ab4295bee6177138f82c74fb7b3e8ed
          7,896 LUT / 2,419 FF / 2 DSP, clk_pixel 39.24 MHz against 25 required
build     bash hardware/boards/artix7/build_a7.sh 100t gpuvga all   (A7_FREQ=25)
load      openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_GPUVGA.bit
```

Resource usage is unchanged from every build today -- the guard costs no
cells, it only removes a term from an existing expression. Per §8 the hash is
not reproducible across builds; this one identifies the artifact now sitting
in `build/`.

**This bitstream still draws ONE triangle with constant depth**
(`tri1_setup(1'b0)`, `tri0_z0=z1=z2=1000`), so flashing it CANNOT exercise any
of this. It confirms no regression in the display path and nothing more. A
silicon test of the depth path needs a two-triangle scene in
`spu_a7_gpu_vga_top.v`, which does not exist yet.

---

## References

- `docs/SESSION_HANDOVER_2026-09-05.md` (previous) §5, §7
- `docs/hardware_evidence.md` §3.9 · §3.8
- `tools/rtl_instantiation_audit.py`
- `hardware/tests/common/spu_gpu_top_depth_anchor_tb.v`
- `tools/verify_repo.sh` · `tools/env_openxc7.fish`
