# GEN1-STA-1 closure (2026-11-07)

**Official disposition: PASS — nominal routed static timing analysis of the frozen Gen-1 implementation under the recorded
constraints and assumptions.** Owner decision, 2026-11-07, accepting the independent review's recommendation.

This is a qualification record for static timing analysis only. It adds no entry to
[`hardware_evidence.md`](hardware_evidence.md) and is not a board observation.

## Scope

| Item | Value |
|---|---|
| Design | golden Gen-1 routed checkpoint (sha256 `48e0e1613a76…`), the design the golden bitstream `442a229e…` was written from; cross-check: CPU-REPRO-1B checkpoint (`3497bbb3e4e9…`) |
| Constraints | frozen package [`cpu_board_3.xdc`](../hardware/boards/artix7/wukong_v3/cpu_v02/constraints/cpu_board_3.xdc) (`9449d1c7…`), the commands embedded in the checkpoint |
| Part / tool | `xc7a100tfgg676-1` (speed −1), Vivado 2026.1; report-only analysis of checkpoint copies, no implementation |
| Criteria | `spu_strategy/GEN1_TIMING_READINESS_2026-11-06.md` §6 (frozen before attempt 1; untracked) |

## Accepted results (attempt 2)

| Item | Result |
|---|---|
| Setup / hold | WNS +6.360 ns (Slow corner), WHS +0.060 ns (Fast corner); 0 of 20,176 endpoints failing |
| Recovery / removal / pulse width | +17.927 ns / +0.233 ns / WPWS +9.500 ns; 0 failing |
| Corners | multi-corner analysis, Slow and Fast both analysed; figures are worst of both (no per-corner tables) |
| Coverage | 20,176 endpoints = intra `cpu_clk` 20,160 + intra `sys_clk` 9 + `cpu_clk`→`sys_clk` 1 + `async_default` 6; check_timing 0 except the known `raw_rst_n` input-delay and `uart_tx` output-delay flags |
| Exceptions / CDC | no user timing exceptions; "All paths are Safely Timed" |
| Clock buffer | `cpu_clk_reg/Q` → one BUFG (`BUFGCTRL_X0Y0`) → 6,771 clock pins; exclusivity shown by NC3 |
| NC1 (sys_clk 8 ns) | WNS −17.640 ns, 2,630 failing; restored — detected as predicted |
| NC2 (+100 ps hold uncertainty) | WHS −0.040 ns, 9 failing; restored — detected as predicted |
| NC3 (`cpu_clk` stopped at the BUFG output) | 6,771 register pins with no clock and 20,166 `cpu_clk`-captured endpoints unconstrained; the `sys_clk` registers stayed clocked — detected as predicted |
| REPRO-1B | identical nominal results and reports apart from headers |

## Owner protocol decisions

1. **NC3 — accepted as a post-hoc methodological repair.** Attempt 1's NC3 used `delete_clocks`, which is not a Vivado
   command, so it never ran. Attempt 2 replaced it with `set_clock_sense -stop_propagation` and changed the NC3 acceptance
   condition accordingly, after attempt-1 results were known. This is a repaired test, not the unchanged frozen test. The
   accepted result shows loss of `cpu_clk` coverage while the `sys_clk` domain is preserved.
2. **Evidence integrity — accepted with limitation.** The local manifests, checkpoint hashes, detached-job records and raw
   reports are accepted as sufficient for internal qualification. The evidence was **not externally anchored** before
   execution: every hash and timestamp is self-written on the same machine, and the criteria file and all run evidence
   are outside Git. No independent timestamp attestation is claimed.

## Review chain

| Step | Outcome | Record |
|---|---|---|
| Attempt 1 (2026-11-06) | judge FAIL; disposition **UNKNOWN** (BUFG query and NC3 harness defects) | `build/gen1-sta-1/INTERPRETATION.md` |
| Read-only disposition review | TARGETED REPAIR REQUIRED | `build/gen1-sta-1/DISPOSITION_REVIEW.md` |
| Attempt 2 (repaired harness, one run) | judge PASS, 30/30 checks | `build/gen1-sta-1/attempt-02/` (`PRELAUNCH.txt`, `run-02/`, `MANIFEST.sha256`) |
| Implementing agent's acceptance review | ACCEPT PASS; **not independent** | `build/gen1-sta-1/attempt-02/ACCEPTANCE_REVIEW.md` |
| Independent review (separate reviewer agent, fresh context, **same model family**) | ACCEPT PASS, with eight disagreements with the previous review | `build/gen1-sta-1/attempt-02/INDEPENDENT_REVIEW.md` (+ `INDEPENDENT_REVIEW_provisional.txt`) |
| Owner decision (2026-11-07) | **PASS** for the stated scope | this note |

The attempt-1 UNKNOWN and all attempt-1 and attempt-2 evidence are kept unchanged as historical records. The `build/`
records are local and not in Git.

Reviewer disagreements recorded (from the independent review): the inherited judge checks pulse width only as WPWS ≥ 0
and its REPRO-1B check covers only four slack values (both closed by hand); NC3 is a post-hoc mechanism change rather than
simply "stricter"; BUFG exclusivity rests on NC3 rather than on the >6000 count; the timestamp sequence is corroborative,
not proof; the criteria file and run evidence are outside Git; and the branch moved (documentation commits only) after the run.

## Not established by this PASS

- Physical timing margin on the board: device grade marking, oscillator, rails and temperature are unverified.
- Asynchronous reset behaviour; I/O timing (`raw_rst_n` has no input delay and `uart_tx` no output delay).
- Behaviour beyond one checkpoint pair and one Vivado version; no voltage or frequency margin test.
- Margins are thin in places: hold +0.060 ns, removal +0.233 ns.
