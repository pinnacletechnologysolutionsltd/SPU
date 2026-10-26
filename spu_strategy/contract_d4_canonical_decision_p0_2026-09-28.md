# Engineering Contract Draft: D4 Canonical Decision P0

Date: 2026-09-28  
Contract ID: `contract_d4_canonical_decision_p0_2026-09-28.md`  
Status: **P0 EXACT ORACLE PASS; REPOSITORY GATE PASS**

Roles: spec author — SPU research track; halt-and-flag implementer — future
agent; integration auditor — future agent. This draft authorizes no SOM,
nearest-lattice quantization, RTL, synthesis, route, or hardware action.

## 1. Decision question and proposed file

Can a bounded exact D4 state be mapped to one closed-chamber representative
and deterministic inverse-transform metadata while reproducing declared
invariant labels and stabilizer-compatible equivariant actions exactly?

Oracle files: `software/tests/test_d4_canonical_decision.py` and
`software/tests/d4_canonical_exact.py` (bounded exact operations).
Reference roots: `software/tests/test_d4_reflection_oracle.py`.
Research boundary: `docs/D4_CANONICAL_DECISION_RESEARCH_NOTE.md`.

## 2. Frozen mathematical domain

Use `D4_B={x in Z^4 : -4<=x_i<=4, sum(x_i) even}`. Assert exactly 3,281
states. Use the existing simple roots `(e0-e1,e1-e2,e2-e3,e2+e3)`.
The chosen closed chamber is `c0>=c1>=c2>=abs(c3)`.

Enumerate `W(D4)` as all pairs `(p,b)` where `p` is a permutation of
`(0,1,2,3)` and `b` is a four-bit tuple with even bit sum. Define
`(w x)_i = (-1)^b_i * x[p_i]`. Sort group encodings first by permutation
tuple, then by bit tuple, both lexicographically. Assert exactly 192 unique
maps and verify their action agrees with the simple-reflection oracle on all
states. Use unbounded integer arithmetic.

For each `x`, enumerate its 192 images. Filter images satisfying the closed
chamber inequalities and assert there is exactly **one distinct vector**
`c`. Define `C(x)=c`. Choose `g_x` as the lexicographically first group
encoding satisfying `g_x x=c`. Keep the group encoding, not only a possibly
non-unique reflection word. Derive its inverse exactly from the group table.

## 3. Exact P0 checks

For every state `x` and all 192 group elements `w`:

1. Assert `C(w x)=C(x)`. Precompute the 3,281 canonical values so this is
   629,952 table-lookup checks after enumeration.
2. Assert `C(C(x))=C(x)` and `C(x)` satisfies all four chamber inequalities.
3. Assert `w x` remains in `D4_B` and `||w x||²=||x||²`.
4. Compute distinct orbit images and stabilizer elements and assert
   `|Orb(x)|*|Stab(x)|=192`. Report the orbit-size histogram, boundary
   count, and total number of distinct canonical representatives. Require
   at least one full-size orbit and at least one nontrivial stabilizer.
5. Assert `g_x^-1 C(x)=x` and that the chosen `g_x` is the first valid
   group encoding under the frozen order.

Test a declared invariant label independently of `C`:

```text
L(x) = (sum_i x_i², sorted tuple of |x_i| in descending order).
```

Assert `L(w x)=L(x)` and `L(C(x))=L(x)` for every state and action.

Test one nonconstant equivariant action in `Z^4`:

```text
s(x) = 1 + (sum_i x_i² mod 3)
F(c) = s(c) * c
A(x) = g_x^-1 F(C(x)).
```

Assert `F(c)` is fixed by every element of `Stab(c)`, then assert
`A(w x)=w A(x)` and `A(x)=s(x)*x` for every state and action. As a negative
control, show that `F(0)=e0` is **not** stabilizer-fixed and reject it as a
well-defined equivariant canonical action. A deterministic metadata tie
rule alone is insufficient on chamber walls.

P0 records orbit compression as an observed count of distinct states versus
representatives. It makes no prediction about SOM node count or hardware
cost. Any failed exact identity is `FAIL`, not a tolerated accuracy rate.

## 4. Proposed command and evidence

After separate owner authorization and pre-execution review, run from the
repository root:

```bash
python3 software/tests/test_d4_canonical_decision.py \
  --output build/d4_canonical_decision_p0/oracle_01.json
git diff --check
```

The script must refuse to overwrite evidence, print one `PASS`/`FAIL`
verdict, and record source revision/dirty status, domain and group counts,
all exact-check counts, orbit/stabilizer histogram, canonical count, and
action-control results. If execution is expected to exceed 60 seconds,
freeze a detached-job timeout and attempt budget before launch.

## 4.1 P0 execution result (2026-09-29)

```bash
python3 software/tests/test_d4_canonical_decision.py \
  --output build/d4_canonical_decision_p0/oracle_04.json
git diff --check
```

Both commands exited 0. The final evidence file has SHA-256
`57bf708d0eefdf16865d75bd1daf049f38cc0598aa071011585fc80d47d0e45d`.
Earlier `oracle_01.json` through `oracle_03.json` preserve pre-final evidence;
none was overwritten. The final run recorded source revision
`4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f` with a dirty tree.

The exact domain contains 3,281 states, 192 group maps, and 57 distinct
closed-chamber representatives. It completed 629,952 image/norm/parity/label
checks, 629,952 canonical-invariance/equivariance checks, 13,124 simple-root
oracle comparisons, 3,281 inverse-metadata checks, and 612 stabilizer-action
checks. Orbit sizes and state counts are `1:1, 8:80, 24:96, 32:320, 48:672,
96:1344, 192:768`; stabilizer sizes and state counts are `1:768, 2:1344,
4:672, 6:320, 8:96, 24:80, 192:1`. There are 2,513 boundary states.
`F(0)=e0` failed stabilizer invariance as required. These are exact software
results only; the repository-wide gate and P1 decision comparison have not run.

Repository-gate preflight: launch exactly one detached attempt with a
1,800-second per-attempt and cumulative limit. The fresh evidence path is
`build/d4_canonical_decision_p0/repo_gate/run_01`. The attempt is consumed on
any outcome; do not relaunch without an owner decision. Run:

```bash
tools/run_detached_job.sh \
  --output build/d4_canonical_decision_p0/repo_gate/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

Interpret only exactly one terminal marker and `result.json` in a later
session. P1, SOM, RTL, synthesis, route, and hardware remain outside P0.

**Repository-gate result (2026-09-29): PASS.** The sole detached attempt at
`build/d4_canonical_decision_p0/repo_gate/run_01` has exactly one terminal
marker, `COMPLETE`, and `result.json` reports exit 0 in 880 seconds. This
consumes the frozen attempt. P1 remains governed by its separate contract.

## 5. Stop conditions and later gate

Halt before implementation if the group encoding, chamber sign convention,
boundary metadata rule, or action codomain is ambiguous. Do not change the
domain, roots, or action checks after observing a result. Do not add a SOM
to P0. A passing P0 permits a separately contracted P1 comparison of raw,
augmented, canonicalized SOM, canonicalized non-SOM codebook, and matched
raw decision baselines, split by base representative. No hardware conclusion
follows from P0 alone.
