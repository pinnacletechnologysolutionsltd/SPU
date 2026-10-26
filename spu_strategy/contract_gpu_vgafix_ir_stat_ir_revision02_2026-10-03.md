# Engineering Contract: VGAFIX IR → STAT → IR, supervisor revision 02

**Date:** 2026-10-03  
**Contract ID:** `contract_gpu_vgafix_ir_stat_ir_revision02_2026-10-03.md`  
**Status:** DRAFT — corrected implementation prepared offline; independent review and new hardware authorization pending  
**Roles:** Codex drafts and implements this bounded correction; reviewer audits the supplied code and contract; owner authorizes any subsequent hardware attempt.

## 1. Review immutable evidence and scoped correction

```bash
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/preparation_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/implementation_review_packet.md
sha256sum build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/frozen_inputs.sha256
sha256sum -c build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/frozen_inputs.sha256
```

Frozen manifest SHA-256: `ab0db933768089ba56c35793759eb2725487a83280ccbffa7240bdf36bdaf00c`.
Bind this contract's separate full SHA-256 from the packet identity in any future authorization; the contract is outside the input manifest to avoid circular hashing.

Preserve the original proposal, all 282 original checks, and its HOLD review beneath `build/gpu/vgafix_ir_stat_ir_20261003/`. Original contract SHA-256: `b2bc27bd892e87b4ab7dda6fc0678bc8bd95fbd3b0b7c946a87b1d796ffcb2d3`. Original review packet SHA-256: `1621335572c1eabd0b737bf4a765c74ec0d520a46183cb9fbdd6b53526443d12`. Its failing lifecycle fixtures remain evidence of that revision.

All revised helpers and evidence occupy the separate campaign `build/gpu/vgafix_ir_stat_ir_20261003_revision02/`. Changes are confined to attempt reservation/terminal recording, Linux process supervision, corresponding offline fixtures, the worker's new contract identity, and this contract. Checked USB/protocol/TAP sequence modules are byte-identical to the original. No RTL, constraints, bitstream, loader, earlier hardware evidence, generated catalog, or repository snapshot is changed.

Review `attempt_record.py`, `process_supervisor.py`, `execute_attempt.py`, `run_diagnostic.py`, their fixtures, and every frozen input before authorization. The exact interpreter, libusb library, libc used for `prctl`, retained firmware/header references, ABI executable, original frozen inputs/review, and offline results are hashed. Native runtime inputs remain immutable external dependencies; do not install or substitute them.

## 2. Review exact operations and side effects

```bash
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/usb_bindings.py
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/checked_usb.py
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/dirty_protocol.py
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/bracket_sequence.py
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/run_diagnostic.py
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/execute_attempt.py
```

Execute no hardware commands during review. Inspect these proposed operations:

1. After the durable reservation, the supervised worker verifies manifest identity, every input hash, fresh owner authorization,
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

## 3. Review offline verification

```bash
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/fixtures_02/sequence_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/fixtures_02/native_usb_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/fixtures_02/usb_open_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/fixtures_02/authorization_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/fixtures_02/abi_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/fixtures_04/supervision_fixtures_01.json
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/fixtures_04/launcher_fixtures_01.json
```

Current normative evidence: 124 sequence/bit/error-stop checks, 23 transfer/resource checks, 55 connection checks, 20 authorization checks, 18 ABI checks, 40 real process-supervision checks, and 35 attempt-accounting checks: **315 PASS**. Earlier local fixture runs are retained and are not added to this count.

Process fixtures use sleeping dummy workers, process forks, independently created sessions, ignored TERM signals, orphaned descendants, interruption of the supervisor, and an exhausted deadline before launch. Every successful supervision fixture checks that owned children were reaped and their recorded PIDs no longer exist. Attempt fixtures test reservation before preflight, malformed arguments, actual worker input rejection before USB, timeout, missing subreaper prerequisites, partial reservation, and refusal of a second invocation.

Normative protocol/ABI fixtures run against copied byte-identical helpers. The latest supervisor/accounting fixtures run against the final revised source copies; their source identities are checked during freezing. No native USB backend is opened. No positive owner authorization is created. Reproduce only in a separate fixture checkout/output directory; never overwrite frozen fixture outputs or call a hardware entrypoint against the production campaign as a fixture.

These checks establish tested software behavior; they do not establish live adapter firmware, electrical timing, SRAM equality, or display correctness. The earlier repository snapshot PASS remains separate. No repository rerun or synthesis is indicated for this diagnostic correction by the owner's scope. No new engineering/repository closeout or silicon PASS is claimed.

## 4. Proposed authorization, durable reservation, and single deadline

```bash
cat build/gpu/vgafix_ir_stat_ir_20261003_revision02/owner_authorization_01.json
```

Do not create positive authorization from this preparation or review. After independent implementation/contract review passes, obtain owner authorization for this exact contract/hash and manifest, plus current readiness and unchanged Wukong/J10/monitor/DirtyJTAG association, harness and settings. Record power continuity explicitly; no prior active configuration is inferred.

Require the worker authorization JSON fields: `authorized_contract` equal to this filename; `contract_sha256` equal to the reviewed full document hash; `manifest_sha256` equal to the manifest above; `owner_authorized`, `same_wukong_j10_monitor`, `setup_unchanged`, `ready_now` all true; `power_continuous_since_crc_load` explicitly Boolean; actual `authorization_quote` and `readiness_quote`; and timezone-aware `readiness_utc` aged 0–300 seconds at worker preflight. A stale or invalid record terminates the consumed attempt before USB.

Budget: **one supervisor invocation, one USB connection, one chain scan, four six-bit IR captures, one STAT read; maximum campaign wall time 32 seconds**. Invocation consumes the sole slot, including preflight rejection, unavailable output, and infrastructure failure. No earlier authorization/budget funds this new proposal.

At entry, capture one monotonic start time. Before argument parsing, hash validation, authorization checks, subreaper prerequisites, or worker launch, exclusively create `attempt_01`, fsync its campaign directory, and write/fsync `launch.json` and its directory. Existing or partially created reservation paths refuse a second invocation. If reservation cannot be durably completed, stop without launching a worker; missing records never authorize retry. Preserve the managed invocation's external evidence for that unavailable outcome.

The supervisor must run as a fresh Linux process, enable and verify `PR_SET_CHILD_SUBREAPER`, and have no inherited children. Then fork/exec exactly one worker. The worker performs all input/authorization preflight before importing/opening hardware-capable helpers. No nested GNU timeout or independent renewed worker budget exists.

All deadlines use the supervisor's invocation start: request TERM at **20 seconds**, force KILL at **22 seconds**, and finish reaping by **30 seconds**, reserving the last **two seconds** for durable terminal evidence within the **32-second cap**. Preflight time is included. If execution budget is already exhausted before launch, record TIMEOUT without a worker. Early worker exit or supervisor TERM/INT/HUP also triggers cleanup; it does not authorize recovery.

Kill the owned worker process group and direct children. Linux subreaping adopts orphaned descendants, including descendants that create independent sessions; repeatedly KILL and nonblockingly reap newly adopted children. Restore signal handlers only after cleanup. A worker that exits while descendants remain is FAILED, even if its exit was zero. COMPLETE requires worker exit 0, no supervisor interruption, no unexpected descendants, and verified reaping of all owned children. Prerequisite/preflight failure is FAILED. Deadline exhaustion is TIMEOUT (exit 124). A reap deadline or measured cap violation is UNAVAILABLE; never report containment PASS or hardware success for that outcome.

Native bulk calls retain their 250 ms limits and 18-second internal deadline; that worker-local guard cannot extend the invocation deadline. Missing terminal evidence, supervisor forced termination, unreaped children, or a recorded limit violation are infrastructure outcomes. Preserve the managed command's elapsed time and exit; no retry, extension, substitute transport, second connection, reload, observation timer, or recovery follows.

## 5. Proposed execution — NOT AUTHORIZED BY THIS DRAFT

```bash
sha256sum -c build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/frozen_inputs.sha256
/usr/bin/python3.14 -I -B /home/user/Projects/hardware/SPU/build/gpu/vgafix_ir_stat_ir_20261003_revision02/preparation_01/execute_attempt.py --manifest-sha256 ab0db933768089ba56c35793759eb2725487a83280ccbffa7240bdf36bdaf00c --authorization /home/user/Projects/hardware/SPU/build/gpu/vgafix_ir_stat_ir_20261003_revision02/owner_authorization_01.json
```

The first command is a read-only input check; stop on failure before the single supervisor invocation. Use the frozen host namespace `mnt:[4026531832]`, reviewed real helper/campaign paths and exact external interpreter/native inputs. Do not add another timeout wrapper or reopen control. Foreground managed execution records command, elapsed time, stdout/stderr and exit for this interactive command below 60 seconds.

The supervisor's `attempt_01` holds `launch.json`, worker stdout/stderr, `result.json`, and exactly one terminal marker: COMPLETE, FAILED, TIMEOUT, or UNAVAILABLE. Records/files and containing directories are fsynced. A missing marker/result is UNAVAILABLE; missing logs can legitimately mean rejection before worker launch. A worker that passes all guards creates a separate fresh `hardware_01` holding authorization, raw journal and diagnostic result. Worker preflight rejection creates no hardware output. Neither directory may be overwritten.

Require terminal record, checked elapsed time and verified reaping before interpreting a result. A COMPLETE process outcome is not configuration-delivery or display PASS. Only append hardware execution to the evidence ledger after a separately authorized physical attempt actually runs.

## 6. Outcomes and stop conditions

| Result | Classification and permitted statement |
| --- | --- |
| Transport/identity/IR low-bit validation failure | HALT; preserve raw/partial records; target state UNKNOWN |
| Before/after raw IR differ | IR_BRACKET_CHANGED; sampled state differs across the bracket |
| Raw IR stable; DONE/INIT disagree with STAT | IR_STAT_DISAGREEMENT; sampled interfaces disagree |
| Raw IR stable; DONE/INIT agree with STAT | IR_STAT_SHARED_FLAGS_AGREE; common flags agree, whether high or low |
| Supervision timeout or missing terminal/result | Infrastructure TIMEOUT or UNAVAILABLE; no retry |

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
