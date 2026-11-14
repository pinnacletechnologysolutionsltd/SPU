# SPU v0.3 RTL-0A plan: programmable execution core (simulation)

**Status: PLAN — APPROVED 2026-11-11 (D1–D5 as recommended), with the refinements marked "owner".**

Implementation is authorized in stages:
- G1 first, as a **hard stop**;
- the frontend modules only after G1 passes.

RTL-0A does not authorize synthesis, place and route, UART work or FPGA testing.

**Specification:** the frozen [v0.3 contract](SPU_V03_CONTRACT_CANDIDATE.md) (frozen 2026-11-11, `6548f4a4`).

**Reference model:** the `programmable-surd` simulator and the independent oracle
`software/tests/psurd_oracle.py`.

## 1. Objective and boundaries

RTL-0A builds and verifies, **in simulation only**:
- the programmable execution core: register file, PC, decoder, arithmetic integration, `STST`, branching,
  refusal flags and termination;
- a simulation-loaded instruction memory.

It ends when the RTL produces byte-identical 213-byte records to the oracle on the registered programs
and fixtures.

**Not in RTL-0A:**
- the SPUI loader, image-valid logic, BUSY, UART and transport (RTL-0B);
- synthesis, place and route, timing and any board work (RTL-0C);
- v0.4 domains or bases;
- any ISA change.

**Frozen Gen-1 files are never edited.** The shared modules used by the Gen-1 build are instantiated
unchanged:
- `hardware/rtl/core/spu13/spu13_surd_{bank,load,arith}.v`;
- `hardware/rtl/math/surd_*`;
- `hardware/boards/artix7/wukong_v3/cpu_v02/**`.

A gate (§5, G6) checks that they are byte-identical.

## 2. What the existing RTL provides (from source inspection)

| Module | Reuse | Gap against the frozen contract |
|---|---|---|
| `spu13_surd_bank` (8 × 192 bits, initialized mask, two asynchronous read ports, one write port) | **Instantiate unchanged** | It resets all tuple bits to (0, 0, 1). The contract permits this but no longer requires it (§2). This reset is why Gen-1 has no LUT-RAM. Dropping it is a later optimization (§7, D3) |
| `spu13_surd_load` (staging, `received`, target) | **Instantiate unchanged** | Matches §4: a different-target `SLI` is refused, `SLD` checks all six slices, the target and d ≠ 0, and `SLD` always clears staging |
| `spu13_surd_arith` (ops 3 `SMUL`, 4 `SADD`, 5 `SSUB`, 6 `SNORM`; raw-fit, then normalize, then refuse) | **Instantiate unchanged** | `SMUL` is Gen-1 qualified. **`SADD`, `SSUB` and `SNORM` have no RTL evidence**; G1 qualifies them. Status codes use Gen-1 numbering, translated by name per §12.2. The `SNORM` `!n_fit` path must be unreachable (§4); G1 checks this |
| `spu13_surd_exec` (Gen-1 execute wrapper) | **Not reused** | It owns the bank's only write port and its only register read path. `SLIK` needs a direct write, and `STST` needs a full 192-bit read. It also decodes `SRD` and `SSTAT`, which v0.3 retires |
| — | **New** | The v0.3 execute wrapper, the sign unit, the frontend FSM and the instruction memory (§3) |

## 3. New modules

Each module is 50–150 lines, in `hardware/rtl/core/psurd/`.

| Module | Function |
|---|---|
| `psurd_imem.v` | 256 × 64 synchronous-read memory. In RTL-0A it is loaded by `$readmemh` from an oracle-built image; RTL-0B replaces the load path |
| `psurd_decode.v` | Combinational full-word decode per §3: all 8 opcode bits and every must-be-zero field. Outputs the class, operands and `bad_encoding`. **0x78–0x7B never reach the arithmetic unit** |
| `psurd_sign.v` | `STST`: sign of a + b√3 from a 192-bit tuple. Same-sign fast path; otherwise an unsigned 128-bit compare of a² with 3b², including b = −2⁶³ and a = −2⁶³. Implementation choice in §7, D1 |
| `psurd_exec.v` | Instantiates bank, load and arith unchanged. Muxes the bank write port between the arith result and `SLIK`. Exposes `qa` for `STST`. It writes the bank only when the arith status is OK, as the Gen-1 wrapper does, so OVERFLOW leaves the destination unwritten. G4 checks this |
| `psurd_core.v` | Sequential multicycle FSM, in the step order of §7: BUDGET check, then PC_OVERRUN, then fetch, decode, operand check, execute and retire. It holds the 9-bit PC, the 32-bit retired count and budget, Z/N/P/CV/R/RS and the last status, and implements the BR order (encoding, then target, then CV, then condition). Exposes the terminal cause and PC |
| Simulation-only dump | Serializes the final state into the §11 record layout: zero-fill for uninitialized registers, CRC-32. It lives in the generated testbench, not in synthesizable RTL; RTL-0B builds the real record path |

## 4. Verification approach

This follows the `hardware/tests/spu13/gen1_integration` pattern. A Python runner, `hardware/tests/psurd_rtl0a/run.py`:
1. hash-checks the frozen sources;
2. builds images and expected records with `psurd_oracle.py` (never from RTL output);
3. generates the testbench into OUT_DIR, with no `.v` file entering the tree;
4. compiles with `iverilog -g2012` and runs;
5. compares each RTL record **byte for byte**.

The C++ simulator is a second reference, and its records must also match. The runner is registered as a
required test in `run_all_tests.py`, like the Gen-1 frontend check, and stays outside the generic bench
manifest.

## 5. Gates for RTL-0A

| Gate | Content | Pass |
|---|---|---|
| G1 arith qualification (**hard stop**) | Unit bench of the unchanged `spu13_surd_arith` for ops 4/5/6 (and 3 as a control): boundary operands (±2⁶³ limits, d = 2⁶⁴ − 1, raw-fit edges, values that need normalization, refusal edges), plus ≥ 2,000 seeded random vectors. Owner additions: the **handshake**, meaning `done` fires exactly once per `start`, the result is held stable until the next `start`, and a reset during an operation produces no stale `done` and a correct next operation | The **stored tuple** (not just the value) and the status agree with the oracle; `SNORM` never refuses. On any failure: **stop**, with no frontend RTL and no change to the contract or the shared unit without separate review |
| G2 sign unit | Boundary set (zero, a = −2⁶³, b = −2⁶³, near-cancelling a² ≈ 3b² from Pell convergents) plus random | Agrees with the oracle sign |
| G3 decoder | All 256 opcodes with zero fields, the 361 per-field malformed words from `psurd_fixtures.py`, and every accepted form | Class and BAD_ENCODING agree; no state change |
| G4 programs | Owner addition, **write atomicity**: on OVERFLOW the bank gets no write, including when the destination aliases a source. Plus Program A cases A–F, Program B for K ∈ {−1, 0, 1, 2, 33, 34, 50}, and the SIM-0 negative-control programs (INVALID, BAD_TARGET taken and not taken, PC_OVERRUN at 1 and 256, BUDGET, BUDGET with PC = L, HALT on the B-th instruction, R cleared with RS sticky, `SLIK` not aliasing `SLI`, staging keeping the old value) | 213-byte records identical to the oracle and to the C++ simulator |
| G5 falsifiability | Planted RTL mutants, built from a scratch copy only: `BR` without the CV check, refusal writing the destination, decoder ignoring bit 59 | Each mutant fails at least one of G1–G4 |
| G6 frozen boundary | Owner refinement: the sha256 of every shared module is compared with a **recorded baseline**, `hardware/tests/spu13/gen1_integration/fixtures/source_hashes.sha256`, not just an empty `git diff`, since a committed change would not show there. Plus Gen-1 conformance 80/80 and the Gen-1 integration runner unchanged | Pass |
| G7 integrated gate | `tools/verify_repo.sh`, detached | COMPLETE with exit 0 |

Optionally, for early warning only: a Yosys `synth_xilinx` resource count. Not a timing claim.

Owner requirements for every bench:
- **Watchdog.** Every generated simulation has a bounded watchdog, and a timeout is recorded as a
  distinct outcome, never as a pass.
- **The record serializer is simulation-only in RTL-0A.** Passing G4 does **not** qualify the
  synthesizable record output or the UART; those belong to RTL-0B.

## 6. Work order

1. G1 arith qualification against the unchanged module. This is the largest unknown, because it is the
   first RTL evidence for `SADD`, `SSUB` and `SNORM`. If it finds a mismatch, **stop and report** before
   writing any core RTL; the contract governs.
2. `psurd_decode` and G3.
3. `psurd_sign` and G2.
4. `psurd_exec`, `psurd_core`, `psurd_imem`, then G4 and G5.
5. G6 and G7, then a report. RTL-0B planning follows separately.

## 7. Decisions requested

| # | Decision | Recommendation |
|---|---|---|
| D1 | `STST` multipliers: two dedicated 64×64 squarers (on the order of 24 more DSPs, by analogy with Gen-1's five 64×64 lanes using 60 of 240; unsynthesized estimate), or a multicycle unit that shares one multiplier | **Dedicated** for RTL-0A (simplest and easiest to verify). Revisit at RTL-0C if DSP or timing pressure appears |
| D2 | New modules' directory | `hardware/rtl/core/psurd/` (separate from `spu13/`) |
| D3 | Register-file reset | **Keep the unchanged bank** (full reset, flip-flops) for RTL-0A. A mask-only-reset bank that allows LUT-RAM is an RTL-0C optimization and its own small change |
| D4 | Test registration | One required runner entry in `run_all_tests.py`, accounted separately like the SIM-0 entry |
| D5 | Simulator for benches | Icarus (`-g2012`), with Verilator only as the existing fallback |

## 8. Risks

- **G1 may find that the RTL's `SADD`/`SSUB` differs from the contract.** The raw-fit rule makes lcm
  alignment bit-visible. Either the RTL or the contract would then need revising, and the contract is
  frozen. A mismatch is reported and goes to an explicit revision; it is not patched quietly.
- **Arithmetic latency is data-dependent** because of the gcd steps. The FSM waits on `done`, with no
  fixed cycle count assumed. Benches use a generous watchdog that is reported, never tuned to pass.
- Combinational asynchronous-read register paths into a 128-bit sign compare may lengthen the critical
  path. That matters only at RTL-0C.
