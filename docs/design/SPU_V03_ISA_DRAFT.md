# SPU v0.3 ISA draft

**Status: DRAFT (revision 2) — SUPERSEDED for execution semantics** by the [v0.3 contract candidate](SPU_V03_CONTRACT_CANDIDATE.md)
(2026-11-11). Kept as design history: the decisions and reasoning below record how the architecture
developed. Where the two differ (for example, `SRD` is retired and a refused LOAD invalidates the
image), the contract governs. These were candidate instruction forms for review. Nothing here changes the frozen [Gen-1 contract](../GEN1_ARCHITECTURAL_CONTRACT.md), the RTL,
the `gen1-surd` simulator profile or the published v0.2.0 release. It builds on the PROVISIONAL
[v0.3 architecture proposal](SPU_V03_ARCHITECTURE_PROPOSAL.md) (cited below as "the brief").

Revision 2 applies the owner review of 2026-11-11:
- the conditions on D-1 and D-5;
- the state model, with atomic staging and a clean start (§3.1);
- comparison validity (§5.1);
- exact PC and budget rules (§5.3–5.4);
- zero and negative counts in Program B;
- a non-canonical orientation case.

Example traces in §7 were checked by hand with a throwaway model of these rules. That model follows
the RTL's arithmetic (lcm alignment, raw-fit, normalize-to-fit, refuse). This is a paper check, not a
simulator result.

## 1. Design summary

- **Machine:** sequential, multicycle, in-order. One instruction is in flight at a time.
- **Domain:** Q(√3) only.
- **State (§3.1):** eight unified 192-bit Surd registers, S0–S7, with the Gen-1 tuple layout (a, b
  signed 64-bit; d unsigned 64-bit, nonzero), each with an *initialized* bit. There is also a staging
  buffer, a PC, the flags and a status register. There is no data memory.
- **Word format:** the Gen-1 64-bit layout: `[63:56]` Op, `[55:48]` R1, `[47:40]` R2, `[39:24]` P1_A,
  `[23:8]` P1_B, `[7:0]` = 0.
- **Opcode space:** one block, 0x70–0x7F, in the `programmable-surd` profile only.
  - 0x70–0x77 are the **existing core Surd operations**, which the core already decodes for any
    register.
  - 0x78–0x7F are **new frontend-only** operations.
  - Every other word is a terminal BAD_ENCODING fault.
- **Gen-1 compatibility:** the four accepted Gen-1 words keep their meaning. A Gen-1 program needs an
  appended `HALT` to run as a v0.3 program. Its overflow behaviour differs on purpose (recoverable,
  §6). The `gen1-surd` profile is unchanged.

### 1.1 Encoding acceptance criteria (D-1 conditions)

1. **Full opcode decode.** The frontend decodes the complete 8-bit opcode and every reserved field.
   It never issues 0x78–0x7F to the core. This prevents an alias: the core decodes only `word[58:56]`,
   and bits [58:56] of 0x78 are `000`, so a 0x78 word reaching the core would execute as `SLI`.
2. **Explicit assembler profile.** The assembler requires an explicit target profile (for example
   `--profile programmable-surd`). It never infers the architecture from the mnemonics used.
   Mnemonic tables are per profile, so legacy telemetry names such as MFOLD (0x70) are rejected in
   this profile, and Surd mnemonics are rejected in the legacy profile.
3. **Architecture identity in the image.** Each image carries a profile identifier and version in its
   loading envelope (§8). The loader refuses an image whose identity does not match the machine, so a
   legacy word can never run as a different, valid Surd instruction.
4. **Negative tests.** Before any conformance claim:
   - every opcode outside the accepted set (all 256 opcode values);
   - each malformed field of each accepted form: nonzero reserved bits, register index ≥ 8, slice ≥ 6,
     condition code > 9, and nonzero `[7:0]`.

   Each must give BAD_ENCODING with no state change.

## 2. Instruction forms

`d`, `a`, `b` are register indices 0–7. Every field not listed must be zero, or the word is
BAD_ENCODING. **R** means the instruction updates the refusal flags (§6).

| Op | Form | Encoding (hex nibbles) | Semantics | R |
|---|---|---|---|---|
| 0x70 | `SLI Sd, s, u32` | `70 0d 0s pppppppp 00`, s < 6 | Write slice s of the **staging buffer** for target Sd (§3.1). Sd is not affected | — |
| 0x71 | `SLD Sd` | `71 0d 00 0000000000` | Validate the staging buffer and atomically commit it to Sd (§3.1) | — |
| 0x72 | `SRD Sd, s` | `72 0d 0s 0000000000` | Copy slice s of Sd to the result buffer. **Approved proposed change (2026-11-11): retired in v0.3; 0x72 becomes reserved (BAD_ENCODING) and the result buffer is removed. Implemented in `8ca63ec0` (image revision 0x03)** ([report](SPU_V03_SIM0_DISCREPANCY_REPORT.md) O6) | — |
| 0x73 | `SMUL Sd, Sa, Sb` | `73 0d 0a 00 0b 000000` | Sd ← Sa·Sb (§4) | yes |
| 0x74 | `SADD Sd, Sa, Sb` | `74 0d 0a 00 0b 000000` | Sd ← Sa + Sb (§4) | yes |
| 0x75 | `SSUB Sd, Sa, Sb` | `75 0d 0a 00 0b 000000` | Sd ← Sa − Sb (§4) | yes |
| 0x76 | `SNORM Sd, Sa` | `76 0d 0a 0000000000` | Sd ← Sa divided by gcd(\|a\|,\|b\|,d); zero becomes (0,0,1) | yes |
| 0x77 | `SSTAT` | reserved in this draft (O6) | BAD_ENCODING | — |
| 0x78 | `SLIK Sd, i32` | `78 0d 00 iiiiiiii 00` | Sd ← (sign-extend(i32), 0, 1); does not touch staging | — |
| 0x79 | `STST Sa` | `79 00 0a 0000000000` | Set Z/N/P from the sign of Sa's value; set CV (§5.1) | — |
| 0x7A | `BR cc, t` | `7A cc 00 tttt 0000 00` | Conditional or unconditional branch to the absolute address t (§5.2) | — |
| 0x7B | `HALT` | `7B00000000000000` | Terminate normally (§5.4) | — |
| 0x7C | `SMOV Sd, Sa` | `7C 0d 0a 0000000000` | Sd ← Sa, bit-exact; never refuses (candidate, O5) | — |
| 0x7D–0x7F | reserved | — | BAD_ENCODING | — |

Any instruction that reads an uninitialized register causes a terminal INVALID fault.

## 3. Registers and values

- Integers (k, 0, 1), rationals (b = 0) and surds all share one representation. The same `SADD`,
  `SSUB` and `SMUL` serve all three; there are no type-specific instructions.
- **Q5, the integer form, is not needed by this draft.** Branch targets are immediates, and
  comparisons test the value's sign, so **no instruction consumes a register as an integer**.
  Non-canonical values work by value (§7.1 case F, §7.3). Q5 stays open until an instruction
  consumes a register as an integer.

### 3.1 State model

**Staging is separate from architectural registers.**
- `SLI` writes only the staging buffer: slice data, a `received` bit per slice, and the target
  register.
- The committed value of the target register is unchanged by `SLI` and stays readable. For example,
  after `SLIK S0, 5; SLI S0, 0, 123`, S0 still holds 5 and is still initialized.
- `SLI` naming a different target while staging is non-empty is a terminal INVALID fault (Gen-1
  rule).

**`SLD Sd` commits atomically.**
- It commits only if all six slices were received for target Sd and the staged d ≠ 0.
- Otherwise it is a terminal INVALID fault, and Sd is unchanged.
- The staging buffer is cleared after the check, whether or not the commit succeeds.
- No partial tuple is ever visible.

**Clean start.** A START that follows a successful load resets every piece of execution state before
the first fetch:
- all registers become uninitialized, with value fields at the reset value (a = b = 0, d = 1);
- staging is cleared;
- Z = N = P = 0 and CV = 0;
- R = RS = 0 and status = 0;
- the result buffer is cleared;
- the retired count is 0 and PC = 0.

Nothing carries over from a previous run. Controlled initial values come only from the image itself
or from a future preload mechanism (O7).

## 4. Arithmetic (all inherited core rules)

- **`SMUL`** computes the raw (ac + 3be, ae + bc, df). If it fits, it commits unreduced. Otherwise
  it is normalized by its gcd and committed if that fits. Otherwise OVERFLOW.
- **`SADD`/`SSUB`** first align the two denominators: g = gcd(d, f), u = f/g, v = d/g. The raw result
  is (a·u ± c·v, b·u ± e·v, d·u), with lcm denominator d·u. The same fit → normalize → OVERFLOW
  rules follow.
  - If the alignment step fails, the result is ENGINE_FAULT. That path is unreachable for
    committed operands but is coded (`spu13_surd_arith.v`).
- **Verification status.** These add/subtract semantics are read from the RTL source. They have not
  been verified for v0.3: Gen-1 qualification exercised only `SMUL`. The v0.3 contract must fix them
  and obtain RTL evidence separately (brief §2.2).
- **Latency (Q8).** `SADD`/`SSUB` always run the gcd aligner, even for (k,0,1) + (m,0,1). An integer
  fast path is an optimization. It must produce the **same tuple** as the general path, not just the
  same value. Measure in the simulator before adding hardware.

## 5. Control

### 5.1 `STST Sa` and comparison validity

`STST` sets Z = (value = 0), N = (value < 0), P = (value > 0), exactly one of them, and sets the
internal flag **CV** (comparison valid) to 1.

Because d > 0, the sign of the value is the sign of a + b√3:
- if a and b have the same sign (or one is zero), the sign is read directly;
- otherwise compare a² with 3b².

With |a|, |b| ≤ 2⁶³, both terms are below 2¹²⁸ (3·2¹²⁶ < 2¹²⁸), so an **unsigned 128-bit comparison
is sufficient for n = 3**, and `STST` never refuses. Zero means exactly a = b = 0, since √3 is
irrational; a non-canonical zero such as (0, 0, 60) tests as zero.

**Validity rules:**
- CV = 0 at start (§3.1).
- Z, N, P and CV keep the result of the last `STST` until the next `STST` or the next start.
  **No arithmetic instruction changes them.**
- A sign-conditional branch (EQ, NE, LT, GE, GT, LE) executed while CV = 0 is a terminal INVALID
  fault.
- AL, RF, NR and RS do not depend on CV.

A two-operand `SCMP` is **not proposed** (D-3). Neither workload needs it, and comparing two tuples
directly needs wider intermediates (brief Q7).

### 5.2 `BR cc, t`

The target t is an absolute word address in `[39:24]`. Condition codes are in the R1 field:

| cc | Name | Taken when | Needs CV |
|---|---|---|---|
| 0 | AL | always (an unconditional jump) | no |
| 1 / 2 | EQ / NE | Z / ¬Z | yes |
| 3 / 4 | LT / GE | N / ¬N | yes |
| 5 / 6 | GT / LE | P / ¬P | yes |
| 7 / 8 | RF / NR | the most recent R-marked instruction refused / did not refuse (R); R = 0 before any arithmetic | no |
| 9 | RS | any refusal so far in this run (sticky) | no |
| 10–255 | — | BAD_ENCODING | — |

Each `BR` checks, in this order:
1. BAD_ENCODING;
2. the target: if t ≥ L (the image length), the result is a terminal BAD_TARGET fault, **whether or
   not the branch would be taken**;
3. CV, for sign conditions;
4. the condition itself.

### 5.3 PC and retirement

- The image holds L words, 1 ≤ L ≤ 256, at addresses 0 … L−1.
- The PC is an **unsigned 9-bit** register, so it can hold L = 256 and never wraps.
- Each instruction has a single retirement point. Its architectural effects (register write, flags,
  status, PC update) commit together at retirement, and the retired count then increases by 1.
- A refused arithmetic instruction (§6.1) also retires and counts. A faulting instruction (§6.2) does
  not retire.
- After a non-branch instruction, or a branch that is not taken, PC ← PC + 1. A taken branch sets
  PC ← t.
- If the next PC equals L, the next fetch is a terminal **PC_OVERRUN** fault with PC = L. This
  includes falling through from address 255 to 256.

### 5.4 Termination and the instruction budget

- `HALT` retires (and counts) and ends the run with cause HALT.
- **The budget is mandatory.** The START request carries a budget B with 1 ≤ B ≤ 2³² − 1; B = 0 is
  refused at START.
- Before each fetch, if the retired count equals B, the run ends with cause **BUDGET**. The record
  then holds the state after the last fully retired instruction, with PC at the next, unexecuted
  instruction.
- A program whose `HALT` is exactly the B-th retirement ends with HALT.

## 6. Refusal and status (D-2)

### 6.1 Recoverable: arithmetic OVERFLOW only

When `SMUL`, `SADD` or `SSUB` cannot commit:

1. Sd is unchanged.
2. Status ← OVERFLOW, R ← 1, RS ← 1.
3. The instruction retires, PC ← PC + 1, and execution continues.

**`SNORM` never refuses** (documentation clarification, 2026-11-11; [discrepancy report](SPU_V03_SIM0_DISCREPANCY_REPORT.md) X2). Dividing an initialized tuple by gcd(|a|, |b|, d) cannot increase any magnitude, so the result always fits. `SNORM` is R-marked only in that a successful `SNORM` sets R ← 0 and status ← OK.

**What clears it.**
- Every R-marked instruction rewrites status and R. A successful one sets R ← 0 and status ← OK.
- RS is **sticky** for the run. It is cleared only at start, and no instruction clears it (O9
  deferred).

**What the flags mean.** RS records that a refusal *occurred*, not that the final answer is invalid.
A program may recover, for example by recomputing another way, and finish with a valid result while
RS = 1. The program decides whether it recovered. The result record reports both the terminal cause
and RS, and readers must interpret the program's own output in the light of both.

In Program A, the program itself treats RS = 1 as "refused" (§7.1 case E). That is a choice made by
that program, not an architectural rule.

### 6.2 Terminal faults

The faulting instruction does not retire. Execution stops, and the result record holds the state
before that instruction, with PC at the faulting word. The causes are:

| Cause | Raised by |
|---|---|
| BAD_ENCODING | any word not matching §2 exactly |
| INVALID | an uninitialized operand; `SLD` with incomplete staging or d = 0; `SLI` with a different target while staging is non-empty; a sign branch with CV = 0 |
| ENGINE_FAULT | an internal arithmetic-engine failure |
| BAD_TARGET | `BR` with t ≥ L |
| PC_OVERRUN | a fetch at PC = L |
| BUDGET | retired count = B before a fetch |

## 7. Representative programs

### 7.1 Program A — exact orientation predicate

Inputs: S0..S5 = ax, ay, bx, by, cx, cy. Each input is loaded with `SLIK` (one word, for an integer)
or with 6×`SLI` + `SLD` (seven words, for a general tuple). The output goes to S7: +1 for CCW, −1 for
CW, 0 for collinear, 2 for refused.

```
L+0   SSUB S2, S2, S0      ; bx-ax
L+1   SSUB S4, S4, S0      ; cx-ax
L+2   SSUB S3, S3, S1      ; by-ay
L+3   SSUB S5, S5, S1      ; cy-ay
L+4   SMUL S0, S2, S5
L+5   SMUL S1, S3, S4
L+6   SSUB S0, S0, S1      ; det
L+7   BR   RS, L+17        ; this program treats any refusal as "refused"
L+8   STST S0
L+9   BR   GT, L+13
L+10  BR   LT, L+15
L+11  SLIK S7, 0           ; collinear
L+12  HALT
L+13  SLIK S7, 1           ; CCW
L+14  HALT
L+15  SLIK S7, -1          ; CW
L+16  HALT
L+17  SLIK S7, 2           ; refused
L+18  HALT
```

It needs 19 words after the input load, and at most 7 registers (6 inputs plus S7). With six full
seven-word inputs, the image is 61 words, which fits even a 64-word memory.

| Case | A, B, C (as tuples) | Result det | Classification |
|---|---|---|---|
| A | (0,0), (2, √3), (1, 2√3) | (0, 3, 1) = 3√3 | CCW |
| B | (0,0), (1, √3), (2, 2√3) | (0, 0, 1) | COLLINEAR |
| C | (0,0), (1, 2√3), (2, √3) | (0, −3, 1) | CW |
| D | (0,0), (1, √3), (2, (1 + 2000√3)/1000) | (1, 0, 1000) = 1/1000 | CCW (exact, near-degenerate) |
| E | (0,0), (2⁴⁰, 0), (0, 2⁴⁰) | **SMUL at L+4 refuses** (2⁸⁰) | REFUSED via RS |
| F | A = ((0,0,1), (0,0,5)), B = ((2,0,2), (0,2,2)), C = ((6,0,3), (0,4,2)); the same points as case B in non-canonical form | (0, 0, 60), a non-canonical zero | COLLINEAR |

In case E, S0 keeps its old value after the refusal, and L+6 then computes a valid-looking but
meaningless det. Only the RS check prevents a wrong answer. The true sign exists, but the 64-bit
tuples cannot hold the product; exactness does not mean unlimited range.

Case F shows that arithmetic and `STST` work by value on non-canonical tuples.

### 7.2 Program B — counted Pell loop (count-down form)

The loop handles every K: K < 0 is reported as an invalid count, K = 0 runs no iterations, and
K ≥ 1 runs K iterations or stops at the first overflow.

```
0..6  SLI×6, SLD S1          ; S1 = (2, 1, 1) = 2+√3   (no one-word surd immediate)
7     SLIK S0, 1             ; x = 1
8     SLIK S3, 1             ; one
9     SLIK S4, K             ; remaining count
10    STST S4
11    BR   LT, 22            ; K < 0
12    BR   EQ, 18            ; K = 0: zero iterations
13    SMUL S0, S0, S1        ; loop
14    BR   RF, 20            ; overflow: S0 still holds the last good x
15    SSUB S4, S4, S3
16    STST S4
17    BR   GT, 13
18    SLIK S7, 0             ; completed
19    HALT
20    SLIK S7, 1             ; stopped by overflow
21    HALT
22    SLIK S7, -1            ; invalid (negative) count
23    HALT
```

It is 24 words and uses 5 registers (S0, S1, S3, S4, S7). Each iteration (words 13–17) is 5
instructions.

Paper trace, with x_k = (2 + √3)^k and d = 1:

| K | S7 | S0 |
|---|---|---|
| −1 | −1 | (1, 0, 1) |
| 0 | 0 | (1, 0, 1) |
| 1 | 0 | (2, 1, 1) |
| 2 | 0 | (7, 4, 1) |
| 33 | 0 | x₃₃ = (3743165875258953026, 2161117825702177665, 1) |
| 34, 50 | 1 | x₃₃ (preserved) |

At k = 34 the raw rational coefficient is 13969685227624439047, which is above 2⁶³ − 1.
Normalization cannot help, because gcd(A, B, 1) = 1. Any K ≥ 34 therefore exits through the
overflow path with a correct x₃₃, the recoverable-refusal behaviour that Q4 asks for.

### 7.3 Non-canonical counter (Q5 probe)

Start the counter at (6, 0, 2), which equals 3, and step it with `SADD S2, S2, S3` where S3 = (1, 0, 1).
Alignment gives g = 1, u = 1, v = 2, so the counter runs (8,0,2), (10,0,2), (12,0,2); the values are
4, 5, 6 and d stays at 2. The test `SSUB` of (6,0,2) − (4,0,1) gives (−2, 0, 2) = −1, and `STST`
reports N. Nothing breaks. The only costs are that the tuple is not canonical and the aligner does
extra work.

## 8. Program image, loading and observation

### 8.1 Load-time vs execution-time checks

**The loader checks, before START is allowed:**
- framing;
- length (1 ≤ L ≤ 256);
- the CRC-32 of the image;
- **the architecture identity**: the profile identifier and version, carried in the LOAD-begin
  payload with the expected CRC.

A failure refuses the image and keeps the previous one, as H0 R3 already does.

**The loader does not decode instructions.** Encoding, target, operand and CV checks happen at
execution (§6.2), so the outcome of a malformed word is always a defined runtime fault at a defined
PC.

A future static validator may reject such images earlier, but it must never accept an image that
execution would fault on, nor change the result of one that runs (O10).

### 8.2 Transport

The transport reuses the experimental H0-UART-1B framing: LOAD begin, LOAD word with an address,
START (with budget B), STATUS and RESULT. The changes form a protocol version 2:
- 9-bit addresses;
- an identity field in LOAD begin;
- B in the START payload;
- a RESULT payload longer than the current 24-byte limit.

H0 is engineering experience, not qualified infrastructure. Its reuse needs its own verification.

### 8.3 Result record (D-5)

The result record is written once per run, at termination, in place of the Gen-1 33-byte frame.

| Field | Content |
|---|---|
| Header | magic, version 3, profile identifier |
| Termination | cause (§5.4, §6.2) and PC (16-bit; may be L for PC_OVERRUN) |
| Flags | Z, N, P, CV, R, RS, and the last arithmetic status |
| Counters | retired-instruction count, budget B |
| Registers | initialized mask (8 bits), then S0–S7 as 24 bytes each (a, b, d; little-endian). **An uninitialized register is serialized as 24 zero bytes**; the mask is the only source of validity |
| Integrity | CRC-32 over all preceding bytes |

The record shows the state **after** the last retired instruction:
- For HALT, that is after `HALT` retires, with PC at the `HALT` word.
- For a fault, it is the state before the faulting instruction, with PC at that word.
- For BUDGET, it is after the B-th retirement, with PC at the next word.
- For PC_OVERRUN, it is after the last instruction, with PC = L.

The record is about 210 bytes, about 18 ms at 115,200 baud.

## 9. Decisions (owner dispositions 2026-11-11)

| # | Decision | Disposition | Where |
|---|---|---|---|
| D-1 | 0x70–0x7F are Surd-CPU opcodes in the `programmable-surd` profile; legacy telemetry names stay with the legacy profile | Approved with conditions | §1.1 |
| D-2 | OVERFLOW is the only recoverable status; everything else is terminal | Approved provisionally | §6 |
| D-3 | `STST` only; no `SCMP` | Approved | §5.1 |
| D-4 | Absolute immediate branch targets; no relative or computed jumps | Approved | §5.2 |
| D-5 | Full-state result record at termination | Approved with conditions | §8.3 |

These are provisional design directions. Freezing the ISA is on HOLD.

## 10. Open items

| # | Item |
|---|---|
| O1 | Image size: 256 words proposed. Program A fits in 64 (61 words), so size is not urgent |
| O2 | An `SLIK` variant with a √3 coefficient or a denominator, to avoid 7-word constant loads (add only if programs show a need) |
| O5 | Whether `SMOV` is needed (both programs run without it) |
| O6 | Keep or retire `SRD`/`SSTAT` once the result record exists |
| O7 | Inputs in the image vs a host register-preload command |
| O8 | Whether an `SADD`/`SSUB` integer fast path is worth adding (measure in the simulator first) |
| O9 | An RS-clear instruction: deferred until a program needs it |
| O10 | Optional static image validator (§8.1 constraints) |

O3 (sign branch before `STST`) and O4 (whether the budget is required) were closed in revision 2,
by §5.1 and §5.4.
