# Quadray coordinates for programmers

A Quadray is a four-component way to address ordinary three-dimensional
tetrahedral geometry. The extra component is deliberate: the four basis axes
point toward the vertices of a regular tetrahedron and their vector sum is
zero.

## One position, many four-tuples

Write a Quadray as

```text
q = (A, B, C, D).
```

Because the four basis vectors sum to zero, adding the same scalar to every
component does not move the represented point:

```text
(A, B, C, D)  ~  (A+k, B+k, C+k, D+k).
```

The components are not restricted to machine floats. In the SPU software
models each component may be an exact element `P + Q·√3`, with rational or
integer `P` and `Q` depending on the layer.

The repo's IVM quadrance is also representation-independent:

```text
Q(q) = Σ (c_i - c_j)²,  for all six pairs i < j.
```

Only component differences occur, so a common offset cancels exactly.

## Normalization: two conventions, two jobs

The host-side `QuadrayVector.normalize()` and `Quadray::normalize()` implement
the traditional point convention: subtract the smallest component from all
four components. For example,

```text
(3, 1, 4, 1) -> (2, 0, 3, 0).
```

Both tuples denote the same point, and the result is canonical because its
minimum component is zero.

The active RTL uses a different representation for displacement vectors:
signed components on the zero-sum hyperplane,

```text
A + B + C + D = 0.
```

The Davis Gate checks that invariant. It does not construct the non-negative
`min=0` form in the hot path. Do not treat canonical point normalization and
the RTL zero-sum invariant as interchangeable operations; choose the
representation required at the API boundary you are using.

## A worked exact rotation

The period-six thirds rotation (ROTC angle 1) leaves `A` fixed and rotates
`B,C,D` with

```text
F = 2/3,  G = 2/3,  H = -1/3

B' = F·B + H·C + G·D
C' = G·B + F·C + H·D
D' = H·B + G·C + F·D.
```

Start with the aligned zero-sum vector `q=(-6,3,0,3)`:

```text
B' = (2·3 - 0 + 2·3)/3 = 4
C' = (2·3 + 2·0 - 3)/3 = 1
D' = (-3 + 2·0 + 2·3)/3 = 1

ROTC_1(-6,3,0,3) = (-6,4,1,1).
```

The result is still zero-sum. Applying inverse angle 4, whose coefficients are
`F=2/3, G=-1/3, H=2/3`, returns `(-6,3,0,3)` exactly.

The alignment matters in integer RTL. The silicon-proven baseline thirds path
uses floor division by three and does not flag a non-divisible lane. Use
lattice-aligned inputs, or the deferred-reduction tagged rotor when its
explicit `MISALIGNED`, `OVERFLOW`, and `INEXACT` fault contract is required.

## Why exactness is preserved

No sine, cosine, square root, or floating-point approximation appears in the
rotation. The coefficients are exact rationals, and `Q(√3)` is closed under
addition and multiplication:

```text
(P₁ + Q₁√3)(P₂ + Q₂√3)
  = (P₁P₂ + 3Q₁Q₂) + (P₁Q₂ + Q₁P₂)√3.
```

The circulant determinant is exactly one, so the inverse is another exact
circulant. This is algebraic exactness, not unlimited range: fixed-width RTL
still needs its documented alignment and overflow preconditions.

## Code map

- `software/lib/rational_robotics.py` is the exact-Fraction rotation oracle.
- `software/spu_vm.py` contains `RationalSurd` and `QuadrayVector`.
- `software/common/include/spu_quadray.h` is the C++ Quadray reference.
- `knowledge/SPU_LEXICON.md` records the canonical-point versus zero-sum-RTL
  distinction.
- `knowledge/isa_reference.md` lists the Quadray opcodes.
