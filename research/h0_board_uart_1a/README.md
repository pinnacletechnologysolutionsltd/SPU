# H0-BOARD-UART-1A preparation

Experimental preparation at `d9a25d2`; no Vivado synthesis, routing, bitstream
or physical FPGA work was performed. This shell instantiates the committed
H0-UART-1C experimental core and the accepted 1B adapter. It has no constant
program table and no LED or header assignments. It is not production RTL.

## V03 schematic and pins

Owner-supplied `QMTECH-XC7A100T_200T-Wukong-Board-V03-20240121.pdf`, SHA-256
`bec53e6201c5c47a7059ce5b5af86e0f3a48535ebdf5643af7583171f7331aee`,
shows the following. Sheet 2 shows the FPGA ball/net mapping and JTAG/config
circuits; sheet 6 shows the USB-UART circuitry; sheet 1 shows 3V3 bank supplies.
This identifies the schematic, not a measurement of the physical board.

| FPGA port | Ball | V03 schematic |
|---|---|---|
| `sys_clk` | M21 | Sheet 2: 50 MHz Y1 `SYS_CLK_M21`; bank 14 at 3V3. |
| `raw_rst_n` | H7 | Sheet 2: KEY0, SW2 to ground, R37 4.7 kΩ pull-up to 3V3; bank 35. |
| `uart_rx` | F3 | Sheet 6 U23 CH340N pin 6 TXD → `BANK35_F3`; FPGA input. |
| `uart_tx` | E3 | Sheet 6 U23 CH340N pin 7 RXD ← `BANK35_E3`; FPGA output. |

U23 is the onboard CH340N on mini-USB J4, with VCC connected to 3V3 on the
schematic. Both UART balls are bank 35, specified LVCMOS33. Sheet 2 connects
configuration flash and JTAG separately; the schematic shows no shared
programming/boot function on E3/F3, and U23 RTS has no shown connection. No
J11 signal is assigned: historically backfeed-exposed pins remain provisionally
excluded. Confirm device speed grade, board revision, wiring and external
power behavior before any separately authorized hardware use.

## Clock, reset, CDC and reports

The frozen supervisor divides 50 MHz by two. UART clocks from the resulting
nominal 25 MHz `cpu_clk`: 217 clocks/bit is about 115,207 baud (about +0.0064%
relative to 115,200). The H0 logic and UART use this single derived domain.
The asynchronous UART input crosses into two synchronized consumers: RX data
and drain-activity detection. The implementation script applies an exception
only from `uart_rx` to the two uniquely identified first-stage D pins after
synthesis; it leaves both synchronizer stages and reset paths timed. If those
pins are merged or renamed, the script fails closed for review. The UART TX
register drives idle high when its reset is asserted; physical power-up and
analog reset behavior are not established by RTL simulation.

The XDC defines the 20 ns primary clock. The script creates and checks the
40 ns generated clock after synthesis; synthesis itself does not see that
clock, so synthesis timing is not comparable with a fully constrained run.
Physical reset H7 and asynchronous UART RX have no fabricated external input
delays; the TX output has no external output delay. Review unconstrained paths,
CDC, clock interaction, setup, hold, recovery/removal, reset topology, DRC and
routing reports before drawing timing conclusions. The source-supported reset
barrier and untagged WAIT_RETIRE caveat remain conditional; a reset-topology
check alone cannot prove glitch-free operation or timing closure.

## Prepared implementation and audit procedure

`sources.f` and `SOURCES.sha256` bind the committed RTL, wrapper, includes,
XDC, scripts, tests and oracle. `implement.tcl` uses Vivado 2026.1, at most two
threads, xc7a100tfgg676-1, and generates synthesis, placement, routing and timing
reports without creating a bitstream. `inspect_synth.tcl` opens a checkpoint
read-only and records bank, fetch, held instruction and result fan-in roots.
It is a structural aid, not an automatic proof of byte-to-program functional
dependence; review missing/renamed cells and the sequential UART/adapter path.
The output marker records report generation, not successful timing closure.

A future owner-authorized run needs a frozen attempt budget and timeout, a new
job output directory and separate new implementation/monitor directories under
this worktree's `build/`. `run_monitored.sh` enforces a 5 GiB available-memory
preflight, records host memory/swap and pressure before, during and after, stops on
sustained severe memory pressure, and never retries;
it does not authorize a waiver. Invoke it through `tools/run_detached_job.sh`
with the frozen timeout, end the turn on LAUNCHED, and later inspect exactly one
terminal marker. That procedure is preparation, not permission to launch.

## Focused simulation

```sh
bash research/h0_board_uart_1a/run_focused.sh build/h0-board-uart-1a/<new-run>
```

The test compares each byte it drives to vectors generated with the committed
Python host `frame()` encoder, transmits through the serial pins, checks reply
framing/checksums and uses the independent oracle on both program results. It
exercises bad-version embedded START, competing LOAD and physical reset during
an incomplete frame and a deliberately stalled owned run, then checks UART idle
and post-reset STATUS. Forced ready/valid-low is a testbench stall, not a claim
that this state occurs in silicon. Baud is accelerated to 16 cycles/bit in this
functional test; the default 217-cycle hardware timing is not physically
qualified. Results do not establish post-synthesis reachability or routing.

For a future run only, after the owner freezes `<seconds>` and approves the
attempt budget, the command structure from this worktree is:

```sh
tools/run_detached_job.sh --output build/h0-board-uart-1a/<job-id> --timeout <seconds> --notify-desktop -- \
  research/h0_board_uart_1a/run_monitored.sh "$PWD" \
  "$PWD/build/h0-board-uart-1a/<implementation-id>" \
  "$PWD/build/h0-board-uart-1a/<monitor-id>"
```

All three IDs must be distinct and new. A post-synthesis inspection requires
its own authorized read-only Vivado invocation of `inspect_synth.tcl` with the
checkpoint and a new output directory; it must not be conflated with synthesis
or physical qualification.

## H0-BOARD-UART-1D implementation-flow gate

Before optimization and again before placement after optimization, the flow
requires 896 named data FFs in each program bank and 192 named result FFs. It
checks each result bit's structural fan-in through endpoint response storage,
adapter response storage, its UART shifter lane, and the TX output. Reports
list the expected and observed counts, matched names and per-bit paths. Fetch
and held-register counts are informational: fixed fields may be optimized.
These are conservative checks of the current register-mapped hierarchy, not
proof that a path is sensitizable. A different legal representation, merging
or renaming can cause HOLD. Missing exact names are reported along with broad
candidate names; if both absence and optimization/renaming are possible, the
report preserves that ambiguity rather than declaring data lost.

The RX pin uses the previously verified internal pull-up. The two HDL
synchronizer chains have identical asynchronous inputs and reset behavior, so
synthesis could merge them. Before applying an RX input exception, and again
after optimization, the flow checks the actual fanout, both first-to-second
stage connections, ASYNC_REG properties and cpu_clk assignment. If merged,
renamed or otherwise unverifiable, it holds without placement; it does not use
KEEP/DONT_TOUCH to prevent merging. The reset structure checks remain in all
four prior stages. These checks and the gate have been exercised only with Tcl
mocks, not against a Vivado-produced netlist for this board top.

`run_monitored.sh`, `run_focused.sh`, the mock test and the read-only synthesis
inspection restrict generated output directories to new children of the
worktree's `build/` area, with normalized paths. No waiver or launch is implied.
Focused gate reproduction:

```sh
tclsh research/h0_board_uart_1a/gate_mock_test.tcl build/h0-board-uart-1a/<new-mock-run>
```

`flow_structure_check.py` checks script ordering and report requests, with
negative controls for a missing post-optimization gate and premature placement.
It is a static check; the Vivado commands and actual synthesized cell paths have
not been exercised. The result observability gate also checks the intervening
UART shift-register chain, not just entry to the shifter.
