# H0-RTL-1F-R3: restricted non-preemptive lifecycle

**EXPERIMENTAL PASS for the stated RTL simulation and closed-hierarchy
assumptions.** This is not production reset, physical timing or release
qualification. Baseline `e90bef1`; R1, R2 and earlier counterexamples remain
unchanged. The separately named R3 wrapper derives from R1 and retains its
single-clock, 14-word/six-slice profile and frozen arithmetic core.

The R1 implementation ignored a START while busy but could accept it later if
the signal stayed high through completion. R3 consumes each sampled assertion
once, reports a rejected START pulse if not admissible, and requires a sampled
low before another assertion. This is a local experimental interface choice;
it is not a UART/SPI protocol. Program writes remain directed to the inactive
bank. The existing bank scan checks the fixed instruction shape and CRC-32 of
the stored image; CRC-32 is not authentication or collision-resistant identity.

An accepted START reserves `owned`, clears prior result/completion, enters INIT
and holds core reset through two sampled rising edges before synchronous release.
If the clock stops in INIT, state and reset remain pending. Issue is possible
only in the owned ISSUE state after initialization, release and core boot.
Loads are rejected while owned. No internal preemption input exists; physical
reset invalidates owner, result and program validity. Completion requires the
14-instruction sequence to reach PC 14 with all six read slices present. The
wrapper returns to IDLE after this termination; it does not instantiate the
frozen frontend's separate HALT state.

## Retirement barrier and assumptions

In this configuration `surd_retire_valid` in the frozen core is driven by the
single enabled `spu13_surd_exec` instance (the disabled generate branch ties it
low); no alternate driver is connected to this wrapper's retirement input.
After a sampled reset, executor busy/retirement, arithmetic state/done,
normalizer state/done/start strobes, GCD and quotient busy/done/state are all
reset. With a shared reliable clock/reset, no force/alternate driver, and no
new accepted issue, the closed hierarchy's IDLE/start logic cannot generate a
retirement from the previous run. This source-supported invariant is described
in `research/h0_rtl_1f_r2/FINDINGS.md`; it is not derived from a quiet window.

The R2 `WAIT_RETIRE` fault-injection counterexample still applies: a forced or
otherwise unexpected untagged retirement there is indistinguishable from the
owned instruction's completion. The experiment relies on the closed-hierarchy
reset/ownership assumptions; it does not prove them in synthesized or
physical hardware or under injected event/clock/reset faults. `run_id` wraps
and resets to zero on physical reset; cross-reset identity and resynchronization
remain unspecified. `cpu_rst_n` here is a simulation expression, not a
reviewed physical generated-clock/reset-distribution circuit.

## Focused evidence

From the worktree root:

```bash
mkdir -p build/h0-rtl-1f-r3/<new-run>
iverilog -g2012 -s cpu_check -o build/h0-rtl-1f-r3/<new-run>/test.vvp -f research/h0_rtl_1f_r3/sources.f
vvp build/h0-rtl-1f-r3/<new-run>/test.vvp
vvp build/h0-rtl-1f-r3/<new-run>/test.vvp +stopped
vvp build/h0-rtl-1f-r3/<new-run>/test.vvp +collisions
vvp build/h0-rtl-1f-r3/<new-run>/test.vvp +stale_issue
vvp build/h0-rtl-1f-r3/<new-run>/test.vvp +before_accept
vvp build/h0-rtl-1f-r3/<new-run>/test.vvp +duplicate
vvp build/h0-rtl-1f-r3/<new-run>/test.vvp +held_start
python3 research/h0_rtl_1f_r3/controls.py --output build/h0-rtl-1f-r3/<new-controls>
```

`focused-02/` records seven zero-exit cases. The normal case checks bank-fed A
`(13,0,4,0,9,0)` and B `(7,0,4,0,4,0)`, a bad replacement preserving A,
reset during loading, multiplication and partial result, and injected stale
retirement in WAIT_BOOT. Separate cases cover stopped-clock initialization,
competing START/load and physical-reset/START/retirement collision, acceptance-
edge and preaccept retirement, duplicate retirement, and a held rejected
START. `controls-02/summary.txt` records designated detections for short reset,
premature issue, stale completion, and replay of a rejected START. The earlier
`focused-01/` and `controls-01/` predate the R3 START fix and are retained.

Source SHA-256:

```text
fb9b936b867cb5c2b22680e011fef7f800488a8a1a09eb4a591de4eabdceb13a  cpu_program_probe.v
78f2b434b2559f8071f6cacef1d7cfd315ed83b411301fa7aef3f930be41f55a  cpu_check.v
5d5d051286205896e34bfe5b27a128f9a89bb35c362bf93635e8406ad7b81c8e  sources.f
83beaa7951f5ae2f7abc89cb5aa3aa1b6e1f3d45a6163ee1ccf7bcbfdf0fdc81  controls.py
e211220cd99fd8849cc46ca4560cd8ed84c721f35c6a83de7e1b5e82b59e7c5f  ../h0_rtl_1f/program_banks_v2.v
```

No synthesis, hardware, full regression, frozen-source modification or commit
was performed. Independent review and any later reset/timing/CDC qualification
remain separate work.
