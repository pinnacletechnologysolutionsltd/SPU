# SPU SDK-0 — v0.3 `programmable-surd` developer interface (experimental)

SDK-0 lets an engineer write a v0.3 program, run it on the simulator or a board, and check the result, without
reading the RTL. It targets **only** the frozen v0.3 profile
([contract](../../docs/design/SPU_V03_CONTRACT_CANDIDATE.md), image revision 0x03). It wraps the existing tools
and changes none of them; nothing here alters the ISA, simulator semantics, RTL or the host protocol.

## Workflow

```sh
mkdir -p build/sdk
make -C software/vm BIN=$PWD/build/sdk/spu_vm          # C++ simulator (once)
python3 software/sdk/spu.py assemble software/sdk/examples/orientation/orientation.spu \
        -o build/sdk/orientation.spui --profile programmable-surd --listing
python3 software/sdk/spu.py run build/sdk/orientation.spui --backend sim --spu-vm build/sdk/spu_vm
python3 software/sdk/spu.py verify build/sdk/orientation.spui \
        --expect software/sdk/examples/orientation/expected.json --spu-vm build/sdk/spu_vm
python3 software/sdk/spu.py disasm build/sdk/orientation.spui
# With a Wukong running the v0.3 board image (docs/hardware_evidence.md §3.53); the port is never guessed:
python3 software/sdk/spu.py verify build/sdk/orientation.spui --expect software/sdk/examples/orientation/expected.json \
        --spu-vm build/sdk/spu_vm --backends oracle,sim,fpga --port /dev/serial/by-id/<CH340 device>
python3 software/tests/test_spu_sdk.py                  # SDK-0 tests (not part of run_all_tests.py)
```

`verify` requires byte-identical 213-byte result records from every backend it is given, and checks the
expectations file.

## The examples

Three canonical examples are provided. Each directory holds a source and an `expected.json`. Each source
assembles byte for byte into a frozen image of the RTL-0C session package
(`hardware/tests/psurd_rtl0c/session_v1/`), and each expectation is that session's frozen record, which the
oracle and the C++ simulator reproduce exactly.

| Example | Image | Frozen record | Result |
|---|---|---|---|
| [`orientation/`](examples/orientation/): exact orientation of (0, 0), (2, √3), (1, 2√3) | `A-A.spui` | `record_01_4150ac7bbcbc.rec` | determinant 3√3, so S7 = +1 (CCW) |
| [`exact_sqrt3_pell/`](examples/exact_sqrt3_pell/): (2 + √3)³³ by 33 `SMUL`s | `B_K33.spui` | `record_07_56c4de4af123.rec` | S0 = x₃₃ = (3743165875258953026, 2161117825702177665, 1), S7 = 0 |
| [`branching_pell_overflow/`](examples/branching_pell_overflow/): the same loop with K = 34 | `B_K34.spui` | `record_08_856aa241facc.rec` | the 34th `SMUL` refuses and `BR RF` takes the overflow branch; S0 keeps x₃₃, S7 = 1 |

To run the Pell examples, replace the source and `--expect` paths in the workflow above with the example's own
directory (for example `examples/exact_sqrt3_pell/pell_k33.spu` and `.../expected.json`).

**What is recorded, and what is not.** The three frozen images were run on one Wukong board in a single session
(ledger §3.53), and every response in that session equalled its expectation. The SDK's own `fpga` backend then
ran the orientation image once (SDK-HW-0 run-01, 2026-11-12), without reloading the board; the returned record
was byte-identical to `record_01_4150ac7bbcbc.rec` (ledger §3.54). Both are **recorded physical-execution
observations from one FPGA unit and one session, not a hardware qualification.** They do not establish
timing margin, reset behaviour, the UART interface, operation across reloads, power cycles, supply or
temperature, or behaviour on any other unit. §3.54 did not verify the bitstream contents: the board
configuration was inferred from the retained state. The evidence directory named in §3.54 is local and is not
part of this repository. The two Pell sources and all `expected.json` files were checked here by the oracle and
the C++ simulator only; running them on hardware again is not claimed.

## Writing programs: refusal, and what a program can take as input

### Refusal

`SMUL`, `SADD` and `SSUB` **refuse** when the exact result cannot be held in the 64-bit fields. A refusal is not a
fault and does not stop the run:

- the destination register keeps its previous value;
- the arithmetic status becomes OVERFLOW, and the flags `R` and `RS` are set to 1;
- the instruction retires, and execution continues at the next instruction.

The old value in the destination is a valid number, but it is **not the result of the operation that was
refused**. A program that does not check, and goes on to use that register, computes from an unintended value.
The run can still end with cause `HALT`: `HALT` means the program reached its `HALT` instruction, not that every
arithmetic instruction succeeded. A bad program can retire a refusal, halt, and look finished.

The flags answer two different questions:

| Flag | Meaning | Branch |
|---|---|---|
| `R` | The most recent arithmetic instruction (`SMUL`, `SADD`, `SSUB` or `SNORM`) refused. Every such instruction rewrites it, so a later success clears it; `SNORM` never refuses and sets `R` to 0 | `BR RF, label` (refused) or `BR NR, label` (not refused), immediately after the operation |
| `RS` | Some arithmetic instruction refused at some point in this run. Only START clears it; no instruction does | `BR RS, label`, normally once at the end |

Check `R` immediately after an operation that can refuse (`BR RF`), before the program uses the destination: that
is the safer general practice, because a final `RS` test shows that a refusal happened but cannot stop later
instructions from using a preserved, unintended intermediate value. `RS` is the right test when the question is
"did anything in this run refuse?". `RS` = 1 does not by itself mean the final output is invalid, since a program may
recover; the result record reports both the output and `RS`, and the program decides.

Both patterns appear in the examples. `orientation.spu` computes the whole determinant and then tests
`BR RS, refused` before it classifies the value, so a refusal anywhere gives S7 = 2 and never a sign. The Pell loop
tests `BR RF` after every `SMUL`: on a refusal it leaves the loop with S0 still holding the last good power.

### Inputs

v0.3 has **no data memory**. The state is eight Surd registers S0–S7 and a program image of 1 to 256 words.
Registers are uninitialized at every START, and reading one before it is written is a fault (`INVALID`).

There is no general facility for supplying operands while a program runs. A host supplies only the **image** (LOAD)
and the **budget** (START). A program's input values are therefore part of its image, written with `LOADT` or
`SLIK`, and different inputs need a different image: edit the source, assemble, load, start. Results come back
in the 213-byte result record. The orientation program decides the orientation of the points written into it;
it cannot be fed a stream of new points. This is a property of the current machine, stated here as a limitation.

## Assembly language (v0.3 only)

One instruction per line. Labels are written `name:`; comments start with `;` or `#`; integers are decimal or
`0x`.
- Instructions: `SLI Sd, s, u32`, `SLD Sd`, `SMUL|SADD|SSUB Sd, Sa, Sb`, `SNORM Sd, Sa`, `SLIK Sd, i32`,
  `STST Sa`, `BR cc, label|address` (cc ∈ AL EQ NE LT GE GT LE RF NR RS), `HALT`.
- `LOADT Sd, a, b, d` is an **assembler macro, not a machine instruction**. It expands to seven words: six
  `SLI Sd, s, u32` (slices 0–5) followed by `SLD Sd`, which loads the tuple (a, b, d), meaning (a + b√3)/d. `SLD`
  commits the staged tuple atomically, and only if all six slices were written for the same target and d is nonzero;
  otherwise the run faults with `INVALID` and `Sd` is unchanged. Each `LOADT` costs 7 of the image's 256 words.
- `SLIK Sd, i32` loads the integer i (sign-extended 32-bit) as (i, 0, 1) in one word.
- `SNORM Sd, Sa` divides `Sa` by gcd(|a|, |b|, d) and never refuses.
- `.word` emits one raw word, for fault tests.
- The profile must be given with `--profile programmable-surd` (contract D-1 condition 2). The assembler
  never infers it.
- Rejected, with an error rather than silently: `SRD`, `SSTAT` and `SMOV`; legacy and SPU-13 mnemonics;
  registers outside S0–S7; out-of-range fields; unknown or out-of-image branch targets; images outside
  1–256 words.

## Tooling inventory (SDK-0, 2026-11-12)

| Tool | Path | Architecture | Use in SDK-0 |
|---|---|---|---|
| Python oracle and encoder | `software/tests/psurd_oracle.py` | v0.3 | `oracle` backend; independent cross-check of the SDK encoder |
| C++ simulator | `software/vm/spu_vm --profile programmable-surd` | v0.3 | `sim` backend. Its capability manifest reports `fpga_demonstrated: true` (`9710dc1c`, citing §3.53: single session, one unit; not a qualification) |
| UART host client | `tools/psurd_uart_host.py` | v0.3 (H0-UART-1B v2) | `fpga` backend (`Client` API, unchanged) |
| RTL-0C session package | `hardware/tests/psurd_rtl0c/session_v1/` | v0.3 | reference images and records for tests |
| Sovereign Assembler `spu13_asm.py`, `*.sas` programs (`examples/`, `software/programs/`) | `software/tools/` | **SPU-13** (R0–R25, QR0–QR12, Lithic-L 64-bit format) | **Not v0.3.** The opcode spaces overlap (for example 0x70 is legacy `MFOLD`, v0.3 `SLI`); the SPUI identity and this assembler's mnemonic table keep them apart |
| `spu_vm.py`, `spu_compiler.py`, `spu_forge.py`, `software/spu_host/` | `software/` | SPU-13 / H0 lineage | Not used |

## Relevance of the Wildberger, Lithic-L and Sovereign work to v0.3

| Work | What it is | Relevance to the v0.3 CPU |
|---|---|---|
| `software/common/include/spu_wildberger.h` (+ `spu_wildberger_test.cpp`) | Triple Quad Formula, tangency variant, Spread Law and rational Fresnel, over `RationalSurd` | **The mathematics is relevant** to future exact-geometry software. **The implementation is not reusable as-is:** it rests on `spu_surd.h` (below). Its "hardware correspondence" opcodes `TRIPLE_QUAD`, `SPREAD_LAW` and `FRESNEL` do not exist in `hardware/rtl`, `software/vm` or the v0.3 contract. On v0.3 these laws would be ordinary `SMUL`/`SADD`/`STST` programs, with finite-width limits (the Triple Quad Formula is degree 4 in the coordinates) |
| `software/common/include/spu_surd.h` | `RationalSurd`: Z[√3], `int32_t` p and q, **no denominator** | **A third arithmetic semantics**, neither an exact unbounded reference nor the v0.3 finite-width model. Overflow **wraps silently**: 50000² gives −1,794,967,296, and without `-fwrapv` that is undefined behaviour. It is not an exact reference type and does not model v0.3 |
| Wildberger research notes (`docs/WILDBERGER_*_2026-10-23.md`, `software/experiments/wildberger_*`) | Exploratory symbolic inventories (spread polynomials, quadrance/turn, Taylor sign certificates; the last one a recorded negative result) | Mathematical input for future exact-geometry software (spread, quadrance) and sign-predicate work. Host-only, with no ISA claims |
| Lithic-L (`knowledge/LITHIC_L_LANGUAGE_SPEC.md`, `spu_lithic_l.h`, `spu_lithic_l_test.cpp`) | Language spec and encoder for the **SPU-13** ISA: R0–R25/QR registers, branchless MUX programs, and a "Chord" encoding for SPU-4 | **Conceptual prior art** for a future mathematical language or IR: a field-native type system with Q(√3) as the atomic type. It does **not** target v0.3. It shares the 64-bit field layout `[63:56] op, r1, r2, p1a, p1b` that v0.3 inherited through Gen-1, but its opcodes, registers and "no branches" rule differ: v0.3 has `BR` and sign tests. Its "REIFIED / bit-locked" status line is not an evidence claim |
| Lithic-C (`spu_lithic.h`) | RP2040 cluster memory map (SPU-13/4 "Ghost OS") | Not relevant to v0.3 |

Implication for future exact-geometry software: start from a new exact type ((a + b√3)/d over arbitrary-precision integers, always
reduced) and a separate type that models v0.3 (64-bit fields, raw-fit → reduce-to-fit → refuse). Port the
Wildberger laws onto the exact type and test them against the existing symbolic inventories.
`RationalSurd` stays as SPU-13 legacy code.
