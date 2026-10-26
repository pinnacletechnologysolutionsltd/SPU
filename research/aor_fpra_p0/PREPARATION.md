# AOR × FPRA P0 — specification revision 3

2026-10-23. Specification-only correction authorized. **Fixture derivation,
candidate implementation, tests and execution HOLD.** No ISA/simulator/RTL work.
Addresses only the four [Revision 2 findings](REVISION2_SPEC_REVIEW.md).
The reviewed predecessor is preserved byte-for-byte as
[revision 2](PREPARATION_REVIEWED_R2.md), SHA-256
19082a62fc22fa10763975b25d47544b420fda5940d792c46544cfd531f6cc5a.
This specifies one fixed six-cell experiment, not a general graph/FPRA interface.

## 1. Review commands and unchanged workload

```bash
sed -n '1,420p' research/aor_fpra_p0/PREPARATION.md
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- research/aor_fpra_p0/PREPARATION.md
```

Let U=2+sqrt(3), U^-1=2-sqrt(3). Exact pair (a,b) means a+b sqrt(3).
Pair multiplication is (ac+3bd,ad+bc); STEP + maps (a,b) to
(2a+3b,a+2b), STEP - to (2a-3b,2b-a). Norm is a^2-3b^2.
Only the pure subgroup U^k is admitted: k uniquely identifies its value, norm=1.
No arbitrary residual/exponent equality or Pell-membership algorithm is implied.

Initially k1=k2=kr=0, z1=z2=r=U^0, kr=k1+k2. The unchanged tape is 32
STEP(z1,+1) then 32 STEP(z2,-1). Observe after each event, every eighth
event, or only event 64. Reset independently per arm/cadence; rho is 64 divided
by whole-graph observation batches: 1,8,64. No locality sweep. Twelve cases
contain 768 events and 292 nominal observations, excluding controls. Every
successful OBSERVE returns all three expanded pairs in z1,z2,r order, three
norms, equality z1=z2 and the receipt below. Product identity never substitutes
for coefficients of the two nontrivial factors.

## 2. Four fixed arms and update schedule

| Arm | Primary payload | Organization |
|---|---|---|
| A | Three expanded exact pairs | Conventional incremental caching |
| B | Three expanded exact pairs | FPRA-style dependencies |
| C | Three integer Pell exponents | Conventional symbolic DAG/cache |
| D | Three integer Pell exponents | FPRA-style dependencies |

All retain common semantic metadata. C/D payload aliases its exponents; A/B pay
for metadata plus expanded payload. Choosing an expanded row is an experimental
representation restriction, not a claim that conventional software cannot factor.
C is the fully capable conventional factored baseline. All get equal identities,
proof reuse, CSE, incremental product updates and within-case sharing.

Freeze this specialized topological order in **all arms**: changed input, r,
that input's norm certificate, r's norm certificate. A/C invoke direct dependencies;
B/D specialize the same fixed dependent lists/early cutoff to this order. No
runtime queue, graph discovery or artificial scan is imposed on one side.
A/B and C/D scheduling work can therefore be identical by construction: record
SCHEDULE_EQUIVALENT. This P0 cannot establish a benefit of an untested distributed
scheduler. Internal traces need not be identical, but all charged work is reported.

| Operation | A/B | C/D | Common actions |
|---|---|---|---|
| RESET | Import identity pairs | No expanded caches | Initialize metadata, norm proofs; empty ladder |
| STEP | Signed STEP kernel on affected input then r | Update exponents, no expansion | Scratch transition, invalidate changed expansion keys, reevaluate dependencies, atomic commit |
| Norm reevaluation | Reuse subgroup proof | Same proof | Refresh snapshots; norm version unchanged |
| OBSERVE | Fresh primary-pair aliases | Probe/expand z1,z2,r | Freshness, output checks, proofs, equality, receipt, serialization, atomic publication |
| SET_EQUAL / unrelated SET | Controls only | Same | No-op creates no dependent work; unrelated input has no six-cell edges |

A/B expansion entries alias fresh primary pairs after RESET/STEP. C/D hold at
most one expanded pair per cell keyed by its logical version. Changed C/D cells
discard old expansion pairs and invalidate keys at STEP commit. No global value
memo or cross-case reuse. Returning to an old value cannot revive its version
key. Count probes, invalidations and installs, including A/B current-alias upkeep.

## 3. Public semantic versions, freshness and receipts

IDs: z1=0,z2=1,r=2,n1=3,n2=4,nr=5. Parents: (),(),(0,1),(0),(1),(2).
Store generation g, exponent triple, versions v[0..5], parent-version snapshots,
VALID flags and three proof tags. Initial g/versions/snapshot versions are zero;
norms are one. Initialization and proof import are charged, not free caches.

A STEP forms scratch k_target+delta and kr=k1+k2. On admission, increment g,
v[target] and v[2] once; leave other versions unchanged. Refresh r's two parent
versions, the affected norm's parent version and nr's parent version. Two norm
proof reevaluations keep norm versions zero by early cutoff. All logical cells
are VALID/fresh after commit, even with absent C/D expansions. Every admitted
STEP changes its source and r in this subgroup; no expansion is needed to know
that. Return to an earlier value still increments versions; never wrap or reuse.

Control SET_EQUAL(target,current_k) returns OK, changed=false: no g/version,
snapshot or cache change. A different k is OUT_OF_DOMAIN for this operation.
Control-only scalar u has no edges; SET(u,new) changes g/u's version iff its
integer value changes, without graph work. Charge its metadata/storage; u is
not a seventh representation node. It starts at zero with version zero.

Receipt: (g, versions[0..5], snapshots in cell-ID order, fresh,
operation_status, code, stage). Success: OK/null/null. Errors: INVALID or REFUSED
with code/stage, no value tuple. Success fresh is six true flags; unsuccessful
operations have fresh=null rather than claiming uncompleted validation.
No public request counter changes versions or
receipts. Unchanged repeated observations have identical receipts; internal
cache validity is private. The changed=false/true event result is separate from
the common receipt and is present only on successful event operations.

Before STEP/SET_EQUAL and at OBSERVE validate freshness: walk roots 0..5
ascending, depth-first parents in listed order. Each validation invocation starts
with a new empty visited set, including STEP, SET_EQUAL and OBSERVE validation;
release it and its entries on validation return or refusal, before subsequent
operation work. Never reuse it across invocations. Count every visit, set probe and parent-version
comparison, including memo hits. On first visit check tag/VALID, norm proof tag
if applicable, then each snapshot and recursively that parent. Invalid tags/proofs
give INVALID_STATE; a snapshot mismatch gives STALE before expansion. Proof tags
originate only from RESET/admitted STEP. LOAD_PAIR always refuses OUT_OF_DOMAIN,
including alleged/non-Pell/zero inputs; no general membership operation is added.

## 4. Kernel, powering and transaction order

These are algorithm specifications, not executed code. No zero/identity skipping.
Signed STEP temporaries: 2a,3b,new_a,2b,new_b using section 1 formulas.
General pair multiply temporaries: ac,bd,3bd,ad,bc,new_a,new_b, in that order.
Every literal multiplication counts; aliased operands do not skip work.

C/D share one positive ladder per case, initially empty. EXPAND(0) returns an
identity-pair copy without constructing a ladder. Otherwise form n=abs(k) and
m=bit_length(n)-1. If missing, import L0=U. Extend consecutive
Lj=PAIR_MUL(L[j-1],L[j-1]) in ascending j through m, never beyond m.
Initialize accumulator to an identity copy; scan j=0..m ascending. One BIT_TEST
of n at j; if set, PAIR_MUL(acc,Lj), even when acc is identity. No final square.
If k<0, negate accumulator b once after the scan. Identical sharing for C/D.
A/B use this helper only in isolated controls, not nominal observation.

OBSERVE validates freshness first. For cells 0,1,2 in order: probe expansion,
use a fresh alias/hit or EXPAND in a private transaction, then check exported a
followed by b. Once all coefficients pass, read proof-backed norms, compare
k1/k2, assemble receipt and serialize privately. Final COMMIT publishes all
prospective ladder/cache entries and the whole output together. Existing ladder
entries remain read-only. On refusal discard every private addition; restore
the immediately pre-OBSERVE state, including invalid keys from prior STEPs.

STEP, SET_EQUAL and SET(u,new) use the same bounded scratch-then-COMMIT discipline.
Stage every prospective value, generation/version, snapshot, cache change and
successful receipt before reserving the final COMMIT unit. A refusal anywhere,
including denial of COMMIT, leaves all committed fields and caches unchanged.
Every successful SET request emits exactly one charged COMMIT, including an
unchanged SET_EQUAL or unchanged SET(u,current). Such a no-op publishes its
acknowledgment only: it changes no generation, version, snapshot or cache, and
emits no dependent EVAL/INVALIDATE/INSTALL. SET_EQUAL with a different exponent
still refuses OUT_OF_DOMAIN without COMMIT. Diagnostics/attempt costs remain
append-only and are never rolled back. OBSERVE failure never undoes a prior STEP.

## 5. Abstract operations, memory and measurement

Each event has SETUP/EVENT/OBSERVE/CONTROL/REFERENCE phase, case/arm/request ID and a unique
path containing cell/ladder/scan index and temporary/test name. These are abstract
algorithm events, not complete Python/CPU work or physical cycle/energy estimates.

| Counter | One event |
|---|---|
| A | Integer add/subtract, including semantic exponent/version/generation arithmetic |
| M | Integer multiply, including literal 2/3 and squares |
| N | Integer negation/absolute value |
| K | Specified ordered comparison, type/domain/limit test or semantic equality |
| B | Magnitude bit-length query: bits(0)=1; otherwise bit_length(abs(value)) |
| T | Specified bit test/shift; no replacing displayed M with shifts |
| COPY / READ | Logical scalar-slot copy / retained field or constant read |
| VISIT / PROBE | Validation/propagation node visit / cache-or-visited-set lookup |
| INVALIDATE / INSTALL | Expansion-key invalidation / cache-or-ladder publication |
| EVAL / PROOF | Relation reevaluation / subgroup proof import or reuse check |
| COMMIT | Successful transaction publication |
| SERIAL | Output serialization call; report exact UTF-8 bytes |

Use displayed arithmetic order. Proof reuse costs PROOF plus required metadata
reads/checks, not fictitious arithmetic. Each specified validation/domain test
costs K; size checks cost B then K. Count copies/conversions explicitly. The
instrumentation's own counter increments are excluded to avoid recursion.
READ applies to each named retained operand/field access; repeated access counts
again. Private scratch reads are not retained READ events. Each norm early-cutoff
compares its proof-backed value to the stored value with one K.
Host loop/index dispatch, allocation internals and decimal formatting instructions
are not modeled: disclose them and include their elapsed time/allocation.
No gcd/division is needed for integral values; report normalization count zero.

Count attempted work and discarded private work. Candidate times exclude the
independent oracle/checker; record checker costs separately inside the same outer
allowance. Report setup/event/observe times, whole-process elapsed, RSS, host
heap sizes and output bytes. No arbitrary combined efficiency score.

Retained logical bits: sum 1+bits(value) per stored integer slot, two bits per
status, one per Boolean/valid flag, plus actual stored tag/ID/key bytes times
eight. The later result schema must enumerate fields. Never deduplicate integer
interning. Explicit aliases only: A/B expansion to primary pairs; C/D payload to
semantic exponent slots; observation views/hits to existing immutable objects.
Count underlying objects once and reference/key fields separately. Literal
constants form a charged retained pool. No other aliases are assumed.

At every primitive boundary record peak retained bits plus private live bits.
Allocate a result before releasing overwritten operands. Release each temporary
immediately after its last listed use; release helper scratch on return. Keep
prospective ladder/cache/pairs and the private serialization buffer until commit
or refusal. Release replaced objects at commit, private work at refusal. Logical
object peaks and host RSS/heap peaks are separate, including failed observations.

### Fixed operand loads, transfers and release order

This schedule applies identically whenever arms perform the same operation.
A load from a retained scalar field/constant is one READ followed by one COPY
into a new private slot. Loading an already-private argument is one COPY and
no retained READ. Repeated argument positions load separately even if aliased.
Never reread a retained operand inside a kernel after these entry loads. A new
arithmetic result occupies its own private slot without an additional COPY;
ownership transfer of a completed result is not a duplicate scalar copy.

| Helper | Entry loads, in order | Last-use release schedule |
|---|---|---|
| Signed STEP | a, b, delta, constants 1, 2, 3 | Compare delta to 1 once (K), select the already-admitted sign, release delta/1; form and check the existing five temporaries. Release 3 after 3b, b/2 after 2b, a after new_b; release 2a/3b after new_a checks, 2b after new_b checks. Return new_a/new_b by ownership transfer. |
| PAIR_MUL | a, b, c, d, constant 3 | Form/check the existing seven temporaries. Release bd/3 after 3bd; a/d after ad; b/c after bc; ac/3bd after new_a checks; ad/bc after new_b checks. Transfer the two result slots on return. |
| EXPAND | k, constants 0, 1 | Test zero once (K). Zero copies 1/0 into its result. Otherwise retain k through the final sign test, n through the last BIT_TEST, m through the scan; release n/m after the scan and k after the sign/conjugation action. Release 0/1 at return. |

Kernel releases occur after the named arithmetic result's required checks and
before the next listed arithmetic operation. EXPAND's ladder probes occur in
ascending index order; retained valid/key fields load once per probe and are
released immediately after it. Importing L0 loads/copies retained 2 then 1.
Accumulator initialization copies its private 1 then 0. Each nested PAIR_MUL
uses the table above: borrowed ladder entries remain live; its returned pair
replaces the private accumulator/ladder destination by ownership transfer.
Release the old accumulator only after the new pair returns successfully.
Prospective ladder entries retain the transaction lifetime defined above.

Each size guard borrows a private result without copying; guarding a retained
coefficient first loads/copies that coefficient. Load/copy the retained profile
limit once per guard, form the B size result, then the K test result. Release
the test, size and limit immediately after the test, in that order; release a
guard-only coefficient copy last. On failure release the same scratch before
the bounded error reporter runs. Administrative test scratch is not recursively
width-tested. The tested arithmetic result remains live for its subsequent use.

Metadata is transferred leaf-by-leaf, not by uncharged object clones. Validation
loads tag, VALID, norm proof tag if present, then parent snapshots in listed
order; each parent-version comparison loads that parent's current version once.
Release comparison copies immediately; release other node-local copies on that
node's return/refusal. The visited set has its per-invocation lifetime above.

After validation, event planning loads each needed retained field once and in
this order: g; k1,k2 for STEP or the target k for SET_EQUAL; u/value-version for
SET(u,new); changed input version then r version for STEP; affected input norm
value then r norm value for STEP; constant 1. Decoded request operands are private
and copy once into the plan. Reuse these copies, never reread for arithmetic.
Build journal leaves in destination cell/field order; each stored scalar or
reference leaf is one COPY from the computed/private source. C/D payload aliases
do not create a duplicate exponent slot. Release plan-only copies when the
journal and receipt have been filled; keep journal values until commit/refusal.
No-op SET plans no changed state leaves but still stages the receipt and COMMIT.

Receipt transfers follow the existing schema order: g, versions 0..5, snapshots
by cell/parent order, fresh flags, operation status/code/stage. Copy each leaf
once directly into the private receipt; READ it first only if its source is
retained rather than the private journal. Event receipts use the prospective
journal overlay. OBSERVE equality loads k1 then k2 once, releases both after K;
norm outputs each load/copy their retained value once. Pair output views keep
their existing permitted aliases. Receipt/output slots stay live through
publication/return or refusal; no additional scalar copy is charged for moving
the completed receipt. Serialization keeps its separate byte/time accounting.

## 6. Limits, precedence and first-failure labels

Nominal E=64 (exponent magnitude), P=256 (arithmetic coefficient bits), R=512
(raw bits), O=256 (export bits). Metadata is exact integer state with P/R checks.
Nominal |k|<=32, coefficients below 2^64 and listed pair/norm raw values below
2^130. These are bounds, not golden values or certified first-refusal stages.

Check each arithmetic temporary against R immediately after formation and before
use; each completed pair component against P. Cancellation cannot rescue an
oversized raw value. OBSERVE checks O in coefficient order even on hits. Paired
small-export controls keep P/R nominal, so expanded/symbolic work does not become
an unequal-completion comparison. Isolated raw-kernel controls are not performance
ratios. Admission/export rules are common; algorithm-specific work use is not.

One work unit per ledger event plus ENTER per API/kernel request and BYTE32 per
started 32-byte serialization chunk. Before every event reserve its unit against
case cap 100,000 and invocation cap 4,000,000. Failure returns WORK_LIMIT at the
denied event before performing it. Log denial outside algorithm counters; retain
prior charges, not the denied event. Refusals/reset microcases never reset the
invocation cap. No separate allowance for controls or reference validation.
Reference work has its own ledger/phase but consumes the same case/invocation
allowance. Case exhaustion stops that case; invocation exhaustion stops the run.
An error envelope is bounded administrative reporting (<=1 KiB), not continued
algorithm work: record its field reads/copies/bytes in a separate diagnostic
ledger and include its time/output. It cannot recursively refuse while reporting
a denial. No user-supplied unbounded value is printed in an error or stage name.

Precedence is procedural: a failed work reservation preempts any next event.
With work available: bounded request-shape/type decoding (INVALID/MALFORMED),
supported domain (OUT_OF_DOMAIN), current tags/proofs/snapshots (INVALID_STATE
or STALE), prospective exponents (EXPONENT_LIMIT), kernel raw/P (ARITH_LIMIT),
export O (COEFFICIENT_LIMIT), serialization/output capacity, final COMMIT.
CAPACITY is checked before allocation, OUTPUT_LIMIT before candidate buffer/write
growth; either can preempt that allocation/write. All codes except MALFORMED
carry REFUSED. No failure encodes FALSE or inequality. Stages follow
`case.arm.request.operation.node-or-index.temporary-or-test`; independent literal
tables must identify the first failing event, not merely its operation family.

## 7. Twenty controls: semantic expectations, not golden derivations

Each row is one reset microcase per arm, at most 66 API/kernel requests. Nominal
limits unless stated. No numerical golden values, operation totals or first-
refusal tables are derived here. Mutants must be detected by the checker; a
wrong result cannot be relabeled an ordinary resource refusal.

| ID | Fixed stimulus / fault | Expected semantic outcome |
|---|---|---|
| 1 | STEP(z2,-1), OBSERVE; flip inverse sign | U^-1 source/product; altered output rejected |
| 2 | STEP(z1,+1), STEP(z2,+1), OBSERVE; exponent difference | Product U^2; altered product rejected |
| 3 | OBSERVE, STEP(z1,+1), OBSERVE; old expansion key | New values/versions; stale result rejected |
| 4 | Same event; suppress r snapshot refresh | STALE before expansion |
| 5 | LOAD_PAIR of alleged non-Pell/zero pair | OUT_OF_DOMAIN; no proof/state minted |
| 6 | STEP(z1,+1), OBSERVE; equality true | Equality false; wrong Boolean rejected |
| 7 | OBSERVE twice, no changes | Identical values/receipts; second validates/hits caches |
| 8 | STEP(z1,+1), OBSERVE, SET_EQUAL(z1,current_k), OBSERVE | No extra version/invalidation/propagation |
| 9 | OBSERVE, SET(u,1), OBSERVE | Only g/u version change; graph caches unaffected |
| 10 | STEP(z1,+1), STEP(z1,-1), OBSERVE | Earlier value with new monotonic input/product versions |
| 11 | Isolated EXPAND(0) | Identity; no ladder/final square |
| 12 | Eight STEP(z1,+1), OBSERVE twice | Common exact U^8 outputs/receipts; C/D cold ladder then warm expansion hit, no unused square; A/B expanded STEP path and fresh current-pair cache hits, no powering requirement |
| 13 | Eight STEP(z1,-1), OBSERVE | Common exact U^-8 outputs/receipts; C/D conjugation after positive powering; A/B signed expanded STEP path and matching current-pair cache state |
| 14 | E=0, STEP(z1,+1) | EXPONENT_LIMIT; committed snapshot unchanged |
| 15 | O=0, OBSERVE at reset | COEFFICIENT_LIMIT; no partial tuple/cache commit |
| 16 | O=31, OBSERVE at reset, 32 STEP(z2,+1), OBSERVE | Small-export refusal after earlier components staged; private additions discarded |
| 17 | Zero remaining case work; malformed request | WORK_LIMIT at ENTER, before parsing |
| 18 | Malformed STEP shape; E=0 and work available | MALFORMED before exponent admission |
| 19 | Isolated PAIR_MUL(U,U); R=1 | ARITH_LIMIT; no wrap/cancellation rescue |
| 20 | Corrupt norm proof tag with valid snapshots; OBSERVE | INVALID_STATE; no proof reuse/minting |

Cases 14–19 require independently certified literal refusal stages and attempt
counts under a fresh bounded authorization. All other cases also need coefficient,
receipt and count expectations. No control is evaluated here. The independent
reference uses signed coefficient recurrence and a separate general pair-product
check for r; candidate powering may not call its oracle. Expanded arms also need
independent literals/checker ownership and deliberate-fault rejection.

## 8. Finite envelope and ownership

Exactly 80 reset control microcases plus twelve nominal cases. No random draws,
extra seeds, timed repeats, tuning or general engine. Per case hold at most 512
logical scalar slots, 64 pair objects and one 64-KiB serialization buffer; refuse
CAPACITY before exceeding them. Save registered state/receipts/ledgers, not
unbounded per-interpreter traces. Artifact writer enforces <=4 MiB total JSON
and <=2 MiB per file. Budget another 4 MiB each for stdout/stderr via OS per-file
limits and 4 MiB for launcher provenance/terminal files: total evidence 16 MiB.
Candidate owns artifact prevention; later launch review must bound stdout/stderr
paths and admit provenance size. Post-run review checks aggregate bytes including
final pin logs; excess is OUTPUT_BUDGET/FAIL, not a performance result. No claim
of an unprovided aggregate filesystem quota.

Use existing detached runner, exclusive new build child, --timeout 60, and child
prlimit hard/soft RLIMIT_AS=1 GiB and RLIMIT_FSIZE=4 MiB. Assert limits before
work. Pin source/reference/command/argv, executable versions and supervisor
identity before GO. No executable command exists yet. Supervisor owns the
CLOCK_BOOTTIME deadline. Its documented termination grace is cleanup after expiry,
not extra accepted work or an enlarged 60-second allowance; record both and
never accept late completion. Report wrapper setup/notification and checker
costs separately from candidate phases. Controls/checker stay in the invocation.

After LAUNCHED end the turn. Later interpretation requires exactly one durable
COMPLETE/FAILED/TIMEOUT and matching result/deadline evidence. Exit zero is not
independent acceptance. Timeout/resource/incomplete output is HOLD for benefit
inference, with no retry/split attempt. Wrong output, receipt or missed mutant
is FAIL. No native-cycle/energy/physical advantage follows.

Remaining gates: narrow independent specification review; fresh bounded literal/
control/first-refusal derivation; candidate source/command/resource review;
separate implementation/execution GO. Laminar principles remain hypotheses, not
ISA instructions. QCG-0, X2, hardware and closed HEX-SOM evidence stay separate.
