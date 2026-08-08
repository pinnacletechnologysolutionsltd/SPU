# TENSEGRITYLINK four-act campaign — Karatsuba candidate as shipped default

**Purpose:** close criterion 5 of
[`ZPHI_KARATSUBA_SWAP_CRITERIA.md`](ZPHI_KARATSUBA_SWAP_CRITERIA.md), the only
unmet criterion for a configuration that has been the production default since
`c1fe58f` (2026-07-23).

**This is not new procedure.** Wiring, pin profile and console commands are in
[`SOUTHBRIDGE_SPI_PROTOCOL.md`](SOUTHBRIDGE_SPI_PROTOCOL.md) — J11 bottom row,
GP1/GP2/GP3/GP0 to pins 7/8/9/10, 100 Ω series on all four signals. This
document adds only what that section does not carry: the campaign structure
and the acceptance bar.

## What is being closed, and why it is not optional

`hardware_evidence.md` §3.2l records the four acts reproduced three times on
2026-07-19 — **with the four-product reference multiplier**, bitstream
`30381825…`. Four days later the default became the three-product candidate.
The §3.2l entry states the `TENSEGRITYLINK` half "remains open, gated on the
power-ready interlock"; that interlock stopped gating anything on 2026-08-04.

So the shipped configuration has never had its transactional half proven.
Criteria 1-4 are met, and this is the remainder.

## Artifact under test

    build/spu_a7_100t_TENSEGRITYLINK_ZK1_S1.bit      3,825,935 bytes
    SHA-256: 40373ab866aa4cdc8a5b563a4f378436e99989b3220d3e73e7f1a7e2f2fe5e0b

Packed 2026-08-09. Confirm this hash at load time; if it differs, something
rebuilt underneath you and the run is not evidence for this artifact.

**Seed 1 is deliberate, not a pick.** `A7_SEED` defaults to 1, so this is what
an ordinary `build_a7.sh 100t tensegritylink` produces — and the point of this
campaign is to evidence what ordinary builds ship, not the seed that measured
best. For the record its post-route guard Fmax is 46.63 MHz against the 25 MHz
constraint; the candidate arm ranged 31.46-52.42 across ten seeds.

Packed from the routed artifact of the 2026-08-08 sweep, so the routed design
is bit-identical to the one measured there.

## Firmware

    cmake -S hardware/rp2350 -B build/rp2350_tgr \
      -DPICO_BOARD=pico2 -DSPU_RP2350_ZERO_HEADER_SPI=ON
    cmake --build build/rp2350_tgr --target rp2350_spu_diag -j
    picotool load -f build/rp2350_tgr/rp2350_spu_diag.uf2 && picotool reboot -f

`SPU_RP2350_ZERO_HEADER_SPI=ON` selects GP0 MISO / GP1 CS / GP2 SCK / GP3 MOSI,
which is the mapping the protocol doc specifies for this spin. Diag SPI baud
defaults to 125 kHz — far below the `clk_fast/6` ceiling, leave it alone.

**Rebuild rather than reusing a stale `.uf2`.** The same trap applies here as
to the LUCAS demo: an old build in a stale directory carries old defaults.

## SD card — four traps found on 2026-08-09, all of them cost time

The RP2350's microSD is `spi1`: **GP10 SCK, GP11 MOSI/DI, GP12 MISO/DO,
GP13 CS/DAT3**, separate from the J11 link on GP0-GP3. Verified in the built
firmware's `flags.make`, not just the CMake defaults.

1. **`ERR no SD card` says nothing about the J11 wiring.** The two buses are
   independent; the link can be perfectly healthy (`ping` → `OK pong`) while SD
   fails.
2. **Supply voltage: check the module type before connecting.** A *bare passive*
   adapter is 3V3-native. A *module with chips on it* (regulator + level
   shifter) needs 5 V. Getting this backwards can destroy the card, and on a
   bare adapter it also puts 5 V onto a **non-5V-tolerant** RP2350 GPIO via the
   card's DO line — the same damage class as the J11 backfeed that retired pins
   1-3, with no series resistors on these lines. On 2026-08-09 a 3V3 bare
   adapter was briefly run at 5 V; the card survived, but treat that as luck.
3. **`sdinit` passing does not mean reads work.** Init runs at 400 kHz
   (`spu_sd.c:181`) and only then switches to `SPU_SD_BAUD_HZ`, 8 MHz by default
   (`spu_sd.c:288`). Init-passes-then-reads-fail is the signature of wiring that
   cannot sustain the post-init rate. Rebuild lower to test:
   `-DSPU_SD_BAUD_HZ=1000000`.
4. **Read the FatFs code, not the message.** `sdcat` reports the raw `FRESULT`:
   `1 = FR_DISK_ERR` (I/O failure), `4 = FR_NO_FILE`, `5 = FR_NO_PATH`. A
   `res=1` is *not* a missing file, and `tgrload`'s friendlier
   `ERR TGR1 file not found` collapses every one of these into one string.

**Console diagnostics available:** `sdprobe` (reports the pin map and MISO
float/pullup/pulldown state), `sdinit`, `sdcat [path]`, `sddrive <cs> <sck>
<mosi>` for metering continuity at the card's pins.

**Fixture path:** the fixtures live under a `TGR/` directory on the bench card,
so the command is `tgrload TGR/00_canonical_balanced.tgr 0`, not a bare
filename. Confirm the actual names on the card before the run.

`tgrload` reads fixtures from SD. Copy both required fixtures:

    tools/build/tensegrity_vectors/00_canonical_balanced.tgr
    tools/build/tensegrity_vectors/06_fault_not_in_equilibrium.tgr

Regenerate them with `python3 tools/gen_tensegrity_vectors.py` if absent.
Prove SD separately with `spu_sd_test.uf2` before relying on it — a failed
`tgrload` caused by SD, not by the link, would be indistinguishable at the
console.

## The four acts — one run

| Act | Command | Expected `tgrstatus` |
|---|---|---|
| 1 admission | `tgrload 00_canonical_balanced.tgr 0` | `state=2 fault=0 stage=8 vector=0 flags=0x08 error=0` |
| 2 mechanical negative | `tgrload 06_fault_not_in_equilibrium.tgr 6` | `state=8 fault=5 stage=8 vector=6 flags=0x08 error=0` |
| 3 corrupt-payload rollback | `tgrloadbadcrc 06_fault_not_in_equilibrium.tgr 6` | `state=8 fault=5 stage=0 vector=6 flags=0x09 error=7` |
| 4 recovery | `tgrload 00_canonical_balanced.tgr 0` | `state=2 fault=0 stage=8 vector=0 flags=0x08 error=0` |

All four lines also carry `nodes=12 edges=30 received=468 expected=468`.

Act 3 is the one that matters most: the firmware flips a payload byte in RP RAM
while emitting a *valid* transport CRC-8, so `error=7` proves the FPGA's
independent TGR1 CRC-32 caught it, and `vector=6` proves the previously
admitted verdict survived the rejection.

## Acceptance bar

**N ≥ 10 complete four-act runs**, all four lines bit-identical to the table
above on every run. One deviating line fails the campaign — record it and stop
rather than re-running until it looks clean.

**On the positive control.** Criterion 5 requires one, and here it is
*internal*: acts 2 and 3 are the control. Act 2 must produce
`state=8 fault=5` and act 3 must produce `error=7`; if either ever silently
returns the act-1 line, the rig is not discriminating and a run of clean
`PASS`es would mean nothing. This differs from the Padé campaign, where the
control had to be a separate known-bad bitstream. **State this reasoning in the
ledger entry** rather than leaving "positive control" ticked by assertion.

## Power sequencing — the rule that cost J11 pins 1-3

FPGA powered **first**, RP2350 connected **after**. On the way down, RP2350
off/disconnected **first**. J11 **bottom row only**; the top row is retired.
`usbreset 1209:c0ca` before every DirtyJTAG load — the adapter stalls under
sustained use and silently voided three campaigns on 2026-08-04/05.

## Deliverable

A new `hardware_evidence.md` section in the §3.2e.6 format — Date, Scope,
build/load commands, bitstream SHA-256, **raw** console lines from at least the
first and last run plus the pass count, Interpretation. Then update §3.2l,
whose "remains open, gated on the power-ready interlock" sentence is stale on
both counts once this lands.

If any run deviates, the deliverable is the deviation, logged. A four-act
sequence that fails on the shipped default is a more valuable finding than a
tenth clean pass.
