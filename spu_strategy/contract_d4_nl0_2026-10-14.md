# D4-NL-0 Exact Nonlinear Equivariant Operators

```bash
python3 -m unittest software.tests.test_d4_nl0 -v
python3 -m software.research.d4_symmetry.nonlinear_demo --output build/research/d4_nl0/reference_02/result.json
git diff --check -- software/research/d4_symmetry/nonlinear.py software/research/d4_symmetry/nonlinear_demo.py software/tests/test_d4_nl0.py spu_strategy/contract_d4_nl0_2026-10-14.md
```

Date: 2026-10-14. Status: ACTIVE — bounded software-only mathematical
reference. This study does not evaluate a task, learning, latency, energy,
hardware implementation, or replacement for neural-network layers.
The first demo artifact at `reference_01/result.json` is retained but
superseded because its odd-threshold primitive counter omitted conditional
comparisons and selections. The corrected contract and evaluator use
`reference_02`; no artifact is overwritten.

## Objective and scope

Implement and qualify three deterministic integer maps that are nonlinear
and exactly equivariant under the existing 192-element `W(D4)` action. Include
identity and group-action maps as linear controls. The maps operate only on
four-component integer vectors. Do not modify D4-SYM-0, D4-MEM-1,
D4-CYCLE-0, Soul-0, or hardware files.

Use the frozen input domain
`D4_B = {x in Z^4 : -4 <= x_i <= 4, sum(x) even}`, with 3,281 states.
The same domain is preserved by every even signed permutation. Let
`s(x)=sum_i x_i^2` and freeze these maps and parameters:

1. `identity(x)=x`.
2. `group_g(x)=g*x` for each of all 192 `W(D4)` elements.
3. `radial(x)=(1+s(x))*x`.
4. `cubic(x)_i=x_i+x_i^3+x_i*s(x)`.
5. `odd_threshold(x)_i=sign(x_i)*max(abs(x_i)-2, 0)`, with `sign(0)=0`.

The latter three are integer-valued, nonlinear maps. The radial and cubic
maps use fixed integer coefficients; no parameters are learned. The odd
threshold is the symmetry-compatible piecewise control. Do not use generic
componentwise ReLU or `max(Ax+b,Cx+d)` as an equivariant map: such forms do
not commute with signed coordinate changes in general.

## Frozen mathematics and finite-width contract

For every map `F` and all `x in D4_B`, `g in W(D4)`, require
`F(g*x) == g*F(x)`. Calculate the left and right sides by independent
implementations: the test oracle applies descriptor permutations/signs
directly and computes each formula from its definition, without calling the
production equivariance helper.

Also check that for every tested `h` stabilizing `x`, `h*F(x)==F(x)`. This
follows from equivariance (`F(h*x)=h*F(x)`) and is an explicit stabilizer
regression, not an invertibility claim.

For `B=4`, the exact maxima used for width accounting are:

- input coordinate magnitude: `4`;
- `s(x)`: `64` (unsigned 7 bits);
- radial output coordinate magnitude: at most `4*(1+64)=260` (signed 10 bits);
- cubic terms: `|x_i^3|<=64`, `|x_i*s|<=256`, and output magnitude at most
  `4+64+256=324` (signed 10 bits);
- odd-threshold output coordinate magnitude: at most `2` (signed 3 bits).

Use exact unbounded Python integers as the oracle. Report these derived widths;
do not silently wrap or saturate. The evaluator must assert every produced
value is within its stated bound. Intermediate widths must be included in the
report, including the signed `x_i*s` product (10 bits) and signed cubic term
(8 bits). Widths are for this frozen domain and coefficient set only.

## Required verification

1. Verify 192 unique group elements and the frozen domain size of 3,281.
2. For each nonlinear map, each of 3,281 inputs, and each of 192 group
   elements, compare independent-oracle results for exact equivariance
   (629,952 checks per map).
3. Verify identity and all group-action controls, including composition with
   the existing action convention.
4. Check representative nontrivial stabilizers, including the origin and
   `(1,1,2,2)`, and verify stabilizer preservation for each nonlinear map.
5. Verify output and intermediate bounds, and record required signed/unsigned
   widths. No fixed-width overflow implementation is in scope.
6. Report deterministic source-level primitive counts by operation category;
   do not combine heterogeneous operations into a performance score.
7. Run the focused tests and deterministic demo. Refuse to overwrite the
   output artifact.

## Explicit exclusions

No map composition benchmark, prediction task, learned coefficient fitting,
reservoir, recurrent state, cellular automaton, KAN, hyperbolic geometry, E8
invariant, RTL, FPGA, or hardware build is authorized here. A later task-level
study must be separately specified and compare against matched conventional
polynomial and piecewise baselines. Exact equivariance and bounded arithmetic
do not imply useful inference or a hardware advantage.

## Interpretation boundary

Passing this study establishes the exact finite-domain identities and the
reported width/accounting facts for these five maps, inputs, and W(D4)
descriptors. It does not establish general equivariant-network performance,
learnability, invertibility, non-expansiveness, stability under recurrence,
or improved prediction.
