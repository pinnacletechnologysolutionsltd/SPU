# ECP5 OSHWA Deliverable Audit

Date: 2026-07-05

## Verdict

Do not submit the current ECP5 carrier Gerbers to a fab house, and do not submit
the current OSHWA application as a completed hardware product.

The current files are useful as an OSHWA concept package and layout generator
prototype, but they are not yet a manufacturable ECP5 carrier board. The KiCad
files now parse, but the electrical design is not coherent and the board fails
KiCad DRC.

## Local Audit Commands

```bash
kicad-cli sch erc hardware/pcb/spu13_ecp5_carrier.kicad_sch \
  --output /tmp/spu13_ecp5_erc.rpt

kicad-cli pcb drc hardware/pcb/spu13_ecp5_carrier.kicad_pcb \
  --output /tmp/spu13_ecp5_drc.rpt
```

## Results

| Item | Status | Notes |
|---|---:|---|
| Hardware license | Pass | `hardware/LICENSE` is CERN-OHL-W-2.0. |
| Software license | Pass | `software/LICENSE` is MIT. |
| DCO | Pass | `CONTRIBUTING.md` contains DCO language. |
| BOM exists | Partial | `hardware/pcb/spu13_ecp5_carrier_bom.csv` exists, but it does not match the actual schematic/PCB implementation. |
| KiCad schematic parses | Partial | Current file parses as KiCad schematic, but it is based on the Arduino Nano template and contains no real ECP5/RP2350 schematic. |
| KiCad version compatibility | Fail | Docs claim KiCad 8.0, while generated files use KiCad 9/10-era file versions (`20250114` schematic, `20241229` PCB). |
| KiCad ERC | Fail | 27 ERC messages: 4 power-input errors and 23 isolated labels. |
| KiCad PCB parses | Partial | Current board parses, but includes Arduino template footprints/nets and appended placeholder ECP5/RP2350 footprints. |
| KiCad DRC | Fail | 77 DRC violations and 2 unconnected items. |
| Gerber ZIP exists | Partial | Gerbers exist, but they are generated from the failing placeholder PCB and are not fab-ready. |
| OSHWA application | Draft only | The documentation overstates the board as a completed ECP5 carrier. |

## Blocking Findings

1. The schematic is not an ECP5 carrier schematic. It still contains Arduino
   Nano template instances and connector nets such as `D13/SCK`, `A0`, and
   `D0/RX`.

2. The PCB is not routed. It contains Arduino template footprints plus appended
   placeholder footprints for `U100` ECP5, `U200` RP2350, capacitors, and
   fiducials.

3. The board outline is malformed. KiCad DRC reports a self-intersecting
   `Edge.Cuts` outline.

4. The generated Gerber ZIP is not evidence of fabricability. It is only an
   export of the current failing PCB state.

5. The BOM is aspirational. It lists major parts such as ECP5, RP2350, flash,
   USB, and microSD, but those components are not represented by a complete
   routed schematic/PCB netlist.

6. The file-version target is inconsistent. Either standardize on the KiCad
   version that generated the files, or regenerate/backport the project to the
   KiCad version named in the OSHWA documentation.

## OSHWA Readiness

OSHWA certification expects original design files, a public BOM, open
licensing, and documentation sufficient for others to build, modify, and
distribute the hardware. The repository has the licensing scaffolding, but the
actual board design files are not ready.

Do not claim "10/10 OSHWA requirements met" until:

1. The schematic is a real ECP5/RP2350 design, not a template graft.
2. The PCB has a valid closed outline.
3. The KiCad file version matches the documented design environment.
4. ERC passes or every remaining warning is documented and justified.
5. DRC passes against the intended fab rules.
6. The BOM is generated from the KiCad design or manually reconciled to it.
7. The Gerber ZIP is regenerated after clean ERC/DRC.
8. Assembly notes and bring-up instructions match the actual board revision.

## Recommended Scope

Reframe this board as:

> SPU-13 ECP5-85F open evaluator for RP2350 southbridge transport, RPLU2 table
> hydration, single-M31 Pade evaluation, and SPI-visible golden trace readback.

Do not frame it as:

> Full dual SPU-13 plus SPU-4 satellites plus full RPLU2 plus Lucas MAC with
> margin.

The full integrated image remains an Artix-7 200T / Kintex-class target.

## Next Work Items

1. Create a real schematic from scratch:
   - ECP5 bank power and decoupling
   - RP2350 southbridge
   - JTAG and ECP5 configuration flash
   - RP2350 USB/debug
   - RPLU table flash or microSD path
   - one or two PMOD/debug headers
   - reset, boot-mode, and clocking
   - use `docs/ecp5_evaluator_ee_handoff.md` as the starting handoff spec

2. Use a conservative layer stack:
   - Four layers minimum for an ECP5 BGA evaluator
   - solid ground plane
   - dedicated power plane or wide pours
   - short local decoupling routes

3. Keep the evaluator RTL small:
   - SPI/PIO southbridge link
   - config hydration
   - one shared M31 multiplier
   - RPLU2 Pade evaluator
   - QR/result readback

4. Regenerate Gerbers only after `kicad-cli sch erc` and `kicad-cli pcb drc`
   are clean enough for the selected fab process.
