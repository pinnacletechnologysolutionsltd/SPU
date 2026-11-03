# H0-UART-1C experimental integration

Single-clock simulation candidate, not production RTL or hardware evidence.
`h0_uart_cpu_top` connects the corrected UART link to `h0_variable_top` using
`h0_uart_endpoint`. The underlying frozen core, bank and reset controller are
unchanged. No board pins, transport PHY, electrical assumptions, synthesis or
FPGA operations are included. CPU-domain RX synchronizes the asynchronous input.
The host must obey the 1B stop-and-wait and error-drain rules.

LOAD acknowledgement follows `bank_accept`; rejection follows `bank_reject`.
VALIDATE waits for final `promoted` or `bank_reject`. START success requires a
new owner and incremented run ID; STATUS returns flags and run ID; RESULT is
available only for the endpoint's latched accepted owner, matching controller
run ID, complete and all six valid slices. Reset clears the endpoint owner and
UART pending state. The 32-bit run ID wraps and resets; it is not a persistent
epoch or authentication. Reset, timeout or lost response can leave the host
uncertain of an already committed operation. There is no command cancellation,
transaction tag, concurrent-host arbitration or guaranteed response on reset.
The inherited untagged WAIT_RETIRE counterexample remains applicable.

`host_loader.py` uses pyserial only when run as a CLI. It submits 14 hex words,
computes the stored-image CRC over each word most-significant byte first,
transmits words least-significant byte first, validates, starts, polls status and
reads six little-endian slices. It checks that the observed run ID stays stable
across polling and result retrieval. An epoch collision after reset is not
excluded. The interface checksum is XOR and is not authentication or a
substitute for program CRC.

Reproduce from the worktree root:

```sh
bash research/h0_uart_1c/run.sh build/h0-uart-1c/<new-evidence-dir>
```

The serial simulation checks a malformed frame containing START, program A,
a refused competing LOAD during a forced testbench stall, invalid-CRC B
replacement preserving A, then valid program B. It asserts physical reset during a deliberately stalled owned run and an
incomplete UART frame, then checks invalidation and no replay. The independent
board oracle decodes the transmitted instruction words and checks all slices.
For the competing-request test, the bench deliberately forces ready and valid
low; this creates a controlled stall and is not evidence that the forced state
arises naturally. Edge tests and mutation controls cover an oversized endpoint
response when acceptance and completion coincide and line activity preventing
premature drain recovery. Host tests use a fake port, not a UART or board.

## H0-UART-1C-R1 endpoint refusal coverage

`refusals.v` incorporates the independent serial-path refusal audit. It checks
START without a valid image and before validation, validation without LOAD,
RESULT before completion, writes without LOAD, out-of-order/out-of-range
addresses, competing START/LOAD and STATUS while an owner is active, repeated
RESULT and freshness after a subsequent START. The busy-state cases deliberately
force ready and valid low; the forced stall is not a physical timing claim.
`endpoint_mutations.py` preserves the three previously detected endpoint
controls (premature validation acknowledgement, ignored bank rejection and
swapped status flags) and adds the four independently detected controls (false
START success, RESULT without completion, missing busy response and missing
address check). Each must fail at its named assertion, including a bounded
response timeout when rejection is ignored.

Six other mutations survived the independent audit and are not treated as
failures of this suite: removing the owned or incremented-ID term individually
from START acceptance (`start_skip_owned`, `start_skip_runid`); unconditional
bank acceptance in WAIT_ACK (`ack_without_bank`); skipping WAIT_EDGE on one
LOAD-begin branch (`no_wait_edge`); removing the RESULT owner guard
(`result_no_owner`); and retaining the endpoint owner-valid bit on reset
(`owner_not_reset`). Under the exercised closed controller lifecycle, paired
signals and reset/result guards may make these changes redundant or the
necessary differentiating state unreachable. Their survival is a bounded
observation, not a proof of equivalence or a claim that the guards are
unnecessary. The preserved independent audit logs provide the original data.
