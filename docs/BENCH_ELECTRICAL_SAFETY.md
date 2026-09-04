# Bench electrical pre-flight

Companion to `BENCH_PROCEDURE_TEMPLATE.md`. That document governs whether a
result means anything. **This one governs whether the hardware survives to
produce it.**

Nothing here is new discipline. Every rule was learned on this bench, at the
cost of a specific piece of hardware, and the provenance is cited so it can be
argued with rather than obeyed.

**The ledger this exists to stop growing:** J11 top row (H4/F4/A4, permanent,
2026-07-13), the iCESugar, L5 on the Tang dock, `led_out[3:0]` (mechanism
still unknown), and an RP2350-Zero DirtyJTAG programmer (2026-09-04).

---

## Part 0 — Before anything is powered

- [ ] **Every board is mechanically secured.** No board floats loose near
      another board's headers.
      *Provenance, 2026-09-04: an RP2350-Zero drifting near the Wukong's
      headers is the leading explanation for its death. Its castellated edge
      carries VBUS, 3V3, GND and GPIO; any contact bridges two powered systems
      arbitrarily. The symptoms — BOOTSEL reset, brownouts under sustained USB
      load, clean wiring measurements afterwards, and an entirely unharmed FPGA
      — fit a momentary short of the programmer's own supply better than any
      wiring fault. Two prior hypotheses (a colour-line short, a mains-earth
      ground loop) both survived contact with the evidence less well.*

- [ ] **Series resistors present** on every MCU→FPGA signal: 100–200 Ω on
      JTAG (TCK/TMS/TDI/TDO), 100 Ω on SPI.
      *Provenance: J11's top row took confirmed backfeed damage without them.
      Note the limit — they protect signal lines, and do nothing about a fault
      returning through ground.*

- [ ] **Nothing external can source current inward.** VGA pin 9 (+5 V) and DDC
      (12/15) clipped and insulated; no monitor, PSU or peripheral able to
      drive a bank pin.

- [ ] **Adjacent header pins read open** on any hand-built harness, board off.
      Resistors soldered flat — no free legs adjacent to live pins.

---

## Part 1 — Power sequencing

**Up:** FPGA board first → MCU/programmer connected second.
**Down:** exact reverse.
*Provenance: `BENCH_BOM.md` §4. Never leave an MCU powered against an
unpowered target.*

Prefer **one mains outlet** for host, FPGA supply and any display. A
battery-powered laptop is better still: it removes a mains earth from the
system entirely.

---

## Part 2 — Before trusting any measurement

- [ ] **Positive control first.** Flash a known-toggling bitstream on the probe
      point before believing a "no signal" reading.
      *Provenance, 2026-09-04: `J10IDENT` — every J10 pin at a distinct
      frequency — repeatedly caught probes that had lost contact, twice while
      the alternative was debugging RTL for a wiring fault.*

- [ ] **Never trust a pin map from a datasheet or vendor listing.** Measure it.
      *Provenance, 2026-09-04: the QMTech README and the LiteX platform file
      list J10's pins in opposite orders and neither states which is physical.
      Two wrong pin maps were issued from documentation before the question was
      settled by experiment.*

- [ ] **Verify a harness end to end before connecting a display or peripheral.**
      Probe at the far connector with the ident bitstream loaded.

---

## Part 3 — Stop conditions

**Stop at the FIRST anomaly. Do not retry.**

*Provenance, 2026-09-04: a programmer showing one BOOTSEL reset was retried
through three further failures and did not survive. The first brownout was the
warning; the retries were what turned it into a dead board.*

Stop immediately on any of:

- USB errors from the programmer (`usb bulk write failed`, `fails to open`)
- An MCU entering BOOTSEL unprompted
- Any device disappearing from `lsusb`
- Sync, link or comms lost at the moment something was physically connected

Then: **power down before diagnosing.** Do not probe a live rig that has just
misbehaved.

---

## Part 4 — Reduce exposure

- **Disconnect the programmer once the bitstream is loaded.** SRAM
      configuration persists while the FPGA stays powered; the programmer is
      only needed to write it. Removing it eliminates the shared ground, the
      ground-loop path, and any chance of mechanical contact — for free.
- **Keep a spare programmer flashed and in a drawer.** Attrition stops being a
      blocker when it is a five-minute swap. RP2350 build recipe is in
      `SESSION_HANDOVER_2026-09-04.md` §3.
- **A USB isolator** (~£15, ADuM3160 class) on the programmer breaks the
      mains-earth loop. Full Speed is sufficient — RP2040/RP2350 USB is Full
      Speed. Do **not** put the fx2lafw analyzer behind one; it is High Speed.

---

## Part 5 — After an incident

1. **Do not conclude a cause from one correlation.** Three separate mechanisms
   were confidently proposed on 2026-09-04 before the mechanical one fitted.
2. **Check the FPGA first** — `openFPGALoader --detect`. It has survived every
   incident so far; knowing that early narrows the search.
3. **Measure before theorising.** Adjacent-pin continuity, each line to ground,
   each line to its neighbour. A clean measurement is a real result.
4. **Record it here** with provenance, so the next session inherits the lesson
   rather than the loss.
