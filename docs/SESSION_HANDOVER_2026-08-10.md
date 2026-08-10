# Session handover — 2026-08-10 (evening)

**Written as work landed.** Previous:
[`SESSION_HANDOVER_2026-08-09.md`](SESSION_HANDOVER_2026-08-09.md), whose late
section already spills into 08-10 (claims pass, typestate paper). This document
covers the evening session only.

## One-line state

**Repo-hygiene and bench-prep session, no silicon.** The README now makes only
claims that were executed from a fresh clone before being written down; the
bench track has a fill-in sheet that emits a ledger entry directly; and the
`bench_adapter` values are resolved. Two of my own earlier statements were
wrong and are corrected in the files rather than only here.

## What landed

| Commit | What |
|---|---|
| `de08e02` | README "check it yourself" block, every command verified from a fresh clone |
| `75e56dc` | Bench procedure template, supply-characterisation session sheet, runbook ordering fix |
| `54e82ff` | `bench_adapter` R5–R12 values resolved; flash-bus reasoning corrected |

## README — claims verified, one false claim caught

Prompted by the same os8088 reasoning as the 08-09 late session. The draft
blocks from `docs/README_BLOCKS_DRAFT.md` were **not** taken on trust; every
command was run from a clean clone at `2ecf1c0` first.

- **Regression is 188/188, 0 FAIL, confirmed on a fresh clone** — not only the
  working tree. This matters here specifically: the 2026-07-19 blocker was a
  fresh-clone-only failure (filesystem-order module dedup) that a working-tree
  run cannot see, and Block B claims fresh-clone behaviour.
- `README.md`'s `173/173 at this revision` is replaced with an explicit
  `Total PASS: 188` **and** `Total FAIL: 0`. The number is the falsifiable part;
  the zero-failures assertion is the part that cannot go stale.
- **One claim in the draft was false.** It told readers each Padé bench "prints
  33/33 in its own output above the summary". It does not:
  `run_all_tests.py:437-450` captures each bench's stdout and **discards it on
  pass**, printing only `[name] PASSED`; full output appears only on FAIL. The
  33/33 figure is real — verified directly, both pipeline modes, six vectors —
  so the direct `iverilog`/`vvp` command that actually shows it is given
  instead. **This is the exact failure mode the block exists to prevent, found
  inside the block itself.** Run every command in a "check it yourself" section
  before publishing it.
- Smaller precision fixes: LUCAS is 166,666 macros / **999,996** primitive ops,
  not "1M-step"; the ROTC trace prints **angles 0-35**, not 0-11.
- **`CLAUDE.md` is stale on that last point** — it still says
  `test_rotc_vm_rtl_trace.py` covers "all 12 ROTC angles (0-11)". Left for the
  claims pass rather than fixed piecemeal.
- Historical `173/173` references in dated docs (`DOCS_RTL_CLEANUP_SCOPE_2026-07-16`,
  `ZPHI_KARATSUBA_INTEGRATION_PLAN`) are deliberately **untouched**: they record
  what was true when written.

**Block A — the "how this was built" disclosure — is not written.** It is a
marked `TODO(John)` placeholder after the badges, invisible to readers on
GitHub. It is a statement about how the author works and should be in his
voice. Draft text remains in `docs/README_BLOCKS_DRAFT.md`.

## Bench — template, session sheet, and an ordering correction

- `docs/BENCH_PROCEDURE_TEMPLATE.md` committed (was drafted-uncommitted since
  08-09). Its output is a §3.2e.6-shaped ledger entry, so filling it in
  *produces* the evidence with no transcription step — which is where §3.2f lost
  its clock.
- `docs/BENCH_SESSION_2026-08-10_SUPPLY_CHARACTERISATION.md` is a pre-filled
  instance ready to carry to the bench: prediction (panel reads ~10 % low per
  the 08-06 prior), falsifier (panel agrees within 2 %), 5-row tables per
  quantity, trim step, seal checklist, abort conditions. The positive-control
  field is marked **N/A with a reason** rather than left to imply a control that
  does not exist — this is a characterisation plus one falsifiable claim, not a
  fix-verification.

### Ordering fix — solder BEFORE characterising

`INA226_CAPTURE_RUNBOOK.md` §2 presented the supply characterisation as doable
now because it needs no INA226. True about the *part*, misleading about the
*order*:

- Quantity **#2 (loaded voltage) is measured at the `VIN−`/actuator node** —
  across the power path — and the trim that follows is entirely a function of
  it. At 300 mA through the breadboard's measured 0.96–1.44 Ω that is
  0.29–0.43 V of error, drifting *within* the session.
- **#1 and #3 are robust**: a CC supply holds its clamp regardless of series
  resistance until it reaches voltage compliance.
- Soldering is itself a rig change, so measuring first means measuring twice.

**Order: solder → characterise → trim → `init`.** Recorded in the runbook.

## `bench_adapter` — corrected blocker list

The 08-09 handover is wrong in both directions on this board.

- **Annotation is NOT done** (08-09 was right, I briefly said otherwise and was
  wrong). The `?` never appears in the `.kicad_sch`: KiCad *appends* it at
  export for **invalid** designators. `J6B`, `JP2A`, `JP2B` end in a letter and
  KiCad requires `<prefix><number>`, so they cannot be annotated as named.
  `kicad-cli sch export bom` prints "schematic has annotation errors".
  **Fix: rename** (J6B→J9, JP2A/JP2B→JP2/JP3) and record the mapping, since the
  spec deliberately names them as a matched A/B pair.
  *Method note: grepping the symbol-level `Reference` property is not how KiCad
  resolves designators — trust `kicad-cli`, not a regex over the s-expression.*
- **A1 has no footprint** — `Local:RPi_Pico2_Module`, the main part on the
  board. 08-09 said "29 symbols, footprints assigned"; three have none, and
  FLG1/FLG2 correctly so (power flags). **No Pico footprint ships with KiCad
  10.** Build via the footprint wizard: 2×20, 2.54 mm pitch, 17.78 mm row
  spacing, 21×51 mm outline — verify against RPi's mechanical drawing,
  especially the Pico 2 debug connector. **This is the real layout blocker.**
- The `Local:` symbol exists **only** as the `lib_symbols` cache inside the
  `.kicad_sch`. No project sym-lib-table, no `Local` entry in the global one, so
  it is not reusable on a future board unless saved out.

### ERC baseline (KiCad 10, errors + warnings)

**145 violations, all warnings, zero errors.** Regenerate with:

```bash
cd hardware/pcb/bench_adapter/kicad
kicad-cli sch erc --output /tmp/erc.rpt --severity-error --severity-warning bench_adapter.kicad_sch
```

| Count | Type | Meaning |
|---|---|---|
| 135 | `endpoint_off_grid` | Consequence of the programmatically-generated schematic. Connectivity is fine, but GUI drags can snap and silently detach a connection that looked wired. |
| 8 | `pin_to_pin` | A1's GND pins typed `Bidirectional` instead of `Power input`. Symbol bug, benign, clears all 8. |
| 1 | `lib_symbol_issues` | The cache-only `Local` library. Expected. |
| 1 | `isolated_pin_label` | `TARGET_3V3_SENSE` reaches one pin — it goes to U2, which does not exist. See below. |

### The schematic is Rev A; the spec describes Rev B

29 symbols, and **none** of them are U1 (74CBTLV3125PGG bus switch), U2
(TLV3011BIDBVR comparator) or any decoupling capacitor — all of which
`bench_adapter_spec.md` calls *mandatory*. Consistent with `BENCH_BOM.md` §4 and
`INA226_SESSION_HANDOFF.md` deferring the power-ready interlock, but the spec
was never reconciled.

**Decision 2026-08-10 — not yet reflected in the spec or schematic: lay out the
full Rev B, populate as Rev A.** Footprints for U1, U2, the 140 k/102 k divider,
the 10 k OE pull-up and decoupling go on the board; the ICs are not fitted.
Rationale: no time pressure on the board, and a second fab run to add the
interlock later costs more than carrying the footprints now.

**This requires four bypass links across U1's channels** — plain THT resistor
footprints fitted with wire links. The bus switch sits *in series* with all four
J2 signals, so an unpopulated U1 breaks the link entirely. Populate the links
**or** U1, never both.

Validate the interlock on the breadboard first
(`hardware/pcb/bench_adapter/power_ready_interlock_breadboard.md`); the 1 MΩ
hysteresis value is deliberately unresolved until measured. **Until silicon says
otherwise, do not describe the board as having a power-ready interlock merely
because the footprints exist.** With the ICs unpopulated, J2's protection is the
100 Ω series resistors alone, which the spec says cut fault current ~3× rather
than preventing the condition.

### Values resolved (`54e82ff`)

| Ref | Value | Note |
|---|---|---|
| R1–R4 | 100 Ω | unchanged |
| R5–R8 | **33 Ω** | flash-PMOD series — **not** 100 Ω |
| R9, R10 | 10 kΩ | CS pull-ups |
| R11 | 1 kΩ | PWR LED, **green**, off 5 V (~2 mA) |
| R12 | 330 Ω | ACT LED, **red** — colour is an electrical constraint |

**R5–R8: my earlier `BOM updates.txt` note said 100 Ω and was wrong.** It argued
they were "the same fix as R1–R4" and that a uniform board was worth having.
The spec already had the right answer at §2.1: the 100 Ω on J2 caps fault
current into an FPGA pin whose board can be powered down while the Pico keeps
driving — the damage that actually happened on the Wukong J11. J3's flash is
powered *by this adapter*, so no unpowered-independent-domain scenario exists.
Uniformity is not an engineering reason and would have silently overridden a
documented, reasoned decision.

**R12 must be red or amber.** John's LED stock is modern InGaN at Vf ≈ 3.0 V.
Off a 3.3 V GPIO that leaves ~0.3 V before the RP2350's own output drop at 4 mA
(0.1–0.3 V more), against ±0.2 V part-to-part Vf spread — comparable to the
whole budget. The result is not "dim but working", it is unpredictable between
parts from one reel. Red/amber are AlGaInP and stay at Vf ≈ 1.9–2.1 V however
modern. Rejected alternative, recorded in both the spec and the BOM notes so it
is not re-proposed: driving from 5 V and sinking with GP14 — it appears to work
because 5 − 3.3 = 1.7 V is below the forward drop, but places a 5 V rail one
failure away from a non-5 V-tolerant pin.

## Fab economics (checked 2026-08-10)

Figures scatter ~10× across sources and are mostly dated — **use the quote
calculator, which takes dimensions and needs no gerbers.** Good enough to size
the decision: 2-layer 5-off at ~80×60 mm is ~US$2 of fab; **shipping to NZ
dominates**, ~US$5 economy to ~US$25 express. All-in ≈ **NZ$20–50, 2–4 weeks on
economy**. No rush → economy.

**LCSC is JLCPCB's sibling and can combine shipping.** Settle the Rev B part
list before ordering boards so U1/U2 ship with the PCBs rather than as a second
consignment.

## Two errors of mine this session

Both changed the work, both are corrected in the files and not only here:

1. **"Annotation is done"** — false; see above. Caused by reading the
   symbol-level `Reference` property instead of asking `kicad-cli`.
2. **"R5–R8 should be 100 Ω"** — false; the spec's 33 Ω was correct and
   reasoned, mine was justified by uniformity, which is not a reason.

## Open

- **Block A** — README disclosure, John's voice. Draft in
  `docs/README_BLOCKS_DRAFT.md`, placeholder in place.
- **KiCad, in order:** confirm Rev B-layout/Rev A-populate scope → rename the
  three designators and annotate → set R5–R12 → *(optional)* fix A1's GND pin
  types → **create the Pico 2 footprint and assign it to A1** → re-run ERC and
  export BOM → netlist → PCB → place → outline → route → DRC → gerbers. The
  footprint is where the hours are.
- **Bench, independent of all the above:** solder the power path (harness, star
  ground, flyback at the motor) → characterise using the session sheet →
  trim to ~3000 mV at load → `init` with the measured limit, **which freezes the
  rig** → INA226 when the R100 spare arrives.
- **Zenodo** — typestate paper; tag a release first, citations are
  repo-relative and §3.2g renumbered on the 09th.
- **Composition silicon trace** — still the last piece of policy §5; needs SOM1
  frames at the bench. Shared datapaths stay deferred until it exists.
- **Claims pass covers two files.** `knowledge/`, `README.md` and the four
  papers are untouched; the repo-wide population is in the hundreds. `CLAUDE.md`'s
  ROTC angle count is a known instance.
- **Do not `pack` `spu_a7_100t_RPLU2PADE`** until rebuilt — its `.json`/`.fasm`
  are from a pipelined non-closing build that overwrote the canonical name.
- **Padé 50 MHz is closed negative.** Do not reopen as a timing tranche.
