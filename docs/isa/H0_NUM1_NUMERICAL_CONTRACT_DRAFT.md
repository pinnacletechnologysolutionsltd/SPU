# H0-NUM-1 — Source-derived numerical semantics for the proposed H0 profile (DRAFT)

**Status:** non-normative draft. Documentation and source inspection only. No RTL, VM, assembler, opcode, algorithm, SPI or hardware change. Numerical ratification and implementation are **HOLD**.
**Baseline:** `dev/next` at `23f7f94c6e6b8f663a90f561e4c2e8bc467da03e` (RTL, VM and C++ sources unchanged from public RC2 `b063280`).
**Profile:** SPU-H0-RPLU2-v0.2 (proposed, see [`H0_C1_PROTOCOL_CONTRACT_DRAFT.md`](H0_C1_PROTOCOL_CONTRACT_DRAFT.md)). Scope: QLDI `0x1D`, QSUB `0x1B`, ROTC `0x1C`, RPLU2 start `0x2A`.
**Evidence classes:** *source* = read from RTL/VM/C++; *oracle* = computed host-side from source formulas or `software/lib/a31_field.py`, **not observed in RTL simulation by this task**; *simulation* = observed in a preserved probe (H0-V1: [`ISA_V02_H0V1_FINDINGS.md`](ISA_V02_H0V1_FINDINGS.md)); *proposed* = not implemented. Nothing here is claimed silicon-verified; the only ledger entries touching these operations are in [`docs/hardware_evidence.md`](../hardware_evidence.md) §3.0 (QLDI, QSUB, ROTC angles 0–5 through the main core on Wukong Artix-7, ROBOTICS smoke) and §3.2g (Tang 25K probe). `0x2A` has no ledger entry for this profile.

Each operation section separates **(O) observed implementation behavior**, **(P) proposed profile semantics**, **(U) unverified questions**. Mismatches are recorded, not normalized.

## 0. Common state

* RTL: `spu_quadray_regfile.v`; 13 lanes × 4 components (A..D) × 64 bits. Component = `{Q[63:32], P[31:0]}`, each a signed int32 (Q = √3 coefficient, P = rational part). ECC wrapper. Lane index (8-bit field) is reduced mod 13 by `qr_lane()` (13→0, 14→1, 255→8).
* RTL reset: A = `64'h0000_0001_0000_0000` (Q=1, P=0 by stated encoding; commented "identity A=1"), B=C=D=0. VE hydration writes lanes 1–12 only (Q12 scale, 1 = `0x1000` in P); **lane 0 is not hydrated**. VMs reset all components to zero. (O) mismatch M7.
* QLDI/QSUB/ROTC never write a nonzero Q half (derived from the formulas below), except lane 0 component A after reset (and any Q halves already present).
* Commit telemetry reports `{32'd0, sext32(value)}` style A..D for QLDI; QSUB/ROTC report the written lane. Telemetry is not architectural state.

## 1. QLDI (`0x1D`)

**(O)** `spu13_core.v` `:1373-1392`. dest = `qr_lane(word[55:48])`. Immediates: A=sext8(`word[39:32]`), B=`[31:24]`, C=`[23:16]`, D=`[15:8]`, each sign-extended to 32 bits into the **P half**; Q half written 0. `word[47:40]` (R2) and `word[7:0]` ignored. Tag UNTAGGED. One commit, `inst_done` next cycle (simulation: H0-V1 §2). VM: `(p1_a>>8)&0xFF` etc., sign-extended, `RationalSurd(A,0)`. C++: same field layout. No refusal path.
**(P)** Same as observed; ignored bits are "must be zero / not checked" until the contract decides (U1). Domain: P ∈ [−128,127] per component, Q = 0.
**(U1)** whether nonzero ignored bits should be rejected by the profile (rejection would be a new behavior, not an observed one).

## 2. QSUB (`0x1B`)

**(O)** `:1343-1372`, `:1564-1571`, `rs_sub64`. dest = `qr_lane(word[55:48])`, lhs = `qr_lane(word[47:40])`, rhs = `qr_lane(word[11:8])` (**only the low nibble of the 16-bit P1_B field**, then mod 13). Per component, per half independently: `{L[63:32]-R[63:32], L[31:0]-R[31:0]}`, 32-bit two's-complement wraparound, no carry between halves, no overflow flag. Two-stage sequence, tags joined, one commit.
**VM:** rhs = `p1_b % 13` with sign-extended 16-bit `p1_b`; arithmetic unbounded Python integers. **C++:** rhs = `(uint16_t)p1_b % 13`; int32 arithmetic with check. RTL, VM and C++ agree on the rhs lane only for `P1_B ∈ [0,15]` (M1). They agree on values only when no half overflows int32 (M2).
Oracle examples: `0x80000000 − 1 → 0x7FFFFFFF` (RTL wrap); `0 − 0x80000000 → 0x80000000`. Rhs lane for `P1_B=0x8000`: VM 5, C++ 8, RTL 0.
**(P)** Per-half 32-bit modular subtraction; rhs lane taken as `qr_lane(P1_B[3:0])`, so profile-valid `P1_B ∈ [0,12]` is the only range where all three agree on lane; 13–15 alias to 0–2 in all three. Overflow is wrap, not refusal (matches RTL; VM/C++ differ).
**(U2)** whether 13–15 and `P1_B > 15` should be rejected rather than aliased. **(U3)** whether wrap or refusal is wanted on overflow (changing RTL would be a repair, not in scope).

## 3. ROTC (`0x1C`)

**(O)** Angle = `word[29:24]` (P1_A[5:0]). `word[31:30]` captured, ignored (multiplier fallback disabled, `ENABLE_TDM_FALLBACK(0)`). src = `qr_lane(word[47:40])`, dest = `qr_lane(word[55:48])`. Angle > `ROTC_MAX_VERIFIED_ANGLE` (35) → fault path: QR untouched, `rotc_debug_flags[7]`, still `inst_done` (decode bound only; 36–63 fault). A passes through for angles 0–5. Per-half independent 32-bit arithmetic with wraparound; thirds angles use `div3` (multiply by `0x55555556`), **truncation toward zero** (oracle: equals trunc on [−100000,100000] and extremes).
Rows (RTL, matching `software/tests/isa_semantics_oracle.py` formulas):

| Angle | B' | C' | D' |
|---|---|---|---|
| 0 | B | C | D |
| 1 | (2B−C+2D)/3 | (2B+2C−D)/3 | (−B+2C+2D)/3 |
| 2 | D | B | C |
| 3 | (−B+2C+2D)/3 | (2B−C+2D)/3 | (2B+2C−D)/3 |
| 4 | (2B+2C−D)/3 | (−B+2C+2D)/3 | (2B−C+2D)/3 |
| 5 | C | D | B |

Rows for angles 1, 3, 4 are exact iff the row numerator is divisible by 3; each is so iff B+C+D ≡ 0 (mod 3) (per half). Angles 2, 5 are permutations (always exact, no wrap).
**VM / oracle:** angles 1/3/4 round to nearest, ties away from zero (Q12 scaled rdiv); RTL truncates toward zero (M3). **C++:** angles 0–5 only.
Angle status: **candidate** 0–5 (profile); **source-supported** 0–35 as RTL decode bound only (no rows verified here); **ledger** 0–5 on Wukong (§3.0) and Tang (§3.2g); 6–35 have no evidence in this task; 36–63 fault.
**(P)** Profile angles 0–5. Result defined bit-exactly by the table with truncating `/3` and 32-bit wrap per half. Angles 6–63 in the profile → UNSUPPORTED/refusal per H0-C1 (outcome encoding not defined here). Inputs with B+C+D ≢ 0 (mod 3) are not exact; whether the profile accepts them is **U4**.
Oracle vectors (exact): (A,B,C,D) = (1,2,3,4): a1→(1,3,2,4). (0,3,−6,9): a1→(0,10,−5,1), a3→(0,1,10,−5), a4→(0,−5,1,10). Any source: a2→(A,D,B,C), a5→(A,C,D,B). Wrap: B=C=D=2³⁰ a1→ −357913941 each (RTL, oracle). Non-exact: (0,−1,0,0) a1: exact (−2/3,−2/3,1/3); RTL (0,0,0); VM/oracle (−1,−1,0).
**(U4)** non-exact source policy (reject, truncate as RTL, or restrict domain). **(U5)** angles 6–35 rows. **(U6)** ROTC through `ENABLE_MATH` spin: the existing `RPLU2` spin has `ENABLE_MATH=0` and ROTC would hang there.

## 4. RPLU2 start (`0x2A`)

**(O)** Opcode `0x2A` is SOM in the spec/VM; in the RTL path with `ENABLE_CORE_RPLU_V2` it starts the RPLU2 pipeline. No simulator models the RTL meaning (M5).
Pipeline (source: `spu13_core.v:580-594,1328-1341,1586-1592`, `rplu_pipeline.v`, `spu_som_bmu.v`, `spu_som_weight_bram.v`, `spu13_btu_core_top.v`, `rplu_thimble_pade.v`):

1. **Features.** Source lane = `qr_lane(word[47:40])`; components A..D each narrowed to `{Q[17:0], P[17:0]}` — low 18 bits of each half, signed 18-bit, so values alias mod 2¹⁸ (M6).
2. **SOM BMU.** 7 nodes, weights fixed in an `initial` block (node0 zeros; n1 f0=(2,0); n2 f1=(2,0); n3 f2=(2,0); n4 f0=(−2,0); n5 f1=(−2,0); n6 f2=(−2,0) and f3=(1,1)). Per feature quadrance (dp²+3dq²)+(2dp·dq)√3 with 18-bit differences, accumulated over 4 features truncated to 32 bits; exact comparison in Q(√3), strict less, lowest index wins ties. Training port tied off.
3. **BTU.** Best id → one-hot → row k (rows 0–6 reachable) of 4 lanes c0..c3 (32-bit; BRAM default zeros), written via `0xA5` selector 3. Saddle x = row.
4. **Padé.** Coefficients via `0xA5` selector 1 (numerator) and 2 (denominator), index < 5; low write (addr idx) stores c0,c1; high write (addr|8) commits with c2,c3. Defaults num0=1, den0=1, others 0. Horner over A₃₁ = F_p[x,y]/(x²−3,y²−5), p=2³¹−1, basis [1,√3,√5,√15]; one tower inversion of the denominator (zero-norm → `flags_v`); final multiply. Oracle: `software/lib/a31_field.py`.
5. **Result.** Limbs c0..c3 → commit telemetry A..D as `{32'd0, c}`, lane label = `qr_lane(word[55:48])`. **No Quadray register-file write.** kappa (selector 6) feeds coherence telemetry only.

Oracle vectors (illustrative; **not** SET-N/SET-R contents): num=2,den=1 → (2,0,0,0); num=1+x, den=1, x=3 → (4,0,0,0); num=1, den=1+x, x=1 → (1073741824,0,0,0) = (p+1)/2; num=x, den=1, x=√3 → (0,1,0,0); witness den0=(0x2CEE24B2,0,0,1) → `flags_v` (REFUSED); den=x at x=0 → `flags_v`. BMU oracle: zero→node0; A=2→1; B=2→2; C=2→3; A=−2→4; B=−2→5; C=−2→0 (node6 needs f3=(1,1)); A=1→0; A=1,B=1 tie→0; A=2¹⁸+2 aliases to A=2→node1.
**Refusal (O):** the sidecar gates `flags_v` correctly; the ordinary RPLU pipeline/core bridge publishes a stale or `x` result with valid indications (A31-R2, simulation), and `0xAE` valid is sticky.
**(P)** `0x2A` is telemetry-only (no QR write). Result is the oracle A₃₁ value of the Padé rational at the saddle row selected by the SOM/BTU path, or REFUSED when `flags_v`. Whether the numeric content may rely on SOM/BTU (vs a single configured row) is **U7**.
**Dependencies on SET-N/SET-R:** coefficient values (numerator/denominator per row, BTU rows 0–6) come from the manifests, whose contents are **not defined here**. SET-R is expected to contain a zero-divisor witness; SET-N must avoid zero norm for exercised inputs.
**(U7)** SOM fixed weights as profile-normative? **(U8)** non-canonical limbs ≥ p behavior (unverified in RTL). **(U9)** behavior when `x` cannot be represented in 18+18 bits. **(U10)** row k when BTU yields rows with unconfigured (zero) coefficients: c=0 numerator gives result 0 or refusal depending on den. **(U11)** result freshness/identity belongs to H0-C1, not here.

## 5. Mismatch register

| # | Mismatch | Sources |
|---|---|---|
| M1 | QSUB rhs lane: VM signed `%13`, C++ unsigned `%13`, RTL nibble `[11:8]` mod 13 | agree only for P1_B 0..15 |
| M2 | QSUB overflow: VM unbounded, C++ int32-checked, RTL wrap | |
| M3 | ROTC thirds: RTL trunc toward zero; VM/oracle nearest ties-away | differ when row sum not divisible by 3 |
| M4 | ROTC angle set: RTL gate ≤35, C++ 0–5, profile 0–5, ledger 0–5 | |
| M5 | `0x2A`: SOM in spec/VM; RPLU2 start in profile; no simulator model | |
| M6 | `0x2A` feature narrowing to 18-bit aliases | RTL only |
| M7 | QR reset: VM zero; RTL A=(Q=1,P=0) reset, VE hydration Q12 scale, lane 0 unhydrated | |
| M8 | Ignored bits (QLDI R2/low byte, ROTC field bits) unchecked in all | |
| M9 | RTL acknowledges unsupported opcodes with `inst_done` (H0-V1) | transport, noted for completeness |

## 6. Finite conformance vector classes (proposed; none are test artifacts yet)

* **QLDI:** immediates {−128, −1, 0, 1, 127} per component; lanes {0, 1, 12}; alias lane 13→0, 255→8 (documented behavior, U1); ignored bits nonzero.
* **QSUB:** self-subtract → 0; 0−0x80000000 and 0x80000000−1 wrap; rhs P1_B ∈ {0, 12, 13, 15, 16} (alias/boundary); lhs=dest aliasing.
* **ROTC:** angles 0–5 on exact source (B+C+D ≡ 0 mod 3) with sources above; angle 2/5 on arbitrary source incl. extremes; angles 1/3/4 on non-exact source (records RTL truncation, flags M3); angle 6 and 36 (refusal/fault classification, U5); six-step angle-1 closure on an exact source.
* **0x2A:** V1–V6 above, each with explicit manifest-independent coefficients; BMU cases incl. tie and alias; refusal witness; configuration-dependent vectors must wait for SET-N/SET-R.

Independent oracles needed: QLDI/QSUB — trivial; ROTC — the isa_semantics_oracle formulas with truncating division (the existing oracle rounds, so a new truncating oracle is required, M3); `0x2A` — a31_field plus an emulation of SOM/BTU/Padé configuration (does not exist yet).

## 7. Qualification blockers

1. M3: profile must pick truncation (RTL) or rounding (VM); VM/oracle and RTL currently disagree on non-exact inputs.
2. M1/M2: QSUB lane decode and overflow policy must be frozen; simulators differ from RTL outside narrow ranges.
3. No simulator or oracle implements `0x2A` as RPLU2 start (M5).
4. SET-N/SET-R manifests undefined; `0x2A` vectors beyond illustrative ones are blocked.
5. QR reset-state ambiguity (M7) affects any vector reading unhydrated lanes (incl. lane 0).
6. Unverified: ROTC angles 6–35, non-canonical A₃₁ limbs, 18-bit aliasing intent, ignored-bit policy.
7. This document's vectors are oracle-derived; no RTL simulation of them has been run in this task, so none is "testbench-verified" and none is silicon-verified.
