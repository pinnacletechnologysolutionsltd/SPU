# SPU-13 Soft v1 SIM-0 review

**Status:** OWNER ACCEPTED — SIM-0 profile; SIM-1 contract preparation only
**Profile:** `spu13-soft-v1`
**Specification version:** 1
**Review date:** 2026-10-15
**Contract:** [SIM-0 engineering contract](../../spu_strategy/contract_spu_sim_sim0_2026-10-15.md)
**Vectors:** [machine-readable SIM-0 vectors](../../fixtures/spu13_soft_v1_sim0_vectors.json)

This review chooses a deliberately small software profile from canonical
ISA-A. It defines a deterministic integer machine with scalar Q(√3) values and
Quadray tuples. It has no flags, data memory, or memory-mapped devices. The
T1d renderer is an independent optional capability with its own input and
output contract. These choices do not change canonical ISA-A or claim that
current RTL executes this subset.

## 1. Authority and source provenance

The canonical encoding authority is [`knowledge/isa_reference.md`](../../knowledge/isa_reference.md).
The implementation comparison is [`ISA_CONFORMANCE_2026-10-10.md`](ISA_CONFORMANCE_2026-10-10.md),
the current C++ candidate is [`software/vm/spu_vm.cpp`](../../software/vm/spu_vm.cpp),
and the GPU packet/profile sources are listed in §8.

Review source identity is bound to repository commit
`4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f` plus this dirty working tree. The
following SHA-256 values were read from the working tree on 2026-10-15. They
are provenance for this draft, not a claim that the source is qualified:

| Source | Working-tree SHA-256 | State at review |
|---|---|---|
| `knowledge/isa_reference.md` | `e548d4d7cda683e1c260516ae48c9f090f0aa7c30f14a8f99ceb62bac0e81c90` | Dirty working-tree content; canonical encoding reference |
| `software/vm/spu_vm.cpp` | `3fbd72bb6347227a108a6caf030dfc8b201c2f7126c77b9bad413a4658d97854` | Modified before this review; partial candidate |
| `software/spu_gpu_eval/device_packet.py` | `cd58f46c68625b473a224d5454e1fdae34600d86cf9426af227d52b077f4d2d1` | Untracked before this review |
| `software/spu_gpu_eval/device_arithmetic.py` | `7ba8856eafab7687219735f0ca8f37490736e0b3b70a0b146df06a5e809336de` | Untracked before this review |
| `software/spu_gpu_eval/device_model.py` | `cc507652fabc257a7baf36ceac905de5fc4a97e7d61871d4d3e57b25f9d059d6` | Untracked before this review |
| `software/lib/gpu_raster_oracle.py` | `0c3d566cf755d7196161e44192bb178d07f290f8df2391db8b7385825f8d5e2b` | Existing direct edge-evaluation oracle |
| `software/lib/gpu_depth_v2_oracle.py` | `963416ea67a13c59c3edb403f6176d8640ca6dec0dc790fb868b64b7a6e5ffe3` | Existing depth interpolation oracle and convention reference |
| `fixtures/gpu_t1d_scene_wire_64b.bin` | `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` | Existing fixture |
| `fixtures/gpu_t1d_scene_reference.json` | `7c48bdeffac97bba871e5c92663168900cb617f8586976e66f09077e11b7f138` | Existing diagnostic reference |

The ISA-reference hash identifies dirty working-tree content, not a clean
source revision. `knowledge/isa_reference.md` is modified relative to base
commit `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`. The accepted immutable pin
is the source SHA-256 plus exact diff recorded in
[`SPU13_SOFT_V1_ISA_SOURCE_PIN_2026-10-15.json`](SPU13_SOFT_V1_ISA_SOURCE_PIN_2026-10-15.json)
and its patch artifact. SIM-1 must consume that pin, not later changes to the
main repository. The GPU modules were already untracked at review start and
are not promoted to repository authority by this document.

## 2. Profile identity and architectural state

`spu13-soft-v1` uses canonical ISA-A 64-bit words with these bit fields:

| Bits | Field | Rule |
|---|---|---|
| 63:56 | opcode | Canonical ISA-A opcode |
| 55:48 | R1 | Scalar or Quadray index, as specified per instruction |
| 47:40 | R2 | Scalar or Quadray index, as specified per instruction |
| 39:24 | P1_A | Immediate field A |
| 23:8 | P1_B | Immediate field B |
| 7:0 | reserved | Must be zero |

There are 26 scalar registers `R0..R25`. Each stores `(a,b)` for `a+b√3`,
where `a` and `b` are signed 32-bit integers. There are 13 Quadray registers
`QR0..QR12`; each stores four scalar values in `[A,B,C,D]` order. Every
component has the same signed 32-bit coefficient range. There is no implicit
floating-point conversion, saturation, or wraparound.

The architectural state at an instruction boundary is the scalar bank, QR
bank, 16-bit-addressable PC represented without narrowing in the host, return
stack, and 64-bit retired-instruction counter. If another instruction would
overflow the counter, it faults atomically as `COUNTER_OVERFLOW`. The profile has **no flags
register**, data memory, or memory-mapped device state. Host run status and
diagnostics are not architectural registers. The profile has no Pell tags;
ROT is excluded, so its metadata behavior is not observable or serialized.

All source and destination register fields are validated before access. Scalar
indices outside `0..25` and QR indices outside `0..12` fault; modulo wrapping
is not part of this profile. A raw word with a nonzero reserved field or a
nonzero field marked unused by its instruction faults as `BAD_ENCODING`.
At execution, opcode support is checked first: a non-admitted opcode faults as
`UNSUPPORTED`; for an admitted opcode, validate reserved/unused fields before
checking register indices, then execute.

## 3. Instruction matrix

The profile admits only the instructions below. All unspecified bits in an
admitted instruction must be zero. Arithmetic that produces a coefficient
outside signed32 faults as `OVERFLOW`.

| Opcode | Instruction | Encoding and state transition | Faults / provenance |
|---|---|---|---|
| `00` | `LD Rd, a, b` | `R[d] ← (sext16(P1_A), sext16(P1_B))`; `R2=0`. | Invalid `Rd`, malformed unused fields. C++ `case 00`; canonical ISA reference. |
| `01` | `ADD Rd, Rs` | `R[d] ← R[d]+R[s]`; in place; `P1_A=P1_B=0`. | Invalid index or signed32 overflow. C++ `case 01`; canonical ISA reference. |
| `02` | `SUB Rd, Rs` | `R[d] ← R[d]-R[s]`; in place; `P1_A=P1_B=0`. | Invalid index or signed32 overflow. C++ `case 02`; canonical ISA reference. |
| `03` | `MUL Rd, Rs` | Exact `(a+b√3)(c+d√3)=(ac+3bd)+(ad+bc)√3`; in place; immediate fields zero. | Invalid index or signed32 overflow after signed128 intermediates. C++ `case 03`; canonical ISA reference. |
| `06` | `JMP target` | `PC ← target`, where target is unsigned `P1_A`; all other fields zero. | Target must be within the loaded image. Invalid target faults before commit. C++ `case 06`; canonical ISA reference. |
| `08` | `HALT` | Retire once, set `PC←PC+1`, stop normally; all operand fields zero. | None. C++ `case 08`; canonical ISA reference. |
| `10` | `QADD QRd, QRs` | Componentwise exact addition into QRd; immediate fields zero. | Invalid QR index or signed32 overflow. C++ `case 10`; canonical ISA reference. |
| `12` | `QNORM QRd` | Find the exact least of A/B/C/D in Q(√3), subtract it from all four components; `R2=P1_A=P1_B=0`. | Invalid QR index or signed32 overflow during subtraction. C++ `case 12`; canonical reference calls the related operation MIN4. SIM profile explicitly adopts exact ordered-Surd minimum. |
| `1B` | `QSUB QRd, QRa, QRb` | `QR[d] ← QR[a]-QR[b]`; QRb is `P1_B[15:8]`; all other immediate bits zero. | Invalid QR index or signed32 overflow. C++ `case 1B`; canonical ISA reference. |
| `1D` | `QLDI QRd, A, B, C, D` | Sign-extend the four ordered bytes from P1_A/P1_B and load integer coefficients `(A,0)..(D,0)`; `R2=0`. | Invalid QR index. C++ `case 1D`; canonical ISA reference. |
| `20` | `CALL target` | Push `PC+1`, then `PC←target`; target is unsigned P1_A; other fields zero. | Invalid target or stack capacity faults before any commit. C++ `case 20`; canonical ISA reference. |
| `21` | `RET` | If stack is nonempty, pop and jump to top. Empty-stack RET retires once, sets `PC←PC+1`, and stops normally. All operand fields zero. | None. C++ `case 21`; canonical ISA reference. |
| `22` | `QREAD QRd, QRs` | Copy all four components from QRs to QRd; immediate fields zero. | Invalid QR index. C++ `case 22`; canonical ISA reference. |
| `FF` | `NOP` | Retire once, `PC←PC+1`; all operand fields zero. | None. C++ `case FF`; canonical ISA reference. |

For scalar arithmetic, `Rd==Rs` is legal and means the specified in-place
operation. For QADD, QSUB, QNORM, and QREAD, all source/destination aliases are
legal and the full right-hand side is read before the destination commits.
`QNORM` uses exact Q(√3) ordering, including values with nonzero `b`; it is not
integer-only MIN4.

### Explicit exclusions

The following canonical words are rejected as `UNSUPPORTED` and make no
architectural commit: `ROT(04)`, `LOG(05)`, `SNAP(07)`, `REGEN(09)`,
`QROT(11)`, `QLOAD(13)`, `QLOG(14)`, `SPREAD(15)`, `HEX(16)`, `EQUIL(17)`,
`IDNT(18)`, `JINV(19)`, `ANNE(1A)`, `ROTC(1C)`, `DELTA(1E)`, `MIN4(1F)`,
`PHADD(30)`, `PHCFG(31)`, `POLY_STEP(60)`, `RATIO_CMP(61)`, `SOM(2A)`,
`SOM_TRAIN(2B)`, `IROTC(D6)`, `LOAD2X(D7)`, `SCALE2(D8)`, Surd `70..77`, and
all unassigned opcodes.

This resolves the C++/Python/RTL gaps by exclusion for v1. The choice makes no
claim about whether those operations should be included in a later profile.
The reasons include hidden Pell/QR tags, divergent rounding or selector
domains, Python-only recovery state, uncertain operand intent, C++ absence, or
hardware execution gaps. Future inclusion requires a new accepted profile
revision or a new profile name; it cannot silently widen `spu13-soft-v1`.

## 4. Control, loading, errors, and atomicity

The instruction stream is immutable code. There is no data-memory address
space, load/store operation, UART, SPI, timer, or memory-mapped device in v1.
`LOG` and `QLOG` are excluded so host console output is not part of machine
semantics.

Sequential execution reaching `PC == word_count` is normal completion. JMP
and CALL targets must satisfy `0 <= target < word_count`; invalid targets
produce `FETCH_RANGE`. CALL pushes the next sequential PC. The return stack is
bounded to 65,535 entries; overflow produces `STACK_OVERFLOW`. The retired
counter increments exactly once after each successfully executed instruction,
including HALT, empty-stack RET, and NOP. An execution budget is a host runner
limit: budget stop is reported separately and leaves the state after the last
retired instruction available for inspection.

The v1 image is a strict byte container:

| Offset | Width | Encoding |
|---|---:|---|
| 0 | 8 bytes | ASCII `SPUSIM` followed by CR LF (`53 50 55 53 49 4D 0D 0A`) |
| 8 | 2 bytes | Version `1`, unsigned big-endian |
| 10 | 2 bytes | Profile ID `1` for `spu13-soft-v1`, unsigned big-endian |
| 12 | 4 bytes | Word count `1..65,535`, unsigned big-endian |
| 16 | `8 × count` bytes | 64-bit instruction words, big-endian |

The loader validates only the container: magic, version, profile ID, word
count, and exact file length `16 + 8 × word_count`. Truncation, trailing bytes,
unknown version/profile IDs, and zero or excessive count reject the image
before changing machine state. The loader does not decode or prevalidate
instruction words. `BAD_ENCODING` and `UNSUPPORTED` are execution faults raised
only when the affected word is fetched; unreachable invalid or unsupported
words do not prevent loading or execution of other words. This records the
owner review choice to separate container validity from instruction
execution. The loader performs no partial program replacement. The
one-word HALT image is
`53505553494d0d0a00010001000000010800000000000000`.

Cold reset creates the initial state: all scalar/QR coefficients zero, PC and
retired count zero, empty stack, and running status. Loading an image into a
running machine is not supported in v1; load replaces the machine with this
cold state only after complete validation. There is no warm program reload.

An execution fault is atomic across the complete architectural state:
destination and source registers, PC, flags, return stack, memory, device state,
and retired count retain their pre-instruction values. The terminal host
result records the error separately. Since v1 has no flags, memory, or devices,
their state sets are empty; the rule still applies to future additions. Load
errors use `BAD_IMAGE` and leave the machine and current image unchanged.
Execution errors are `BAD_ENCODING`, `UNSUPPORTED`, `INVALID_REGISTER`,
`OVERFLOW`, `FETCH_RANGE`, `STACK_OVERFLOW`, and `COUNTER_OVERFLOW`. An
execution error stops the run and does not retire the failing instruction.

## 5. Snapshot and replay

Snapshots are captured only at instruction boundaries. Serialize as UTF-8 JSON
with sorted object keys, no insignificant whitespace, no floating-point
values, and decimal integers. The schema is
`spu13-soft-snapshot-v1`; it contains profile, image SHA-256, PC, retired count,
nonzero scalar values keyed by decimal register index, nonzero QR values keyed
by decimal register index, return stack from bottom to top, run status, and a
nullable error name. Each scalar is `[a,b]`; each QR value is four such pairs
in `[A,B,C,D]` order. Omitted registers are zero. No hidden host metadata is
serialized.

A replay record binds the image SHA-256, profile/specification version, cold
reset, runner budget (if any), and the starting snapshot. There are no external
device inputs in v1. Given equal records, every instruction-boundary snapshot
and terminal result must be byte-identical.

## 6. CPU conformance vectors

The `cpu_vectors` array contains five cases: exact Q(√3) multiplication,
Quadray arithmetic and normalization, CALL/RET state transitions, simple
overflow preservation, and overflow after nontrivial state accumulation. The
last case faults with a nonzero PC and retirement count, a populated return
stack, populated scalar registers, and a populated QR register. It records
literal 64-bit words and expected architectural values instead of deriving
expected values through the C++ assembler or VM. Runtime instruction-validation
vectors separately show that unsupported and malformed words load, then fault
only if fetched. SIM-1 must add vectors for each admitted instruction, each
fault class, every alias shape, image rejection, and control-flow boundaries
before claiming full v1 conformance. For every execution-fault class, capture
the complete architectural state immediately before the instruction and after
the fault, then assert
`S_after_fault == S_before_instruction`. Include destination and source
registers, PC, flags, stack, memory, device state, and retired count in this
comparison. The host error report and terminal run status are outside `S`.

The v1 implementation is conformant only if accepted images execute to the
literal expected state and invalid images/instructions return the specified
error without partial state changes. The current C++ VM is a candidate source,
not evidence of conformance. The Python VM is not treated as an independent
oracle merely because it is a second implementation.

## 7. T1d graphics capability

T1d is a separately queried device capability named
`gpu.scene.t1d.two-triangle-v1`; it is not an ISA instruction or mapped address
range. Its input is exactly 64 bytes: byte zero `A5`; bytes 1..63 contain two
252-bit triangle records packed consecutively, least-significant bit first
within the little-endian payload. Each triangle record contains three signed
`a:16,b:16,c:32` edge equations, RGB nibbles, and three unsigned 16-bit depth
values, in that order. The field widths sum to 252 bits per record.

The frame is 640×480, row-major from `(0,0)`, with samples at integer pixel
coordinates. An edge accepts signed-32 wrapped `a*x+b*y+c >= 0`; all three
edges must accept a triangle. Covered overlapping triangles compare the
finite-width prepared depth values; smaller wins and exact ties choose triangle
0. Background is black. Each RGB nibble expands to RGB8 by multiplication by
17. Output is exactly `640×480×3 = 921,600` bytes in RGB channel order.

Depth setup uses this finite-width profile. For each edge coefficient
`(a,b,c)` and corresponding vertex depth `z`, compute signed coefficient
products using `(abs(coefficient)*z) mod 2^37`, apply the coefficient sign,
and accumulate each of the three sums with signed40 wrap. Sum the three `c`
coefficients with signed34 wrap for denominator `D`. For nonzero `abs(D)`,
normalize to a 16-bit mantissa by shifting its highest set bit to bit 15,
derive `exponent=(31+shift) mod 128`, select ROM index `mantissa[14:7]`, and
read the unsigned16 reciprocal seed from
`hardware/rtl/arch/gpu_reciprocal_lut_q15.mem`. Compute `prod0=(mantissa*y0)
mod 2^33`, `err=(2^32-prod0) mod 2^33`, `prod1=(err*y0) mod 2^49`, and
`y=(prod1 >> 31) mod 2^16`. Scale each signed40 sum by `y`, apply the sign of
the sum and denominator, and wrap to signed56 to obtain `a_z,b_z,c_z`. At a
pixel, evaluate `(c_z+a_z*x+b_z*y)` with signed56 wrap and arithmetic-shift
right by `exponent`; compare the resulting signed56 values. For `D=0`, the
reciprocal tuple is zero and all prepared depth coefficients are zero. Raw
64-byte device packets are decoded by this profile; JSON scene-parser checks
such as nonzero geometry area are not packet-loader validation. A capability
call is stateless: validate exact packet length and start byte, then return the
complete frame. An invalid packet returns an input error and no frame; there
is no scene activation, partial-frame, or retained device state.

For `fixtures/gpu_t1d_scene_wire_64b.bin`, the current Python finite-width
device model produced RGB8 SHA-256
`96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10`.
The input SHA-256 is
`aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee`.
The six required diagnostic pixels are recorded in the vectors file and
cross-check the existing
[`gpu_t1d_scene_reference.json`](../../fixtures/gpu_t1d_scene_reference.json).
The same full-frame hash was independently reproduced with direct integer edge
evaluation and exact rational barycentric depth, without using the
finite-width depth-preparation or pixel-selection functions. For triangle `i`,
at `(x,y)`, evaluate `Fij = aij*x + bij*y + cij`, set
`Ni = Σj(Fij*z_ij)` and `Di = Σj(cij)`, then compare `N0/D0` and `N1/D1` by
cross multiplication; equal depth selects triangle 0. For this fixture,
`D0 = D1 = 257600`, and every edge value across the active rectangle is within
`[-276000,276000]`, so signed32 coverage wrapping does not change the result.
The exact-rational frame and finite-width frame differ at zero of 307,200
pixels. This validates the complete expected frame for this fixture only; it
does not bound depth error or establish agreement for other scenes. Both
calculations use the same decoded edge and depth fields, so this does not
independently validate packet parsing. Neither calculation establishes RTL
timing, synthesis, or physical output.

Freeze this packet as the initial GPU Level 1 conformance target for SIM-1.
The accepted implementation must reproduce the full-frame hash and six
diagnostic pixels recorded in the vectors file. Packet-decoder independence
and other-scene behavior remain later conformance work.

## 8. GPU source inventory and remaining evidence

| Concern | Source | SIM-0 reading |
|---|---|---|
| Packet bytes and fields | `software/spu_gpu_eval/device_packet.py` | Independent decoder; 64-byte packet, 0xA5 prefix, two 252-bit records. |
| Finite-width reciprocal/depth preparation | `software/spu_gpu_eval/device_arithmetic.py` and `hardware/rtl/arch/gpu_reciprocal_lut_q15.mem` | RTL-shaped widths and reciprocal ROM; not exact rational depth. |
| Pixel selection/frame output | `software/spu_gpu_eval/device_model.py` | Settled frame, wrapped edge/depth arithmetic, first-triangle tie. No clock model. |
| Reciprocal seed | `hardware/rtl/arch/gpu_reciprocal_lut_q15.mem`, SHA-256 `a64327c1bc0c8c74a4fb8c849a922a1f8b3d6a6e2e3bb58951d11f2012bb5248` | Frozen 256-entry unsigned16 table used by depth preparation. |
| Diagnostic reference | `fixtures/gpu_t1d_scene_reference.json` | Six selected pixels and high-level rule. |
| Input packet | `fixtures/gpu_t1d_scene_wire_64b.bin` | Binary scene above. |
| Mathematical raster coverage oracle | `software/lib/gpu_raster_oracle.py` | Independent direct edge evaluation for coverage; does not independently implement prepared depth or full RGB framebuffer. |
| Exact framebuffer cross-check | Direct integer edge and rational barycentric computation described in §7 | Full-frame exact RGB8 hash matches the finite-width model for the named fixture; single-scene result. |
| Physical evidence | `docs/hardware_evidence.md` | Must be consulted for each exact image/observation; no new physical claim follows from this review. |

The reciprocal ROM source and arithmetic above define the named profile;
depth approximation error bounds across other scenes remain unmeasured. The
full-frame comparison covers one fixed fixture and does not replace broader
conformance vectors.

## 9. Evidence status and owner decisions

| Claim | Status at this review |
|---|---|
| Canonical ISA-A word layout and opcode ownership | `specified` by the existing reference; its working-tree hash is recorded in §1. |
| Proposed CPU subset semantics | `specified` and owner accepted for `spu13-soft-v1`; no implementation qualification. |
| CPU conformance vectors | `specified` and owner accepted; not run against a clean v1 implementation. |
| Container and snapshot formats | `specified` here; no loader implementation or compatibility history. |
| T1d packet decode and finite-width software frame | `specified` from current working-tree model. |
| Full-frame mathematical agreement for the named fixture | Direct exact-rational recomputation: zero pixel differences. Other scenes remain unverified. |
| RTL cycle behavior and synthesis for this software profile | `unsupported` as a SIM-0 claim; separate future work. |
| ROCK64/AArch64 runtime | `unresolved`; host portability not yet built. |
| Silicon result | `NOT CLAIMED`; this document adds no entry to `docs/hardware_evidence.md`. |

### Owner acceptance record

On 2026-10-15, the owner accepted this bounded software profile and its
specified decisions: fetch-time instruction validation; the container and
loader behavior; no data memory or flags; strict register validation; empty
stack `RET`; the explicit exclusion list; CPU vectors; the named T1d fixture;
and the immutable ISA source pin recorded above. This acceptance approves
SIM-0 and preparation of a separate SIM-1 implementation contract. It does not
authorize simulator implementation, Verilator integration, FPGA builds, or
hardware operation. Other-scene depth bounds and packet decoder independence
remain outside the first GPU target.
