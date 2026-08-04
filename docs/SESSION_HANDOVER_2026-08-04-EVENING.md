# SPU-13 Session Handover — 2026-08-04 (evening close)

Companion to `SESSION_HANDOVER_2026-08-04.md`, which covers the day's earlier
work. This one closes the Padé arc and states where to resume.

## Stop state

- **Tree clean, `master` == `origin/master`.** Verify yourself.
- **Regression 184/184**, including the new `PADE_DEBUG_TRACE` variant in
  `PARAM_VARIANTS`.
- **No RTL fix was attempted.** The structured inverter remains default-off
  (`21bdfde`); the defect is contained, not resolved.
- Bench idle. INA226 untouched — see
  [`INA226_SESSION_HANDOFF.md`](INA226_SESSION_HANDOFF.md), which is standalone
  and needs nothing from this document.

## The headline: the Padé fault is placement-sensitive

`gtp_contract_pade_localisation_2026-08-05.md` **stopped at its Part C gate.**

| | |
|---|---|
| Canonical control | 20/20 PASS |
| **Instrumented v1 seed 127** | **10/10 PASS** |
| Same build, uninstrumented | **0/10** |

Adding observation-only instrumentation to a **deterministically failing** build
made it pass. Part D was not executed and **no trace was interpreted** — which
is correct: a trace from a build that no longer reproduces the fault describes a
working design while looking authoritative.

Campaign `build/pade_campaigns/20260804_224827/`, findings in
`spu_strategy/gtp_findings_pade_localisation_2026-08-05.md`, instrumentation
`353a1b3`, candidate `717876b0dee3baeb…`, routed 33.83 MHz, artifacts archived
at `build/evidence_archive/pade_localisation_seed127_trace_2026-08-05/`.

**Two gates in two tranches have now stopped work that would have been wasted.**
Writing speculative follow-on work *with a stop condition* is the practice that
paid; keep doing it.

## A correction I owe to my own earlier conclusion

Earlier today I wrote that **"timing is dead in every form tested."** That is
**too strong**, and the placement result is what exposes it.

The campaign showed no correlation between **reported Fmax** and reliability.
But Fmax is a **single number describing the single worst path**. It says
nothing about whether a *particular* net in the Padé datapath is marginal in a
*particular* placement. Two builds can report the same Fmax with completely
different slack on the path that actually matters.

So the accurate statement is narrower:

> **Reported Fmax does not predict reliability.** A placement-dependent marginal
> path has *not* been ruled out — and the Part C result, where a placement change
> alone flipped 0/10 to 10/10, is positively *consistent* with one.

Checked and also negative: the **slack histograms** of the matched seed-127 pair
(v1 0/10 vs v2 10/10) do not discriminate — both carry thousands of
negative-slack endpoints at the 50 MHz constraint, worst buckets −9018 vs
−8182 ps. Do not spend time on histogram comparison.

Also unavailable: this `nextpnr-xilinx` build has **no `--report` support**, so
the conditional at `build_a7.sh:309` never fires and no per-path timing JSON
exists for any Artix-7 build. Per-path analysis would need a newer nextpnr.

## The obvious experiment that was never finished

**Run the failing design at a divided clock.** `A7_CLK_DIV_LOG2=1` halves
`clk_fast` to 25 MHz — a 40 ns period against a ~30 ns critical path, so roughly
10 ns of slack where there is currently none.

This was started on 2026-08-04 and **lost to contamination**: the queued build
fired while the worktree was being edited, producing a mixed-RTL pair that had
to be discarded. It was never redone. It is one build plus one campaign.

| Outcome | Reading |
|---|---|
| 0/10 build passes at 25 MHz | The design does not meet 50 MHz and the fault is timing after all. Fix is a divided clock for this spin, or real datapath pipelining. **A shippable answer.** |
| Still fails at 25 MHz | Timing is genuinely excluded and the cause is electrical or structural. |

**This is the highest-value next step.** It is cheap, decisive either way, and
it tests the operating frequency rather than the router's opinion of it.

Note: neither `A7_FREQ` nor `A7_CLK_DIV_LOG2` appears in the artifact name
(`build_a7.sh:106`), so a divided-clock rebuild at an existing seed **silently
overwrites**. Use a fresh seed or copy aside first.

## A timing-closed Padé configuration now exists (2026-08-05)

The divided-clock builds landed. At **`A7_CLK_DIV_LOG2=1`** (`clk_fast` = 25 MHz)
**all four close**, independently verified from the last `Max frequency` line of
each archived log:

| Build | `clk_fast` | Verdict |
|---|---|---|
| v1 S127 (was 0/10 at 50 MHz) | **38.00 MHz** | `PASS at 25.00 MHz` |
| v2 S149 (was 0/10) | **35.53 MHz** | `PASS at 25.00 MHz` |
| v1 S149 (was 8/10) | **30.25 MHz** | `PASS at 25.00 MHz` |
| v2 S137 (control, 10/10) | **40.81 MHz** | `PASS at 25.00 MHz` |

**Every previous Padé build on record missed its constraint. These meet it with
20–60% margin.** Artifacts in `build/pade_clkdiv_study/` with `.nextpnr.log` and
`.pnr.fasm` alongside each `.bit`.

That is a real deliverable independent of the bench result — but note the cost:
a divided clock **halves throughput** for this spin. Acceptable for a
demonstration, and honest because it is documented rather than hidden, but it
matters if the Padé pipeline ever becomes a performance claim.

**The bench campaign has not run yet.** Two attempts were voided at the
canonical control with `usb bulk write failed -9` / `Fail to get version`.
Voiding was correct.

- The adapter is **not dead** — `--detect` returns the A7-100T IDCODE cleanly
  before and after a `usbreset`. `-9` is `LIBUSB_ERROR_PIPE`, a stalled
  endpoint, and `1209:c0ca` has not re-enumerated all session. The trigger is
  sustained load: a campaign is ~110 back-to-back loads.
- **The harness already carries the fix, opt-in**
  (`bench_pade_campaign.py:344`): pass **`--dirtyjtag-usb-id 1209:c0ca`** and it
  resets the adapter before every load. `usbreset` is installed and verified.

**The re-run must include a POSITIVE control** — the un-divided v1 S127
(`5c36ad0a…`, 0/10 at 50 MHz). If the four divided builds pass, that is equally
consistent with *"the divided clock fixed it"* and *"the fault is not
reproducing this session"*, and nothing in the divided builds separates those.
The canonical control proves the bench works; this one proves the fault still
exists. Without it a clean sweep is unreadable.

## What is established, and what is not

**Established:**

- The FP4 structured inverter is **not** the cause — v1 fails too, so the
  `21bdfde` revert rested on a false attribution.
- Failures are **deterministic per build**: v1 S127 0/10, v2 S149 0/10, v1 S149
  8/10, everything else 10/10 across 120 measurements.
- The fault is **placement-sensitive** — observation-only instrumentation
  removes it.
- The bench is sound: canonical 20/20, repeatedly, across sessions.

**Not established:**

- Which pipeline stage is at fault. Free algebraic back-solve over the 23
  distinct failure words gives `popcount(X ⊕ 3⁻¹)` mean 12.6 against 15.5 for
  random — a weak pull toward *"the inverter's output is corrupted"* over
  *"the final multiply got a bad operand"*, but the 4–21 spread cannot localise.
- Whether a placement-specific marginal path is responsible. See above.

## Corrections ledger

Six this session. Recording them because the pattern, not any single error, is
the finding.

| Retracted | Cause |
|---|---|
| The 08-03 v1/v2 margin table | one log's post-place and post-route lines read as two builds |
| "Timing is exonerated, miscompile earned" | over-extended from "v2 is not slower than v1" |
| "v2 passes / v1 fails" | single bench run per condition |
| The `D5` invariant signature | five samples; it is 13 of 25 across 23 distinct words |
| The readiness / settle-delay hypothesis | my settle was **longer**; the real difference was port selection |
| "Timing is dead in every form" | Fmax describes only the worst path (this document) |

**Every one came from too few samples, or from one number standing in for a
distribution.** Two were caught before they cost anything. The countermeasures
are now structural rather than remembered: N≥10 for any bench claim and N≥20
before calling a build clean, pass *rates* as the harness default, and stop
conditions written into speculative tranches.

## Standing hazards

- **A single bench run is not a result.** Use `tools/bench_pade_campaign.py`
  with its fixed named port; do not hand-roll a capture. Hand-rolling with
  `ls -t /dev/ttyACM*` against three devices is what produced the discarded
  data.
- **Read the LAST `Max frequency` line**, never the first — the first is a
  post-placement estimate.
- **Archive the `.nextpnr.log` with every `.bit` and `.fasm`.**
- **Pin builds to a commit and refuse a dirty tree.** A queued build against a
  live worktree produced a mixed-RTL pair that had to be discarded.
- **`FP4_STRUCTURED=0` without `FP4_EVIDENCE=1` writes the canonical production
  name** (`build_a7.sh:102-106`). Echo the resolved path before every run.
- Neither `A7_FREQ` nor `A7_CLK_DIV_LOG2` is in the artifact name.
- **Burned seeds — regenerate, never hand-maintain:**
  `ls build/ | grep -o '_S[0-9]\+' | sort -u -t S -k2 -n | tr '\n' ' '`
- **Check `spu_strategy/` for an active contract before starting any tranche** —
  it is gitignored, so a clean `git status` and the handover can both look idle
  while a same-day contract assigns the work elsewhere.
- **Stage explicit paths, never `git add -A`.** Shared worktree.

## Open / next

1. **INA226 block 0** — the priority. Lead commercial wedge, Phase A of the SOM
   roadmap, no further spend required. Everything verified ready;
   `INA226_SESSION_HANDOFF.md` is self-contained.
2. **The divided-clock test** on the Padé fault — cheap, decisive, never
   finished.
3. **SU3's full oracle** — the one soft cell in the eight-spin sweep.
4. **Rebuild remaining spins against the `PULLUP` XDCs** — hygiene only.
5. **Ecosystem work** — tooling and demonstrations, per the agreed sequence:
   stabilise the repository → prove in silicon → develop the ecosystem → *then*
   campaign. The campaign starts after, not alongside.

**Platform is frozen.** No further hardware spend; ECP5 migration was evaluated
and rejected on numbers (LUCAS needs 120 DSP48E1, ECP5-45F has 72 MULT18X18
total and the RPLU2 probe already uses 72/72; 40 nm versus 28 nm makes a
routing-bound path worse). Build and refine on the FPGAs in hand.

## Useful restart commands

```sh
git status --short --branch
ls -t spu_strategy/*.md | head          # active contracts — gitignored
python3 run_all_tests.py                # expect 184/184
python3 tools/ina226_capture_pipeline.py verify build/ina226_capture/manifest.json
```
