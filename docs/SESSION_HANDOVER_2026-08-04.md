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

## GTP tranche — IN FLIGHT, not a result yet

`spu_strategy/gtp_contract_a7_timing_closure_2026-08-04.md`, rewritten this
session after Part C invalidated its premise.

**Part A1 complete — v2 does not close at 50 MHz on any seed:**

| Seed | post-place | routed | Verdict |
|---|---|---|---|
| 127 | 31.30 | **35.48** | FAIL at 50 |
| 131 | 28.97 | **33.44** | FAIL at 50 |
| 137 | 30.96 | **37.98** | FAIL at 50 |

All three ended `0 warnings, 1 error`. nextpnr writes `.pnr.fasm` and
`.pnr.json` *before* raising the timing error, which is why the numbers exist
despite the stage failing. No `.bit` — `pack` never ran.

**Part B (v1 control, same three seeds) was running at 11:01.** Not yet
readable.

> **Do not conclude "the revert stands permanently" from A1 alone.** That
> reading requires v1 to *close*. v1's 38.18 came from a `--freq 2` build and is
> a **floor**, not a measurement — under a 2 MHz constraint the router stops
> optimising as soon as it clears 2 MHz. v1 at `--freq 50` could land anywhere
> at or above 38.18. If v1 also fails to close, "doesn't close" stops
> discriminating and the paired numbers are the entire answer.

Encouraging for decisiveness: v2's seed spread is 33.44–37.98, about ±7%. The
3× scatter that motivated the three-seed design came from `FP4EVIDENCE`, a
different design. For this spin scatter is modest, so a v1/v2 gap of more than a
few MHz will be meaningful.

Still outstanding in the tranche: **Part A0** (rebuild v2 at `A7_FREQ=2` to
recover the lost measurement of the actual failing configuration, ~4 min,
directly comparable to v1's 38.18), Part B, and Part A2 only if something
closes.

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

1. **Finish the GTP tranche** — Part B is the decider, then A0, then A2 only if
   something closes. Audit against the contract's outcome table.
2. **INA226 block 0** — fully unblocked. Capture the three sessions, confirm
   mean current ascends across the classes, then commit to blocks 1-9. Phase A
   of the SOM product roadmap and the lead commercial wedge.
3. **`AGENTS.md` table hygiene** — rows 63/65 are duplicate `rplu2pade` entries;
   rows 64/66 start with `||`, which breaks the table render.
4. **SU3's full oracle** — the one soft cell in the eight-spin sweep. Bench work.
5. **Rebuild remaining spins against the `PULLUP` XDCs** — hygiene only.
6. **Show HN timing** — still the project owner's call.

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
