# SPU-BOUND-0 findings

**PASS — BOUNDED DISCOVERY.** Prefix matrices give reusable, sharp independent coefficient ranges for the specified integer rectangles and Pell words. This is exact mathematical evidence for this bounded domain, not a Gen-1 substitution certificate. No RTL, ISA, or hardware claim is made.

## Bounds and independent checks

For prefix matrix M and original rectangle [l₁,h₁] × [l₂,h₂], row i has lower endpoint Σⱼ min(Mᵢⱼlⱼ, Mᵢⱼhⱼ), and upper endpoint Σⱼ max(Mᵢⱼlⱼ, Mᵢⱼhⱼ). Each extremum is attainable because the original coordinates vary independently; two different row extrema need not be jointly attainable. The statement applies to every prefix; the complete correlated output set is generally not a rectangle. Arithmetic is unbounded integer arithmetic.

Exhaustive independently implemented pair multiplication agreed with matrix endpoints at every prefix for all 25, 15, 1, 1 and 1 inputs in the five fixtures, respectively. Direct values also agreed with separately constructed generator powers for every input. Interval bounds contained all enumerated values. In the cancellation box, exact final bounds are [-2,2] for both coefficients; repeated interval propagation gives [-38,38] and [-22,22], losing correlations. For the mixed box, exact final bounds are [-26,26], [-15,15], versus interval [-362,362], [-209,209]. Singleton intervals remain exact.

Z3 independently proves, for the encoded box [-2,2]², the first-step bounds [-10,10] and [-6,6] and U/V reconstruction (both UNSAT for a counterexample). It finds a witness attaining both positive maxima. The plausible but wrong bound |2a+3b|≤2 max(|a|,|b|) fails at (1,1), giving 5>2; the SMT control uses the weaker fixed claim |2a+3b|≤4 and also finds this witness. An incorrect inverse is SAT. These are integer-formula results, not proofs of the implementation, all sequences, machine arithmetic, or RTL. The endpoint argument above is a mathematical derivation; enumeration is finite evidence for its implementation.

## Representation and costs

Widths are minimum signed two's-complement bits; eager temporary width includes the direct formula's products and sums, not all temporaries in matrix or bound computation. Prefix matrix width is stored entries, not products used to calculate them. The report prints exact counts per fixture; they count naive scalar multiplications/additions including zero and unit multiplications, and are analytical counts, not measurements of time, area or power. Matrix construction costs are shown per evaluation; they can be amortized across inputs, unlike per-input eager operations. Endpoint min/max comparisons, exponent accumulation, input iteration, allocation and width checks are excluded from those arithmetic counts. Reported containment checking costs four comparisons per point per prefix; proving an entire rectangle requires the derivation or proof, not merely those observations.

| Fixture | steps; final exponent | eager coefficient / product-and-sum peak | prefix matrix peak | final exponent storage |
|---|---:|---:|---:|---:|
| cancellation box | 2; 0 | 5 / 6 bits | 3 bits | 1 bit |
| mixed box | 4; 2 | 6 / 7 bits | 5 bits | 3 bits |
| contracting direction | 34; 34 | 33 / 34 bits | 66 bits | 7 bits |
| refusal example | 2; 0 | 65 / 66 bits | 3 bits | 1 bit |
| small cancellation | 2; 0 | 3 / 4 bits | 3 bits | 1 bit |

The contracting example starts at U⁻¹⁷(1,0), crosses the small region and ends at U¹⁷(1,0). Its exponent is small, but materializing U³⁴ by this implementation requires 66-bit matrix entries even though every eager coefficient fits 33 signed bits. The exponent representation also retains the original two coefficients; a fused representation retains four matrix entries and the original input; bounds retain the original input rectangle and four current endpoints. Sizes omit object overhead and lifetime/version bookkeeping. Final numerical use still requires reconstruction, potentially with wider products and accumulators. Linear powering is one implementation, not a lower bound, and the counts do not establish a performance advantage.

## Finite-width boundary

For (2⁶³−1,0), U then V has a representable final mathematical pair, but its first exact coefficient needs 65 signed bits. MATHSTATE-0 F3 reports the Gen-1 eager SMUL refusing at the first instruction with status 2 and preserving the destination, while the fused final mathematical value fits. This agrees with the prefix bound and contradicts final-only safety. The mathematical script here executes unbounded continuation after that point; it does not simulate refusal. MATHSTATE-0 F7 also reports equal final tuple, validity and status for one small cancellation while write and retirement events differ. Intermediate reads and status transitions can be observable. Raw arithmetic, normalization/rescue, denominator and invalid-input rules can affect instruction outcomes even when a final mathematical value fits; this experiment does not prove their effects for arbitrary tuples or intermediate widths. Bounds alone do not authorize instruction substitution or establish architectural equivalence.

## Reproduction and limits

Observed HEAD `71adca8`; checkout contained unrelated pre-existing changes. Python 3.10.12, Z3 4.15.5. Each process was limited to 1 GiB virtual memory and 30 seconds; no network, hardware or Vivado used. The initial test had an incorrect hand-entered interval endpoint of ±24; actual propagation and independently enumerated checking indicated ±22, and the expectation was corrected before the successful run.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.spu_bound_0.test_experiment -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.spu_bound_0.experiment)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/spu_bound_0/verification.smt2)
```

All three tests passed; solver outcomes were UNSAT, UNSAT, SAT, SAT, SAT. No random sampling. Gen-1 observations are cited from [MATHSTATE-0](../mathstate_0/FINDINGS.md), not independently rerun or generalized here. No independent architectural qualification or performance assessment is claimed.
