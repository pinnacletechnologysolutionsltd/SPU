# D4/E8 primitive-ledger diagnostic execution

```bash
python3 software/tests/test_lattice_drycount.py
python3 -m software.research.lattice_drycount.driver --help
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/lattice_drycount software/tests/test_lattice_drycount.py spu_strategy/contract_d4_e8_ledger_drycount_2026-10-13.md docs/D4_E8_LEDGER_PREPARATION_2026-10-13.md spu_strategy/contract_e8_root_image_proposal_2026-10-13.md
tools/run_detached_job.sh --output build/d4_e8_math_20261013/ledger_diagnostic_01 --timeout 1800 --notify-desktop -- nice -n 10 python3 -m software.research.lattice_drycount.driver --output build/d4_e8_math_20261013/ledger_diagnostic_01/counts --source-manifest build/d4_e8_math_20261013/ledger_preparation_01/source_manifest.json
```

Date: 2026-10-13. Authority: owner explicitly requests the complete frozen-case
ledger dry count, including the256-token E8 matrix workload, without changing
limits or launching qualification. Status: DIAGNOSTIC PREPARATION; qualification
HOLD. One diagnostic invocation,1800-second operational wall-clock guard, no
automatic retry. This is not a qualification budget, acceptance test or limit
ratification. The1800-second guard is independent of modeled primitive units.

## Files and preservation

Add `software/research/lattice_drycount`, its test and new documents only.
Do not alter the original preparation/comparison sources or fixture identities.
Verify the original16-source and subsequent9-source manifests,665 protected
source hashes and265 SGN evidence hashes before and after diagnostic execution.
Keep modules at most150 lines. Freeze new source and snapshot identities under
`build/d4_e8_math_20261013/ledger_preparation_01/` before launch.
No CPU/RTL/ISA edits, hardware builds, physical attempts or board commands.
Backend repair retains priority; run the CPU-only diagnostic at nice10.

## Diagnostic authority versus qualification

Inspect all120 unchanged fixtures and540 applicable arm evaluations, not540
independent workloads. Four general approaches apply to both systems; signed
permutations apply only to D4. No E8 root-image arm is added. Table construction
and descriptor composition retain their separate stages and actual schedule.
Qualification assertions about arbitrary inputs, repeated-run determinism,
finite-resource admission or hardware efficiency remain unestablished.

The proposed scalar64, temporary256 and256-token bounds still reject invalid
arithmetic or admission. Work and storage are observation-only in this authorized
diagnostic: record exceedances of2,000,000 primitives and1,048,576 live bits,
without truncation, substitution or updating either proposed Profile value.
The suggested16-million ceiling is not adopted. Abort on output disagreement,
formula mismatch, invalid scalar width, source drift or an escaped control.
Preserve partial rows and the first failure; no automatic repair/retry.

## Primitive schedule, model version1

`meter` is an explicit host register/array model. Charge each scalar type check,
two bound comparisons, operand reads, integer operation, result write and
result checks. This conservative schedule checks operands on every operation,
including previously admitted inputs; do not delete these checks selectively.
Count indexed array reads/writes, constant moves, allocation/release validity
checks, loop initialization, every loop condition including termination, and
every increment. Observer counter updates, bit telemetry, trace storage and
ownership-catalogue names are excluded. Branch dispatch and instruction addresses
are excluded; branch predicate operations are counted where scheduled.

`exact` uses explicit schoolbook rational pairs and Surd triples, with Euclid
remainder/zero/move work and checked quotients. Rational normalization performs
gcd(a,d); Surd normalization performs gcd(gcd(a,b),d). No CPython Fraction cost
or pre-cancellation is substituted. Negative denominators negate all fields.
Zero is normalized to0/1 or(0,0,1). All raw products are width-checked before
normalization, and normalized fields must fit signed64 with positive denominator.
Static trusted generators are frozen source constants; load their tables with
charged indexed reads/writes. Setup is charged, not inferred from past runs.

Coordinates use dense integer dot and exact quotient4. Retained words copy all
tokens and evaluate every token without reduction. Matrices build rational
reflection tables and left-compose dense matrices, summing from zero without
sparse shortcuts. Surds use B=0 input/root encoding but the full tuple datapath;
subtraction negates both right coefficients then executes the addition schedule.
D4 signed descriptors use the conventional composition rule and conditional
sign negation. Every approach uses the same admission and output lattice checks.

Wire version1 is little-endian. Header bytes: version1, kind, system4/8, flags0.
Arrays have a32-bit count; matrices also have32-bit rows and columns. All scalar
fields are signed64, including positive denominators. Word tokens use2/3bits,
LSB-first with zero final padding; D4 descriptors have12 meaningful payload bits
and four zero padding bits. Reject bad tags, flags, shapes, lengths, canonical
normalization and padding. The observer decoder is independent of the metered
byte schedule; the latter performs actual shifts/masks, byte writes/reads,
signed restoration, word packing/unpacking and denominator/GCD checks.
Observer encode/decode assertions are excluded from primitive totals.

## Storage and endpoints

Own vector/word headers and payloads, root rows, matrices and their row headers,
Surd/rational arrays, input/output wire buffers, descriptor old/new buffers,
normalization workspace and loop controls. Track lifetimes with explicit
allocate/release events; calculate simultaneous global live peak by summing
currently owned slots. Do not sum individual maxima. Matrix wire views own
32-bit index/reference slots; allocator/pointer implementation overhead remains
excluded. Model references outside these explicit views as aliases to owned
arrays, not duplicated scalar storage.

Reserve a dispatch frame with16 temporary256-bit registers and16 control32-bit
slots, a constants object and profile metadata. Helpers reserve explicit fixed
register frames; these are allocated capacity, not dynamic Python object sizes.
Loop frames reserve one32-bit index. Binary exact operators reserve12 temporaries
and4 controls; normalization reserves8/4; Euclid4/2; reflection12/4; dense matrix
composition12/4; matrix/vector evaluation8/4; wire16/8. Frames include32-bit
headers. These fixed reservations are a research model to review, not a proven
minimum workspace or a realizable CPU implementation budget.

Capture stages separately: admission, input wire, setup, setup conversion,
construction, conversion, evaluation and commit. Report cold total, setup total,
case work, peak fixed live bits, retained output bits, raw and normalized widths,
and output serialized bytes. Phase totals expose descriptor construction and
materialization; no descriptor-only cost is compared with a materialized vector.
The diagnostic executes every vector case independently. Repeated-vector setup
amortization may be derived from the five fixed vector groups, not host timings.
No extra or substituted workloads are authorized.

## Independent checks and limits of the ledger claim

`ledger` imports no candidate meter: replay scalar arithmetic, range events,
category/stage counts and allocation lifetimes for captured short witnesses.
Mutants corrupt scalar results, drop a terminal-loop charge, change work or
change peak storage; each must be detected with a specific reason.
Full dry-count rows omit huge per-primitive traces. Each row is checked against
the separate rational reflection oracle and hand-derived formulas:

* Coordinates/deferred words:2nL multiplies andL quotients in evaluation.
* Dense matrix composition:5n^3L integer multiplies and4n^3L normalization
  quotients; arithmetic-only lower bound40n^3L.
* Surd evaluation:22nL multiplies and12nL normalization quotients.

Those checks cannot prove absence of every omitted instrumentation operation.
Independent reviewer sign-off remains PENDING. Costs are exact for the specified
executed register schedule, not measured host instructions, cycles or energy.

## Terminal handling

After LAUNCHED record unit/evidence and end the turn. Interpret results only in
a later invocation with exactly one COMPLETE, FAILED or TIMEOUT marker. Report
per-system/per-arm maximum work and simultaneous storage with witness fixture
IDs. Do not recommend a new common limit until the schedule and actual evidence
have independent review. Full repository/hardware qualification remains NOT RUN.
