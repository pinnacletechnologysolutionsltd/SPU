# SPU v0.3 external pre-freeze review (record)

**Status: HISTORICAL REVIEW RECORD — not a contract.** The authoritative execution semantics are in the
[v0.3 contract candidate](SPU_V03_CONTRACT_CANDIDATE.md).

**Provenance.**
- Section 1 is the review **verbatim**, as supplied by the repository owner on 2026-11-11. Nothing has
  been edited, reworded or reordered; only a heading was added.
- The reviewer was an independent Claude session working from uploaded files. It built against
  `gen1_*.hpp` from public `main` and reviewed revision `0x03` as it stood before `f2104cac`.
- Its reported evidence (the differential programs, exact-rational checks, sign tuples, encoding words
  and sanitizer run) was **not reproduced in this repository**, and no artifacts from it are stored
  here.
- Section 2 records the owner's dispositions separately. Section 3 maps them to commits.

The categories distinguish:
- the reviewer's **execution** results (software behaviour);
- its **proofs** (mathematical arguments);
- its **reasoning** (architectural hazards not demonstrated);
- the absence of any RTL evidence, as the reviewer itself states.

## 1. Original review (verbatim)

SPU v0.3 pre-freeze review: findings
Verdict: the execution semantics can be frozen. I found no correctness defect and no simulator/oracle disagreement. Two blockers remain, both in the contract text rather than the machine.

Scope: I ran the files as uploaded, built against gen1_*.hpp from public main (the v0.3 branch isn’t pushed). I did not run your 133-check harness, the 271 gate, Gen-1 80/80 or your fuzz generator. There is no RTL evidence. The unrelated SIM-G3 file was not used.
BLOCKER
B1. The contract contradicts itself and the ISA draft (source inspection).
- Internal conflict: the contract header says the simulator “now implements revision 0x03”. §12.2 says “SIM-0 still accepts it”, §14 says “SRD retirement is not yet implemented”, and §15 is headed “planned; implementation on HOLD”.
- Conflict with the draft:
  - Draft §2 still lists SRD and SMOV, and §3.1 still lists the result buffer.
  - Draft §3.1 clears staging on a failed SLD; contract §4 leaves it unspecified.
  - Draft §1 says a Gen-1 program runs with an appended HALT. That is now false, and contract §12.1 denies it.
- Stale references: psurd_arith.hpp line 2 names the draft as its specification, and the harness hashes the draft, not the contract.
- Correction: delete the three stale statements, tag each §14 evidence item with its revision, and add one sentence making the contract authoritative over the draft.
B2. Refused-load behaviour is normative, unverified and unsafe as written (reasoning, not demonstrated).
- Location: contract §10 requires a hardware loader to “keep the previously validated image”; §14 admits this is unverified.
- Hazard: the record (§11) carries no image identity. If a host misses the refusal and sends START, it gets a valid, CRC-clean record from the old image and cannot tell.
- Correction (smallest): a refused load leaves no valid image, and START is refused until a load succeeds. The alternative is to add the image CRC to the record, which changes the 213-byte layout.
RISK
- Arithmetic RTL is unverified. SADD, SSUB, SNORM and ENGINE_FAULT have software evidence only. Raw-fit commits make the lcm alignment bit-visible in the record, so the RTL must match the formula exactly, not just the value.
- The frontend is the only decode barrier. The core reads [58:56], so 0x78–0x7B alias to SLI, SLD, SRD and SMUL. The directed harness misses several per-field negatives that D-1 condition 4 requires, such as register index ≥ 8 on most forms and BR with R2 ≠ 0. My sweep covered them, but they should be RTL fixtures.
- Code numbering invites mistranslation. The Gen-1 core emits status 1 INVALID and 4 BAD_ENCODING; v0.3 causes are 1 BAD_ENCODING and 2 INVALID, and status 2 is OVERFLOW. Renumbering later would change the record.
- §2 over-specifies reset. The (0, 0, 1) value of an uninitialized register is unobservable. Requiring it forces a full register reset at START and constrains memory inference; only the mask needs clearing.
- Run length is unbounded in time. The budget counts instructions, latency is data-dependent, and the contract is silent on LOAD or START during a run.
- L has no hardware cross-check. The “L against file size” argument (X9) needs a word-count equivalent in the transport.
OPTIONAL
- State the stronger invariant: cause, PC, flags and retired count are also representation-independent.
- Clarify that the BUDGET PC can equal L (L = 1, B = 1 gives PC = 1), and add that directed test.
- §13 does not say what “just above” means. At |x| = 2^30 exactly I got 0 of 729 refusals.
- Note that record version 0x03 equalling image revision 0x03 is a coincidence.
NO ISSUE
- Widths (proof): SMUL |A| ≤ 2^128, attained with all coefficients at −2^63; SADD/`SSUB` raw values and STST terms stay below 2^128.
- Value-determined refusal (proof and execution): the contract’s argument is complete. Against an independent exact-rational reference, 277,200 operations on boundary and random operands gave 0 violations.
- Signed boundary: −2^63 is representable and +2^63 is not, so negation can refuse. This is consistent with the contract.
- Sign test (execution): 40,196 tuples, 20,000 of them near-cancelling, matched 120-digit decimal.
- Encoding (execution): 11,979 words, including every single-bit flip of 14 forms, agreed across the contract table, the C++ and the oracle.
- Differential fuzz at 0x03 (execution): 20,000 random programs plus 21,196 arithmetic and sign programs, 0 mismatches, clean under the undefined-behaviour sanitizer.
- Sequencing: budget precedence, terminal PC, aliasing, loader refusals (including 0x02) and START bounds all behave as specified.
- Completeness: both workloads run, and the §13 bounds hold (0 of 729 and 0 of 15,625 refusals). SMOV is not needed, because SMUL by (1, 0, 1) copies bit-exactly.

## 2. Owner dispositions (2026-11-11, recorded separately)

| Finding | Disposition |
|---|---|
| B1 contract consistency | **Accepted.** A documentation defect, not an ISA defect. The contract is made authoritative over the draft; the draft is marked superseded but its historical decisions are kept; stale statements are removed; evidence is tagged by revision; source comments and the harness identity are corrected. `gen1-surd` and its contract are not modified |
| B2 refused-load semantics | **Accepted.** A refused LOAD invalidates the executable image, and START is refused until a LOAD succeeds. Hardware may clear one validity bit rather than erase memory. A transport rule covers partial or interrupted transfers. Preferred over adding an image CRC to the record (the 213-byte format is kept). This does not authenticate programs |
| Reset over-specification (§2) | **Accepted.** At START registers become architecturally uninitialized and their stored bits are unspecified. Reads are guarded by the mask, and the record zero-fills uninitialized registers |
| Missing per-field decoder fixtures | Add to the RTL-0 verification plan |
| Gen-1 vs v0.3 status numbering | Keep an explicit translation |
| Data-dependent latency | Document; no ISA change |
| LOAD/START during execution | Define a simple BUSY or rejection policy |
| Transport image-length validation | Require hardware word-count checking |
| BUDGET PC may equal L | Clarify and add a fixture |
| §13 "just above" wording | Correct |
| Image/record version coincidence | Document |
| Stronger representation-invariance claim | **Deferred** unless proven for the stated scope. Instruction sequences can observe initialization and raw tuples, so the existing value-determined refusal invariant is the better-scoped claim |
| SMOV not needed (SMUL by (1, 0, 1)) | Noted. Reinforces keeping SMOV unsupported |
| Arithmetic RTL unverified; frontend decode barrier | RTL-0 qualification scope |

The owner also judged that no further broad pre-freeze review is needed after these corrections.

## 3. Where each disposition was applied

| Commit | Applies |
|---|---|
| `f2104cac` (docs) | B1; the B2 contract text (image-valid table, transport rule, word count); the register-reset relaxation; BUSY; the status translation table; latency; BUDGET PC = L; the §13 wording; version independence |
| `0020a00c` (simulator and tests) | B2 in the SIM-0 loader (image-valid, `--do` session mode); source comments and the harness contract hash. New fixtures: four refused-LOAD kinds, each with invalidation and recovery; stale registers unobservable; BUDGET with PC = L; 361 per-field decoder words. Harness 156/0 including Gen-1 80/80 |

One requested fixture is noted rather than complete: the reviewer's example of register index ≥ 8 is
covered for R1, R2 and Sb on every form that has those fields (`psurd_fixtures.py`). Formal RTL decoder
fixtures remain in the RTL-0 plan.
