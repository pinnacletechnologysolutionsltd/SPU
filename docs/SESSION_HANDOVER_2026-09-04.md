# Session Handover — 2026-09-04

## 0. One-line state

Artix-7 bench went from **silently non-functional** to **a verified 640x480
VGA pipeline driving a real monitor**; HDMI is blocked upstream, the RP2040
programmer died to a ground loop, and tensegrity's active-control primitive
was falsified before any RTL was written.

---

## 1. THE BIG ONE: the A7 toolchain was dead and nobody knew

`nextpnr-xilinx` was missing **7** Boost shared libraries and `bbasm` **2**.
The openXC7 prebuilts are linked against **Boost 1.91**; the system had moved
to **1.92**, which is not ABI-compatible. **Every A7 build had been dying at
P&R.** That is why `build/` contained no `.bit` files at all.

**Symlinking 1.92 as 1.91 does NOT work** — `bbasm` then dies on
`undefined symbol: _ZN5boost15program_options3argB5cxx11E`.

**Fix:** extracted the 1.91 shared objects from the cached Arch package
`boost-libs-1.91.0-2` into `~/.local/openxc7/lib/boost-1.91`. No system
package downgraded, no root. `tools/env_openxc7.sh` now prepends any
`$OPENXC7_ROOT/lib/boost-*` directory to `LD_LIBRARY_PATH` and is a no-op
elsewhere. Commit `972e5c9`.

**Do not `paccache -r` aggressively** — that cached package is what saved
this. Diagnostic for next time:
`ldd ~/.local/openxc7/bin/nextpnr-xilinx | grep 'not found'` **before**
suspecting RTL or build scripts.

---

## 2. Display path

### 2.1 A real repo bug: the spurious HDMI pair

`spu_a7_100t.xdc` constrained `hdmi_d_p/n[3]` to **D5/E5**. Those are **J10
expansion header** pins, not HDMI, and the polarity was inverted (D5 is
`IO_L13N`, E5 is `IO_L13P`). **Every A7 bitstream ever flashed was driving
two J10 header pins to 0.** Removed; port narrowed `[3:0]`->`[2:0]` in all
four A7 tops, all re-verified by synthesis. Commit `2d44fad`.

Remaining eight TMDS pins verified against the LiteX `qmtech_wukong`
platform file and prjxray `package_pins.csv`: genuine differential pairs,
bank 35, correct polarity, `hdmi_clk_p/n` on D4/C4 correct.

Also corrected `knowledge/RATIONAL_SHADER.md`, which claimed "HDMI display
Ready" citing two files that do not exist anywhere in the repo.

### 2.2 HDMI/DVI: BLOCKED UPSTREAM, do not retry

`hal_hdmi.v` had **never been instantiated by any top on any board**. Its
Xilinx branch serialised in fabric at 250 MHz, which will not close on a -1
part. Replaced with `hal_hdmi_serdes_a7.v` (OSERDESE2 MASTER/SLAVE, 125 MHz
DDR). `spu_a7_video_top.v` wires it up with an MMCM.

It synthesises cleanly and **nextpnr-xilinx hangs forever in the placer.**
Root cause confirmed upstream: **openXC7/nextpnr-xilinx issue #66, "diff out
from IOSERDES blocks", OPEN since Jul 2025 — differential output is
unimplemented.** A toolchain rebuild will NOT fix this.

Bisection (default heap placer):

| design | result |
|---|---|
| LUCAS (no MMCM, no diff IO) | builds + loads |
| video logic, no MMCM, single-ended | OK |
| MMCM + video logic, single-ended | OK |
| MMCM + OBUFDS/TMDS_33, no OSERDESE2 | **HANG** |
| full VIDEO | **HANG** |

MMCM fine, OSERDESE2 fine. **Differential output is the blocker.**

**`--placer sa` is broken in this build.** It reports
`post-placement validity check failed for Bel .../A5FF (no cell)` and
`Invalid global constant node .../VCC_WIRE` (upstream #154). These are
placer artifacts, NOT design faults — they sent me chasing control sets,
MMCM and OSERDESE2 before I bisected properly. **Always use heap.**

Path forward for HDMI: Vivado (free for xc7a100t, ~40 GB, glibc 2.44 risk on
CachyOS), or an upstream nextpnr contribution. RTL is written and waiting.

### 2.3 TMDS encoder: first test in its life

`hal_hdmi_tmds.v` shipped untested since creation. Added
`hardware/tests/common/hal_hdmi_tmds_tb.v` — checks against an **independent**
reference model of DVI 1.0 written from the spec, not copied from the DUT.
**4518 checks pass**, and the count reconciles exactly (4 control + 256x2
data + 4000 disparity + 2 negative controls). **Mutation-tested 3/3**:
corrupted control word, broken DC-balance term, flipped `xnor_mode`
threshold all caught. The encoder itself is correct.

### 2.4 VGA: WORKS

Single-ended LVCMOS33, no OSERDESE2, **no MMCM** (640x480@60 wants 25 MHz;
the board oscillator is exactly 50 MHz, so divide by two). Reuses the
pre-existing `hal_vga.v`, already wired into `spu_gpu_top`.

`clk_pixel` closes at **170.97 MHz** against 25 MHz. 246 LUTs, 54 FFs.

**Silicon measurements (fx2lafw on J10):**

| signal | measured | expected | error |
|---|---|---|---|
| HSYNC | 31248.25 Hz | 31250 | **0.006%** |
| HSYNC duty | 88.01% | 88.00% | exact VESA 96-of-800 |
| pixel clock | 24.9986 MHz | 25.0000 | 0.006% |
| frame rate | 59.520 Hz | 59.524 | 0.007% |
| GREEN | 1.00 runs/line | bars 0-3 contiguous | ✓ |
| RED | 2.00 runs/line | bars 0,1 + 4,5 | ✓ |
| BLUE | 3.64 runs/line | bars 0,2,4,6 x 480/525 | ✓ |

All three colour channels read ~36.4% high against 36.6% predicted
(40% x 480/525) — vertical blanking confirmed independently in each.

**A real monitor locked (green LED, no "no signal") on `VGAREV`.**

### 2.5 J10 pin order — settled by experiment

The QMTech README and the LiteX platform file list J10's pins in **opposite**
orders and neither states which is physical. **`VGAREV` is the one that
locks a monitor**, so the README order is physical. Both xdc variants are
kept; `spu_a7_vga_rev.xdc` is the correct one.

`J10IDENT` drives all eight J10 pins at frequencies a factor of two apart,
making every pin self-identifying. It repeatedly caught probes that had lost
contact — **silence on a probe means nothing until a known-toggling
bitstream has been seen on the same point.**

---

## 3. BENCH: RP2040 programmer destroyed

Worked for hours, then died after the VGA harness reached a **monitor**.
Sequence: one BOOTSEL reset, three USB bulk-write failures, total loss of
enumeration (no BOOTSEL either — BOOTSEL is mask ROM, so that means dead).

**Leading hypothesis, not demonstrated: a ground loop through the monitor's
mains earth.**

```
monitor earth -> VGA ground -> FPGA ground -> JTAG ground lead
    -> RP2040 -> USB ground -> PC -> mains earth
```

Supported by elimination: with the monitor disconnected, the replacement
programmer performs full 3.8 MB writes flawlessly — the same operation that
failed four times with the monitor attached. The series resistors on
TCK/TMS/TDI do not help here; the fault current returns through **ground**,
bypassing them.

**Replacement:** RP2350 Pico 2, DirtyJTAG built and flashed, verified
driving the FPGA. Build recipe, which cost several attempts:

```bash
cmake -S tools/rp2040_tooling/repos/pico-dirtyJtag -B build/pico_dirtyjtag_rp2350 \
  -G Ninja -DPICO_BOARD=pico2 -DPICO_PLATFORM=rp2350-arm-s \
  '-DCMAKE_C_FLAGS=-mcpu=cortex-m33 -mthumb -DBOARD_TYPE=BOARD_RP2040_ZERO'
```

- `PICO_PLATFORM` must be **`rp2350-arm-s`**, not `rp2350` (else
  `PICO_USE_SW_SPIN_LOCK` build failure).
- `BOARD_TYPE` must go through `CMAKE_C_FLAGS`, which **replaces** the SDK's
  arch flags, so `-mcpu=cortex-m33 -mthumb` must be supplied. Passing
  `BOARD_TYPE` as a plain CMake variable silently builds the **wrong pinout**
  (GP16-19), which looks like dead wiring at the bench.
- Verify with `picotool info -a`: must read `0:TDI 1:TMS 2:TCK 3:TDO`.

**DO NOT reconnect the monitor until a USB isolator is fitted.** ~£15,
ADuM3160-class. Full Speed 12 Mbps is sufficient — RP2040/RP2350 USB is Full
Speed anyway. Note the fx2lafw analyzer is High Speed and must NOT be put
behind a FS isolator.

Free interim mitigation: PC, Wukong supply and monitor on the same mains
outlet, or run the host laptop on battery.

---

## 4. Tensegrity: primitive FALSIFIED before any RTL

The active-control frontier was gated on an explicit contract, which did not
exist. Wrote `spu_strategy/contract_tensegrity_active_control_2026-09-04.md`
answering the five required specification points, then ran its own §7
falsification gate.

**Chosen primitive: one exact rotation of one strut, octahedral group (24).**

**Naive result looked like a pass:** 120/120 breaking perturbations
recovered by a single rotation, 100%.

**Real result:** every perturbation had *exactly* 4 restorers — the order of
the `C4` stabiliser of a strut axis. Enumerating all 144 single rotations
from the balanced state: 24 balance, and **all 24 produce identical geometry
AND identical node labels. Zero new geometries.** The rotations that
preserve balance are exactly the ones that do not move the strut.

**100% recovery was recovery by not moving.** A controller whose reachable
balanced set is one point performs no control. Contract status **BLOCKED**,
no RTL authorised.

Survives as a *fault-recovery* mechanism, which needs no proposal search.

**Scope limit, stated:** tested the 24-element octahedral group, not all 36
ROTC angles. Angles 1-20 are Quadray/thirds and likely fail the contract's
own lattice-closure invariant in the signed-32-bit `Z[phi]` ABI — hypothesis,
not shown. Also: the Python oracle is built on unbounded `Fraction`, so it is
a `Q(phi)` model and **structurally cannot detect lattice overflow**; an
explicit integrality check had to be bolted on.

Tensegrity regression: **69 PASS, 0 FAIL.**

---

## 5. Tang Primer 25K: deprioritized

John, verbatim: *"Forget the Tang 25k until I can buy a functional
baseboard. I don't think the Tang 25k is that useful for our work anymore."*
This shelves the 2026-08-26 GPU pixel-content mismatch and the planned
RP2350-as-serial-bridge on K11.

---

## 6. Commits (5, unpushed)

```
04bd312  a7: VGA spins that actually build, plus a J10 pin-identification probe
0d4947e  a7: VIDEO spin (640x480 DVI) -- builds, but openXC7 cannot place it
827b86c  hdmi: OSERDESE2 serialiser for A7, and the TMDS encoder's first testbench
2d44fad  a7: remove spurious HDMI data pair, verify the real pinout, fix a false claim
972e5c9  toolchain: portable Boost shim so openXC7 survives a distro Boost bump
```

**Deliberately NOT committed** (pre-existing in the tree, not this session's
work, per the never-`git add -A` rule): `docs/INA226_*`,
`software/lib/ina226_capture.py`, `tools/bench_metrics/*`,
`tools/ina226_capture_pipeline.py`, `hardware/boards/tang_primer_25k/*`, and
untracked `SESSION_HANDOVER_2026-08-27/09-01/09-02/09-03`,
`ina226_coarse_monitor_v5.json`, `interactive_capture.py`,
`tools/memory_search/`.

---

## 7. Next session

**Resume condition is concrete and short.** Fit the USB isolator, connect
three colour wires (J10-2/3/4 through 270R to VGA pins 3/2/1), load
`build/spu_a7_100t_VGAREV.bit`, expect eight colour bars with a red line
scrolling down. Twenty minutes.

Then, in rough priority order:

1. **GPU on the proven display path.** `spu_gpu_top.v` already has
   `vga_r/g/b`, `vga_hsync`, `vga_vsync` and already instantiates `hal_vga`.
   Wiring the real rasterizer to a verified VGA path is a small change, not a
   project. Needs a resource check against LUCAS's ~20%.
2. **Southbridge SPI throughput** — the §4 priority from 09-03, untouched
   today. It is also the processor->display link for a live scene, so it is
   not competing with the GPU work.
3. **Vivado decision** for real HDMI, with a working display already in hand.
4. **Buy the power-ready interlock parts.** Deferred in August on the
   grounds that series resistors mitigate the damage class; tonight is
   evidence against that.

## References

- `spu_strategy/contract_tensegrity_active_control_2026-09-04.md`
- openXC7/nextpnr-xilinx issues #66 (diff out, OPEN) and #154 (VCC_WIRE)
- `docs/SESSION_HANDOVER_2026-09-03.md` (previous)
