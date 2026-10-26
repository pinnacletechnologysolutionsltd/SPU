# Engineering Contract: VGAFIX CRC/startup offline audit

**Date:** 2026-10-02  
**Status:** OFFLINE AUDIT RECORDED — owner instruction: "Let's run the audit."  
**Roles:** Codex drafts, reviews, executes offline checks and records findings.

## 1. Preserve inputs and scope

```bash
sha256sum -c build/gpu/vgafix_crc_delivery_20261002/preparation_01/frozen_inputs.sha256
cat build/gpu/vgafix_crc_delivery_20261002/hardware_01/hardware_result_01.json
```

Use new evidence directory `build/gpu/vgafix_crc_delivery_20261002/offline_audit_01`.
Preserve all previous contracts, packets, helpers, images, manifests and hardware
logs. This scope permits source downloads, disassembly, software compilation,
offline packet/CRC checks and evidence reports. No loader invocation against USB,
JTAG, SRAM load, STAT query, reset, flash, UART, analyzer, synthesis or repository
gate is authorized. Prior repository PASS applies only to its frozen snapshot.

## 2. Bind loader behavior to inspected inputs

```bash
rg -n 'program_mem|dumpRegister|read_register|reset' build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/xilinx.v1.1.0.cpp build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/main.v1.1.0.cpp
nm -C /opt/oss-cad-suite/libexec/openFPGALoader | rg 'Xilinx::(program_mem|dumpRegister|read_register|reset)'
```

Fetch release-v1.1.0 upstream source into this evidence directory; record URL,
hash and tag identity. Version text alone does not establish source/binary
equivalence. Inspect the exact installed binary with `objdump`; preserve the
function ranges and bytes. Trace JPROGRAM/BYPASS/CFG_IN/JSTART, final IR capture,
STAT packet generation, byte reversal, TAP transitions and cleanup. Distinguish
TAP reset from configuration reset. Inspect DirtyJTAG initialization and main
dispatch without opening a device. Flag any incomplete query cleanup separately
from any inference that it caused the observed low flags.

## 3. Audit CRC coverage against independent existing bitstreams

```bash
python3 build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/scan_crc.py
python3 build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/trace_query.py
```

Use the frozen CRC recurrence but independently parse packet coverage. Compare
the frozen candidate with existing Project X-Ray configuration test images and
the installed Artix-7 SPI bridge image, reading their supplied CRC words.
These images are offline fixtures only and may never be programmed under this
contract. Record headers, file hashes, packet counts, reset/checkpoint locations,
register coverage, expected/observed CRC and unsupported constructs. Do not infer
physical correctness from a software agreement or force fixture agreement by
silently changing the algorithm. Preserve a failed hypothesis as failed.

Run source-extracted `dumpRegister` with a mock JTAG recorder; verify actual
generated words and bit/byte reversal for recorded good and anomalous STAT
values. The recorder has no USB/JTAG implementation. Inspect binary behavior
separately, without claiming execution of the installed binary against hardware.

## 4. Halt-and-flag and closeout

HALT an implementation path on unsupported packet semantics, fixture mismatch,
source identity change or unhandled edge case; record the minimal correction
before continuing a different offline analysis. Keep the frozen CRC campaign
unchanged. Report established defects, ruled-out explanations and unresolved
causes separately. Any subsequent hardware proposal requires its own reviewed,
frozen commands and owner budget; this audit authorizes none.

Record an audit report in `spu_strategy/` and durable JSON evidence. Append
interpretation to the hardware ledger without rewriting raw observations.
Use scoped falsifiable offline checks; no new engineering/repository closeout
is claimed and no mandatory repository gate is rerun in this audit.

## 5. Recorded execution and fixture correction

**Status:** OFFLINE AUDIT RECORDED; hardware diagnosis remains unresolved.
The original §3 query command HALTed because its fixture treated CFG_OUT dummy
input as a written NOP. `fixture_halt_01.json` freezes the failure and proposed
minimal correction. Preserve the original helper, assertions, binary and logs.
The corrected offline path used separate names and outputs:

```bash
python3 build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/trace_query_02.py
python3 build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/check_crc_controls.py
python3 build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/trace_transport.py
```

These commands have already executed; evidence creation uses exclusive writes,
so this record is not an instruction to repeat them into existing outputs.
The corrected expectation distinguishes five CFG_IN writes from input bits
during the CFG_OUT read scan. All five write expectations remain unchanged.
CRC checks: six checkpoints across three images match, three mutation controls
reject. Query checks: three values round-trip; two mutation controls reject.
Transport checks: +1/-1 driver failures are discarded; a rejecting control
demonstrates the wrapper defect. No installed loader modification occurred.

AMD UG470 Table 6-5 confirms TAP-reset cleanup for JTAG STAT reads; DESYNC in
the SelectMAP table is not a missing JTAG requirement. No causal link between
the transport defect and the hardware anomaly is established. Full findings:
[`diagnosis_gpu_vgafix_crc_loader_audit_2026-10-02.md`](diagnosis_gpu_vgafix_crc_loader_audit_2026-10-02.md).
Audit closeout records input/evidence hashes and confirms preservation of the
frozen campaign. No additional hardware or repository phase was launched.
