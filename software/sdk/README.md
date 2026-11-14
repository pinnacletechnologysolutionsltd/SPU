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

## The example

[`examples/orientation/`](examples/orientation/) is Program A, case A: the exact orientation of (0, 0),
(2, √3), (1, 2√3). The determinant is 3√3, so S7 = +1 (CCW).
- Its source assembles byte for byte into `hardware/tests/psurd_rtl0c/session_v1/A-A.spui`, the image run
  in the RTL-0C session.
- Its expected record is that session's frozen record `record_01_4150ac7bbcbc.rec`, which the oracle and the
  C++ simulator reproduce exactly.
- §3.53 of the evidence ledger reports every response in that session equal to its expectation, on one board
  and in one session. That is a single-session silicon observation, not a qualification.

The SDK's own `fpga` backend was run once in **SDK-HW-0 run-01** (2026-11-12,
`build/sdk-hw-0/run-01/`). The board was configured as in §3.53 and not reloaded. The committed source returned
a record byte-identical to `record_01_4150ac7bbcbc.rec`. This is a single observation on one unit, not a
qualification of the SDK host path, and it is not yet in the evidence ledger.

## Assembly language (v0.3 only)

One instruction per line. Labels are written `name:`; comments start with `;` or `#`; integers are decimal or
`0x`.
- Instructions: `SLI Sd, s, u32`, `SLD Sd`, `SMUL|SADD|SSUB Sd, Sa, Sb`, `SNORM Sd, Sa`, `SLIK Sd, i32`,
  `STST Sa`, `BR cc, label|address` (cc ∈ AL EQ NE LT GE GT LE RF NR RS), `HALT`.
- `LOADT Sd, a, b, d` is a macro for the seven words that load (a + b√3)/d.
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
| C++ simulator | `software/vm/spu_vm --profile programmable-surd` | v0.3 | `sim` backend. Its capability manifest reports `fpga_demonstrated: true` (`9710dc1c`, citing §3.53) |
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
