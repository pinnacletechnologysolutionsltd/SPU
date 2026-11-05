# SPU southbridge Rev 1 — schematic candidate

Status: **DRAFT; NOT FOR FABRICATION**. Owner-authorized schematic exploration,
2026-11-05. This is a separate alternative to the comparator/bus-switch
[Rev B adapter](../bench_adapter/bench_adapter_spec.md), not an amendment or
qualification of that design. No layout, Gerbers, purchases or hardware operations
are included. Existing bench-adapter files are untouched.

Open [the schematic](southbridge_rev1_candidate.kicad_sch) directly in KiCad 10,
or read [the PDF](review/southbridge_rev1_candidate.pdf).
[The BOM](bom.csv), [ERC report](review/erc.rpt),
[SVG](review/southbridge_rev1_candidate.svg) and
[exported netlist](review/netlist.xml) accompany it. All symbols and footprints
use standard KiCad libraries; no project-local library is required.

## Requirements and limits

- R1: With either board unpowered and the other operating, keep both endpoints
  within their electrical ratings and avoid unintended powering via SPI.
  The three translators are a **candidate** for this property, not bench proof.
  Isolation has finite leakage; zero current is not the acceptance criterion.
- R2 (separate): Disable communication until both domains are within their
  operating ranges. **Not implemented**: there is no power-good detector, OE or
  approximately 2.95 V undervoltage threshold. This candidate cannot replace
  the existing interlock if that threshold remains mandatory.
- Dedicated four-wire, single-target SPI, mode 0. MISO at the Pico is actively
  driven even while CS# is high; it cannot be shared with another SPI slave.
- Pico is USB powered. A1 pin 36 supplies PICO_3V3. J2 pin 6 supplies
  TARGET_VCCO_3V3 from the FPGA's actual bank rail. They are never tied.
  Common ground is required; this is not galvanic isolation or arbitrary
  hot-plug/incorrect-voltage protection.
- No UART, flash-programmer or other cross-board connection is included.
  Such paths require their own power-domain review before use.

## Rev 1 power distribution and planning budget

Owner direction: USB powers Pico 2, whose onboard regulator supplies the
breakout's small 3.3V loads. No additional regulator or external power input
is planned for Rev 1. Wukong retains its own supply; TARGET_VCCO_3V3 is only
for the translator B-side circuitry and target-side pulls, never peripherals.
The grounds are common. The translators form a power-domain interface, not
a galvanic isolation barrier.

The [official Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf),
section 3.1, recommends less than 300mA external load on pin 36; available
current depends on RP2350 load and VSYS voltage. This is not 300mA of
unconditionally spare capacity. Our initial external-load ceiling is **100mA**,
subject to checking USB source/cable capacity, Pico workload and temperature.
It covers simultaneous peaks and startup, not just average module currents.

The following are **proposed allocation slots**, not measured currents,
manufacturer limits or evidence that a module fits. Exact modules are not yet
selected. Unused slots remain headroom; exceeding a slot requires revisiting
the budget. The same table is supplied as [CSV](power_budget.csv), with a
summary on the KiCad schematic.

| Load on Pico pin 36 | Planning slot (mA) | Evidence / implementation status |
|---|---:|---|
| Translator A-sides, Pico-side bias, signal-load allowance | 10 | Circuit drawn; switching current and loads unmeasured |
| INA226 module, including its LEDs/pull-ups | 5 | Module compatibility and total current TBD; not drawn |
| Small I2C sensors, including all pull-ups | 10 | Exact modules and peak currents TBD; not drawn |
| SPI storage total, including startup/write bursts | 50 | Flash or microSD selection TBD; not drawn; no card approved |
| External indicator LEDs | 2 | LED/resistor selection TBD; not drawn |
| Unallocated margin | 23 | Keep available for uncertainty and transients |
| **Total envelope** | **100** | 77mA allocated + 23mA margin; not a load measurement |

The Pico's own RP2350/onboard loads are outside this *external* table but
still consume regulator and USB capacity. Translator dynamic current depends
on frequency, capacitance and driven loads; quiescent current alone cannot
close the budget. B-side currents and target-side bias belong in Wukong's
separate bank-rail budget, which is still TBD. Decoupling inrush must also be
considered in both domains.

Before approving any module, record its exact part/revision, 3.3V supply and
logic compatibility, documented maximum continuous and startup/burst current,
measured peak under simultaneous activity, and its rail. Sum the concurrent
peaks; retain margin and demonstrate acceptable voltage droop at the farthest
header under storage writes and maximum intended Pico activity. A 50mA slot
does not mean an arbitrary microSD card fits; select a documented device or
revise/defer that option. Generic 5V microSD modules with onboard regulators
or level shifters must not be assumed to work from 3.3V.

A logic-analyser header exports signals and ground only; it does not supply
the analyser, which has its own USB power. Future peripheral headers will
use Pico-derived 3.3V and ground. Provision a peripheral disconnect jumper,
indicator, and labelled PICO_3V3 / TARGET_VCCO_3V3 / GND test points when
capturing the peripheral sheet; these are not present in this interface-only
candidate. Current limiting remains a component/cost decision, not an
implemented feature. Disconnecting peripheral power alone can leave GPIO
backfeed paths; the future sheet must handle those paths too.

ESP32/radio modules and motors/servos/actuators have no allocation in this
revision. External powered devices must not feed either 3.3V rail or bypass
the protected FPGA interface. Industrial 12V/24V inputs, regulators and
protection belong to a later variant. No physical power testing has run.

## Exact identities and pin connections

Sources: TI [SN74LVC2T45, SCES516N](https://www.ti.com/lit/ds/symlink/sn74lvc2t45.pdf)
and [SN74LVC1T45, SCES515N](https://www.ti.com/lit/ds/symlink/sn74lvc1t45.pdf),
both revised June 2024, sections 4, 5.5, 7.3.5–7.3.6 and 8;
[Raspberry Pi Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf),
pinout/mechanical specification. Checked 2026-11-05.

| Ref | MPN | Package / KiCad footprint |
|---|---|---|
| A1 | SC1631, Raspberry Pi Pico 2 | Module:RaspberryPi_Pico_Common_THT; fit two 1x20 sockets |
| U1 | SN74LVC2T45DCUR | DCU VSSOP-8; Package_SO:VSSOP-8_2.3x2mm_P0.5mm |
| U2, U3 | SN74LVC1T45DBVR | DBV SOT-23-6; Package_TO_SOT_SMD:SOT-23-6 |

A1 uses KiCad's RaspberryPi_Pico symbol, whose description explicitly supports
Pico 2. The common THT footprint supports the socketed module. Mechanical fit,
USB clearance and connector orientation still require review before layout.

| Pin | U1 | U2 | U3 |
|---|---|---|---|
| 1 | VCCA = PICO_3V3 | VCCA = PICO_3V3 | VCCA = PICO_3V3 |
| 2 | A1 = P_SCK | GND | GND |
| 3 | A2 = P_CS_N | A = P_MOSI | A = MISO_DRV |
| 4 | GND | B = MOSI_DRV | B = F_MISO |
| 5 | DIR = PICO_3V3 | DIR = PICO_3V3 | DIR = GND |
| 6 | B2 = CS_DRV | VCCB = TARGET_VCCO_3V3 | VCCB = TARGET_VCCO_3V3 |
| 7 | B1 = SCK_DRV | — | — |
| 8 | VCCB = TARGET_VCCO_3V3 | — | — |

R1: SCK_DRV to F_SCK; R2: CS_DRV to F_CS_N; R3: MOSI_DRV to F_MOSI;
R4: MISO_DRV to P_MISO. All are 100 ohm starting values, placed at the
translator output in layout. They are termination/damping components, not
sufficient powered-off protection on their own. Layout/edge measurements may
require adjustment; no SPI speed or cable-length qualification is claimed.

R5/R9: 10k CS# pull-ups to PICO_3V3 / TARGET_VCCO_3V3 respectively.
R6/R10: 10k SCK pull-downs; R7/R11: 10k MOSI pull-downs;
R8/R12: 10k MISO pull-downs, on Pico / target sides respectively.
These define translator inputs during MCU reset or FPGA configuration.

C1/C2 bypass U1 VCCA/VCCB; C3/C4 bypass U2; C5/C6 bypass U3.
Each is 100nF, X7R, at least 16V, 0805, to GND. Place each at its supply
pin with a short return. All resistors use 0805 footprints.

## Physical cable and firmware profile

| Signal | A1 Pico GPIO / physical pin | Adapter J2 | This Wukong J11 / FPGA ball |
|---|---|---|---|
| CS# | GP17 / 22 | 1 | 7 / J4 |
| MOSI | GP19 / 25 | 2 | 9 / B4 |
| MISO | GP16 / 21 | 3 | 10 / B5 |
| SCK | GP18 / 24 | 4 | 8 / G4 |
| GND | All digital ground pads | 5 | 11 |
| Target bank 3.3V | **Never Pico pin 36** | 6 | 12, provisional pending rail verification |

J2 is a 1x6 2.54mm male header. The cable is mapped, **not straight-through**
to Wukong or Tang. Confirm pin 1 and viewing orientation physically.
A1 pin 33 (AGND) is unused on this carrier; analog circuitry is not connected.
VBUS, VSYS, 3V3_EN, RUN, ADC_VREF and unused GPIOs are explicitly NC.
The module remains powered by its own USB connector.

The GP16–19 profile matches
[the full-size Pico firmware](../../rp2350/rp2350_su3_j11_smoke.c), which sets
CPOL=0/CPHA=0. It differs from older RP2350-Zero GP0–3 wiring; use a matching
firmware build. The live source currently requests 25kHz; historical 2MHz
operation does not qualify this new circuit at 2MHz.
The remapped target balls follow
[the current Artix constraints](../../boards/artix7/spu_a7_100t.xdc).
Do not reuse this unit's damaged J11 upper-row pins.

## Electrical review holds and proposed bench acceptance

1. Verify the exact Wukong revision's schematic and continuity: J11-12 must
   track VCCO_35, including shutdown. The XDC comment is supporting provenance,
   not independent electrical proof. J2-6 is now a supply, not sense-only;
   check its current capacity, rail tolerance and the actual endpoint ratings.
2. TI specifies high impedance when either supply is at ground and discusses
   glitch-free sequencing in either order. Neither establishes a 2.95V UVLO.
   Review partial-rail behaviour against the FPGA/RP2350 operating and absolute
   maximum limits before making a brownout safety claim.
3. Begin any later authorized bench work with independent current-limited
   supplies and dummy inputs/loads, without the FPGA. Check all four steady
   power combinations, drive every input high and low, and measure off-domain
   signal current and rail uplift. Include a disconnected/floating supply case;
   a supply clamped to 0V can conceal back-powering.
4. Set a numeric acceptance budget for endpoint injection current and off-rail
   rise from actual endpoint specifications before testing. Record instrument
   resolution and loads. Compare translator leakage with the precise TI table
   conditions; do not treat a total board-current reading as a per-pin Ioff test.
5. Scope both rails and all SPI lines during startup, shutdown and unexpected
   target loss during traffic; include slow ramps, repeated power cycles and
   MCU reset / FPGA unconfigured states. Check rail-relative overshoot and
   logic margins as well as decoded transactions. No FPGA connection until
   the electrical review and dummy-load checks pass.

These are proposed checks, not executed tests or authorization to power hardware.
Manufacture remains on hold pending electrical and mechanical review and bench
acceptance. Software ERC cannot establish either requirement electrically.

## Reproduce schematic checks

Run from the repository root, using KiCad CLI 10.0.7 and Python 3:

```bash
kicad-cli sch erc --exit-code-violations -o hardware/pcb/southbridge_rev1_candidate/review/erc.rpt hardware/pcb/southbridge_rev1_candidate/southbridge_rev1_candidate.kicad_sch
kicad-cli sch export netlist --format kicadxml -o hardware/pcb/southbridge_rev1_candidate/review/netlist.xml hardware/pcb/southbridge_rev1_candidate/southbridge_rev1_candidate.kicad_sch
python3 hardware/pcb/southbridge_rev1_candidate/review/check_netlist.py
kicad-cli sch export pdf -o hardware/pcb/southbridge_rev1_candidate/review/southbridge_rev1_candidate.pdf hardware/pcb/southbridge_rev1_candidate/southbridge_rev1_candidate.kicad_sch
kicad-cli sch export svg -o hardware/pcb/southbridge_rev1_candidate/review/ hardware/pcb/southbridge_rev1_candidate/southbridge_rev1_candidate.kicad_sch
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- hardware/pcb/southbridge_rev1_candidate
```

2026-11-05 results: ERC **0 errors, 0 warnings**; exported-netlist check
**74 connected pins, 23 components**, passive values and exact module/translator
MPNs/footprints passed. PDF rendered and inspected; SVG exported. Initial ERC
identified the standard module symbol's power-output AGND tied to digital
power-output GND plus a redundant GND flag; unused carrier AGND is now NC and
the redundant flag was removed. Final exports and ERC were regenerated.
The checker validates the exported connectivity; rerun export after any edit.

Repository doc audit exited 0 but reported findings outside this new directory
(14 broken links, 30 uncited claims, 3 stale totals, 171 orphans and 1 superseded
status). It scans tracked Markdown and excludes these new untracked files;
a separate direct link check of this README passed. Whitespace checks passed,
including direct checks of new files. CSV line endings and trailing whitespace
in the generated SVG were normalized for repository hygiene. No software/RTL, arithmetic, build flow
or deployed hardware behaviour changed; schematic ERC/netlist/export checks
apply to this draft, not FPGA synthesis or runtime conformance tests.

Source context: HEAD `1d010a648e5a3f75b288143edfcd4a3424a43a8f`, pre-existing
dirty working tree including bench-adapter, firmware and Artix files. This
candidate uses that working-tree pin mapping. Only this new directory was
written during capture. Results are schematic consistency evidence,
not independent electrical review, simulation, synthesis, timing or physical
qualification.


## Review branch preparation

Prepared on `review/southbridge-rev1-translator-candidate`, based directly on
`origin/master` at `4e0d5b9`, in a separate worktree. Only this candidate
directory is included; the original working tree remains untouched. The
master firmware also uses the GP16–19 mapping and 25kHz default.
ERC and the exported-netlist checker passed again in the isolated worktree.
The master-based documentation audit exited 0 with existing findings outside
this directory: 19 broken links, 30 uncited claims, 1 stale total, 121 orphaned
documents and 1 superseded status. These counts describe the master-based
checkout and differ from the original dirty-tree capture above.

No purchasing comparison was performed. Lower cost or superiority over the
power-ready circuit is not established; the two candidates provide different
undervoltage behaviour. Publication of this draft does not release hardware
or supersede the existing design.

Power-plan update validation (2026-11-05): only schematic text annotations,
budget files and review exports changed; electrical connectivity is unchanged.
ERC again reports 0 errors / 0 warnings and all 74 netlist pin checks pass.
PDF was rendered and inspected. The CSV slots sum to 100mA. README local links
and whitespace checks pass. Repository doc audit exits 0 with the same
master-based findings above, except 120 orphans after tracking this README.
No current, voltage-droop or thermal measurements have been made.
