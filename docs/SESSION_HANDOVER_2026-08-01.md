# SPU-13 Session Handover — 2026-07-31 → 2026-08-01

> **SUPERSEDED IN PART, 2026-08-03.** The section "Where the fault actually is
> — localised on silicon" is **wrong**. The break was not between chord-accept
> and QR-commit; `u_spi` was never running at all. Root cause: `spu_a7_top` fed
> the raw `rst_n` pad into every async reset. Fixed in `0eec6f4`; all eight
> spins rebuilt and bench-tested, seven pass. See `hardware_evidence.md`
> §3.2m. Items 1 and 2 under "Open / next" are **done**. Everything else in
> this document still stands.

## Stop state

- **`origin/master` = `master` = `a12d220`, in sync, tree clean.** Verified with
  `git status --short --branch`, not assumed. (The 2026-07-24 handover claimed
  "nothing unpushed" when two commits were local-only. Check, don't trust this
  line either — this document was itself stale for several hours before being
  brought current at `a12d220`.)
- **Regression is now 183/183.** Three FP4 parameter-variant runs (`b24413c`)
  took it 179 → 182; the LUCAS SPI integration bench (`c69a7d5`) took it to 183.
- 21 commits this session, all pushed. `spu_strategy/` remains gitignored with
  **0 tracked files**.
- **Bench is live and at a known-good resting state:** Wukong holding
  `TENSEGRITYLINK`, Pico 2 running `rp2350_spu_diag` at 125 kHz, link answering
  `0xB3 version=1`. DirtyJTAG + CH340 + Pico 2 all connected, J11 bottom row →
  GP0–3 through the spliced 100 Ω resistors.

## The headline: the southbridge SPI rate rule is now silicon-confirmed

`SCK <= clk_fast / 6`, measured in simulation (`3f7252c`) and then **confirmed
on hardware** (`cdfa2e2`). Every observation at ratio ≥ 6 passed; every rate
below 6 was unreliable in a specific way — **stable within one configuration
cycle and inverted between them**. 4.412 MHz failed once then passed 3/3 in a
later session; 5.000 MHz passed once then failed 3/3.

That is the SCK-to-sampling-clock phase relationship, fixed at configuration and
re-rolled on the next load. It is why `spu_spi_slave_ratio_tb.v` sweeps four
phase offsets instead of testing one alignment — a single-phase test would have
called ratio 5 safe on either session.

**Operational rule: never run below ratio 6.** A ratio-5 link passes a whole
bench session convincingly, then fails after an unrelated reconfigure with
nothing in between to explain it.

Signal integrity did **not** bind first: with the 100 Ω series resistors, the
failure arrived exactly where the ratio predicted.

## Facts corrected this session

Each of these was wrong in the repo and had misdirected work.

- **The Wukong board clock is 50 MHz, not 100** (`799ef5b`). Measured with
  `tools/uart_baud_probe.py`, a tool added this session: `UARTPROBE` divides the
  raw clock by a fixed 434, so the baud at which its output is legible *is* the
  oscillator. `AGENTS.md` had recorded 1.5625 MHz for the divided core-spin
  `clk_fast`; the real figure is **781.25 kHz**, so the core-spin SPI ceiling is
  **130 kHz, not 260**.
- **`A7_FREQ` is a nextpnr `--freq` timing constraint and does not divide the
  clock.** `A7_CLK_DIV_LOG2` does. The "clk_fast max" figures in
  `hardware_evidence.md` are max-achievable, not operating frequencies.
- **Not every spin uses `spu_a7_top.v`.** `TENSEGRITYLINK` has its own top and
  clocks `u_spi` from a divide-by-2 of `sys_clk` — 25 MHz, a 4.17 MHz ceiling,
  and `A7_CLK_DIV_LOG2` never applies. **Check which top a spin uses before
  computing its ceiling.**
- **Spin UART silence is expected, not a fault** (`99dfb4a`). The default UART
  is `.start(hex_valid)` — event-driven, so a healthy spin with no SPI master is
  silent at every baud. Use `UARTPROBE` or an `A7_UART_DIAG=1` build as a
  free-running witness. This is indistinguishable from a dead board and misled
  this session's checkpoint.
- **`CARRYCASCIN` is a backend defect, not an SPU defect** (`c932127`). No SPU
  source instantiates DSP48E1; the pin is unconnected in every netlist on disk,
  in designs that route *and* fail. nextpnr materialises the tie-low itself.
  **Do not look for an RTL or synthesis fix.**
- **The SPI backfeed resistors are installed** (`371c615`). Only the *rule* was
  written down, so the text read as an open prerequisite and blocked a bench
  session that was already cleared. The remaining half is a per-session
  discipline, not an install: never leave one side powered and driving into an
  unpowered board.

## Firmware: the SPI rate is now self-reporting

All nine RP2350 firmwares previously discarded `spi_init()`'s return. They now
report it (`db55c94`, `abe895f`, `3652e7d`), and the reason is measured, not
theoretical: **asking for 2 MHz yields 1,973,684 Hz** on this silicon
(150 MHz `clk_peri` / 76). A rate quantising *upward* past the ceiling would have
been indistinguishable from a correct setup.

`rp2350_spu_diag` dropped 250 kHz → **125 kHz** (ratio 6.25 on a divided core
spin). Cost is ~5% of transaction time, because `spu_link` spends ~3 ms per
transaction in fixed CS/turnaround delays against 160 µs of clocking. If this
link ever needs to be faster, the 3 ms is where the 20× is — not the baud.

Per-spin ceilings and working probes are in `docs/SOUTHBRIDGE_SPI_PROTOCOL.md`.
Note `0xB3` does **not** exist on LUCAS (`ENABLE_TENSEGRITY` defaults to 0), so
that probe is invalid there; use `rp2350_lucas_j11_smoke`.

## FP4 structured inverter: switched on by default

Twenty-seed matrix measured under contract and independently audited (all 40
Fmax values re-extracted from raw logs, every statistic recomputed, `r`
reproduced at 0.9061, netlist hashes checked to prove the frozen netlists were
copied not re-synthesized). **The 2-fast/3-slow split was an n=5 artifact.**

Default flipped in `5399b4c`; folded into the evidence doc in `15b3118`.

Two calibrations that must travel with any quote:

1. **Mean and median tell opposite stories.** Fmax mean 1.007939 reads as a win;
   median 0.964448 is a ~3.6% loss. **12 of 20 seeds have a slower v2 clock.**
   Quote the median.
2. **There is a real tail.** v2 wins wall-clock on 19 of 20 seeds (mean 9.8%),
   but **seed 59 is 30.4% slower** on a 15.7 ns routing critical path. Expect it
   rather than diagnose it fresh after an unrelated rebuild.

A coverage gap had to be closed first: every parameterised bench pinned
`USE_STRUCTURED_INVERTER = 0`, so the regression exercised v1 regardless of the
default and **v2 had no functional coverage at all**. `b24413c` runs all three
benches at both values. Verified non-vacuous — `iverilog` rejects unknown `-P`
names, so a clean variant run proves the parameter was applied.

## Build-path fixes

- **`ZPHI_KARATSUBA` defaulted to 1 and hard-failed every non-tensegrity spin**
  (`be58544`). Introduced 2026-07-23; every documented non-tensegrity build
  command was broken for eight days. Now only an *explicit* non-zero on an
  unsupported spin is rejected.
- **The FP4 default switch broke artifact naming** (`56bf39f`). Tagging was
  conditioned on `FP4_STRUCTURED = 1`, correct while v1 was default; flipping it
  made every default build emit `..._FI1B0_S1.bit`. Production is canonical
  again, non-production stays tagged.

## The A7 build blocker — half solved

**Fixed:** the 230-node timing-graph rejection. `spu_a7_top.v` omitted
`tgr_transport_status`, leaving a 128-bit input undriven; the X/Z-fed decode cone
is what nextpnr-xilinx 0.8.2 rejected. Tying it to zero gives **zero nodes, clean
route, 76.08 MHz**, matched control still failing at 230. Third omitted input
port on that module to present as a toolchain symptom.

> **The fix's diff is in `c932127`, whose message describes only CARRYCASCIN.**
> It was swept in by a `git add -A`. Recorded in `hardware_evidence.md` rather
> than rewriting pushed history.
>
> **This happened twice.** `4dddb50` likewise carries a
> `TENSEGRITY_BALANCER_FEASIBILITY.md` scope note written concurrently by a
> collaborator. Both landed intact and stay discoverable via
> `git log -- <file>`, so neither was rewritten. **The remedy is procedural:
> stage explicit paths, never `git add -A`, while this worktree is shared.**

**Not fixed, and it is not LUCAS-specific.** `SU3` (`_CORE=0`) and `ROBOTICS`
(`_CORE=1`) were both rebuilt from current source and fail identically —
`ROBOTICS` returns `ARITHMETIC_BLAZE: FAIL 0/13`, every `rotc_commit valid=0`.

| Board top | Spins tested | `_CORE` | Silicon |
|---|---|---|---|
| `spu_a7_top` | LUCAS (2 builds, 2 backends), SU3 | 0 | **fail** |
| `spu_a7_top` | ROBOTICS | 1 | **fail** |
| standalone tops | `TENSEGRITYLINK`, `SOMSIDECAR` | — | **work** |

**The discriminator is `spu_a7_top` itself, and no narrower.**

**Himbächel 0.10 is closed.** It routes LUCAS but the bitstream fails on
silicon, and it **crashes on `TENSEGRITYLINK`** (`assertion_failure` in
`relptr.h:56`, reproduced on two seeds) — a design 0.8.2 builds and ships. Not a
default-backend candidate. Note Himbächel *is* upstream's successor to
nextpnr-xilinx, not an alternative vendor; there is no third open-source option.

## Where the fault actually is — localised on silicon

This supersedes the earlier "live hypothesis" that RTL wiring was at fault.

**The integration bench was built and it passes.**
`spu13_a7_lucas_spi_integration_tb.v` (`c69a7d5`) drives real SPI `0xB1`+CRC →
`0xAE` through an actual `spu_a7_top #(.SPIN("LUCAS"))` and matches all four
oracle vectors. Audited independently here — real top, real SPI, oracle matching
`rp2350_lucas_j11_smoke.c:44` exactly, and it reproduces. **The behavioural RTL
is exonerated.** Its one modelling boundary: `sim_xilinx_bufg.v` is
`assign O = I;`, so no clock-network behaviour is modelled.

**An `A7_UART_DIAG=1` build then localised the break directly**, which is why no
`spu_a7_top` bisection was needed:

| Signal | Evidence | Status |
|---|---|---|
| `clk_100mhz` | `HB` toggles | alive |
| **`clk_fast`** | `diag2` block is clocked by `clk_fast` (`spu_a7_top.v:204`) and decoded correctly | **alive** |
| CS at the pin | `CS:1` | arrives |
| `0xAC` decode | `AC:1`, in the `clk_fast` domain | works |
| Chord bytes | `LC:36` = trailing CRC of `D0200C05…` | all arrive |
| CRC accept | `crc_error_sticky` clear | accepted |
| **QR commit** | `0xAE` returns `valid=0` | **never fires** |

**The SPI slave is fully functional on silicon.** The break is strictly between
`u_spi` accepting the chord and the sidecar committing QR.

Note `HB` alone proves nothing about `clk_fast` — it is deliberately free-running
off raw `clk_100mhz`. It was `AC`/`LC`, both in the `clk_fast` domain, that
established the fabric clock is live.

Also ruled out by direct comparison: SPI pins byte-identical between the XDCs
(J4/G4/B4/B5); `rst_n` identical (H7); clock input pin identical (M21 in every
XDC); BUFG placement identical (`BUFGCTRL_X0Y0` in both a failing and the
working build); `core_boot_ready` gates nothing functional
(`spu_a7_top.v:348/750/812/1033` — status byte and diagnostics only).

**Next step is observability, not bisection.** Contract written:
`spu_strategy/gtp_contract_a7_inst_observability_2026-08-01.md` — add sticky
`clk_fast` latches for `spi_inst_valid` (`IV:`), `qr_commit_valid` (`QC:`) and
the latched `inst_word` (`IW:`) to the DIAG line. Those three partition the
remaining space with no ambiguous outcome.

> A caution for whoever reads the `spu_a7_top.v:241` comment: it claims the
> fabric-derived clock BUFG is "pinned to the BUFG site used by the
> silicon-proven image". **No such constraint exists in any XDC.** It is a
> comment describing an unimplemented mitigation. It did not turn out to explain
> this failure, but it will send you down a dead end.

## Stale bitstreams — still open

**10 of 17 A7 bitstreams predate the 2026-07-13 J11 remap** and route SPI to the
damaged top row, returning all zeros. This includes every southbridge-relevant
spin: `LUCAS`, `SU3`, `SU3SHARE`, `RPLUCFG`, `RPLU2CORE`, `RPLU2PADE`,
`ROBOTICS`, `IROTC_nosparse`. Only `J11LOOPBACK`, `TENSEGRITY*` and `SOMSIDECAR`
are post-remap.

A stale bitstream fails by returning zeros — indistinguishable from a dead link,
a damaged pin, or a boot FSM that never reaches READY.

**Two were rebuilt (`SU3`, `ROBOTICS`) and both fail on silicon, so the
remaining five were deliberately left alone** — they would produce five more
non-working bitstreams. Finish the `spu_a7_top` fault first, then the bulk
rebuild is mechanical.

**All eight originals are preserved** in
`build/evidence_archive/prerebuild_2026-08-01/` with a `MANIFEST.sha256`,
verified 15/15 `OK`. Spot-checked against `hardware_evidence.md`: `RPLU2CORE`
`71319fbb…` and `SU3SHARE` `0f886350…` match their cited hashes, so the evidence
survived the rebuild.

**Packing now works without hand-set environment variables** (`a12d220`). Three
gaps each masked the next: fasm2frames discovery needed `PRJXRAY_ROOT` exported;
the script needs the `fasm`/`textx` venv rather than system python3; and
fasm2frames also imports `prjxray` from its own checkout root, which needed to
be on `PYTHONPATH`. Now:

```sh
source tools/env_openxc7.sh
A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t <spin> all
```

Budget real time for `pack`: fasm falls back to its slow pure-Python textX
parser because the antlr accelerator ships as an uncompiled `.pyx`. Rebuilding
fasm from source does **not** compile it — that was attempted and reverted, and
the venv restored to the exact `fasm 0.0.2.post66` that packed the verified
bitstreams. Roughly 5 minutes for `ROBOTICS`' 35 MB FASM, well under 1 for
`LUCAS`' 12 MB. Also: repacking an unchanged route produced a **different
bitstream hash**, so do not assume the pack step is bit-reproducible.

## Damage report — artifacts lost

`TENSEGRITYPROBE_ZK1_S1`: `.json`, `.nextpnr.log`, `.pnr.fasm` and `.pnr.json`
all lost. The first two went to a validation run of mine that omitted the stage
argument (the default stage **builds**); the rest to a further P&R at 11:44 the
same day. Only `timing_summary.json` survives — it carries the metrics and the
originals' hashes, so Phase 4 figures stay quotable and the loss stays provable,
but nothing can be re-derived or hash-confirmed.

**`_ZK1_S1` is the default tag for the default configuration**, so *any* bare
`build_a7.sh 100t tensegrityprobe` lands on it. Treat it as write-protected and
pass an unburned `A7_SEED` if that configuration genuinely needs rebuilding.

## Standing hazards

- **Never invoke `build_a7.sh` against an existing `_ZK{n}_S{seed}` name for any
  reason, including argument validation, and never omit the stage argument** —
  the default stage builds.
- Synthesis is not bit-reproducible here. Burned seeds: **1, 2, 3, 5, 7, 11, 13,
  17, 19, 23, 29, 31, 41, 53, 67, 79**, plus **211, 233, 307** used this session.
- `build/` is gitignored. There is no recovery from an overwrite.
- Never use `--ignore-loops` or `--timing-allow-fail` to obtain a pass.
- **`run_all_tests.py` treats any `FAIL` substring anywhere in a testbench's
  output as a failure.** Benches that legitimately report sub-failures must use
  other labels.
- **Fresh-clone run is the only honest check after touching `run_all_tests.py`.**
  Done this session for `b24413c`: 182/182 at that commit (the gate reached 183
  later, at `c69a7d5`).
- Paper build paths differ: `rplu_paper.tex` builds from the repo root,
  `LUCAS_MAC_PAPER.tex` from `docs/`.

## Open / next

1. **The `spu_a7_top` silicon failure** — the observability contract
   (`gtp_contract_a7_inst_observability_2026-08-01.md`). Add `IV:`/`QC:`/`IW:`
   to the DIAG line; the three outcomes partition the space completely. GTP
   builds, the bench run happens here.
2. **Bulk rebuild of the remaining five stale spins** — deliberately deferred.
   `SU3` and `ROBOTICS` were rebuilt and fail, so the rest would too. Mechanical
   once item 1 lands.
3. **INA226 capture — fully unblocked.** Motor (Tamiya 75026), ZK-5KX, INA226
   (`R100` confirmed), breadboard and RP2350 all in hand. **The interlock BOM is
   NOT required** — it gates a different subsystem. Manifest generated at
   `build/ina226_capture/manifest.json`, probe `tamiya_75026_v1`, block rotation
   and fold assignment verified against the frozen contract, stall shunt at 37%
   of the 75,000 µV abort. One conflict: the Pico 2 cannot be both the SPI
   southbridge and the MicroPython INA226 logger — use the RP2350-Zero, or
   restore `rp2350_spu_diag.uf2` afterwards. Capture block 0 only, verify
   ascending phase current, then commit to blocks 1–9.
4. **Permanent v2 coverage is done**, but the same question applies elsewhere:
   any parameter with a non-default value that ships is a candidate for the
   `PARAM_VARIANTS` table in `run_all_tests.py`.
5. **Show HN timing** — still the project owner's call.

## Useful restart commands

```sh
git status --short --branch
python3 run_all_tests.py                     # expect 183/183
openFPGALoader -c dirtyJtag --detect
python3 tools/uart_baud_probe.py             # oscillator / liveness check

# Rebuild a spin (packing needs no extra env vars since a12d220):
source tools/env_openxc7.sh
A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t <spin> all

# Read the chain diagnostic (needs an A7_UART_DIAG=1 build loaded):
#   DIAG HB:<clk_100mhz> CS:<cs seen> AC:<0xAC decoded> RDY:<boot_ready>
#        BST:<boot state> LC:<last cmd byte>
```

Bench resting state, for comparison next session: Wukong holding
`TENSEGRITYLINK`, Pico 2 running `rp2350_spu_diag` at 125 kHz, `0xB3` returning
`version=1`. Anything that fails against that is new, not baseline.
