# SFL-0 — Small-Form Lowering and Width Inference (DRAFT — NOT AUTHORIZED TO EXECUTE)
Class A, host-only software, if later authorized. Authorization needed: baselines, domains, width accounting and acceptance criteria below must be reviewed first.
No change to frozen ISA, no RTL, no synthesis, no hardware/timing claim. A negative result (no special instruction needed) is a success.

## Question
Can a small set of exact primitives (exact mul/add/sub in the stated domain, plus explicit refusal checks) express Gram, quadratic and bilinear operations while preserving
mathematical semantics and refusal-state equivalence, without avoidable intermediate width, compared with fused geometric operations?

## Kernels (reuse verified fixtures; no new oracles)
K1 gram_v1 SPREAD on Quadray/Q(√3) — oracle software/tests/gram_v1_oracle.py (4022 cases).  K2 Quadray quadrance/B(v,w).  K3 E8 reflection s_r(x)=x−B(x,r)r and B(x,y) on 8 integer lanes — software/lib/icosian_e8.py + test_icosian_e8.py.  K4 (optional) BQ-0 norm, only to measure width, no fixed-width claim.

## Implementations under identical arithmetic contracts
I0 conventional expression with competent optimization: hand/CSE-minimized (state exactly which CSE and strength-reduction rules; must be at least as good as a careful programmer).
I1 compiler-lowered expression graph with domain-aware width analysis (interval/bit-width propagation per node; state the analysis algorithm and its soundness argument).
I2 candidate fused operations (K1 as one op; K3 as fused bilinear-reflect), defined by their semantics, not their circuits.

## Measurements (exact, deterministic)
M1 counts by type (mul, add/sub, compares, refusal checks). M2 max live intermediate bit width (per node and global). M3 peak live storage (values live at once, schedule fixed and stated).
M4 exact result equality vs oracle AND refusal-state equivalence (same OK/DEGENERATE_METRIC/OVERFLOW class; destination state unchanged on refusal). M5 input-domain bit widths swept (state: e.g. 8/16/32-bit coefficients) with seeded cases.
Hardware cost, timing and area: UNMEASURED and out of scope.

## Acceptance / decision rules (to be frozen at review)
D1 If I0 or I1 matches I2 on M1–M3 within a stated tolerance and M4 holds, conclude: no dedicated instruction needed for that kernel on these grounds.
D2 If I2 is strictly better on width or storage by more than the tolerance, or provides an atomic refusal contract I0/I1 cannot express without extra state, record as justification for native status.
D3 Any M4 mismatch is a defect in the implementation under test, reported before any performance conclusion.
Negative controls: a deliberately width-undersized I1 must fail M4; an oracle-corrupted case must fail.

## To settle before authorization
Tolerance values; schedule model for M3; width-analysis algorithm; seed lists; where outputs live (single result file, no process framework); whether K4 is in scope.
Not touched: ARCH-X2 (independent review), QCG-0 (amendment review), AGS (closed).
