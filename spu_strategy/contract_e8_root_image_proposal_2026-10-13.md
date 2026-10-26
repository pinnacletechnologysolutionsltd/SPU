# E8 root-image descriptor — separate research proposal

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_e8_root_image_proposal_2026-10-13.md
```

Date: 2026-10-13. Status: PROPOSAL ONLY; no implementation or campaign launched.
Authority: prepare a separate software-only proposal. Do not add a sixth arm,
change the existing120 fixtures or modify qualified/source-frozen evidence.
No hardware, ISA, AOR-S1 integration or new qualification budget is authorized.

## Conventional representation and precise basis

Freeze the lexicographically sorted240 doubled E8 roots from the existing
mathematical oracle and the exact ordered eight simple roots. Let B have their
physical vectors as columns; G=B^T B is the symmetric Cartan Gram matrix with
diagonal2. For w store r_i=index(w(alpha_i)), i=0..7. Eight unsigned8-bit indices
give a64-bit payload; IDs240..255 are reserved. Add schema/basis/root-table
version identity, header and padding to every reported serialized descriptor.
The payload alone is not complete machine storage.

This is a conventional finite Weyl-group representation, not an SPU invention.
Primary software references expose matrix and root-permutation realizations and
reduced-word operations in [Sage Weyl groups](https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/root_system/weyl_group.html)
and [finite Coxeter groups](https://doc.sagemath.org/html/en/reference/categories/sage/categories/finite_coxeter_groups.html).
Sage is a future optional independent reference, not an executed dependency.
The conventional E8 degrees2,8,12,14,18,20,24,30 multiply to696,729,600; the
information lower bound is30bits. No30-bit encoding is proposed as implemented.

## Admission and proof obligations

Require eight actual integers, no bools, each0..239, matching schema/root/basis
identities. Decode beta_i from the frozen root table. Verify all36 upper-triangle
inner products beta_i dot beta_j = G_ij exactly, with coordinate scaling handled
explicitly. Reject repeated images and Gram disagreements. Do not admit arbitrary
eight-root lists merely because each entry is individually valid.

Proof obligation: Gram equality gives a unique orthogonal map M=Y B^-1, where
Y has beta_i as columns. G has determinant1 and the simple roots form an integral
basis of the unimodular E8 lattice. The admitted images lie in that lattice and
have the same covolume, hence form another lattice basis. M therefore preserves
the lattice and its240 norm2 roots. Use the root-automorphism decomposition and
the absence of E8 Dynkin-diagram automorphisms to conclude M lies in W(E8).
This chain requires independent review; finite tuple sampling is not a proof.
Do not transfer this sufficiency statement to D4, whose diagram has triality.

## Composition conventions

Preserve chronological tokens: append token j by LEFT action w'=s_j composed w.
Precompute T[j,r]=index(s_j(root[r])). Then r'_i=T[j,r_i], exactly eight table
lookups, plus token validation, index reads/writes, ownership and completion work.
Table lookup count is not a total operation count. Verify table membership,
involution, root coordinates and oracle correspondence independently.

RIGHT action w'=w composed s_j gives beta'_i=beta_i-G_ij beta_j because roots
have norm2. Derive and charge exact root-coordinate combinations and root-index
lookup for that update; it is not the same eight-lookups algorithm. Include
noncommuting two-token literals that distinguish left from right action.
General composition u composed v requires applying u to every image supplied by
v; charge basis decoding or a full transient240-root permutation explicitly.

## Inverse and evaluation

Cartesian M=Y B^-1 is orthogonal, so M^-1=M^T. In the simple-root basis C=B^-1Y,
C^T G C=G and C^-1=G^-1 C^T G. Do not use C^T as the inverse in that basis.
Form inverse images M^-1 alpha_i, root-index them, and rerun admission. Require
both composition orders yield identity and independent exact matrix agreement.

For a lattice vector x, solve c=B^-1x exactly, then w(x)=sum_i c_i beta_i.
Charge coefficient conversion, eight-vector accumulation, normalization,
intermediate growth, validation and final materialization. Compare with direct
coordinate reflections, dense matrices, ordinary words and reduced words on
the same inputs/endpoints in a later separately frozen experiment.

## Conventional reduced-word baseline

Use exact positive-root coordinates relative to B. Repeatedly choose the lowest
ID j for which w(alpha_j) is negative and RIGHT-strip s_j, reducing Coxeter
length by1, until identity. If stripped IDs are j1,...,jm, then
w=s_jm ... s_j1. Under the frozen chronological LEFT-action token convention,
reconstruct with the stripping sequence j1,...,jm itself. A conventional matrix
product word instead lists jm,...,j1. Verify both conventions against the exact
matrix; reversing chronological tokens would reconstruct the inverse.
Charge descent searches, coordinate tests, reductions and reconstruction.
Verify reduced length independently using the count of positive roots sent
negative. E8 has120 positive roots; reduced words have at most120 tokens.
No claim that reduced words are unique; fix this deterministic selection policy.
Charge the length header and3-bit IDs, not the original unbounded input word.

## Table and storage costs

At minimum include240 root rows, eight basis IDs, the8x240 reflection-ID table,
Gram and inverse-basis tables, decoding/search metadata, descriptor old/new
buffers and arithmetic workspace. Report table construction, mutable peak,
retained and serialized storage separately, and cold/amortized evaluation.

Raw reflection IDs:8*240*8=15,360bits (1,920bytes), before headers. Full signed64
root coordinates:240*8*64=122,880bits (15,360bytes), before headers. A hypothetical
3-bit signed doubled-coordinate packing costs5,760bits but needs a separately
implemented decoder and range proof; do not compare it as an existing encoding.
Record packed indices versus direct-address table layouts and all padding.
No physical memory, LUT, latency, timing or energy advantage is established.

## Fixtures, controls and later execution gate

Prepare a separate fixture identity: identity, simple reflections, noncommuting
orders, inverse products, a longest-element witness and diverse deterministic
words. Negatives: out-of-range/bool IDs, duplicate images, wrong Gram signs,
table permutation corruption, mismatched root order/version, transpose used as
a simple-basis inverse, left/right confusion and omitted table/decoding costs.
Freeze exact finite widths, work/storage refusal limits, conversion costs and
atomic publication. Preserve source and evidence independently of the existing
comparison. Independent review must accept admission sufficiency, inverse,
composition and reduced-word correctness before proposing a bounded software
qualification command. Separate explicit owner budget is required to launch.
