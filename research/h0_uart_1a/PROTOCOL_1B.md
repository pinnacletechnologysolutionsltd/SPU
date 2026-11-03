# H0-UART-1B experimental protocol, version 1

Scope: simulated framing and a mocked endpoint, not an H0 controller connection
or evidence of program-memory commitment. No pins or physical interface are
specified. The 8N1 link runs on the supplied H0 clock. The UART and adapter
remain separate from the transport-independent command endpoint.

A request is `A5 01 command length payload checksum`. The checksum is the
8-bit XOR of every preceding byte of the frame, including A5. It detects a
single-bit error but does not detect every multi-bit error; it is not the
stored-program CRC-32 or an authentication mechanism. Length is 0–9 bytes.
A response is `A5 01 (command | 80) status length payload checksum`, with the
same XOR rule and response payload up to 24 bytes. Multibyte values are
little-endian. A parser error before the command byte uses response command 80.

| Request | ID | Length | Endpoint contract |
|---|---:|---:|---|
| LOAD begin | 01 | 4 | Start a staging image; payload is expected CRC-32. |
| LOAD word | 01 | 9 | Payload byte 0 is the ordered address, bytes 1–8 the 64-bit word. |
| VALIDATE | 02 | 0 | Validate the staged 14-word image; report the final promotion or refusal, not initial receipt. |
| START | 03 | 0 | Report actual ownership acceptance or refusal. |
| STATUS | 04 | 0 | Return five bytes: flags, then the 32-bit little-endian run ID. |
| RESULT | 05 | 0 | Return six fresh 32-bit slices (24 bytes), or a refusal/fault. |

Endpoint status conventions: `00` completed successfully, `20` refused,
`21` fault and `22` busy. Other endpoint status values are reserved. Parser
statuses: `01` malformed frame/version/checksum/UART stop bit, `02` invalid
length, `03` unsupported command and `04` inter-byte timeout. Parser errors
carry no payload. STATUS flag bits 0–5 mean active image valid, owned, complete, fault, loading
and checking, respectively; bits 6–7 are zero. The adapter transports up to
24 response bytes without interpreting them or enforcing command-specific
response lengths. The mock serial test returns an empty STATUS payload, so it
tests framing only and does not validate STATUS semantics. The real endpoint
must enforce STATUS and RESULT payload formats, result ordering and freshness;
no mock result is hardware evidence.

The adapter makes no endpoint request until the entire frame and checksum have
passed. `req_valid` and its command/payload remain stable until `req_ready`.
The endpoint must produce one `done_valid` completion (which may coincide with
acceptance), carrying the actual outcome. Receipt and `req_ready` alone never
generate a success response. A request has no endpoint timeout in this stage;
a host timeout does not establish refusal or cancellation. Reset clears parser,
request and response state, but cannot undo an effect the endpoint already
committed. Any late completion outside the active request is ignored; the real
endpoint must suppress or identify late completions across resets and requests.
The untagged handshake cannot authenticate a falsely attributed completion.

This is a **stop-and-wait** protocol: the host must send no new frame until it
has received the complete response. Bytes arriving while a request is pending
or a response is being sent are ignored and receive no BUSY response. A host
must resynchronize after reset or timeout; byte loss and late effects are not
resolved by this prototype. `FRAME_TIMEOUT` measures cycles between received
bytes, defaults to 50,000 cycles in the link, and must exceed a byte time.
Oversized frames are discarded for their declared payload length plus checksum,
then refused; a timeout during discard also refuses. After every parser error,
the adapter drains incoming bytes until RX has been idle for FRAME_TIMEOUT
clock cycles. Activity during the error response also resets this timer. The
host must leave that quiet interval after an error before sending a new frame.
The interval must exceed a complete UART byte including synchronization delay;
otherwise continuous framed input may be mistaken for an idle interval. A physical reset must
assert the adapter's `rst_n`; the future wrapper owns that connection.

## Reproduction

```sh
bash research/h0_uart_1a/run_1b.sh /tmp/h0-uart-1b-check
```

The mock tests cover complete-frame gating, bad XOR, version, oversize with an
embedded start marker, truncated input and timeout, unsupported command,
invalid length, UART framing error, delayed endpoint acceptance and completion,
endpoint refusal, response integrity, reset during a frame and a pending request,
all five commands and a 24-byte response. A second test sends a STATUS frame
through the actual RX/TX primitives to a mock endpoint. These do not establish
controller semantics, real write acceptance, program CRC behavior or CPU
execution. No physical timing, board, synthesis or hardware claim is made.

The audit regression includes bad-version and broken-stop serial frames whose
trailing bytes contain a valid START, and an oversized frame with the embedded
START placed after an immediate error response could finish. Six mutation
controls require their corresponding specific assertions, including checksum
skipping, early acknowledgement, invalid LOAD length, oversized endpoint
response, bypassed quiet drain and bypassed oversize discard.
