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

1. ~~Re-confirm §3.9 after a reseat and power cycle~~ — **DONE**, §3.10 second
   observation. Both loads came up without prodding.
2. ~~Load the rebuilt GPUVGA spin~~ — **DONE**, §3.10.
2b. **Tensegrity Option A in Python (§11).** The named next work: enumerate
   coordinated group rotations against the existing exact oracle, gated on
   "genuinely new geometry", not on the guard's verdict. Zero RTL, zero bench.
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

## 10. Two-triangle depth scene — built, verified in simulation, then FLASHED

`spu_a7_gpu_vga_top.v` now drives two overlapping triangles resolved by
per-pixel depth, replacing the single flat-depth triangle. This is what makes
a bench trip test the depth path at all: the previous spin had
`tri1_setup(1'b0)` and `z0=z1=z2=1000`, so `unit0_wins` reduced to `cov0` and
no depth value was ever read.

Both triangles share the top edge y=0 from x=40 to x=600, so **both cover
scanline 0** — deliberate, because the defect in §2/§9 was row-0-only and a
scene that does not reach row 0 cannot show that class of fault on a monitor.

**THE PREDICTION:** a vertical colour boundary at **x = 320**, the exact
horizontal centre of the screen, from the top edge down to y ≈ 268 where the
triangles separate. Nothing in the geometry puts an edge there — it exists
only because depth is being compared per pixel. A boundary anywhere else is a
depth fault, not a coverage fault.

**Verified before building.** The frame was rendered out of `spu_gpu_top` in
simulation at full 640x480 and compared against an independent Python oracle
built from the geometry: **0 mismatches over 307,200 pixels**, boundary at
x=320 on every overlap row, red 91,525 px / green 91,256 px. The reference
image and what to look for are in
`docs/bench_captures/2026-09-06_predicted_two_triangle_scene.{png,md}` — a
render, explicitly not a photograph.

**A trap found and avoided in the process.** The first render mismatched by 2
pixels, both on row 0. Not the RTL: my bench REGISTERED the setup pulse
(`t0 <= ...`) while the board top drives it combinationally
(`wire frame_start = ...`), which delays setup by a cycle and shifts scanline
0 right by one pixel. Third instance today of the same mistake — a bench that
does not drive the DUT the way the real top does. Fixed, then 0 mismatches.

```
bitstream build/spu_a7_100t_GPUVGA.bit
          SHA-256 ce5bdc70753fc88d1a6e91bc1e573dff2c40756f66e9d689f9880139285e25e2
          7,896 LUT / 2,419 FF / 2 DSP, clk_pixel 41.36 MHz against 25 required
build     bash hardware/boards/artix7/build_a7.sh 100t gpuvga all   (A7_FREQ=25)
load      openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_GPUVGA.bit
```

Utilisation is **identical** to the one-triangle spin, which looked wrong
until checked: `u_attr0` and `u_attr1` are both present as instances in the
netlist, so both units were always synthesised and only the constants feeding
them changed. Not a stale build — the yosys log shows it read the edited top.

**LOADED AND MEASURED — see `hardware_evidence.md` §3.10**, written the same
day. Two observations, the second across a confirmed power cycle and a harness
reseat: boundary at 0.5062 and 0.4986 of lit width against 0.5000 predicted,
and scanline 0 displaced 0.46 px where an unfixed anchor would have displaced
it ~24 px. Suite 226 PASS, 0 FAIL, gate exit 0.

---

## 11. NEXT WORK: tensegrity, refactored — what to test and what not to trust

Prompted by an external analysis reviewed 2026-09-06. Its tensegrity section
was **checked against the contract and is accurate**; its graphics section
repeats errors this project has already corrected twice. Both are recorded,
because the mix is the point: the same document can be right where it reasons
from a source and wrong where it reasons from enthusiasm.

### What is actually established

`spu_strategy/contract_tensegrity_active_control_2026-09-04.md` FALSIFIED the
single-strut octahedral-rotation primitive. Verified line by line today:

| Outcome of all 144 single rotations from the balanced canonical state | Count |
|---|---:|
| Balanced results | 24 / 144 |
| — identical geometry AND identical node labels | **24** |
| — genuinely new geometry | **0** |

All 24 are the `C₄` stabiliser of each strut's own axis: they map the strut
onto itself pointwise and do not move the structure. The naive gate answer was
"120/120 recoverable, VIABLE"; the real answer is **recovery by not moving**,
and a controller whose reachable set is one point performs no control. §7 HALT
applies, no RTL. The guard itself (`spu13_tensegrity_guard.v`) is sound and
has silicon evidence at §3.2l — nothing about it was refuted.

### The proposed refactor, and the trap it must clear

**Option A — coordinated multi-strut group rotation ("Jitterbug mode").**
Actuate the three orthogonal strut pairs together in symmetric opposition
rather than one strut alone. The claim is that cable lengths stay uniform, the
force densities stay balanced, and the structure moves through a continuum of
valid shapes; and that `spu13_tensegrity_guard.v` evaluates such a proposal
unchanged, since the guard only ever sees a node table.

The guard claim is plausible and cheap to confirm. **The physics claim is
asserted, not tested** — and it is the same shape as "100% recovery, VIABLE"
was on 09-04, one day before it turned out to mean nothing.

Two things to know before spending time on it:

1. **Jitterbug is not implemented anywhere in this repo.** It appears in docs
   and in `hardware/rp2040/rp2040_visualiser.c`. There is no RTL and no
   software model. It is a concept here, not a verified mechanism.
2. **The gate must be "genuinely new geometry", not "balanced".** The
   falsified primitive returned `ST_BALANCED` twenty-four times. Any Option A
   test that stops at the guard's verdict will reproduce exactly the 09-04
   mistake. The comparison must be against the canonical node table, checking
   for *displacement*, with relabeling handled explicitly — the 09-04 sweep
   separated "identical geometry, relabeled endpoints" from "genuinely new"
   and found 0 of the latter. Keep that column.

**The tooling already exists.** `software/lib/tensegrity_balancer.py` is an
exact oracle — rational arithmetic, Q(√3) sign checks, Z[φ] coordinates, no
floating point — and `software/tests/test_tensegrity_balancer.py` drives it.
This is a Python afternoon, zero RTL, zero bench time.

**Option B — tendon / cable rest-length control.** Physically what real
tensegrity robots do (NASA SuperBall). Needs a non-uniform self-stress solver,
because asymmetric cable pulling produces varying force densities that the
current type-uniform guard cannot express. Strictly more machinery than
Option A. Not next.

**Option C — keep TGR1 as a safety admission guard.** This is not a refactor;
it is what the guard already is, and it already has silicon evidence (§3.2l).
Worth stating plainly so it is not re-derived as a discovery.

### RESULT — Option A FALSIFIED on the octahedral catalogue

Run: `python3 software/tools/tensegrity_group_rotation_sweep.py`.

Each strut is rotated about **its own midpoint** — not a global rotation of
the structure, which is what makes new geometry possible at all. Four schemes:
the same rotation applied to all six struts, and three "symmetric opposition"
variants (R to one orthogonal pair, R⁻¹ to another, identity to the third).

| scheme | balanced | genuinely new geometry |
|---|---:|---:|
| all | 1 / 24 | **0** |
| opposed, hold pair 0 | 1 / 24 | **0** |
| opposed, hold pair 1 | 1 / 24 | **0** |
| opposed, hold pair 2 | 1 / 24 | **0** |

The single balanced case is the identity, in every scheme.

**Two controls, because without them the negative is worth nothing:**

- **Every rotation preserves every strut's quadrance.** A broken rotation
  would fail all 24 candidates and produce exactly the same "0 new geometry"
  answer as a genuine falsification. This is the control that separates them.
- **The fault distribution is real**: 16 `STRUT_INTERSECTION`,
  7 `NOT_IN_EQUILIBRIUM`, 1 `BALANCED` — not one degenerate mode.

### The scope limit is the more useful half

What is falsified is coordinated group rotation drawn from the **24 discrete
octahedral rotations** — the subset the 09-04 contract identified as
"unambiguously representable in the RTL's integer `Z[φ]` ABI".

**The Fuller Jitterbug is a *continuous* motion**, and its intermediate states
are generally not representable in that ABI at all. So this result does **not**
say the Jitterbug mechanism is wrong. It says the exact catalogue the hardware
can express does not contain it.

That is a statement about the **representation**, not the mechanics, and it
reframes the question: the obstacle to tensegrity active control here may be
the ABI rather than the physics. Whether a richer exact catalogue — finer
rotations still closed over `Z[φ]`, or a different actuation primitive
entirely — contains a reachable balanced set is **open and untested**.

**Still no RTL, and none justified.** §7 HALT continues to apply.

### Corrections to the same analysis, recorded because they recur

Its graphics section repeats the three errors 09-05 §8 already logged as
having come from an external adviser more than once:

| claim | reality |
|---|---|
| "60 FPS streaming to display beam" | the triangle is **static**; the panel refreshes at 60 Hz, nothing animates |
| "render **3D** polygons in real-time hardware" | nothing 3D anywhere — §3.10 records no 3D, no projection, no transform; coefficients are hand-written 2D constants |
| "Padé rational inversion in 114c" | misattributed. ~114 cycles is the **A₃₁[i] inverter for SU(3)** (`SU3_EXTENSION_PLAN.md`), an estimate, not a silicon measurement, and unrelated to Padé |

**And one correction that went the other way.** 09-05 §8 listed "there is no
spliced VGA cable" among the outreach corrections. The operator confirms on
2026-09-06 that **a VGA cable was in fact spliced** for the LCD harness. That
line is now corrected in place in the 09-05 handover. The narrower claim it
was reaching for is true and still holds: **the CRT cable will not be cut.**
A list of corrections is worth less than nothing if it is not itself checked
with the operator — which is how this one survived three weeks.

What it gets right: framebuffer-less streaming with no VRAM bandwidth; depth-v2
silicon-verified (true as of §3.10, today); SU(3) over the degree-8 A₃₁[i]
extension.

Its closing suggestion — "get rotating Quadray/Jitterbug geometry driving the
monitor" — skips a **transform pipeline, a projection stage and a host link**,
none of which exist. Today's scene is `localparam` constants; changing it means
resynthesis. That is the real wall, and it is the same one §10 names: two
triangles proved depth, a third proves nothing, and the next actual capability
is getting geometry in at runtime.

---

## 12. DECIDED: the GPU is a native IVM rasterizer, not a GPU with Quadray inputs

Operator decision, 2026-09-06, taken at the end of the session and recorded
here as the first thing to read tomorrow. **Everything in Quadray coordinates,
everything in Wildberger quadrance. Rasterize natively on the IVM lattice.**
Per the operator this was always the plan in the original repository, and the
documentation supports that.

**TWO OUTPUT PATHS, not one pipeline with a mandatory conversion:**

1. **Native 60° output** — the first-class path. The lattice is the output,
   not an internal representation that must be converted away.
2. **A Bresenham converter for conventional displays** — a *compatibility
   adapter*, not a pipeline stage.

That distinction matters architecturally. A mandatory resample would make the
IVM lattice an internal detail; a compatibility adapter makes it the actual
output and the square grid the special case. It also means §3.10's
framebuffer-less streaming property may survive on the native path even if
the adapter needs buffering.

### Why this is not a new direction

`knowledge/MATHEMATICAL_FOUNDATIONS.md` §3 — *"Why Q(√3) is the Required
Field"* — states it outright:

> The IVM lattice has 60° angles. The hexagonal cross-sections of this lattice
> involve cos(60°) = 1/2 and sin(60°) = √3/2. Therefore, any algebraic
> computation in the IVM will encounter √3.

**Q(√3) exists in this project *because of* IVM rasterization.** The arithmetic
foundation was derived for exactly this and has been waiting for a consumer.
09-05 §7's observation — that the graphics RTL contains no surd, Quadray, A₃₁
or φ types and that "the distinctive machine is still ahead" — describes the
gap this decision closes.

### The architectural fact that shapes the pipeline

`knowledge/RATIONAL_CURVES_SPEC.md`: **"In the IVM lattice, quadrances are
exact integers."** For a right spread, `Q₃ = Q₁ + Q₂` — Pythagoras without a
square root.

That gives a clean split, and it is the opposite of what one might assume:

| stage | arithmetic |
|---|---|
| **IVM rasterizer core** | **exact integers.** Quadrances are integral in the lattice, so edge functions, coverage and depth need no surds at all |
| **Bresenham adapter to a square grid** | **Q(√3).** The 60° → 90° basis change is where √3 appears, and where the surd hardware earns its place |

So the surd ALU belongs at the **output boundary**, not in the hot path — and
the hot path gets *simpler*, not harder, by moving to IVM. That is worth
verifying before it is relied on, but if it holds it inverts the usual
expectation that exact arithmetic costs performance.

### What this changes in the tranche

- **T3 is not "hardware triangle setup" as the contract describes it.** Setup
  in a 4-axis basis with integer quadrances is a different module from the
  `A = yj-yi, B = -(xj-xi)` screen-space computation currently specified.
  The contract needs revising before T3, and probably before T2.
- **T1's command format should speak Quadray from day one.** It is the next
  piece of work and the cheapest possible moment to decide its vocabulary. A
  loader that speaks screen-space triangles would have to be redone.
- **A Bresenham adapter joins the design** as a compatibility block feeding
  `hal_vga`. It does not exist and is not in the contract. The native path
  needs its own output definition, which also does not exist.
- **`spu_quadrance_accum.v` gains a consumer.** The zero-instantiation audit
  (§1) found it DEAD — no top, no testbench. This decision is what it was
  written for.

### The native path is a bet on displays catching up — and it has literature

Operator, same session: *"of course we're waiting for display technologies to
catch up with hexagonal grids."* Recorded as the strategic position it is,
because it is defensible rather than wistful.

**The hexagonal lattice is the optimal 2D sampling lattice.** For an
isotropically band-limited signal the hexagonal sampling density is √3/2 ≈
0.866 of the square-grid density — **13.4% fewer samples for the same
reconstruction quality**. This is standard multidimensional sampling theory
(Petersen & Middleton, 1962), not an SPU claim: the hexagonal lattice is the
densest circle packing, so it covers a circular band-limit with the fewest
points. **Square pixel grids are a convenience of manufacture, not an
optimum.**

So the position is not "we prefer triangles". It is that the display industry
standardised on a provably suboptimal lattice for manufacturing reasons, the
arithmetic to work natively in the optimal one already exists here in
`Q(√3)`, and the Bresenham adapter is what pays the conversion tax **for as
long as the displays require it**.

That reframes the CRT point above: the CRT is not a nostalgia exercise, it is
the one display available today whose sample positions are set by timing
rather than by a fixed matrix.

**Not claimed:** that 13.4% fewer samples translates into any measured
advantage in this design. It is the theoretical basis for the direction, and
nothing here has been measured.

### What is NOT yet decided, and should be taken rested

1. **The lattice-to-pixel mapping itself.** Rendering on a 60° lattice and
   resampling to a 90° grid is the entire novel content, and nothing here
   specifies it. Nearest-lattice-site, area-weighted, or something exact in
   Q(√3) are all open.
2. **Whether the resample is where antialiasing lives.** It may subsume the
   analytic-coverage AA in 09-05 §7 item 4 entirely, which would make that
   item moot rather than deferred.
3. **THE CRT MAY BE THE NATIVE 60° DISPLAY — worth checking early.**
   An LCD has a fixed square pixel matrix and physically cannot present a
   triangular lattice. A CRT has no pixel grid at all: it is a continuous
   phosphor surface scanned by a beam, and the sample positions along each
   line are set by analog timing. **Staggering alternate scanlines by half a
   sample pitch yields a triangular lattice on a CRT and is impossible on an
   LCD.**

   If that holds, the CRT is not a side quest and not merely an
   aliasing-observation rig — **it is the only display in the building that
   can show the native output**, and the Bresenham adapter exists precisely
   for everything that is not a CRT. That would also make the queued CRT
   experiment the test of the 60°-vs-90° hypothesis recorded in
   `ivm-perceptual-motivation` (exact maths still shimmered on a Bresenham
   grid; IVM viewing produced a magic-eye pop-out), rather than a
   stair-stepping check.

   **This is an inference from how CRTs work, not an established result.** It
   needs the half-pitch stagger demonstrated before anything is built on it.
   It is cheap to test: it is a timing change, not new hardware.
4. **Whether §3.10's streaming, framebuffer-less property survives.** An IVM
   rasterizer plus a resample stage may need a buffer between them. If so the
   "no framebuffer" claim changes, and T2's BRAM budget was computed for a
   square 320x240 grid — a triangular lattice of equivalent coverage is a
   different count.

**Nothing here is built and nothing is claimed.** §3.10 and §3.11 remain the
last silicon results.

---

## References

- `docs/SESSION_HANDOVER_2026-09-05.md` (previous) §5, §7
- `docs/hardware_evidence.md` §3.9 · §3.8
- `tools/rtl_instantiation_audit.py`
- `hardware/tests/common/spu_gpu_top_depth_anchor_tb.v`
- `tools/verify_repo.sh` · `tools/env_openxc7.fish`
