# Session handover — 2026-08-09

**Written as work landed.** Previous:
[`SESSION_HANDOVER_2026-08-08.md`](SESSION_HANDOVER_2026-08-08.md), whose
"Plan for 2026-08-09" is now executed — items 1, 2 and 3 are done, item 4 was
dropped, item 5 remains.

## One-line state

**Both open silicon-evidence gaps are closed.** The Karatsuba candidate — the
production default since 2026-07-23 — now satisfies all five pre-registered
swap criteria, and the LUCAS 200-step claim that had sat unbacked since
2026-07-17 is evidenced.

## What landed

| Commit | What |
|---|---|
| `a6e462d` | Sweep complete: criteria 1-3 met; stale-metrics trap found and fixed |
| `125aabf` | Criterion 4 met; the swap turned out to have shipped on 07-23 |
| `95a188f` | TENSEGRITYLINK gap recorded as the top bench item |
| `d0d8c3c` | Four-act campaign plan |
| `26a646d` | Four SD traps recorded |
| `78cb516` | **§3.2l.1 — TENSEGRITYLINK four acts proven on the candidate, 10/10** |
| `714ce8c` | All five swap criteria met |
| `0ac49ae` | `spu_host` `connect()` fixed for already-booted boards |
| `317a0f4` | **§3.2e.7 — LUCAS 200-step zero-drift proven, 10/10** |
| `7c59b57` | This handover |
| `0f8e639` | Bench-supply characterisation procedure (DMM-only, no INA226 needed) |
| `8451aae` | Sweep + four-act drivers promoted into `tools/` |

## Karatsuba — evidence chain complete

| # | Criterion | Status |
|---|---|---|
| 1 | Every candidate build meets 25 MHz | MET — worst 31.46 MHz (+6.46) |
| 2 | Routing reliability within +1 of reference | MET at the limit — PROBE 1 non-convergence vs 0 |
| 3 | LUTX ≤ +1 %, FFX ≤ ref, DSP equal | MET — LINK +32, PROBE −44, both −176 FFX, DSP ±0 |
| 4 | Formal + regression at the swap commit | MET at `a6e462d` — 3/3 sby, zphi 46/46, tensegrity 48/48 |
| 5 | Four-act bench, N ≥ 10 + positive control | MET — 10/10, §3.2l.1 |

No criterion was amended after seeing results. **No Fmax claim is available in
either direction** and none is made: seed spread is ~9-21 MHz against an arm
median difference of ~2 MHz.

The **PROBE candidate cell is n=9**, missing seed 1, which did not converge
(`build/zk_pnr_campaign/20260808_194219/NONCONVERGED_PROBE_ZK1_S1.md`). Quote
it that way.

## What was actually wrong today — three false alarms and one real misread

Three things presented as broken hardware and were not:

1. **Card reader** — never enumerated; unrelated to the bench.
2. **SD supply and rate** — a bare 3V3 adapter, briefly run at 5 V (recorded in
   §3.2l.1 as a limitation), then `FR_DISK_ERR` at the 8 MHz post-init rate
   while the 400 kHz init passed. Runs at 1 MHz.
3. **`ERR no SD card` / `file not found`** — the fixtures live under `TGR/`,
   and the RP2350's microSD bus (`spi1`, GP10-13) is independent of the J11
   link (`spi0`, GP0-3), so link health says nothing about SD.

And one real misread, mine: **`tgrstatus version=0` is the signature of an
unconfigured FPGA, not a healthy idle sidecar.** I reasoned from the RTL that
`header_version` resets to 0 and called it expected. A configured idle sidecar
reports `version=1`. The bitstream had never been loaded this session; every
zeroed readback was saying so. **Check the FPGA is configured before
interpreting any SPI readback** — an unconfigured device answers plausibly with
zeros, and `status raw=00 00 00 00` versus `5A 00 10 00` is the tell.

## Traps and fixes worth carrying

- **`spu_host` `connect()`** raised against any already-booted board, so
  `lucas_demo.py` only worked immediately after a reset. Fixed in `0ac49ae`.
- **Stale metrics survive a killed build.** A cancelled P&R leaves the previous
  campaign's metrics file under the same name; seed-completeness cannot see it.
  The analyser now filters on the campaign's `started_utc`. This silently
  inflated PROBE candidate to n=10 before it was caught.
- **Retiring a gate needs a search for what cites it.** §3.2l said the four-act
  work was "gated on the power-ready interlock" while the interlock's removal
  was recorded only in the roadmap and BOM. It sat unblocked for five days.

## Delegation — batch claim audits dropped

Two GTP tranches, two failures, both caused by contract design rather than
execution: v1 under-reported (23 claims presented as the population), v2
over-claimed (141 of 208 rows `BACKED` while naming no ledger section).
Replaced by ledger discipline at the point of writing — see **Claim discipline**
in `AGENTS.md`. Both contracts are marked CLOSED in `spu_strategy/`.

**The rule that came out of it:** delegate what a script can check, keep what
needs a judgement call. GTP compute remains well suited to P&R sweeps, long
formal runs, and pipelining searches — work whose output is verifiable from
artifacts rather than from a report.

## Open

- ~~**ROBOTICS spin synth re-check**~~ — **DONE 2026-08-09, PASSES.**
  `bash hardware/boards/artix7/build_a7.sh 100t robotics synth` completes clean:
  rc=0, **zero errors**, 100 warnings (in line with other spins), netlist
  `build/spu_a7_100t_ROBOTICS.json` written, 56,330 cells at `spu_a7_top` with
  47 DSP48E1, 8,483 FDCE, 2,514 CARRY4. The last carried bench prerequisite is
  cleared — the spin is ready for its next Wukong session, which was the point
  of the re-check. Note this is synthesis only; P&R and a board run are
  separate.
- **Composition/adapter policy** — the 08-07 service-composition boundary still
  defers shared datapaths until a cross-domain adapter policy and an
  oracle-backed composition trace exist. Nothing produces either; the repo
  blocks its own next integration step. Needs John's judgement on product
  claims.
- **INA226** — order the R100 spare; complete the electrical rebuild (soldered
  harness, star ground, flyback, series R < 0.1 Ω, true current limit by DMM)
  **before** the part arrives, because the runbook's freeze rule forbids
  changing the rig after block 0.
- **Padé 50 MHz** — works at 25 MHz with half throughput; datapath pipelining
  is the route back. **Contract issued to GTP 2026-08-09:**
  `spu_strategy/gtp_contract_pade_pipelining_2026-08-09.md`. Chosen because
  every gate is machine-checkable from artifacts — a missed 50 MHz constraint
  is a hard nextpnr error under `set -euo pipefail`, so completion *is* the
  proof — which is the opposite of the judgement-heavy audits that failed.
  Silicon validation stays with us; GTP delivers to P&R evidence and leaves the
  tree uncommitted. Requires five seeds, not one, and says explicitly that "it
  cannot close without unacceptable cost" is a legitimate result.
- ~~**Sweep tooling**~~ — **DONE `8451aae`.** `tools/zk_pnr_sweep.sh`,
  `tools/zk_analyse.py`, `tools/tgr_four_act.py`, listed in the AGENTS.md
  command table, repo root from `git rev-parse` rather than a hardcoded path.
  Promoted because §3.2l.1 cites the four-act driver's output directly and the
  swap criteria rest on the sweep — evidence-producing tools do not belong in a
  session scratchpad.

- **Bench supply characterisation** — procedure added `0f8e639`
  (`INA226_CAPTURE_RUNBOOK.md` §2, recording table in the handoff). Needs only a
  DMM and the actuator, so it is doable now, and it is a hard prerequisite for
  the manifest re-`init`: `init` freezes `--supply-limit-ma` into all thirty
  sessions. Five readings minimum per quantity; the 2026-08-06 figures
  (3100 mV, 307.4 mA against a 280 mA display) are single-shot priors to be
  replaced.
