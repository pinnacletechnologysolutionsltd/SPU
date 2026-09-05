# My FPGA Toolchain Had Been Dead for Weeks and I Didn't Know

**2026-09-04. First video output of any kind from this project, on any board.**

Eight colour bars and a scrolling marker line, 640×480 at 60 Hz, on a physical
monitor. Getting there meant finding out that every FPGA build I'd run for
weeks had been failing silently, that the HDMI path I'd designed can't be
placed by my toolchain at all, and that the vendor documentation for the
board's expansion header is wrong in both available versions.

Here's what actually happened.

---

## The builds had been failing and leaving no trace

`build/` contained no bitstreams. Not stale ones — none. I'd been assuming a
design problem.

```
$ ldd ~/.local/openxc7/bin/nextpnr-xilinx | grep 'not found'
```

Seven missing Boost shared libraries. Two more for `bbasm`. The openXC7
prebuilts link against **Boost 1.91**; my system had rolled forward to
**1.92**, which is not ABI-compatible. Every place-and-route invocation had
been dying on library load.

Symlinking 1.92 as 1.91 does *not* work — `bbasm` then dies with
`undefined symbol: _ZN5boost15program_options3argB5cxx11E`. The fix was to
extract the actual 1.91 shared objects out of the cached Arch package
`boost-libs-1.91.0-2` and point `LD_LIBRARY_PATH` at them. No system
downgrade, no root.

That cached package is the only reason this was recoverable in an afternoon.
If you run a rolling distro with a prebuilt EDA toolchain, don't run
`paccache -r` aggressively.

**The lesson isn't about Boost.** It's that a broken toolchain and a broken
design present identically — you get no bitstream either way. `ldd` on your
binaries costs two seconds and should come before you suspect your own RTL.

## HDMI: correct RTL, blocked upstream

I'd written the HDMI path properly. The original `hal_hdmi.v` turned out to
have **never been instantiated by any top on any board** — and its Xilinx
branch serialised in fabric at 250 MHz, which will not close on a -1 part. I
replaced it with a real OSERDESE2 implementation at 125 MHz DDR.

It synthesises cleanly. Then nextpnr-xilinx hangs forever in the placer.

I bisected it:

| design | result |
|---|---|
| no MMCM, no differential IO | builds and loads |
| video logic, single-ended | OK |
| MMCM + video logic, single-ended | OK |
| MMCM + OBUFDS/TMDS_33, no OSERDESE2 | **hang** |
| full HDMI | **hang** |

MMCM is fine. OSERDESE2 is fine. **Differential output is the blocker** —
openXC7/nextpnr-xilinx issue #66, "diff out from IOSERDES blocks", open since
July 2025 and unimplemented. Rebuilding the toolchain will not fix it.

I burned real time before that bisection because I tried the simulated-anneal
placer, which in this build reports
`post-placement validity check failed for Bel .../A5FF (no cell)`. That's a
placer artifact, not a design fault, and it sent me chasing control sets and
clocking for hours. Always use heap.

While I was there I wrote the first testbench the TMDS encoder has ever had —
it had shipped untested since creation. **4518 checks pass** against a
reference model of DVI 1.0 written independently from the spec rather than
copied from the design under test, and the count reconciles exactly: 4 control
words + 256×2 data + 4000 disparity + 2 negative controls. Mutation-tested 3/3
— corrupted control word, broken DC-balance term, and flipped `xnor_mode`
threshold are all caught. The encoder is correct. It just can't be placed yet.

## VGA: measure the pins, don't read the datasheet

VGA needs no differential output and no MMCM. 640×480@60 wants a 25 MHz pixel
clock; the board oscillator is exactly 50 MHz, so divide by two. One bit per
channel through a three-resistor DAC. 246 LUTs, 54 flip-flops.

Then nothing appeared on the monitor, and I wasted a long stretch on two
mistakes worth naming.

**First: I read a green monitor LED as "sync locked."** It meant "monitor
awake." That single misread pointed the entire search in the wrong direction.

**Second: I built three bitstreams on pin mappings inferred from
documentation before measuring anything.** The QMTech README and the LiteX
platform file list the J10 header's pins in *opposite* orders, neither states
which is physical, and — as it turns out — neither is wholly right.

The fix took two minutes once I stopped guessing. I built a bitstream that
drives all eight header pins at frequencies a factor of two apart, so every
pin announces itself, then probed at the VGA plug:

```
VGA pin 13 (HSYNC) <- FPGA D5    6103.0 Hz, 0.0% error
VGA pin 14 (VSYNC) <- FPGA E5     381.5 Hz, 0.0% error
```

J10's top row follows the LiteX order. Its bottom row does not. Both of my
earlier constraint files had exactly one of the two sync signals right.

That beacon bitstream kept earning its keep: it repeatedly caught probes that
had silently lost contact. **Silence on a probe means nothing until you've
seen a known-toggling signal on the same point.**

## The result

Measured on silicon with a logic analyser, 2-second captures:

| quantity | measured | expected | error |
|---|---|---|---|
| HSYNC frequency | 31248.25 Hz | 31250 | **0.006%** |
| HSYNC duty | 88.01% | 88.00% | exact |
| implied pixel clock | 24.9986 MHz | 25.0000 | 0.006% |
| implied frame rate | 59.520 Hz | 59.524 | 0.007% |

The 88.01% duty is the VESA 640×480@60 sync pulse exactly — 96 low out of 800.
That makes this standards-conformant timing rather than a square wave at
roughly the right rate. The three colour channels each read ~36.4% high
against 36.6% predicted (40% × 480/525), so vertical blanking shows up
independently in all three.

And then eight vertical bars in the correct order — white, yellow, cyan,
green, magenta, red, blue, black — with the marker line scrolling down the
screen. The scroll is the point: static bars can't distinguish a running
pipeline from a frozen one.

## The bench bit back

My programmer had worked for hours, then died once the VGA harness reached a
monitor. One BOOTSEL reset, three
USB bulk-write failures, then total loss of enumeration — no BOOTSEL either,
and BOOTSEL is mask ROM, so that means dead.

**Leading hypothesis, not demonstrated:** a ground loop through the monitor's
mains earth, from monitor earth through VGA ground to FPGA ground, out the
JTAG lead, through the programmer to USB ground and back to mains. It's
supported by elimination — with the monitor disconnected, the replacement
programmer performs full 3.8 MB writes flawlessly, the same operation that
failed four times with the monitor attached. I haven't proven it, and I'm not
going to write it up as proven.

Worth noting for anyone doing the same thing: the series resistors I'd added
to TCK/TMS/TDI after an earlier incident don't help here. The fault current
returns through ground and bypasses them entirely.

---

Everything above is in the repository: the constraint files including the two
wrong ones, kept as the record of how the mapping was narrowed; the bitstream
SHA-256 and the commit that built it; the raw logic-analyser measurements; and
the HDMI RTL, written and waiting for a placer that can handle it.

*SPU project — [github.com/pinnacletechnologysolutionsltd/SPU](https://github.com/pinnacletechnologysolutionsltd/SPU)*
