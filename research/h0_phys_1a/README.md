# H0-PHYS-1A isolated board-oriented candidate

**Status: implemented and simulation-tested; physical timing unqualified.**
Baseline `87833c7`. The source-only H0-PHYS-0 plan in the separate
`h0-phys-0-worktree` is the design input; frozen Gen-1 and production RTL are
not modified. No pin mapping, transport, synthesis or FPGA activity is included.

`h0_board_top` instantiates the unchanged `cpu_rst_1b_supervisor` to derive
`cpu_clk` and `base_rst_n`. Its completion inputs are tied low and its
completion output is unused. A derived R3 controller owns the H0 lifecycle;
`h0_reset_ctl` drives execution reset from a single register with asynchronous
assertion by `base_rst_n` and clocked release from the controller's registered
`exec_release`. START owns the run before INIT; INIT holds reset for two
sampled core-clock edges, and RELEASE waits for the reset register before
WAIT_BOOT and fetch. No core-clock progress means no initialization progress.
The derived bank uses `base_rst_n`, not the raw input pin, as its reset/write
gate. Internal execution reset does not reset the bank. Physical reset through
the frozen supervisor clears base-domain validity and ownership.

The separate `h0_demo_sequencer` is a temporary constant-table adapter: one
instance emits program A or B selected by the `DEMO_B` parameter, verifies the
bank and starts one run. It is not a UART, SPI or general host interface. The
board-level outputs expose the H0 controller's own completion and gate result
and result-valid to zero until complete and fault-free. No LED or J11 pins are
assigned. The temporary internal CPU test harness still inspects the controller
mask during execution; it is not the board publication interface.

## Focused verification

From the worktree root, with Icarus Verilog and Python 3:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 research/h0_phys_1a/run.py --output build/h0-phys-1a/<new-run>
```

`build/h0-phys-1a/focused-03/` contains source hashes, compilation and simulation
logs, the independent arithmetic oracle, five mutation controls and a PASS
marker. The seven R3 cases use a copied **and adapted** harness against
`h0_phys_cpu_controller` and the registered reset boundary: normal A/B,
stopped-clock initialization, collisions, acceptance-edge stale retirement,
preaccept retirement, duplicate retirement and a held rejected START. The
board-level test instantiates the frozen supervisor and two board tops; it runs
both adapters, asserts physical reset in all ten encoded controller states
(FAILED reached by injected retirement), verifies invalidation, forces a write
while base reset is active and checks actual bank contents/acknowledgement,
and confirms a partial result is not published after an injected fault.
Physical reset and clock edges are simulated with the testbench's phase choices;
this is not exhaustive analog reset coverage.

`board_oracle.py` independently decodes observed sequencer words and uses exact
rational polynomial arithmetic: A produces `(13,0,4,0,9,0)`, B produces
`(7,0,4,0,4,0)`. The four adapted R3 controls detect shortened reset sequencing,
early issue, stale completion and replay of rejected START. An additional
`release_early` mutant asserts execution release at START and is caught by the
reset-hold check. The original short-reset mutant alone shortens the new
three-observed-edge hold to two, so it is not by itself evidence of a violation
of the two-edge minimum. Earlier `focused-01/` and `focused-02/` are retained
development runs; `focused-03/` is the final tested version.

## Remaining boundaries

**H0-PHYS-1B demonstrator limitation:** the controller has a `start_rejected`
output, but `h0_board_top` leaves it unconnected and the temporary sequencer
does not observe it. The demonstrator therefore cannot report a rejected START;
do not infer that it was accepted from the sequencer moving to DONE. This is
unresolved demonstration behavior, not a defined host protocol.

The R2 `WAIT_RETIRE` injected-event counterexample remains: an unexpected
valid-looking untagged retirement there is indistinguishable from the owned
instruction. This candidate relies on the closed hierarchy and reset-flush
invariant; finite tests do not prove arbitrary event exclusion. Bank validation
uses CRC-32 for accidental corruption, not authentication or collision-resistant
identity. `run_id` wraps and restarts on physical reset; host resynchronization
is unspecified. R3 completes after PC 14 and six results rather than using the
frozen frontend's separate HALT state.

The execution-reset register is a source-level structural choice, not timing
closure. Fanout, asynchronous assertion/recovery/removal, generated clock,
reset distribution, placement and power-up behavior require later independent
analysis and separately authorized physical implementation. Input reset bounce,
actual device pins, timing and board behavior are unmeasured. No claim of
silicon verification is made.

## H0-PHYS-1B focused closure

`build/h0-phys-1b/focused-01/` contains a fresh run of all seven prior
controller cases, the board test, the independent oracle and existing five
mutation controls, plus two additions. `immediate_restart` starts the same
verified image on the earliest rising edge after the first completion, checks
that ownership changes while completion, all six valid bits and result data
are cleared, then checks all six results from the second run. The
`write_during_reset` mutant deliberately writes the selected staging bank in
the active reset branch. The board test detects it at `no write while base
reset`, confirming the check distinguishes an ineffective write gate; the
unmodified design accepts no write in the tested reset window. This is RTL
simulation, not proof of a physical reset edge's timing or recovery behavior.

Reproduce with a new output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 research/h0_phys_1a/run.py --output build/h0-phys-1b/<new-run>
```

### Audit follow-up: direct restart and write-gate coverage

`build/h0-phys-1b/coverage-04/` records the follow-up run. The immediate-restart
case counts rising edges at which `cpu_rst_n` is low before synchronous release
and requires at least three (the design requirement is at least two); a mutant
that shortens only the second run's reset
is detected at that assertion. The bank-specific test seeds a real storage
word, then forces `loading`, `count` and bank selection while base reset is
active, isolating reset priority even though those controls normally clear on
reset. A mutant that bypasses reset priority when a normal write is presented
is detected by the storage/acknowledgement assertion. The forced internal
state is a deliberate negative-control setup, not a claim it is reachable in
the unmodified design.

All eight controller cases, the board simulation, oracle and eight mutation
controls passed. `coverage-01/` is retained: the new mutant did hit the correct
assertion, but the runner initially failed to match its truncated display text.
`coverage-02/` corrected that test-reporting issue; `coverage-03/` added the
restart-only mutation and checked the two-edge minimum, and `coverage-04/`
strengthens the check to the observed three edges. No wrapper, bank or frozen arithmetic RTL changed in
this follow-up. The demonstrator's unconnected `start_rejected`, physical
timing limitations and R2 retirement caveat above remain unchanged.
