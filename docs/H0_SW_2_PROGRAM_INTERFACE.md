# H0-SW-2 bounded program interface: software prototype

**Status: experimental software only, not an approved H0 protocol or a
hardware implementation.** The prototype does not run on an FPGA, simulate RTL
cycles, or establish Gen-1 ISA conformance. Its direct formula evaluates a
restricted program shape; it is not a general instruction interpreter. No
production integration is authorized by this note. Source baseline `7ac2cc0`.

## Interface and evidence boundary

`software.spu_host.h0_program.ProgramController` exposes four logical operations:

| Operation | Accepted state and behavior |
|---|---|
| `load(bytes, sha256_hex)` | In any state except ACTIVE, accept exactly 112 immutable bytes and a lowercase 64-character digest. Allocate a new `(epoch, sequence)` owner and replace the prior candidate/result. Invalid requests leave the old state intact. |
| `verify(id)` | In LOADED, check the supplied digest against the stored bytes and check the entire supported program shape and bounds. Failure leaves the candidate LOADED and does not authorize execution. |
| `execute(id)` | In VERIFIED, enter ACTIVE; this starts only a software simulation. Competing loads are BUSY and cannot replace active state. |
| `result(id)` | Return a result only in COMPLETE and only for the current owner; otherwise return a deterministic refusal. |

`advance_simulation(id)` is a local test-driver step that evaluates the
candidate and enters COMPLETE. It is not a fifth hardware or wire command.
Successful results are explicitly labelled `SIMULATED_RESULT` and contain
`(a*a+3*b*b, 2*a*b, d*d)`. `reset()` clears candidate, result and ownership and
increments the software epoch. Missing, malformed or stale identities do not
mutate state. A failed load or a busy request cannot overwrite active work.
After a successful replacement load, prior results are inaccessible.

The accepted program is exactly 14 big-endian 64-bit words: six SLI S0 slices
in order, SLD S0, SMUL S0,S0,S0 and six SRD S0 slices in order. Only
nonnegative one-limb `a,b` in `[0,1000]`, `d` in `[1,1000]`, with zero high
limbs, are accepted. These restricted values avoid overflow and signed/normalization
questions in this prototype; other valid CPU programs are deliberately refused.
SHA-256 detects mismatch against a supplied expected digest, not a malicious
sender or an independently authenticated source. Both bytes and digest may be
chosen by the caller. Identity tokens are unique only within a continuous
controller instance; restart, persistent epochs, wrap, multi-client ownership,
concurrency and transport replay protection are unspecified. The API is
sequential and requires faithful identities. Reset does not establish hardware
reset observation, physical cancellation or rollback. An interrupted real
operation has unknown outcome until separately specified recovery; it is not a
confirmed refusal.

The prototype reuses the reviewed H0-SW-1 `Identity` type and its strict
identity representation checks. It does not reuse `H0Model` itself: that model
only accepts the synthetic ECHO operation and its result/commit contract is not
a generic CPU backend. The host's notion of ACTIVE or COMPLETE is not evidence
of actual device effect commitment. No physical refusal or UART behavior is
asserted.

## Source-derived hardware gap and candidate boundary

The silicon-used `cpu_fetch_1b.v` has a 16-word initialized synchronous ROM,
fixed termination after PC 13, held issue word, ready/retire handshake, result
capture and sticky HALT/FAULT. It has no writable program port or external
program start/length. `cpu_integrate_1_top.v` connects the frontend to the
`spu13_core` surd issue, retirement and readback signals; the supervisor
generates reset and latches completion only for six valid result slices. These
are observations of the committed frozen sources under
`hardware/boards/artix7/wukong_v3/cpu_v02/rtl/`, not evidence of a writable
CPU image.

A future implementation needs, at minimum, writable bounded instruction storage
with exclusive load ownership and no writes while executing; a validation and
integrity boundary before execution; a latched verified image identity and
length/termination rule; explicit start, reset and completion/fault handling;
and a coherent fresh result associated with the accepted run. The current fixed
ROM and PC-13 halt require a revised frontend or wrapper, and the supervisor's
six-slice completion policy must be retained for this narrow profile or revised
under a new contract. Core state initialization between programs and the
interaction of reset with stored programs and pending writes need explicit
decisions. Storage writes, validation, core effects and reset at their actual
clock boundaries must be independently verified; late effects and ambiguous
reset cannot be assumed away.

An initial UART adapter could translate framed, length-bounded messages into
the four logical calls and return identities, statuses and result bytes. Frame
format, wire commands, checksum, authentication, flow control, timeout, reset
observation and acknowledgement are **not** specified here. The execution
controller must remain independent of the chosen transport. An adapter cannot
turn local software simulation into a hardware guarantee.

## Reproduction

From the worktree root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s software/tests -p test_h0_program.py -v
```

Tests build real existing SLI/SLD/SMUL/SRD encodings using
`software.tools.surd_cpu_encoding`, submit two distinct programs to the same
controller without reconfiguration, and check `(13,4,9)` and `(7,4,4)`.
They also cover integrity mismatch, unsupported words and bounds, busy
preservation, stale and malformed identities, reset and pre-completion reads.
This does not compare against RTL or qualify arithmetic in silicon.
