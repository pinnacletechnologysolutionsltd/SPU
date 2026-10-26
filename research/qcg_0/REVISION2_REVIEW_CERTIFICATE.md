# QCG-0 Revision 2 independent consistency review

Date: 2026-10-22. Reviewer: `/root/qcg0_fixture_reviewer`, continuing the independent mathematical fixture review, separate from the author and HEX-SOM acceptance context. Author scratch seen: no. **Disposition: REVISE.** The new exact §9.2 fixture values are derived and conditionally certified below; the entire Revision 2 is not consistent enough to freeze. No candidate engines, cost benchmark, P0, source amendment or hardware work occurred.

## Identity, authority and method

Read `REVISION2_REVIEW_CALCULATION_AUTHORIZATION.md` first. Recomputed all seven owner-supplied identities plus the unchanged packet before calculations. All matched. Revision 2 SHA-256 is `fbaf2b5a85615bf6a3ade33c759f2d496596aeff234dcf2ce684f0f25bec4f42`. Independently reversed the supplied unified diff **in memory**, validating every context/current chunk, and obtained the original Revision 1 SHA-256 `b33205e92370a41de5d1b7806f8435057065ea5272ea21866f5700be99025fa8`. Did not read the author's scratch path named in the diff header. All original pinned review artifacts and current input documents remained unchanged; pins were checked again at the end of the calculation.

Read Revision 2, its request and diff against the original certificate. Existing PH5 data were read, not regenerated or reselected. New §9.2 polynomials were freshly built with Fraction convolution, integrated, differentiated, and evaluated. Tangents and curvatures came from coefficient derivatives and Euclidean speed. Exact Bernstein conversion/de Casteljau independently checked positions, derivatives, second derivatives and length at every used parameter. Geometric join truth values were computed from the resulting velocity/tangent/curvature data, separately from generator cross/dot values. The serialized canonical-rational tree was read back and compared exactly. No candidate helper supplied expectations.

One of the new allowance's two calculation invocations was used; exit 0, COMPLETE, no failed invocation or retry. Externally enforced 30 seconds and 1 GiB; cumulative external ceiling consumed 30 of 60 seconds. Reported runtime 0.023638 seconds, maximum RSS 17,928 KiB. Largest serialized rational numerator/denominator 82 bits; fixed tiny-degree operations are far below 4096-bit reduced and 16384-bit raw bounds. Values file 35,957 bytes; all new review outputs remain below 10 MiB. No children, network, devices, installation or services. timeout 9.12, prlimit 2.42.4 and Python 3.14.8 were invoked successfully for version checks before calculation; source was inspected before execution. Full command, source and artifact hashes and transcript paths are in `REVISION2_REVIEW_MANIFEST.json` outside this certificate.

## Findings requiring revision

1. **§11 shared-computation metric is algebraically vacuous.** As written, Sigma = cost(S1)+(cost(S2)−cost(S1))+(cost(S3)−cost(S2)) = cost(S3). With J=cost(S3 joint) and the same cost function, J/Sigma=1 for a nonzero category; zero categories give 0/0. Calling the engines separate does not make repeated occurrences of the same defined quantity different. Minimal correction: define distinct standalone-output cost functions, e.g. Sigma=cost_standalone(position)+cost_standalone(S2-only observables)+cost_standalone(S3-only observables), and J=cost_joint(all S3 observables), with exactly the same outputs and charged work. Freeze scalar/category interpretation and zero-denominator convention. This is a substantive measurement-definition correction, not a fixture correction or permission to choose a favorable metric after results.

2. **§5 and §9.2 do not explicitly gate higher continuity predicates on lower ones.** Equality of endpoint velocities is not C1 continuity across a position gap; equality of curvatures alone is not G2. b9 has equal derivatives/tangents/curvature but a position gap. b7 has the same signed curvature as a but opposite tangent, so it is a cusp, not G2. Minimal correction: expose raw endpoint equality predicates separately; define geometric G1=G0 and tangent equality, C1=G0 and velocity equality, C2=C1 and acceleration equality, G2=G1 and signed-curvature equality, cusp=G0 and opposite tangent. The reference JSON records both layers. Do not silently interpret a raw equality as a geometric join. Under these explicit gates the fixture data are fully determined.

3. **§3 sign-changing h does not generally retrace the path.** Counterexample on an interval containing 0: h=t,U=1,V=t gives x=t²/2−t⁴/4,y=2t³/3. At opposite nonzero t, x agrees but y has opposite signs, so the two branches do not retrace. Minimal correction: retain that the velocity reverses relative to the continued direction and actual tangent changes sign; remove the universal retracing claim. The specific phi_bad composition does retrace and R6 remains correct. Use t−1/2 instead of t if a counterexample strictly inside [0,1] is wanted, with the corresponding translated generator.

4. **§16(a) still says completeness is open, cited and not proved.** This contradicts §3, the closure ledger and §17 item 4. Replace it with the established independent proof status and any genuinely remaining implementation question. §0.1 item 10 can remain as historical owner wording, provided its resolved condition is explicit.

5. **Hand-count wording overstates the below-threshold conclusion.** The 28/27 versus 26/23 arithmetic counts are correct under the stated degree-only Horner and free-doubling-by-shift convention: reductions are 2/28=1/14 and 4/27 respectively, both below 20%. But §13 permits a signal in storage or peak width too. Thus arithmetic hand counts alone do not establish that the *whole Cell A Pareto screen* will land below threshold. Minimal correction: say these two predicted arithmetic categories fall below the threshold; other counted categories remain unmeasured. The shift implementation and costs must be frozen consistently for all arms before execution.

6. **Residual small scope/notation corrections.** The §12 stationary row still says 'T from generator defined'; call it continued direction d, since actual T is expressly refused. In R2, S must be named S_or when h may be negative; otherwise the formula for decreasing phi and negative original h can be misread as composition of the original nonnegative accumulated length. P-CHAIN's parenthetical 'no translation' should say 'no additional gap': placement of zero-origin local segments does require translating them by preceding endpoints. The JSON uses start_b=end_a, with explicit listed gaps added. The initial claim that the drafting calculator was the 'only computation' is now historical and should be qualified in view of the independently recorded review calculations. These do not change the supplied numerical fixture inputs.

## Consistency items that pass

§0.2 pins and quoted PH5 coefficients, endpoints, arc length and curvatures agree with the original artifacts. §3 actual speed |h|g, actual T=sign(h)w²/g and Euclidean signed curvature 2N_raw/(|h|g²) are correct. Stationary points refuse actual tangent/curvature while retaining d wherever g is nonzero. Reversal sign conventions are consistent. R6 correctly distinguishes oriented total 0 from accumulated total 8/3, with the exact piecewise formula and the declared single-polynomial class refusal.

The completeness paragraph faithfully states the independently proved Q[t] result. Coprimeness of C+A,C−A is up to rational units; alpha beta is a rational square; choosing the sign of Z positive on a regular interval makes h positive because U²+V² is positive there. No unproved descent from a real-field representation is used. This proof does not establish h=1 for every rational triple.

Cell A's true numerator is now N_kappa=2N_raw and denominator D_kappa=sigma² for PH5. The old file remains unchanged. New JSON `CellA_adapted_true_curvature_pair` contains all 16 rows with **only index 7 doubled**; indices 0..6 and 8, query order, repeats and flags are preserved. The adapted pair's quotient equals each old explicitly corrected quotient. S3 null final increment is now frozen. Equal caches remain available to all arms; sequential forward differences remain a negative control. Float64 misclassification was removed from arms and P0 controls, and §17 explicitly supersedes its old claim and the old factor-two/sparsity statements.

The E0/E1/E2 class separation is retained. Harmonic order-4 forward/backward residual remains the nonzero operator −127/37748736 times I, with no invented initial state. Finite C4 rotation entries are bounded while accumulated positions need not be; 3-4-5 powers' denominator growth is separate from a ledger-specific refusal stage. A31 is not used as ordered geometry. Generic E0 polynomial-arc claims in §6 must be read together with its explicit sign-changing accumulated-length refusal, rather than granting a single polynomial length across that refusal.

## Exact §9.2 references

The new file `REVISION2_FIXTURE_VALUES.json` is the literal machine-readable reference, schema `QCG0-revision2-independent-values-v1`, with canonical rational pairs and separate discrete metadata. It contains all nine CH1 rows, both CH1 joins, all b1–b9 raw and gated predicates, both loop vectors, and adapted Cell A rows. It does not overwrite or replace the original values.

For CH1, placement gives segment starts (0,0), (2/3,1), (−2/3,4) and preceding lengths 0,4/3,14/3. On the first two segments the chain agrees with PH3 at global parameter u. On segment 2 let t=u−2 and q=t+t²/2; position=(−2/3−3q,4+4q), tangent=(−3/5,4/5), speed=5(1+t), length=14/3+5q. Right-continuous evaluation assigns u=1 to seg1,t=0, u=2 to seg2,t=0 and u=3 to seg2,t=1.

| u | position | unit tangent | speed | accumulated length |
|---|---|---|---|---|
| 0 | (0,0) | (1,0) | 1 | 0 |
| 1/3 | (26/81,1/9) | (4/5,3/5) | 10/9 | 28/81 |
| 2/3 | (46/81,4/9) | (5/13,12/13) | 13/9 | 62/81 |
| 1 | (2/3,1) | (0,1) | 2 | 4/3 |
| 4/3 | (44/81,16/9) | (−7/25,24/25) | 25/9 | 172/81 |
| 3/2 | (3/8,9/4) | (−5/13,12/13) | 13/4 | 21/8 |
| 2 | (−2/3,4) | (−3/5,4/5) | 5 | 14/3 |
| 7/3 | (−11/6,50/9) | (−3/5,4/5) | 20/3 | 119/18 |
| 3 | (−31/6,10) | (−3/5,4/5) | 10 | 73/6 |

At u=1 the join is C2 and G2. At u=2 it is C1/G1 but not C2/G2: acceleration changes from (−4,2) to (−3,4), and curvature from 2/25 to 0. The speed is continuous at both joins; the final segment's h derivative is included.

For b1–b9, a's endpoint velocity is (0,2), acceleration (−2,2), curvature 1/2. All booleans below are **geometric join predicates with the stated lower-order gates**:

| b | G0 | G1 | cusp | C1 | C2 | G2 |
|---|---|---|---|---|---|---|
| b1 | true | true | false | true | false | false |
| b2 | true | true | false | true | true | true |
| b3 | true | true | false | true | false | true |
| b4 | true | true | false | false | false | false |
| b5 | true | true | false | true | true | true |
| b6 | true | false | false | false | false | false |
| b7 | true | false | true | false | false | false |
| b8 | true | false | false | false | false | false |
| b9 | false | false | false | false | false | false |

b1 has right acceleration (2,2), curvature −1/2. b3 has (−2,6), curvature 1/2. b4 has speed 8, curvature 1/16. b7's curvature is 1/2 despite its opposite tangent. b8 has generator cross 1 and nonzero angular mismatch. b9's gap is (1/4,0) while every raw tangent/velocity/acceleration/curvature equality with b2 remains true; geometric continuity must not survive the gap.

L0's reversed second generator is (t−1,1), h=1: residual (0,0), total length 8/3. L1 multiplies the reversed displacement by 1000001/1000000, so its residual is **(−1/1500000,−1/1000000)**, nonclosed, with total length 2000001/750000. It is a vector residual, not an invented scalar norm or the old undefined 10^−6 loop residual.

The chain/join/loop numbers are exact mathematical references under the stated placement and gated-predicate interpretation. Their derivation does not resolve the measurement-definition defects, fix the cost ledger or establish atomic implementation refusal. Original certificate/values/manifest, all author documents and other campaigns remain untouched. Freeze and P0 remain HOLD.
