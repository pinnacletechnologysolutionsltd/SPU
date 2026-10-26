# E8 root-image tranche — exact reference preparation

```bash
python3 software/tests/test_e8_root_images_preparation.py
python3 -m software.research.e8_root_images.prepare --help
python3 -m software.research.e8_root_images.prepare --output build/e8_root_images_20261013/preparation_01
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/e8_root_images software/tests/test_e8_root_images_preparation.py spu_strategy/contract_e8_root_image_preparation_2026-10-13.md docs/E8_ROOT_IMAGE_PREPARATION_2026-10-13.md
```

Date: 2026-10-13. Authority: owner says continue the separate E8 tranche.
Scope: implement mathematical references and short preparation witnesses for
the [separate proposal](contract_e8_root_image_proposal_2026-10-13.md).
Status: PREPARATION ONLY; root-image qualification HOLD / NOT RUN.
Specification, implementation and audit roles are sequentially performed by
the same preparer; independent reviewer sign-off remains PENDING.

## Files and immutable boundary

Add only `software/research/e8_root_images/`, its test, this contract and the
[preparation report](../docs/E8_ROOT_IMAGE_PREPARATION_2026-10-13.md).
Keep each Python module/test at most150 lines. Preserve original16-source,
comparison9-source and ledger18-source identities,665 protected sources,
265 SGN evidence files and the20-file completed ledger diagnostic inventory.
Do not modify existing120 fixtures,540-evaluation results, comparison adapters,
root-image proposal, qualification ceilings or CPU/RTL/ISA/build sources.
No new D4/E8 diagnostic, formal qualification campaign or hardware job is allowed.
The separate root-image package is not a sixth comparison arm.

## Representation, admission and immutable context

Use the existing exact ordered240 doubled E8 roots and ordered eight simple
roots. S has doubled simple roots as columns. Gram G=S^T S/4 has determinant1.
Candidate Gauss-Jordan computes S^-1; an independent cofactor/Bareiss inverse
checks it, along with all240 integral simple-root coefficient vectors.
Static context is a frozen dataclass of tuples. Basis coordinate rows alias
root rows through eight basis IDs; do not count duplicated basis coordinates.
No mutable transformation cache or dynamic hash lookup table is used. Index
lookup is binary search over the immutable sorted roots.

A descriptor is eight distinct actual integer IDs0..239. Reject bools, reserved
IDs, bad length, repeats and any mismatch in36 upper-triangle Gram entries.
The Gram admission proof relies on the unimodular lattice basis and equality
of E8 root/lattice automorphism and Weyl groups. The implementation performs
the finite exact predicate; universal sufficiency requires independent review.
Validate the trusted setup context before a future qualified execution service.
Current public context arguments are trusted mathematical reference contexts,
not a protocol for admitting arbitrary externally supplied table objects.

## Exact operations and conventions

LEFT update is s_j composed w, with eight reflection-table lookups. Public
reference functions additionally run Gram admission before and after updates;
eight lookups is not their total cost. RIGHT update forms beta_i-G_ij*beta_j,
then root-indexes the result. General u composed v applies u to v's eight images.
Chronological words accumulate on the left; maximum accepted input word256tokens.
All token types/ranges are checked. Refusals return no partial descriptor and
do not mutate caller inputs; no emulated CPU register publication is involved.

Cartesian M=Y S^-1; inverse M^T. Simple-basis C=S^-1 Y satisfies C^T G C=G;
inverse G^-1 C^T G. Do not use C^T alone. Materialization decodes integral
coefficients c=S^-1 X and returns Yc for doubled lattice vector X. It validates
input/output lattice membership; exact coefficient and intermediate arithmetic
is unbounded host integer/Fraction reference arithmetic, not a finite CPU profile.

Conventional reduced words: count positive roots sent negative; choose lowest
ID right descent, strip on the right and verify length decreases by1. Reconstruct
using the stripping IDs in the same chronological LEFT-action order. Stop after
120 iterations if identity is not reached; never silently reverse the tokens.
The longest-element witness is minus identity, with inversion count/reduced
length120. This is a conventional group-theoretic baseline, not SPU novelty.

## Wire format and initial table accounting

Full version1 record is76bytes: four-byte header(1,0xE8,8,0),32-byte root hash,
32-byte basis hash and eight image-index bytes. Hash compact canonical JSON
numeric arrays with SHA256. Payload is64bits; the76-byte record includes identity
metadata. Reject altered schema/flags, root/basis versions, length and reserved
image IDs before Gram acceptance. Context-known shorter records are not implemented.

Initial logical static layout uses signed64 integer and128-bit rational slots,
headers/counts and row headers. Include roots, packed basis/reflection IDs,
Gram, inverse basis, all240 cached coefficient vectors, positive-root IDs and
context hashes/header. This layout totals307,680bits. It is a proposed static
inventory, not a measured memory size or complete simultaneous execution budget.
Workspace, decoder/reduction buffers, stack, host object/cache/pointer overhead,
construction work, dynamic widths and hardware resources remain unmeasured.
No packed3-bit coordinate implementation,30-bit descriptor or cost advantage
is claimed. Do not compare this static sum with a different model's live peak.

## Preparation fixtures and independent checks

Freeze a NEW16-case preparation plan: identity; eight simple reflections;
two noncommuting orders; inverse pair; two diverse words; repeated word;
minus identity. Three doubled lattice vectors per case,48 materializations.
This plan is independent of the unchanged120-case comparison corpus.

Check all1,920 simple-reflection table entries with the separate rational
reflection oracle and involution checks. Confirm the independent norm-shell root
set, Gram determinant, cofactor inverse and coefficient sign partition. For16
descriptors require independent rational word-matrix agreement, both inverse
orders, exact matrix/materialized vector agreement, Euclidean norm preservation,
240-root permutation action, reduced-word reconstruction and wire round trip.
These3,840 root actions are finite preparation checks, not a Weyl-group sweep.

Seven focused tests cover literal left/right order, inverse metric, shortest-word
length/reconstruction, longest length120, wire identities, table mutation,
malformed IDs/tokens/Gram, bools, input-domain refusal and no caller mutation.
Retain first failures; changed source/context identities halt preparation.
Independent reference algorithms are distinct from independent reviewer sign-off.
Do not infer universal proof or arbitrary scheduling/finite-width behavior.

## Next gate — no automatic execution

1. Independently review the Gram admission proof, basis/index identities,
   composition sides, inverse formulas and descent/reconstruction convention.
2. Freeze metered table construction, validation, coordinate lookup, inverse,
   reduced-word, equality, conversion and materialization schedules.
3. Complete global lifetime/storage and intermediate-width accounting, finite
   refusal controls, cold/warm setup and repeated-vector amortization fixtures.
4. Compare ordinary/reduced words and root-image descriptors under one reviewed
   endpoint policy in a separately scoped campaign; do not modify the current
   comparison. Neither64million nor any hardware width is ratified here.
5. Only after review, define exact command, maximum attempts, per-attempt timeout
   and cumulative allocation; obtain separate explicit owner authorization.

CPU/backend repair remains the physical priority. No synthesis, placement,
routing, bitstreams, board access, RTL changes or hardware integration occur.
