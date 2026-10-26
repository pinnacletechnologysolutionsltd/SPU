# E8 review and amortization accounting preparation

```bash
python3 software/tests/test_e8_workload_preparation.py
python3 -m software.research.e8_workload_preparation.prepare --help
python3 -m software.research.e8_workload_preparation.prepare --output build/e8_root_images_20261013/workload_preparation_02
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/e8_workload_preparation software/tests/test_e8_workload_preparation.py spu_strategy/contract_e8_review_accounting_preparation_2026-10-13.md docs/E8_ROOT_IMAGE_MATHEMATICAL_REVIEW_PACKET_2026-10-13.md
```

Date: 2026-10-13. Authority: owner says continue the separate E8 software track.
Scope: reviewer-ready proof dossier, short accounting kernel and deterministic
cold/warm observer fixture preparation. Status: PREPARATION ONLY.
Independent reviewer: UNASSIGNED / PENDING. Same preparer performs draft,
implementation and evidence reconciliation. No formal review sign-off is implied.

## Immutable boundary

Add only `software/research/e8_workload_preparation/`, its test, this contract
and the [proof/review packet](../docs/E8_ROOT_IMAGE_MATHEMATICAL_REVIEW_PACKET_2026-10-13.md).
Keep Python modules/tests at most150 lines. Preserve the12-source E8 milestone,
16-source original math milestone,9-source comparison,18-source diagnostic,
665 protected sources,265 SGN evidence files and20-file completed diagnostic.
Do not edit those sources, original120 fixtures, qualification limits or FPGA
workflows. The proposed64-million ceiling remains unratified. This does not
add a sixth arm or qualify a new E8 processing element.

## Review packet and proof obligations

Use the exact existing doubled basis S and physical basis B=S/2. Record the
Gram-admission sufficiency argument, E8 lattice-basis index step and equality
of lattice/root automorphisms with W(E8), with primary references. Derive both
composition sides and G-metric inverse. Give the right-descent word order and
inversion-length argument. State which claims depend on trusted context/setup.
Independent reviewer must sign the exact source/context identities and each
argument; a same-author proof dossier or emitted-event replay is not that review.

Bounded coefficient observations: fixed S^-1 has row L1 maximum5 and all
denominators divide4; cached root coefficients have magnitude at most6.
Normalized Cartesian transformations have denominators dividing4 and entries
bounded by1 from orthogonality. For |X_i|<=A, decoded coefficients have |c_i|<=5A.
Raw coefficient multiplication/addition under a normalization-after-each-step
schoolbook rational schedule is bounded conservatively by108A; denominator
products by16. This is a restricted schedule/domain argument to review, not a
finite-width qualifier. Do not apply it to arbitrary Surd/Pell/AOR values.

## Short metered kernel — deliberately incomplete accounting scope

Implement paired Gram admission plus one LEFT update in an isolated adapter.
Keep the frozen reference unchanged. Use the already frozen diagnostic Meter
and independent ledger replay as host-model components; do not change their
limits. This kernel's duplicate check is28 pairwise comparisons, whereas the
reference uses a set; label it a distinct proposed schedule, not measured
frozen-reference work. Trust the previously verified immutable setup context.

Each admission computes36 eight-coordinate dots,36 index additions and36
Gram scaling multiplies:324 scalar multiplies and324 additions. Two admissions
surround the eight reflection-ID lookups. LEFT-update stage reads eight old IDs,
eight table rows and eight table entries:24 indexed reads, not eight total
primitive operations. Charge writes, validation, loops, frames and allocations.
Retain the entire307,680-bit reference context as a shared static live object,
96-bit input/output descriptor objects and explicit register/loop frames.
Report all categories/stages and independent scalar/storage replay. Corrupted
work or peak totals must be rejected. Atomic failure means no caller mutation
or partial returned tuple, not a qualified CPU commit/reset protocol.

Excluded from this short kernel: table build/setup validation, wire identity
parsing, inverse, general/right composition, matrix decoding, materialization,
equality, reduced-word execution and repeated-workload scheduling. A kernel
pass cannot close the complete-accounting gate. Keep all those items pending.

## Prepared cold/warm corpus — no campaign execution

Prepare384 configuration records, with frozen generator/source identities:
clients K in{1,4,16,64}; steps L in{8,32,128,256}; materialization cadence
in{1,4,16,final}; two word families; three ownership regimes. No cross-product
performance run is permitted now. Prospective approaches: eager coordinates,
dense matrices, ordinary words, reduced words and root images. They belong to
a new E8 experiment;1920 prospective configuration/approach evaluations are
not independent workloads or authorized executions.

Every client consumes a deterministic xorshift32 generator word. Fix client
seeds independently of regime/cadence so words and initial vectors match across
conditions. Scrambled words use low3bits; inverse-pair words concatenate a
generated half with its reverse. Vector seeds are separate; vectors are exact
integer combinations of two E8 roots at four fixed magnitude scales. Bound
doubled inputs by2^31. Do not replace vectors or remove cancellations after
observing results. Workload generation/checking is observer work, equally
excluded from all candidate totals.

At tick t, the observable is w_t(initial_vector), with cumulative LEFT action.
Do not feed a materialized output back through the entire retained prefix or
reset descriptors at checkpoints. Include the final observation exactly once
even if cadence exceeds L. Compare matching (tick,client,value) traces.
Eager coordinates update each tick; ordinary words replay the full prefix at
each observation; matrices/root images materialize current cumulative state.
The reduced-word retention policy still needs a reviewed operational schedule;
do not borrow free root-image/matrix state for its reduction/evaluation.

| Regime | Active clients | Setup instances | Peak context instances |
|---|---:|---:|---:|
| cold_serial | 1 | K | 1 |
| private_lockstep | K | K | K |
| shared_lockstep | K | 1 | 1 |

Private versus shared lockstep holds concurrency fixed. Cold serial is a
separate scheduling control; do not attribute its latency differences solely
to sharing. With the current root-image context, K=4 private copies already
need1,230,720 static bits; K=64 needs19,691,520, before any workspace. These are
structural lower bounds, not measured global live peaks. Do not carry the old
comparison's1,048,576-bit proposal into this new domain without review.
Each baseline owns only its necessary tables/caches; do not charge every arm
the full root-image context or hide borrowed reduction tables as checker work.

## Short preview scope and next gate

Run only four L8 previews with K1 or K4, covering per-tick/final observations
and the private/serial inverse-pair control. Check outputs against independent
rational prefix application and conventional reduced-word reconstruction.
These previews use one mathematical reference context; they do not allocate
K private contexts, simulate scheduling costs or measure cold/warm performance.
Prepare the other configurations as metadata only.

Next: obtain independent proof/operator review; instrument all operations and
table initialization; complete ownership/temporary lifetime and bit-growth
accounting; freeze reduced-word retention and equality/serialization policy;
review common work/storage/refusal limits; then define a separately authorized
campaign command with explicit attempt and wall-clock limits. No budget exists
for that campaign now. Qualification HOLD, hardware work excluded, Surd CPU
backend and physical implementation remain the engineering priority.
