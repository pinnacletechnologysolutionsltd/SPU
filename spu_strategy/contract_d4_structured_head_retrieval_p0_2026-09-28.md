# Engineering Contract: D4 Structured-Head Retrieval P0

Date: 2026-09-28  
Contract ID: `contract_d4_structured_head_retrieval_p0_2026-09-28.md`  
Status: **P0 SOFTWARE AUDIT PASS; RETRIEVAL UTILITY NOT ESTABLISHED**

Roles: Spec author — SPU research track; halt-and-flag implementer — agent;
integration auditor — agent using the exact commands below.

## 1. Decision and scope

Run a software-only exact audit of D4 reflection heads. Determine whether
asymmetric query/key words change rankings after accounting for the selected
coordinates, and report whether those changes are useful against a fixed
full-dimensional nearest-neighbour reference. Compare the same maps with an
independent even signed-permutation implementation. This P0 cannot establish
a D4-specific representational advantage: `W(D4)` *is* the even signed-
permutation group.

Modify only `software/tests/test_d4_structured_head_retrieval.py`, its
single-purpose `software/tests/d4_head_exact.py` helper, this contract, and
the related research note. Do not change RTL, fixtures, existing
D4 oracles, build profiles, or hardware evidence. No chamber fold, training,
synthesis, place-and-route, FPGA programming, or hardware transmission.

## 2. Exact algebraic controls

Use the root order and exact `r_alpha(v)=v-(v dot alpha)alpha` arithmetic from
`software/tests/test_d4_reflection_oracle.py`. A word `(a,b,...)` applies
roots left to right. Use unbounded Python integers; wraparound and floating-
point scoring are excluded.

For full-dimensional Euclidean score, `||wq-wk||²=||q-k||²` for every
shared word. Assert exact score and exact ranking equality, including ties.

For output coordinates `S=(0,1)`, let `T(w)` be the input-coordinate set
mapped into `S` by signed permutation `w`. Assert for every query/key pair:

```text
||select_S(wq)-select_S(wk)||² = sum(j in T(w)) (q_j-k_j)².
```

`T(w)` is the **pulled-back mask**. Using output mask `S` directly as the
input control is wrong whenever `w` permutes coordinates.

For asymmetric words, define `R=w_Q^{-1}w_K` and `T=T(w_Q)`. Assert:

```text
||select_S(w_Q q)-select_S(w_K k)||²
    = sum(j in T) (q_j-(R k)_j)².
```

Record `(T,R)` for every head. `R` alone determines the full-dimensional
score, but a selected-coordinate score also depends on `T`.

## 3. Frozen retrieval domain and heads

Use 625 keys in lexicographic `itertools.product(range(-2,3), repeat=4)`
order. Use 81 queries in lexicographic
`itertools.product((-2,0,2), repeat=4)` order. Exclude the exact query vector
from its candidate-key list, leaving 624 keys per query. Rank by ascending
integer squared distance, breaking ties by the lexicographic key tuple. Use
top-5 sets. The reference is full-dimensional squared Euclidean distance.

Use these word/mask probes, where `()` is identity:

| Probe | `w_Q` | `w_K` | Output `S` |
|---|---|---|---|
| symmetric controls | each of `()`, `(1)`, `(2,1)`, `(0,2,1)` | same as Q | all four |
| selected controls | each of `()`, `(1)`, `(2,1)`, `(0,2,1)` | same as Q | `(0,1)` |
| asymmetric `h0` | `()` | `(0)` | `(0,1)` |
| asymmetric `h1` | `()` | `(1)` | `(0,1)` |
| asymmetric `h2` | `(1)` | `()` | `(0,1)` |
| asymmetric `h3` | `()` | `(2,1)` | `(0,1)` |

The asymmetric set intentionally includes `h1` and `h2`, which share a
relative word but have different pulled-back masks. It tests the need to
record both. A duplicated ranking is a legitimate result.

## 4. Metrics and falsifiers

Implement an independent signed-permutation evaluator using explicit
swap/sign-swap rules. Check its transformed vector and every score against
the formula path. Fail the program on any algebraic, control, or ranking
mismatch.

For each head and its pulled-back-mask control, report top-5 hits against the
full-dimensional reference and top-1 agreement. Also report the number of
queries whose top-5 sets differ between them. For each asymmetric head pair,
report exact complete-
ranking equality count, Spearman rank correlation, and top-5 Jaccard
**similarity**. Spearman uses the deterministic tie-broken rank positions and
the exact rational formula `1 - 6 sum(d_i²)/(n(n²-1))`; report numerator and
denominator, not a rounded pass threshold. Report Jaccard as intersection and
union counts, with `distance=1-similarity` only if separately needed.

Classify algebraic checks separately from empirical outcomes. If every
asymmetric head matches its mask-only control on every query, close this
construction as rank-degenerate on the frozen domain. If rankings differ,
report the exact distinguishing counts and quality; this establishes
non-degeneracy on this domain, not useful attention or hardware advantage.
Do not advance to hardware from diversity alone.

## 5. Exact command and evidence

From the repository root, after pre-execution review, run:

```bash
python3 software/tests/test_d4_structured_head_retrieval.py \
  --output build/d4_structured_heads_p0/summary_01.json
git diff --check
```

The script must refuse to overwrite an existing output. Record dataset
cardinalities, words, masks, `(T,R)` tuples, exact equality counts,
correlations, top-5 overlap and recall, source revision/dirty status, and a
single `PASS` (algebraic audit) or `FAIL` line. A negative diversity finding
is a valid `PASS` audit result and must be reported separately.

The repository-wide gate is not part of this P0 campaign; it needs its own
long-running detached-job authorization under the SPU governance rules.

**P0 result (2026-09-28):** The initial exact audit exited 0 and wrote
`build/d4_structured_heads_p0/summary_01.json`. The same frozen corpus,
words, masks, score, and tie rule were then rerun after adding mask-control
quality fields to the report. The final-code run is
`build/d4_structured_heads_p0/summary_03.json` (SHA-256
`0b12d11f94b752a011fec1f4d30e72e0fe4ccb16f324e8cb5965f1eda1969a29`).
It is byte-identical to the preceding `summary_02.json` report.
The algebraic audit passed: the formula and independent signed-permutation
paths agreed, shared full-dimensional words and pulled-back masks gave exact
score/ranking equality, and the asymmetric `(T,R)` normal form agreed for
every candidate comparison. `git diff --check` passed.

Asymmetric top-5 sets differed from their pulled-back-mask controls on
54, 63, 63, and 81 of 81 queries for `h0..h3`; head-pair top-5 sets differed
on 72–81 queries. This establishes non-degeneracy on the frozen domain.
However, each asymmetric head recovered only 15 of 405 reference top-5
positions, versus 45 of 405 for each corresponding mask-only control.
Top-1 agreement was 0 or 1 of 81. This is a negative retrieval-quality
finding for these fixed words and data, not an attention or hardware result.
The matched signed-permutation implementation was exactly equivalent, as the
group structure predicts. No hardware step is justified by P0 alone.

## 6. Stop conditions

Halt if a claimed algebraic equality fails, if the independent signed-
permutation implementation disagrees, or if the frozen inputs cannot be
reproduced. Do not alter the scoring rule or replace the corpus after seeing
results. Keep complete chamber folding and any bounded reducer in a separate
contract.
