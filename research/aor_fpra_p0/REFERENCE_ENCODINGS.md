# Reference encoding freeze R1

2026-10-23. Applies only to the independent reference implementation. Revision 3
remains unchanged at `8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb`.
No registered fixture is calculated by this document.

Requests are ordered JSON objects with `op` then positional `args` array.
Operations: STEP [cell,delta], OBSERVE [], SET_EQUAL [cell,exponent],
SET ["u",integer], LOAD_PAIR [a,b], EXPAND [exponent], PAIR_MUL [a,b,c,d].
Internal arithmetic uses Python integers; bool is not an integer argument.
RESET is charged case construction, not an additional submitted request.
Cell IDs are integers 0–5. STEP/SET_EQUAL targets are 0/1 only. STEP delta is
exactly -1 or +1. Malformed control 18 omits delta. LOAD_PAIR control 5 uses
[0,0]; every LOAD_PAIR payload is refused, irrespective of membership.

Fault names: control 1 `inverse_sign`, 2 `product_exponent`, 3 `old_key`,
4 `stale_snapshot`, 5 `mint_proof`, 6 `equality_true`, 20 `bad_proof`.
Inverse-sign mutation affects z2 (cell 1): use the opposite signed kernel in
A/B, the opposite exponent increment in C/D. Product-exponent mutation uses the
opposite signed product update in A/B and exponent difference in C/D on the
second STEP. Old-key mutation suppresses the changed input's cache invalidation
and forces use of its previous pair at the following observation. Snapshot
mutation suppresses r's first parent update. Proof mutation replaces retained
n1's proof tag with `BAD` before validation. Equality mutation forces true in
the observation. Fault rejection is distinct from ordinary valid refusal.
Control 5 tests ordinary refusal and rejects a forged successful proof result.

Retained tags are ASCII `PELL`, `PRODUCT`, `NORM`, `UNIT`, `BAD`. IDs/key fields
use unsigned eight-byte big-endian integers in the logical storage inventory;
versions also retain their integer magnitude slots. Expansion entries retain
valid Boolean, cell ID, version key and pair reference; references are eight-byte
logical IDs, independent of Python pointers. Ladder entries retain valid,
index key and pair reference. Constants retained: -1,0,1,2,3 and active E/P/R/O.
Freeze a 64-entry directory of valid/index-key/null-reference headers in every
arm, including A/B isolated-helper capability; it initially contains no pairs.
All arms pay identical header initialization. Missing rung probes therefore
have concrete valid/key sources; this creates no arithmetic or precomputed
ladder entries. Primary A/B pairs have separate eight-byte primary references;
cache references alias their objects. Directory/cache headers are not duplicated
in the common field map. Null references have no value bits until populated.
Status is two logical bits. Null fields have no scalar value slot. Scalar
integer bits follow Revision 3, including a sign bit. Explicit aliases only.

Public observation object field order: `pairs`, `norms`, `equal`, `receipt`.
Pairs are ordered [z1,z2,r], each [a,b]; norms are [n1,n2,nr]. Receipt field
order: `g`, `versions`, `snapshots`, `fresh`, `operation_status`, `code`, `stage`.
Snapshots are six parent-version arrays in cell order, empty for source cells.
Successful event output has `changed`, `receipt`; errors have `receipt` only.
All mathematical integers, versions, generations and snapshot integers serialize
as canonical decimal strings (zero `0`, no plus/leading zeros). Booleans remain
JSON booleans and null remains null. IDs/indices in evidence are JSON integers.
UTF-8, ensure_ascii=false, compact separators, insertion order, no NaN, one final
LF. SERIAL counts one encoding call and BYTE32 covers that LF too. Observation
bytes and evidence JSON bytes are separate. Diagnostic records are <=1 KiB.
Request evidence keeps cell IDs numeric but writes mathematical arguments as
decimal strings; the fixed tape constructors supply strictly typed Python
integers to the request validator. No external JSON-to-request decoder is used.
Canonical byte serialization is charged for OBSERVE; event receipts are staged
structured results. Their later evidence encoding is reference writer overhead.
Attempted, completed and published observation-byte totals remain separate.

Common retained fields are constants/limits; g/u/u-version; each cell's ID,
version, tag and valid flag; three exponents; three norm values/proof tags;
parent IDs and parent-version snapshots. A/B additionally retain primary pair
references. Cache and directory headers own their fields separately. Scalar
slots are never deduplicated by equal numeric value or Python interning.

Evidence files use the six packet names. The manifest lists the other five
file hashes; it cannot contain its own hash. Its hash is reported externally.
No circular self-hash is claimed. Source manifest includes these decisions.
Control records identify the active deliberate fault. Where the replay output
is deliberately wrong, `expected_output` records independently computed truth;
`faults.json` preserves expected and altered records or the internal corrupt
state and its validation refusal. Mutant replay counts are control evidence,
not nominal performance comparisons. Per-request cache events are attempted
events; a refusal leaves the committed inventory unchanged. Wire hashes bind
completed successful OBSERVE bytes; discarded byte counts cover failed ones.

Journal order: globals g/u/u-version, then cells 0..5; within each cell ID,
version, tag, valid, exponent or norm/proof, parent-ID/snapshot pairs, primary
reference, cache valid/key/reference. Ladder headers stage in ascending rung
order, valid/key/reference. Only changed leaves are journaled; no-op SET has no
changed leaves. Computed pair coefficients transfer ownership without COPY.
Retained reads, journal/receipt transfers and primitive paths are deterministic.

For control 17, zero remaining work is the simulated algorithm's budget state,
not fictitious performed derivation work. Real reference and modeled primitive
events still share the unchanged 100000/4000000 derivation allowances. No check
or reference arithmetic receives a free allowance. Actual derivation exhaustion
stops the derivation; a successfully derived intentional refusal is distinct.

The reference models arm schedules, never candidate performance. REFERENCE work
is separately charged into the same shared budget. Exact counting/source
acceptance remains an independent review gate. Encoding R1 may not be silently
changed after review or after any derivation launch.
