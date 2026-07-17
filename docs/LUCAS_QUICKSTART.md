# LUCAS evaluator quickstart

The `LUCAS` spin is a Wukong Artix-7 100T evaluator for exact arithmetic in
`Z[φ]/L_521`. In one run, `tools/lucas_demo.py`:

1. checks the four sidecar operations PSCALE, PCHIRAL, PMUL, and PINV against
   exact-integer results; and
2. feeds 200 successive φ-scalings back through the FPGA while running the
   same recurrence in exact Python integers and IEEE-754 `float64`.

The FPGA result must remain bit-exact. The `float64` comparison is pinned to
lose the exact residue at step 79. This is the short evaluator demonstration;
the separate Lucas oracle test carries the one-million-step zero-drift proof.

## 1. What you need

- QMTech Wukong Artix-7 100T board
- an RP2040 running DirtyJTAG, or another supported JTAG adapter
- an RP2350-Zero/Pico 2 running the SPU diagnostic console
- five signal/ground jumpers and USB cables
- the OSS CAD Suite/OpenXC7 environment described in
  [the toolchain guide](toolchain_setup.md)

The current constraints use the remapped **bottom row** of Wukong J11. On the
repository's bench unit, J11 pins 1-3 were damaged by backfeeding and must not
be used.

## 2. Wire the southbridge

Power both boards down before changing wiring.

| Wukong J11 | FPGA signal | RP2350 |
|---|---|---|
| J11-7 / J4 | CS# | GP1 |
| J11-8 / G4 | SCK | GP2 |
| J11-9 / B4 | MOSI | GP3 |
| J11-10 / B5 | MISO | GP0 |
| J11-11 | GND | GND |

Do not join the boards' 3V3 rails. J11-12 is a target reference, not a power
input for the RP2350. Power the Wukong before allowing the RP2350 to drive its
SPI pins, and stop or unplug the RP2350 before powering the Wukong down. This
avoids driving an unpowered FPGA through its I/O protection network. The full
board and JTAG wiring is in
[the build and bring-up guide](build_and_bringup_guide.md#42-wukong-j11-spi-wiring).

## 3. Build and load the FPGA spin

From the repository root:

```bash
A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t lucas all
openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_LUCAS.bit
```

The `A7_FREQ=2` setting is intentional. This CE-paced evaluator routed at
4.41 MHz in the recorded build; it is a low-speed bring-up profile, not a
50 MHz timing-closure claim. A successful SRAM load ends with `isc_done 1`,
`init 1`, and `done 1`.

## 4. Build and load the RP2350 console

The host demo uses the interactive `rp2350_spu_diag` firmware. Configure it
for the GP0-GP3 header mapping and the conservative 250 kHz SPI clock:

```bash
cmake -S hardware/rp2350 -B build/rp2350_lucas_demo \
  -DPICO_BOARD=pico2 \
  -DSPU_RP2350_ZERO_HEADER_SPI=ON \
  -DSPU_DIAG_SPI_BAUD_HZ=250000
cmake --build build/rp2350_lucas_demo --target rp2350_spu_diag -j
picotool load -f build/rp2350_lucas_demo/rp2350_spu_diag.uf2
picotool reboot
```

After reboot, find the CDC port with `ls -l /dev/serial/by-id/` or the
equivalent command for your operating system. The console banner begins
`SPU RP diagnostic console ready`.

## 5. Run the evaluator

Install the host package once, then name the RP2350 CDC port:

```bash
python3 -m pip install -e .
python3 tools/lucas_demo.py --port /dev/ttyACM0 --steps 200
```

The important output is:

```text
Act 1: the four Z[phi]/L_521 sidecar ops (silicon-proven vectors)
  PSCALE ... [ok]
  PCHIRAL ... [ok]
  PMUL ... [ok]
  PINV ... [ok]
...
  step     79: float64 diverged ...
  silicon: bit-exact against ground truth for all 200 steps.
  float64: lost the exact value at step 79 and never recovers.
PASS: silicon matched exact-integer ground truth on every check.
```

Any mismatched lane or coefficient makes the command exit nonzero. Use at
least 79 steps to expose the float boundary; the default of 200 leaves useful
margin without turning the CDC round trip into a marathon.

## 6. Hardware-free check

The regression test pins instruction encoding, all four golden results, PINV
over an operand sweep, the float divergence point, and both pass/fail handling
with an emulated sidecar:

```bash
python3 software/tests/test_lucas_demo.py
```

Expected footer: `PASS (14 checks)`.

## Evidence boundary

The arithmetic engine and four SPI-visible operations were proven in Wukong
silicon in the recorded J11 smoke test; see
[hardware evidence section 3.2e.2](hardware_evidence.md#32e2-wukong-j11-lucas-spi-sidecar-proof).
That 2026-07-03 run used the original J11 row. The replacement bottom-row
transport was subsequently electrically and core-level proven, and is now the
constraint-file source of truth. The `tools/lucas_demo.py` evaluator itself is
hardware-free regression tested; its first combined run on the remapped pins
should be appended to the evidence ledger rather than silently folded into the
older proof.

This evaluator demonstrates exact finite modular-ring arithmetic and deterministic
replay. It does not claim real-number accuracy for unbounded Fibonacci growth,
production timing closure, or a deployed sensor application.

---

*CC0 1.0 Universal, like the rest of `docs/`.*
