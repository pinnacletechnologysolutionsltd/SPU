# E8 mathematical and accounting review packet — 2026-10-13

Reviewer-ready preparation, not independent sign-off or qualification.
The [contract](../spu_strategy/contract_e8_review_accounting_preparation_2026-10-13.md)
adds only a separate proof dossier, one short metered kernel and cold/warm fixture
preparation. The [original E8 milestone](E8_ROOT_IMAGE_PREPARATION_2026-10-13.md)
and existing comparison evidence remain unchanged.

## Gram admission: necessity and sufficiency argument

Let L be the physical E8 lattice and B its ordered simple-root basis, with
G=B^T B and det(G)=1. Let Y have eight admitted root images as columns. Gram
equality Y^T Y=G gives a unique linear map M=YB^-1 with M^T M=I. In particular,
det(Y)^2=det(B)^2=1; equality does not require positive determinant.

The columns of Y lie in L. Their integral span L' is a full-rank sublattice of
L with the same covolume1. Therefore [L:L']=1 and L'=L. M maps the basis lattice
onto L and permutes its norm2 roots. For E8 these lattice/root automorphisms are
exactly its Weyl group; see the group discussion in section2.2 of
[Winter and van Luijk](https://link.springer.com/article/10.1007/s00373-021-02315-8).
Thus the fixed-context Gram predicate admits precisely the intended transforms.
The derivation relies on the validated E8 basis/lattice and published group
identification; independent review must check those premises and the index step.
It is not a formal proof artifact or an exhaustive enumeration of Weyl elements.

For doubled S=2B, det(S) has magnitude256 and physical Gram is S^T S/4. The
existing cofactor/Bareiss oracle checks the candidate inverse and determinant.
Root/basis hashes and setup validation are prerequisites; eight IDs under an
arbitrary or corrupted context are not covered by the argument. Triality prevents
blindly transferring the same Weyl-membership conclusion to D4.

## Operators and reduced-word convention

LEFT token j sends beta_i to s_j(beta_i), using the reflection permutation.
RIGHT token j sends beta_i to beta_i-G_ij beta_j. General u composed v sends
each alpha_i to u(v(alpha_i)); neither chronological convention changes it.
In Cartesian coordinates M^-1=M^T. In the simple-root basis C=B^-1MB,
C^T G C=G, hence C^-1=G^-1 C^T G. The transpose alone is insufficient.

Coxeter length equals the number of positive roots sent negative. A negative
simple-root image identifies a RIGHT descent and right multiplication reduces
length by1. Choose the lowest such ID deterministically. If stripped tokens are
j1,...,jm and w s_j1 ... s_jm=I, then w=s_jm ... s_j1. The chronological
LEFT-action word is therefore j1,...,jm without reversal. See the conventional
inversion/descent interfaces in [Sage Coxeter groups](https://doc.sagemath.org/html/en/reference/categories/sage/categories/coxeter_groups.html).
The longest E8 element has120 inversions; the existing minus-identity witness
checks120 steps and reconstruction. Independent review remains PENDING.

## Bounded transformation state versus arithmetic width

For the frozen doubled basis, exact table inspection gives row L1(S^-1)<=5,
inverse-basis denominators in{1,2,4}, numerator magnitude<=7, and root-basis
coefficients of magnitude<=6. Because M=YS^-1 with integral Y, normalized
matrix denominators divide4. Orthogonality gives |M_ij|<=1. Those bounds concern
this finite E8 transformation family, not arbitrary scalar/Pell/AOR arithmetic.

For doubled lattice input |X_i|<=A, decoded |c_i|<=5A. A partial coefficient
sum has magnitude<=5A and normalized denominator<=4, so its numerator is
bounded by20A. The next product numerator is bounded by7A. A schoolbook
addition before normalization is therefore bounded by80A+28A=108A and its
denominator by16. Coordinate accumulation Yc is bounded conservatively by80A;
the final orthogonal output actually satisfies |(MX)_i|<=sqrt(8)A<3A.

These are reviewer obligations for a normalize-after-every-operation schedule.
They neither validate all temporary lifetimes nor implement finite-width refusal.
The new fixture generator uses A=2^31. Long unreduced words can grow linearly
in storage even though normalized transformation matrices/root images remain
bounded. Intermediate implementation costs still require measurement.

## Initial accounting increment and outstanding work

The new metered kernel performs two Gram admissions around one LEFT update.
Its proposed pairwise duplicate check differs from the frozen reference's set
operation; the recorded counts belong to that new schedule. One admission has
324 multiplications and324 additions, including index and Gram-scale arithmetic.
The transition has eight table-entry fetches but24 indexed reads in total.
An independent emitted-event replay reconstructs scalar results, work and live
storage. It does not prove that the proposed schedule omitted no required work.

The kernel includes one resident307,680-bit static context, descriptor objects
and modeled frames. It excludes context setup/validation, wire admission, inverse,
right/general composition, equality, reductions and materialization. Complete
accounting remains OPEN. Baselines must pay for their own required machinery;
the full root-image context must not be charged automatically to every baseline.

## Prepared amortization fixtures

384 configuration records vary clients, word length, observation cadence, word
family and ownership regime. They are prepared, not executed as a campaign.
At observation t, every representation must expose w_t(initial_vector); a
checkpoint does not reset transformation state or reinterpret a cumulative
prefix as an incremental update. Inputs match across regime/cadence controls.

Three regimes separate serial cold setup, concurrent private contexts and
concurrent shared tables. Four private root-image contexts alone require
1,230,720 modeled static bits, above the old comparison's proposed1Mi-bit ceiling.
This is a lower-bound calculation; no memory allocation or finite-buffer run
establishes an actual peak. A new profile needs independent scope/limit review.

Four short observer previews and five focused tests check schedule semantics,
fixed inputs, inverse-pair endpoints and metered-kernel counts/ledger controls.
They are not performance measurements and do not establish a crossover point.
The full prepared corpus and a prospective five-approach comparison remain HOLD.

Final metadata checks tightened client/length/cadence types so floats cannot
pass integer-schema comparisons. The first draft snapshot remains preserved;
valid384 configurations and preview inputs did not change.

Evidence: `build/e8_root_images_20261013/workload_preparation_02/`. Independent
reviewer assignment/sign-off, complete accounting, shared/private lifetimes,
reduced-word retention policy and campaign budget remain pending. No new FPGA
work is launched; the Surd CPU backend remains the physical priority.
