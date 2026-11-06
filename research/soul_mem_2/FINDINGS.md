# SOUL-MEM-2 findings

**Disposition: PARTIAL.** The registered comparison is deterministic, respects
the measured byte budgets, exercises retention pressure and reports meaningful
negative results. However, the M0 representation uses the *absence* of a
candidate to produce an unknown answer; it does not persist an explicit
uncertainty label as required by the proposed architecture. Thus it cannot
distinguish, for example, an unseen key from an explicitly unresolved key in its
stored state. The results are preserved as registered and have not been repaired
or rerun under a changed policy.

## Results

Separate calibration yielded the same per-policy byte limits: small 239, medium
431 and large 815. Each cell below is correct answers out of eight: seven current questions and one explicit historical question. The exact per-query classification is in the evidence.

| Budget | Compact M0 | Full-history M1 | Indexed M2 |
|---|---:|---:|---:|
| 239 bytes | 7/8 | 7/8 | 6/8 |
| 431 bytes | 7/8 | 7/8 | 7/8 |
| 815 bytes | 8/8 | 8/8 | 7/8 |

The two S2/S3 revocation-and-revision tasks were answered correctly by all
policies at all budgets. The compact policy could preserve multiple candidates,
unlike the SOUL-MEM-1 baseline. For S4, every policy answered the current and
historical door questions correctly at every budget. In the pressure scenario,
all policies lost the early parcel fact at the first two budgets; at 815 bytes
M0 and M1 retained it, while M2 evicted it to accommodate its index and
summary. At the smallest budget M2 also evicted the key fact in S1. Missing
answers were `unknown`, and the recorded checker reported no unsupported
assertion. These results do not show a decision advantage for retained history
on the chosen fixtures.

| Budget | Policy | Query record visits | Additional index-validation visits | Query logical bytes | Defined query ops | Defined ingest ops |
|---|---|---:|---:|---:|---:|---:|
| 239 | M0 | 14 | 0 | 1,051 | 22 | 30 |
| 239 | M1 | 16 | 0 | 1,155 | 24 | 30 |
| 239 | M2 | 10 | 12 | 2,012 | 38 | 79 |
| 431 | M0 | 21 | 0 | 1,581 | 29 | 26 |
| 431 | M1 | 23 | 0 | 1,685 | 31 | 26 |
| 431 | M2 | 12 | 19 | 2,836 | 47 | 96 |
| 815 | M0 | 29 | 0 | 2,193 | 37 | 22 |
| 815 | M1 | 31 | 0 | 2,297 | 39 | 22 |
| 815 | M2 | 12 | 27 | 3,660 | 55 | 102 |

M0 visits are compact-candidate reads; M1/M2 query visits are archive reads.
M2's separately counted full index-validation scans are also archive visits.
Consequently M2 inspected 22, 31 and 39 archive records in total respectively,
versus M1's 16, 23 and 31. Its indexed lookup alone visited fewer records, but
its declared validation and index maintenance reverse that comparison. These
are logical counters, not measurements of runtime or physical memory. M2's
summary is stored and budgeted but is not used as a query shortcut; this is a
policy limitation, not a general property of indexed retrieval.

All 45 trial conditions stayed within their registered limits after every
committed update. The maximum occupied byte counts across scenarios were
184/181/225 (M0/M1/M2) at 239, 415/412/360 at 431 and 723/720/776 at 815.
Serialized temporary-state estimates are recorded separately; they do not
measure actual transient Python memory. Every committed state, discarded record
and reason is recorded in `evidence/registered-1.json`. Not-recoverable IDs
include deliberately invalidated observations and dropped revocation tombstones
as well as budget evictions; the event log distinguishes them. There was no
additional compression beyond M0's three-candidate cap and omission of revocation
tombstones.

All 12 controls passed, including feasible summary, missing and revoked evidence,
false source, two-premise transitivity, missing inference rule, actual disabled
retrieval, stale index after incorrect eviction, infeasible minimum budget,
overflow eviction, corrupt index and valid indexed archive. Five focused tests
passed. Two registered runs were byte-identical; this is reproducibility, not
independent implementation verification.

## Interpretation

**Established within the registered fixtures:** each condition received the same
stream and budget, with complete serialized persistent-state accounting after
each atomic update; M0 retained alternatives when permitted; and the separately
coded checker tested actual direct propositions and a transitive control. Its
SUPPORTED status is relative to available trusted observations and declared
rules, not a proof of outside-world truth or of absence of missing counterevidence.

**Observed:** a compact representation matched or exceeded the two tested
history policies on this workload. At equal budget, M2's metadata cost caused
additional eviction; its full validation scans and index rebuilds increased the
defined work counters. The specific controls and five scenario families do not
establish that compact memory is generally sufficient or that indexing is always
inefficient.

**Assumed:** fixture observations, epochs, source strengths, revocations,
proposition semantics and evaluator world states are correct. The source ID is a
reference, not independently authenticated provenance. Observation IDs are
unique; the stream is ordered. Fixed policy code and budgets are shared
configuration rather than agent data. Candidate capacity, oldest-first eviction,
the M2 validation policy and the small fixed workload strongly shape outcomes.

**Unknown:** how a compact representation with explicitly stored uncertainty
would behave at the same limits; how different retention policies, more complex
source conflicts, long streams or dynamic workloads would compare; and actual
peak transient memory or wall-clock efficiency. The absence of an uncertainty
label means the experiment does not establish full compliance with the compact
memory contract, even though it can return unknown for the tested queries.

**Excluded:** rule learning, neural models, physical substrates, consciousness,
production use, publication, network access and hardware work.

## Reproduction and preservation

Python 3.10.12; base repository revision
`5769c0e0191e6ae411ece5bc58ba825a4b71ae1f`, with unrelated existing workspace
changes. The separate calibration fixture ran before registration. The policy,
scenarios, scoring, controls, budgets and instructions were hashed before either
registered run; `sha256sum -c` passed afterward. Five tests passed. Both
registered outputs were byte-identical (`diff -r` exit 0), and the first is
preserved in `evidence/registered-1.json`. No registered repair or criteria
change occurred. Reproduction commands and the precise accounting conventions
are in [README](README.md). The campaign stops here; the separate SOUL-LEARN-0
candidate has not been started.
