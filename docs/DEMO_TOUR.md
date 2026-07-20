# Hardware-free demo tour

Run these commands from the repository root after the setup in
[Your first hour with SPU-13](FIRST_HOUR.md). Each demo uses checked-in data and
the Python standard library; no FPGA is required.

## 1. Rational robotics closure

```bash
python3 software/tests/test_rational_robotics.py
```

Expected output:

```text
PASS (104 checks)
```

What it shows: Pell forward/inverse closure, exact F/G/H joint inverses,
forward/inverse kinematic chains, and the six-step rotation trace all return
with a bit-exact zero closure error in the software oracle.

Claim boundary: this is zero arithmetic drift for the tested exact transforms.
It is not a claim about actuator backlash, sensor noise, arbitrary trajectories,
or closed-loop physical robot accuracy. The Tang silicon proof covers the
separate frozen six-step fixture, not every oracle case.

## 2. LUCAS exact arithmetic

```bash
python3 software/tests/test_lucas_mac_oracle.py
```

Expected output includes:

```text
Self-check: (3+5φ)·(3+5φ)⁻¹ = (1, 0)  ✓
ZERO-DRIFT: PASS — 38461 full periods, bit-exact closure every time
COMPOSITE ZERO-DRIFT: PASS — 166666 identity macros, 999996 mixed primitive ops
```

What it shows: `PSCALE`, `PCHIRAL`, `PMUL`, and `PINV` identities over
`Z[φ]/L_521`, including one million-step-scale closure tests, using exact
integers.

Claim boundary: this command proves the software oracle. The four operations
also have recorded Wukong silicon vectors, but this run does not contact that
board and does not turn modular `Z[φ]/L_521` arithmetic into real-number
floating-point arithmetic.

## 3. Checked Iris SOM classification

```bash
python3 tools/iris_som_demo.py
```

Expected output:

```text
Map SHA-256: 3373e851c29450e37fca76281f9ea4dbbdf1b94b34cf1b7bd74f6d83fe8eaa15
Dataset SHA-256: 6f608b71a7317216319b4d27b4d9bc84e6abd734eda7872b71a458569e2656c0
Oracle confusion matrix
                 predicted
true             set  ver  vir
setosa            50    0    0
versicolor         0   48    2
virginica          0    1   49
accuracy: 147/150 (98.0%)
```

What it shows: deterministic regeneration of the checked seven-node map and
exact quadrance-based classification of the checked 150-row Iris corpus.

Claim boundary: `147/150` is an in-sample result for this frozen corpus and
map, not a generalization benchmark or a superiority claim. The optional
hardware run establishes FPGA/oracle decision equivalence; it does not change
the semantic accuracy to 150/150.

## 4. Exact Voronoi decision evidence

```bash
python3 tools/som_voronoi_explain.py software/models/iris_som_v1.json 5100 3500 1400 200
```

Expected output:

```json
{
  "best_quadrance": 58213,
  "exact_tie": false,
  "format": "SPU_SOM_VORONOI_EXPLANATION_V1",
  "inequality": {
    "coefficients": [
      -1082,
      -1056,
      -178,
      -202
    ],
    "lhs": -9503800,
    "meaning": "winner is no farther than runner_up when lhs <= rhs",
    "relation": "<=",
    "rhs": -9263819,
    "slack": 239981
  },
  "label": 0,
  "point": [
    5100,
    3500,
    1400,
    200
  ],
  "runner_up": 5,
  "second_quadrance": 298194,
  "winner": 4
}
```

Expanding the reported coefficients gives the exact winner-versus-runner
inequality:

```text
-1082*x0 - 1056*x1 - 178*x2 - 202*x3 <= -9263819
lhs = -9503800, slack = 239981
```

What it shows: the selected winner is no farther than its runner-up, and the
inequality slack equals the exact quadrance gap.

Claim boundary: this is a faithful local explanation of one BMU decision. It
does not explain why the training process produced the map, establish causal
feature importance, or compare the winner against every node in one printed
inequality.
