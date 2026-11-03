# H0-UART-1A — incomplete experimental work

Status: REVISE. Only the separate clocked 8N1 RX and TX primitives and a small
simulation exist. There is no frame parser, command controller, host loader,
H0 connection, versioned frame format or operation acknowledgement. Do not use
these primitives as a complete loading interface or claim two-program coverage.

`h0_uart_rx` has a two-flop input synchronizer, samples at the middle of a
start bit, samples eight LSB-first data bits and reports a stop-bit framing
error. `h0_uart_tx` accepts one byte when idle. Both use the supplied clock;
`CLKS_PER_BIT` is a parameter and must be at least 4. The default 217 corresponds
to approximately 115,207 baud for a nominal 25 MHz clock. Actual oscillator
frequency, asynchronous sampling tolerance and electrical interface have not
been qualified. A UART reset clears partial receiver state. No timeout or frame
recovery is yet implemented.

The isolated worktree is based on `87833c7`. The copied H0-PHYS-1B controller
is reference material only. No physical pins or host connection are specified.
The test is limited to one received byte, one bad stop bit and a single TX/RX
loopback byte; it is not an exhaustive UART or reset test.

```sh
iverilog -g2012 -s uart_check -o /tmp/h0-uart-1a.vvp research/h0_uart_1a/uart_rx.v research/h0_uart_1a/uart_tx.v research/h0_uart_1a/uart_check.v
vvp /tmp/h0-uart-1a.vvp
```
