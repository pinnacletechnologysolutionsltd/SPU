# Engineering Contract: GPU Pipeline Tranche

**Date:** 2026-09-06
**Contract ID:** `contract_gpu_pipeline_tranche_2026-09-06.md`
**Status:** DRAFT rev 5 — 2026-09-06. §0a RATIFIED. Three review rounds plus
a Gemini audit; **twelve findings, all accepted, zero rejected.** HALT stands
until rev 5's changes are themselves reviewed — the dual-port revert, the
parallel colour clear, T1's clocking and the free-running `frame_start` are
all new and unchecked by anyone but me.

## Revision history

**rev 5, 2026-09-06 — Gemini audit. Strongest round; two findings neither I
nor the prior reviewer caught, and one that REVERSES rev 3/4.**

1. **The single-port `READ_FIRST` Z policy is physically impossible at
   1 px/clk.** One address bus: reading A1 at cycle *k* forces the bus back to
   A1 at *k+1* to write it, so A2 cannot be read before *k+2* — ≥2
   clocks/pixel, capping fill at 10.4 screens/frame against a contract
   asserting 20.9. `READ_FIRST` does not help, since `WE` cannot be asserted
   before the compare resolves. **Verified independently, then accepted.**
   Reverted to true dual-port with a D-stage interlock. *The prior reviewer's
   collision hazard was real; their proposed remedy was not.*
2. **The colour framebuffer was never cleared.** Rev 4 cleared Z only.
   Background used to be combinational in the streaming design and must now be
   written; without it, uncovered pixels show frame N-1. Rev 4's own gate
   would have failed on first run. Fixed by one counter sweeping both
   memories in parallel — same 76,800 cycles, no extra latency.
3. **T1 would have accidentally created a CDC** by clocking the UART from
   `sys_clk` while the rasterizer ran on `clk_pixel`; `clk_raster` does not
   exist until T2. T1 now mandates `clk_pixel` for both.
4. **`frame_start` conflated with `swap_ack`** — an idle GPU raises no
   `swap_req`, so a commit gated on `swap_ack` would never activate. Separated.
5. Signedness independently corroborated (already fixed at rev 4), and the
   20.9 figure independently reproduced — but clarified as **pixel evaluation
   capacity**, not visible fill.

**rev 4, 2026-09-06 — third review round.** Three findings, all accepted and
all correctness-class. (1) The far-plane clear was **not type-safe**: the
existing pipeline is signed end to end and genuinely produces negative depths,
so `16'hFFFF` would have been `-1` — nearer than everything — and the
Z-buffer would have rejected every fragment. Fixed by making Z **unsigned**
normatively, and by requiring the signed-56 → unsigned-16 conversion (scale,
bias, clamp both ends) to be specified before RTL, which rev 3 had not noticed
was undefined at all. (2) The clear/swap transition is now an **explicit
atomic state machine**; "gated on swap_ack" permitted interleaving triangle
writes with the clear. (3) **Pending-commit** behaviour defined as
back-pressure. The reviewer independently reproduced the 20.875 ≈ 20.9
screens/frame figure and confirmed all four rev-3 checks.

**rev 3, 2026-09-06 — second review round.** §0a ratified by the operator.
Three further findings, all accepted: the Z-buffer had **no defined frame
lifecycle** (rev 2 would have rendered frame N+1 against frame N's depths);
the proposed cross-port Z read/write is a **RAMB36 collision with undefined
read data**; and §3a invented a "UART bit clock" domain that does not exist.
Fixed in §0b, T2's collision policy, and §3a respectively. The CRT sequencing
concern (§9b item 6) was confirmed by the reviewer and is now a precondition
on T2, not a note.

**rev 2, 2026-09-06 — external review, three P0 findings, all accepted.**
The review found three architectural blockers not in rev 1's §9. All three
are valid. Two of them (framebuffer write granularity, depth persistence)
**invalidated rev 1's chosen configuration outright** — 640x480 6 bpp
double-buffered does not fit once depth persistence is budgeted, and its
packed layout could not accept one arbitrary pixel per clock. The
configuration in §0a replaces it. The reviewer's requested narrowing of the
"unbounded triangle count" claim is adopted verbatim. Rev 1 is superseded,
not amended; the errors are recorded in §9a rather than deleted.

**Roles:**
- **Spec Author:** Claude (this document)
- **Halt-and-Flag Implementer:** unassigned per tranche
- **Integration Auditor:** `bash tools/verify_repo.sh` + operator

---

## 0. Where this starts from

As of `hardware_evidence.md` §3.10 the GPU is: two hardcoded triangles,
resolved by per-pixel depth, streamed synchronously to the display beam with
**no framebuffer of any kind**. Verified on silicon, twice, across a power
cycle. Resource use is **7,896/126,800 LUT (6%), 2,419 FF (1%), 2/240 DSP,
0/135 BRAM**.

It is a rasterizer, not a GPU. The gap is enumerated in §2.

**Operator decisions, 2026-09-06:**

1. **Perspective projection**, not affine-only. Division is confined to
   setup time via `spu_reciprocal_core`.
2. ~~6 bits per pixel, 640x480, double-buffered.~~ **SUPERSEDED at rev 2 —
   it does not fit.** See §0a.

## 0a. REVISED CONFIGURATION — requires operator ratification

Rev 1 specified 640x480 at 6 bpp double-buffered, 100/135 BRAM. Review found
two independent reasons that cannot stand:

- **It has no depth storage.** A serial rasterizer needs the depth already
  written at a pixel by earlier triangles. A 16-bit Z-buffer at 640x480 is
  **134 blocks on its own**; with the colour buffers that is 234/135 = 173%.
- **Its packed layout cannot take one arbitrary pixel per clock.** Six 6-bit
  pixels share a 36-bit word, so a single-pixel write is read-modify-write.
  Dual-port BRAM does not fix write granularity.

**RAMB36 native port widths are 1, 2, 4, 9, 18, 36. Six and twelve are not
among them.** Storing one pixel per word at a native width eliminates
read-modify-write completely, at the cost of wasted bits. Budget:

```
config                            colour            Z          total   fits
640x480  6bpp x2 +  8-bit Z    9b x2 = 150    9b =  75          225    NO  167%
320x240  6bpp x2 + 16-bit Z    9b x2 =  38   18b =  38           76   YES   56%
320x240 12bpp x2 + 16-bit Z   18b x2 =  76   18b =  38          114   YES   84%
400x300 12bpp x2 + 16-bit Z   18b x2 = 118   18b =  59          177    NO  131%
```

**PROPOSED: 320x240, 12 bpp (4 bits/channel) double-buffered, 16-bit Z-buffer.
114 of 135 BRAM36 (84%), 21 blocks spare.**

Why this is better than what it replaces, not merely smaller:

- **No read-modify-write anywhere.** One pixel per 18-bit word, native width.
  P0-1 is dissolved rather than mitigated.
- **A real Z-buffer**, so depth persistence across serially-processed
  triangles is actually provided rather than assumed. P0-2 resolved.
- **4 bits per channel, not 2** — which is what the R-2R ladder in
  `BENCH_BOM.md` §2a actually delivers. Rev 1's 6 bpp gave 2 bits/channel.
- **The proven display path is untouched.** Render 320x240, **pixel-double on
  scanout** to 640x480. The VGA timing verified in §3.8, §3.9 and §3.10 does
  not change at all — scanout reads each pixel twice horizontally and each
  line twice vertically.
- **Fill rate improves 4x** (4x fewer pixels): 5.47 screens/frame at 25 MHz,
  21.9 at 100 MHz.

**The cost is half the linear resolution.** That is the trade, stated plainly.

**RATIFIED by the operator, 2026-09-06.**

## 0b. Z-buffer frame lifecycle — NORMATIVE (added rev 3)

Review finding, accepted: rev 2 specified a single 38-block Z-buffer with **no
defined frame transition**. After the colour-bank swap, rasterization targets
the other colour bank while the Z still holds depths describing the frame now
on screen. Rev 2 was silent on this and would have rendered frame N+1 against
frame N's depths.

**The decisive observation: a second Z-buffer buys nothing.** Once the swap
happens, the old Z described the frame now being displayed and is never read
again. There is no reader for a retained second copy. The only real question
is what a clear costs. (For completeness: double 16-bit Z is **152/135 — it
does not fit** regardless; double 8-bit Z fits at 114 but halves depth
precision to buy nothing.)

**DECISION: one 16-bit Z-buffer, cleared at the start of every frame.**

```
clear 76,800 addresses, one write per clock
  at  25 MHz    3.072 ms   18.4% of a 16.67 ms frame     -- too expensive
  at 100 MHz    0.768 ms    4.6% of a frame              -- ACCEPTED
  at 100 MHz using both ports (2/clk)   0.384 ms   2.3%  -- optional optimisation
```

**Normative rules:**

1. **ATOMIC FRAME-TRANSITION SEQUENCE — NORMATIVE, added rev 4.** Review
   finding: "gated on swap acknowledgement" is directionally right but
   permits an implementation to observe `swap_ack`, begin rendering, and
   interleave triangle writes with the clear. The order is exact and the
   raster side implements it as an explicit state machine:

   ```
   S_WAIT_ACK  : frame complete; assert swap_req; wait for swap_ack
   S_SWAP      : on swap_ack, switch the writable colour bank
   S_CLEAR     : run the Z clear to completion.
                 TRIANGLE WRITES ARE BLOCKED IN THIS STATE -- no fragment is
                 accepted, not merely not issued
   S_RENDER    : clear done; accept the first triangle of the new frame
   ```

   Scanout reads colour, never Z, so the clear may overlap scanout of the old
   colour bank — that is what makes one Z-buffer sufficient. The constraint is
   ordering against **rasterization**, not against scanout.
2. **THE CLEAR SWEEPS BOTH MEMORIES — added rev 5, fatal omission.** Rev 4
   cleared only Z. In the §3.10 streaming design, background was produced
   *combinationally* (`!cov0 && !cov1` selects `4'h0`); it was never stored.
   In a double-buffered framebuffer, background must be **written**. Clearing
   only Z leaves `draw_bank` holding the colours written **two frames ago**,
   so any pixel not covered by geometry in frame N+1 displays frame N-1.
   Rev 4's own §0b gate — *"frame N+1 must show background in that region"* —
   would have failed immediately, in simulation and on hardware.

   **One 17-bit counter (0 … 76,799) sweeps both memories in parallel:**
   write `16'hFFFF` to the Z-buffer and the background colour to
   `framebuffer[draw_bank]` on the same cycle. They are separate BRAM
   primitives on `clk_raster`, so this costs **the same 76,800 cycles and zero
   extra latency**. Serialising the two clears instead would cost 153,600
   cycles and drop the fill rate to 19.87 screens/frame — do not serialise.
3. **Rev 4's rule-2 wording was wrong and is withdrawn.** It said the clear is
   gated so it "can never touch a buffer still being scanned out". **The
   Z-buffer is never scanned out at all** — scanout reads colour only, so
   there is zero port contention on Z. The clear does overlap scanout (0.768
   ms against a 16.67 ms frame, roughly display lines 0–22) and that overlap
   is harmless. The real constraint is ordering against **rasterization**,
   which the state machine above enforces. The *colour* half of the clear does
   touch a colour bank — which is why it targets `draw_bank`, never
   `display_bank`, and why it follows the swap.
4. **Gate:** a bench that asserts no fragment write occurs while the clear is
   in flight, and that `S_RENDER` is unreachable before the clear's final
   address. **Negative control:** remove the block and the bench must FAIL.
   **Second negative control, added rev 5:** disable the *colour* half of the
   clear and confirm the bench sees frame N-1's geometry persisting. Rev 4
   would have passed its own gate only because no such control existed.
3. **Z REPRESENTATION — NORMATIVE, rewritten at rev 4.** Review finding, and
   it is sharper than rev 3's wording admitted. The existing pipeline is
   **signed end to end**: `spu_depth_compare` takes `signed [55:0]` and
   compares `depth0 <= depth1`; `spu_attr_stepper` outputs
   `acc >>> frac_bits` as signed 56-bit; `spu_depth_math` applies signs
   explicitly. It **does** produce negative depths in practice — measured
   2026-09-06 during the anchor investigation, unit 1 read `-1616` and
   `-3616` at real pixels. So `16'hFFFF` as a "far" clear would be `-1`
   under the inherited convention: **nearer than every valid depth**, and the
   Z-buffer would reject every fragment. Normative:
   - **The Z-buffer is UNSIGNED 16-bit.** The test is `z_new < z_old`,
     unsigned, strict.
   - **Far clear is `16'hFFFF`.**
   - **`16'hFFFF` is RESERVED for "empty".** Real fragments clamp to
     `16'hFFFE`, so that a genuine far-plane fragment still passes the strict
     `<` against a cleared pixel instead of being invisible.
   - **The signed-56 → unsigned-16 conversion must be specified before RTL**,
     and it is not merely a truncation. It requires a stated scale
     (right-shift), a stated bias, and **clamping at both ends**: depths at or
     below the near plane clamp to `16'h0000`, depths at or beyond the far
     plane clamp to `16'hFFFE`. Negative inputs are legal today and must
     clamp, not wrap.
   - **RTL, host oracle, clear value and the collision bench must all use this
     one representation.** A parity test where the oracle is signed and the
     RTL unsigned will disagree about ordering, not arithmetic, and the
     disagreement will look like a rasterizer bug.
5. **Budget accounting:** the clear consumes 76,800 of the 1,680,000 raster
   clocks available per frame at 100 MHz, leaving 1,603,200 — **20.875 ≈ 20.9
   screens/frame**, independently reproduced by two reviewers.
   **This figure is PIXEL EVALUATION capacity, not visible fill (rev 5).** A
   bounding-box traversal spends cycles on pixels it then rejects, so
   effective *shaded* throughput is nearer 6–10 screens/frame depending on
   triangle shape. Any evidence entry must say which of the two it means.
5. **Gate:** a bench that renders two consecutive frames where frame N covers
   a region that frame N+1 does not. Frame N+1 must show **background** in
   that region, not frame N's geometry. **Negative control:** with the clear
   disabled the bench must FAIL — a lifecycle test that cannot see a stale Z
   proves nothing.

---

## 1. Objective

Take the rasterizer to a GPU that can be fed real geometry at runtime, in
four separately-committable tranches, each with its own falsification gate.

**Non-objective:** matching any existing GPU architecture. Where this design
diverges from mainstream practice (§3), the divergence is deliberate and the
reason is recorded.

---

## 2. What is missing, and what is not

| Stage | Status |
|---|---|
| Host / command interface | **missing** — pin F3 and `spu_uart_rx.v` both exist, unwired |
| Vertex storage | **missing** |
| Transform (model / view / projection) | **missing** |
| **Clipping** (near-plane, guard band) | **missing** — see §7, this is the trap |
| Backface culling | **missing** — cheap, it is the sign of `D` |
| Viewport transform | **missing** |
| **Triangle setup** (edge coefficients) | **missing — computed in Python by hand today** |
| Rasterization / coverage | ✅ `spu_raster_unit` |
| Depth test | ✅ `spu_depth_compare`, 2-way |
| Attribute interpolation | ✅ `spu_attr_stepper` — depth only; generalises |
| Shading | **missing** — flat colour per triangle |
| Blending / alpha | **missing**, and out of scope for this tranche |
| Framebuffer / output merge | **missing** — T2 |
| Display output | ✅ `hal_vga` |
| Double buffering / vsync | **missing** — T2 |

---

## 3. Why a full-frame BRAM framebuffer and NOT tile-based deferred rendering

Recorded because TBDR was the operator's first instinct and the reasoning
should survive review.

TBDR bins geometry per tile so that a **small on-chip tile buffer** suffices,
and pays for it with a parameter buffer in external memory — which is the
genuinely hard part of the architecture. The premise is that a full
framebuffer does not fit on-chip.

**On XC7A100T it does:**

```
BRAM available                        4,860 Kb  (135 x BRAM36, currently 0 used)
640x480 @ 6 bpp, one buffer           1,843,200 bits = exactly 50 BRAM36
double-buffered                       100 / 135 = 74%,  35 blocks spare
packing                               36-bit word holds exactly 6 pixels;
                                      51,200 words = exactly 50 deep
```

The fit is exact, not approximate. Building TBDR here means building the
workaround for a constraint that does not exist, and surrendering the
project's actual distinguishing claim — **no external memory at all** — in
exchange for it.

**The claim this architecture supports, and it is stronger than the current
one:** a complete GPU with no external memory of any kind. Not "no
framebuffer" (which stops being true at T2) — *no DRAM, no VRAM, no
parameter buffer.*

### The trade this introduces, stated up front

A framebuffer removes the triangle-residency ceiling (≈140 parallel units,
LUT-bound, measured 2026-09-06: 436 LUT + 288 FF per raster unit, 463 LUT +
224 FF per attribute stepper) and replaces it with a **fill-rate** limit:

```
frame = 800 x 525 = 420,000 clocks
screen = 307,200 pixels
at 1 px/clk on clk_pixel (25 MHz)    1.37 screens of fill per frame
at 1 px/clk on a 100 MHz raster clk  5.47 screens of fill per frame
```

**Therefore the raster side runs on its own clock**, not `clk_pixel`. True
dual-port BRAM makes this clean rather than clever: write port on the raster
clock, read port on `clk_pixel`, no hand-built CDC. `clk_100mhz` already
exists on the board.

**Unbounded triangle count, bounded total coverage.** That is the honest
statement of what T2 buys, and it must appear in any evidence entry.

---

## 3a. Clock-domain crossings — NORMATIVE (added rev 2, P0-3)

Review finding, accepted: rev 1 said "dual-port BRAM is the synchroniser".
That is true of the **data path** and false of everything else. Dual-port BRAM
does not synchronise buffer-select state, swap requests, `frame_start`, or the
UART commit signal. The domain inventory is below.

**Corrected at rev 3.** Rev 2 listed a "UART bit clock" domain. That is wrong:
`spu_uart_rx` is clocked by the FPGA system clock and derives baud timing with
an internal counter — oversampling, not a separate clock. There is **no third
domain** unless the implementation deliberately creates one.

| domain | clock | owns |
|---|---|---|
| raster | `clk_raster` (100 MHz proposed) | **UART RX and the triangle loader**, triangle setup, rasterization, FB/Z writes, Z clear |
| scanout | `clk_pixel` (25 MHz) | FB reads, pixel doubling, sync generation, `frame_start` |

**The implementation MUST name the actual clock its UART receiver runs on in
the module header**, and its `CLK_HZ` parameter must match that clock — the
baud divisor is derived from it and a mismatch is silent.

**T1 CLOCKING — NORMATIVE, added rev 5.** Review finding: the table above
describes the **T2** end state. **`clk_raster` does not exist in T1.** Today
`spu_a7_gpu_vga_top` has only `sys_clk` (50 MHz) and `clk_pixel` (25 MHz). A
UART receiver clocked from `sys_clk` while the streaming rasterizer runs on
`clk_pixel` would **accidentally create the very CDC this section exists to
avoid**, in the tranche that is supposed to be the simplest.

> **In T1, `spu_uart_rx` and the triangle loader are clocked by `clk_pixel`
> (25 MHz), giving zero clock-domain crossings.** Migrate both to
> `clk_raster` in T2, at which point the §3a table applies and rule 2's
> handshake becomes load-bearing.

**FRAME_START IS FREE-RUNNING AND SEPARATE FROM `swap_ack` — added rev 5.**
Review finding: rule 2 toggles `swap_ack` only in response to a `swap_req`
raised by a *completed frame render*. If the GPU is idle — waiting for a
scene to load, or between uploads — no `swap_req` is raised, so `swap_ack`
never arrives, and a triangle-table commit gated on it **would never
activate**. The two signals must not be conflated:

- Scanout emits a free-running one-cycle **`frame_start_pulse`**, synchronised
  from VSYNC into the raster domain, **every frame, unconditionally**,
  independent of whether any swap is pending.
- Triangle-table commits activate on `frame_start_pulse`.
- Colour-bank swaps use the `swap_req`/`swap_ack` handshake of rule 2.

**Normative rules:**

1. **No multi-bit control signal crosses a domain unsynchronised.** Buffer
   select, swap-pending and commit are multi-bit or shared state; a two-flop
   synchroniser on each bit is **not** sufficient and must not be used.
2. **Bank ownership crosses by toggle handshake.** The scanout domain owns
   `display_bank`. The raster domain requests a swap by toggling `swap_req`;
   scanout samples it through a two-flop synchroniser, performs the swap **at
   `frame_start` only**, and toggles `swap_ack`. The raster domain must not
   write the newly-displayed bank until it has seen `swap_ack`.
3. **The triangle table.** With the receiver on `clk_raster` this is a
   *shadow-bank* problem, not a CDC one: the loader fills a shadow bank and
   sets `commit`, and the swap to active takes effect only at `frame_start`
   (itself synchronised from the scanout domain by rule 2). A partially
   received triangle must be structurally incapable of becoming active — not
   merely unlikely. If the receiver is placed in its own domain, this becomes
   a genuine crossing and needs the rule-2 handshake as well.
   **The UART receiver's `CLK_HZ` parameter must be documented in the module
   header as the raster clock**, since its baud divisor is derived from it and
   a mismatch is silent.
4. **PENDING-COMMIT POLICY — NORMATIVE, added rev 4.** Review finding: with
   one shadow bank, a second commit can arrive while the first is still
   waiting for `frame_start`. Rev 3 was silent, which permits the loader to
   overwrite a bank pending activation. **Decision: back-pressure.**
   - While a commit is pending, the loader **rejects** further triangle
     writes and returns an explicit NAK/status byte. It does not silently
     drop them, and it does not coalesce.
   - Worst-case host wait is one frame, 16.7 ms.
   - Rejected because they are harder to test, not because they are wrong:
     *coalescing to the newest complete image* has an ambiguous notion of
     "complete" mid-write, and *a second shadow bank* costs a third table for
     a case that back-pressure handles in one status byte.
   - **Gate, negative control:** issue a second commit while one is pending
     and assert the pending image reaches the raster side **unmodified**.
4. **Reset must be defined per domain**, and release must be synchronised into
   each. `spu_a7_gpu_vga_top` already does this for `clk_pixel`
   (`pix_rst_sync`); each new domain needs the same.
5. **Every crossing is enumerated in a table in the implementing module's
   header**, naming source domain, destination domain, and mechanism. A
   crossing not in that table is a contract violation.

**Gate:** a testbench that runs the two clocks at a deliberately hostile,
mutually-prime ratio and asserts that no partially-committed triangle table
and no torn bank swap is ever observed across many thousands of frames. A CDC
test at a clean integer ratio proves nothing — the failure mode is precisely
the awkward phase relationship.

---

## 4. Tranches

Each is separately committable and separately gated. **A tranche does not
begin until the previous one's gate has passed and been committed.**

### T1 — Host link: geometry at runtime

* **Objective:** stop requiring a 4-minute resynthesis to change the scene.
* **Files:**
  - `hardware/boards/artix7/spu_a7_gpu_vga_top.v` — add `uart_rx` (pin F3)
  - `hardware/boards/artix7/spu_a7_gpu_vga.xdc` — F3 constraint
  - `hardware/rtl/gpu/spu_tri_loader.v` — **new**, ≤150 lines
  - `hardware/tests/common/spu_tri_loader_tb.v` — **new**
  - `software/tools/spu_gpu_send.py` — **new**, host-side sender
* **Design:** byte-oriented command over the existing onboard CP2102N.
  `spu_a7_100t.xdc` records: *"CP2102N TXD is available on F3, but
  `spu_a7_top` currently exposes TX only."* Reuse
  `hardware/rtl/peripherals/whisper/spu_uart_rx.v`.
* **Invariant — double buffering of the triangle table.** A partially
  received triangle must never be rendered. The loader writes to a shadow
  bank; a commit byte swaps banks, and the swap takes effect only at
  `frame_start`.
* **Gate (all must pass):**
  1. Loader testbench: a byte stream produces the exact expected coefficient
     registers, checked against a Python-generated vector file.
  2. **Negative control:** a truncated stream must leave the active bank
     *unchanged*. A loader that commits partial data passes any test that
     only sends complete messages.
  3. **Negative control:** a commit arriving mid-frame must not tear — assert
     the active bank is constant for the whole of any measured frame.
  4. **Silicon, F3 first — added rev 2.** Review finding: `spu_a7_100t.xdc`
     documents F3, but `spu_a7_gpu_vga.xdc` has **no F3 constraint today**.
     The gate requires an **actual loopback/echo bitstream built and loaded**,
     proving RX on F3 in isolation, **before** the loader is integrated. Not a
     note about future work — a build.
  5. Silicon: upload the §3.10 scene over UART, confirm the boundary is still
     at x = 320 by the measurement method in §3.10.
* **HALT if:** the UART RX path cannot be demonstrated on F3 in isolation
  first. Bring up a loopback or echo before wiring it to the GPU — do not
  debug a link and a consumer simultaneously (`spu_a7_gpu_vga_top.v`'s own
  header states this principle).

### T2 — BRAM framebuffer + Z-buffer, 320x240, 12 bpp, double-buffered

* **PRECONDITION — do not start T2 until this is discharged.** T2 changes the
  output to 320x240 pixel-doubled, which alters the spatial-frequency content
  the CRT control experiment (09-05 §7) exists to observe. Either **run the
  CRT capture on the current 640x480 streaming path first**, or explicitly
  redefine what that experiment measures. Confirmed by review; it is a
  sequencing constraint, not a caveat.
* **Objective:** depth-correct rendering of arbitrarily many *submitted*
  triangles; decouple rasterization from the beam.
* **CLAIM, narrowed at rev 2 per review — use this wording, not rev 1's:**
  *unbounded submitted triangle count, subject to explicit fill-rate limits
  and to the Z-buffer's depth precision.* Rev 1 said "unbounded triangle
  count", which was overstated: removing the two-unit residency limit does not
  by itself provide correct arbitrary-order overlap. The Z-buffer does.
* **Files:**
  - `hardware/rtl/gpu/spu_framebuffer.v` — colour, true dual-port, ≤150 lines
  - `hardware/rtl/gpu/spu_zbuffer.v` — **new**, read-compare-write per pixel
  - `hardware/rtl/gpu/spu_fb_scanout.v` — read side, pixel-doubling to 640x480
  - `hardware/rtl/gpu/spu_gpu_top.v` — raster writes to FB/Z instead of streaming
  - testbenches for each
* **Design:**
  - 320x240. Colour 12 bpp in **18-bit-wide** words, one pixel per word,
    2 banks = 76 BRAM36. Z 16-bit in 18-bit words = 38. Total **114/135**.
  - **One pixel per word at a native port width — no read-modify-write.**
  - Z is read-compare-write per rasterized pixel: read old Z, compare, and on
    pass write both Z and colour.
  - **BRAM collision and read-after-write policy — NORMATIVE, added rev 3.**
    Review finding: rev 2 proposed putting the Z read on one port and the
    write on the other. That is **wrong** — in 7-series RAMB36 a same-address
    access from both ports where one is writing is a **collision**, and the
    read data is explicitly undefined. Required instead:
    0. **REVERTED AT REV 5 — the single-port policy was physically
       impossible.** Rev 3/4 specified one port in `READ_FIRST`. A single
       synchronous BRAM port has **one address bus**: reading A1 at cycle *k*
       forces the bus to A1 again at *k+1* to write it, so A2's read cannot
       begin until *k+2*. That is **≥ 2 clocks per pixel**, capping fill at
       10.4 screens/frame against a contract asserting 20.9 — internally
       contradictory. `READ_FIRST` also does not help: it selects what the
       data output shows **when `WE=1`**, and `WE` cannot be asserted until
       the depth compare has finished. Verified independently before
       accepting.
    1. **TRUE DUAL-PORT.** Port A is a dedicated **read** port
       (`ADDR = addr_in`, `EN = cov`). Port B is a **write** port, multiplexed
       between the frame clear (§0b) and the depth-passing fragment write.
       The two never target the same address in the same cycle except through
       the hazard case below, which the interlock resolves.
    2. **Pipeline depth D is normative, not left open.** D = 2 with fabric
       read latency, D = 3 if `DOA_REG` is enabled for 100 MHz closure. The
       implementation states which, in the module header.
    3. **Same-address hazard interlock, covering the COMPLETE write latency**
       — read latency, compare latency, write issue and any outstanding
       forwarding window, not merely the triangle boundary. Within a triangle
       the rasterizer steps monotonically and consecutive pixels never share
       an address, so the hazard count there is **zero**; the case that
       matters is triangle N+1 starting on a coordinate triangle N just
       processed. Formally: stall or forward when
       `valid_in && (addr_read == addr_pipe[i])` for `i in 1..D`.
       **Cost is negligible** — 200 triangles with a 3-cycle bubble at every
       boundary is 600 cycles, 0.037% of a frame — so the interlock does not
       threaten the fill-rate figure.
    4. **Throughput is MEASURED, not asserted.** The one-pixel-per-clock claim
       stands only once a bench demonstrates it including the interlock's
       stalls. If it degrades to two clocks per pixel the fill rate halves to
       ~10 screens/frame at 100 MHz — still adequate, but §0a would be wrong
       and must be corrected rather than quietly kept.
  - Scanout pixel-doubles horizontally and vertically. `hal_vga` and the VGA
    timing are unchanged from §3.8/§3.9/§3.10.
  - Bank swap on `frame_start` only, via the §3a handshake.
* **Gate:**
  1. Render the §3.10 two-triangle scene through FB+Z and compare the
     scanned-out frame to an oracle: **0 mismatches**, the bar §3.10 met.
  2. **Negative control:** double-buffering deliberately disabled → the bench
     must *detect* a tear. A tear test that cannot see a tear proves nothing.
  3. **Negative control — depth, and this is the P0-2 test:** submit two
     overlapping triangles **in both orders**. The rendered image must be
     **identical**. A Z-buffer that is absent or broken gives painter's-algorithm
     behaviour, which is order-dependent — so this test fails loudly without one.
  4. **Negative control:** 200 triangles, exceeding rev 1's ~140 residency
     ceiling, rendered correctly. That is the point of T2 and must be shown.
  5. Post-route: **verify `RAMB36E1` inference actually occurred** and the
     count is ≤114. Also verify **write behaviour and effective throughput**,
     not just the block count — a correctly-inferred BRAM with a
     read-modify-write penalty still fails the fill-rate claim.
  6. `clk_pixel` meets 25 MHz; `clk_raster` meets its constraint. Report the
     **LAST** "Max frequency" line.
* **HALT if:** yosys maps the framebuffer to distributed RAM, or if the
  measured write throughput is below one pixel per raster clock. Either
  invalidates the fill-rate figure in §0a.

### T3 — Hardware triangle setup

* **Objective:** the actual rasterizer→GPU boundary. Edge coefficients are
  computed in Python by hand today; a GPU computes them from vertices.
* **Files:**
  - `hardware/rtl/gpu/spu_tri_setup.v` — **new**, ≤150 lines
  - `hardware/tests/common/spu_tri_setup_tb.v` — **new**
  - `software/tests/test_gpu_tri_setup_rtl_parity.py` — **new**, oracle parity
* **Design:** from three screen-space vertices, compute per edge
  `A = yj - yi`, `B = -(xj - xi)`, `C = -(A·xi + B·yi)`, plus
  `D = C0 + C1 + C2`. Two multiplies and three subtractions per edge. **238
  DSP48E1 are idle**; use them rather than LUT multipliers.
* **Backface culling — NORMATIVE policy, added rev 2.** Review finding: rev 1
  said "the sign of `D`" without stating which sign is front-facing or how the
  edge inequalities follow. Normative:
  - **`D > 0` is front-facing.** This matches the existing convention:
    `spu_edge_stepper`'s `inside_out` is `(f >= 0)`, and every triangle in
    §3.9/§3.10 was constructed so all three edges evaluate **positive** at
    their opposite vertex (`D = +95,200` and `+257,600` respectively).
  - **`D < 0` is back-facing → cull.** Do NOT flip the inequalities to render
    it; reject it. Rendering both windings would require either two inequality
    senses in the stepper or negating all coefficients at setup, and neither
    is in scope.
  - **`D == 0` is degenerate → reject.** Collinear vertices, zero area.
  - The host-side oracle must apply the identical rule, or the parity test
    will disagree on winding rather than on arithmetic.
* **Gate:**
  1. RTL/oracle parity over a randomised vertex corpus, exact match.
  2. **Negative control:** degenerate triangles (collinear vertices, `D = 0`)
     must be rejected, not rasterized. `spu_reciprocal_core` already has a
     `degenerate` output for `d_in == 0` — use it, do not reinvent it.
  3. **Negative control:** both windings must be tested. A culling test that
     only feeds front-facing triangles asserts nothing.
  4. The §3.10 scene, generated by hardware setup from vertices, must
     reproduce the committed reference render bit-for-bit.
* **HALT if:** the coefficient widths cannot be bounded. §3.10's scene uses
  `C` up to 276,000; a general vertex range must be range-analysed **before**
  RTL, not after an overflow is observed on screen.

### T4 — Transform, perspective, clipping, culling

* **Objective:** 3D geometry in, screen-space vertices out.
* **Files:**
  - `hardware/rtl/gpu/spu_vertex_transform.v` — **new**
  - `hardware/rtl/gpu/spu_clip_near.v` — **new**
  - oracle + parity tests for both
* **Design:**
  - 4×4 matrix transform to clip space. Integer/fixed-point throughout — no
    floats (AGENTS.md §3.1).
  - **Perspective divide by `w` at setup time**, via `spu_reciprocal_core`
    (`[33:0] d_in`, `[15:0] y_out`, `[6:0] exp_out`, shared multiplier port,
    characterised against `software/lib/gpu_reciprocal_oracle.py`). **Do not
    write a second reciprocal.**
  - **PRECONDITION, added rev 2 — this tranche may not start until the
    reciprocal is re-characterised for perspective.** Review finding: the
    existing evidence gives ~15 correct bits over a **16–25-bit denominator
    range**, with ~1.2–1.7 units of 16-bit depth error on representative
    cases. That is depth evidence, not a perspective-divide bound. Required
    before RTL:
    1. fixed-point format for clip-space `w`;
    2. camera near/far range the design commits to;
    3. worst-case screen-coordinate error in **pixels**, derived not assumed;
    4. an explicit acceptable pixel error, agreed in advance.
    If the existing core cannot meet (4) over (2), **HALT** — that is an
    architecture change, not a tuning exercise.
  - **Clipping — NORMATIVE, added rev 2.** Rev 1 said only "`w <= 0` must be
    clipped", which review correctly called underspecified. Required:
    1. **Clip-space convention** stated explicitly (which handedness, and
       whether the near plane is `z >= 0` or `z >= -w`).
    2. **Near-plane inequality** stated as an exact integer comparison — no
       epsilon, no float.
    3. **Guard-band limits** derived from the coefficient width bounds, so an
       off-screen vertex cannot wrap `A`, `B` or `C`.
    4. **Edge-intersection arithmetic** for clipped vertices specified in
       fixed point, including how the interpolation parameter is computed
       without division (or with a setup-time reciprocal).
    5. **`w == 0` policy defined BEFORE the reciprocal is invoked.** It is a
       geometry decision, not a reciprocal-core test: the vertex is at the eye
       and the triangle must be rejected or clipped upstream. Relying on the
       core's `degenerate` output is a backstop, not the policy.
* **Gate:**
  1. Transform/oracle parity over randomised matrices and vertices.
  2. **Negative control — the one that matters:** a triangle with one vertex
     behind the eye plane (`w <= 0`) must be clipped, not rasterized. Feed it
     unclipped first and confirm the bench *fails*; then clip and confirm it
     passes. Without the first half this test asserts nothing.
  3. **Negative control:** a vertex exactly at `w = 0` must hit the
     reciprocal's `degenerate` path and be rejected, not produce a wrapped
     coordinate.
  4. Guard-band: coordinates far off-screen must not wrap the coefficient
     widths. Range-analyse, and test at the limits.
* **HALT if:** perspective-correct *attribute* interpolation is proposed. The
  depth-v2 evidence entry states plainly that perspective-correct texture
  mapping is out of scope and needs a genuinely per-pixel reciprocal, not a
  setup-time one. That has not changed. Screen-space-linear depth is what
  `spu_attr_stepper` does and all this tranche requires.

---

## 5. Invariants (the "Never" list)

- [ ] **No floating point, no division in RTL.** Reciprocal is setup-time only.
- [ ] **No external memory.** No DDR3, no VRAM, no parameter buffer. If a
      tranche appears to need one, HALT and revise the contract — that is an
      architectural change, not an implementation detail.
- [ ] **No second reciprocal, no second multiplier arbiter.** Reuse
      `spu_reciprocal_core` and `spu_shared_mult35`.
- [ ] **Lithic modules, 50–150 lines.** Split rather than grow.
- [ ] **Every new module gets a testbench with at least one negative control
      that has been observed to FAIL on broken RTL.** A bench that has only
      ever passed proves nothing — see `spu_gpu_top_depth_anchor_tb.v`, whose
      first version passed against RTL that was still broken.
- [ ] **Every new module must be instantiated by a top or a bench before the
      tranche closes.** Run `python3 tools/rtl_instantiation_audit.py`; a new
      module appearing in DEAD or TB-ONLY is a tranche failure.
- [ ] **No silicon claim without a `docs/hardware_evidence.md` entry.**

---

## 6. Mandatory verification

```bash
# per-tranche scoped run
TB_FILTER=gpu python3 run_all_tests.py

# full gate -- run it TWICE. It was not idempotent until 2026-09-06 and
# one pass is exactly what the broken version also produced.
bash tools/verify_repo.sh && bash tools/verify_repo.sh

# dead-code sweep: no new module may be unreachable
python3 tools/rtl_instantiation_audit.py --class dead
python3 tools/rtl_instantiation_audit.py --class tb-only

# board rebuild -- simulation-green says nothing about a spin
source tools/env_openxc7.fish   # or .sh
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t gpuvga all
```

**Note on bitstream hashes:** A7 `.bit` files are **not byte-reproducible** —
they carry a build timestamp (measured 2026-09-06: two builds from identical
source differ in exactly 3 bytes at offsets 122–125, all configuration data
identical). A hash mismatch on rebuild proves nothing. Compare the
**utilisation table** instead.

---

## 7. THE TRAP: clipping

Recorded separately because it is the single most likely way this tranche
produces a defect that looks like an RTL bug and is not.

Every triangle drawn on this project so far has been **hand-placed, fully
on-screen, with all vertices in front of the eye.** Clipping has therefore
never been exercised, and its absence has never been felt. The moment T4
lands and anything moves, a vertex will cross the eye plane, `w` will go to
zero or negative, the perspective divide will produce a wrapped or saturated
coordinate, the edge functions will invert, and the screen will fill with
geometry that looks exactly like a rasterizer bug.

**The debugging cost of finding this after the fact is far higher than the
cost of building it in.** T4's gate 2 exists specifically to force it, and it
is written as a *negative* control — the unclipped case must be observed to
fail — because a clipping test that only feeds valid geometry is vacuous.

---

## 8. Stop conditions

- Any pre-execution review finding an unhandled edge case or contradiction →
  **HALT and flag**, with a minimal proposed correction. Do not silently
  rewrite the architecture.
- Any testbench asserting FAIL, or timing not closing → **HALT**.
- Do not add pipeline stages or FIFOs to paper over a timing failure without
  a revised contract.
- Any tranche that appears to require external memory → **HALT** (§5).

---

## 9. Review status

### 9a. Rev 1 errors, recorded not deleted

External review, 2026-09-06. Three P0 findings, **all accepted**. Two of them
invalidated rev 1's configuration outright.

| # | Rev 1 error | Status |
|---|---|---|
| P0-1 | Packed 6 px/36-bit word cannot take one arbitrary pixel per clock; needs read-modify-write. "Dual-port BRAM" does not address write granularity | **DISSOLVED** by §0a — one pixel per word at a native 18-bit width |
| P0-2 | No depth persistence. Serial rasterization needs the depth earlier triangles wrote; a colour buffer cannot supply it. "Unbounded triangle count" was overstated | **RESOLVED** by §0a's 16-bit Z-buffer; claim narrowed in T2 per the reviewer's wording |
| P0-3 | CDC absent. Dual-port BRAM synchronises data, not buffer-select, swap request, `frame_start` or UART commit — and there are three domains | **ADDRESSED** by new §3a, normative |
| — | T3 winding policy unstated | fixed: `D > 0` front-facing, normative in T3 |
| — | Reciprocal evidence is depth-range only | fixed: T4 now blocked on a precondition with four deliverables |
| — | Clipping arithmetic underspecified | fixed: five normative requirements in T4 |
| — | F3 not constrained in the GPU xdc | fixed: T1 gate now requires a built loopback bitstream |
| — | BRAM estimate theoretical until inference proven | fixed: T2 gate 5 requires verifying inference **and** write throughput |

**Rev 1's §3 arithmetic was correct and useless.** The 50-BRAM packing was
exact — and it was the packing that created P0-1, while the budget it fed
omitted depth entirely. Being precise about the wrong quantity is not
partial credit.

**What rev 1 got right and survives:** the TBDR rejection (§3) — the reviewer
did not challenge it, and the memory-capacity argument holds at 320x240 with
even more headroom. The tranche structure, the negative-control discipline,
and the §7 clipping trap all stand.

### 9b. Still open — attack these next

1. **Operator ratification of §0a.** Half the linear resolution is a real
   cost and is not mine to accept.
2. **Z read-compare-write throughput.** T2 asserts one pixel/clock using the
   second BRAM port for the read. Unproven. If it costs two clocks per pixel
   the fill rate halves to 2.7 screens/frame at 25 MHz — still adequate, but
   the number in §0a would be wrong.
3. **16-bit Z precision** across the committed near/far range. Not analysed.
   Z-fighting on near-coplanar surfaces is the failure mode.
4. **The T4 reciprocal precondition** may simply fail. It is the most likely
   place this contract is wrong, and it was the most likely place before the
   review too.
5. **Tranche ordering.** T1 before T2 still gives value soonest, but T2 now
   changes the raster interface more than rev 1 implied (Z read-compare-write,
   not just a write port). Reordering may avoid rework.
6. ~~Pixel-doubling and the CRT experiment.~~ **CONFIRMED by review and
   promoted to a T2 precondition at rev 3.** No longer open.
7. ~~§0b and T2's collision policy unreviewed~~ — **reviewed at rev 4 and
   confirmed viable**, with the interlock requirement strengthened: it must
   cover the **complete write latency** (clear completion, read latency,
   compare latency, write issue, and any outstanding write-forwarding
   window), not merely the triangle boundary.
8. **The signed→unsigned Z conversion is specified but not designed.** Scale,
   bias and clamp points are named as required deliverables in §0b rule 3 and
   have not been chosen. This is the most likely place rev 4 is still wrong.
9. ~~Gemini audit outstanding~~ — **landed, rev 5.** It reversed rev 3/4's Z
   port policy and caught a fatal omission (no colour clear). Both are fixed
   and both are now the newest unreviewed material.
10. **Rev 5 itself is unreviewed.** Dual-port + D-stage interlock, the
    parallel two-memory clear, T1-on-`clk_pixel`, and the free-running
    `frame_start_pulse`. Given that every round so far has found real defects
    in the previous round's *fixes*, assume this one does too.

**Reviewer note:** claims here are graded. Distinguish "silicon-verified" (a
`docs/hardware_evidence.md` entry exists), "testbench-verified", and
"unmeasured". Nothing in this contract is silicon-verified; §0's starting
state is.
