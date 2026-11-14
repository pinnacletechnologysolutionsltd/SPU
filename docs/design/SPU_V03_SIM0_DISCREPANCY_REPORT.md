# SPU v0.3 SIM-0 discrepancy report

**Status: ACCEPTED (owner, 2026-11-11) — focused semantic audit; no simulator change.** This report compares three sources:
- the [ISA draft, revision 2](SPU_V03_ISA_DRAFT.md) (dev/next `1bb76c9b`);
- the committed `programmable-surd` C++ profile (`software/vm/psurd_*.hpp`, `60a70357`/`98ed4612`);
- the independent oracle (`software/tests/psurd_oracle.py`).

It covers the `programmable-surd` profile only. The frozen `gen1-surd` profile and v0.2 behaviour are
outside its scope and unaffected (§4).

## 1. Method and evidence

| Evidence | Result |
|---|---|
| SIM-0 harness (`test_psurd_sim0.py`) | 128/0 standalone; 127/0 with `--skip-gen1` inside the gate |
| Integrated gate at `98ed4612` | COMPLETE, exit 0, 271 PASS / 0 FAIL (`build/psurd-sim0/integrated-gate-01`) |
| **Differential fuzz (new for this audit)** | **8,000 random programs, 0 record mismatches** (`build/psurd-sim0/audit-fuzz-01`) |

**What the fuzz did.** It generated random programs of 1–39 instructions, plus a 56-word preload in
two of the three runs, with random budgets of 1–1000. The instructions were:
- valid forms with random registers, random 64-bit and boundary operands, and random denominators;
- random branch targets, including targets beyond the image;
- single-bit corruptions of valid words.

Each program's full 213-byte record from the simulator was compared with the oracle's.

**Coverage.** Every terminal cause except ENGINE_FAULT occurred. RS = 1 in 427 runs and CV = 1 in
274. Run 1 is dominated by uninitialized-read faults, and the preload runs by BUDGET.

**Limits.** Agreement is not proof of equivalence. The two models are independent in code (the
oracle imports nothing from C++), not in authorship.

**Result: no observable disagreement between the C++ simulator and the oracle was found.** Every
discrepancy below is between the **draft text** and the **two implementations**, or concerns state
that cannot be observed.

## 2. Discrepancy table

| # | Topic | Draft rev 2 | C++ / oracle | Disposition | Remaining uncertainty |
|---|---|---|---|---|---|
| X1 | `SMOV` 0x7C | §2 lists it as a candidate | Both: BAD_ENCODING (`well_formed` default; `fields_ok` → False) | **Owner D:** unsupported; 0x7C reserved. The contract must not list it as supported | None |
| X2 | `SNORM` refusal | §6.1 lists SNORM among ops that may not commit | Both: never refuses (dividing by the gcd cannot grow magnitudes); updates R ← 0 and status OK | **Owner B:** SNORM never overflows; R-marked only in that it clears R. Draft clarified | None |
| X3 | ENGINE_FAULT | §6.2 terminal cause | Code 3 is defined in both and never produced (exact software arithmetic) | **Owner C:** keep the category; software path unreachable; untested until RTL fault injection | Untested by design |
| X4 | Terminal PC | §8.3 gives a per-cause rule | Both match it (checked by harness PC assertions and fuzz) | **Owner E:** the PC identifies the instruction at the point execution can no longer proceed (§3) | None |
| X5 | BUDGET vs PC_OVERRUN in the same step | Silent | Both: budget checked first at the next fetch; `HALT` on the last slot reports HALT | **Owner decision** adopted; boundary tests retained | None |
| X6 | Binary layouts | §8.3 lists fields only; §8.1 has no byte layout | Both implement the layouts in §5 below | **Owner A:** document as implemented (§5); provisional, not a frozen hardware protocol | Review before RTL |
| X7 | `SRD` / result buffer | §2 copies a slice to the result buffer; §3.1 clears it at start | C++ maintains the buffer; the oracle does not. The record has no buffer field, so `SRD`'s only observable effect is its INVALID check on an uninitialized register | **Owner O6: retire `SRD` from v0.3** (0x72 reserved → BAD_ENCODING; result buffer removed). A deliberate design change, not a SIM-0 defect; `gen1-surd` keeps `SRD` | SIM-0 still implements `SRD` until reconciliation |
| X8 | Staging after a failed `SLD` | §3.1: staging cleared whether or not the commit succeeds | Neither clears it on failure; the run ends terminally first | No observable difference. **Owner:** staging contents after a terminal fault are architecturally unspecified (unobservable state is not constrained) | None observable |
| X9 | Image CRC coverage | §8.1: "the CRC-32 of the image" | The CRC covers the **instruction words only**. Header fields (magic, identity, L) are each validated explicitly, and L is cross-checked against file size | **Owner X9: keep the current coverage** for v0.3 (§5.1). Reconsider if mutable header metadata is added | None found: every header byte is either fixed (magic, profile, revision) or cross-checked (L against file size), so header corruption is refused even without CRC coverage |
| X10 | Assembler profile requirement (D-1 condition 2) | §1.1 | No `programmable-surd` assembler exists; tests encode with the oracle's encoder | Not yet applicable. Must be met by any future assembler | — |
| X11 | Refused image keeps the previous one | §8.1 | The SIM-0 CLI loads one image per process; not exercised | Transport/hardware property; verify in RTL-0 | — |
| X12 | Byte order | Not stated | Image words **big-endian** (Gen-1 ROM convention); record and envelope integers **little-endian** | Document (§5); intentional | — |

**No genuine mismatch between the C++ simulator and the oracle was found, so no implementation change
is proposed.** The draft-text corrections needed are X1, X2 and X6/X9/X12 (documentation), plus the
X4/X5 conventions.

## 2a. Owner dispositions (2026-11-11)

- **O6 — retire `SRD` in v0.3.** The full-state record makes slice readback redundant. Opcode 0x72
  becomes reserved, and the v0.3 result buffer is removed from architectural state. `gen1-surd` keeps
  `SRD` unchanged. Compatibility with Gen-1 is provided by that profile, not by interchangeable program
  images. SIM-0 currently accepts `SRD`; reconciliation follows contract review.
- **X9 — keep the image CRC as implemented.** The contract distinguishes three things:
  - *image integrity*: the CRC detects accidental corruption of the instruction words;
  - *header validation*: fixed values and the declared length are checked explicitly;
  - *authentication*: neither of the above establishes that an image came from a trusted source.

  The SPUI format is an experimental loading format, not a security boundary.
- **Principle.** The contract specifies what software can observe and what RTL must guarantee. State
  that cannot be observed (X7 before retirement, X8) is left unspecified rather than constrained.
- **Fuzz evidence** applies to the implementation it ran on: simulator binary built from `98ed4612`
  (sha256 prefix `b8583b1bb8a664e8`).

## 3. Terminal PC convention (owner E, provisional)

The terminal PC identifies the instruction at the point where execution can no longer proceed:

| Cause | PC | Retired count includes |
|---|---|---|
| HALT | address of the `HALT` word | the `HALT` |
| BAD_ENCODING, INVALID, ENGINE_FAULT | address of the faulting word | not the faulting word |
| BAD_TARGET | address of the `BR` | not the `BR` |
| BUDGET | address of the next, unexecuted word (budget checked before PC_OVERRUN) | exactly B instructions |
| PC_OVERRUN | L, the attempted next-fetch address (up to 256; never wraps) | every instruction executed |

## 4. Profile boundary

- `gen1-surd` is unchanged: `gen1_*.hpp` changed only in the diagnostic text (`aa390e83`), and
  Gen-1 conformance is 80/80.
- `programmable-surd` runs only with an explicit `--profile programmable-surd`. There is no default
  and no inference.
- The historical 0x70–0x76 telemetry names (contract D1) remain in `spu13_arch.h`,
  `spu_isa_defines.vh` and the assembler. Neither profile reinterprets v0.2 behaviour.

## 5. Provisional SIM-0 binary layouts (as implemented)

Not a frozen hardware protocol. CRC-32 throughout is CRC-32/ISO-HDLC (`zlib.crc32`): reflected
polynomial 0xEDB88320, initial value 0xFFFFFFFF, final XOR 0xFFFFFFFF. Every CRC field is stored
little-endian.

### 5.1 SPUI image envelope (file size exactly 12 + 8L bytes)

| Offset | Size | Field | Rule (checked in this order; any failure refuses the image, with no record produced) |
|---|---|---|---|
| 0 | 4 | magic | `53 50 55 49` ("SPUI"); a size below 12 also counts as bad framing |
| 4 | 1 | profile id | `0x01` (`programmable-surd`) |
| 5 | 1 | draft revision | `0x02` |
| 6 | 2 | L, u16 LE | 1 ≤ L ≤ 256, and the file size must equal 12 + 8L |
| 8 | 4 | CRC-32, u32 LE | over bytes 12 … 12+8L−1 (the words only; see X9) |
| 12 | 8L | instruction words | L × 64-bit, **big-endian**, no padding |

There are no reserved fields. Instructions are not decoded at load time.

### 5.2 Result record (213 bytes, one per START)

| Offset | Size | Field | Values |
|---|---|---|---|
| 0 | 1 | magic | `0xA5` |
| 1 | 1 | record version | `0x03` |
| 2 | 1 | profile id | `0x01` |
| 3 | 1 | cause | 0 HALT, 1 BAD_ENCODING, 2 INVALID, 3 ENGINE_FAULT, 4 BAD_TARGET, 5 PC_OVERRUN, 6 BUDGET |
| 4 | 2 | PC, u16 LE | per §3 (0 … 256) |
| 6 | 1 | flags | bit 0 Z, 1 N, 2 P, 3 CV, 4 R, 5 RS; bits 6–7 are always 0 |
| 7 | 1 | last arithmetic status | 0 OK, 2 OVERFLOW (1 and 3 are never produced) |
| 8 | 4 | retired count, u32 LE | see §3 |
| 12 | 4 | budget B, u32 LE | 1 … 2³²−1 |
| 16 | 1 | initialized mask | bit i = Si initialized |
| 17 | 192 | S0 … S7, 24 bytes each | a (i64 two's complement LE), b (i64 LE), d (u64 LE). **An uninitialized register is 24 zero bytes** |
| 209 | 4 | CRC-32, u32 LE | over bytes 0 … 208 |

**Reserved values.** These fields have none beyond those listed: flags bits 6–7, status 1 and 3,
and cause values above 6. A reader should reject a record that carries any of them.

**Stability.** Every harness and fuzz comparison checks all 213 bytes against the oracle's
independent serializer.

## 6. Recommendation

The three sources agree on all observable behaviour that was tested. The next contract revision
should:
1. drop `SMOV` from the supported list (X1);
2. state the `SNORM` rule (X2) and the conventions in §3 and §5;
3. record X3 and X7–X11 as known limits.

Two choices remain before RTL-0:
- **O6:** keep `SRD` and the result buffer, or retire them;
- **X9:** whether the image CRC should also cover the header.
