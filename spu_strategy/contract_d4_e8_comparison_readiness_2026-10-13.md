# D4/E8 comparison readiness contract

```bash
python3 software/tests/test_lattice_comparison_preparation.py
python3 software/tests/test_lattice_symmetry_preparation.py
python3 -m software.research.lattice_comparison.prepare --help
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/lattice_comparison software/tests/test_lattice_comparison_preparation.py spu_strategy/contract_d4_e8_comparison_readiness_2026-10-13.md docs/D4_E8_COMPARISON_READINESS_2026-10-13.md
```

Date: 2026-10-13. Status: DRAFT comparison contract; preparation permitted;
qualification HOLD. No execution budget or campaign command is authorized.
Authority: owner's request to complete comparison preparation. This increment
does not reopen the frozen mathematical milestone or existing D4/SGN campaigns.
Spec author, implementer and auditor: sequential roles, same preparer.
Independent reviewer: UNASSIGNED; algorithmic cross-checks are not that sign-off.

## 1. Files and boundary

Add only `software/research/lattice_comparison/`, its focused test, this contract
and the [readiness report](../docs/D4_E8_COMPARISON_READINESS_2026-10-13.md).
Keep modules at most150 lines. Evidence: a new child of
`build/d4_e8_math_20261013/comparison_readiness_01/`.
Do not modify the original `lattice_symmetry` package, its test, original
contract/report, CPU, RTL, ISA, build flows or qualified evidence.
Verify the original16-source manifest,665 protected sources and265 SGN hashes.
Stop on a changed identity; do not restore another worker's edits automatically.
Surd CPU carry-cluster/backend repair and routed25MHz qualification retain
priority. No FPGA, board, finite-buffer network or hardware job is in scope.

## 2. Comparison domain and endpoints

Retain the original120 fixtures and their ordering unchanged. Each fixture
has doubled coordinates X=2x, literal generator IDs and left-to-right action.
Maximum actual word length is256 for an inverse pair; nominal128 is not the
execution bound. Freeze the serialized fixture hash before qualification.
Fixtures cycle generators and include zero, opposite roots, a root sum and a
17-fold root. They are correctness/cost fixtures, not an application workload
or representative sampling of Weyl group elements. Do not select replacements
after results. Broader nonperiodic words need a separately reviewed increment.

Run four arms on both systems: immediate coordinates, exact rational matrices,
ordinary unreduced generator words, and standalone rational Surds (B=0).
Add an even signed-permutation arm on the60 D4 cases. E8 signed-permutation
results are `NOT_APPLICABLE`, not zero cost, a refusal or a substituted method.
Thus the proposed120-case comparison has540 applicable arm evaluations per
execution condition. This count does not authorize any executions.

Require final materialized doubled vectors equal the independent rational
oracle. Use the same input admission and mathematical domain for every arm.
Report norm and inverse restoration independently. Report three endpoints:
descriptor construction, one-vector end-to-end materialization, and repeated
evaluation on the frozen five vectors for each shared word. Do not compare a
descriptor-only cost with another arm's materialized result.
Immediate coordinates have no retained transformation descriptor; report that
endpoint `NOT_APPLICABLE`. Repeated-vector evaluation must replay its word.

## 3. Conventional D4 baseline

Represent y_i=(-1)^b_i X_{p_i}, with p a permutation of0..3 and b four bits
of even parity. The domain has24*8=192 descriptors. Compose left after right:
p'_i=right.p[left.p[i]], b'_i=left.b[i] XOR right.b[left.p[i]].
The four literal simple reflections agree with the frozen D4 simple roots.
Use12 meaningful descriptor bits: four2-bit indices and four signs. Serialized
payload occupies2 bytes; four padding bits must be zero. Include the common
header below. The information-theoretic8-bit lower bound is not an implemented
rank/unrank representation; no8-bit compression benefit may be reported.
Validation rejects duplicate indices, odd sign parity, bools and malformed
payloads. No dependency on older qualified D4 decision/head implementations.

## 4. Full arithmetic and work schedule

Use an explicit modeled integer primitive interpreter, not CPython timings.
Every primitive contributes one unit to its category and the work total:
type/shape/range/zero/sign/equality comparisons; add; subtract; multiply;
negate; absolute; quotient; remainder; Boolean AND/OR/XOR; shift; indexed read;
indexed write; move; allocate; release; loop condition; loop-index increment.
Count taken operations, including all loop conditions and terminal conditions.
Branch selection itself is not a separate unit. Constants and literals are
declared static storage; reading a constant is an indexed read or move.
Integer width telemetry and counter maintenance belong to the observer and
are excluded. Limit/range checks are interpreter operations and are included.
Do not add semantic Fraction/Surd operation annotations to integer totals.

Freeze these stage boundaries for every arm:

| Stage | Mandatory charged work |
|---|---|
| Admission | Shape/types, scalar ranges, lattice uniform parity, sum modulo4, token ranges/count, descriptor validation |
| Setup | Root/generator table construction or static-table reads, identity initialization, allocation and representation tags |
| Construction | Coordinate updates, matrix composition, word copies/appends or D4 descriptor composition |
| Conversion | X/2 encoding, rational/Surd normalization, block forward/inverse conversion if used, type tags and scale checks |
| Evaluation | Every deferred reflection, dense matrix/vector product or signed-permutation read/sign/write |
| Commit | Exact X restoration, output range/lattice checks, complete result publication and releases |

Dense doubled-coordinate reflection uses n multiply/add pairs for the dot,
remainder4 check, exact quotient4, then n multiply/subtract pairs; no implicit
zero skipping or sparse rewrite. Matrices use dense row-major multiplication,
n products and n additions per cell starting from zero. Build each reflection
matrix I-alpha*alpha^T using normalized rational alpha=A/2. Charge construction
separately from amortized use. Word construction copies tokens without algebraic
reduction; evaluation runs every token. D4 composition uses four indexed
permutation reads and four sign XORs, plus all reads/writes, bounds and loops.
Its evaluation reads four coordinates and conditionally negates each sign.

Rational operations use normalized pairs (a,d), d>0. Add: ae+bd over de;
multiply: ab over de. Subtraction replaces the numerator add with subtract.
Normalize sign, then unsigned Euclid on abs(numerator), denominator. Count every
remainder, zero comparison and state move, including termination. Divide both
by the GCD, checking zero remainder for each quotient. Zero normalizes to0/1.
No implicit pre-cancellation or uncharged Fraction normalization is allowed.
Independent Fraction arithmetic is an output oracle only, outside cost totals.

Surd tuples are (A,B,D), D>0. Add uses AF+CD, BF+ED, DF: five multiplications
and two additions. Multiply uses AC+3BE, AE+BC, DF: six multiplications including
the factor3, two additions. Normalize with gcd(gcd(abs(A),abs(B)),D), charge
both Euclid calls and three checked quotients. Negation and subtraction charge
both coefficient sign operations and the chosen addition schedule. Charge
X/2 admission and 2A/D materialization, B==0 checks, tables and all conversions.
This arm is explicit-denominator software, not AOR-S1 or CPU execution.

## 5. Full logical storage and serialization

Report fixed-profile logical storage, serialized bytes and dynamic minimum
width observations separately. Scalar slots are signed64bits; raw temporaries
are signed256bits. Positive normalized denominators occupy64bits with accepted
range1..2^63-1. Rational slots128bits, Surd slots192bits. No variable bit packing
advantage may be inferred from small fixture values.

Every logical object has a32-bit header: version8, kind8, system8, flags8.
Arrays also have a32-bit element count; matrices additionally have32-bit rows
and32-bit columns. Words have32-bit count and2/3-bit D4/E8 tokens; empty words
still own header/count. D4 payload12bits plus header; top-level wire encoding
is byte-aligned and padding must be zero. Nested arrays own their own headers.
Reject unknown tags, reserved flags, length/shape disagreement and nonzero
padding before accepting storage/cost evidence. This wire decoder is NOT YET
IMPLEMENTED; pack/unpack currently cover only the12-bit D4 payload.

Inventory all live input, descriptors, output, tables, old/new arrays, raw
numerators/denominators, GCD pairs, accumulators, conversion intermediates,
loop indices, stack frames and construction buffers. Control slots are32bits.
List each lifetime and acquire/release event. Compute global simultaneous
peak from live objects; do not sum independent local maxima. Static table bits
are included once per run and reported separately from mutable peak. Retained
storage includes only objects still owned at the endpoint, plus shared tables.
Dynamic widths include unreduced raw arithmetic before normalization; report
normalized numerator/denominator widths separately. Allocator metadata,
Python object/pointer sizes, actual host memory and physical hardware area are
excluded explicitly. Logical headers and modeled control/workspace are included.

## 6. Proposed finite profile and atomic refusal

Candidate profile: scalar64, temporary256, maximum256tokens,2,000,000 charged
primitives per arm per case,1,048,576 simultaneous logical live bits per arm.
Shared table setup receives the same separate2,000,000-unit limit and is reported
as setup cost. Limits reset only at declared boundaries; no counter rollover.
These are proposed research-model limits, not existing CPU architectural limits.
Do not assume all120 cases fit; establish that before freezing the campaign.

Reject unsupported system/arm, malformed input or serialization, width overflow,
inexact quotient, zero denominator, excessive tokens, work or storage exhaustion
with a named reason. Check raw results before normalization to catch cancellation
overflow. Check each committed numerator/coefficient and positive denominator.
Preserve input and prior result; publish no partial vector/descriptor on refusal.
Retain charged prefix, first failing operation and source identity. No truncation,
automatic wider retry, algorithm fallback or silent skip. A valid fixture refusal
halts qualification for review; it is not a comparable successful measurement.
`limits.py` and `rational.py` are preparation witnesses. Complete arm admission,
serialization, storage lifetimes and instrumentation still require implementation.

## 7. Controls, independent review and halt conditions

Retain the original15 mathematical controls as original evidence. Add controls
for D4 duplicate indices/odd parity, reversed composition, malformed tags/padding,
signed minimum negation, raw cancellation overflow, committed denominator
overflow, token257, work exhaustion, simultaneous storage exhaustion, inexact
quotient, zero denominator, partial publication and omitted normalization.
Every control needs a literal expected reason and a mutation that would escape
the checker if that gate were removed. Do not qualify by counting exceptions.

Require an independent reviewer to sign the exact root definitions, scale2,
Cartan Gram determinants4/1, reflection divisibility proof, rank6/8 distinction,
retained-sum metric, composition order, fixture limitations and operation/storage
schedules. Record reviewer identity, independence, dated findings and source
hashes. An algorithmically independent reference or same-author audit does not
replace this review. Freeze all comparison sources only after defects close.

## 8. Literal implementation sequence; no campaign launch

1. Review and approve this proposed domain, schedules and limits.
2. Implement a new instrumented arm adapter, storage/wire checker and independent
   per-tick primitive ledger checker; preserve original preparation sources.
3. Run short literal witnesses for every stage and refusal; reconcile counters
   with hand-derived schedules and exact independent outputs. Do not run120cases.
4. Obtain independent reviewer sign-off and freeze fixtures/source manifest.
5. Draft a detached qualification command and explicit maximum attempts,
   per-attempt wall-clock timeout and cumulative budget. No values are granted
   by this contract; request separate owner authorization before launch.
6. Interpret only a sole durable terminal marker. Preserve failed evidence and
   halt; no implicit repair retry or scope expansion.

Current qualification: NOT RUN. Physical performance and useful-workload
advantage: UNMEASURED. Full repository regression: NOT RUN for this preparation.
