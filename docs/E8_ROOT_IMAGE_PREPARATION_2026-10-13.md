# E8 root-image reference tranche — 2026-10-13

Separate software mathematical preparation. Root-image qualification and the
original D4/E8 comparison remain HOLD. No sixth comparison arm was added.
See the [implementation contract](../spu_strategy/contract_e8_root_image_preparation_2026-10-13.md)
and preserved [original proposal](../spu_strategy/contract_e8_root_image_proposal_2026-10-13.md).

The new `software/research/e8_root_images/` reference implements eight-root-image
descriptors, exact Gram admission, sided composition, inverse, materialization,
wire identities and a conventional deterministic reduced-word baseline.
All computations use integers and exact Fractions. No CPU/RTL operation or new
ISA instruction is implemented.

## Preparation evidence

Seven focused tests pass. Short preparation checks cover:

| Check | Bounded preparation scope |
|---|---:|
| Independent simple-reflection table agreement/involution | 1,920 entries |
| Root set / basis validation | 240 roots; physical Gram determinant1 |
| Basis inverse | Gauss-Jordan candidate versus cofactor/Bareiss reference |
| Descriptor fixtures | 16 |
| Root actions | 3,840 |
| Lattice-vector materializations / exact norm checks | 48 |
| Longest-element reduced length | 120 |

The independent rational matrix reference checks chronological composition.
On the all-ones doubled vector, tokens(0,2) produce(0,2,0,0,0,0,0,2), while
(2,0) produce(2,0,0,0,0,0,0,2). This literal distinguishes the two sides/orders.
Both inverse composition orders restore the identity descriptor. A deliberately
naive simple-basis transpose fails the inverse check; G^-1 C^T G succeeds.

Right-descent reduction picks the lowest negative simple-root image ID, checks
each inversion-count decrement and reconstructs the original transformation.
The stripped IDs are already chronological LEFT-action tokens; reversing them
would produce the inverse. Minus identity sends120 positive roots negative and
reconstructs from120 tokens. These checks do not enumerate all Weyl elements.

## Payload and total context are distinct

Eight root IDs require64 payload bits. The implemented self-describing record
is76bytes: header plus root/basis SHA256 identities plus the eight IDs. Altered
versions, identities, reserved IDs, duplicate images and wrong Gram relations
are rejected. Full vectors and matrices are reconstructed only when requested.

The reference's declared fixed-slot static context is307,680bits, including
the roots,8x240 reflection-ID table, coefficient cache, Gram/inverse-basis
tables, positive-root IDs and headers. Basis rows alias the root table.
This is not a complete live-storage or Python memory measurement. Workspace
and arithmetic work remain uninstrumented. A compact payload alone establishes
no efficiency advantage; future comparisons must charge cold setup, admission,
decoding, repeated evaluation and final materialization.

## Admission proof and remaining work

For physical simple-basis B, G=B^T B has determinant1. If root images have
the same Gram matrix, YB^-1 is orthogonal. Images in the unimodular E8 lattice
with that determinant form a full lattice basis, so the map preserves the
lattice and all norm2 roots. The identification of those automorphisms with
the Weyl group is supported by the primary paper
[Winter and van Luijk, The Action of the Weyl Group on the E8 Root System](https://link.springer.com/article/10.1007/s00373-021-02315-8).
The proof chain and this implementation still require independent review.
The separate exact algorithms are not an independent reviewer sign-off.

Conventional root-permutation/matrix and reduced-word baselines are documented
in [Sage Weyl groups](https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/root_system/weyl_group.html).
Sage was not executed and is not a dependency. Root-image descriptors are a
conventional mathematical representation; no SPU novelty is claimed here.

Next: independent proof/operator review, complete primitive/lifetime accounting,
finite-width and work/storage refusal semantics, and cold/warm amortization
fixtures. Existing host references use unbounded exact arithmetic; they do not
qualify a finite processing element. No execution budget or limit is ratified.

Evidence: `build/e8_root_images_20261013/preparation_01/`. Original source,
fixture and diagnostic inventories remain unchanged. Documentation audit's
existing unrelated findings are recorded separately. Surd CPU/Himbächel repair
retains hardware priority; no new FPGA work or qualification campaign is run.
