# H0-RTL-2 integration record (experimental)

Imported from isolated worktrees at baseline `e90bef1`. **Experimental RTL
simulation only**: not in `tools/release_tests.txt`, not in any production or
board source manifest, no synthesis, timing or hardware evidence. Terra's final R3
source review and the independent arithmetic oracle (H0-ORACLE-1) returned PASS.
`REVIEW_SHA256.txt` still verifies unchanged (`sha256sum -c`). Frozen Gen-1 CPU
and arithmetic sources under `hardware/` are not modified.

## Reproduce

```bash
python3 research/h0_rtl_1f_r3/run_focused.py --output build/h0-rtl-2/<new-run>
python3 -I research/h0_rtl_1f_r3/independent_oracle.py
```

The runner compiles `sources.f`, runs the seven focused cases, the four negative
controls and the oracle, and prints `H0_RTL_1F_R3_FOCUSED PASS` only if all pass.

## Archived evidence

`evidence/h0_rtl_logs_2026-11-02.tar.gz` (SHA-256 in `evidence/SHA256SUMS`) holds
the text logs and summaries of the earlier runs, relative to the original
`build/` tree: `h0-rtl-1`, `h0-rtl-1e`, `h0-rtl-1f-r1`, `h0-rtl-1f-r2`,
`h0-rtl-1f-r3` (focused-01/02 and controls-01/02 plus the two independent
verification runs) and `h0-oracle-1`. It excludes simulator images, waveforms and
source copies. The `build/...` paths quoted in `RESULTS.md`, `FINDINGS.md`,
`REVIEW_NOTE.md`, `EXPERIMENT.md` and `STATUS.md` are original run locations; they
are retained verbatim as reviewed and resolve to directories inside this archive.
The R1/R2 counterexample (`../h0_rtl_1f/COUNTEREXAMPLE.md`) and its reproduction
material are preserved unmodified.

## Limitations

- Single `cpu_clk` domain; `cpu_rst_n` is a simulation expression, not a reviewed
  reset/clock distribution or CDC design.
- `WAIT_RETIRE` untagged-retirement counterexample still applies; exclusion of a
  stale retirement rests on the closed-hierarchy reset invariant, not a tag.
- Program integrity is CRC-32 (accidental errors only, not authentication).
- `run_id` wraps and resets on physical reset; cross-reset identity unspecified.
- Wrapper terminates at PC 14 and does not use the frozen frontend's HALT state.
- No UART/SPI transport; no synthesis, timing or board evidence. Not a
  hardware-evidence entry; nothing here is silicon-verified.
- H0-SW-2 (`software/spu_host/h0_program.py`) is a software simulation, not an
  RTL comparison; see `docs/H0_SW_2_PROGRAM_INTERFACE.md`.
