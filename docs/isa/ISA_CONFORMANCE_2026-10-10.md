# Canonical ISA scoped conformance

Date: 2026-10-10. Scope: current dirty working tree, canonical ISA-A assembler,
Python VM, C++ VM and active core dispatch. No WF/SPI/GPU encoding migration.
Contract: [scoped repair](../../spu_strategy/contract_isa_conformance_2026-10-10.md).
Status: scoped qualification COMPLETE; all listed gates exited 0. The immutable
preparation snapshot and review bundle retain the earlier pending wording.
No new board observation or integrated timing result is claimed.

## Evidence vocabulary

- **Matching:** agreement within the stated subset; source agreement alone is
  not executable qualification.
- **Conflicting:** different encodings or observable semantics.
- **Unsupported:** outside the named implementation's capability subset.
- **Unverified:** semantics, domain or evidence do not establish agreement.

Authority: [ISA](../../knowledge/isa_reference.md).
Surfaces: [assembler](../../software/tools/spu13_asm.py),
[Python](../../software/spu_vm.py), [C++](../../software/vm/spu_vm.cpp),
[core](../../hardware/rtl/core/spu13/spu13_core.v).

## Explicit capabilities

| Surface | Supported encoding/execution subset | Restrictions |
|---|---|---|
| Standalone assembler | LD/ADD/SUB/MUL/ROT/LOG; JMP/SNAP/HALT/REGEN/CALL/RET/NOP; QADD/QROT/QNORM/QLOAD/QLOG/QSUB/ROTC/QLDI/DELTA/MIN4/QREAD; SPREAD/HEX; EQUIL/IDNT/JINV/ANNE; IROTC/LOAD2X/SCALE2; SLI/SLD/SRD/SMUL/SADD/SSUB/SNORM/SSTAT | Emission does not imply target execution. PHADD/PHCFG, SOM/SOM_TRAIN and polynomial source emission absent. |
| Python VM | Canonical scalar/control/QR/geometry/Janus families; REGEN; IROTC/LOAD2X/SCALE2; PHADD/PHCFG; SOM/SOM_TRAIN; RATIO_CMP; simulation POLY_STEP at E0 | Surd unsupported. Inline QLDI also accepts historical packed halves. Legacy polynomial allocation remains conflicting. |
| C++ VM | LD/ADD/SUB/MUL/ROT/LOG; JMP/SNAP/HALT/CALL/RET/NOP; QADD/QROT/QNORM/QLOAD/QLOG/QSUB/ROTC/QLDI/DELTA/QREAD; SPREAD/HEX; EQUIL/IDNT/JINV/ANNE | ROTC angles 0..5 only. int32 coefficients, unchecked arithmetic limits. No MIN4/REGEN/IROTC/phinary/SOM/polynomial/Surd support. |
| Core dispatch | QLDI/DELTA/QSUB; ROTC with ENABLE_MATH; HEX telemetry; REGEN; IROTC/LOAD2X/SCALE2 with ENABLE_IROTC; SOM/SOM_TRAIN with appropriate feature selection; Surd with ENABLE_SURD_CPU | No scalar R-file execution or JMP/CALL/RET/HALT/SNAP implementation established. Unsupported words can be acknowledged. Math-disabled ROTC can hang. Optional sequencer is sequential ROM playback. |

Core sidecar hooks E0,48,4C,4D and configurable RPLU2 result paths have separate
interfaces. They do not establish the similarly named scalar instruction's
semantics. Source support and raw execution support are separate capabilities.

## Findings and disposition

| Item | Classification after scoped repair | Evidence / limitation |
|---|---|---|
| 8/8/8/16/16 fields and low reserved byte | Matching for ordinary emitted words | Literal fixtures compare all C++ mnemonics against both Python assemblers. Ordinary reserved-bit rejection remains unspecified. |
| CALL=20,RET=21,QREAD=22; COND unallocated | Matching software | Existing nested-control tests retained. No core stack support added. |
| Standalone QREAD/MIN4 omitted operands | Matching after repair | QREAD QR2,QR1 now emits 2202010000000000; MIN4 QR12 emits 1f0c000000000000. |
| Third ADD/SUB/MUL operands | Matching rejection after repair | Canonical in-place two-operand form required before folding; no third-source encoding invented. The two Pell demo copies were migrated using their declared initial constants and their intended arithmetic outputs are tested. |
| Inline four-component QLDI and DELTA steps | Matching after repair | Literal signed-byte and unsigned-halfword fixtures; packed-half inline QLDI retained. |
| HEX/SPREAD second destination folding | Matching after repair within scalar output tests | Invalidate R[d+1] including R25 wrap. Reproducer previously gave 8 without fold,18 with fold; both now give8. |
| ROT folding | Matching preservation after repair | ROT remains an instruction because LD cannot retain Pell step/polarity. Nine-step coefficient and metadata checks. No universal optimizer/VM-cycle equivalence claimed. |
| C++ HALT | Matching after repair | HALT stops before a following LD; no core HALT execution added. |
| Unsupported software source/raw words | Matching rejection policy for tested subset | Explicit errors replace silent source omission/raw NOP for unsupported VM opcodes. C++ ROTC6 stops without PC/destination commit. |
| Ordinary register invalid indices | Unverified contract | Assemblers mask indices, QR paths wrap, scalar accesses are incompletely guarded. Surd rejects full indices. No global rejection policy introduced. |
| Scalar arithmetic overflow | Conflicting | Python unbounded; C++ int32 with narrowing and possible signed overflow. Bound coefficients and intermediates before claiming parity. |
| ROT/QROT source/exponent semantics | Conflicting | Reference table differs from destination-only one-step VM behavior. Pell representation metadata is not a general exact-field encoding. |
| QLDI/DELTA execution | Matching bounded source structure | Signed-byte components; DELTA endpoint=(Q1+Q2,0,steps-or4,0). New VM fixtures include Q1=65535,Q2=32768. |
| QSUB malformed source field | Conflicting outside legal QR0..12 | RTL preserves low-nibble RHS decoding; VMs use P1_B. This repair preserves compatibility rather than changing malformed-word interpretation. |
| HEX source read | Matching repaired RTL telemetry timing | Alternating distinct lanes, negative result and held-valid retirement checks pass in live-core simulation. |
| HEX destination/order/width | Conflicting explicit subset | VM writes (A-D,B-D) to R[d],R[d+1]. Core emits 16-bit (B-D,A-D) telemetry and ignores Rd. No transport ordering changed. |
| QNORM versus MIN4 | Conflicting outside rational-only values | Python MIN4 minimizes rational coefficients; QNORM compares full surds. |
| SPREAD/JINV reference operands | Conflicting | VM SPREAD takes two QR vectors and writes numerator/denominator to R pair; JINV conjugates R, not QR. Freeze canonical intent before changing behavior. |
| ROTC thirds | Conflicting | VM rounding differs from active TDM truncation; exact parity requires divisible input or a reviewed representation change. Tagged rotor is separate. |
| ROTC range/fault completion | Unsupported C++6..35; conflicting completion | Python raises, RTL faults/completes. Full-byte encoding is masked to six angle bits. |
| IROTC tags and preservation | Matching source structure; boundary parity unverified here | Python/core guards and tags correspond. C++ lacks tag representation; QREAD there is only a basic copy. |
| REGEN eligible set | Matching named membership; execution subset conflicting | Core counts IDNT/QLOG although its active dispatch does not implement their VM effects. E_REGEN membership is not execution support. |
| POLY_STEP allocation | Conflicting | Canonical60 versus effective Python E0 and RTL artery-emission hook. Preserve legacy records; do not translate raw words by opcode alone. |
| FLAGS/SNAP | Conflicting / unsupported core interface | VM checks stability, Python also evaluates SDF; six-bit FLAGS read is not established in core dispatch. |
| Reset/load/completion | Unverified common contract | VM load preserves register/stack state; RTL resets and hydrates different state. Core issuer must serialize operations and wait for retirement. |
| RTL lane modulo | Matching compatibility after repair | Bounded 19-stage compare/subtract replaces byte modulo13; all256 byte inputs tested. QSUB low-nibble input retained. |
| Flash-library CALL addresses | Conflicting | Listed 010000+ addresses exceed the current 16-bit CALL target field; no truncating migration or fetch architecture added. |

## Surd 70..77

All eight operations are unsupported in both VMs and rejected there. The
[encoder](../../software/tools/surd_cpu_encoding.py),
[frontend](../../hardware/rtl/core/spu13/spu13_surd_exec.v),
[loader](../../hardware/rtl/core/spu13/spu13_surd_load.v),
[arithmetic](../../hardware/rtl/core/spu13/spu13_surd_arith.v) and
[normalizer](../../hardware/rtl/math/surd_normalize_unit.v) match the current
extension's source-level contract:

| Opcode | Classification | Required behavior present in source |
|---|---|---|
|70 SLI|Matching|Six u32 slices; full index validation; staged writes only.|
|71 SLD|Matching|Complete target staging and nonzero u64 denominator; atomic commit.|
|72 SRD|Matching|Initialized tuple required; selected32-bit slice read.|
|73 SMUL|Matching|Signed64 coefficients, u64 denominator; wide products, raw fit or exact rescue.|
|74 SADD|Matching|GCD-aligned exact addition and fit/rescue policy.|
|75 SSUB|Matching|GCD-aligned exact subtraction and fit/rescue policy.|
|76 SNORM|Matching|Always reduce; valid zero=(0,0,1); exact zero remainders required.|
|77 SSTAT|Matching|Held status read without clear.|

Success-only bank write gating preserves destinations on failure. One operation
is in flight; sources are captured by the arithmetic engine. Ordinary R/QR
state is separate. Source agreement does not establish exhaustive arithmetic,
reset cancellation, staging retry policy or timing. Directed Surd checks passed:
39 preservation checks, 17 alias cases and 6 engine-fault injections. Retained
kernels were not executed; boot/reset are excluded.
Retained qualification limits remain in
[the diagnosis](SURD_QUALIFICATION_DIAGNOSIS.md).

## Verification and remaining decisions

```bash
python3 software/tests/test_isa_conformance.py
python3 software/tests/test_isa_fold_conformance.py
python3 software/tests/test_canonical_control.py
TB_FILTER=spu13_core_hex_conformance python3 run_all_tests.py
```

The repair contract lists full gates and the one-shot detached launch policy.
The detached evidence directory must carry source snapshots/hashes, commands,
individual logs, exit codes and exactly one terminal marker before interpretation.
No commit or board programming is included.

Before broader repairs, freeze overflow/preservation for ordinary arithmetic,
ROTC rounding/representation, ROT/QROT operands, FLAGS/SNAP, invalid indices,
reset versus reload, polynomial allocation and flash target addressing. Core
unsupported-op status and fetch/stack support need a separate reviewed contract.

WF's 5-bit register layout and overlapping opcode numbers remain experimental.
[SPI/GPU transport boundaries](../TRANSPORT_BOUNDARIES.md) remain independent.
Historical board evidence stays in [the ledger](../hardware_evidence.md).

## Completed qualification and independent review

The detached job has exactly one terminal marker, COMPLETE, and exit 0;
duration 2032 seconds. Full repository regression reports 243 passed, 0 failed;
scoped regression reports 75 passed, 0 failed. The Artix-7 Padé build completed
place-and-route and bitstream generation. This is not an ENABLE_SURD_CPU image
qualification or a new board observation. Source identities still matched the
frozen preparation manifest before this documentation-only closure.

- [Detached result](../../build/isa_conformance/qualification_01/result.json)
- [Individual gate commands, logs and exits](../../build/isa_conformance/qualification_01/gates/)
- [Directed Surd results](../../build/isa_conformance/qualification_01/surd/results.json)
- [Frozen source identities](../../build/isa_conformance/preparation_01/source_identity.json)
- [User-supplied independent review disposition](ISA_CONFORMANCE_REVIEW_DISPOSITION_2026-10-10.md)

The document audit exits 0 but reports existing links/claims/status findings;
its exit code is not evidence that all repository documentation is clean.
