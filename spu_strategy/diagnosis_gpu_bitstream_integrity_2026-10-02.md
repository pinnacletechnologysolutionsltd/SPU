# VGAFIX and recent GPU bitstream integrity diagnosis

**Date:** 2026-10-02  
**Status:** Offline audit recorded; authorized CRC campaign halted on startup anomaly  
**Scope:** Owner prioritized diagnosing recent bitstreams; existing analyzer draft deferred. Sections 1–5 record offline preparation; §6 records the separately authorized CRC load/query. No synthesis, UART, wiring change, or repository regression rerun.

Read the durable results:

```bash
cat build/gpu/t1r_bitstream_audit_20261002/packet_inventory_01.json
cat build/gpu/t1r_bitstream_audit_20261002/frame_comparison_01.json
cat build/gpu/t1r_bitstream_audit_20261002/comparison_negative_controls_01.json
```

## 1. Disk images and packed frames

The current historical VGAFIX file matches the exact SHA-256 cited for the
successful September display: `a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379`.
The recent T1q and T1r files likewise match their recorded route/load hashes.
All seven inspected VGAFIX/T1m/T1n/T1o/T1p/T1q/T1r headers identify
`xc7a100tfgg676-1`; their declared payload lengths and packet boundaries parse
fully. The seven configuration command streams are identical when their frame
data bodies are excluded. Their frame payloads are distinct.

| Key image | Current SHA-256 | Retained frame-input comparison |
|---|---|---|
| Historical VGAFIX | `a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379` | PASS |
| T1q Q1 | `c2458086d6efcc323f70039dce87754ae6ff8bcf8012aed2e1404862332a728d` | PASS |
| T1r Q1 | `5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7` | PASS |

For those three key images, independent Python reconstruction from retained
`.pnr.frames` and part topology reproduces the entire packed FDRI payload,
including frame ECC and row padding: 9448 device frames plus sixteen padding
frames, 955864 words. Rules were inspected in the local Project X-Ray source;
their hashes are preserved in `reference_source_hashes_01.json`. Digest and
length mutation controls both reject. This verifies consistency of file
packing with the retained frame inputs; it does not prove logical correctness
of those inputs or actual FPGA SRAM contents.

The installed `bitread` decoder failed before decoding VGAFIX in two offline
probes with return code -11. It is not used as passing evidence. Preserve the
first stdout/stderr and original comparison adapter; the second probe's return
code was observed in the tool output and is recorded in the comparison report.
No toolchain repair or decoder rebuild was attempted. The successful comparison
uses the separate Python reconstruction, not a success inferred from that crash.

## 2. Build profile, sources, and retained netlists

All eight archived T1r outputs match their recorded hashes and the corresponding
current primary artifacts. Every path in its route-preflight source hash list
still matches. The synthesized T1q/T1r top parameters select their respective
truth-table/palette-pair profiles, with four primitives, UV scene, pipeline
partition, and post-winner register enabled; incompatible profile flags are off.
The recorded T1r build used the UART synthesis script, and the retained netlist
contains `uart_rx`.

Retained VGAFIX/T1q/T1r routed netlists use identical clock/reset and VGA I/O BEL
locations. Their FASM contains the reset pull-up. Source-derived clock division
remains 50 MHz / 2. No new pin-placement or profile mismatch was found in these
checks. The conflicting J10 numbering is in comments, not changed executable
PACKAGE_PIN constraints; it does not explain a changed packed configuration.

Retained metrics report pixel-clock timing PASS for T1q (36.92 MHz) and T1r
(35.73 MHz) against 25 MHz. Historical VGAFIX metrics have the previously noted
source-anchor discrepancy and remain contextual. A retained route/profile is
not a fresh logic-equivalence proof connecting the netlist to current silicon.
The completed Padé verification result is a separate repository gate.

## 3. Configuration integrity gap

Every inspected bitstream writes frame data, then issues RCRC (reset CRC) before
GRESTORE/LFRM/START. None contains a write to the CRC register supplying an
expected checksum. The local Project X-Ray `createConfigurationPackage<Series7>`
code emits that same sequence. This behavior exists in the historical working
VGAFIX image as well as the recent GPU images; it is not a newly introduced
T1r command-sequence change.

The October VGAFIX programming/startup result remains PASS as defined by its
contract: transfer and startup flags passed and STAT reported no CRC error.
That result is not an end-to-end comparison of the transferred configuration
payload. In particular, no CRC error does not establish matching frame data
when these files never supply the expected CRC check. File hashes and frame ECC
in the archived file do not supply live SRAM readback evidence.

The installed loader's capabilities can be reviewed without touching hardware:

```bash
openFPGALoader --help
```

Its `--verify` option is explicitly SPI-flash-only. It does not verify this SRAM
load. A flash dump is not SRAM configuration readback and may use a bridge that
changes the volatile configuration; do not substitute that operation.

## 4. What the audit establishes and the next diagnostic

No disk corruption, wrong-device header, retained-frame packing mismatch,
changed startup command sequence, T1r archived-output mismatch, or recorded
source/profile mismatch was found within this offline scope. The same historical
VGAFIX bytes that previously displayed bars are now reported as corrupted after
a load; newly changed VGAFIX file bytes cannot account for that difference.
Evidence for the physical observations remains
[hardware ledger §§3.8 and 3.33](../docs/hardware_evidence.md#333--vgafix-display-control-programmingstartup-pass-visual-hold-2026-10-02).

The next bitstream-focused diagnostic should establish file-to-SRAM integrity:
review a supported configuration-frame readback path, or prepare and validate
a CRC-checked variant of the same frozen frame payload for one separately
bounded load. That proposal must preserve image/frame identity, declare the
readback comparison/masks or exact CRC algorithm and insertion point, freeze
its commands and budget, and pass implementation review before execution.
A CRC check would test delivery integrity; it would not establish reset release,
pixel-clock liveness, or display correctness. No specific physical cause is
assigned by this audit, and no follow-on hardware operation is authorized here.

Repository PASS stays limited to the earlier frozen snapshot. VGAFIX remains
visual HOLD. These new reports and offline audit helpers were not inputs to
the completed repository gates.

## 5. Prepared delivery diagnostic

Review the separately bounded proposal in
[`contract_gpu_vgafix_crc_delivery_2026-10-02.md`](contract_gpu_vgafix_crc_delivery_2026-10-02.md).
The installed loader offers no ready SRAM frame-readback command; custom
readback/masking remains outside this preparation. A derived VGAFIX copy
adds two expected CRC checks by replacing the two post-initial RCRC packets.
The full 955864-word frame payload and all other bytes are preserved.

The candidate SHA-256 is
`534e88759e10aa66330fbeb10856635f93d7c5306c277de841a09587ccde49f9`.
Offline verification recorded 83 passing checks, including independent C++
checksum agreement and falsifiable corrupted-image/guard fixtures. Review
evidence is in `build/gpu/vgafix_crc_delivery_20261002/preparation_01/`.
Preparation did not identify the display fault. At preparation closeout the
candidate was unprogrammed and the new hardware budget awaited authorization.

## 6. Authorized CRC campaign: startup anomaly

The owner subsequently authorized the frozen campaign and confirmed the same
setup, continuous power and readiness. Preflight and frozen inputs passed.
The single SRAM job completed with exit 0 in 32 seconds, 100% transfer and
immediate IR `isc_done 1`, `init 1`, `done 1`.

The subsequent single STAT query returned `0x40000018`, with INIT Complete,
INIT B, GWE, Release Done and Done all 0. CRC/ID/DEC errors were reported absent
and EOS was 1. The command exited 0, but the frozen startup guard correctly
HALTed. This disagrees with the immediate post-load IR report and prevents
classifying CRC delivery or startup as PASS. Active configuration is UNKNOWN.
No root cause is assigned from these two observations.

The campaign stopped before its photo/video observation. No further hardware
command, recovery, replacement image or repository rerun was performed.
Preflight, launcher, load and query slots are consumed; the observation was
NOT RUN because its prerequisite failed. Preserve the authorized contract and
frozen helper/image hashes unchanged. Evidence and independent classifications
are in `build/gpu/vgafix_crc_delivery_20261002/hardware_01/hardware_result_01.json`
and [hardware ledger §3.34](../docs/hardware_evidence.md#334--vgafix-crc-delivery-transfer-complete-subsequent-startup-anomaly-2026-10-02).

The owner-authorized offline follow-up is recorded in
[`diagnosis_gpu_vgafix_crc_loader_audit_2026-10-02.md`](diagnosis_gpu_vgafix_crc_loader_audit_2026-10-02.md).
Independent supplied CRC checkpoints support the file-level construction;
the query words and cleanup agree with the JTAG-specific procedure. An installed
loader transport-return-code defect was reproduced offline, but no evidence
establishes that it caused the recorded startup anomaly. No hardware operation
or repository rerun occurred. The HALT and UNKNOWN classifications remain.
