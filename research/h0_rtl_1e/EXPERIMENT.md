# H0-RTL-1E: controlled-reset frozen-core experiment

**EXPERIMENTAL PASS for the named simulation cases only.** This does not
qualify reset, a frontend, a program loader or an FPGA image. Baseline
`e90bef1`; frozen core and production RTL are unchanged.

`reset_core_probe.v` is a separately named simulation wrapper using the same
core parameters and ties as the frozen CPU integration. It drives the actual
frozen `spu13_core.rst_n`, holds reset for two sampled rising edges, releases it
on a clock edge and blocks new commands during initialization. It clears its
own pending command, accumulated six-slice result and completion. It then
waits for boot, not-busy and no-retire observations. The testbench drives
instruction words directly; this is **not** the frozen frontend, a writable
frontend, or an interface ready for use. The 14-retirement completion is a
test probe, not a verified frontend HALT. The adjacent H0-RTL-1 two-bank
experiment is instantiated independently: one validated active program is
retained across internal initialization, but it does not feed this wrapper's
instructions. No transport is present.

The explicit simulation source filelist is `sources.f`; it names the imported
frozen core, shared arithmetic, normalizer, GCD, quotient and other elaboration
sources. The exact hashes of the list and source files are captured in the run
directory. From the worktree root, with Python 3 and Icarus Verilog:

```bash
python3 research/h0_rtl_1e/run.py --output build/h0-rtl-1e/<new-run>
```

## Evidence summary

`build/h0-rtl-1e/sim-03/normal.log` is the waveform-equivalent event summary;
no waveform file was generated. In the simulator's displayed ps timestamps:

* At 556000, initialize during a live GCD after entering normalization.
* At 1516000, initialize during a live quotient operation; both subunit and
  executor busy were observed clear after initialization.
* At 1930000, initialize during a fast-path multiply.
* At 2306000, a subsequent 14-instruction sequence produced slices
  `(13,0,4,0,9,0)`; after another initialization, at 2676000, a second
  sequence produced `(7,0,4,0,4,0)`. These correspond respectively to
  `(1+2√3)²/9` and `(2+√3)²/4` using independent integer identities.

The test checks bank validity across internal initialization, reset-edge
coverage, cleared result validity/completion, busy and retirement clearing,
and a 20-cycle post-reset no-retirement observation. `sim-03/summary.txt`
also records two separately compiled mutants detected at their designated
assertions: insufficient sampled reset and failure to clear stale completion.
Compilation failure, timeout or a different assertion is not counted as
detection. Earlier `sim-01` and `sim-02` preserve intermediate test versions.

The 20-cycle observation is **not** a proof that no stale retirement can
occur at a later time, for a different operand, at another arithmetic phase,
or in another core configuration. Retirement is untagged. The wrapper's
reset expression and request interface are simulation constructs, not a
reviewed generated-clock, reset-CDC, ownership or physical reset design.
Boot/idle observations are not a proof that all hidden state is quiescent.
No full-bank integrity, validation/promotion integration, command arbitration,
run identity, UART/SPI, stopped-clock coverage or FPGA timing is established.
No core alteration was required for these bounded cases; broader coverage and
independent review are still required before H0-RTL-1 integration.
