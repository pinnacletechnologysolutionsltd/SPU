# SU(3) Co-Processor Extension over A₃₁[i]

Extends the existing M31 pipeline into a degree-8 complex algebra for
deterministic 3×3 unitary matrix operations. No floating point, no exp(),
no division in hot paths.

## Algebra Stack

| Layer | Extension | Basis | Inversion cost |
|---|---|---|---|
| F_p | Base field (M31) | — | — |
| A₃₁ | F_p[u,v]/(u²−3, v²−5) | [1, √3, √5, √15] | parallel v1: 83-cycle unit / 7-cycle singular |
| A₃₁[i] | A₃₁[x]/(x²+1) | [1, √3, √5, √15, i, i√3, i√5, i√15] | ~114 cycles |

## Implemented Modules

### RTL: `hardware/rtl/core/spu13/spu13_su3_mult.v`

Verilog module. The standalone spin instantiates a dedicated
`spu13_m31_multiplier` and sequences 27 complex A₃₁[i] multiplies via TDM
through a 4-phase FSM. The separate `SU3SHARE` spin muxes the SU3 sidecar onto
the top-level shared M31 multiplier; this shared path is proven in RTL and on
silicon. The standalone module itself remains dedicated.

**Interface:** Element-wise load (9 elements per matrix), start/done handshake.
Each element is 256 bits: `{imag[127:0], real[127:0]}`, where each 128-bit
half is A₃₁ `{c3, c2, c1, c0}` × 32-bit over M31.

**Performance:** ~224 compute cycles per 3×3 multiply. Result elements now
stream in row-major order as each C[i][j] accumulator completes; there is no
separate 9-cycle C-matrix drain stage.

### RTL: `hardware/rtl/core/spu13/spu13_su3_sidecar.v`

SPI-visible Artix-7 bring-up adapter for the existing CMD `0xB1` instruction
path. The sidecar does not duplicate the multiplier's A/B matrix storage.
It assembles one 256-bit element from eight 32-bit host chunks, then streams
the completed element directly into `spu13_su3_mult`.

**Protocol:**

| Opcode | Name | Fields |
|---|---|---|
| `EA` | `SU3_START` | `[51:48] = result element 0..8 to capture` |
| `E8` | `SU3_LOAD_A` | `[55:52] = element 0..8`, `[50:48] = word 0..7`, `[31:0] = data` |
| `E9` | `SU3_LOAD_B` | `[55:52] = element 0..8`, `[50:48] = word 0..7`, `[31:0] = data` |
| `EB` | `SU3_READ` | `[55:52] = QR lane`, `[51:48] = captured result element` |

After `SU3_START`, send all A elements in row-major order, each as words
0..7, then all B elements in row-major order. `SU3_READ` commits the captured
256-bit result element to QR A/B/C/D as four 64-bit lanes.

### Python Oracle: `software/tests/test_su3_oracle.py`

20 checks verifying:
- A₃₁[i] arithmetic (i² = -1 over M31)
- 3×3 matrix multiply closure
- Dense A₃₁[i] packed matrix-product constants used by the RTL testbench
- Gell-Mann structure constants (λ₁² = diag(1,1,0), λ₃ diagonal)
- λ₈ basis encoding (`1/√3 = √3/3` in A₃₁)
- Conjugate transpose (dagger) correctness
- Determinant verification (det(I) = 1)
- PHSLK-style coherence check (λ₁·λ₁† = λ₁²)

### Testbench: `hardware/tests/spu13/spu13_su3_mult_tb.v`

5 public-output test cases (I×I, λ₁×λ₁, I×λ₁, Zero×I, dense A₃₁[i]), all PASS.
Auto-discovered by `run_all_tests.py`.

## Status

**RTL, Artix sidecar, Wukong bitstream load, and J11 SPI/QR readback are
verified.** Oracle proves the math, testbenches prove the multiplier and
SPI-visible sidecar protocol, and the Wukong Artix-7 SU3 sidecar-only spin
synthesizes and routes with `A7_CLK_DIV_LOG2=6`. The generated bitstream loads
successfully over DirtyJTAG, and the RP2350 J11 smoke firmware now streams the
dense A/B fixture over SPI and reads exact 256-bit QR commits from hardware.

2026-07-04 silicon smoke result over Wukong J11:

- `elem=0 lane=2`: `A=0x7FFE271F7FFC43EF`,
  `B=0x7FFF6B677FFED36F`, `C=0x00021510000446A0`,
  `D=0x0000A30000014F30`
- `elem=4 lane=5`: `A=0x7FFD2A6B7FFA47FF`,
  `B=0x7FFF196B7FFE2E9F`, `C=0x00034B480006BAA8`,
  `D=0x00010678000218A8`
- `elem=8 lane=8`: `A=0x7FFBF6DF7FF7DE5F`,
  `B=0x7FFEB5277FFD653F`, `C=0x0004CAA00009C0F0`,
  `D=0x00018250000312E0`

All three cases reported `PASS` and the run ended with `SU3_J11: PASS`.
The initial July smoke was later expanded to all nine dense-product result
elements on both standalone and `SU3SHARE` images. The standalone full-oracle
proof logged twelve complete runs with all nine exact 256-bit commits passing;
the shared image also passed all nine QR-lane checks.

**Corrected 2026-08-07.** The committed defaults are **25 kHz with 1000 us**
guards, not 20 us; no build-time override exists in the repository, so the
20 us figure described an uncommitted local build. The claim that a 5 us probe
produces intermittent invalid QR reads, and that 20 us is therefore the
practical margin, **did not reproduce**: 44 consecutive complete runs at
100 kHz with 5 us guards returned no invalid read. Most likely resolved by the
reset conditioning applied to the Artix XDCs after 2026-07-04. Full sweep and
caveats in `hardware_evidence.md` §3.2e.6. Do not quote a guard-delay margin
as a design constraint.
The committed standalone smoke defaults are 25 kHz SPI and 1000 us link guards.
The guard-delay sweep recorded 12 complete runs at 25 kHz/1000 us, 27 at
100 kHz/20 us, and 44 at 100 kHz/5 us, with no invalid reads. No minimum safe
guard interval has been characterized, so do not present 20 us as a required
margin. The RP2350 checker polls per-chunk status and treats final `LOAD_B`
completion as durable `SIDE_IDLE + result_ready`, because internal
`SIDE_WAIT` can be too brief to observe from the host.

2026-07-06 `SU3SHARE` expanded smoke: the RP2350 firmware now checks all nine
dense-product result elements, commits them through QR lanes 0 through 8, and
reports `SU3_J11: PASS` on the shared-multiplier Artix image. The expanded UF2
SHA-256 is
`a6d8f0541fd2cce3a930173b0ee43ba071c92826fc5dc81540674c1e0a9da87d`.

## Resource Estimate

| Resource | Count | Notes |
|---|---|---|
| DSP slices | 64 DSP48E1 on Artix-7 | 16 logical 32×32 products; each maps to 4 DSP48E1 |
| Cycles per 3×3 multiply | ~224 | Result pulses occur as C elements complete |
| Inverter latency | ~114 cycles | Conjugate reduction tower, stage 3 (if needed) |
| SU3 multiplier | ~6.2k estimated LCs on Artix-7 | A/B matrix stores, no C matrix store |
| SU3 Artix spin | ~8.2k estimated LCs, 64 DSP48E1 | Sidecar-only spin: SPI, UART stub, SU3 sidecar; core shell pruned |
| P&R pack snapshot | 21,092 LUT cells, 9,488 FFs, 64 DSP48E1 | Wukong 100T SU3 sidecar-only spin |
| Clocking | `A7_CLK_DIV_LOG2=6` | 50 MHz board oscillator divided to ~781 kHz `clk_fast` for first SPI smoke |
| Post-route timing | 51.58 MHz max for `clk_div[5]`; 128.63 MHz for oscillator path | PASS at 2 MHz route target; router converged at iter 11 |
| Bitstream | `build/spu_a7_100t_SU3.bit` | Generated from `build/spu_a7_100t_SU3.sidecar_div64.pnr.fasm`; SRAM load reports DONE |
| RP2350 smoke | `hardware/rp2350/build/rp2350_su3_j11_smoke.uf2` | All-nine dense-matrix readback is documented in `docs/hardware_evidence.md` §§3.2e.5–3.2e.6; committed standalone defaults are 25 kHz / 1000 us |

## Open engineering questions

No new SU3 FPGA build is currently authorized. The existing 100 kHz / 5 us
result shows that the earlier 20 us guard hypothesis was unnecessary for the
tested setup, but it does not establish a transport limit or a general timing
margin. Any higher-throughput campaign must first define the target SPI rate,
exact firmware/bitstream profile, repeated-run acceptance rule, timing
constraints, attempt budget, and timeout. A combined SU3/LUCAS or RPLU2 spin
is a separate integration objective and needs its own resource and timing
baseline before implementation.
