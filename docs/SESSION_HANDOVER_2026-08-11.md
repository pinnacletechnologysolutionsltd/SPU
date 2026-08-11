# Session handover — 2026-08-11

Previous: [`SESSION_HANDOVER_2026-08-10.md`](SESSION_HANDOVER_2026-08-10.md).

## One-line state

**`bench_adapter` schematic went from Rev A-with-gaps to complete and
verified — 37 components, every footprint assigned, 0 ERC errors.** The Rev B
interlock is drawn, the Pico 2 footprint exists, and three separate captures
were found wrong against real parts or real datasheets. **None of it is
committed.** No silicon, no bench.

## ⚠ Commit before opening KiCad

The `.kicad_sch` is 4,532 lines, ~1,660 of them added by hand this session as
raw s-expressions. **KiCad rewrites the whole file on first save** —
reformatting, reordering, pruning orphaned cache symbols. Open-and-save before
committing and today's design work becomes indistinguishable from the tool's
reshuffling in one diff.

```
 M hardware/pcb/bench_adapter/bench_adapter_spec.md
 M hardware/pcb/bench_adapter/kicad/bench_adapter.kicad_pro
 M hardware/pcb/bench_adapter/kicad/bench_adapter.kicad_sch
 M hardware/pcb/bench_adapter/kicad/bench_adapter_bom.csv
?? hardware/pcb/bench_adapter/kicad/bench_adapter.pretty/
?? hardware/pcb/bench_adapter/kicad/fp-lib-table
```

Two untracked paths need adding explicitly. **Explicit paths only, never
`git add -A`** — GTP shares this worktree.

## What landed (all uncommitted)

| Area | Change |
|---|---|
| JP2 | Two `Conn_01x03` symbols → one `Conn_02x03_Odd_Even`, single designator |
| R5–R12 | Values finally written into the schematic (`54e82ff` only touched docs) |
| Value fields | All 14 remaining designator-as-value fields set |
| Interlock | U1, U2, R13–R17, C1, C2, FLG3 drawn; U1 spliced in series with J2 |
| A1 | Pico 2 footprint created; project footprint library + `fp-lib-table` |
| J6 | Rebuilt as a single 1×08 against the physical module; J9 deleted |

## Three captures that were wrong

### 1. JP2 contradicted its own spec

`bench_adapter_spec.md` §2.2's 2026-07-09 correction says JP2 is a 2×3 block,
"**still one reference designator**", BOM qty 1. The capture had two separate
`Conn_01x03` symbols on two `PinHeader_1x03` footprints — 2× 1×3 in the BOM,
and two poles placeable independently, losing the matched-pair property the
correction exists to create.

The 08-10 handover's proposed fix (`JP2A`/`JP2B` → `JP2`/`JP3`) would have
**frozen the bug**, not fixed it. Now one `Conn_02x03_Odd_Even`, one
designator. **Shunts bridge along the columns (1–3 / 3–5, 2–4 / 4–6), never
across the rows** — across-rows is the default mental model for a 2×3 and is
wrong here; bridging 1–2 shorts `FLASH_MISO_PRE_R` to `FLASH_CS_PRE_R`. That
is now a silkscreen requirement, not a preference.

### 2. J6 would have destroyed the INA226 module

Three sources, three different wrong answers:

| Source | Claimed |
|---|---|
| Schematic | 1×05: SDA, SCL, ALERT, VCC, GND |
| Spec BOM | 6-pin: VCC, GND, SCL, SDA, ALERT, + NC/A0 |
| **Physical part** | **1×08: IN+ IN− VBS ALE SCL SDA GND VCC** |

Seating the real module into the captured 1×05 would have put the 5 V
metering rail onto the I²C lines. J9 is deleted; J6 is one `Conn_01x08`.

**VBS was missing from the design entirely** — the bus-voltage sense input,
on the channel that actually failed on 2026-08-07. Tied to **IN−**, matching
the breadboard rig, so VBUS keeps reading the load-side node. **Do not
re-point it**: `software/datasets/ina226_coarse_monitor_v2.json` is frozen and
has no partial-redo path, so moving the measured node silently breaks
cross-session comparison.

J5's row already guards against this class by naming the module order inline
(`3V3 CS MOSI CLK MISO GND`). §2.5 now does the same for J6. **That convention
is the fix — apply it to every module socket.**

### 3. The interlock spec was wrong in three places

Pinouts taken from [SCDS037K](https://www.ti.com/lit/ds/symlink/sn74cbtlv3125.pdf)
§4 and [SBOS300C](https://www.ti.com/lit/ds/symlink/tlv3011.pdf) Table 5-1.
*A web search summary returned "Pin 6: OUT/V+" for U2 — wrong, and it would
have inverted the safety circuit. Datasheets only.*

- **U2 polarity resolved.** Open-drain OUT pulls low when IN− > IN+, so the
  divider drives **IN− (pin 4)** and REF drives **IN+ (pin 3)**. U1 confirmed
  by Table 7-1: OE H → Disconnect, L → A=B.
- **R16 alone would not have worked — R17 (10 kΩ) added.** REF sources 0.5 mA
  and holds IN+ directly, swamping a 1 MΩ feedback. Positive feedback needs a
  series resistor from REF. Without it the escape hatch that justifies
  choosing TLV3011B over MAX9063 does not exist.
- **§2.1's hysteresis-scaling rule points at the wrong node.** It scales
  against R17, not the sense divider. The divider's *ratio* still refers the
  band up to J2-6 (×2.3725); its *impedance* is irrelevant to hysteresis.
- **TLV3011B already has built-in hysteresis** (V_HYS 2/6/8 mV ≈ 14 mV at
  J2-6). The breadboard doc implies it has none. Bench step 1 should start
  from "there is already ~14 mV".

## Decisions taken

- **U1/U2 mount on DIP breakout carriers**, not bare SMD. Keeps the board
  inside its own "hand-solderable / module carrier" scope, avoids the 0.65 mm
  TSSOP-14 joint, and **replaces the four bypass-link footprints** the 08-10
  Rev A-populate plan called for: fit a wire-link header in U1's socket, swap
  for the real module at Rev B. Populate links **or** U1, never both.
- **FLG3 added on `V3V3`.** Typing the new supply pins `power_in` exposed the
  board's first real ERC *error* — the Pico's 3V3 output is `Bidirectional`,
  so nothing drove the rail. FLG1/FLG2 were on V5_OUT and GND only.
- **J8 stays on the Pico side** of U1, per §2.6's `SPI_*` naming. Target-side
  visibility comes from the §5 test pads.

## Verification status — read before ordering

| Item | Status |
|---|---|
| J5 microSD order | ✅ confirmed against the physical module |
| J6 INA226 order | ✅ confirmed against the physical module |
| U1/U2 pinouts, polarity | ✅ TI datasheets |
| A1 Pico 2 footprint | ⚠ **datasheet-derived, never seen a real part** |
| U1 DIP-14 carrier | ⚠ **adapter not chosen; outline unverified** |
| U2 DIP-6 carrier | ⚠ **adapter not chosen; SOT-23-6 breakouts vary** |
| J3 flash PMOD order | ⚠ **mating cable never recorded anywhere** |

Pico geometry: board 51×21, pitch 2.54, rows 17.78, pin 1→20 = 48.26, **pin 1
sits 1.37 mm from the top edge — the grid is centred**. Derived arithmetically
and measured off the scaled drawing as 1.386 mm; two methods agreeing, but
neither is a physical part. **Print at 1:1 and lay a Pico on it.** The USB
overhang on `F.Fab` is indicative only — not measured; the courtyard reserves
3 mm above the board edge to cover it.

## Canvas map (schematic mm)

| Block | Where |
|---|---|
| Left column | J2 (40,40) J3 (40,80) J4 (40,120) J5 (40,160) |
| A1 Pico | (120,100) |
| **Interlock** | U1 (152.4, 50.8), U2 (152.4, 88.9) |
| Interlock discretes | R13/C1/C2/R16/R17 in a row at y=25.4, x 139.7→190.5 |
| Sense divider | R14 (190.5, 78.74), R15 (190.5, 99.06) |
| FLG3 | (205.74, 25.4) |
| Right column | J6 (220,40) J8 (220,100) T1 (220,140) T2 (220,160) J7 (220,190) |
| JP2 | (88.9, 220.98) — placed on a 2.54 grid, unlike the rest |

## Hazards while working in the GUI

- **127 `endpoint_off_grid` warnings are a live risk now.** A GUI drag can
  snap an off-grid endpoint and silently detach a connection that still looks
  wired. After any session of moving symbols, re-check — and note ERC will
  *not* tell you a wire quietly stopped connecting; export the netlist and
  diff it.
- **Do not let KiCad "rescue" or remap symbols.** Three `lib_symbol_issues`
  are expected: `Local:RPi_Pico2_Module`, `Local:74CBTLV3125`,
  `Local:TLV3011B` live only in the schematic cache with no project symbol
  library. There is nothing to remap *to*; accepting could detach A1/U1/U2
  from their pins. Building a proper project `.kicad_sym` is a fine later
  exercise and is not needed to lay out.

### Regression baseline

```bash
cd hardware/pcb/bench_adapter/kicad
kicad-cli sch erc --output /tmp/erc.rpt --severity-error --severity-warning bench_adapter.kicad_sch
kicad-cli sch export netlist --output /tmp/net.net bench_adapter.kicad_sch
```

**Current: 0 errors.** 127 `endpoint_off_grid`, 9 `pin_to_pin` (A1's
`Bidirectional` GND pins — benign, pre-existing), 3 `lib_symbol_issues`.

## One error of mine this session

Removing the old J6/J9 wire stubs, I matched on the pin-column x-coordinate
(214.92) — which **every** symbol at x=220 shares. It deleted four of J8's
GND stubs. Caught by the removal count coming out 11 against 7 expected;
restored from backup and redone against exact pin coordinates with an
assertion that each removal matches exactly once. J8's ten pins verified
intact afterwards. *Coordinate-based edits to this schematic need to key on
the full point, never one axis.*

## Open

- **Block A** — README disclosure, John's voice. Draft in
  `docs/README_BLOCKS_DRAFT.md`, placeholder at `README.md:18`. Still open
  from 08-10.
- **KiCad, in order:** commit → open → netlist → PCB → place → outline →
  route → DRC → gerbers. **Place J6 first** and let the terminal blocks
  follow; it is now doubly constrained (≥2 mm metering path *and* the Pico's
  I²C/ALERT on one connector).
- **Before gerbers:** the four ⚠ rows above.
- **Ordering:** the combined LCSC + JLCPCB consignment still wants the U1/U2
  adapter listings settled. The ~NZ$10–40 shipping saving stops justifying
  serialisation if layout runs past ~2 weeks — at that point order the
  interlock parts separately.
- **INA226 spare is NOT ordered** — confirmed with John 2026-08-11;
  `BENCH_BOM.md` §2's "being ordered" wording was stale and is now corrected.
  Different supplier track, same 2–4 week lead. It gates the INA226 capture
  work and does **not** depend on the PCB, so it should not queue behind the
  layout.
- **Bench, independent of all the above:** solder the power path →
  characterise with `BENCH_SESSION_2026-08-10_SUPPLY_CHARACTERISATION.md` →
  trim → `init`. Blocked on the harness wire and 1N4001 having arrived.
