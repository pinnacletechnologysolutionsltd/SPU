# Engineering Contract: D4 Structured-Head Candidate Fusion P1

Date: 2026-09-28  
Contract ID: `contract_d4_structured_head_fusion_p1_2026-09-28.md`  
Status: **P1 SOFTWARE AUDIT PASS; FROZEN D4 RETRIEVAL CONSTRUCTION CLOSED**

Roles: spec author — SPU research track; halt-and-flag implementer — agent;
integration auditor — agent running the exact commands below.

## 1. Decision and boundary

Determine whether the four frozen P0 asymmetric heads are complementary
candidate generators despite weak individual retrieval. Do not change the
corpus, queries, head words, output mask, distance, or tie rule frozen in
`contract_d4_structured_head_retrieval_p0_2026-09-28.md`. No transform search,
learning, chamber fold, E8, RTL, synthesis, or hardware work.

The signed-permutation control must have **identical** results to the D4 word
implementation, because both implement the same exact maps. This P1 cannot
establish a D4-specific representational advantage over signed permutations.

## 2. Exact inputs and aggregation

Use the P0 625 keys, 81 queries, self exclusion, four asymmetric head pairs,
four pulled-back-mask controls, integer squared distance, and lexicographic
tie break. For each query and source, obtain four complete rankings. Confirm
the D4 rankings are exactly equal to independently evaluated even signed-
permutation rankings before aggregation.

For each per-head intake `b in (1,2,5,10,20)`, form the union `U_b` of the
first `b` keys from each of four head rankings. Apply four fixed rules:

1. `union`: retain all of `U_b` (at most `4b` candidates).
2. `vote`: retain at most `2b` from `U_b`, ordered by descending number of
   heads contributing a candidate, then ascending sum of its 0-based ranks
   among contributing heads, then lexicographic key.
3. `rrf`: retain at most `2b` from `U_b`, ordered by descending exact
   `sum(1/(rank+1))` over contributing heads, then lexicographic key.
4. `rank_sum`: retain at most `2b` from `U_b`, ordered by ascending sum of
   per-head 0-based ranks with absent rank assigned `b`, then key.

Rerank every retained candidate with the exact full 4D squared distance and
the same lexicographic tie rule. Assert that the number of reference top-5
keys retained equals the number present in the reranked top-5. In this setup,
exact reranking cannot recover a reference neighbour omitted upstream.

## 3. Evidence and decision rule

For every `(source,b,rule)`, record mean/min/max unique candidate count,
reference top-5 hits out of `81*5=405`, and the exact fraction. Report the
D4-minus-mask hit difference and candidate-size difference at each matched
`(b,rule)`. A D4 candidate point is *strictly dominated* if a mask point has
at least as many hits with no more mean candidates; otherwise report the
tradeoff without asserting a win. Signed-permutation values must be exactly
equal to D4 values for every query, rule, and budget.

No target recall is assumed. A result showing more distinct candidates but
lower reference capture is destructive diversity for this frozen task. A
favourable candidate-size/recall point warrants a separate hardware-cost
contract; it does not itself justify RTL or E8. If no favourable point exists,
close this fixed D4 retrieval construction without further hardware work.

## 4. Command and stop conditions

Implement only `software/tests/test_d4_structured_head_fusion.py` and update
this contract and the research note. Run from repository root:

```bash
python3 software/tests/test_d4_structured_head_fusion.py \
  --output build/d4_structured_heads_p1/fusion_01.json
git diff --check
```

The output path must be new; do not overwrite evidence. `PASS` means the
frozen arithmetic and aggregation controls held, regardless of whether
fusion is useful. Halt on any mismatch or input drift. The repository-wide
gate and any long-running campaign require separate authorization.

## 5. P1 result

The command above exited 0 and recorded `PASS` in
`build/d4_structured_heads_p1/fusion_01.json` (SHA-256
`d62cf0834251f9a2626f530a9ac9eea5aa018788da56b7dfecf5ec3fd8e44de5`).
The independent even signed-permutation path matched every D4 ranking and
all 1,620 per-query candidate selections (`81 queries * 5 budgets * 4 rules`).
Exact full-space reranking retained precisely the reference neighbours
already present in the candidate set. `git diff --check` passed.

| Per-head intake | D4 union: mean candidates, reference top-5 hits | Mask union: mean candidates, reference top-5 hits |
|---:|---:|---:|
| 1 | 3.41, 8/405 | 1.89, 15/405 |
| 2 | 7.11, 16/405 | 3.78, 30/405 |
| 5 | 17.30, 37/405 | 9.56, 78/405 |
| 10 | 35.30, 90/405 | 19.56, 168/405 |
| 20 | 68.21, 161/405 | 38.22, 301/405 |

All 20 matched `(intake, rule)` D4 points captured fewer reference neighbours
while using more mean candidates than their mask-only controls. Thus every
D4 point was strictly dominated even before considering other mask budgets.
The four frozen asymmetric D4 heads gave destructive diversity on this
retrieval task. Close this fixed D4 candidate-generation construction; do
not advance it to hardware or E8. This result does not rule out other tasks,
different trained maps, or a separate compact word-encoding study.
