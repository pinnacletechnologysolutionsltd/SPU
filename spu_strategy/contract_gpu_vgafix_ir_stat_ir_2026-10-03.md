# Engineering Contract: single-process VGAFIX IR → STAT → IR diagnostic

**Date:** 2026-10-03  
**Contract ID:** `contract_gpu_vgafix_ir_stat_ir_2026-10-03.md`  
**Status:** DRAFT — offline preparation recorded; implementation review and new hardware authorization pending  
**Roles:** Codex drafts, implements offline and records evidence; reviewer checks implementation/contract; owner authorizes the proposed hardware budget.

## 1. Review the frozen preparation

```bash
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/preparation_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/implementation_review_packet.md
printf '%s  %s\n' '27941d6cedf3ebf565a07e9d23477b0bb9171da94fbf8cd8ccc01d82a34f8743' 'build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/frozen_inputs.sha256' | sha256sum -c -
sha256sum -c build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/frozen_inputs.sha256
```

Review only the new helpers/evidence beneath
`build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/` and this contract.
No RTL, constraints, loader installation, old contract, bitstream, generated
catalog, old hardware evidence or repository snapshot is changed. Root contract
template: `spu_strategy/contract_template.md`. The earlier audit and physical
observations remain in `spu_strategy/diagnosis_gpu_vgafix_crc_loader_audit_2026-10-02.md`
and `docs/hardware_evidence.md` §3.34.

The frozen manifest covers 46 inputs: all new Python helpers, six offline fixture
records, the C ABI reference/source, retained firmware/header references,
the exact Python interpreter, libusb shared library, timeout executable/header,
and immutable earlier CRC-contract/hardware baseline evidence.
Manifest SHA-256: `27941d6cedf3ebf565a07e9d23477b0bb9171da94fbf8cd8ccc01d82a34f8743`.
The new contract is bound separately by its full SHA-256 in the review packet
and in the eventual owner authorization record; it is outside the manifest to
avoid a circular identity dependency.

Native execution dependencies are immutable external inputs:
`/usr/bin/python3.14`, `/usr/lib/libusb-1.0.so.0.6.0` and `/usr/bin/timeout`.
Their hashes are in the frozen manifest and checked before native imports.
Do not install PyUSB, modify dependencies or substitute another transport.
Unknown firmware format or environment identity halts this proposal.

## 2. Review exact operations and side effects

```bash
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/usb_bindings.py
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/checked_usb.py
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/dirty_protocol.py
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/bracket_sequence.py
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/run_diagnostic.py
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/execute_attempt.py
```

Execute no hardware commands during review. Inspect these proposed operations:

1. Verify manifest identity, every input hash, fresh owner authorization,
   setup/readiness fields, and host mount namespace `mnt:[4026531832]`.
   Reject inherited bytecode caches, symlinked helper paths and existing output
   directories. Use the isolated Python interpreter with bytecode writes disabled.
2. Initialize libusb, enumerate cached device descriptors, require exactly one
   `1209:c0ca`, open it once, check serial `CB81353DCE678119`, require USB
   configuration 1 and interface 0 free of a kernel driver, then claim it.
   No USB reset, configuration selection, detach or alternate-interface change.
3. Read CMD_INFO once: require exactly ten bytes `DJTAG2\n\0\0\0`.
   Write CMD_FREQ once with bytes `02 03 E8 00` (requested 1 MHz).
   No retry on missing, malformed or partial response. This identifies a protocol
   format; it does not attest the adapter's installed firmware image.
4. Apply six high TMS clocks and one low clock to reset the TAP and enter idle.
   Scan 64 DR bits once using incoming ones; require first 32 captured bits,
   LSB first, equal `0x03631093`, and remaining 32 equal `0xffffffff`.
   This checks the known single-target chain shape. No separate loader detect
   or adapter reopen is permitted.
5. Shift six-bit BYPASS (`0x3f`, LSB first), preserving all captured IR bits
   as `ir_before`. Require the mandatory low capture bits `01`; record other
   flags even if DONE/INIT are low. Return to idle.
6. Reset TAP to idle, shift CFG_IN (`0x05`), preserve its captured IR,
   then send exactly five 32-bit configuration words, MSB first:
   `AA995566 20000000 2800E001 20000000 20000000`.
   Keep SHIFT_DR for the first four words; exit on the last bit of the fifth.
   Select CFG_OUT (`0x04`), preserve its IR capture, read exactly 32 STAT bits
   while shifting dummy input `0x00000020`, then return to idle.
7. Reset TAP to idle; shift six-bit BYPASS again and preserve `ir_after`.
   Return to idle and release/close the same USB handle. No reopen control.

This uses AMD UG470's JTAG STAT procedure, Table 6-5, whose cleanup is TAP reset.
TAP reset changes JTAG state; this sequence does not issue configuration-reset
instructions. [AMD configuration guide](https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content).
Allowed IR inputs: CFG_IN, CFG_OUT, BYPASS only; the default IDCODE after TAP
reset is read without loading a new IR. No JPROGRAM, JSTART, ISC_ENABLE,
SHUTDOWN, RCRC, DESYNC, frame-data write, reload, flash, UART or board reset.
GETSIG/SETSIG masks cover TCK/TDI/TMS only, never TRST/SRST.

Check every native result code and every returned byte count. For bulk transfers,
zero return alone is insufficient; partial transfers can accompany errors.
Record raw bytes and counts before raising an error.
[libusb synchronous I/O documentation](https://libusb.sourceforge.io/api-1.0/group__libusb__syncio.html).
No loop retries an empty or short read. Every TMS clock is sampled through
GETSIG; every scan captures TDO. Preserve outgoing packets, raw responses,
normalized serial bits, monotonic elapsed time, UTC phase endpoints and decoded
fields in a flushed/fsynced journal. Record void resource-release calls as void;
check interface-release status. On failure, close resources without additional
JTAG clocks or recovery. TAP/target state after a partial operation is UNKNOWN.

CMD_FREQ has no firmware acknowledgment. Complete host writes do not independently
prove firmware execution or physical frequency. The 1 MHz request governs PIO
shift bursts; manual TMS clocks have USB/software pacing. No measured frequency
or timing tolerance is asserted. The local firmware reference is commit
`59b7f34fb031e164dafae6b3a56875687d1acf77`, with captured source hashes/license;
its identity is not attributed to the running adapter.

## 3. Inspect bounded offline verification

```bash
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/sequence_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/native_usb_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/usb_open_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/authorization_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/launcher_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/abi_fixtures_01.json
```

Recorded checks: 124 sequence/bit/error-stop, 23 bulk/resource/error checks,
55 connection prerequisite checks, 20 authorization/frozen-input guards,
42 launcher/terminal checks and 18 C ABI checks — 282 PASS.
The independent software TAP model expects 40 exchanges, 79 bulk calls and
340 TCK edges on a complete sequence. It rejects wrong packet contents and
injects failure at every exchange, verifying that no later command is sent.
The C reference compares descriptor layout against the installed libusb header
and verifies selected native signatures without loading the USB library.
All fixtures are offline, use exclusive output creation and have already run.
Do not rerun them over their frozen outputs. They do not establish electrical
timing, live firmware behavior, SRAM contents, measured reset or display correctness.

Repository verification remains the earlier frozen snapshot PASS. As specified
by the owner, no repository rerun is indicated by these diagnostic findings.
This preparation claims no new engineering/repository closeout or silicon PASS.

## 4. Proposed owner authorization and frozen hardware budget

```bash
cat build/gpu/vgafix_ir_stat_ir_20261003/owner_authorization_01.json
```

Do not create a positive authorization record from this review. After
implementation/contract review passes, obtain explicit owner authorization for
this exact contract/hash and input manifest. Separately obtain current readiness
and unchanged Wukong/J10/monitor/DirtyJTAG association and harness/settings.
Record whether board power has stayed continuous since the CRC load; a reported
power interruption is retained and prevents assuming the prior configuration.
Neither value makes active configuration known. No current readiness is inferred
from older messages.

Require a real file at the command's authorization path with these JSON fields:
`authorized_contract` equal to this filename; `contract_sha256` equal to the
reviewed document hash; `manifest_sha256` equal to the frozen manifest above;
`owner_authorized`, `same_wukong_j10_monitor`, `setup_unchanged`, `ready_now`
all true; `power_continuous_since_crc_load` explicitly Boolean;
`authorization_quote`, `readiness_quote` preserving the owner's actual words;
and timezone-aware `readiness_utc`, aged 0–300 seconds at each guard check.
Expired readiness is a stop, not an approval or automatic refresh.

Budget: **one launcher invocation, one USB connection, one chain scan, four
six-bit IR captures and one STAT read**. Outer wall-clock timeout 30 seconds,
forced-termination grace two seconds; maximum cumulative campaign budget
32 seconds. The child diagnostic has a 20-second external limit plus two-second
grace, contained within that outer limit. Native bulk calls have 250 ms limits
and an 18-second internal deadline checked before each bulk call.
Human review/readiness waits authorize no operation and do not consume tool time.
Launching consumes the sole slot regardless of guard failure, unavailable output,
error, timeout or result. No retries, timeout extensions, second connection,
comparison control, observation timer or recovery. Earlier budgets cannot fund it.

## 5. Proposed execution — NOT AUTHORIZED BY THIS DRAFT

```bash
printf '%s  %s\n' '27941d6cedf3ebf565a07e9d23477b0bb9171da94fbf8cd8ccc01d82a34f8743' 'build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/frozen_inputs.sha256' | sha256sum -c -
sha256sum -c build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/frozen_inputs.sha256
/usr/bin/timeout --signal=TERM --kill-after=2s 30s /usr/bin/python3.14 -I -B /home/john/Projects/hardware/SPU/build/gpu/vgafix_ir_stat_ir_20261003/preparation_01/execute_attempt.py --manifest-sha256 27941d6cedf3ebf565a07e9d23477b0bb9171da94fbf8cd8ccc01d82a34f8743 --authorization /home/john/Projects/hardware/SPU/build/gpu/vgafix_ir_stat_ir_20261003/owner_authorization_01.json
```

Run sequentially in the frozen host namespace; halt on either input-check failure
before the hardware-stage launch. Foreground managed execution is appropriate
for this interactive hardware command bounded below 60 seconds. The launcher
creates new `attempt_01`, records command/authorization/start, and invokes one
bounded child. The child creates new `hardware_01` for authorization, journal and
result. Both refuse existing output paths; no overwrite or alternate path retry.
The launcher writes exactly one terminal marker: COMPLETE for child exit 0,
TIMEOUT for exit 124, FAILED otherwise. Exit 137 is FAILED with preserved status;
do not infer timeout causality from SIGKILL alone. Missing terminal markers mean
UNAVAILABLE, including termination of the outer launcher. No inference from logs,
missing process or elapsed time. Require result/journal as well as the marker.
No COMPLETE marker is a startup, delivery or display PASS.

Preserve the managed command's exit and output separately if the launcher never
writes a terminal result. Record outer timeout/forced termination as infrastructure
evidence while leaving the missing internal result unavailable. No new launch
is permitted. Append physical execution evidence to the hardware ledger only
after this separately authorized attempt has actually run.

## 6. Outcomes and stop conditions

| Result | Classification and permitted statement |
| --- | --- |
| Transport/identity/IR low-bit validation failure | HALT; preserve raw/partial records; target state UNKNOWN |
| Before/after raw IR differ | IR_BRACKET_CHANGED; sampled state differs across the bracket |
| Raw IR stable; DONE/INIT disagree with STAT | IR_STAT_DISAGREEMENT; sampled interfaces disagree |
| Raw IR stable; DONE/INIT agree with STAT | IR_STAT_SHARED_FLAGS_AGREE; common flags agree, whether high or low |
| External timeout or missing terminal/result | Infrastructure TIMEOUT or UNAVAILABLE; no retry |

Record all STAT flags and all captured IR flags regardless of the shared-flag
classification. Low flags are useful diagnostic observations and do not cause
the bracket to stop after a valid sample. No automatic restoration or reload
follows any classification. Preserve active-configuration UNKNOWN and delivery
NOT ESTABLISHED because status sampling does not identify the frame payload.
Do not classify display behavior; no new photo/video observation is proposed.
Earlier display HOLD remains independent.

There is no no-query comparison interval or USB-reopening comparison control.
A bracket change cannot establish that the query caused it; a difference from
the earlier separate-process result cannot isolate USB reopening from elapsed
time, transport implementation, clock pacing or target-state changes. Freeze
a separate comparison proposal before making those causal claims.

HALT review on an unhandled protocol state, clock/sampling hazard, identity
dependency, accepted negative fixture or contradiction between code and contract.
Record a minimal proposed correction and revised hashes before authorization.
No synthesis, repository gate, loader patch or hardware operation is authorized
by offline preparation or by this DRAFT.
