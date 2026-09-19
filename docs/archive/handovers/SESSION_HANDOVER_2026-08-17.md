# Session handover — 2026-08-17

Two threads today, both starting from a single question about the SPU-4 ABI:
whether modular spins or custom ASICs built from this RTL could be identified
in silicon. That became ABI v1.1's `id` port, which led to a real,
repo-wide evidence-accuracy bug (nextpnr's estimate-vs-final Fmax split) that
touched the *pinned* SPU-4 core reference. Separately, the narrowed SPU-4 edge
node programme moved from "not instantiated, no weight-upload path" to two of
its five steps landed: the flash-boot weight loader and the customer wrapper
around it, both simulation-proven end to end.

*Written after the session closed, not incrementally — a deviation from the
08-01 lesson worth naming rather than pretending didn't happen. Nothing here
went stale in the meantime since the session ran start to finish in one
sitting.*

## 1. Repository state

- `master`, clean, **in sync with origin** — 10 commits today, all pushed.
- Regression **200 PASS / 0 FAIL** (was 198 at session start).
- No board work today except one real Tang 25K bench session (§2) and one
  Artix-7 rebuild for verification only (§3) — no new silicon claims for the
  edge-node RTL, which is simulation-only so far.

| Commit | Change |
|---|---|
| `7fb4db9` | **SPU-4 ABI v1.1** — `id`, a read-only identity port |
| `daabf25` | `id` wired into the ABI probe's UART line |
| `64640d3` | **`id` proven in silicon** — Tang 25K, 10/10 loads |
| `1549597` | `id`-bearing probe's post-P&R cost measured; Fmax bug found |
| `debfa2a` | **5 nextpnr Fmax estimate-vs-final citations fixed, repo-wide** |
| `9727468` | A7 Fmax citations verified safe (different mechanism than assumed) |
| `a8bc2e0` | **`spu4_som_flash_loader.v`** — weight-upload path, step 1 |
| `39c8fe5` | `gen_spu4_som_boot_image.py` — the packer step 1 was missing |
| `6e93672` | **`spu4_som_edge_wrapper.v`** — customer wrapper, step 2 |
| `b1ee1e2` | Docs CI fix — two broken links were failing `mkdocs --strict` |

## 2. SPU-4 ABI v1.1 — the `id` discovery port

John's framing going in: RISC-V's actual lesson isn't "no discovery register,"
it's that the *discoverable space* itself is unbounded — dozens of optional
extensions turn "what does this chip support" into a combinatorial problem.
`id` is built the other way: one 16-bit word, four fixed nibbles
(`ABI_MAJOR`/`ABI_MINOR`/`WRAPPER_ID`/reserved), no open-ended registry.
`docs/SPU4_ABI.md` §2a has the full bitfield and the reasoning written in.

Added to `spu4_customer_wrapper` as a pure append (v1.0 → v1.1, no existing
port touched), then wired into `spu13_tang25k_spu4_abi_probe`'s UART line as a
new `I=` field, then flashed and read back **10/10 loads on Tang 25K,
matching the documented bitfield exactly** — the discovery mechanism itself
proven end to end, not just simulated. `hardware_evidence.md` §3.2j.6.

## 3. The Fmax estimate-vs-final bug

Measuring the `id`-bearing probe's post-P&R resource cost required rebuilding
the *pre-`id`* commit for comparison. That rebuild's raw nextpnr log showed
**two** `Max frequency for clock` lines — a post-placement estimate, then,
after a full `Critical path report`, the real post-route figure — and the
number already published for that build (`160.26 MHz`, §3.2j.3) was the
estimate. The actual final Fmax was **211.60 MHz**.

A same-day audit checked every other Fmax citation this pattern could
plausibly affect and found four more live instances, one of them in the
**pinned SPU-4 core reference** (§3.2j.2, cited 4×+): `160.38 → 161.11 MHz`.
Three more were unlabeled ranges (`rotc_tagged_probe`,
`satellite_aggregator_probe`, `spu_whisper_v1_probe`) where whoever recorded
them had evidently seen both numbers and reported the spread as ordinary
variance rather than recognizing the split — all collapsed to their correct
single final value. One citation (`six_step_probe`) was already correctly
labeled "post-placement," because that design never finishes routing (96%
congestion) and no final figure exists to cite.

Artix-7 was the open question — `nextpnr-xilinx` wasn't on `PATH`, initially
read as "not installed." It was, at `~/.local/openxc7`. Rebuilding `LUCAS`
found the installed version doesn't support `--report` at all, so
`build_a7.sh` was already falling back to log-based parsing for every A7
build — a different safety mechanism than the `--report` JSON reasoning used
for the Tang builds, but empirically confirmed correct (55.33 → 61.94 MHz,
final value extracted correctly). No A7 citation needed correction.

Every fix is inline-annotated (`CORRECTED 2026-08-17: was X, nextpnr's
post-placement estimate`) rather than silently rewritten, across
`hardware_evidence.md`, `SPU4_ABI.md`, `SPU4_FAULT_REPORTING_CONTRACT.md`,
`BENCH_PROCEDURE_2026-08-3_2j_SPU4_REANCHOR.md`, `SESSION_HANDOVER_2026-08-16.md`,
and `board_build_manifest.json`. Full record:
[[nextpnr-fmax-estimate-vs-final]] (memory) and `SPU4_ABI.md` §5.1.

## 4. SPU-4 edge node — steps 1 and 2 landed

Per the 08-16 narrowing, this is the only programme. Two of five steps moved
today, both simulation-only:

**Step 1 — weight upload, decided flash-boot not live.** John has the
hardware for it already (RP2040 flash PMOD, spare SPI flash chips, XGECU as
SOP8 fallback for loose chips), which settled the design question in favor of
the product-appropriate answer: train once offline, program a $2 flash chip,
plug it in, no host present at runtime. `spu4_som_flash_loader.v` hydrates
`spu4_som_edge`'s four nodes from a new flash region
(`FLASH_SPU4_SOM_BASE = 0x120000`) on one `start` pulse, owning
`spu_flash_bridge.v` — not the old `spu4_boot_master.v`, which is dead
research-era code for iCE40 LP1K and the since-dropped Dream Sequencer.
`gen_spu4_som_boot_image.py` packs a trained-weights JSON (or a synthetic
profile, since no trainer exists yet for this 4-node topology) into the exact
byte layout the loader expects.

**Step 2 — the customer wrapper, local pins only.** John's call, explicit
against feature creep for a still-prototype product: no networked reporting,
no class-label mapping. `spu4_cluster_bridge.v` exists in the tree but is a
different product's mechanism (SPU-4 as an SPU-13 satellite, reporting to a
governor that doesn't exist for this deployment) and was deliberately not
reached for. `spu4_som_edge_wrapper.v` auto-hydrates on reset and exposes the
same start/busy/done discipline `spu4_customer_wrapper` established, under
one `busy` signal that covers both boot and classification. Its own `id` is
`WRAPPER_ID=2` in the same shared registry §2a started.

Both testbenches exercise the real downstream module, not mocked interfaces —
the loader's TB feeds a real `spu4_som_edge` and checks the BMU picks the
exact-match node at quadrance 0; the wrapper's TB drives the whole thing the
way a customer would (boot → start-during-boot ignored+reported → classify →
results held → start-during-busy ignored+reported without corruption).

**Two testbench races found and fixed while writing the wrapper's TB** — see
§6, both now match the established convention `spu4_customer_wrapper_tb.v`
already used correctly.

## 5. Docs CI

The public docs site build (`mkdocs build --strict`) was failing. Reproduced
locally in the repo's own `.venv` (mkdocs-material already installed, no
fresh install needed) and found two independent bugs: three files linking to
a heading anchor with a double hyphen where the real one (confirmed from the
built HTML's `id` attribute, not guessed at) collapses an em dash to a single
hyphen, and one file linking to `docs/hardware_evidence.md` from a file
already inside `docs/`, doubling the path. Both fixed; strict build is clean.

Running the build script locally also destroyed a tracked symlink
(`docs/knowledge -> ../knowledge`), replacing it with a real directory copy —
caught via `git status` before committing, restored with `git checkout`.
Saved as [[build-docs-site-symlink-gotcha]] so it doesn't cost a "why does
`docs/knowledge` show as deleted" investigation next time.

Confirmed live afterward: `https://pinnacletechnologysolutionsltd.github.io/SPU/`
— John checked the bare org root first (`.github.io/` with no path), which
will always 404 regardless of this repo; the actual Pages URL includes the
repo name.

## 6. Corrections to earlier beliefs, made and caught in the same session

- I initially guessed the Tang-side tool-shielded scripts were safe because of
  a dict-overwrite quirk in `collect_fpga_metrics.py`'s log parser. Wrong —
  they're safe because they pass `--report <json>`, which structurally only
  ever contains the final post-route analysis. Verified empirically before
  writing it into the permanent record.
- I assumed `nextpnr-xilinx` "wasn't installed" when it wasn't on `PATH`.
  It was, at `~/.local/openxc7`, and `build_a7.sh` already auto-detects and
  sources it — I hadn't checked before concluding A7 was unverifiable.
- A first draft of `SPU4_ABI.md`'s resource-cost section attributed the
  `id`-bearing probe's Fmax drop to "a longer UART message-byte mux" without
  checking. The actual nextpnr critical path runs through
  `spu4_dissonance.v`'s residual adder chain, unrelated to `id` or the UART
  logic. Caught before commit by actually reading the critical-path report
  instead of inferring from the cell-count delta.
- `gen_spu4_som_boot_image.py`'s first draft had a dead `if False else`
  branch left over from editing — cosmetic, no functional bug, but a
  reminder that "it compiled and produced the right bytes" isn't the same
  check as "the code is clean."
- `spu4_som_edge_wrapper_tb.v`'s first draft drove `start` with blocking
  assignment (`start = 1`), which raced the DUT's own clocked block for the
  same edge and made `start_ignored` checks pass or fail nondeterministically
  depending on process-scheduling order — not caught by reasoning about the
  RTL, only by adding a debug `$strobe` and watching the actual sample
  values. Fixed with nonblocking `<=`, the same convention
  `spu4_customer_wrapper_tb.v` already used for exactly this reason. A
  second, related bug (reading a status bit immediately after the edge that
  sets it, racing the NBA update) needed the same `#1` settling delay that
  file's `launch` task already documents.

## 7. What's next

Step 3 of the SPU-4 edge-node programme: a full-chain testbench against the
`software/lib/rational_som.py` oracle (bit-exact classification verdicts, not
just "the BMU picks the right node for a hand-built fixture," which is what
today's testbenches check). Step 4 is a board probe → silicon for the wrapper
— nothing blocks it. Step 5 (real INA226 data) still waits on parts that
haven't been ordered yet.

**No trainer exists for `spu4_som_edge`'s 4-node topology.**
`tools/som_trainer.py` trains the SPU-13 seven-node hex SOM, a different map
format — real weights for the edge node still need either a new trainer or a
decision to wait for step 5's real data to train against.

**Outreach: reaffirmed WAIT, with a clarification.** Right after today's RTL
milestone, John raised building out the company side — Hugo site, domain
email, social accounts, blog posts. The 08-16 decision (no campaign until the
real-sensor result) holds; his call was to draw the line at
publish/broadcast, not build: site infrastructure, email, and empty social
accounts are fine to set up now, actually posting content is still held.
See [[outreach-timing-decision]].

## 8. PARKED by name (unchanged from 08-16)

SPU-13 tranches · GPU/rasterizer · PDM audio · Padé/RPLU2 · quantum · the
papers · `QADD` · ECP5 port · the `irotc_spi` router anomaly ·
`six_step_probe` trimming · A7 manifest targets · re-anchor decisions for
§3.2g.1 and §3.2k · `build_a7.sh:12` spin-name drift.

Today's work (the `id` port and the Fmax audit) was a genuine, useful detour
from this list, not scope creep back into it — it strengthened the ABI the
edge-node wrapper now depends on and fixed evidence the pinned core reference
was resting on. Worth naming as a detour anyway, since the 08-16 handover's
whole point was noticing drift before it compounds.
