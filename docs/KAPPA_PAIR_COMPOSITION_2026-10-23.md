# One Pair-Composition Law: Euclid Turn, Pell Boost, surd5 (2026-10-23)

Status: exploratory, host-only; no RTL simulated or changed; no ISA/QCG-0 change. Script: `python3 software/experiments/kappa_pair_composition.py` (SymPy 1.14 optional for the generic-κ identities; 18 checks, all PASS, ~2 s). The Python models of the RTL come from **reading the source**; the RTL itself was not simulated here (existing testbenches are unchanged).

## Law
(a,b)∘(c,d) = (ac + κbd, ad + bc), matrix R(a,b)=[[a, κb],[b, a]]. Generic-κ symbolic checks: R(a,b)R(c,d)=R((a,b)∘(c,d)); norm N=a²−κb²=det R multiplicative; R maps x²−κy² to N·(x²−κy²) (exact when N=1); commutative, associative (K1–K4). κ=−1 Euclid turn (complex), κ=3 Pell/Q(√3), κ=5 Q(√5).
Ratio u=b/a obeys **u∘u' = (u+u')/(1+κuu')** (K5): κ=−1 is the book's turn law (Ex 9.2); κ>0 is Lorentzian addition with c²=1/κ (set V=√κ·u, K6). So Pell pairs are boosts in units where the light speed is 1/√3, and the rational ratio u=b/a needs no √3; for ε=2+√3, u=1/2<1/√3 and uₙ→1/√3 from below (D6). This is the exact form of the "almost one sign" observation.

## Existing RTL, mapped to the law (all four-product, same pair format)
| Module | Law | How κ is realised | Products | Overflow policy |
|---|---|---|---|---|
| `core/shared/spu_cross_rotor.v:66-73` | κ=3 | `prod_aa + ((prod_bb<<1)+prod_bb)`; bits [43:12] of 64-bit sums | 4 × mult32 | wraps (bit-slice) |
| `math/surd_cpu_products.v:35-36` (used by `spu13_surd_arith.v`) | κ=3 (unaligned path); aligned path is add/sub | `z0+(z1<<<1)+z1` | 5 shared 64-bit products | exact (130-bit) |
| `math/rational_surd5_mul.v:34-36` (used by `laminar_node.v`) | κ=5 | `p1p2 + q1q2*5` | 4 | saturates (32-bit clamp) |
Models equal the generic law on random inputs (R1–R4); the three overflow behaviours are demonstrated on one input (R5). **One law, three overflow policies** is a real inconsistency to know about, not a defect claim.

## What differs between κ=−1 and κ=3 in hardware terms
1. The combine step on the bb product: shift-add for 3, negate for −1 (`z0−z1`, which the aligned add/sub path already performs), ×5 for surd5. One operand transform on one adder input; multiplier count and pair format are identical.
2. The invariant sign (a²+b² vs a²−3b²): one subtract/add.
3. **State admissibility, not datapath, is the large difference:**
   - κ=3: integer N=1 pairs are exactly ±(2+√3)ⁿ — one generator (D1), closed under ∘ with no scale to track (D4).
   - κ=−1 over Z: the only N=1 pairs are the four Gaussian units (D2); an exact (3,4) turn composes to norms 25ⁿ (D3), so exact length-preserving rotations need a tracked scale or a division (forbidden in RTL; AGENTS §3.1).
   - Over the SPU field Q(√3), Euclidean rotors exist exactly (30°: (√3/2, 1/2), 12th power = identity, D7), but each pair entry is itself a surd: 4 surd products = **16 integer products** per composition vs 4 for a Pell pair.
   - Over F_p (p=2³¹−1) both forms are anisotropic (−1 and 3 non-residues, D5); the A31 null-vector hazard (previous note) arises from the extra √ in the algebra, not from these F_p pairs.

## Answer to the proposal
- **Confirmed:** turn composition and Pell composition are the same multiplication law with different κ; a κ-parameterised kernel would share the four products. The existing κ=3 and κ=5 modules already instantiate it twice.
- **Corrected:** (1) "exact rotation if a²+b²=1" holds over Q but not over Z; integer Euclidean pairs need a tracked norm/scale or division, whereas Pell units close exactly. (2) A Euclidean rotor *over Q(√3)* costs 16 integer products, not 4. So a shared kernel does not make the Euclidean case as cheap as the Pell case. (3) A turn is a direction relationship; a projective pair (a:b) also loses the scale N.
- **Verdict:** do **not** replace the Pell rotor with a turn. Whether to parameterise one kernel over κ (and unify the three overflow policies) is UNRESOLVED: the saving at the multiply level is one operand transform, unmeasured; any decision needs resource/timing data and agreement on one overflow policy.

## Dispositions (owner-confirmed 2026-10-23; closed as a software-and-source audit)
| Proposal | Disposition |
|---|---|
| Replace the Pell rotor with a Wildberger turn | REJECT |
| Separate turn-composition ISA instruction | DO NOT INTRODUCE |
| Generic-κ law as the shared mathematical specification | KEEP |
| One parameterised RTL kernel replacing existing modules | UNRESOLVED |
| Overflow-contract audit at module boundaries (exact / refused / wrapped / saturated; wrap or saturate can break norm identities) | RECOMMEND, deferred to the next CPU/RTL conformance work; no urgency, no module change now |
| FPGA area/timing comparison | DEFER |
Qualifications: Pell closure is a statement about the norm-one **integer** subgroup (±(2+√3)ⁿ; the sign is selected by a>0), not about all Lorentz transformations. The 18 checks support the algebraic correspondences and the source-derived models; they do not establish RTL equivalence or physical efficiency. QCG-0 is untouched.

## Limitations
RTL not simulated (models from source); κ=−1 hardware cost is derived by counting, not built; no timing/area claim; one seed (20261023) for random model checks.
