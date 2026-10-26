# VGAFIX CRC and loader audit — 2026-10-02

**Result:** Offline audit recorded. CRC construction and STAT serialization
checks pass. A loader transport-error propagation defect is reproduced offline
and confirmed in the installed binary. Its involvement in the hardware anomaly
is unproven. Active FPGA configuration remains UNKNOWN; CRC delivery validation
remains NOT ESTABLISHED. Earlier VGAFIX visual HOLD is unchanged.

Owner instruction: "Let's run the audit." Scope and execution rules:
[`contract_gpu_vgafix_crc_offline_audit_2026-10-02.md`](contract_gpu_vgafix_crc_offline_audit_2026-10-02.md).
Evidence: `build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/`.
No hardware command, repository gate, synthesis, reset or reload ran in this audit.
All frozen preparation inputs and recorded hardware log hashes were checked at
closeout. No installed loader, frozen image or hardware helper was modified.

## 1. The observation to explain

The authorized SRAM load ended at `2026-10-02T09:06:47Z`, reporting 100% transfer
and captured IR `0x35` with DONE and INIT Complete set. The subsequent standalone
STAT query returned `0x40000018`; its frozen guard HALTed at
`2026-10-02T09:07:24.699893+00:00`. This value reports EOS set but INIT Complete,
INIT B, GWE, Release Done and Done clear. Both commands exited 0 with empty
stderr. Neither observation overrides the other. There is no measurement between
them locating a state change or establishing whether the STAT sample was valid.

Raw evidence and classifications remain in
[`hardware ledger §3.34`](../docs/hardware_evidence.md#334--vgafix-crc-delivery-transfer-complete-subsequent-startup-anomaly-2026-10-02)
and `hardware_01/hardware_result_01.json`. A software check cannot convert this
HALT into a silicon startup or delivery PASS.

## 2. CRC packet coverage is independently corroborated

`scan_crc.py` independently parses headers, Type-1/Type-2 packet extents and
register addresses, using the frozen checksum recurrence. It includes written
register data and addresses, handles RCRC resets and checks residuals after CRC
register writes. It rejects unsupported packet operations. Supplied checksums
in the existing fixtures are held-out inputs; they were not replaced or generated
by the candidate preparation script.

| Offline input | First supplied CRC | Second supplied CRC | Result |
| --- | --- | --- | --- |
| Frozen VGAFIX CRC candidate | `0x0b4dc570` | `0xe3ad7ea5` | Both match; residuals zero |
| Project X-Ray `configuration_test.bit` | `0x4e23c07c` | `0xe3ad7ea5` | Both match; residuals zero |
| Installed `spiOverJtag_xc7a100tfgg676.bit.gz` | `0x48032281` | `0x615009a6` | Both match; residuals zero |

The Project X-Ray fixture identifies Vivado 2016.3 / `7a50tfgg484`. The installed
compressed bridge identifies Vivado 2021.1 / `7a100tftg256`; its internal part
differs from its package filename. It was used only as a packet/checksum fixture,
with no assertion that it is suitable for this board. Neither fixture was loaded.
The candidate's second checksum also agrees with the corresponding example tail
in AMD UG470 Table 5-19. [AMD configuration guide](https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content).

`check_crc_controls.py` deliberately changes a frame-data bit, a COR0 bit and a
supplied CRC bit in separate copies of the independent Project X-Ray fixture.
All three fail the first checkpoint. This demonstrates that the checks can reject
bad data. `crc_coverage_01.json` records full packet coverage and identities;
`crc_controls_01.json` records the mutation offsets and results.

This evidence supports the candidate's file-level CRC construction. It does not
measure USB delivery, SRAM contents, FPGA checksum acceptance or display signals.

## 3. The STAT packet sequence matches the JTAG procedure

Upstream release v1.1.0 resolves to commit
`a33b53873be7bc8f28c0ac73bd3c88c88b27aa91`. The source-extracted `dumpRegister`
method writes five CFG_IN words:

```text
AA995566 20000000 2800E001 20000000 20000000
```

It selects CFG_OUT, shifts 32 response bits and resets the TAP. The configuration
words and port sequence agree with AMD UG470's JTAG STAT procedure, Table 6-5.
That procedure ends with TAP reset and does not mandate DESYNC. The explicit
DESYNC in Table 6-1 belongs to the SelectMAP procedure; applying that requirement
to this JTAG query would be incorrect. [AMD configuration guide](https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content),
[version-pinned query source](https://github.com/trabucayre/openFPGALoader/blob/a33b53873be7bc8f28c0ac73bd3c88c88b27aa91/src/xilinx.cpp).

`trace_query_02.py` compiles the actual extracted method with an offline recorder.
Three supplied STAT values (`0x401079fc`, `0x40000018`, zero) round-trip unchanged.
Wrong-header and wrong-decode controls are rejected. Exact installed-binary
disassembly corroborates the five writes, read instruction, reversal and TAP
reset. The mocked recorder assumes the driver's serial bit convention and does
not model USB, firmware, electrical timing or FPGA state.

The original fixture incorrectly expected the dummy CFG_OUT input to be a NOP.
The actual bytes `{0,0,0,4}` serialize as `0x00000020` on that read scan and are
not a CFG_IN packet. Execution HALTed on this fixture error; the failed helper,
binary and logs remain intact with `fixture_halt_01.json`. The corrected fixture
changes this expectation only, retains all five write expectations and labels
the combined list as shifted words. No CRC algorithm or loader code was changed.

## 4. Transport failures can be discarded by the loader

In v1.1.0, `Jtag::read_write` calls the cable driver's `writeTDI` but ignores its
return code, advances its software TAP state and returns zero. DirtyJTAG has
failure paths returning both positive and negative values. The installed binary
also discards that call's result: call at `0x1e3b39`, state update, then zero in
EAX at `0x1e3b57` and return at `0x1e3b60`.
[Version-pinned JTAG source](https://github.com/trabucayre/openFPGALoader/blob/a33b53873be7bc8f28c0ac73bd3c88c88b27aa91/src/jtag.cpp),
[DirtyJTAG driver](https://github.com/trabucayre/openFPGALoader/blob/a33b53873be7bc8f28c0ac73bd3c88c88b27aa91/src/dirtyJtag.cpp).

`trace_transport.py` compiles the actual extracted wrapper with an injected
driver. Driver results 0, +1 and -1 all become wrapper result 0 with state
advanced. A control that throws on a nonzero driver result is rejected by the
same harness, making the finding falsifiable. Evidence:
`transport_trace_01.json` and `Jtag_read_write.exact.installed.asm`.

This is an established software error-propagation defect. It means command exit
0 alone does not prove successful JTAG transport. The recorded programming and
query stderr are empty, whereas inspected driver error paths print diagnostics.
No recorded USB failure establishes that this defect occurred in our campaign.
It therefore cannot be assigned as the cause of `0x40000018` or the display fault.

A proposed loader correction must propagate failures before advancing state and
ensure upper-level scans abort. TMS flushing returns a bit count on success, so
its error check cannot blindly reuse a nonzero-is-failure test. The offline fault
control is a fixture, not a reviewed or installed loader patch.

## 5. Startup and process boundary

Source and exact function disassembly show the SRAM path uses JPROGRAM, waits
for initialization, streams CFG_IN data, issues JSTART, supplies clocks and then
captures BYPASS IR. The standalone query path does not issue JPROGRAM, RCRC,
ISC_ENABLE, SHUTDOWN or a configuration-reset command. Main dispatch invokes a
configuration reset only when the explicit reset flag is set; the recorded query
had no such flag. DirtyJTAG initialization opens USB and sets its frequency;
the inspected path does not deliberately assert board SRST/TRST. These findings
do not measure effects of USB reopening or actual target state.
[Version-pinned dispatch source](https://github.com/trabucayre/openFPGALoader/blob/a33b53873be7bc8f28c0ac73bd3c88c88b27aa91/src/main.cpp).

Installed ELF SHA-256:
`2956f63e5afbedf0747ec880e3b17c316fef311f4710d6f71bc23abea7821ed9`.
`binary_ranges_01.json` and `transport_binary_ranges_01.json` bind inspected
symbols, exact ranges and assembly hashes to that binary. Agreement of these
inspected behaviors is not a reproducible-build identity claim for all upstream
and installed code.

## 6. Interpretation and next diagnostic

No CRC coverage error, query packet error, demonstrated byte-order error or
JTAG DESYNC omission defect was found. The discarded transport return code is
real, but its involvement is unmeasured. A valid low STAT value, invalid sampling,
USB/firmware behavior and a target-state change remain unresolved possibilities.
The audit does not establish wiring, monitor, FPGA or RTL correctness.

A useful next proposal would bracket one STAT read with captured IR status in a
single process, checking transport results and preserving raw TDO. That would
help distinguish a process-reopen effect, query-associated change and sampling
failure. Its exact transport implementation, side effects, duration and attempt
budget require a separate reviewed contract before any hardware execution.
This report authorizes no query, retry, reset, reload or observation.

Repository PASS remains confined to the previous frozen verification snapshot.
These new audit scripts and reports were not included in its gates. This is an
offline diagnostic result, with engineering/display closeout still unresolved.
