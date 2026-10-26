# QCG-0 P0: request for a bounded reviewer calculation allowance (sequential and Cell B W31 stage tables)

Date: 2026-10-23 (re-pinned after the Revision 3.2.1 PASS). **This is a REQUEST drafted by the author. It authorizes nothing.**

**Pinned subject.** The programs and grammar to be traced are those of `QCG0_P0_EXECUTION_CONTRACT.md` Revision 3.2.1, SHA-256 `1f8aca9f088ffbaafb002ba5cffde7bdee7b33fdfcf18dcf20dec16202b8cf2f`,
which passed the independent read-only review (`P0_CONTRACT_R321_REVIEW_CERTIFICATE.md` `384db31162658f709a002006c42086bbaf277011d0bde4a558692cb6fd4ec2b4`; manifest `36f8b3773a75635015e3c1ab619132febea48abfa712219106729a0a1806b10c`). The reviewer verifies these
identities, the owner dispositions D-1…D-6 and every earlier pin (pre-registration §0.2, contract §0) before any calculation. The R2 allowance (three invocations, 90 s) is
exhausted and no calculation may run under it. The reviewer is asked to confirm or replace every proposed number below before any
owner authorization; the owner has stated that no new allowance is authorized yet.

**Purpose.** Derive, under Profile W31 (reduced ≤ 31 bits, raw ≤ 63 bits), the first-refusal event ids (grammar of contract §3, programs
of §5, Revision 3.2.1) that remain uncertified: (A) sequential arms and (B) Cell B arms. Cell A is certified and is not recomputed.

**Scope of derivation.**
* *Preparation:* for each arm and curve, whether the P-phase passes W31 or where it first refuses (event id `arm.P.step.k.sub`).
  Cell B composite preparation (`PCOMP`, `PMUL`, `BERN`, degree 9 with denominators powers of 49) is expected to be the most
  likely to refuse; the table will say so or not.
* *Sequential (PH3 and PH5; tapes S1, S2, S3; k = 0..16):* arms Horner, Bezier, TS, FD, PH, PHFD, C1 (= PHFD), C2. For each
  (arm, curve, tape) the first refusal event over the 17 samples, or none; routes whose preparation refuses are marked
  `PREPARATION_REFUSED(event)` and not queried.
* *Cell B (PH3 with φ_sq; the 16 registered queries in tape order):* arms B-COMP, C1 (stand-alone), E-COMP, E-BEZ, E-TS: the first
  refusal event per arm (or none) and the query index.
* *Method:* the reviewer's own exact-rational trace of the written programs and sub-check order; stop at the first refusal per
  route; no candidate engine, no alternate algorithm, no change to the programs; every successful route reported as passing.

**Proposed ceilings (to be confirmed or replaced by the reviewer).** At most **3** invocations; each under
`/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304 -- /usr/bin/python3 -B -I <review-script>`;
cumulative external ceiling **90 s**; cumulative review outputs **≤ 10 MiB**; no child processes, network, devices, installs; internal
tracking limits 4096 reduced / 16384 raw bits; scripts read before execution; actual argv, cwd, script and input hashes, stdout,
stderr, exit and resource accounting recorded; no automatic retry, no extension, and exhaustion is a valid terminal result.
The estimated work is small and is stated per route, not as a lump: **21 preparations** (8 sequential arms × 2 curves = 16, plus 5 Cell B arms × 1 curve),
**48 sequential routes** (8 arms × 2 curves × 3 tapes) of at most 17 samples each, and **5 Cell B routes** of at most 16 queries: at most
**896 sample or query evaluations**, each stopping at the first refusal of its route.

**Required schema.** Every reported stage carries its route context: `{profile: "W31", curve, tape or cell, arm, request or sample index, event id, status}`,
with `null` where the route passes; event strings are never compared across contexts. FDINIT and C2 stage ids follow the Revision 3.2 text.

**Deliverables.** A certificate, a JSON of event ids (null where a route passes), a manifest of hashes; certified Cell A references and
all earlier artifacts untouched; no hash recorded into the pre-registration or contract by the reviewer.

**Preconditions.** The independent PASS of the amended contract (Revision 3.2.1) is now in hand; the allowance should be authorized only against that pinned text, so that
stage tables are not derived against text that then changes; and with the reviewer's own statement of the invocation count, time,
memory and output limits before the first calculation.

**Not requested.** Candidate implementation, any benchmark or P0 run, regeneration of any certified reference, or a change to any
decision D-1…D-6.
