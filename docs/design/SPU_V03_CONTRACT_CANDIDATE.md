# SPU v0.3 programmable-surd contract (FROZEN)

**Status: FROZEN — v0.3 ISA (11 November 2026).** This document states the execution semantics of the
`programmable-surd` profile over Q(√3).

> **Freeze record.**
> - **Approved:** by the repository owner on 2026-11-11.
> - **What is frozen:** the semantics of the contract text at `f2104cac`. The freeze commit changed
>   only status wording, this record and §16; no ISA content changed.
> - **Implementation baseline:** `0020a00c`. It implements image revision `0x03` and passes the SIM-0
>   harness, 155/0 inside the gate and 156/0 including Gen-1 80/80.
> - **Gate:** COMPLETE, exit 0, 271 PASS / 0 FAIL (`build/psurd-sim0/prefreeze-gate-01`).
> - **Reviews:** the reconciliation is in §15 and the
>   [discrepancy report](SPU_V03_SIM0_DISCREPANCY_REPORT.md); the external
>   [pre-freeze review](SPU_V03_EXTERNAL_PREFREEZE_REVIEW.md) is filed verbatim with provenance
>   (`0335a65c`).
> - **This is an ISA freeze, not a v0.3 release.** RTL implementation, timing and physical FPGA
>   qualification have not started. No hardware claim follows from this contract.
> - **Changes after freeze.** Any incompatible change needs an explicit architectural revision, with a
>   new image revision in §10, never a silent edit. The file keeps its `_CANDIDATE` name so that
>   existing links stay stable. **For execution semantics it is authoritative
over the [ISA draft](SPU_V03_ISA_DRAFT.md)**, which is kept as design history.

**Sources:**
- the executed SIM-0 behaviour (`60a70357`, gate `98ed4612`);
- the [ISA draft revision 2](SPU_V03_ISA_DRAFT.md);
- the accepted [SIM-0 discrepancy report](SPU_V03_SIM0_DISCREPANCY_REPORT.md).

**Changes from the original SIM-0 behaviour** (all approved 2026-11-11):
- `SRD` is retired (§12.2), marked by image revision `0x03` (§10);
- a refused LOAD invalidates the executable image (§10);
- register storage is not reset at START; only the initialized mask is (§2).

**Implementation status.** The simulator implements revision `0x03`:
- `SRD` retirement since `8ca63ec0`;
- the image-invalidation rule and the session fixtures in the commit after it (§15).

**Evidence by revision.**
- Revision `0x02`, which still accepted `SRD`: the harness and gate runs at `60a70357`/`98ed4612`,
  the 8,000-program fuzz, and the contract checks.
- Revision `0x03`: the runs in `build/psurd-sim0/recon-01` and `recon-gate-01`, and later runs.

> **Boundary.** The frozen [Gen-1 contract](../GEN1_ARCHITECTURAL_CONTRACT.md) and the `gen1-surd`
> profile are unchanged, and nothing here reinterprets v0.2 behaviour. This profile is selected only
> by an explicit `--profile programmable-surd`. The historical 0x70–0x76 telemetry names (Gen-1
> contract D1) belong to the legacy profile and have no meaning here.

## 1. Machine

The machine is sequential, multicycle and in-order: one instruction in flight, no pipeline, no data
memory. It has one fixed domain, Q(√3). A run consists of:

- **LOAD:** a validated image of L words, 1 ≤ L ≤ 256 (§10);
- **START:** with a budget B, 1 ≤ B ≤ 2³² − 1;
- **execution:** until one terminal cause (§8);
- **result record:** one per run (§11).

## 2. Architectural state

| State | Width | Reset at every START |
|---|---|---|
| S0–S7 | 192 bits each: a (signed 64), b (signed 64), d (unsigned 64, nonzero when initialized) | **uninitialized**; stored bits **unspecified** (not reset) |
| Initialized mask | 8 bits | 0 |
| Staging buffer | six 32-bit slices, a 6-bit `received` mask, a 3-bit target | cleared |
| PC | 9 bits unsigned (0 … 256) | 0 |
| Flags Z, N, P, CV, R, RS | 1 bit each | 0 |
| Last arithmetic status | OK (0) or OVERFLOW (2) | OK |
| Retired count | 32 bits | 0 |
| Budget B | 32 bits | from START |

Every register read is guarded by the initialized mask (§4), so stale storage is never observable. The
record serializes an uninitialized register as zeros (§11). An implementation therefore need not reset
the 1,536 register bits, which leaves room for a distributed-RAM register file.

Loader and control state, outside the execution state above:
- **image-valid**, 1 bit: set only by a successful LOAD and cleared by any refused one (§10);
- **busy**, 1 bit: set from an accepted START until the record is produced (§9).

There is no result buffer (§12.2). No state carries over between runs. The image itself is not
execution state.

## 3. Encoding

**Word layout:** `[63:56]` Op, `[55:48]` R1, `[47:40]` R2, `[39:24]` P1_A, `[23:8]` P1_B, `[7:0]`.

A word is accepted only if it matches one row below exactly. **Every other word is BAD_ENCODING**,
including:
- 0x72, 0x77 and 0x7C–0x7F;
- every opcode outside 0x70–0x7B;
- any nonzero bit in a field the row does not use.

The frontend decodes all 8 opcode bits. Frontend-only opcodes (0x78–0x7B) must never reach the core
decoder, which reads only `[58:56]`.

| Op | Mnemonic | Field constraints | Operands |
|---|---|---|---|
| 0x70 | `SLI Sd, s, u32` | R1 < 8; R2 < 6; `[7:0]` = 0 | d = R1, s = R2, payload `[39:8]` |
| 0x71 | `SLD Sd` | R1 < 8; R2 = 0; `[39:0]` = 0 | d = R1 |
| 0x73 / 0x74 / 0x75 | `SMUL` / `SADD` / `SSUB Sd, Sa, Sb` | R1 < 8; R2 < 8; `[39:32]` = 0; `[31:24]` < 8; `[23:0]` = 0 | d = R1, a = R2, b = `[31:24]` |
| 0x76 | `SNORM Sd, Sa` | R1 < 8; R2 < 8; `[39:0]` = 0 | d = R1, a = R2 |
| 0x78 | `SLIK Sd, i32` | R1 < 8; R2 = 0; `[7:0]` = 0 | d = R1, i = `[39:8]` as signed 32-bit |
| 0x79 | `STST Sa` | R1 = 0; R2 < 8; `[39:0]` = 0 | a = R2 |
| 0x7A | `BR cc, t` | R1 ≤ 9; R2 = 0; `[23:0]` = 0 | cc = R1, t = `[39:24]` (16-bit) |
| 0x7B | `HALT` | the whole word equals `7B00000000000000` | — |

## 4. Instruction semantics

Each instruction checks in this order:
1. encoding (§3);
2. operand initialization (INVALID if any source register is uninitialized);
3. the instruction-specific rules below.

A check failure is a terminal fault; the instruction does not retire (§8).

- **`SLI`** writes slice s of the staging buffer and sets `received[s]`.
  - If staging is non-empty and its target is not d, the result is INVALID.
  - Otherwise the target becomes d. Rewriting a slice is allowed.
  - Committed register state is unaffected.
- **`SLD Sd`** commits the staged tuple to Sd atomically and sets Sd initialized, if `received` =
  all six, target = d, and d_staged ≠ 0. Otherwise the result is INVALID and Sd is unchanged.
  Staging is cleared on success. After a terminal fault, staging contents are **unspecified**
  because they cannot be observed.
- **`SMUL`, `SADD`, `SSUB`** follow §5. They are R-marked (§8.1).
- **`SNORM Sd, Sa`** divides Sa by gcd(|a|, |b|, d); a zero becomes (0, 0, 1). It **never refuses**.
  It is R-marked only in that it sets R ← 0 and status ← OK.
- **`SLIK Sd, i`** sets Sd ← (sign-extend(i), 0, 1) and marks it initialized. Staging is unaffected.
- **`STST Sa`** follows §6.
- **`BR`** and **`HALT`** follow §7.

Operands are read before the destination is written, so any of Sd, Sa and Sb may alias.

## 5. Arithmetic

Operands x = (a, b, d) and y = (c, e, f) each have the value (a + b√3)/d.

**Raw results:**

| Op | Raw (A, B, D) | Exact width needed |
|---|---|---|
| `SMUL` | (ac + 3be, ae + bc, df) | \|A\| ≤ 2¹²⁸ (130-bit signed, as the RTL `raw_a` is); \|B\| ≤ 2¹²⁷; D < 2¹²⁸ |
| `SADD` / `SSUB` | g = gcd(d, f), u = f/g, v = d/g; (a·u ± c·v, b·u ± e·v, d·u) | \|A\|, \|B\| < 2¹²⁸; D < 2¹²⁸ |

**Commit rule** (identical to Gen-1 `SMUL`):
1. If A and B fit in signed 64 bits and 0 < D < 2⁶⁴, commit the raw tuple, unreduced.
2. Otherwise, if A = B = 0, commit (0, 0, 1).
3. Otherwise divide A, B and D by g = gcd(|A|, |B|, D), with exact division. If the result fits,
   commit it.
4. Otherwise the result is OVERFLOW: recoverable (§8.1), with Sd unchanged.

Results are therefore not necessarily canonical.

**Candidate invariant — value-determined refusal.** Whether an operation refuses depends only on the
mathematical values of its operands, not on their tuple representations. The committed tuple, and
whether normalization ran, may depend on the representation.

*Argument.* The raw tuple is an exact representation of the result. Its gcd reduction is the unique
primitive representation with a positive denominator. A refusal happens exactly when that primitive
tuple does not fit, because if the raw tuple fits then so does the primitive one.

*Evidence:* 152,463 representation combinations across 2,000 operand pairs and the three operations,
0 violations. The simulator refusal flag was identical across representations in 436 runs
(`build/psurd-sim0/contract-checks-01`). This should become a formal-verification target.

**Integer invariant.** If both operands have d = 1, a successful result also has d = 1, and a refusal
leaves the destination unchanged. Canonical integers therefore stay canonical under `SADD`, `SSUB`
and `SMUL`. This makes a d = 1 fast path possible (O8); any fast path must commit the **same tuple**.

## 6. Sign test and comparison validity

`STST Sa` sets exactly one of Z, N, P from the sign of a + b√3 (d > 0), and sets CV ← 1:
- if a and b have the same sign (or one is zero), the sign is read directly;
- otherwise the larger of a² and 3b² decides. Both are below 2¹²⁸, so an unsigned 128-bit comparison
  is sufficient.

Zero means exactly a = b = 0, so a non-canonical zero such as (0, 0, 60) tests as zero. `STST` never
refuses.

Z, N, P and CV keep their values until the next `STST` or START; no other instruction changes them.

There is no two-operand compare. `SSUB` followed by `STST` can refuse even when both inputs are
representable. A general comparator would need roughly 260-bit intermediates (cross-products of the
denominators, then squaring); it stays deferred.

## 7. Control flow, retirement and termination

**`BR cc, t`** checks, in order:
1. encoding;
2. if t ≥ L, **BAD_TARGET**, whether or not the branch would be taken;
3. if cc ∈ {EQ, NE, LT, GE, GT, LE} and CV = 0, **INVALID**;
4. the condition.

Taken: PC ← t; not taken: PC ← PC + 1.

| cc | 0 AL | 1 EQ | 2 NE | 3 LT | 4 GE | 5 GT | 6 LE | 7 RF | 8 NR | 9 RS |
|---|---|---|---|---|---|---|---|---|---|---|
| taken when | always | Z | ¬Z | N | ¬N | P | ¬P | R | ¬R | RS |

**Retirement.** An instruction's effects commit together, and the retired count then increases by 1.
A refused arithmetic instruction retires; a faulting instruction does not.

**Step sequence** (owner decision; BUDGET precedes PC_OVERRUN):
1. Before each fetch, if retired = B, the run ends with **BUDGET**.
2. Then, if PC = L, the run ends with **PC_OVERRUN**. A PC of 256 does not wrap.
3. Fetch, check and execute. A fault ends the run (§8.2).
4. `HALT` retires and ends the run with **HALT**, even when it is the B-th retirement.

**Terminal PC.** The PC identifies the instruction at the point where execution can no longer proceed:

| Cause | PC | Retired count |
|---|---|---|
| HALT | the `HALT` word | includes the `HALT` |
| BAD_ENCODING, INVALID, ENGINE_FAULT | the faulting word | excludes it |
| BAD_TARGET | the `BR` word | excludes it |
| BUDGET | the next, unexecuted word; this **may equal L** when the budget runs out on the last word, since BUDGET precedes PC_OVERRUN | = B |
| PC_OVERRUN | L | all executed |

## 8. Refusal and faults

### 8.1 Recoverable refusal

Only OVERFLOW from `SMUL`, `SADD` or `SSUB` is recoverable:
- Sd is unchanged;
- status ← OVERFLOW, R ← 1, RS ← 1;
- the instruction retires, and execution continues at PC + 1.

Every R-marked instruction rewrites R and the status. RS is cleared only at START, and no
instruction clears it.

**What RS means.** RS = 1 records that a refusal occurred during the run. It does not certify that
the program's output is invalid: a program may recover. The program decides, and the record reports
both its output and RS.

### 8.2 Terminal faults

| Cause (code) | Raised by |
|---|---|
| BAD_ENCODING (1) | §3 |
| INVALID (2) | an uninitialized source register; `SLD` rule failure; `SLI` naming a different target; a sign branch with CV = 0 |
| ENGINE_FAULT (3) | internal arithmetic-engine failure. **Unreachable in the exact software model and untested.** Reserved for RTL; fault injection is deferred |
| BAD_TARGET (4) | `BR` with t ≥ L |
| PC_OVERRUN (5), BUDGET (6) | §7 |

HALT is cause code 0.

## 9. START

START is accepted only when image-valid = 1, busy = 0 and 1 ≤ B ≤ 2³² − 1. Otherwise it is refused
and no run happens. An accepted START sets busy, performs the §2 reset, and begins at PC 0. Busy
clears when the record is produced.

**LOAD or START while busy is refused with a BUSY response.** It has no effect on the running program,
the loaded image or image-valid; it is not a load attempt in the §10 sense. There is no preemption and
no abort in v0.3.

**Latency is data-dependent:** the gcd steps vary with the operand values. The budget counts retired
instructions, not cycles, and the ISA makes no timing guarantee.

A run's result is unaffected by **when** it was started (repeated START on one image gives identical
records). In SIM-0, runs are synchronous, so BUSY cannot arise; it is an RTL-0 requirement.

## 10. Loading — SPUI envelope (provisional format)

The file size is exactly 12 + 8L bytes. Checks run in the order shown. Instruction words are **not**
decoded at load time.

**Image validity (owner decision 2026-11-11, replacing "keep the previous image"):**

| Event | image-valid |
|---|---|
| Successful LOAD | 1 |
| Refused LOAD, for any reason: framing, identity or revision, length, CRC | **0** |
| START while image-valid = 0 | refused; no run, no record |
| Later successful LOAD | 1 |

A refused LOAD therefore can never leave an older image runnable. That rules out the sequence "load
A, load B fails, START runs A". The old bytes may remain in memory, but they are not executable;
hardware can clear one bit instead of erasing memory.

**Transport rule for hardware.**
- A LOAD attempt clears image-valid when it **begins**, so an interrupted or partial transfer leaves
  no runnable image.
- The loader must **count the received words** and require exactly L before the CRC check.

In SIM-0, the session mode (`--do load:… / --do start`) implements and tests this rule.

| Offset | Size | Field | Rule |
|---|---|---|---|
| 0 | 4 | magic | `53 50 55 49` ("SPUI"); a size below 12 also counts as bad framing |
| 4 | 1 | profile | `0x01` = programmable-surd |
| 5 | 1 | contract revision | `0x03` only. `0x02` is the historical SIM-0 revision, in which 0x72 was `SRD`; it is refused at load rather than run with changed semantics |
| 6 | 2 | L, u16 little-endian | 1 … 256, and the file size = 12 + 8L |
| 8 | 4 | CRC-32, u32 little-endian | over bytes 12 … 12+8L−1 only |
| 12 | 8L | words | 64-bit **big-endian**, no padding |

**CRC-32/ISO-HDLC** (`zlib.crc32`): reflected polynomial 0xEDB88320, initial value 0xFFFFFFFF, final
XOR 0xFFFFFFFF.

The format distinguishes three things:
- **integrity**: the CRC covers the instruction words;
- **header validation**: every header byte is fixed or cross-checked;
- **authentication**: none. The format is not a security boundary.

Coverage should be reconsidered if mutable header metadata is ever added.

**Load rejection is not an execution result.** A refused image, or a refused START, produces **no**
result record, because §11 records only runs. The host must receive a distinct load or START
refusal: in SIM-0, exit status 1 with a diagnostic on stderr and nothing on stdout. For hardware,
this acknowledgement belongs to the RTL-0 transport protocol, which must never report it as an
execution fault.

## 11. Observation — result record (213 bytes, provisional format)

The record is produced once per run, after termination, and holds the state described in §7. All
multi-byte fields are little-endian.

| Offset | Size | Field |
|---|---|---|
| 0 | 1 | `0xA5` |
| 1 | 1 | record version `0x03`. Numbered independently of the image revision (§10); the two are both 3 by coincidence |
| 2 | 1 | profile `0x01` |
| 3 | 1 | cause code (§8.2; 0 = HALT) |
| 4 | 2 | PC |
| 6 | 1 | flags: bit 0 Z, 1 N, 2 P, 3 CV, 4 R, 5 RS; bits 6–7 = 0 |
| 7 | 1 | last arithmetic status (0 or 2) |
| 8 | 4 | retired count |
| 12 | 4 | budget B |
| 16 | 1 | initialized mask |
| 17 | 192 | S0 … S7: a (i64), b (i64), d (u64) per register. An uninitialized register is 24 zero bytes |
| 209 | 4 | CRC-32 over bytes 0 … 208 |

A reader should reject a record with cause > 6, status ∉ {0, 2}, or flags bits 6–7 set.

## 12. Compatibility with Gen-1

### 12.1 Profile separation

`gen1-surd` is the frozen v0.2 machine: fixed 16-word ROM, S0 only, an implicit halt at PC 14, any
nonzero status faults, and a 33-byte UART frame. It keeps `SRD`. Compatibility is guaranteed by that
profile, **not** by running Gen-1 program images on this one.

### 12.2 Deliberate differences in programmable-surd

| Area | Gen-1 | programmable-surd |
|---|---|---|
| `SRD` 0x72 | accepted | **retired** (BAD_ENCODING); implemented since `8ca63ec0` |
| OVERFLOW | terminal fault | recoverable (§8.1) |
| Termination | implicit, at PC 14 | explicit `HALT`, BUDGET or a fault |
| Program | ROM in the bitstream | SPUI image loaded at run time |
| Output | 33-byte frame | 213-byte full-state record |

`SLI`, `SLD` and `SMUL` keep their Gen-1 meaning, generalized to any register.

**Status and cause numbering differ between the profiles.**

| Condition | Gen-1 status code (internal, never transmitted) | programmable-surd |
|---|---|---|
| OK | 0 | status 0 |
| OVERFLOW | 2 (a terminal fault) | status 2 (recoverable) |
| INVALID | 1 | cause 2 |
| ENGINE_FAULT | 3 | cause 3 |
| BAD_ENCODING | 4 | cause 1 |

Translate by name, never by number.

## 13. Workloads: liveness and precision

| Program | Words | Live registers | Representability |
|---|---|---|---|
| A, orientation (draft §7.1) | 61 (with six 7-word inputs) | 7 | Never refuses for integer coordinates \|x\| < 2³⁰, or for Q(√3) coordinates with \|a\|, \|b\| < 2²⁹ and d = 1 |
| B, Pell count-down (draft §7.2) | 24 | 5 | First refusal at k = 34; x₃₃ is preserved |

**Orientation bounds.** These are derived sufficient conditions, not tight limits.
- Differences need m + 1 bits; products 2m + 2 (2m + 4 with the 3be term); the determinant one more
  bit.
- An extremes enumeration found 0 refusals inside the bounds, and 92 of 729 (integer) and 11,672 of
  15,625 (Q(√3)) refusing at the tested values above the bounds (\|x\| and \|a\|, \|b\| = 2³¹ − 1).
  The enumeration does not locate the exact threshold.

**In-circle (paper estimate, not checked).** It is degree 4, so integer inputs of about \|x\| < 2¹³
would be needed.

**Rational inputs.** Denominators multiply under alignment, so there is no useful general bound.
Refusal reports the limit.

New workloads should report their precision requirements alongside their liveness.

## 14. Evidence and limitations

**Evidence:**
- SIM-0 harness 128/0;
- integrated gate 271/0 at `98ed4612`;
- differential fuzz: 8,000 programs, 0 C++/oracle mismatches;
- value-determined refusal and bounds checks (§5, §13);
- 4/4 mutation controls.

All of it is **software only**: no RTL or silicon evidence exists for this profile.

**Limitations:**
- the C++ model and the oracle share an author;
- fuzz coverage is uneven (see the report);
- ENGINE_FAULT is untested;
- there is no `programmable-surd` assembler (D-1 condition 2 is still unmet);
- the image-invalidation rule is tested in software only, and BUSY is untestable in SIM-0; both are
  RTL-0 loader requirements;
- the SPUI and record formats are provisional.

## 15. Reconciliation record

The revision `0x03` reconciliation (`SRD` retired) was **done in `8ca63ec0`**, following the plan below.
The image-invalidation rule and the session, boundary and per-field decoder fixtures were added in the
following commit.

Not carried out: the representation-invariance harness test (item 3, third bullet). It was outside
the approved scope; its evidence remains `build/psurd-sim0/contract-checks-01`.

The plan as approved:


1. `psurd_machine.hpp`:
   - remove the 0x72 case from `well_formed` and `step`, so it falls to BAD_ENCODING;
   - delete the `result` member and its reset.

   It is psurd-only state; `gen1-surd` uses `gen1::Run::result` and is untouched.
   In `psurd_cli.hpp`, accept image revision `0x03` only (§10).
2. `psurd_oracle.py`:
   - drop 0x72 from `fields_ok` and `run`;
   - keep the `SRD` encoder only to build the negative test.
3. `test_psurd_sim0.py`:
   - remove 0x72 from the opcode sweep's valid set;
   - change "malformed SRD slice 6" to a well-formed-SRD → BAD_ENCODING test with no state change;
   - add a representation-invariance test, a small fixed subset of `contract-checks-01`.
4. Manifest: list `SRD (0x72)` as unsupported, and record image revision `0x03`.
   Tests must cover:
   - a `0x02` image is refused;
   - a `0x03` image executes;
   - a well-formed `SRD` gives BAD_ENCODING with no state change.
5. Checks: the SIM-0 harness, Gen-1 conformance 80/80, then the integrated gate (detached).

## 16. Items recorded at freeze (none blocks the frozen semantics)

- §10 and §11 are frozen as the RTL-0 interface, with formats provisional for the transport;
- O8 (fast path) is measured after RTL-0 and does not block the freeze;
- the register count (8/16/32) is decided by synthesis comparison after RTL-0 and does not block the
  freeze;
- the host-visible load and START refusal acknowledgement for the RTL-0 transport, including BUSY
  (§9, §10);
- per-field decoder fixtures, carried into the RTL-0 verification plan (they exist in the SIM-0
  harness).

Decided 2026-11-11: image revision `0x03` (§10).
