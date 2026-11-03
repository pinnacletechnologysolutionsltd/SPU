# H0-UART-1D integration record (experimental)

Imports the accepted H0-UART-1C-R1 experimental UART loading path at baseline
`87833c7`. **RTL simulation only**: not in `tools/release_tests.txt`, not in any
production or board source manifest, no pin assignment, synthesis, timing or
hardware evidence for the UART path. Nothing here is silicon-verified. Frozen
Gen-1 sources under `hardware/` are not modified
(`hardware/boards/artix7/wukong_v3/cpu_v02/PACKAGE_SHA256.txt`: 36/36 OK). The
14-word program format and the ISA are unchanged.

## Contents

| Path | Role |
|---|---|
| `research/h0_uart_1a/` | 8N1 RX/TX primitives, frame adapter, link, protocol v1 (`PROTOCOL_1B.md`), 1B focused tests and mutation controls. `README.md` there is the historical 1A note; `PROTOCOL_1B.md` is current. |
| `research/h0_uart_1c/` | H0 command endpoint, single-clock experimental top, `h0_variable_top` (H0-OPT copy), host loader, serial/refusal/edge benches, endpoint mutation controls. |
| `research/h0_phys_1a/` | Accepted H0-PHYS-1A/1B controller, two-bank storage, reset control, board oracle and their focused tests (dependencies of the 1C manifest). |
| `research/h0_uart_1d/evidence/` | Text-only log bundles (`SHA256SUMS`). |

Package files are byte-identical to the reviewed worktree copies. Manifests:
`research/h0_uart_1c/SOURCES.sha256` (44 entries, sha256 `ae9b3bc5…`),
`research/h0_uart_1a/SOURCES_1B.sha256` (11, `32123a6a…`),
`research/h0_uart_1a/SOURCES.sha256` (3, `e5d211e8…`); all verify.

## Reproduce

```bash
export PATH=$HOME/.local/opt/oss-cad-suite-20261027/bin:$PATH   # Icarus >= 12
sha256sum -c research/h0_uart_1c/SOURCES.sha256 research/h0_uart_1a/SOURCES_1B.sha256
bash research/h0_uart_1c/run.sh build/h0-uart/<new>/uart1c
bash research/h0_uart_1a/run_1b.sh build/h0-uart/<new>/uart1b
PYTHONDONTWRITEBYTECODE=1 python3 research/h0_phys_1a/run.py --output build/h0-uart/<new>/phys1a
```

## Focused regression (H0-UART-1D job-01)

Detached unit `spu-job-01-20261103T192406Z-486492`, COMPLETE, exit 0, 44 s;
logs in `evidence/h0_uart_1d_regression_2026-11-04.tar.gz`.

- Manifests 58/58 OK; frozen Gen-1 package 36/36 OK.
- 1C: serial A/B through the real core PASS; board oracle PASS for A
  (13,0,4,0,9,0) and B (7,0,4,0,4,0); refusal bench PASS (35 endpoint
  requests); edge bench PASS; host-loader tests 2/2 (fake port).
- Nine effective mutation controls in the 1C package, each failing at its named
  assertion: endpoint `start_always_ok`, `result_no_complete`, `result_no_busy`,
  `address_unchecked`, `validate_on_accept`, `reject_ignored`,
  `status_bits_swapped`; adapter `simultaneous_length`, `line_activity`.
- 1B: UART, adapter, link and embedded-frame benches PASS; 6/6 controls detected.
- PHYS-1A: 8 CPU cases, board, oracle and bank reset priority PASS; 8/8 controls.

## Surviving mutations (bounded, unproven observations)

Six endpoint mutations survived the independent audit: `start_skip_owned`,
`start_skip_runid`, `ack_without_bank`, `no_wait_edge`, `result_no_owner`,
`owner_not_reset`. Under the exercised closed controller lifecycle the guards
appear redundant or the differentiating state unreachable. This is an
observation from the exercised tests, not a proof of equivalence and not a
reason to remove the guards; it must be re-examined if the controller changes.
Original data: `build/h0-uart-1c-worktree/build/h0-uart-1c-claude-audit-01/`
inside `evidence/h0_uart_logs_2026-11-04.tar.gz`.

## Known limitations

- Frame integrity is an 8-bit XOR: it misses many multi-bit errors and is not
  authentication. Program identity uses CRC-32 (accidental errors only).
- A timeout, reset or lost response leaves the host uncertain whether the
  operation committed. There is no transaction tag, cancellation or guaranteed
  response on reset; the host must wait `FRAME_TIMEOUT` quiet after an error.
- `run_id` is 32-bit, wraps and resets on physical reset; it is not a persistent
  epoch, and a post-reset collision is not excluded.
- The untagged `WAIT_RETIRE` counterexample (`research/h0_rtl_1f/COUNTEREXAMPLE.md`)
  still applies.
- Busy-state tests force core `ready`/`valid` low; the stall is a testbench
  construct, not a timing claim. A stuck-low RX line holds the drain state.
- No physical qualification: no pins, electrical interface, baud tolerance,
  synthesis or timing for the UART path.

## Preserved related evidence (status unchanged)

- `evidence/h0_opt_evidence_2026-11-04.tar.gz`: H0-OPT-2 synthesis and H0-OPT-2B
  connectivity audit of `h0_variable_top` (Codex worktree logs, reports and
  scripts; checkpoints excluded). Synthesis-only; no implementation claim.
- `evidence/h0_phys_2_text_evidence_2026-11-04.tar.gz`: H0-PHYS-2 impl-01 job,
  reports, analysis and implementation package. Archived as a
  **program-A-specialized** physical implementation of the constant-table
  demonstrator: routed timing and reset-structure results are valid only for
  that netlist, not for the programmable CPU or this UART path. The full
  archive with checkpoints stays outside git at `build/h0-phys-2/archive-01/`
  (`h0_phys_2_impl01_evidence.tar.gz` sha256 `367fa394…`).
- `evidence/h0_uart_logs_2026-11-04.tar.gz`: 1B/1C/1C-R1 runs, jobs and
  independent audits (simulator images excluded).
