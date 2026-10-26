# Strategic Contract: Graphics-First Priority

**Date:** 2026-09-04
**Revision:** 2 — revised against a cold review that corrected two central claims
**Contract ID:** `contract_graphics_first_priority_2026-09-04.md`
**Status:** ACTIVE pending John's confirmation
**Durable copy:** https://claude.ai/code/artifact/4470f365-7770-4d1e-879a-035de715d08e
(this directory is gitignored and was lost once to `rm -rf`; the artifact is the backup)

**Roles:** Spec Author — Claude (Opus 5) · Cold reviewer — Gemini · Decision — John

---

## 1. Thread states

| Thread | State | Reason |
|---|---|---|
| Graphics / GPU | **ACTIVE** | First video output 2026-09-04, §3.8 |
| Power characterisation | **PHASE 1 RIDER** | INA226 rig built, idle since SOM shelved |
| Southbridge SPI | QUEUED | Load-bearing at Phase 2, not before |
| HDMI / DVI | **BLOCKED** | openXC7 #66, open, unimplemented |
| Tensegrity active control | **FALSIFIED** | Reachable balanced set has one element |
| SOM / INA226 | SHELVED | 2026-09-03 |
| Tang Primer 25K | PARKED | Until a functional baseboard |
| Photonics | **RULED OUT for graphics** | Structural mismatch — §6 |

---

## 2. The case for graphics-first

The only thread whose next step is short, visible and de-risked. Every other
live thread has a broken dependency: HDMI needs a placer that does not exist,
tensegrity needs a primitive just falsified, the southbridge is plumbing with
no consumer until something needs per-frame geometry.

- `spu_gpu_top.v` already exposes the VGA ports and instantiates `hal_vga`.
- **No framebuffer** — pixels stream with display timing; no DDR3 behind it.
- Depth-v2 math chain already silicon-proven (§3.7).
- Display path measured end to end: HSYNC 0.006%, VESA 96-of-800 duty exact.

### 2.1 Power — the underweighted argument

Neither the first draft nor the cold review made this case. It may be the
strongest available, because it is **measurable on your own bench this month**.

Three properties compound: no floating-point units, no division, and — the
significant one — **no external memory**. In conventional GPUs DRAM access runs
~100x the energy of an ALU op and memory traffic dominates consumption. A
renderer that never touches external memory is architecturally low-power in a
way that is not marketing.

**Measure differentially.** Absolute FPGA power is dominated by static leakage
and clock distribution. Same board, same clock — VGA test pattern vs full GPU
rendering — cancels the static term and isolates the rasterizer's real cost.
`tools/bench_metrics/`, `power_log.py` and the INA226 pipeline already exist.

**Honest counterweight.** Momentum was the stated reason SOM was shelved.
Graphics-first serves that, but a rasterized triangle is not a product and the
perceptual hypothesis remains undemonstrated. The technical case survives the
momentum argument's removal and should be stated without it.

---

## 3. Sequence

### Phase 1 — Rasterizer on the proven display path (1-2 sessions)

Wire `spu_gpu_top` to `spu_a7_vga_fix.xdc`, hardcoded triangle coefficients as
`test_gpu_top_integration.py` does, verify in simulation against the existing
oracle before loading.

**Two measurements are outputs, not afterthoughts:** LUT utilisation (this is
falsifier F3, free from the first synthesis run) and the INA226 power delta
against the VGA-only bitstream.

### Phase 2 — The exact algebraic processor, visualized (weeks)

Jitterbug stepping through exact ROTC angles, geometry provably returning to
its start via exact group elements with known finite periods.

**Framing discipline — the correction the cold review earned.** Do NOT pitch
this as "a GPU where rotating objects don't drift." Graphics engines have
re-orthogonalized quaternions every frame for thirty years; drift is a solved
non-problem there and that pitch gets a shrug. **The screen is not the product;
the screen is the oscilloscope displaying an exact algebraic processor.**

Exact closure matters where a constraint is algebraic and must hold: tensegrity
equilibrium, linkage/origami closure, long-horizon coordinate return where
float diverges without artificial re-projection.

### Phase 3 — Decide the display path (after Phase 2)

VGA or Vivado-for-HDMI, with a working renderer in hand. HDMI RTL is written,
committed and waiting; only the placer is missing. Switching toolchains
mid-bring-up trades a 95%-complete result for a 0%-complete one.

### Not scheduled — tensegrity active control

Measurement: all 24 balance-preserving rotations leave the strut geometrically
fixed. The cold review supplied a **mechanical explanation** that converges
independently — in a class-1 tensegrity the struts float in an antagonistic
24-cable network, so rotating one in isolation is kinematically overconstrained.
That is an **argument from mechanics, not a measurement**: it raises confidence
that the full 36-angle catalog would not rescue the primitive without settling
it. Viable routes: tendon actuation, or coordinated multi-strut symmetry. Each
needs its own contract.

---

## 4. FALSIFIER GATE — 90 days

Revision 1 stated no falsifier for its own central choice. Any one of these
abandons the direction.

**F1 — Framebuffer complexity cliff.** A rotating closed polyhedron (8-12
triangles with depth) cannot sustain on-the-fly raster-beam timing and forces
an off-chip DDR3 controller. *Streaming without a memory bus is the whole
architectural claim and the entire power argument. Add DDR3 and you have
rebuilt a slow 1995 graphics card.*

**F2 — Nobody has the problem.** Phase 2 recorded and shown to robotics
kinematicians, CAD kernel developers and computational geometry researchers,
and **zero** identify a concrete pain point that exact closure solves and cheap
float re-normalization does not.

**F3 — Logic resource starvation.** GPU + rasterizer exceed **35% of the
Artix-7 100T's LUTs**, preventing co-existence with the SPU-13 core, RPLU2 and
coordinate math. *Cheapest and first — falls out of Phase 1's first synthesis
run. LUCAS alone is ~20%.*

### UNRESOLVED CONFLICT

**F2 requires outreach, held since 2026-08-19 including warm contacts.** Either
that hold gets an explicit carve-out for technical validation, or F2 cannot
fire and the gate has only two working conditions. A decision, not something
the plan can paper over.

---

## 5. Cold review outcomes

| Q | Outcome |
|---|---|
| Q1 graphics-first or momentum? | **Upheld.** Only thread without a broken dependency; restated without motivational framing |
| Q2 is Phase 2 distinctive? | **Corrected.** Distinctive for constrained kinematics; uninteresting as a GPU feature. Framing rewritten |
| Q3 tensegrity too narrow? | **Sound, and now explained** by a mechanical argument. Recorded as argument, not measurement |
| Q4 real market? | **Rationalisation, accepted** — see below |
| Q5 falsifier? | **Supplied and adopted** — §4 |

**Q4 in full.** DO-254 / ASIL-D is ~95% process: traceability, FMEDA, tool
qualification, an accredited quality system. Incumbents (CoreAVI, Barco) already
serve deterministic display with certified 2D vector cores. Not enterable by a
solo project. **Replacement positioning:** open silicon / FPGA IP for
deterministic spatial computing, robotics forward kinematics and symbolic CAD
geometry kernels — which re-labels assets that already exist
(`software/lib/rational_robotics.py`, the silicon-verified ROBOTICS spin)
rather than requiring a pivot.

---

## 6. Ruled out, and why

### Photonics has no application to this GPU

Checked, not assumed: `docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md` contains
**zero** mentions of raster, pixel, graphics or render, and is explicitly
hypothetical with no silicon evidence. The mismatch is structural:

**1. Optics cannot cheaply make a step function.** Optics is physically
excellent at *linear continuous* algebra — Fourier transforms, phase
accumulation, matrix-vector products across WDM wavelengths. Rasterization is
none of those. It is a blizzard of discontinuous Boolean inequalities:
`inside iff E0>=0 AND E1>=0 AND E2>=0`, `visible iff z_interp < z_current`.
In CMOS a comparator is a few transistors snapping between rails. In optics it
needs nonlinear bistability or an O-E-O round trip — which destroys the very
latency and power advantage optics was reached for.

**2. 99.9% is catastrophic here, and the number is small.** 640x480 =
307,200 pixels, so 0.1% error is ~307 wrong pixels per frame and ~18,400 per
second at 60 Hz. In deep learning (where photonic startups actually play) a
small analog perturbation is absorbed by the next nonlinearity. In graphics it
is Z-fighting and edge sparkle, and human vision is acutely sensitive to
high-frequency temporal noise. The photonics contracts were about cascade
depth, k-noise, detector boundaries and corruption descriptors — that track was
fighting analog error throughout, which is precisely what a rasterizer cannot
tolerate.

**3. The bandwidth inversion, quantified.** Co-packaged optics exists to move
3+ TB/s between HBM stacks and compute dies. This GPU streams
640x480x60x3 bytes ~= **55 MB/s** and has no memory bus at all. That is roughly
five orders of magnitude below where photonic interconnect becomes relevant.
The design choice that makes this architecture elegant removes the only problem
photonics would solve.

**4. The smart objection, pre-empted.** Optics *is* good at matrix-vector
multiplication, and vertex transforms are exactly that — so why not photonics
for the transform stage and digital for rasterization? Because the SPU's
transforms are **exact ROTC group elements with finite periods**. An analog
optical transform cannot be exact, so it destroys the precise property Phase 2
exists to demonstrate. It would photonically accelerate the one stage whose
exactness is the entire architectural claim.

**Note.** The human sensitivity to high-frequency temporal noise in point 2 is
the same perceptual mechanism behind the shimmer observed in the earlier
compute-shader work — different cause (sampling geometry, not analog error),
same reason it is visible and irritating. Small piece of theoretical grounding
for the IVM hypothesis, arriving from an unrelated direction.

Photonics stays closed; its "needs a fresh reason" gate is not met.

### Also excluded

- **Avionics certification as a market** — Q4.
- **A Vivado install** — deferred to Phase 3 by decision.
- **Reviving SOM** — its *instrument* is reused for power measurement; the
  product thread is not.
- **The IVM perceptual hypothesis as a deliverable** — needs a controlled
  experiment with subjects, not more RTL.

---

## 7. Bench safety, ranked by loss prevented per pound

| Measure | Cost | Addresses |
|---|---|---|
| **Mechanically secure every board** | £0-5 | The mechanism that destroyed the programmer |
| **Everything on one power strip** | £0-10 | Earth-potential difference driving a ground loop |
| **Spare programmer, flashed, in a drawer** | ~£5 | Dead board becomes a five-minute swap |
| **Use `docs/BENCH_ELECTRICAL_SAFETY.md`** | £0 | The retry-after-first-anomaly pattern |
| USB isolator (ADuM3160) | ~£15 | Mains-earth loop. Full Speed suffices |
| Harness adapter board | ~£10 | Flying-lead flakiness |
| Power-ready interlock | £10-20 + build | Backfeed. A project, not a purchase |

The first four cost almost nothing and cover observed failures better than the
interlock, which addresses a class already mitigated by series resistors and
would not have prevented the most recent loss. Independently endorsed by the
cold review.

Not all of the ledger is hardware fragility: the GPU stall was a probe
artifact, the total build outage was a Boost library. Some of the kill count is
diagnosis error, which process fixes free.

## References

- `docs/hardware_evidence.md` §3.8 — bitstream `a80b6d0c…`, commit `bf00be0`
- `docs/SESSION_HANDOVER_2026-09-04.md` · `docs/BENCH_ELECTRICAL_SAFETY.md`
- `spu_strategy/contract_tensegrity_active_control_2026-09-04.md` (BLOCKED)
- openXC7/nextpnr-xilinx issue #66
