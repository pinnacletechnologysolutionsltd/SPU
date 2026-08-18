# Session handover — 2026-08-18

One programme (SPU-4 edge node), three threads that turned out to be one
connected arc: build a real interface for the SOM edge classifier → realize
nothing trains its weights → build the trainer → realize there's no honest
way to test it → build held-out cross-validation → realize the frozen
real-data evaluation gate never named this classifier at all → fix that →
realize the gate had no code behind it yet → write that code. Each step
surfaced the next gap rather than being planned upfront.

Also: the bench parts (INA226 ×2, IR encoder, logic analyzer) were ordered
today, and the Sipeed dock schematics were pulled to resolve a UART pin
question — resolving it surfaced a real, previously-unnoticed pin-contention
risk between the dock's onboard debugger and a legacy RP2350 bodge-wire
scheme, confirmed clear on this board specifically.

Written after the session closed, in one sitting — no incremental-handover
staleness risk this time.

## 1. Repository state

- `master`, clean except pre-existing unrelated `hardware/rp2040/build/`
  CMake-cache drift (not touched, flagged, not mine to clean up).
- **9 commits ahead of origin, none pushed.** 7 from today, 2 carried from
  the prior session.
- Regression **209 PASS / 0 FAIL** (was 203 at session start).

| Commit | Change |
|---|---|
| `752aa2c` | Fix: stale `S=07` should be `S=06` in the fixed SOM edge probe's docs |
| `2e20f9f` | **Interactive UART bench probe** — RTL, testbench, host client, demo CLI |
| `3a4f650` | **`spu4_som_edge_trainer.py`** — the 4-node trainer that didn't exist |
| `edc4b81` | **Held-out k-fold cross-validation** for the trainer |
| `a2ab6df` | **INA226 v4 contract** — predeclared `spu4_som_edge` gates |
| `3ad5da7` | **`spu4_som_edge` wired into the real scoring pipeline** |
| `6465b96` | `knowledge/SPU13_ARCHITECTURE.md` + both cores wired into the docs nav |

## 2. Interactive UART bench probe

The only existing probe for `spu4_som_edge` (`spu13_tang25k_spu4_som_edge_probe.v`,
silicon-proven, §3.2j.7) replays one hardcoded query forever — useful as a
smoke test, useless for actually trying inputs. New:
`spu13_tang25k_spu4_som_edge_interactive_probe.v` wraps the same, unmodified,
frozen `spu4_som_edge_wrapper` and adds a UART RX path (new reusable
`spu4_uart_rx_bitsync.v` core, unit-tested standalone) so a host can submit
an arbitrary 4-feature query and get a live classification back. The TX side
is copy-adapted from the fixed probe's engine, not rewritten, so both probes
share one host-side parser (`software/lib/spu4_som_probe_parser.py`).
Full-chain testbench: all 8 oracle-checked queries plus 3 malformed-line
recovery cases, 36/36. Host tooling:
`software/lib/spu4_som_probe_client.py` (encode/decode/transport) and
`tools/spu4_som_edge_demo.py`, the actual customer-facing CLI — prints
hardware results next to the independent software oracle and exits non-zero
on any mismatch.

**Board-side status:** bitstream built clean (`build/tang_primer_25k_spu4_som_edge_interactive_probe.fs`,
5.9 MB, nextpnr final Fmax 44.32 MHz — the *second* of two printed "Max
frequency" lines, not the first; see §5). The `uart_rx` pin (`B3`) is now
constrained in `tang_primer_25k.cst`. Not yet done: actually wiring the
board and running it — no hardware has been connected this session.

### The B3 pin finding

Identifying `uart_rx`'s physical pin from the Sipeed
`Tang_Primer_25K_Dock_60033` schematic surfaced something real: `B3` is the
onboard BL616 debugger chip's own UART RX line (schematic-confirmed, paired
with the already-used `uart_tx`/`C3`), but this repo separately documents a
"legacy fallback" scheme (`docs/rp_mcu_bringup_plan.md`) that bodge-wires an
external RP2350's UART TX onto that *same* pin. Nobody had cross-checked the
two. If both were ever connected on the same board, that's two live UART TX
drivers fighting one pad — the same damage class as the documented J11
backfeed incident, just not yet discovered. **Confirmed NOT connected on
this board, 2026-08-18** — `uart_rx` wired in `tang_primer_25k.cst`,
finding recorded in `knowledge/` memory
(`tang25k-b3-pin-contention-risk`) so it gets rechecked rather than assumed
clear on any other board.

## 3. The trainer that didn't exist

`tools/spu4_som_edge_trainer.py`. Adapts `tools/som_trainer.py`'s proven
algorithm shape (exact-integer dyadic competitive learning, farthest-point
init, SHA256-seeded deterministic epoch order) to `spu4_som_edge`'s flat
4-node structure — no hex-neighbor diffusion, because there's no topology to
diffuse across. BMU selection during training calls
`software/lib/spu4_som_edge_oracle.py`'s `find_bmu_edge` directly, not a
reimplementation, so "which node wins" during training is bit-identical to
the RTL by construction. Real scalar features get `RationalSurd(value, 0)`,
matching this repo's existing Q=0-means-ordinary-number convention. Output
is deliberately two files, not one: a weights JSON matching
`gen_spu4_som_boot_image.py`'s schema exactly, and a separate training
report (node → majority class label) that stays out of the boot image,
matching the wrapper's own "no label mapper in v1" contract.

Demonstrated against `software/tests/data/synthetic_current_v1.csv` (an
existing SPU-13-demo dataset, reused rather than duplicated — same feature
schema as the INA226 contract): trained cleanly, 36/36 on training data.
**That number was flagged immediately as meaningless** — a model graded on
what it memorized — which is what led to §4.

## 4. Held-out cross-validation

`tools/spu4_som_edge_cross_validate.py`. Stratified, SHA256-seeded
deterministic k-fold: for each fold, train on the other k−1 only, derive
node labels from *that* training data only (labeling from held-out data
would leak test information into the ground truth), then score the fold the
model never saw. Reports balanced accuracy (mean per-class recall), so a
majority class can't hide a minority class's failures. Test suite includes
both a positive control (well-separated data generalizes near-perfectly)
and a negative control (three classes drawn from the *same* distribution
score near chance, not near-perfect) — proving the harness can report a
negative, not just confirm whatever it's pointed at.

Real result on the same synthetic dataset: **100% balanced accuracy across
all 5 genuinely held-out folds.** Honest caveat stated at the time and worth
repeating here: clean synthetic data, well-separated by construction —
proves the trainer/oracle-matching/evaluation methodology is wired
correctly end to end, says nothing about real INA226 data, which will be
noisier.

## 5. The frozen gate that never caught up

Asked "what else before hardware arrives," checked whether the INA226
capture contract already had an answer (it did — a "what can be built
before the sensor arrives" section, everything on it already built in prior
sessions), and checked the frozen "Baselines and frozen gates" section while
there. Found: it names only the seven-node SPU-13 SOM, carried over
unchanged since v2 (2026-08-06) — meaning `spu4_som_edge`, the actual
product target since the 2026-08-16 edge-node pivot, had no predeclared
accuracy gate. A gate written after real data exists has no integrity, so
this had to be resolved now or not at all — same reasoning the v3
`pulses`-covariate amendment used.

**Decision (John's call, presented as three options): target both models
explicitly**, not replace one with the other. v4 contract amendment
(`software/datasets/ina226_coarse_monitor_v4.json`,
`docs/INA226_COARSE_MONITOR_CONTRACT.md`): `spu4_som_edge` gets its own
gate — same real captures, same frozen folds, same thresholds as the
seven-node SOM (aggregate ≥90%, worst fold ≥80%, per-class recall ≥80%,
deliberately the identical bar, not an easier one for the newer classifier)
— scored and gated independently. Documented honestly rather than forced
into false symmetry: `spu4_som_edge`'s v1 ABI has no runner-up quadrance, so
it gets no ambiguity gate, unlike the SOM1 evidence frame's confidence gap.

That amendment explicitly did NOT touch `tools/ina226_capture_pipeline.py`
or its test — declaring the gate blind was the part with integrity
requirements; the scoring code could safely follow. It did, same session:
`_spu4_som_edge_session_pairs()` now mirrors `_som_session_pairs()`,
training and scoring `spu4_som_edge` per fold alongside the seven-node SOM,
independently gated, verified end-to-end on the same synthetic fixture
(100% balanced accuracy both models, both gates `True`, boot-image
round-trip check holding on every fold). `DEFAULT_CONTRACT` now points at
v4. **The software side of Track A is now fully ready** — the only
remaining gap for a real result is real captured data.

## 6. Bugs found and fixed along the way

- **`S=07` should be `S=06`** in the fixed SOM edge probe's header comment
  and build script. The RTL's own PASS condition requires `busy==0`
  (`status[0]`), which gives `S=06`; the real recorded silicon evidence
  (§3.2j.7) already has the correct value. Found wiring a golden-line check
  for a new hardware-free smoke test; the RTL itself was never wrong, only
  two comments describing it.
- **`RationalSurd` cross-module import-identity bug.** `spu4_som_edge_trainer.py`
  imports `RationalSurd` via `software.lib.rational_som`;
  `ina226_capture_pipeline.py` initially imported the same class via
  `lib.rational_som` — same file, but Python caches modules by full import
  path, so these loaded as two *different* classes. Dataclass equality
  requires `self.__class__ is other.__class__`, so structurally identical
  `RationalSurd` instances compared unequal — caught by the boot-image
  round-trip check printing identical values on both sides of a failing
  `!=`. Fixed by importing via the trainer's exact path everywhere in the
  pipeline, with a comment explaining why, since this class of bug is easy
  to reintroduce by accident in code crossing between `tools/` and
  `software/lib/` import styles.

## 7. What's next

**Physical, blocked on nothing but time and hardware:**

1. Board bring-up for the interactive probe — wire the dock's USB-C
   (JTAG + host UART, same connector, no DirtyJTAG needed for this board),
   flash the `--profile demo` or `--profile oracle_fixture` boot image via
   the RP2040 flash PMOD (confirm `id` reports `EF4018` before writing),
   load the bitstream, run `tools/spu4_som_edge_demo.py` against real
   silicon for the first time.
2. Track A: parts ordered 2026-08-18, waiting on delivery. Once they land —
   verify the encoder counts on the Pico, then the 30-session capture
   campaign against the frozen v3 capture schema (v4 only touched
   models/gates, capture itself is unchanged).

**Software, not blocked, not yet started:**

- No trainer exists for the *seven-node* SOM's real INA226 data path either
  in a sense that matters here — that one already exists
  (`tools/som_trainer.py`, already wired into `run_study`). What's actually
  missing once real data lands is nothing code-side; both models are ready
  to score the moment a sealed manifest exists.
- The interactive probe's board bring-up (§2) doesn't need Track A at all
  and could happen in parallel with the parts shipping, same reasoning as
  the rest of this session.

## 8. PARKED by name (unchanged from 08-16)

SPU-13 tranches · GPU/rasterizer · PDM audio · Padé/RPLU2 · quantum · the
papers · `QADD` · ECP5 port · the `irotc_spi` router anomaly ·
`six_step_probe` trimming · A7 manifest targets · re-anchor decisions for
§3.2g.1 and §3.2k · `build_a7.sh:12` spin-name drift.

The seven-node SOM gate work in §5 touches code that also serves the
SPU-13 seven-node path (`tools/ina226_capture_pipeline.py`), but the actual
new work was entirely `spu4_som_edge`-side — no SPU-13 tranche was reopened
to do it.
