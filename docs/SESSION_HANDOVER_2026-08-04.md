# SPU-13 Session Handover — 2026-08-04

**Written incrementally through the session, not at the end.** The 2026-08-01
handover went stale within hours of being written; this one is updated as work
lands. The GTP tranche below is **in flight at time of writing** and its section
is explicitly marked unfinished — do not read it as a result.

## Stop state

- **4 commits, all docs.** `2ac4ae9`, `92cac25`, `c0cb2ae` are **pushed**
  (`21bdfde..c0cb2ae`); `8980ae2` is **committed but unpushed**. Verify yourself
  with `git status --short --branch` rather than trusting this line.
- **Regression 184/184**, run once at session start. Nothing but documentation
  has changed since, so it still stands — but it has not been re-run against
  these commits.
- **No RTL, board script, or tool changed today.** Seven `.md` files plus the
  runbook. Nothing here alters what a build produces.
- `spu_strategy/` remains gitignored with 0 tracked files.

## The headline: a headline finding from 2026-08-03 is retracted

**The v1/v2 Padé margin table was one build read as two.**

nextpnr prints `Max frequency` **twice per run** — a post-placement estimate
immediately after `SA placement time …`, then the real figure after `Routing
complete.` Routing improves the number by 16–96% across the logs on disk.

The table that drove the whole timing investigation —

| Build | Fmax | Silicon |
|---|---|---|
| v2 | 29.64 MHz | 4/5 |
| v1 | 38.18 MHz | 5/5 |

— is **both lines of a single file**: `spu_a7_100t_RPLU2PADE.json.nextpnr.log`,
line 268 (post-place) and line 1428 (post-route). That file is the **v1** build,
mtime `2026-08-03 23:56`, matching its `.bit` at `23:58`. `grep -rl` over all of
`build/` finds `29.64 MHz` and `38.18 MHz` in that one log and nowhere else.

The "29% less margin" is v1's **routing gain**, not a comparison. **v2's routed
Fmax had never been measured.**

### How the v2 log was lost

v2 and v1 both wrote the **canonical** `spu_a7_100t_RPLU2PADE.*` name, so the v1
rebuild overwrote v2's log — and `pade_v2_fail_2026-08-03/` archived the `.bit`
and `.pnr.fasm` but **not** the `.nextpnr.log`. Second instance in two days of
the artifact-overwrite hazard that destroyed `LUCAS 41df24aa…`.

**New standing rule: archive the `.nextpnr.log` with the `.bit` and `.fasm`.**
It is small and it is the only record of what the router achieved.

### The pessimism counter-evidence was wrong the same way

"The 2026-07-03 LUCAS build reported 4.79 MHz and passed on silicon at 50 MHz"
cites `LUCAS.j11.nextpnr.log`, a **superseded** build. Current LUCAS routes at
**79.90 MHz** and closes at 50 with 60% margin. LUCAS is not an example of a
spin working while unclosed.

**The argument survives, relocated, and the better example was already in
hand:** `RPLU2PADE` **v1** routes at 38.18 MHz, runs `clk_fast` at 50 MHz on
silicon, and passes 5/5. Current, same design, direct.

### What survives

**The Padé pipeline really is the timing outlier.** The reasoning that aimed the
tranche was wrong; the target was right.

## Part C — the timing survey (complete)

Read-only over 95 `.nextpnr.log` files. Newest routed figure per spin; coreless
spins target 50 MHz, the tensegrity guard clock targets 25 MHz.

| Spin | Clock | Routed | vs target |
|---|---|---|---|
| RPLUCFG | `clk_fast` | 80.60 | closes |
| LUCAS | `clk_fast` | 79.90 | closes |
| SOMSIDECAR | `sys_clk` | 65.63 | closes |
| TENSEGRITYLINK | `guard_clk` | 46.54 | closes vs 25 |
| **SU3** | `clk_fast` | **45.51** | **under by 4.5** |
| **RPLU2PADE** | `clk_fast` | **38.18** | **under by 11.8** |
| TENSEGRITYPROBE | `guard_clk` | 34.37 | closes vs 25 |
| RPLU2LIVE | — | **no routed data** | — |
| SOMPROBE | — | **no log at all** | — |

**"Unclosed at 50 MHz" is not the normal condition on this board.** Everything
with current routed data closes comfortably except SU3 (marginal) and Padé (the
outlier by a wide margin).

`RPLU2LIVE` and the legacy `SOM` logs **end mid-routing with no `Routing
complete.`** — interrupted runs. Their 2.11/2.59 MHz entries are post-place
estimates, not results. Do not cite them. Three of the nine spins have no usable
routed measurement.

Full working: `spu_strategy/claude_findings_a7_timing_survey_2026-08-04.md`.

## GTP tranche — COMPLETE. The margin hypothesis is dead.

`spu_strategy/gtp_contract_a7_timing_closure_2026-08-04.md`, rewritten this
session after Part C invalidated its premise. Parts A1 and B both landed.

**Paired result, `--freq 50`, routed `clk_fast` Fmax:**

| Seed | v1 (control) | v2 (structured) | v1 − v2 | Faster |
|---|---|---|---|---|
| 127 | 34.46 | **35.48** | −1.02 | **v2** |
| 131 | **42.17** | 33.44 | +8.73 | v1 |
| 137 | 37.44 | **37.98** | −0.54 | **v2** |
| mean | 38.02 | 35.63 | +2.39 | — |
| range | 34.46–42.17 | 33.44–37.98 | — | — |

**All six builds FAIL at 50 MHz.** Every one ended `0 warnings, 1 error`.
nextpnr writes `.pnr.fasm`/`.pnr.json` *before* raising the timing error, which
is why numbers exist despite the stage failing. No `.bit` was packed.

### Two conclusions, both negative for the timing story

**1. The arms interleave — v2 is *faster* than v1 on two of three seeds.** The
+2.39 MHz mean gap is carried entirely by seed 131; the median paired difference
is **−0.54 MHz, favouring v2**. The ranges overlap heavily. At n=3 the arms are
indistinguishable, and what separation exists points the wrong way for the
hypothesis. This is precisely the outcome the amended contract predicted as
fatal: *"the original two-build comparison was measuring placement luck."*

**2. v1 does not close at 50 MHz either — and v1 passes 5/5 on silicon.** This
is the stronger of the two. It is direct, same-design, same-constraint evidence
that **failing to close at 50 MHz does not predict silicon failure on this
board.** So "v2 doesn't close" cannot explain `seven_over_three`, because the
control that works perfectly doesn't close either.

> **SUPERSEDED THE SAME EVENING — see "The bench result" below.** I wrote here
> that timing was exonerated and the miscompile hypothesis earned, and
> recommended a netlist diff. **Both conclusions were wrong**, and the netlist
> diff would have been the wrong move. What the paired Fmax data actually killed
> was "v2 is systematically slower than v1"; I over-extended that to "timing is
> not the mechanism." The bench then showed the fault is **intermittent** and
> affects **both** inverter arms, which no amount of routing data could have
> settled.

### What this does not establish

**None of the six builds has been benched.** The tranche measured routing, not
behaviour. The `seven_over_three` failure was observed on the *original* v2
build (`A7_FREQ=2`, default seed), which is not among these.

**Part A0 is now low value** — recovering the original v2's `--freq 2` Fmax
mattered when a margin gap was live. With the arms shown comparable it would
only complete the record. Deprioritised, not withdrawn.

### The decisive follow-up, cheaper than a netlist diff

Bench a **v2 build that is faster than a v1 build known to work**:

- v2 seed 137 routes at **37.98 MHz**
- v1 seed 127 routes at **34.46 MHz**

Pack both and bench them. If v2@37.98 still fails `seven_over_three` while
v1@34.46 passes, timing is conclusively excluded on a same-constraint,
same-seed-family, *adverse-to-the-hypothesis* comparison — and the netlist diff
starts from certainty rather than inference. Two `pack` invocations plus one
bench session.

Use `FP4_EVIDENCE=1` on the v1 pack or it writes the canonical production name.

## The bench result — the fault is intermittent, and the inverter is exonerated

Ran on the evening of 2026-08-04. **This supersedes both of the day's earlier
conclusions.**

| Bitstream | `A7_FREQ` | Routed | Runs | Passes |
|---|---|---|---|---|
| **canonical** (seed 1) | **2** | 38.18 | 3 (+41 hist.) | **3** |
| `FI1B0_S137` (v2) | 50 | 37.98 | 4 | **4** |
| `FI0B0_S131` (v1) | 50 | 42.17 | 2 | **1** |
| `FI0B0_S127` (v1) | 50 | 34.46 | 1 | 0 |
| `FI0B0_S137` (v1) | 50 | 37.44 | 1 | 0 |
| `FI1B0_S127` (v2) | 50 | 35.48 | 1 | 0 |
| `FI1B0_S131` (v2) | 50 | 33.44 | 1 | 0 |

### What is established

**The FP4 structured inverter is not the cause.** v1, the reference inverter and
current default, fails too. **The 2026-08-03 attribution behind the revert in
`21bdfde` was wrong** — `seven_over_three` is not a v2 defect.

**The fault is intermittent.** `FI0B0_S131` failed, then passed — same
bitstream, same wiring, twenty minutes apart.

**The bench is sound.** The canonical image passed 3/3 the same evening on the
same firmware and wiring, so the failures are real properties of the builds.

**Closure at 50 MHz is not the discriminator.** All six new builds miss it; so
does the flawless canonical. `FI0B0_S131` routes highest of the six at
42.17 MHz and still failed.

### The signature — the strongest clue we have

Correct is `0x55555557`. Observed: `0x19D57157`, `0x19D5711F`, `0x47D55D37`,
`0x7FD5701A`, `0x19D57157`.

**Every failure has `D5` where the correct value has `55`** — same nibble, one
extra bit — then diverges. **Two different builds returned byte-identical
`0x19D57157`.** A shared mechanism, not placement luck. `wide_constants`
failures also put nonzero data in lanes B and D, which are zero in every
passing run and must be zero.

### The methodological lesson, which cost three wrong conclusions in one day

> **A single bench run is not a result. An intermittent fault can only be
> characterised by pass RATES over N runs.**

The 08-03 margin table, "timing is exonerated", and "v2 passes / v1 fails" all
came from reading one number per condition. The next tranche mandates N ≥ 10,
and N ≥ 20 before any build may be called clean — the canonical build's
reputation rests on 41 consecutive passes.

All six bitstreams, their `.nextpnr.log`s and every bench log are archived at
`build/evidence_archive/pade_intermittency_2026-08-04/`.

### The critical path is routing, not logic — and that reframes "is it the tools?"

| Spin | Logic | Routing | Total |
|---|---|---|---|
| **RPLU2PADE** | 5.7–6.6 ns | **17.9–23.9 ns** | ~24–30 ns |
| LUCAS | 3.6 ns | 8.9 ns | 12.5 ns |
| RPLUCFG | 2.1 ns | 10.3 ns | 12.4 ns |

**Routing is 75–80% of Padé's critical path.** Six ns of logic would meet
50 MHz with 14 ns to spare; twenty ns of *wire* does not. That is placement
quality — logic spread across the die rather than clustered — which is where
openXC7 is weakest against Vivado, whose placer and silicon-correlated timing
model are substantially better. **On the narrow question of why this design
will not close, the toolchain is a real part of the answer**, and Vivado would
likely close it.

Three things that follow, worth keeping separate:

- **It is not the board.** The canonical image passes 44/44 on this unit.
- **It is not a miscompile.** A miscompile is deterministic; this is not.
- **It would not hit every design on this flow.** LUCAS and RPLUCFG sit near
  80 MHz routed against a 50 MHz clock — 60% headroom, never a problem. Padé is
  the only design in the project pushing the flow's limits. The honest framing
  is not "openXC7 is broken" but "openXC7 gives up perhaps 40% of placement
  quality, and exactly one design needs it."

**Still unproven, and the thing to guard against asserting:** that timing is the
mechanism *at all*. A CDC or handshake soundness bug between the SPI domain and
`clk_fast` would produce every symptom on record — intermittent on identical
bitstreams, placement-sensitive through metastability resolution, the same wrong
value when the same logical bit is mis-captured, and simultaneous corruption of
lanes B and D. That would be a **design** defect that neither toolchain would
catch and that closure would not fix.

## The campaign — 120 measurements, and Fmax is not the mechanism

Run by GTP with `tools/bench_pade_campaign.py` (`84a510e`). Campaign
`build/pade_campaigns/20260804_214716/`. **Canonical control 20/20, zero
infrastructure errors** — the run is valid.

Sorted by routed Fmax:

| Routed | Build | `A7_FREQ` | Rate |
|---|---|---|---|
| 25.38 | v1 S139 | 2 | 10/10 |
| 26.88 | v2 S139 | 2 | 10/10 |
| 29.75 | v1 S149 | 2 | **8/10** |
| 33.44 | v2 S131 | 50 | 10/10 |
| **34.46** | **v1 S127** | 50 | **0/10** |
| 35.48 | v2 S127 | 50 | 10/10 |
| 37.44 | v1 S137 | 50 | 10/10 |
| 37.98 | v2 S137 | 50 | 10/10 |
| 38.18 | canonical | 2 | 20/20 |
| **40.35** | **v2 S149** | 2 | **0/10** |
| 42.17 | v1 S131 | 50 | 10/10 |

**Zero correlation with Fmax.** The slowest build is perfect; the
second-fastest is 0/10; the failing freq-50 build sits between two perfect ones
one MHz either side. **`A7_FREQ` is dead too** — failures appear in both groups.

Per the contract's own N≥20 bar, **no 10/10 build is called clean.**

### Three things this retracts

1. **The timing hypothesis, in every form tried.** Fmax, closure at 50 MHz, and
   the `A7_FREQ` constraint are all ruled out by direct measurement.
2. **My single-shot bench results from earlier the same evening.** I recorded
   v2 S131, v2 S127 and v1 S137 as FAIL. All three are **10/10**. Only v1 S127
   agreed. Three of four wrong is systematic, not luck.
3. **The `D5` signature, which I overstated.** I claimed every failure carried
   `D5` where the correct value has `55`. Across GTP's larger sample it is
   **13 of 25**, with **23 distinct A words**. It is real but not invariant, and
   it was five samples talking.

### The live lead — readiness, not timing

The procedural difference between my failing runs and GTP's passing ones is
that **GTP's harness waits 1 second after reboot before capturing; mine
connected as soon as the CDC port appeared.**

If that delay is what separates them, then querying the sidecar too soon after
configuration returns wrong answers — a **readiness/sequencing** defect, not a
timing one. It would also explain the apparent intermittency, and it is
consistent with GTP's Part C finding that output-only captures cannot
discriminate between Horner, inverter handoff, and final multiply.

**Cheap decisive test:** re-run a 10/10 build with the settle removed. If it
fails, the bug is real and was found by measuring badly.

### Tranche status

- `gtp_contract_pade_intermittency_2026-08-05.md` — **complete.** Findings in
  `gtp_findings_pade_intermittency_2026-08-05.md`, signature words in
  `pade_intermittency_signature_words_2026-08-05.csv`.
- `gtp_contract_rns_check_pipeline_2026-08-05.md` — **STOPPED BY ITS OWN ENTRY
  GATE.** It required Fmax to correlate with reliability. It does not. Do not
  build it. The gate worked exactly as intended and saved the effort.

## `A7_FREQ` is documented, not deleted

The 08-03 handover flagged that every documented Artix-7 build passes
`A7_FREQ=2` while `build_a7.sh:122-127` has defaulted it to 50 since `84294ab`.
**The obvious remedy is wrong.** A routed timing miss is a nextpnr `ERROR` and
`build_a7.sh:20` runs `set -euo pipefail`, so stripping the override makes the
documented commands abort at P&R with no bitstream. `A7_FREQ=2` is load-bearing.

So `2ac4ae9` documents the semantics instead: canonical note in
`SOUTHBRIDGE_SPI_PROTOCOL.md` next to the `clk_fast`/SCK table, cross-referenced
from `build_and_bringup_guide.md`, `toolchain_setup.md`, `AGENTS.md` and
`CLAUDE.md`. It retracts `LUCAS_QUICKSTART.md`'s claim that `A7_FREQ=2` is "a
low-speed bring-up profile" — LUCAS builds at `A7_CLK_DIV_LOG2 = 0`, so there is
no low-speed clock.

**Scoped to the coreless class.** Core spins run `clk_fast` at 781.25 kHz, so
the `A7_FREQ=2 A7_CLK_DIV_LOG2=6` commands for `rplu2core` and `su3share` are
*over*-constrained and correct as written.

Evidence records were deliberately left alone — `hardware_evidence.md`,
`CURRENT_STATUS.md`, the paper tables and archived handovers record how cited
bitstreams were actually produced.

## The burned-seed register was wrong by 15 of 34

`92cac25`. The register listed 19; `build/` holds artifacts for 34. Missing:
`37 43 47 59 61 71 73 83 89 97 101 103 107 109 113`.

**Provenance:** `gtp_contract_fp4_seed_split_2026-07-31.md:53-54` nominated
exactly those 15 as seeds to draw from. They were consumed on 2026-07-31 and
never folded back, so the "safe to use" list silently became the burned one.

Two agents then picked from the stale list believing it fresh — the 08-04
contract chose seed 97 and asserted "seed 97 is unburned" when S97 artifacts had
existed four days, and I picked 37/43/47 the same way. Neither collided, because
the `RPLU2PADE_*` prefix differs from the `FP4EVIDENCE_*` that consumed them.
That was luck, not the register working.

**Stop hand-maintaining it.** The command is the authority:

```sh
ls build/ | grep -o '_S[0-9]\+' | sort -u -t S -k2 -n | tr '\n' ' '
```

Limitation: only variant-tagged artifacts carry `_S<n>`. A production-named
build records its seed solely in its metrics note, so the output is a **lower
bound**, never proof an untagged seed is free.

## INA226 capture — runbook fixed, bench prep unblocked

`8980ae2`. The chain is sound: contract sha256 still matches (`58b37ec5…`),
`test_ina226_capture.py` passes 28 checks, all four referenced tools exist, and
the manifest is well-formed. No captures exist yet; all 30 `csv_sha256` are null.

Five errors would have bitten at the bench:

1. **Manifest path.** Every command said `capture_manifest.json`; the file is
   `manifest.json`. Errors with `No such file or directory` at all four sites.
2. **`init` would clobber the manifest** — a bare `write_bytes` with no
   existence check (`ina226_capture_pipeline.py:390`). Step 1 now says not to
   run it.
3. **Probe mismatch would void the session.** Step 3 printed `dc_fan_v1` while
   the manifest pins `tamiya_75026_v1`. Enforced per row at
   `ina226_capture.py:294` (and `:296` for phase) — but only at `seal`/`verify`,
   *after* the physical capture, with re-running the session as the only fix.
4. **`pyserial` is only in `.venv`**, not system Python.
5. **`--supply-limit-ma 600` sat next to a 280 mA actuator.** Replaced with real
   values.

Added: a block-0 shakedown with paste-ready commands and the
ascending-current check to run before committing to blocks 1-9, and the warning
that **the Pico 2 cannot be both SPI southbridge and MicroPython logger** —
flashing the logger displaces `rp2350_spu_diag` and breaks the documented
resting state.

## Standing hazards

- **Read the LAST `Max frequency` line, never the first.** Reading the
  post-place estimate as a result produced the retraction above.
- **Archive the `.nextpnr.log` with the `.bit` and `.fasm`.**
- **Never invoke `build_a7.sh` against an existing artifact name**, and never
  omit the stage argument. An irreplaceable bitstream died this way on 08-03.
- **`FP4_STRUCTURED=0` without `FP4_EVIDENCE=1` writes the canonical name.**
  `FP4_STRUCTURED=0` equals `FP4_PRODUCTION_STRUCTURED`, so `INVERTER_VARIANT`
  resolves empty (`build_a7.sh:102-106`) and the build targets the
  silicon-verified production artifact. Echo the resolved name before every run.
- **Check `spu_strategy/` for an active contract before starting any tranche.**
  It is gitignored, so a clean `git status`, a clean `git log` and the handover
  can all look idle while a same-day contract assigns the work to GTP. This
  happened today.
- **Contracts can carry false premises.** The 08-04 contract's seed claim and
  its central Fmax table were both wrong. Audit the tasking document, not only
  the delivered work.
- **Stage explicit paths, never `git add -A`.** Shared worktree.
- Synthesis is not bit-reproducible. **SCK ≤ clk_fast / 6**, silicon-confirmed.
- Never use `--ignore-loops` or `--timing-allow-fail` to obtain a pass.
- `run_all_tests.py` treats any `FAIL` substring anywhere in a bench's output as
  a failure.

## Archives created

- `build/evidence_archive/pade_v1_pass_2026-08-04/` — the canonical
  silicon-proven 5/5 Padé bitstream `d411692c…`, with `MANIFEST.sha256`. **It
  had never been archived**, despite being the shipping image, and it lives
  under exactly the filename a default `rplu2pade` build overwrites.

`build/` is gitignored — these live on this machine only.

## Open / next

1. **DONE — the adverse pair was benched, and then some.** All six builds ran;
   see "The bench result" above. Outcome: the inverter is exonerated and the
   fault is intermittent. Next work is
   `spu_strategy/gtp_contract_pade_intermittency_2026-08-05.md` — a freq-2 build
   matrix and, more importantly, a **committed bench harness** that reports pass
   rates over N runs instead of single shots.

   | Build | Routed | Bitstream | SHA-256 (first 16) |
   |---|---|---|---|
   | **v2** seed 137 | **37.98 MHz** | `build/spu_a7_100t_RPLU2PADE_FI1B0_S137.bit` | `1c0e5556afedd00d` |
   | **v1** seed 127 | **34.46 MHz** | `build/spu_a7_100t_RPLU2PADE_FI0B0_S127.bit` | `5c36ad0a592584fb` |

   Both archived with their `.pnr.fasm` **and** `.nextpnr.log` at
   `build/evidence_archive/pade_adverse_pair_2026-08-04/` with a
   `MANIFEST.sha256`. Canonical `RPLU2PADE.bit` verified `d411692c…` unchanged
   before and after packing; it was held read-only for the duration.

   ```sh
   openFPGALoader -c dirtyJtag --freq 1000000 \
     build/spu_a7_100t_RPLU2PADE_FI1B0_S137.bit          # the FASTER v2
   # then over the rp2350_spu_diag console, run the five Padé cases.
   # seven_over_three: expect 0x55555557 (= 7·3⁻¹ mod M31)
   #                   the recorded failure returned 0x0CA45881
   ```

   Then repeat with the v1 image. **Read the outcomes as a pair:**

   | v2@37.98 | v1@34.46 | Reading |
   |---|---|---|
   | fails | passes | **Timing conclusively excluded.** The faster build fails and the slower one works — margin cannot be the mechanism. Go to the netlist diff. |
   | fails | fails | Not a v1/v2 discriminator at all. Something about these seeds or `--freq 50`; re-test the canonical v1 to separate it. |
   | passes | passes | The defect does not reproduce at these seeds. `seven_over_three` may be placement-specific — a much narrower and more interesting problem. |

   > Both designs **failed timing** at `--freq 50`. Packing them is deliberate,
   > not a workaround: v1 already fails to close *and* passes 5/5 on silicon, so
   > non-closure demonstrably does not predict behaviour on this board. No
   > `--timing-allow-fail` was used and nothing was coerced into reporting a
   > pass.
2. **INA226 block 0** — fully unblocked, runbook corrected. Capture the three
   sessions, confirm mean current ascends across the classes, then commit to
   blocks 1-9. Phase A of the SOM product roadmap and the lead commercial wedge.
3. **~~Netlist/FASM diff~~ — DROPPED.** It was licensed by a conclusion the
   bench then overturned. The fault is intermittent and hits both inverter
   arms, so a static netlist comparison cannot explain it. Do not spend on this
   until Part C's signature analysis says which stage to look at.
4. **SU3's full oracle** — the one soft cell in the eight-spin sweep. Bench work.
5. **Rebuild remaining spins against the `PULLUP` XDCs** — hygiene only.
6. **Show HN timing** — still the project owner's call.

> **Device assignment for the 2026-08-04 evening session, confirmed with the
> project owner: RP2350-Zero = SPI southbridge, Pico 2 = INA226 logger.**
> Two devices, two roles, so items 1 and 2 do **not** contend and both proceed
> independently. No `rp2350_spu_diag.uf2` re-flash is needed.
>
> This is the natural assignment: the firmware carries explicit RP2350-Zero SPI
> pinsets (`CMakeLists.txt:39-55`), while the logger is a MicroPython `main.py`
> that any RP2350 runs.
>
> **Build the southbridge with `-DSPU_RP2350_ZERO_HEADER_SPI=ON`.** Without it
> `SPU_SPI_PIN_DEFS` is empty and the compiled-in defaults are **GP16-19**
> (`rp2350_spu_diag.c:47-57`), not the GP0-3 the header is wired to. The result
> is a silent total failure that looks exactly like the all-zeros symptom which
> cost three weeks in July. The alternative pinset,
> `SPU_RP2350_ZERO_G25_SPI`, is GP20-23; setting both is a `FATAL_ERROR`.
> Already documented in `LUCAS_QUICKSTART.md:77`,
> `SOM_SIDECAR_QUICKSTART.md:74` and `SOUTHBRIDGE_SPI_PROTOCOL.md:116`.
>
> `PICO_BOARD` is hardcoded to `pico2` at `CMakeLists.txt:4` — a plain `set()`,
> so `-DPICO_BOARD=` on the command line is ignored. Harmless here: the RP2350
> is the same silicon, stdio is USB CDC, and no firmware target references a
> board-specific pin (no `PICO_DEFAULT_LED_PIN` usage anywhere).
>
> The packing half of item 1 needs neither bench nor either device.

**Done this session, previously listed:** `AGENTS.md` table hygiene (`d399cd4`).

## Useful restart commands

```sh
git status --short --branch
ls -t spu_strategy/*.md | head          # active contracts — gitignored
python3 run_all_tests.py                # expect 184/184
ls build/ | grep -o '_S[0-9]\+' | sort -u -t S -k2 -n | tr '\n' ' '
```

Bench resting state for comparison: Wukong holding `TENSEGRITYLINK`, Pico 2
running `rp2350_spu_diag` at 125 kHz, `0xB3` returning `version=1`. **If the
INA226 logger was flashed, the Pico 2 will not match this until
`rp2350_spu_diag.uf2` is restored** — that is expected, not a new fault.
