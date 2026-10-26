# D4/E8 accounting-limit preflight — 2026-10-13

Implementation is halted at a preflight defect in the proposed resource profile.
Qualification remains HOLD; this is a mathematical cost bound, not a campaign
result or a change to CPU hardware limits.

The [limit-review contract](../spu_strategy/contract_d4_e8_accounting_limit_review_2026-10-13.md)
records the arithmetic certificate and proposed correction. Under the frozen
dense rational schedule, each matrix inner-product term costs at least40
primitive operations, including two Euclid normalizations. E8 matrix composition
alone therefore needs at least2,621,440 units for128 tokens and5,242,880 for256.
Both exceed the proposed2,000,000-unit per-arm limit before other required costs.

At least10 existing E8 cases would refuse on the matrix arm for this reason.
The540 applicable arm evaluations represent the same120 cases; they are not
540 independent workloads. No full comparative evaluation has been run.

The minimal correction is to retain the full schedule and fixed fixtures while
deriving conservative work/storage bounds, then review a common finite ceiling.
No replacement number is silently adopted. Reducing the fixture domain or
optimizing away required work would need a separately reviewed contract.

The original mathematical preparation and comparison-readiness files remain
unchanged. The adapter/serialization/ledger implementation has not begun in
this increment. Complete live-storage bounds and independent reviewer sign-off
remain pending. No FPGA work was launched; Surd CPU backend repair retains priority.

Evidence: `build/d4_e8_math_20261013/accounting_limit_preflight_01/`. The general
documentation audit retains its previously recorded unrelated findings; this
increment makes no clean repository-wide or qualified implementation claim.
