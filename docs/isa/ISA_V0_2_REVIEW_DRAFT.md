# SPU Instruction Set Architecture v0.2
## Domain, metric, and exact-execution specification — REVIEW DRAFT

**Document revision:** 0.2-draft.4 (amendments ISA-V02-D1-A, QROT-1 and SNAP-1 summaries, documentation only; source baseline for the amendment is O6 commit `2cbfa6f` on the public-RC2-derived `dev/next` in `/home/john/spu-public-v0.2-rc2`, not the private integration history)

**Date:** 26 October 2026  
**Status:** **NON-NORMATIVE / FOR ENGINEERING REVIEW**  
**Reference integration commit:** `6fc6efc951b4e5b898f0ed0f2451c7434953d5ed`  
**Implementation status:** Consolidated C++/Python/Verilog regression **COMPLETE / PASS** (261 passed, 0 failed; 185/185 Verilog variants across 177 files). This is a *source regression*, not a statement of FPGA implementation timing, complete ISA coverage, or silicon qualification.  
**Change control:** This document does not modify existing frozen contracts, opcode assignments, repository branches, or executable implementations.

> **Design thesis.** SPU investigates exact algebraic and intrinsic geometric computation as architectural semantics rather than merely software conventions layered over floating point. ISA v0.2 aims to describe a small, reviewable family of typed operations, metrics, canonicalization rules, bounds, and refusal effects. It does **not** claim that all investigated mathematical domains are currently available as native hardware instructions.

---

## 1. Purpose, scope, and authority

The primary purpose of v0.2 is to make the existing SPU work intelligible and independently reviewable without conflating (i) mathematical definitions, (ii) the behavior of a particular simulator, (iii) synthesizable RTL, and (iv) physically qualified hardware.

**In scope for this draft:** the known arithmetic domains and their status; explicit metric identity; Quadray gauge considerations; checked exact operation semantics; documented Gram v1 spread behavior; profile separation; criteria for promoting an operation into the native ISA; and reproducible conformance expectations.

**Not granted by this draft:** any new instruction encoding, new register width, unified overflow behavior across existing engines, BQ-0 or ICOS-0 hardware support, E₈ opcode, completed physical timing, ASIC performance, or an ISA compatibility promise.

The existing frozen implementation and test contracts remain authoritative for current code. Where this draft recommends a future convention, it is marked **PROPOSED**. Where a behavior is not established in available findings, it is marked **UNRESOLVED**. Apparent inconsistencies must be settled against the exact cited source revision before normative release.

### 1.1 Three qualification levels

| Label | Meaning |
|---|---|
| **Implemented / profile-specific** | Behavior exists in a named implementation; width, state, and error behavior must be read from that implementation's contract. |
| **Oracle-qualified** | Exact software mathematics and fixtures have been checked, but finite-width ISA and RTL execution are not necessarily defined. |
| **Proposed** | An architectural design choice under review; not yet an observable behavior of existing systems. |

Passing source regressions does not imply that every mathematical domain or implementation profile is covered by every stage.

## 2. Core architectural principles

1. **Domain-typed semantics.** Each instruction definition identifies its coefficient domain, geometry/metric where applicable, and a concrete execution profile. Equal physical width does not mean equal algebraic meaning.
2. **Exactness with finite representability.** An unbounded algebraic oracle may be exact even when a bounded implementation must refuse a result. The exact value and the acceptance rule are different parts of the specification.
3. **Metric explicitness.** Every norm, quadrance, spread, rotation, reflection, or determinant identifies the form it uses. The word *rotation* alone is not a correctness contract.
4. **Observable failure.** Checked operations specify validation order as needed, acceptance/refusal classes, protected state, and permitted diagnostic effects. No partially published destination state is permitted for a new **atomic checked** profile.
5. **Minimal native vocabulary.** Mathematical elegance alone does not justify a dedicated opcode; distinct semantic or measurable execution value must be established against competent lowering.
6. **Implementation independence.** Reference mathematics, simulator encodings, RTL structures, and physical layouts are separate layers linked by conformance tests.

## 3. Arithmetic and representation domains

| ID (descriptive, not binary encoding) | Mathematical representation | Evidence / present state | v0.2 treatment |
|---|---|---|---|
| **SURD3** | `a + b√3`; rational-valued versions require an explicit denominator | Python oracle may be unbounded; C++ VM checks final signed-32-bit coefficients in cited profile; surd bank has signed-64-bit `a,b` plus positive unsigned-64-bit denominator `d` under its stated configuration | **Existing / profile-specific**. Encoding and arithmetic must be attached to a named profile. |
| **QUADRAY3** | Four SURD3/integer components representing a three-dimensional space with common-offset redundancy | Quadray and Gram operations implemented in software profiles | **Existing / profile-specific**; geometric and bitwise equality deliberately distinguished. |
| **GOLDEN** | `a+bφ`, `φ²=φ+1`, coefficients over integers unless the profile states otherwise | Golden arithmetic in earlier SPU work; ICOS-0 verifies a related exact icosian oracle | **Existing research / profile-specific**; no inferred generic fixed-width gold-field ISA from ICOS-0. |
| **A31** | `F_p[x,y]/(x²−3,y²−5)`, `p=M31`, four modular coefficients | Existing modular algebra investigations; zero divisors possible | **Separate modular profile**; cannot inherit characteristic-zero field inverse rules. |
| **BQ** | `Q(√3,√5)`, rational basis `[1,√3,√5,√15]` or golden integral basis `[1,√3,φ,√3φ]` | BQ-0 exact Fraction oracle and tests; reported ~131-bit product coefficient is an unqualified scratch observation | **Oracle-qualified only**; bounded register and refusal rules deferred. |
| **ICOS/E8** | Four `Z[φ]` quaternion coordinates (eight integer coefficient lanes); lanes are integer numerators of value/2, i.e. entries lie in ½·Z[φ], with specified lattice constraints | ICOS-0 roots, exact bilinear products and reflections checked in software | **Oracle-qualified only**; no E₈ native opcode or fixed register class authorized. |

**Important representation notes:**

- A bare pair `(a,b)` does not determine whether it is an integer coefficient pair, a fixed-point pair with implicit scale, or a rational value with explicit denominator. Profile metadata must supply that distinction.
- Characteristic-zero fields have no nonzero zero divisors; **A31 does have zero divisors**. Its division/refusal logic is categorically different.
- ICOS-0's compact root coefficients describe constrained root/reflection workloads, not arbitrary products over the underlying algebra. Unrestricted products showed coefficient growth in its software experiment.

### 3.1 Proposed equality convention

**PROPOSED:** Distinguish **representation equality** (all encoded components and flags match) from **geometric value equality** (the operands represent the same geometric object). For Quadrays, adding the same scalar to all four coordinates leaves the represented geometry unchanged, so geometric equality is **gauge equivalence**. Raw register/debug comparison remains component equality.

No canonical gauge-fixing algorithm, overflow policy for gauge conversion, or encoding of a gauge-equality instruction is ratified here.

### 3.2 Normalization and canonical form

The existing surd-bank finding distinguishes raw-fitting committed outputs from explicit `SNORM` canonicalization, and describes normalization on some overflow paths. **This draft does not standardize those into a new universal policy.** Every profile must say whether normalization is mandatory, optional, or an implementation-local operation; how zero is encoded; and whether representation equality changes.

## 4. Geometric forms and invariants

### 4.1 Quadray Gram form

For four-component Quadray representatives `v,w`, the established bilinear form is:

\[
B_Q(v,w)=4\sum_{i=1}^{4}v_iw_i-\left(\sum_{i=1}^{4}v_i\right)\left(\sum_{i=1}^{4}w_i\right).
\]

Its quadrance is `Q(v)=B_Q(v,v)`. This form is unchanged by a common-coordinate offset and therefore respects the Quadray gauge relation. The equality with the tested VM quadrance is recorded in the Gram v1 research contract.

**PROPOSED v0.2 default for a newly named geometry profile:** Gram-based spread rather than `legacy_dot`. The legacy operation remains identifiable as compatibility behavior; changing the meaning of an existing opcode in an existing profile is **not** authorized.

### 4.2 Gram v1 spread

For nondegenerate operands, the tested spread returns an **unreduced** numerator/denominator pair:

\[
N=B_Q(v,v)B_Q(w,w)-B_Q(v,w)^2,
\qquad D=B_Q(v,v)B_Q(w,w).
\]

A Quadray direction is degenerate when all four of its components are equal. The frozen Gram v1 contract governs exact operand checks, validation ordering, and the concrete instruction encoding.

**Recorded instruction:** Gram spread opcode `0x15` in its existing specified profile. No additional opcode is assigned in this document.

**Operand form.** The historical row in `knowledge/isa_reference.md` (`SPREAD QRd, Q1,Q2,Q3`, spread from three quadrances) does not describe the implementation. The assembler (`RQQ`) and both VMs use `SPREAD Rd, QRa, QRb`: numerator in `R[d]`, denominator in `R[(d+1) mod 26]`. See `docs/isa/ISA_SPREAD_CLARIFICATION_2026-10-25.md` and `research/sim_cap1_spread/GRAM_V1_CONTRACT_FROZEN.md`. A zero operand Gram quadrance refuses with `DEGENERATE_METRIC` **before** representability is checked.

**Existing C++ VM test profile:** `OK`, `DEGENERATE_METRIC`, and `OVERFLOW` (checked against final signed-32-bit coefficient bounds). The reported 4,022 cases comprised 1,253 OK, 2,761 OVERFLOW, and 8 DEGENERATE. Python's unbounded arithmetic and the C++ bounded profile must not be described as identical.

### 4.3 Legacy dot

`legacy_dot(v,w)=Σvᵢwᵢ` is retained as a historical operator name, but **must not be presented as the qualified intrinsic Quadray Gram metric**. The source matrix records a spread self-test of `8/9` for a representative direction under the legacy semantics. A metric qualification should specify the intended geometric axioms, not merely the existence of a scalar product.

### 4.4 Pell transformations

Multiplication by `2+√3` preserves the Pell-type indefinite form `x²−3y²` in its corresponding representation. It does **not** preserve the Quadray Euclidean quadrance used elsewhere: a FIELD-0 witness changes `Q=24` to `Q=24(7+4√3)`.

**Actual software operand form (O6/D1-A, source-checked).** The historical row in `knowledge/isa_reference.md` is `QROT Rd, Rs, n` with `R[d] = R[s] × (2+√3)ⁿ` (scalar registers, exponent operand). The Python VM (`software/spu_vm.py`, `OPCODES["QROT"]`) and the C++ VM (`software/vm/spu_vm.cpp`, `case 0x11`) instead implement `QROT QRn`: one in-place step on Quadray register `n = R1 mod 13`, no exponent. The assembler accepts `QROT QRd [, Rs]` and encodes the optional second operand in `R2`, which both VMs ignore. Each component is multiplied by `(2+√3)` through `rotate_phi()` and the result is then passed through `normalize()` (common-offset removal). The Python VM additionally sets the register's φ-plane tag to `PHI_UNTAGGED`. These are two incompatible contracts; neither is ratified here.

**QROT-1 characterization** (findings: [`ISA_V02_QROT1_FINDINGS.md`](ISA_V02_QROT1_FINDINGS.md); reproduce with `python3 -I tools/qrot1_repro.py [--cpp]`; analysed on the `19d652a` tree, executable sources identical to public RC2 `b063280`). For **untagged** Quadray components, `QROT` is `normalize(u·v)` with `u = 2+√3`. On gauge classes this is a bijective similarity: quadrance and the Gram form scale by `u² = 7+4√3` (`Q(QROT v) = (7+4√3)·Q(v)`; FIELD-0: Q 24 → `24(7+4√3)`). Spread is preserved (numerator and denominator both scale by `u⁴`), and the field norm of the quadrance is preserved because `N(u)=1`. It is **not** a Euclidean isometry, and quadrance is not preserved; the source comments saying otherwise (`spu_vm.py`, `spu_quadray.h`) are incorrect and unedited. **Not covered by that contract:** Pell-tagged components (from `LD R,1,0`/`ROT` via `QLOAD`) are replaced by the next `PELL_ORBIT` entry; at step 7 the mantissa wraps and mixed steps scale components unequally, so the similarity property does not hold there. Operand encoding (`R2` ignored), tag effects (Python sets `PHI_UNTAGGED`, C++ has no tags), bounded-profile refusal (C++ `int32`, atomic refusal) and a C++ end-of-run display abort remain unresolved. SPU-4's `QROT` (opcode `0x45`, Q8.8 circulant ALU) is a different, profile-specific operation and is not evidence for ISA-A `QROT`. Normative disposition: **HOLD**; the preference for the implemented one-step in-place form stays a provisional owner direction.

**PROPOSED:** describe the operation in future documentation as a **Pell unit dilation** (uniform scaling of every component by the unit `u=2+√3`; a similarity, not an isometry), not an unqualified Euclidean `QROT` isometry. In the (embedding, conjugate) plane it acts as `diag(u, 1/u)`, which is why "boost" is sometimes used; that wording is avoided here to prevent a Lorentz-boost reading. Existing executable names remain unchanged until separately reviewed. Whether to rename or replace the relevant instruction is **UNRESOLVED**.

### 4.5 Icosian / E₈ bilinear form

ICOS-0 uses a quaternionic dot product `dot(x,y)=a+bφ`, and the rational-valued form:

\[
B_E(x,y)=2(a+b)=2\operatorname{Tr}(\lambda\,\mathrm{dot}(x,y)),
\quad \lambda=(5+\sqrt5)/10.
\]

The oracle constructs 240 roots of squared `B_E`-norm 2, checks root products/reflections, and verifies an even unimodular rank-eight lattice via its stated argument. Its reflection formula is `s_r(x)=x−B_E(x,r)r` for normalized roots. This section describes **software-verified mathematics**, not a present hardware instruction.

## 5. Execution profiles and bounded behavior

A conforming profile description shall enumerate: register types and encodings; accepted coefficient/denominator ranges; arithmetic intermediates and their required bounds; normalization rules; success and refusal classes; which architectural registers/flags may change; and a conformance suite covering successful, degenerate and out-of-range cases.

| Profile or path | Boundedness | What is presently supported by evidence | Required caution |
|---|---|---|---|
| Python reference VM | Generally unbounded host integer/Fraction arithmetic for cited operations | Exact oracle-style results | No implied finite-width overflow parity. |
| C++ VM Gram v1 | Checked final signed-32-bit coefficient result | Gram-specific success/degenerate/overflow cases | Do not extrapolate to all instructions or intermediate datapaths. |
| Surd CPU/bank | Signed-64 coefficient fields and positive unsigned-64 denominator in cited configuration | Dedicated status semantics and canonicalization functions | Must inspect the exact bank contract for state-write details. |
| A31 | Fixed modular field-size coefficients | Zero-divisor condition and associated flagging in cited work | Exact refusal post-state **not established** in the uploaded matrix. |
| BQ / ICOS | Exact research software, not ISA-register bounded | Mathematical test fixtures | No architectural commitment to fixed width or timing. |

### 5.1 Proposed new atomic-checked profile

**PROPOSED, not inherited automatically:** For a future profile designated `CHECKED_EXACT`, an operation computes a candidate result, checks every specified admissibility condition, and either publishes the complete destination state on success or leaves the designated protected architectural state unchanged on refusal. Only explicitly enumerated diagnostic/status effects are permitted on refusal.

This proposal requires each instruction to specify its fault precedence where multiple conditions apply, whether execution halts/traps, and what happens to counters, flags, program state and ancillary registers. It must not silently rewrite existing C++/Python/RTL behavior. `CHECKED_EXACT` is a **working profile label**, not an assigned binary profile identifier.

### 5.2 Known failure behavior and unknowns

- **Gram v1:** tested refusal categories `DEGENERATE_METRIC` and `OVERFLOW`; the frozen contract protects pre-instruction state other than specified halt/fault reporting. In the Python VM a `DEGENERATE_METRIC` refusal halts the core and records `fault_kind`; halt and fault status are therefore the permitted state effects of this profile's refusal, and any `CHECKED_EXACT` definition must say whether refusal halts.
- **Surd bank:** documented `SSTAT` values include `OK`, `OVERFLOW=2`, `ENGINE_FAULT=3`, and `BAD_ENCODING=4`; the bank's last-status semantics are profile-specific.
- **A31 inverse:** zero-divisor handling associates a `FLAGS.V` condition; exact destination and ancillary state effects remain **UNRESOLVED** here. RTL source (`spu13_fp4_inverter.v`) shows the zero-norm path raising `flags_v` and `done` without writing the `inv0..3` outputs; whether consumers gate those stale values is not established. The inverter checks one norm; whether that detects every non-invertible element of the split algebra is an open mathematical audit (HOLD, not started).
- **BQ/ICOS:** no finite-width refusal contract exists yet; software exactness is not evidence for one.

## 6. Instruction vocabulary and status

This document is a **semantic architecture draft**, not a replacement for the frozen opcode enumeration in `knowledge/isa_reference.md` and the implementation matrix. The following table is deliberately limited to instructions/operations with directly cited status in the source matrix.

| Operation | Existing encoding | Domain/metric | Present designation | v0.2 action |
|---|---|---|---|---|
| Gram v1 `SPREAD` | `0x15` (profile-specific) | Quadray, `B_Q` | Implemented/tested in software VM | Retain; propose Gram semantics for a new explicit v0.2 geometry profile. |
| `SNORM` | Refer to existing ISA reference | Surd bank | Implemented, profile-specific | Carry forward without redefining encoding/behavior. |
| Surd arithmetic / conversions | Refer to existing ISA reference | SURD3 | Existing bank/RTL profiles | Record exact width/status per profile. |
| Pell `ROT`/`QROT` | `ROT 0x04`, `QROT 0x11` | Pell-type indefinite form | Operand-form conflict (§4.4); untagged domain characterized (§4.4); tag path and encoding unresolved | HOLD; no renaming/metric redefinition until review. |
| A31 inverse | **No ISA-A encoding found (O6)**; inverter `flags_v` pin only | A31 modular algebra | Existing RTL unit; not an instruction | Refusal post-state audit and zero-divisor coverage audit remain HOLD (§5.2). |
| E₈ root reflection | **No encoding assigned** | ICOS/E8 `B_E` | Oracle-qualified | **Lower first**; no dedicated opcode yet. |
| BQ norm/inverse | **No encoding assigned** | BQ field | Oracle-qualified | Defer fixed-width/ISA inclusion. |

Other current SPU opcodes are **not deleted or renumbered** by omission from this table. A future normative v0.2 specification requires an exhaustive machine-readable opcode inventory checked against the reference tree.

### 6.1 Rule for new native instructions

A proposed opcode must offer a clearly stated reason why its observable contract or measured execution is not better served by competent lowering to existing operations. Candidate reasons include: useful atomic refusal, explicit certified metric semantics, bounded intermediates, or measured substantial reduction in cost. A favorable software operation-count result alone does not prove hardware advantage.

**SFL-0** (Small-Form Lowering and Width Inference) is the proposed separate host-only experiment to test that rule for Gram and lattice operations. Its I0 conventional-CSE, I1 domain-aware lowering, and I2 fused cases require comparable primitive-level schedules and identical refusal semantics. **SFL-0 execution remains HOLD** pending reviewed tolerance, scheduling, sound width analysis, frozen inputs and acceptance definitions.

### 6.2 Proposed common-core vocabulary and extension layering (amendment D1-A)

**PROPOSED, documentation only. No opcode is renumbered, added or removed.** Three layers are distinguished: the **core ISA** (registers, scalar/surd/Quadray operations, control, exactness and refusal), **typed architectural extensions** (named, separately enabled mathematical capabilities) and **execution hardware** (units that implement instructions). An extension is an architectural namespace, not necessarily a hardware sidecar; a hardware unit that merely executes a defined native instruction is not an extension. Profile strings such as `SPU-CORE-0.2 + SURD3 + GRAM` are **illustrative only**; names and definitions are not yet assigned.

Membership is an architectural decision and is **not** inferred from agreement among the specification, Python VM and assembler. The opcode inventory is source-derived evidence (`isa_v02_o6_inventory.json`), not a membership ruling. A core *vocabulary* candidate is not a claim of RTL support: the active RTL core implements an explicit subset (see `ISA_CONFORMANCE_2026-10-10.md`).

| Family | Opcodes (ISA-A) | Proposed treatment | Status |
|---|---|---|---|
| Scalar | `LD ADD SUB MUL ROT LOG` (`0x00–0x05`) | Core candidate | Spec/VM/assembler present; RTL core scalar execution not established |
| Control | `JMP HALT CALL RET NOP` (`0x06 0x08 0x20 0x21 0xFF`) | Core candidate | `CALL`/`RET` encodings frozen 2026-10-09 |
| `SNAP` | `0x07` | **HOLD**, see §6.5 | VM stability scan vs spec FLAGS read |
| Quadray | `QADD QNORM QLOAD QLOG QSUB QLDI DELTA MIN4 QREAD` | Core candidate | `MIN4` absent from C++ VM |
| `QROT` | `0x11` | **HOLD**, see §4.4 | Operand-form conflict; untagged similarity established, tag path HOLD |
| Rotation/geometry | `ROTC` (`0x1C`), `SPREAD` (`0x15`), `HEX` (`0x16`), `EQUIL IDNT JINV ANNE` | Core candidate | `SPREAD` metric profile per O1 |
| `REGEN` | `0x09` | Core candidate | Testbench-verified RTL; no silicon entry in the ledger |
| `POLY_STEP` | `0xE0` | Core candidate, **encoding candidate only**, see §6.4 | Semantic blocker |
| Surd extension | `0x70–0x77` | Typed extension (`ENABLE_SURD_CPU`, default 0) | Not in either VM; in assembler and RTL |
| IROTC extension | `0xD6–0xD8` | Typed extension (`ENABLE_IROTC`, default 0) | Not in C++ VM |
| SOM / SOM_TRAIN | `0x2A 0x2B` | Extension profile, **core membership unresolved** | See §6.3 |
| RPLU2 | `0x2A` and config path | Extension profile | See §6.3 |
| Phinary / legacy poly | `PHADD PHCFG` (`0x30 0x31`), `RATIO_CMP` (`0x61`) | Core membership unresolved | `PHADD` may expose reusable exact arithmetic; judged by semantics, not origin |
| Lucas, Neuro, SU3 | `0xD0–0xD5`, `0xE0–0xE3`, `0xE8–0xEB` | **Legacy experimental** extensions, outside the common core | See §6.3 |
| `JSCR`, `NSA` | `0x48`, `0x4C 0x4D` | Implementation extensions | See §6.3 |

**Evidence is preserved, not reclassified.** `docs/hardware_evidence.md` contains entries for Lucas (§3.2e, §3.2e.1, §3.2e.2, §3.2e.7), SU3 (§3.2e.5, §3.2e.6), the Neuro SPI probe (§3.2d), RPLU2 (§3.2c, §3.2e.4, §3.2f) and SOM (§2.6). Classifying a family as an extension neither strengthens nor weakens those entries; this document restates none of them. The ledger has no entry for `JSCR`, `NSA` or `POLY_STEP`.

### 6.3 Extension profiles and reachability (D1 active-decode audit)

"Reachable" means decodable in at least one in-tree build configuration (sources only; external configurations and board qualification were not evaluated). Source locations are in [`ISA_V02_O6_FINDINGS.md`](ISA_V02_O6_FINDINGS.md) §D1.

| Opcode | Owner(s) and enabling conditions | Collision | Classification |
|---|---|---|---|
| `0x2A` as **SOM** (classify) | `spu13_core.v`, `ENABLE_CORE_SOM`, and not (`ENABLE_CORE_RPLU_V2` and `..._PIPELINE`) | RPLU2 start on the same value | Extension profile "SOM"; core membership **UNRESOLVED** |
| `0x2A` as **RPLU2 start** | `spu13_core.v` when `ENABLE_CORE_RPLU_V2 && ..._PIPELINE`; or the coreless `spu13_rplu2_sidecar` / `..._pade_sidecar` | SOM on the same value | Extension profile "RPLU2" (implementation extension) |
| `0x2B` SOM_TRAIN | `spu13_core.v`, `ENABLE_CORE_SOM` only | none decoded | Extension profile "SOM"; membership **UNRESOLVED** |
| `0xE0` | `spu13_core.v`: ungated POLY_STEP handler; `spu13_neuro_sidecar_adapter` (Tang probe only) | `NEURO_CFG`; **not reachable together** in any in-tree top | POLY_STEP: core candidate; `NEURO_CFG`: legacy experimental |
| `0x48` JSCR; `0x4C 0x4D` NSA | `spu13_core.v`, effect only with `ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_EXTENSIONS`; without it `0x48` is acknowledged with no effect | none | Implementation extension |
| `0xD0–0xD5` Lucas | `spu13_lucas_sidecar`, `SPIN="LUCAS"` | none | Legacy experimental |
| `0xE8–0xEB` SU3 | `spu13_su3_sidecar`, `SPIN="SU3"`, `"SU3SHARE"` | none | Legacy experimental |

**Current FULL and INTELLIGENCE configuration (Artix-7 `spu_a7_top.v` spin table).** Both spins set `ENABLE_CORE_SOM = 1`, `ENABLE_CORE_RPLU_V2 = 1` and `..._PIPELINE = 1` (extensions off). In those builds the core decodes `0x2A` as **RPLU2 start**; the legacy SOM launch is suppressed for that opcode, while `0x2B` SOM_TRAIN remains decoded under `ENABLE_CORE_SOM`. So these two spins do not provide legacy `0x2A` SOM classification. Whether the SOM-enabled weights and the RPLU2 pipeline's own SOM stage interact on those spins was not audited. The Colorlight RPLU2 top has SOM off and RPLU2 pipeline on (`0x2A` = RPLU2). Resolution of the two meanings (separate profiles that must not co-enable, or an explicit selector) is a future encoding decision and is not made here.

**Arbitration.** In `spu_a7_top.v` a sidecar that claims an instruction masks it from the core (`core_inst_valid = spi_inst_valid && !lucas_claimed && !su3_claimed && !rplu2_sidecar_claimed`). The Neuro adapter is instantiated only in the Tang probe and has no such arbiter alongside a core.

**Board-qualification limits.** `JSCR`/`NSA` are enabled only by two testbenches (`spu13_core_jscr_tb.v`, `spu13_core_nsa_handshake_tb.v`); every synthesis target found sets `EXTENSIONS` to 0, and there is no ledger entry. They are **simulation-only**.

### 6.4 `POLY_STEP` encoding candidate and semantic blocker

**Encoding candidate: `0xE0`**, supported by current executable decode: the Python VM's effective table value, the core RTL handler (`spu13_core.v`), and `L_OP_POLY_STEP` in `spu_lithic_l.h`. The specification row (`0x60`) and a shadowed `0x60` entry in the VM dict are legacy. `RATIO_CMP` remains `0x61`. The retained SIM0 review (`SPU13_SOFT_V1_SIM0_REVIEW_2026-10-15.md`) names `POLY_STEP(60)` as rejected `UNSUPPORTED`; `0xE0` is equally unsupported there, so execution behavior is unchanged. Per `ISA_CONFORMANCE_2026-10-10.md`, legacy records must not be translated by opcode value alone. This is a candidate, not an executed or ratified renumbering of the specification.

**UNRESOLVED qualification blocker (semantics).** The Python VM executes `POLY_STEP Rbase, Rx` as a Padé P(x)/Q(x) (4/4, Q32) evaluation with numerator and denominator written to `R[r1]`, `R[r1+1]`. The core RTL handler issues an RPLU Artery write (`sel = 7`, address index from `inst_word[33:24]`) and writes no scalar result. These are different architectural effects; the instruction has no single observable contract.

### 6.5 `SNAP` implemented behavior and the FLAGS contract

Findings: [`ISA_V02_SNAP1_FINDINGS.md`](ISA_V02_SNAP1_FINDINGS.md) (source reading at `dev/next` `6deab30`; executable sources identical to public RC2 `b063280`). Normative `SNAP`/FLAGS semantics: **HOLD**.

**`SNAP` (`0x07`) as implemented.** Both VMs scan scalar registers `R0–R25` for non-zero registers that are not laminar (`a²−3b² ≤ 0`), increment `snap_failures` once per `SNAP` if any fail, print the result, and continue (nonhalting); no scalar or Quadray register is written. The Python VM additionally evaluates its SDF layer on every `SNAP`; an SDF conflict increments `snap_failures` only when the scalar scan found no failure. The C++ VM has no SDF layer. `snap_failures` is shared with `EQUIL`, and a non-zero value makes either VM process exit with code 2 (host behavior). The SPU-13 RTL core has no `SNAP` decode. `SNAP` therefore does **not** mutate registers but **does** update diagnostic state (`snap_failures`, stdout and, in Python, SDF internal state); it is not free of observable side effects. Proposed treatment: a VM-specific diagnostic instruction, the C++ scalar scan as the common behavior and Python scalar scan plus SDF as an extended diagnostic profile.

**Not `SNAP`.** The RTL core's autonomous per-axis stability network (`stability_bits`, `is_janus_point`) is triggered by the TDM sweep, not by an instruction, and is not an implementation of `SNAP`.

**FLAGS is an unresolved architectural proposal.** The 6-bit FLAGS word that `knowledge/isa_reference.md` says is "read via the `SNAP` opcode" (Z, C, V, MISALIGNED, OVERFLOW, INEXACT) is not implemented as a register: neither VM produces one and no SPU-13 RTL FLAGS register was found. The historical bit positions 3–5 collide with `rotc_debug_flags[3:5]` in `spu13_core.v`, which mean "rotation done" markers; the MISALIGNED/OVERFLOW/INEXACT outputs exist only in the tagged rotor core, instantiated in a Tang probe and a testbench but not in `spu13_core`. A v0.2 document must not advertise an architectural FLAGS readout. `FLAGS.V` for A31 is currently unreachable from the instruction set (the inverter drives a `flags_v` pin; its consumer path was not traced and its architectural visibility is **UNRESOLVED**).

**Status classes (proposed vocabulary).** *Architectural state*: registers, PC and other state a named profile defines. *Architectural status*: faults or results observable through specified mechanisms (for example Surd-extension `SSTAT`, implemented and independent). *Implementation diagnostics*: VM `snap_failures` and `fault_kind`, the SPI-exposed `rotc_debug_status`, pins such as `flags_v`, and the tagged rotor fault outputs. These are not interchangeable and are not unified here.

## 7. Conformance and provenance

### 7.1 Reference baseline

The combined integration baseline is:

`6fc6efc951b4e5b898f0ed0f2451c7434953d5ed`

A supplied verification receipt records `COMPLETE`, exit 0, 959 seconds, 261 passed/0 failed, full profile with zero profile skips, and 185/185 Verilog variants passed across 177 files, with zero compile errors or timeouts. It also records both Gram v1 suites, the BQ-0 suite and the ICOS-0 suite passing, integration worktree clean, and master unchanged. Hashes of `result.json`, `stdout.log`, `stderr.log`, `command.txt` and `git_commit` are in that receipt. The detached-job evidence for this run is in the gitignored `build/integration/full_regression/20261026_b`; a durable copy of its terminal marker, exit status, source identity, summary and log hashes is kept outside git in `spu-archive/active-checkout-snapshot-20261026/receipts/20261026_b`.

**Interpretation:** this qualifies the tested source regression at that exact commit. It does not verify all eventual v0.2 semantics, Vivado static timing, ASIC implementation, an external evidence archive, or the correctness of every mathematical claim beyond tested scope.

### 7.2 Minimum conformance model for future named profiles

Every accepted instruction/profile combination should eventually provide:

1. **Exact success cases** with reference outputs, including representative and boundary operands.
2. **Exact refusal cases**, including reason and all permitted/forbidden state effects.
3. **Independent mathematical identities** or differential oracles where available.
4. **Mutation controls** capable of detecting at least one plausible violation of each critical invariant.
5. **Profile-specific width tests** (including signed extrema and intermediates), not only mathematical-oracle agreement.
6. **Frozen revision and evidence identity**: commit, command, execution environment, result receipt and hashes.

Passing one profile does not confer conformance on another. A separately specified HDL/synthesis test is necessary to qualify RTL behavior, and timing requires its own physically meaningful analysis.

## 8. Compatibility and evolution policy

1. Existing profile-specific semantics and opcodes remain authoritative unless superseded by a separately approved normative specification.
2. New geometric defaults must be **explicitly named**, not silently substituted for historical `legacy_dot` or other operations.
3. A new domain is not included in a hardware profile until representation bounds, refusal behavior, and conformance fixtures have been qualified.
4. Source baselines and research results may evolve independently. ISA v0.2 documentation should reference immutable commits and identify its own revision.
5. Research experiments (AGS-7, BQ-0, ICOS-0, Golden Core, ARCH-X2, QCG-0) retain their own scope/authorization; this document grants none of them implementation or execution GO.

## 9. Open decisions before normative v0.2

| ID | Decision | Current recommendation / status |
|---|---|---|
| **O1** | Which named profile owns Gram-default spread? | **PROPOSED:** new v0.2 geometry profile; legacy remains explicit. Profile name/compatibility mapping unresolved. |
| **O2** | How is Quadray geometric gauge equality exposed? | **PROPOSED:** value equality is gauge-based, raw equality component-based. Gauge canonicalization algorithm and encoding unresolved. |
| **O3** | How to document/name Pell `QROT`? | **PROPOSED:** Pell boost or qualified similarity; frozen instruction naming unchanged pending review. Operand-form conflict now recorded (see O11). |
| **O4** | Are BQ and ICOS fixed-width operations in initial v0.2? | **PROPOSED:** no; retain as oracle-backed research fixtures. |
| **O5** | Which implemented profiles guarantee atomic refusal? | **UNRESOLVED** pending per-profile state audits; proposed new checked profile only. |
| **O6** | Exhaustive opcode table, encodings and machine-state model? | Source-derived inventory exists (`isa_v02_o6_inventory.json`, findings in `ISA_V02_O6_FINDINGS.md`); discrepancies are recorded, not repaired. Machine-state model and per-opcode fault precedence remain **REQUIRED**. |
| **O7** | Exact integer/fixed-point scaling, normalization, fault precedence and register layouts? | **REQUIRED** per profile before normative release. |
| **O9** | Ownership of `0x2A` (SOM vs RPLU2) and of SOM/SOM_TRAIN core membership | **UNRESOLVED**; reachable collision, see §6.3. FULL/INTELLIGENCE currently resolve to RPLU2. |
| **O10** | `POLY_STEP` canonical encoding and contract | Encoding candidate `0xE0`; VM/RTL semantic blocker open (§6.4). Spec amendment of the row not executed. |
| **O11** | `QROT` normative form and preserved quantity | Implemented in-place one-step form preferred provisionally; **HOLD**: untagged similarity of ratio `u²` established (§4.4); tag/octave path, operand encoding and bounded refusal unresolved. |
| **O12** | `SNAP` and the FLAGS-word contract | Stability scan preferred provisionally as a VM diagnostic instruction with explicit diagnostic-state side effects; FLAGS is an unresolved proposal, not an implemented register (§6.5, SNAP-1). **HOLD.** |
| **O13** | Common-core membership of `SOM`, `PHADD`, `PHCFG`, `RATIO_CMP`, `MIN4`, `REGEN` | **UNRESOLVED**; decided by semantic qualification (§6.2). |
| **O8** | Instruction-granularity cost evidence? | SFL-0 pending approved experiment; not a prerequisite for documenting existing semantics, but needed before new fused-op adoption. |

## 10. Proposed release gate

A future **normative** ISA v0.2 release should require a frozen, complete opcode and architectural-state inventory; resolution of O1–O7; executable conformance for each advertised profile; compatibility notes from predecessor specifications; a reproducible source baseline and test receipt; and clearly separated hardware qualification evidence. Publication as a **research draft** does not require those gates to be completed, provided the gaps remain conspicuous.

---

## References and source scope

This review draft derives its specific implementation claims from the supplied:

- [`ISA_V0_2_DOMAIN_SEMANTICS_MATRIX_DRAFT.md`](ISA_V0_2_DOMAIN_SEMANTICS_MATRIX_DRAFT.md) (draft domain/metric/profile matrix).
- [`SFL0_CONTRACT_DRAFT.md`](SFL0_CONTRACT_DRAFT.md) (unapproved small-form research contract; not authorized to execute).
- [`ICOS0_FINDINGS.md`](../ICOS0_FINDINGS.md) (software icosian/E₈ oracle findings).
- [`ISA_V02_SNAP1_FINDINGS.md`](ISA_V02_SNAP1_FINDINGS.md) (`SNAP`/FLAGS and status-mechanism characterization, source reading at `6deab30`).
- [`ISA_V02_O6_FINDINGS.md`](ISA_V02_O6_FINDINGS.md) and `isa_v02_o6_inventory.json` (source-derived opcode/state inventory and D1 reachability audit, commit `2cbfa6f`).
- `verification_summary.json` (integration revision and full-regression receipt; kept outside git, see §7.1).

The matrix itself identifies further authoritative repository documents to consult before ratification: `knowledge/isa_reference.md`, `docs/isa/ISA_IMPLEMENTATION_MATRIX.md`, `research/sim_cap1_spread/GRAM_V1_CONTRACT_FROZEN.md`, FIELD-0/1 and Golden Core findings, and BQ-0 findings. At review (`6fc6efc`) the following claims were checked against those documents: the Gram form and spread formulas, the 4,022-case outcome counts, the `8/9` legacy self-test, the surd-bank widths and `SSTAT` values, the ICOS-0 form and roots, the BQ-0 131-bit scratch figure, and the FIELD-0 Pell witness. Opcode encodings, instruction-format bits, the exhaustive register layout and unspecified state transitions are still not reproduced here and have not been invented (see O6, O7).

**Final draft disposition:** ISA v0.2 **REVIEW DRAFT COMPLETE**; normative ratification and repository publication **NOT AUTHORIZED by this document**.
