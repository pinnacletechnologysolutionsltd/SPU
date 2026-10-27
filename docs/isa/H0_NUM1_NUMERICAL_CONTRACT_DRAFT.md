# H0-NUM-1 — Numerical semantics for the proposed H0 profile (revision 5)

**Status:** non-normative draft; proposed profile decisions are not implemented or qualified. Numerical ratification and RTL implementation **HOLD**. This revision changes documentation only.
**Baseline:** `dev/next` at `15e9c961b41ebaceb332f8f5f7a744847d76c941`; earlier revisions remain in git history. RTL, VM and C++ sources are unchanged from public RC2 `b063280`.
**Profile:** proposed `SPU-H0-RPLU2-v0.2`; transport and transaction requirements are in [`H0_C1_PROTOCOL_CONTRACT_DRAFT.md`](H0_C1_PROTOCOL_CONTRACT_DRAFT.md). `0x2A` has profile-specific RPLU2 semantics, not the ISA-A VM's SOM instruction semantics.
**Evidence labels:** **Observed** means source reading, unless a preserved simulation is explicitly cited. **Proposed** describes owner-approved H0 behavior that current hardware does not necessarily enforce. **Unresolved** requires a later decision or verification. Host-computed or algebraic examples are not RTL or FPGA conformance evidence.

The owner-approved decisions are canonical lanes 0–12 and zero reserved bits; QLDI's unscaled load; QSUB's independent modulo-2³² subtraction in each half; candidate ROTC angles `{0, 2, 5}`; and the bounded RPLU2 input domain and post-validation 18-bit extraction described in §6. No QSUB overflow or ROTC divisibility refusal is proposed. A valid-transport instruction accepted while READY but noncanonical under this profile completes as **UNSUPPORTED**, with no instruction side effects, under H0-C1. Those checks are not present in the current core.

## 1. State and initialization

Each of 13 QR lanes holds four 64-bit components A, B, C and D, stored as `{Q[31:0], P[31:0]}`: the upper half is the signed 32-bit √3 coefficient and the lower half the signed 32-bit rational coefficient (`hardware/rtl/core/shared/spu_quadray_regfile.v:4-5`). Each half is also a 32-bit bit pattern for the modular operations specified below. Tags are separate state; reset sets them UNTAGGED.

On reset, every lane receives A=`0x00000001_00000000` and B=C=D=`0x00000000_00000000`. Under the register-file encoding the A pattern has Q=1 and P=0, despite its source comment saying “identity A=1”. The VE loader then overwrites lanes 1–12; it does **not** overwrite QR0. At READY, after the complete hydration walk, the source-derived component patterns are:

| QR lane | A | B | C | D |
|---|---|---|---|---|
| 0 | `0x00000001_00000000` | Z | Z | Z |
| 1 | N | Z | Z | P |
| 2 | N | Z | P | Z |
| 3 | N | P | Z | Z |
| 4 | Z | N | Z | P |
| 5 | Z | N | P | Z |
| 6 | Z | Z | N | P |
| 7 | Z | Z | P | N |
| 8 | Z | P | N | Z |
| 9 | Z | P | Z | N |
| 10 | P | N | Z | Z |
| 11 | P | Z | N | Z |
| 12 | P | Z | Z | N |

Here Z=`0x00000000_00000000`, P=`0x00000000_00001000`, N=`0x00000000_FFFFF000`. P and N are the VE loader's Q12 representations of +1 and −1. This is a description of bit patterns and the loader's scale label, not a decision that all QR contents use one uniform scale. The VMs initialize their QR vectors to zero. The conflicting `{P,Q}` comment in the VE loader and the reset A comment require reconciliation with the actual register-file encoding before numerical ratification; profile conformance must test the whole READY state on the target image.

QLDI writes zero Q halves. QSUB and ROTC can propagate or transform nonzero Q halves already present, including those derived from QR0. `qr_commit_*` and `0xAE` are result telemetry; they do not by themselves establish an architectural register write.

## 2. Canonical instruction encoding and outcome

The word is 64 bits with opcode in `[63:56]`. The following are **proposed H0 encodings**, derived from the current execution paths and the owner's zero-reserved-bits decision. They are not yet enforced by the current RTL or frozen as a broader ISA-A encoding. All named lane fields MUST be 0–12; no modulo aliases are canonical.

| Instruction | Used bits | Proposed reserved bits, all zero |
|---|---|---|
| QLDI `0x1D` | destination `[55:48]`; signed immediate bytes A `[39:32]`, B `[31:24]`, C `[23:16]`, D `[15:8]` | `[47:40]`, `[7:0]` |
| QSUB `0x1B` | destination `[55:48]`, lhs `[47:40]`, rhs `[11:8]` | `[39:12]`, `[7:0]` |
| ROTC `0x1C` | destination `[55:48]`, source `[47:40]`, angle `[29:24]` ∈ `{0, 2, 5}` | `[39:30]`, `[23:0]` |
| RPLU2 start `0x2A` | result-telemetry lane label `[55:48]`, QR source `[47:40]` | `[39:0]` |

**Encoding ambiguity:** the proposed zero masks for QSUB's unused P1_A bits, ROTC's field selector and remaining operand bits, and `0x2A`'s non-lane bits narrow behavior that current paths may ignore. In particular the assembler describes ROTC bits `[31:30]` as a field selector while the current core selects the no-fallback rotor path. The H0 classifier and any H0 assembler must agree on these masks before they are ratified. This table does not assert that every unrelated parallel decode ignores those bits.

When READY, the shared classifier accepts a CRC-valid B1 request into the transaction protocol, classifies noncanonical fields or an opcode/angle outside the H0 set as UNSUPPORTED, and emits one terminal outcome without starting any instruction-caused side effect. Before READY or while busy, H0-C1's transport/acceptance rejection rules apply. A supported instruction's arithmetic is not refused solely for QSUB wrap or a thirds-rotation condition. The existing RTL does not yet implement this classification or enforce the masks.

## 3. QLDI (`0x1D`)

**Observed:** `spu13_core.v:1373-1392` sign-extends each 8-bit immediate to the low P half, writes zero to its Q half, clears the destination tag to UNTAGGED, and emits a QR commit. The RTL applies `qr_lane()` to the 8-bit destination and currently ignores `[47:40]` and `[7:0]`. Python and C++ VMs use the same four immediate fields and sign extension.

**Proposed H0:** for a canonical destination, write `(Q,P)=(0,sext32(imm8))` independently to A, B, C and D and set the tag UNTAGGED. The immediate is loaded unscaled; no conversion to VE's Q12 representation is implied. Invalid lane or reserved bits yield UNSUPPORTED as described in §2.

## 4. QSUB (`0x1B`)

**Observed:** the core reads lhs and rhs in sequence, where rhs is `qr_lane(word[11:8])`, and subtracts the two 32-bit halves independently (`spu13_core.v:1259-1264,1342-1369,1564-1571`). There is no carry between halves and no overflow signal. The tag is the existing tag join. For destination and lhs the current core applies modulo 13 to the 8-bit field; for rhs it applies modulo 13 to the low nibble.

The Python VM uses the signed 16-bit P1_B modulo 13 and unbounded integer subtraction; C++ uses unsigned 16-bit P1_B modulo 13 and checked signed-32 subtraction. All three select the same rhs lane for P1_B 0–15, including aliases 13–15; they also agree on other individual encodings, such as 208. They differ for other bit patterns: for `P1_B=0x8000`, Python selects 5, C++ selects 8 and RTL selects 0. Canonical H0 uses only 0–12, regardless of other coincidental agreements.

**Proposed H0:** for each component and each half, `result = (lhs − rhs) mod 2^32`, preserving that 32-bit result pattern; no overflow refusal is raised. Apply the current tag join to canonical source lanes. For example, `0x80000000 − 1` gives `0x7FFFFFFF`, and `0 − 0x80000000` gives `0x80000000`. These are fixed-width H0 semantics, not a claim of equivalence to unbounded ISA-A Python or the checked C++ VM. Source/destination aliasing and atomic writeback require verification.

## 5. ROTC (`0x1C`)

**Observed:** the core takes the angle from `[29:24]`, currently accepts the decode range 0–35 and has a bad-angle path for 36–63. The current core instantiates the rotor with `ENABLE_TDM_FALLBACK=0`; it captures `[31:30]` as a field selector, but the disabled fallback leaves its role in this path to be verified. Historical evidence in [`docs/hardware_evidence.md`](../hardware_evidence.md) §3.0 covers a Wukong ROBOTICS main-core smoke including angles 0–5; §3.2g records a separate Tang 25K probe. Neither qualifies the proposed H0 image.

**Proposed H0:** candidate angles are exactly `{0, 2, 5}`; all others are UNSUPPORTED. On each full 64-bit component, the proposed mappings are:

| Angle | Destination `(A, B, C, D)` |
|---|---|
| 0 | `(A, B, C, D)` |
| 2 | `(A, D, B, C)` |
| 5 | `(A, C, D, B)` |

These are identity/permutations, with no divide-by-three or arithmetic overflow in the mapping. The existing tag rule preserves the source tag for these angles; qualify that rule together with each complete component pattern, including nonzero Q halves and extreme 32-bit patterns. The current source permits more angles; the narrower H0 rule needs classifier implementation.

Angles 1, 3 and 4 remain research evidence, outside initial H0. For their **unbounded mathematical** row numerators, each numerator is divisible by three exactly when `B+C+D ≡ 0 (mod 3)`, separately for P and Q. This divisibility condition alone does not make the present RTL mathematically exact: its preceding 32-bit doubling, negation and sums can wrap before division. For example `B=C=D=2^30` meets the unbounded divisibility condition but wraps in RTL. The RTL's `/3` path truncates toward zero, while the Python VM and `isa_semantics_oracle.py` round to nearest; non-divisible numerators **can**, but need not, yield different rounded outputs. None of these research observations extends the H0 angle set or establishes conformance.

## 6. RPLU2 start (`0x2A`)

**Observed:** with the core RPLU2 pipeline enabled, the instruction selects the source QR lane and starts SOM → BTU → Padé. Each component's P and Q halves are narrowed to their low 18 bits, then interpreted by the SOM as signed 18-bit feature halves (`spu13_core.v:580-594`). Values differing by a multiple of 2^18 in either half can therefore alias. The result bridge emits the four A₃₁ limbs as host telemetry with a lane label; it does **not** write that result into the QR register file. The Python ISA-A VM's `0x2A` is SOM classification with different observable results.

**Proposed H0 (NUM-SOM-3 owner decision):** each of the selected QR lane's eight original signed 32-bit P/Q coefficients MUST be in `[-9457, 9457]`. Validate the full original halves after the selected lane is read and before any SOM start or 18-bit extraction. In-domain values are exactly representable in signed 18 bits; the existing extraction can then be used without changing their values. This supersedes revision 4's proposed unconditional narrowing with no range refusal: an out-of-domain original value is refused even when its low 18 bits alias an in-domain value. QSUB remains separately defined as modular arithmetic.

An accepted canonical `0x2A` with any out-of-domain coefficient completes exactly once as **REFUSED / NUMERIC_DOMAIN**. It starts no SOM, BTU or Padé work, performs no QR write, and publishes no fresh result telemetry or result-valid. A retained earlier payload is historical only and is not associated with this transaction. The semantic reason is host-visible in the transaction record; its encoding is undecided. Pre-acceptance transport/busy rejection, accepted UNSUPPORTED encodings, and A₃₁ arithmetic refusal remain distinct as specified by H0-C1. The existing RTL implements neither this guard nor the required terminal reporting.

For accepted in-domain input the SOM winner is the mathematical minimum of the stated fixed-image weighted quadratic-field distances, with the lowest node index on an exact tie. Both P and Q distance coefficients are signed. A successful `0x2A` reports the subsequent SOM/BTU/Padé result as four limbs and a canonical lane label, not a QR write; SET-N or SET-R identity is part of provenance. A compile-time signedness parameter, legacy unsigned-P by default and explicitly signed-P for H0 RPLU2, is an approved **design direction**, not an implemented feature.

**Bound and evidence:** with four features, the fixed seven nodes and wired feature weight `(P,Q)=(0,1)`, each feature-minus-node coefficient has magnitude at most 9459. Conservative `|P| ≤ 24×9459² = 2147344344` and `0 ≤ Q ≤ 16×9459² = 1431562896` fit signed 32 bits; differences fit signed 18 bits and per-feature products and sums fit signed 36 bits. This is a sufficient box bound, not a maximal bound or a result for other weights, feature counts or configurations. It assumes fixed node weights, correct signed comparison, intact source values and the stated operation ordering; neither the guard nor a complete image has been qualified. The proof does not establish BTU selection, Padé or A₃₁ correctness, refusal propagation, transaction publication, timing or hardware behavior. Directed comparator/BMU fixture evidence and its limitations are in [`ISA_V02_NUMSOM2_FINDINGS.md`](ISA_V02_NUMSOM2_FINDINGS.md).

**Fixed-width SOM oracle specification, still to be implemented and independently checked:**

1. Decode canonical lanes, interpret the original P/Q halves as signed 32-bit and refuse any outside `[-9457, 9457]` before extraction. For in-domain inputs extract the low 18 bits and interpret them as signed 18-bit. Model each feature-minus-weight subtraction at the RTL's 18-bit width.
2. Use the seven fixed-image SOM nodes in `spu_som_weight_bram.v`; the pipeline ties off their training port. For each feature the pipeline wires P-weight 0 and Q-weight 1 (`rplu_pipeline.v`, `spu_som_bmu.v`). Preserve the RTL’s 36-bit signed per-feature products, shifts and sums, then its 32-bit accumulator truncation. The SOM `accum_overflow` output is unconnected in this pipeline; do not assume it is reported or causes refusal. Do not replace these stages with unbounded distance arithmetic.
3. The serial comparator zero-extends the upper P half and sign-extends the lower Q half, while the SOM accumulator emits a signed, 32-bit-truncated P slot (with the wired weights, `6Σdp·dq`). Directed RTL simulation of `spu_som_bmu` reproduces the resulting wrong winner: for A=B=C=−3, D=2 (Q=0) the RTL selects node 4 while the mathematical nearest node is 6, because node 6's P slot `0xFFFFFFFA` is read as a large positive value ([`ISA_V02_NUMSOM1_FINDINGS.md`](ISA_V02_NUMSOM1_FINDINGS.md)). Separately reproduced: 18-bit subtraction wrap, 36-bit product wrap, 32-bit accumulator truncation and input narrowing change the distance itself (MINP, ALIAS_MIN, SQ_WRAP, ACC_4xMIN). **Intended semantics (owner decision):** the winner is the node minimizing the specified quadratic-field distance, with the lowest index winning an exact tie; the comparator's signed/unsigned mismatch is not part of that definition. The approved correction direction is compile-time signed P for H0, defaulting to legacy unsigned P, with weight wiring unchanged; it is not implemented. The owner-selected sufficient domain and its required guard are specified above but remain unimplemented and unqualified. Only the BMU module was simulated; BTU, Padé and hardware behavior were not.
4. Map the selected node to the one-hot BTU row and read the selected row's four configured 32-bit limbs. Apply the **global** five numerator and five denominator A₃₁ coefficients via Horner evaluation and the selected inverter semantics. Kappa is a separate configuration input to coherence reporting; the numerical meaning of its error and of RNS/ECC/stall events remains unresolved in H0-C1 D7.
5. Return the four limb patterns, telemetry lane and success/refusal according to the proposed H0 contract once ratified. The ordinary pipeline currently publishes stale or undefined data with valid on the characterized A₃₁ refusal; A31-R2 reproduces this in directed simulation. H0-C1 requires its repair before qualification.

Independent expected cases must cover zero features, node-centered inputs, candidate ties, 18-bit input aliases and signed boundaries, intermediate subtraction/accumulator boundaries, known A₃₁ multiply/inverse cases, and the characterized zero-divisor witness. Two SOM references are needed: a mathematical oracle (the intended nearest node) used for acceptance, and a bit-exact model of the existing RTL (`hardware/tests/spu13/num_som_1/som_models.py`) kept as a regression reference showing that a repair changes the defective behavior; expected winners must not be assumed from either host model alone. These are candidate checks, not results of a simulation in this task. The existing [`software/lib/rational_som.py`](../../software/lib/rational_som.py) is a potential starting point for an oracle, not established H0 bit-parity; its arithmetic, weighting and ordering must be assessed independently. A mathematically independent A₃₁ calculation should cross-check `software/lib/a31_field.py`, which is itself a behavioral model of the RTL arithmetic chain. The scope of the inverter's zero-divisor detection, noncanonical A₃₁ limbs and every D7 integrity outcome remain qualification blockers.

## 7. SET-N / SET-R requirements

Both manifests must bind the exact image/profile identity, canonical ordered A5 `(selector, material, address, value)` sequence, expected write acknowledgements and final configuration identity. They enumerate the **global** numerator and denominator arrays (five A₃₁ coefficients each), separately configured BTU row limbs needed for the permitted SOM nodes, kappa/validity, and every other runtime-writable input influencing the profile. Fixed SOM node weights and other constants are bound to the image/build identity. Include source, tool and fixture/oracle revision identities and independent expected results.

SET-N is intended to define the ordinary configuration once qualified and representative successful cases. SET-R is identified as a qualification mode and supplies the characterized zero-divisor witness and expected refusal/no-telemetry result. The two are not per-BTU-row coefficient banks. Exact values, image, hashes and expected cases are not yet frozen; changing sets follows the full H0-C1 configuration sequence. Manifest matching establishes what was loaded, not its mathematical correctness.

## 8. Evidence, proposed checks and remaining blockers

| Item | Source-derived distinction and proposed check |
|---|---|
| QLDI / initialization | Test all 13 READY lane patterns, signed immediate boundaries, canonical and rejected encodings, tags, and reset/hydration timing. |
| QSUB | Test canonical lanes 0–12, lhs/destination aliases, independent P/Q halves and signed boundary wraps; reject noncanonical encodings without mutation. |
| ROTC | Test `{0,2,5}` with independently established identity/permutation fixtures, nonzero Q halves, extreme patterns, tags and aliases; classify every other angle UNSUPPORTED. Historical thirds and their rounding/overflow differences remain outside this profile. |
| RPLU2 | Establish the fixed-width end-to-end oracle and compare independently derived cases to the exact image; test each of eight original coefficient positions at −9458, −9457, 9457 and 9458, signed 32-bit extremes and out-of-range aliases; test signed/unsigned comparator modes and legacy default, exact SOM ties, BTU rows, global coefficients, SET-N success, SET-R refusal, telemetry freshness and no QR write. |
| Protocol | Jointly review H0-C1's acceptance, UNSUPPORTED classification, protected-state gating, result-valid and refusal behavior against §2. No host-only canonicality rule is sufficient for the advertised hardware contract. |

The existing assembler lacks an H0-specific `0x2A` RPLU2 encoding; an explicitly profiled encoding and qualified tooling are dependencies, not part of this documentation change.

Qualification tests must require a successful simulator process exit as well as matching expected output; matching logs after a nonzero exit are not a pass. NUM-SOM-2 fixtures do not qualify the complete RPLU2 path.

Numerical qualification remains blocked on implementing and verifying the SOM comparator mode and pre-narrowing guard, H0-specific assembler support, the canonical masks' architectural review; the exact QR representation and READY state; independently established fixtures/oracle and SET-N/SET-R identities; the selected image's RTL and hardware evidence; the A₃₁ refusal propagation repair and its scope; and classification of integrity events. Existing VM/RTL and historical board evidence do not qualify this proposed image. No host-computed vector alone is an RTL, timing or physical-hardware conformance result.
