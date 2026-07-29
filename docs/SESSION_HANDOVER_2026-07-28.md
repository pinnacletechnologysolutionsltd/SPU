# SPU-13 Session Handover — 2026-07-28

## Stop state

- **`origin/master` = `1f9dfaa`, local `master` in sync, nothing unpushed,
  tree clean.** Verified with `git status --short --branch` at time of
  writing, not assumed. (The 2026-07-24 handover claimed "nothing unpushed"
  when two commits were in fact local-only — check, don't trust this line
  either.)
- Full regression independently re-run: **177/177, exit 0**.
- `spu_strategy/` remains gitignored with **0 tracked files**. All GTP
  contracts live there and stay out of the public repo.

## Closed this session

### RPLU v0.2 published — corrigendum, not retraction

- **v0.2 is live: `10.5281/zenodo.21613009`**, resolving from concept DOI
  `10.5281/zenodo.21446712`, with v0.1 (`21446713`) immutable beneath it.
  Verified via the Zenodo API, not assumed.
- Corrected **two** material errors, not one: the parallel conjugate tower is
  **83 clocks, not 76**, and the complete jet inverse is **105 clocks** — not
  the 95 you would get by naively swapping the tower constant, because the
  shadow chain costs 22 clocks rather than 12.
- Measured from historical RTL at `f1e4dbf` in a detached worktree, full
  provenance recorded in `docs/RPLU_V01_LATENCY_CORRIGENDUM_EVIDENCE.md`.
- **Always cite concept DOIs**, confirmed via the Zenodo API rather than
  inferred from numbering: RPLU `10.5281/zenodo.21446712`,
  LUCAS `10.5281/zenodo.21447440`. Note `21447441` is LUCAS's *version* DOI
  and is NOT its concept DOI — using it pins readers to v0.1.

### A real RTL defect found and fixed

`core_boot_ready` was **undriven** on all five `_CORE=0` spins (LUCAS, SU3,
RPLUCFG, RPLU2LIVE, RPLU2PADE): declared as a bare wire, driven only inside
`generate if (_CORE)`, but consumed unconditionally by `u_spi`. Fixed in
`05d1709`. Independently verified across all five spins —
`core_boot_ready = ['0']`, zero undriven `x` nets remaining.

### The P&R rejection — correctly split, still partly open

Two distinct causes, previously conflated:

1. The **one-node** rejection at `746d376` was the undriven net above. That
   source point now routes at **43.20 MHz**.
2. The **230-node** rejection is a **nextpnr-xilinx 0.8.2 limitation**, not
   an RTL defect.

`spu_spi_slave.v` is exonerated structurally, not just in simulation: three
`always @(posedge clk ...)` blocks, four `assign`s on registered signals,
**every output port an `output reg`** — zero combinational input-to-output
paths — and a cycle detector over its synthesized netlist found 3,543
combinational cells with **no cycle**.

**AGENTS.md previously claimed this was "independent of any RTL change."
That was disproved by controlled bisection and has been corrected** (commit
`9f3a4fa`). That claim had misdirected work since 2026-07-15.

### Toolchain migration evaluated and CLOSED

Upstream **nextpnr 0.10 Himbächel XC7** was built side-by-side at
`~/.local/nextpnr-0.10-xc7`; the openXC7 0.8.2 baseline at
`~/.local/openxc7` was left untouched and verified so.

**Both backends fail RPLU2PADE, at different stages:**

| Backend | Timing graph | Routing |
|---|---|---|
| openXC7 0.8.2 | FAILS — 230 unschedulable nodes | never reached |
| upstream 0.10 | PASSES — 0 nodes, **both** clock domains analysed (`clk_fast` 23.74 MHz, `clk_100mhz` 119.76 MHz) | **DEADLOCK** — stuck at `overused=2` for 68,000 iterations, no FASM |

**Do not re-explore migration without new information.** 0.10 trades a
timing-graph blocker for a router deadlock. The `FP4EVIDENCE` harness remains
justified, and the isolation caveat on those measurements stands.

Also proven, and repo-wide in consequence: **openXC7's XDC parser honours no
timing constraints whatsoever.** Garbage TCL (`get_bananas`) is accepted
silently with zero warnings, and deleting the file's only `create_clock`
changes nothing. Writing XDC timing constraints for that backend is dead
text. Documented in `docs/toolchain_setup.md`, `docs/hardware_evidence.md`
§3.2f.1, and inline in `spu_a7_100t.xdc`.

### Structured inverter seed matrix — PASSED, with calibration

> **SUPERSEDED 2026-07-30 — the Fmax figures below are wrong.** Seed 17 was
> re-run on matched source. Its ratio moved 1.152158 → **0.939883**, and the
> **matrix median Fmax ratio moved 1.152158 → 0.971056** — from a 15% apparent
> gain to a 3% loss. Three of five seeds are slower, not two. Wall-clock mean
> is ≈14.6%, not ≈18%. The gate still passes (0.971 ≥ 0.90, now 5/5).
> **Do not quote any Fmax number from this section.** Current figures:
> `docs/FP4_STRUCTURED_INVERTER.md`. The text below is retained unaltered as
> the record of what was believed on 2026-07-28.

Predeclared gate met honestly: median LUT ratio 1.074302 (≤1.08), median
Fmax ratio 1.152158 (≥0.90), 5/5 seeds individually passing (≥4/5 required),
all statistics reported with no dropped seeds.

**Three calibrations are now in `docs/FP4_STRUCTURED_INVERTER.md` and must
travel with any public quote of this result:**

1. "5/5 PASS" does **not** mean uniformly faster. The gate was ≥0.90×
   (*not much worse*), not ≥1.00×. **Two of five seeds are slower in Fmax** —
   seed 41 (ratio 0.902022, cleared by 0.2%) and seed 53 (0.971056).
2. Wall-clock gain is a **range: 1.2% to 31%**, mean ≈18%. Seed 17's 22.6%
   is above median-typical and should not be quoted alone.
3. **Seed 17 is not source-matched** to the other four (LUT 9,415 vs 9,421)
   yet supplies the reported median Fmax ratio. Excluding it, the four-seed
   median is ≈1.096. Verdict survives either way.

### Other

- **Stale-FASM guard** landed (`eccb2f3`, `build_a7.sh:316`): packing now
  aborts if `.pnr.fasm` is not newer than its synthesized `.json`. Closes a
  real hazard where a "successful" build could silently ship stale logic.
- **LUCAS paper**: added the ℤ[ζ₅] limitation as future work (`1f9dfaa`).
  ℚ(φ) is the real quadratic subfield of ℚ(ζ₅), so ℤ[φ] carries quantum
  dimensions and diagonal φ⁻¹ F-symbols but **not** the Fibonacci braid
  phases (R-matrix eigenvalues are primitive 5th roots of unity). Nothing in
  the paper was false; the omission would have invited a reviewer to assume
  the ring was chosen without checking. **Source now leads the v0.1 deposit;
  this is not a corrigendum and does not warrant one.**
- SPU expansion unified as **Synergetic Processing Unit** (`7d75920`).

## Bench hardware

**Ordered:** Tamiya **75026** Mini Motor Set (PB Tech) and the **ZK-5KX**
bench supply.

The Tamiya was chosen over the Jaycar YM2706 and an unbranded 130-size motor
because it is the only one with a *rated operating* current from a real
manufacturer: **280 mA at optimum voltage/load**, citable part number,
published specs. At 280 mA the shunt sits at 28 mV against the 75 mV abort
threshold — comfortable, where the Jaycar's 690 mA max-efficiency figure sat
right on the line. It also ships with a **rubber tube**, which solves the
repeatable-friction-load problem for the `elevated_load` and
`current_limited_stall` phases.

**Suggested manifest:** `--nominal-bus-mv 3000`,
`--actuator-model 'Tamiya 75026'`, `--actuator-continuous-ma 280`,
`--supply-limit-ma 280`. Expect normal ≈150 mA, elevated ≈220 mA, stall
CC-clamped at 280 mA.

**PSU (salvaged, JBL Cinema SB180):** measured **18.44 V** open-circuit,
**red = positive, black = common**. No label; JBL don't publish the adapter
rating, but comparable JBL 19 V soundbar supplies are 2–3 A against your
~200 mA need. Ample. Mains-side safety rule stands: **unplug at the wall**,
don't assume primary caps are discharged.

**The CC clamp is the ZK-5KX itself** — no extra hardware. The INA226
measures current but does **not** limit it; nothing else restrains stall
current. Verify the limit before block 0 (runbook §2 step 2).

**Interlock BOM finalised — U2 reverted to TLV3011B** (`16f2f3d`). LCSC
sourcing made the original part available, and it is *preferred*, not merely
equivalent: its noninverting input is externally accessible, restoring the
hysteresis feedback path MAX9063 cannot provide. **Divider changes with the
reference: 137k/100k** for TLV3011B's 1.242 V (not 137k/10k for MAG9063's
0.2 V). **Adapter is SOT-23-6, not SOT-23-5.** Two same-family traps
recorded: **TLV3012 is push-pull** where this circuit needs open-drain, and
**MAX9062 has inverted polarity**.

## Task list (human side)

1. Solder Pico 2 headers.
2. **Send the Dr. Thomson email** — drafted, verified, and deferred twice.
   Use LUCAS's **concept** DOI `10.5281/zenodo.21447440`, and tighten "the
   first component paper" (there are two). All links verified: repo is
   public, `ICOSAHEDRAL_QUADRAY_CATALOG.md`, `IROTC_SPEC.md` and
   `hardware_evidence.md` §3.2k.1 all exist and say what the draft claims.
3. Place the LCSC order (interlock BOM above). **Add a spare INA226** — the
   frozen contract has no partial-redo path, so a mid-capture module failure
   costs all thirty sessions. **No camera** — vision is explicitly parked and
   there is no feature pipeline to receive it.
4. Once INA226 + Pico 2 + breadboard + ZK-5KX + motor are ready: run the
   physical capture. **Verify phase-current ordering on block 0** (normal <
   elevated load < CC clamp) before committing to all thirty.
5. Interlock breadboard bring-up steps 1–5 once parts arrive → then
   `TENSEGRITYLINK` → then SU3 Path B.

## Open / next

- ~~**Seed 17 re-run on matched source**~~ — **DONE 2026-07-30.** Both arms
  now reproduce the other four seeds' synthesis hashes bit-identically. The
  result was adverse: matrix median Fmax ratio 1.152158 → **0.971056**. See
  the superseded banner above and `docs/FP4_STRUCTURED_INVERTER.md`.
- **Default-switch decision** for the parallel structured inverter. Per
  project rule, it gets its own commit, separate from evaluation. **The case
  changed materially on 2026-07-30**: it is now "7.4% more LUT for a ~3%
  median Fmax loss, with 2/5 seeds substantially faster", not "15% faster for
  7% area". The wall-clock gain survives only via the 74-vs-83 cycle count.
  Worth understanding why seeds 67/79 gain 22-30% while 17/41/53 lose before
  deciding.
- **Tang ABC9 non-termination** — the one v2-exercising consumer build that
  never closed (no verdict after 2:01:51).
- **DSP `CARRYCASCIN` cascade defect** — the honest next lead on the
  production top. Both toolchains touch it, which makes it more likely real
  than either backend's individual quirk.
- **Show HN timing** — still an open judgment call for the project owner.
- **Quantum/anyon outreach**: pursue *no*, promote *cheaply and later* —
  after the INA226 result, in the same warm-network pass as Thomson, and to
  a topological-QC academic. **Xanadu is the wrong target** (photonic/CV, not
  topological; φ has no privileged role there).

## Standing hazards

- **Synthesis is not bit-reproducible in this environment.** Never re-run
  `synth` against an existing artifact name. Burned seeds: **1, 2, 7, 13, 17,
  29, 31**; 41/53/67/79 used by the seed matrix.
- **Never overwrite evidence artifacts.** `build/spu_a7_100t_RPLU2PADE.json`
  (2026-07-19) and its `.nextpnr.log` (2026-07-06, a *successful* run) are
  evidence. Copy to scratch.
- **Paper build paths differ.** `rplu_paper.tex` uses a root-relative
  `\input{docs/...}` and must be built **from the repo root**;
  `LUCAS_MAC_PAPER.tex` uses a docs-relative `\input{...}` and must be built
  **from `docs/`**. Getting this wrong looks like a missing-file error.
- Never use `--ignore-loops` or `--timing-allow-fail` to obtain a pass.

## Useful restart commands

```sh
git status --short --branch
python3 run_all_tests.py
python3 tools/ina226_capture_pipeline.py --help
openFPGALoader -c dirtyJtag --detect
```
