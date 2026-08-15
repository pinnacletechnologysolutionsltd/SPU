# Session handover — 2026-08-15

Evidence-anchoring session. Worked the 08-14 handover's list top to bottom.
Closed T9 and T7.4, and found a third silently-unbuildable flagship spin.

*Written incrementally as work landed, per the 08-01 lesson that a handover
written at a checkpoint goes stale within hours.*

## 1. Repository state

- `master`, clean, in sync with origin at session start.
- Regression **193 PASS / 0 FAIL**, re-run independently twice (once mid-session
  after T7.4 broke it, see §4).
- Five commits, listed below. One further change in flight at time of writing
  (§6).

| Commit | Change |
|---|---|
| `cf4cc4d` | Anchor the silicon evidence ledger to source commits (T9) |
| `511f3f3` | Explain two DIFFERS entries, correct a wrong anchor (T9) |
| `f9754a6` | Export `dissonance` from the standalone wrapper (T7.4) |
| `4f3fc9b` | §3.2k.1 is BUILD_FAILED, and it is not a regressing commit |

## 2. Two items were already further along than the 08-14 handover said

- **The board-build check was already committed** (`239bf4c`, 23:21 the previous
  night). The handover's "next session, item 1" was done.
- **The A7 chipdb already existed.** §4.1 said the sidecar re-validation needed
  `xc7a100tfgg676.bin` generated from a 464 MB `.bba`. It was on disk, dated
  Jun 19. That item was never blocked.

## 3. A7 SOM sidecar — §4.1 closed at the build level

`bc06156`'s `BAUD_COUNTER` change had only been checked through yosys. Full
synth/pnr/pack now passes:

```bash
PRJXRAY_ROOT=$HOME/toolchains/prjxray \
OPENXC7_PYTHON=$HOME/.local/venvs/prjxray/bin/python \
  bash hardware/boards/artix7/build_a7.sh 100t somsidecar all
```

Zero overused wires at routing iteration 4; **80.18 MHz post-routing** against
the 50 MHz constraint. 8,161 LUT / 3,131 FF / 44 DSP / 4 RAMB18, against the
July record's 8,013 / 3,098 / 44 / 4.

**Build only.** The image is `bf4c1614…`, the flashed one was `f22a34e7…`, and
nothing was loaded to a board. §3.2g.6's silicon claim still rests on the July
run. Recorded as §3.6a.

## 4. T7.4 closed — `dissonance` exported (`f9754a6`)

The contract's allowed wording was **false for the named product interface**:
`dissonance` was a `spu4_core` port only. John chose option 2 (add the port and
re-anchor), then chose to extend the probe telemetry so the bench session proves
the signal rather than only re-anchoring a hash.

| Variant | LUT4 | ALU | DFF | Bitstream |
|---|---|---|---|---|
| Baseline (07-08 silicon) | 835 | 390 | 336 | `9599f5e4…` |
| Port only, not exposed | 865 | 390 | 336 | `6457e31e…` |
| **Adopted: port + UART** | **979** | **460** | **336** | **`cbd6f83a…`** |

The port-only row reproduces the 2026-08-14 attempt's figures *and* its
predicted hash exactly, independently confirming both measurements.

Golden line is now `SPU4:P A=0000 B=0155 C=0155 D=0155 R=FF`.

- **`R`, not `E`** — `E=` already means an error code on the IROTC and
  series-stream probes where `00` is healthy; the healthy SPU-4 fixture reads
  `FF`.
- **`R=FF` is correct**, not a fault: the QROT fixture settles at A=0,
  B=C=D=0x155, a residual of 0x3FF that saturates.
- Both testbenches assert `FF` rather than `00`, since `00` is also what a
  stripped or stuck-at-zero port reads.

**The regression caught a real error before it landed** — I wrote the golden
line as `R=00`; `spu13_tang25k_spu4_probe_tb` failed 192/1 on it.

**Inherited defect, documented not fixed.** The residual expression sign-extends
to 17 bits but sums four 16-bit signed addends needing 19, so a large residual
wraps before saturating and can read *small* — a false laminar reading. It is
`spu4_core` behaviour that the wrapper now mirrors deliberately. Fixing it moves
both bitstreams and is out of T7.4 scope. **Worth its own small tranche.**

**§3.2j is superseded, not rewritten.** Its flashed hash and 36-char line stay
untouched. It needs a bench re-run against the 41-char line, N≥10 with a
positive control.

## 5. §3.2k.1 is BUILD_FAILED — and it is nobody's regression

The 08-14 handover recorded this as UNMEASURED, believing the 90-minute kill was
caused by `--placed-svg` / `--routed-svg` / `--detailed-timing-report`. **All
three were removed and it still does not build.**

| Tree | Cells | Placement | Routing |
|---|---|---|---|
| HEAD | 23,081 | succeeds | **livelock**, 317k iters / 8.5 h, ~58,011 of 71,950 arcs unrouted |
| Anchor `6f6ec43` | 22,997 | **fails legalisation** | never reached |

Nothing is near a limit: 52% LUT4, 37% DFF, 15% MUX2_LUT5, 1/56 BSRAM.

**Ruled out:** a regressing commit (the trees differ by 0.37% yet fail in
*different phases*, and HEAD places where the anchor does not); `5399b4c`, the
prime suspect, which flipped `USE_STRUCTURED_INVERTER` default-on — synthesising
this spin with it at 1 and at 0 gives *identical* cell counts, because the
inverter is unreachable from this top and is pruned; and design growth.

**What remains:** the spin sits at the edge of what the Gowin placer and router
handle, unstable to perturbations far smaller than any intentional change.
§3.2k.1 is **not reproducible from its own sources** and cannot be re-anchored
by rebuilding.

Not excluded: a toolchain move since July specific to this design. The 08-14
toolchain check covered the SOM sidecar, not this spin. Against it, the narrow
`irotc_probe` still builds today.

**Recommendation, recorded in §3.6f: stop treating `irotc_spi` as a Tang 25K
target.** The ledger already says the 25K is "closed as a split-probe regression
target" and that full integration "belongs on an Artix-7 200T / Kintex-class
board". A 51-source full-core spin is what that boundary excludes.

## 6. T9 — the ledger now has source anchors (§3.6)

Corrected counts while auditing: **16** entries carry a bitstream hash, not 14;
**4** lack a build command, not 8 — the earlier figure counted entries recording
only a flash command.

Exactly **one** anchor is confirmed (§3.2g.5 from `f4e271e`). The rest carry a
date-derived *candidate*, labelled as such. Two demonstrated weaknesses:

- **§3.6b — a commit message anchored to a hash its own tree does not build.**
  `bc06156` quotes `af0c5e4c…`; the tree builds `a7d3459e…`, now reproduced
  three times, and `git diff bc06156..HEAD` over the build's complete input set
  is empty. `af0c5e4c…` came from a tree never committed. **Do not use it.**
- **§3.6c — a date-derived anchor that is provably wrong.** §3.2g.2 records
  07-06 → candidate `a71635c`, but `a8b5bdc` (07-07) modifies one of its two
  sources and the current tree still reproduces the flashed hash. True anchor is
  `a8b5bdc` or later — *after* the entry's own date. Reproduction upgrades an
  anchor to a measured range, not a point.

Also: §3.2k's DIFFERS is **closed-explained** (§3.6d) — `73acd91` moved the
IROTC ROM to BSRAM after the 07-10 proof, behaviour preserved. §3.2g.1's
manifest note corrected from a single-cause guess to "five commits, not
isolated".

**§3.6e — a structural limit.** Hash-reproduction anchors narrow probes and is
useless for full-core spins, which absorb every core commit. This decides what
belongs in the manifest.

Stale header facts corrected: regression headline said 173 (is 193), toolchain
line said Yosys 0.50 (0.63+87, and it predates the July proofs), §6 omitted the
openXC7/prjxray toolchain entirely.

## 7. In flight at time of writing

**Board-build check widened from 5 to 21 targets.** 26 Tang scripts exist; 21
were uncovered. Classified by source breadth per §3.6e:

- **11 narrow** (≤11 sources) added as hash-compared.
- **5 full-core** (28–50 sources) added with a new `"check": "builds"` mode —
  gated on buildability, not hash equality, because a DIFFERS says nothing there
  but a BUILD_FAILED says everything.
- **`irotc_spi` deliberately excluded**: BUILD_FAILED and takes ~8.5 h to fail.

Also added a **per-entry build timeout** derived from `approx_seconds`, so one
pathological target cannot stall the check the way `irotc_spi` stalled this
session. `--self-test` still passes.

**RESULTS IN (`42c65e9`) — 15 of 22 targets build, 7 do not.**

| Failing | Cause |
|---|---|
| `som_southbridge` | **SYNTH** — `spu13_axiomatic_gatekeeper` instantiated in `spu13_core`, absent from this spin's `.ys`. Regression from `7b80a59` (08-13) |
| `rotc_probe` | placement, `MUX2_LUT5` after 10001 attempts |
| `southbridge` | placement, `MUX2_LUT8` after 10001 attempts |
| `series_stream_probe` | placement, no BELs remaining for LUT4 |
| `som_probe` | placement, "probably at utilisation limit" |
| `six_step_probe` | timeout at 1200 s |
| `irotc_spi` | router livelock, 8.5 h (§5) |

**None of this is new breakage.** Nothing rebuilt board tops until `239bf4c`,
so these have been broken for unknown periods — exactly as the SOM sidecar was
for four weeks. A backlog becoming visible, not a collapse.

**Six of seven share one signature**: Gowin placement/routing pathology on the
25K, three naming a `MUX2_LUT*` cell directly. That is the mechanism `bc06156`
recorded as "the Gowin mux blow-up remains unexplained" and that the 08-14
handover recommended leaving alone. At one instance that was reasonable; **at
six it is the highest-leverage bug in the tree.**

`som_southbridge` is the exception and the cheapest win — a missing file in a
synth script, two days old.

**`spu4_probe` builds and is bit-reproducible**, so T7, the declared primary
direction, is not blocked by any of this.

## 8. Open

0. **The Gowin mux pathology is now the top technical item.** Six failing
   targets share it. It was deferred at one instance on 2026-08-14 with
   "recommend leaving it"; that recommendation is superseded by the count.
   `bc06156` already refutes two candidate fixes (narrowing the counter to
   `$clog2` bits; replacing the 48:1 dynamic index with a shift register) —
   start from there, not from scratch.
0b. **`som_southbridge` — add `spu13_axiomatic_gatekeeper` to that spin's
   `.ys`.** Cheapest fix in the tree, and a two-day-old regression.
1. **Bench re-run for §3.2j** against the 41-char line (T7.4's cost).
2. **Bench re-run for §3.2g.6** — build-validated only.
3. **`dissonance` width limit** — 17-bit intermediate, 19 needed. Small tranche.
4. **Re-anchor decisions** for §3.2g.1 and §3.2k, both DIFFERS with known or
   partly-known causes. John's call, not mechanical.
5. **§3.2e.6 / §3.2e.7 anchors are unrecoverable** — full hashes, no build
   command, so the env prefix (`A7_FREQ`, `A7_SEED`, `ZPHI_KARATSUBA`) is lost.
6. **§3.2m records 16-hex prefixes**, not full SHA-256, and one bitstream is
   lost. Future sweeps should record full hashes.
7. **A7 targets are still outside the manifest.** The chipdb exists, so this is
   now only a question of build time.
8. Spin-name drift in `build_a7.sh:12` — cosmetic, still unfixed.

## 9. Corrections to earlier beliefs

- The 08-14 handover's §4.1 blocker (A7 chipdb) did not exist; the file was
  already on disk.
- The 08-14 handover's explanation for the §3.2k.1 timeout (SVG/timing flags)
  is refuted by measurement.
- `bc06156`'s commit message contains an anchor hash that its own tree does not
  produce.
- My own prediction that an unconnected `dissonance` port would be stripped was
  wrong — the port-only build measures +30 LUT4 and a distinct hash.
- I proposed batching the INA226 order with the PCB parts; `BENCH_BOM.md` §2
  explicitly says not to, since it is the longest-lead dataset-track item and
  must not queue behind the bench_adapter layout.
