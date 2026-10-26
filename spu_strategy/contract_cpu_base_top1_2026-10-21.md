# Engineering Contract: CPU-BASE-TOP-1 — Base SPU CPU Wukong Artix-7 top (PREPARATION)

**Date:** 2026-10-21 (amendment A1 same day)
**Contract ID:** `contract_cpu_base_top1_2026-10-21.md`
**Status:** DRAFT, amendment A1 — D1–D5 ratified by John. Preparation only. Nothing here is implemented, simulated, synthesized, routed or run on a board. S1 implementation is HOLD.

**Roles:** Spec Author: Claude (this draft). Halt-and-Flag Implementer: unassigned. Integration Auditor: unassigned (independent of the implementer).
Every stage below needs its own GO from John. This document authorizes none of them, and the budgets in §8 allocate no execution time.

## 0. Amendment A1 — ratified decisions (2026-10-21)

| ID | Resolution | Where applied |
|---|---|---|
| D1 | Add only a minimal `ENABLE_REGEN` parameter pass-through to the existing workload top (default 1 preserved). The Base top explicitly instantiates `ENABLE_REGEN=0`. | §1, §3 |
| D2 | Proven 50 MHz input conditioning (2-FF synchronizer + 256 stable-high samples) **plus** a two-stage synchronized reset release in the derived 25 MHz domain. Proposed adaptation, not silicon-proven. | §5 |
| D3 | S3 placement: 1 attempt, 1,800 s. S4 routing: 1 attempt, 3,600 s. Combined ≤ 5,400 s, 8 GiB per process, no retries, separate GO each. A timeout is a terminal result, not evidence the design cannot fit. | §8 |
| D4 | OpenXC7 first for implementation feasibility. Vivado on Ubuntu is the preferred independent timing-qualified flow, subject to readiness. No install, licensing, import or Vivado run is authorized. | §6, §8 |
| D5 | The constrained port stays `uart_tx`; documented as `checksum_parity_out` (checksum parity), never UART serial data. | §4, §6 |
Also ratified: the Base physical bring-up is gated behind defensible timing qualification (§8: S7 requires S6). A positive-control board experiment stays a diagnostic prerequisite and is not Base qualification.

## 1. Objective and scope

Define the smallest useful Wukong XC7A100T-FGG676-1 evaluation top for the **Base SPU CPU** (`ENABLE_REGEN=0`), keeping the qualified
CPU behaviour and the existing synthetic workload, with bounded stages and independent gates. Frozen: 50 MHz board input with a derived
25 MHz CPU clock; keep the synthetic checksum workload for first bring-up (no new UART, SPI, host-command or instruction-loading protocol);
OpenXC7 for initial feasibility, Vivado (separately reviewed) for timing qualification.

**Files this contract would later create/modify (all out of scope now):**
- NEW `hardware/boards/artix7/spu_a7_surd_cpu_base_top.v` (clock/reset wrapper) and `spu_a7_surd_cpu_base.xdc` (proposed text in §6).
- MODIFY (D1) `hardware/boards/artix7/spu_a7_surd_cpu_bench_top.v`, minimal: `parameter ENABLE_REGEN=1` added to the parameter list and
  `.ENABLE_REGEN(ENABLE_REGEN)` added to the `spu13_core` instantiation. Nothing else. Pre-image hash `aeeae0f81c57050a…` must be recorded before editing,
  and any unrelated working-tree changes preserved. This file is also used by the Full-CPU flow (`tools/build_surd_cpu_a7.sh`), so default behaviour must not change.
- NEW Base synthesis script (copy of the C1/C4 flow without the REGEN-only lines, see §8). `build_a7.sh` and `board_build_manifest.json` untouched until a stage gate says otherwise.

## 2. Frozen starting point (identities, verified 2026-10-21)

| Item | Identity |
|---|---|
| Repo HEAD | `963a685004b9` (worktree has extensive uncommitted work; identities below are of the working-tree files) |
| `hardware/rtl/core/spu13/spu13_core.v` (carries `ENABLE_REGEN`, default 1) | `a6bd0fc2442a13d2c8b6c95a9c129d64bee2631bf7251708074f2e6df0df7199` |
| `hardware/rtl` tree hash (path+content, sorted) | `303a8a89062473ae…` (`build/cpu_test_gate_1b/identities.json`) |
| `software/spu_vm.py` (profile `"base"`) / `run_all_tests.py` | `5fda0badfb7c633a…` / `f047ef94561626009f89…` |
| Existing workload top `spu_a7_surd_cpu_bench_top.v` (unmodified) | `aeeae0f81c57050a…` |
| Existing bench XDC `spu_a7_surd_cpu_bench.xdc` | `690f7fea7006f6d5…` |
| Clock/reset precedent `spu_a7_tensegrity_link_top.v` / `.xdc` | `d74f5c4e9a5cc5cb…` / `9c97679cf46c4f9d…` |
| UART pin precedent `spu_a7_uart_loopback.xdc` | `1074b08e2e204e8d…` |
| Base synthesis estimate (C4 run_02, Yosys 0.63+87, `-chparam ENABLE_REGEN 0`) | `build/cpu_syn_c4_01/run_02/cpu_1.json` sha `31e1ab9c25f06656…` |

**Source set (19 `.v`, as in the C1/C4 flow):** `spu_hamming_72_64`, `spu_quadray_regfile`, `spu_quadray_regfile_ecc`, `fpga_chain`, `spu13_core`,
`spu13_regen`, `spu13_surd_arith`, `spu13_surd_bank`, `spu13_surd_exec`, `spu13_surd_load`, `rational_surd5_scale_manager`, `surd_binary_gcd3`,
`surd_cpu_products`, `surd_exact_quotient`, `surd_normalize_unit`, `spu_annealer`, `spu_i2s_out`, `spu_ve_qr_init`, plus the top. With
`ENABLE_REGEN=0`, `spu13_regen` and `fpga_chain` remain *listed* but are not instantiated (the C4 netlist contains neither). The final source set will add the new
wrapper (and the modified bench top). Include directories: `hardware/rtl/arch` and `hardware/rtl/core/spu13`.

**Separate synthesis estimates (never combined, never differenced into a REGEN-only claim):**
Base 21,603 LUT / 12,854 FF / 80 DSP / 45,168 cells (C4); Full 78,025 LUT / 13,523 FF / 210 DSP / 121,822 cells (C1/C3). The two runs
differ by more than REGEN (module `fpga_chain` pruned, one unchanged module mapped 57 LUT lower, bench-top parameter plumbing). Estimates only.
Regression reference (CPU-TEST-GATE-1B, measured): Full 254/254 PASS, Base 249/249 PASS.

## 3. Base profile semantics and controls

- Hardware: core instantiated with `.ENABLE_REGEN(0)`, `.ENABLE_SURD_CPU(1)` (other parameters as in the existing bench top). REGEN (0x09) completes immediately,
  writes no QR state, and latches a sticky REGEN_PREC fault (`regen_debug_status[9]`). No chain mirror, no Stage B. QLDI/QSUB/ROTC commits match the full profile (5-commit trace).
- Software contract: VM `SPUCore(profile="base")`, manifest via `capability_manifest("base")`.
- **Explicit profile in the board source (D1):** the new top instantiates the workload as
  `spu_a7_surd_cpu_bench_top #(.ENABLE_SURD_CPU(1), .ENABLE_REGEN(0)) u_workload (.sys_clk(cpu_clk), .rst_n(cpu_rst_n), .uart_tx(checksum_parity_out));`
  so the profile is visible in the file that defines the image, not only in a `-chparam` or default. `ENABLE_REGEN` must not default to 0 anywhere.
- Do not advertise chain, REGEN or Stage B capability for this image. Existing silicon evidence belongs to full-profile builds and does not transfer.
- Open item: the bench top passes `DEVICE("SIM")` to the core. It synthesized with inferred DSPs in C1/C4, but a hardware image labelled "SIM" must be explicitly checked in S1/S2
  for any simulation-only primitive selection (record the result; do not change it without a decision).

## 4. Workload and observable result (what actually exists) — D5

`spu_a7_surd_cpu_bench_top` drives the core with a 27-step deterministic Surd instruction sequence (LFSR seed
`64'h13579bdf2468ace1`, ops 0x70–0x77, 0x1D, 0x1B), folds `s_data`/`s_status`/QR commit words into a 32-bit rotating `checksum`, and drives
`uart_tx = ^checksum`.

**Naming (D5):** the externally constrained port stays `uart_tx` (pin E3 continuity). In the wrapper, in documentation and in test evidence the signal is called
`checksum_parity_out` — the **parity bit of the checksum, not UART serial data**. No UART framing, baud rate or terminal readability may be claimed.

**Observation:** a logic analyzer on E3 compared with a simulated golden transition trace (aligned to the `cpu_rst_n` release, see §5). A stalled CPU, a held reset,
a dead clock and an open pin all produce a constant pin, so (mandatory, from the standing bench rules):
- a **positive-control image** with the same clock/reset/divider/BUFG scaffolding **including the local release synchronizer** and a known toggle on E3 is observed *before* any silence is interpreted;
- a **reset-held negative control** (pin constant) is recorded;
- results are rates over N≥10 bounded observations per condition, not single captures. The available analyzer has no working continuous mode (multi-shot only);
- the negative control must also be shown to accept the known-good case (a control that fires on the correct input is vacuous);
- the golden trace comes from RTL simulation of the finished top (S1): a regression oracle for the RTL, not an independent mathematical oracle.

## 5. Clock and reset topology (specification) — D2

```
M21 sys_clk (50 MHz) -> IBUF -> BUFG#1 (inserted by the tool at the port; do not instantiate)
 50 MHz domain contains ONLY: 2-FF input synchronizer, 8-bit stable-high counter, 1 divider flop
 divider flop (toggles every 50 MHz clock, held 0 while !rst_n_int) -> BUFG#2 (explicit, `ifdef SYNTHESIS`) -> cpu_clk (25 MHz)
 cpu_clk domain: 2-FF release synchronizer (NEW), spu13_core (ENABLE_REGEN=0), workload, checksum, checksum_parity_out
```
Specification (behavioural intent, not final RTL):
```
// 50 MHz (proven, tensegrity link top)
rst_sync <= {rst_sync[0], rst_n};            // INIT 2'b00
if (!rst_sync[1]) rst_count <= 0; else if (!rst_n_int) rst_count <= rst_count + 1;   // INIT 0
rst_n_int = (rst_count == 8'hFF);
div <= rst_n_int ? ~div : 1'b0;              // INIT 0;  -> BUFG#2 -> cpu_clk
// 25 MHz (NEW, unproven): asynchronous assert, synchronous release
always @(posedge cpu_clk or negedge rst_n_int)
  if (!rst_n_int) cpu_rst_sync <= 2'b00; else cpu_rst_sync <= {cpu_rst_sync[0], 1'b1};
assign cpu_rst_n = cpu_rst_sync[1];
```
- **BUFG rule:** BUFG#2's input is a fabric flop output, never another BUFG output. Exactly two BUFGs (verify in the netlist). The old outage
  (`docs/hardware_evidence.md`, lines ~2895–2952) was a BUFG fed from the port's BUFG, emitted as an undriven clock with no warning.
- **The raw `rst_n` pad must not reach any core reset or any flop in the cpu_clk domain.** The only sink of the pad is `rst_sync[0]`. `rst_n` carries `PULLUP` (H7 has no external pull).
- **Why the local release synchronizer is required, not just prudent:** while `rst_n_int` is low the divider holds `cpu_clk` low (stopped). The workload top resets its
  registers *synchronously* (`if(!rst_n)` on the clock), and a stopped clock gives them no edge. After a mid-run reset those registers would keep stale values. With the local
  synchronizer, `cpu_rst_n` stays low for the first two `cpu_clk` rising edges after `rst_n_int` rises, so the synchronous resets execute twice. This must be verified in S1 (restart-from-step-0 test) and is the main
  difference from the proven tensegrity top, whose sinks use asynchronous resets.
- **Ordering, nominal timing (hand analysis; OpenXC7 does not time it, Yosys/iverilog do not model BUFG delay):**
  - Assert: pad low → `rst_sync[1]` low within 2 sampled 50 MHz edges → `rst_count` cleared on the next edge → `rst_n_int` low → `cpu_rst_sync` and the core reset asynchronously. The divider is forced to 0 at the next 50 MHz edge; `cpu_clk` may therefore finish one normal high phase (≥ 20 ns) and then stop low. No runt clock pulse is possible because `div` only changes on 50 MHz edges.
  - Release: after the pad's last low sample, 2 + 256 sampled edges (≈ 5.16 µs) until `rst_n_int` rises; `div` starts toggling on the next 50 MHz edge; `cpu_rst_n` rises after the second `cpu_clk` rising edge (≈ 60–80 ns later); the first edge on which the workload runs un-reset is the third.
  - Short pulses: a low pulse spanning fewer than two 50 MHz sample edges is not guaranteed to be seen (no claim below ≈ 40 ns); a longer pulse clears the counter; a pulse during the 256-sample window restarts the window.
- **Hazard to analyse (not fix) in S1:** `rst_n_int` is a combinational 8-bit decode that also drives an asynchronous clear. A transient `FF` pattern is possible only at the `0x7F→0x80` carry boundary. A runt high on `rst_n_int` while the clock is stopped cannot release `cpu_rst_sync` (it needs clock edges), so the new path tolerates it; record the argument. The same decode already exists in the proven top; registering it would be a deviation needing its own evidence.
- The existing bench XDC comment ("No divider or generated clock … externally supplied 25 MHz") describes the old bench and must NOT be copied. The workload's `tick`, `rng` and step counters live in the cpu_clk domain, so no external 25 MHz source exists or is needed.

**S1 simulation requirements (focused, deterministic):**
1. Release-phase sweep: pad `rst_n` released at ≥ 8 different phase offsets relative to the 50 MHz edge (e.g. 0, 3, 6, 9, 12, 15, 18, 19.5 ns); `cpu_rst_n` must change only on `cpu_clk` rising edges and ≥ 2 rising edges must occur with `cpu_rst_n` low after `rst_n_int` rises.
2. No runt clock: every `cpu_clk` high and low phase ≥ 20 ns, across assertion at all phases.
3. Pulse widths {1, 2, 3, 10, 300} 50 MHz cycles, one starting inside the 256-sample window, one mid-run: the mid-run case must restart the workload from step 0 and reproduce the golden `checksum_parity_out` trace.
4. Golden trace defined relative to the `cpu_rst_n` rise; identical across all release phases and across a mid-run restart; generated twice identically.
5. Structural check: the pad net's only fanout is `rst_sync[0]`; no pad-derived net reaches the core or the cpu_clk domain.
6. Mutations that must be caught (and the unmutated design must pass the same checks): remove the local synchronizer; wire the pad raw into the core reset; let the divider run during reset; shorten the stable-high count; drive BUFG#2 from BUFG#1.
7. Limit stated in the result: simulation uses a zero-delay BUFG model, so BUFG insertion delay, skew and metastability are not exercised.

## 6. Constraints (proposal text; not written to the tree) — D4, D5

Provenance: M21/`sys_clk` and `create_clock -period 20.000`, and H7/`rst_n` + `PULLUP`, are line-for-line the silicon-proven
`spu_a7_tensegrity_link.xdc`. E3 is from `spu_a7_uart_loopback.xdc` and `spu_a7_100t.xdc` (E3 telemetry captured on silicon,
`docs/hardware_evidence.md` near line 1683). The existing bench XDC says M21's frequency "is not established by this build constraint";
the 20 ns value rests on other builds' evidence and is re-checked on the board in the positive-control stage.

```tcl
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]          ;# 50 MHz board oscillator (primary)
# Derived 40 ns CPU clock — Vivado only (nextpnr-xilinx 0.8.2 takes one global --freq and ignores XDC timing).
# Attach the generated clock to the divider register's Q pin so it propagates through BUFG#2; exact pin name is
# UNVERIFIED until the netlist exists (S6 reviews it):
# create_generated_clock -name cpu_clk -source [get_ports sys_clk] -divide_by 2 [get_pins <divider_reg>/Q]
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]
set_property PACKAGE_PIN E3 [get_ports uart_tx]                       ;# carries checksum_parity_out, NOT UART data
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]
```
Unsupported/unknown, to be recorded in every result: (1) generated-clock and cross-domain constraints are ignored by OpenXC7; `A7_FREQ=25` is a global figure applied to the divided clock and the 50 MHz domain's small logic is effectively untimed; (2) no I/O delay constraints; (3) nextpnr's Fmax is an estimate and not a timing-closure claim (use the last "Max frequency" line only); (4) no CDC analysis; (5) async recovery/removal on `cpu_rst_sync` (launched from the 50 MHz domain) is untimed by OpenXC7 and must be reviewed in Vivado.

**Timing-flow position (D4):** OpenXC7 results are implementation-feasibility evidence only. Vivado cannot inherit them. If chosen, S6 must independently qualify *its own* implemented candidate (source set, constraints, device, clock definitions, and the paths in §8 S6) and produce its own bitstream.

## 7. Evidence claims (kept separate; none established yet)

| Evidence claim | Status |
|---|---|
| Structural validation | NOT RUN (no top exists) |
| Functional simulation of the Base top | NOT RUN; core-level Base regression 249/249 PASS exists |
| Synthesis | Estimate only, 21,603 LUT, bench-top variant in a build directory, not this top |
| Place-and-route | NOT RUN. Full CPU OpenXC7 route did not complete in prior bounded attempts; Base routing is unknown |
| Interface validation: clock, pins, 50 MHz reset conditioning | Evidence from other builds (M21/H7/E3, tensegrity reset+divider), not this image |
| Interface validation: 25 MHz local release synchronizer | **No evidence anywhere; new in A1** |
| Independent timing qualification | NOT RUN; Vivado not installed |
| Silicon observation | NOT RUN for Base |

## 8. Stages and independent acceptance gates (each needs a separate GO; a failed gate stops the sequence)

| Stage | Work | Budget (D3; allocates nothing now) | Independent gate |
|---|---|---|---|
| S1 RTL + sim | Create the top, XDC file, D1 parameter pass-through. Compile; run the §5 simulations; produce golden trace. Re-run the 16-TB core matrix and `SPU_PROFILE=full/base` regression | host-only, ≤ 1,200 s | Full stays 254/254, Base stays 249/249 (plus the new top TB); existing TB logs identical for the default profile; §5 checks 1–7 pass with mutations caught; parameter diff is exactly the two D1 lines |
| S2 Synthesis | Base flow = C1 flow minus the REGEN-only `select/chtype` lines, plus `select -assert-none spu13_regen`; `-chparam ENABLE_REGEN 0` | 1 attempt, 600 s, 8 GiB, 4 threads | `spu13_regen`/`fpga_chain` absent; exactly 2 BUFG, none fed by a BUFG; pad net fans out only to the synchronizer; LUT/DSP reported against 21,603/80 as a *comparison*, not a target; DSP ≤ 240 |
| S3 Placement | OpenXC7 place only (`--freq 25`, heap placer), detached runner | **1 attempt, 1,800 s**, 8 GiB, no retries | placement integrity audit PASS; no ignored legalization warnings. A TIMEOUT is a terminal result, not a verdict on fit |
| S4 Routing + FASM | OpenXC7 route, FASM, bitstream | **1 attempt, 3,600 s**, 8 GiB, no retries; **S3+S4 ≤ 5,400 s combined** | complete route; independent route audit; bitstream hash recorded; **no timing claim**. Budget exhaustion is a valid terminal result |
| S5 Positive control (diagnostic) | Blinky with identical clock/reset/divider/BUFG scaffolding **including the local release synchronizer** on E3; reset-held negative control that also accepts the good case | board op, separate GO | toggle at the expected rate in N≥10 bounded observations; confirms M21 = 50 MHz. **Diagnostic only — not Base CPU qualification** |
| S6 Independent timing qualification | Vivado on Ubuntu (preferred), separately reviewed and authorized. Prerequisites: installed/licensed tool and exact version recorded; XC7A100T-FGG676-1 supported (verify against the vendor device table); a *Base-specific* frozen source package (the existing C1 package is the **Full** CPU, core hash `2f860c31…`, not `a6bd0fc2…`); XDC with `create_generated_clock`; source/constraint correspondence to S1/S2 | separate review | Vivado's own implementation of the candidate: timing met for the 20 ns primary and 40 ns derived clock; recovery/removal and clock-interaction reports reviewed; DRC clean (incl. no BUFG→BUFG); the qualified bitstream is the Base bring-up artifact. Only then may a 25 MHz claim be made, scoped to that candidate |
| S7 Base CPU bring-up | Load the **S6-qualified** image; multi-shot capture of E3 vs golden trace; reset-held negative control | board op, separate GO; **requires S6 PASS** | rate over N≥10 bounded runs, reproduced after a power cycle; recorded in `docs/hardware_evidence.md` before any "silicon-verified" wording |

An OpenXC7-built Base image loaded on a board before S6 would be a separate, explicitly diagnostic experiment needing its own GO and labelled "no timing qualification"; it is not S7.

**Stop conditions:** a failed gate, a netlist containing REGEN logic, a BUFG→BUFG connection, any raw-pad reset path, an unexplained zero/constant output
without a positive control, or exceeding a frozen budget. No retries, extensions or substitute methods without renewed authorization.

## 9. Remaining contradictions and open items (identified during amendment A1)

1. **Which bitstream is the Base bring-up artifact?** With S7 gated behind S6, the artifact is the *Vivado* candidate; the OpenXC7 S3–S4 output is feasibility evidence and does not transfer. If Vivado is unavailable, there is no timing-qualified Base image and S7 stays HOLD. **Needs John's confirmation (D6).**
2. **Vivado readiness is unmet today.** `vivado` is not on PATH; `docs/VIVADO_ENVIRONMENT_READINESS_2026-10-19.md` (untracked) records that Ubuntu installation and licensing are pending by owner decision. The existing Vivado reference tranche pins the **Full** CPU (C1 core `2f860c31…`) and cannot be reused as the Base candidate.
3. **D2 supersedes the earlier "exact proven pattern" recommendation.** The 50 MHz conditioning is proven; the 25 MHz local release synchronizer is not. The positive-control image (S5) must contain it or it will not test it. A latent issue it fixes: the workload's synchronous resets need clock edges during reset (see §5).
4. **D3 placement ceiling is tight against the only placement-time evidence.** An earlier, different-architecture saved-placement run (52,090 cells) took 1,724 s (`openxc7_route_fasm_preparation_20261017/REVIEW.md`), about 4% under the 1,800 s ceiling; Base is 45,168 cells. A timeout is plausible and is, by D3, a terminal result and not a fit verdict. The 3,600 s routing ceiling is half the 7,200 s that earlier CPU routing attempts exhausted.
5. **`DEVICE("SIM")`** in the bench top's core instantiation (see §3) needs an explicit hardware-image review.
6. **Combinational `rst_n_int` decode** also drives the new asynchronous clear (analysis item, §5).
7. **The golden trace is an RTL-regression oracle**, produced by the same RTL it checks; it detects regressions and reset-ordering faults, not arithmetic errors.
8. **Shared-file edit:** D1 touches a file used by the Full-CPU flow; default behaviour must be proven unchanged in S1 (lexical diff limited to two lines; Full-profile regression unchanged).
9. **Budget scope:** D3's 5,400 s covers S3+S4 only; S1, S2, S5, S6 and S7 are budgeted separately when authorized.

## 10. Preservation

Full CPU default (`ENABLE_REGEN=1`) unchanged; existing full-profile builds and board manifests untouched; CPU-PROFILE-2R, CPU-TEST-GATE-1A/1B, DOC audit and C1–C4 synthesis evidence unchanged;
historical 238/243/247 totals unchanged; no governance file edits. Any later stage that modifies a shared file must first record its pre-image hash. The 254/249 regression reference
and the separate 21,603-LUT (Base) / 78,025-LUT (Full) synthesis estimates stay labelled as such.

## 11. Verification commands (for later stages; none run now)

```bash
SPU_PROFILE=full python3 run_all_tests.py     # expect 254 pass / 0 fail (+ new top TB)
SPU_PROFILE=base python3 run_all_tests.py     # expect 249 pass / 0 fail (+ new top TB)
bash tools/verify_repo.sh
tools/run_detached_job.sh --output build/<unique> --timeout <frozen> -- <exact command>   # anything over 60 s
```
