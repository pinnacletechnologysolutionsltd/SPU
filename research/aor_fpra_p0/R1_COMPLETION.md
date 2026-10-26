# AOR × FPRA P0 repository reference R1 completion

2026-10-23. **Prepared for independent source/command review; execution HOLD.**
No registered derivation, nominal case, control microcase or numerical fixture
was run/generated. No attempt was consumed. The ZIP was neither read nor
imported in this tranche. No candidate, ISA, simulator, RTL or hardware change.

Frozen [Revision 3](PREPARATION.md) remains
`8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb`.
The [derivation packet](REFERENCE_DERIVATION_PACKET.md) and reviewed predecessor
remain unchanged. Later owner authorization supplied reference implementation
permission; the old packet is preserved rather than rewritten.

## Changed paths and identities

- [pell.py](reference/pell.py): preserved signed recurrence/general product/norm
  truth, with separately charged reference primitives and atomic truth updates.
- [accounting.py](reference/accounting.py): typed logical slots, owned pair
  results, immediate raw/completed width guards, deterministic event digest,
  scratch release, accumulator replacement and private ladder replay. BYTE32
  reservations precede buffer growth; failed work remains charged.
- [semantics.py](reference/semantics.py): fixed six-cell request execution,
  metadata READ/COPY and journal order, validation-local visited sets, cache
  maintenance, staged receipts and atomic COMMIT. Refusal discards every private
  addition. The committed state includes all header keys/references and pairs.
- [controls.py](reference/controls.py): all twenty request definitions, independent
  semantic/coefficient checking and internal fault targets. Inverse sign affects
  z2; stale snapshots and corrupt proofs reach validation. Controls 12–13 retain
  arm-specific power/cache requirements. Fault outputs are explicitly labeled.
- [derive.py](reference/derive.py): bounded six-file writer, pending files and
  manifest-last publication, source/input rechecks, fixed argv/cwd checks,
  provenance, phase times, RSS and heap telemetry. Incomplete output cannot
  publish a complete artifact manifest or exit successfully.
- [synthetic tests](reference/test_reference_synthetic.py),
  [encoding freeze](REFERENCE_ENCODINGS.md),
  [source identities](R1_SOURCE_SHA256.json), and
  [proposed command](R1_PROPOSED_COMMAND.txt).

The source manifest contains full SHA-256 values for all five modules, tests,
encodings, frozen authority, accepted R3 review and detached/deadline tools.
It excludes itself; its hash is reported separately. Files remain untracked in
the existing working tree; no staging/commit or unrelated cleanup was performed.

## Synthetic verification

Final source suite: **31 tests PASS**, exit 0, 6.982 seconds under the command:

```bash
/usr/bin/timeout 60 /usr/bin/prlimit \
  --as=1073741824:1073741824 --fsize=4194304:4194304 -- \
  /usr/bin/python3 -I -B research/aor_fpra_p0/reference/test_reference_synthetic.py
```

Coverage includes helper result ownership; immediate width refusal and stage
attribution; every primitive denial boundary of a custom seeded OBSERVE; changed
and no-op SET/SET_EQUAL COMMIT denial; fresh validation and warm caches; typed
key/status storage; all seven fault mechanisms on synthetic states; deterministic
event replay; independent truth/version checks on a distinct synthetic tape;
BYTE32 reservation ordering; output bounds, manifest binding and interrupted
publication. Tests do not call registered tape/control constructors or main.

The deliberately nonregistered seeded graph uses exponents 5,-2,3; its test
outputs are assertions only, not saved reference tables. Synthetic writer tests
use disposable temporary directories and never the registered destination.
No claim is made that registered controls have already passed.

`derive.py --help`, AST/import inventory and whitespace checks are nonlaunching
checks. Documentation audit findings elsewhere are not repaired in this tranche.

## Encoding and resource review points

The encoding document freezes typed requests, internal fault hooks, 64-bit
ID/key/reference fields, two-bit statuses, ASCII tags, exact decimal/UTF-8 JSON,
field inventory, journal/receipt order and output roles. The fixed 64-header
directory contains no precomputed pairs; every arm pays its initialization.
This is an explicit reference storage choice for the next reviewer to assess,
not a native topology or physical area estimate.

The nominal mathematical bounds remain those of Revision 3. A source-based
conservative work-envelope estimate for review is: modeled setup <=400 events;
STEP <=400 in A/B or <=300 in C/D; warm OBSERVE <=350 in A/B or <=1100 in C/D;
each newly needed ladder rung <=60 extra events; reference STEP checks <=30,
observation checks <=50, and reference setup 23 COPY events. Nominal exponents
require at most six rungs; all helper/control inputs stay within the registered
small envelope. These coarse bounds, not literal reference counts, put the
largest nominal case below 100000 combined units and the complete packet below
4000000. Independent review must validate this estimate, including serialization
and journal events; no registered trace was used to establish it.

Logical storage has <=279 retained scalar slots at the full E=64 bound,
including all 192 directory headers. A coarse transaction-lifetime count is
below 448 scalar slots and 32 pair objects, within 512/64. The observer buffer
has its independent 64-KiB cap and contributes to logical bit peaks. Reference
truth/bookkeeping storage is measured in host RSS/heap, not represented as free
candidate cache storage. Python dispatch, instrumentation, hashing and evidence
formatting remain host overhead included in elapsed/RSS/heap and byte reports;
abstract counters are not complete machine-operation costs.

Each JSON file is checked before write against 2 MiB and all six against 4 MiB.
Pending files are exclusive; payloads publish before the hash-bound manifest.
Summary and manifest require pending independent acceptance, never PASS. Work,
byte or memory exhaustion cannot turn into mathematical inequality or acceptance.
Unexpected refusal/failed checking raises a nonzero exit. No retry or fallback
workload is implemented. External terminal/deadline evidence remains mandatory.

The [proposed command](R1_PROPOSED_COMMAND.txt) retains 60 seconds, 1 GiB address
space, 4-MiB per-file RLIMIT_FSIZE and the exclusive packet destination. The
child asserts limits, input identities, exact argv and launcher provenance.
It reads files created before systemd launch rather than racing LAUNCHED.
The pinned supervisor enforces CLOCK_BOOTTIME, with a 10-second termination
grace after expiry; this grace is never accepted work. No aggregate filesystem
quota is claimed. Later acceptance must check <=16 MiB total evidence, exact
terminal-marker uniqueness and deadline status.

Telemetry separates replay, reference setup/checks and output overhead. Heap
tracing begins after preflight; final RSS covers the process high-water mark.
The supervisor's deadline record supplies the complete elapsed command interval,
including startup/preflight. No candidate/native timing or energy result follows.

Observed tool identities for review:

| Executable | Version | SHA-256 |
|---|---|---|
| `/usr/bin/python3` | 3.14.8 | `375532f83be620283ab780c14ca6bcc5907dc379d2b621de0c5d0a112cf5458b` |
| `/usr/bin/prlimit` | util-linux 2.42.4 | `092bb6db10a743ecccfc7d6e72055007064abf8910c85d736832fb53697fff96` |

## Remaining gate

Obtain independent review of source identities, concrete encodings, event order,
ownership/rollback, all control hooks, work/storage estimates, writer completeness
and the proposed command. Dynamic user-manager/PATH/tool identities, destination
exclusivity and absence of conflicting source changes must be rechecked only
under a later execution authorization. Full registered runtime/output fit and
literal coefficients/counts/first-refusal tables remain unmeasured/underived.
This note is not launch authorization or independent acceptance. QCG-W31 and
Vivado work, their budgets and frozen evidence remain separate.
