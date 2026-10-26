# QCG-0 development evidence — provenance

Status: **exploratory, implementer-generated development output.** Not independently certified, not a registered P0 result, no acceptance standing. Not a certified reference.

| File | Original path | SHA-256 |
|---|---|---|
| `pareto_02.json` | `build/qcg_0/dev/pareto_02.json` | `f92a0196…b5fb` |
| `integration_01/results.json` | `build/qcg_0/dev/integration_01/results.json` | `06bd67ef…8494` |
| `integration_01/{readback.txt,results.sha256,RUNNER_DONE}`, `integration_01.stdout`, `integration_01.stderr` | `build/qcg_0/dev/` | full list in `SHA256SUMS` |

Copies are byte-identical to the originals (`cmp`); originals untouched.

**What each is**
- `integration_01/`: the single direct `stages.build()` development check (2026-10-23, `run.py --out`, not `launch.sh`, 60 s / 1 GiB / 4 MiB limits; verdict PASS, readback OK, 24/24 mutants, 243,609 counted operations). It was produced **before** the PHFD role-matching fix, so its `pareto` section classifies PHFD as a conventional arm and is superseded for Pareto purposes by `pareto_02.json`. Its other sections are unaffected by that fix.
- `pareto_02.json`: `stages.run_cells()` rerun once after the fix (sequential conventional arms = Horner, Bezier, TS, FD, PH exactly). Pareto and equivalence sections only. Historical observation; not to be regenerated.

**Environment:** Python 3.14.8, GNU coreutils 9.12 `timeout`, util-linux 2.42.4 `prlimit`, Linux. **Source revision:** `research/qcg_0/p0/` is untracked, so no commit identifies it. Repository HEAD was `12c1e4e` (worktree dirty, shared). The `p0` source state is identified only by the draft `PINS.sha256` (regenerated after the fix; the integration run verified the earlier draft). `PINS.sha256` remains a draft.

**Boundaries:** the sequential and Cell B W31 observations inside `integration_01/results.json` are uncertified outputs, not expectations. The two S1 SIGNALs (PH3, PH5; C1 vs FD) are exploratory flags under the registered 20% trigger and guard rules, not measured CPU/GPU/FPGA speedups.
