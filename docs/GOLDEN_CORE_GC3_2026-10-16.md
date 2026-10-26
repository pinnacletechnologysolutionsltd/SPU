# Golden Core GC-3 — exact icosahedron demonstrator

**Status:** COMPLETE within the tested software scope; no ISA, RTL, or hardware qualification

**Date:** 2026-10-16

## Retained arithmetic inventory

| Retained source | What it contains | GC-3 use and boundary |
|---|---|---|
| `software/tests/test_icosahedral_catalog.py` | Test-only `Qp` arithmetic in the `a+bφ` basis; the 12 vertices formed from cyclic permutations of `(0, ±1, ±φ)`; a flag construction of 60 rotations. | Independent geometry/rotation reference. Its 23 checks passed: every rotation is orthogonal, determinant +1, vertex-set-preserving, and the catalog is closed and inverse-closed. This is not the new reusable field library. |
| `software/lib/tensegrity_balancer.py:Phi` and `software/tests/test_tensegrity_balancer.py` | A separate exact rational-coefficient `a+bφ` implementation with canonical rational coefficients, equality, field division, and exact sign comparison by rational-square comparison. | Independent arithmetic/geometry oracle. The retained test suite passed 44 checks. It is embedded in the balancer module, so GC-3 uses it only as an oracle. |
| `software/lib/irotc_catalog.py`, `software/tests/test_lucas_mac_oracle.py`, Lucas MAC RTL | Fixed-profile/doubled IROTC matrices and quotient-ring arithmetic over `Z[φ]/L_p`. | Kept separate. A quotient ring and its finite-width hardware profile do not qualify arithmetic in the characteristic-zero field `Q(√5)`. |

## GC-3 reference

The new `software/golden_core/exact.py` uses canonical rational pairs
`a+b√5`. It implements exact addition, subtraction, multiplication, division,
conjugation, norm, equality and real-embedding comparison. The golden ratio is
`φ=(1+√5)/2`, so its defining identity is checked exactly. A deterministic
2,048-case comparison checks the new implementation against the retained
`a+bφ` implementation in the tensegrity balancer.

`software/golden_core/icosahedron.py` constructs the standard 12 exact vertices.
The frozen fixture `fixtures/golden_core_gc3_icosahedron.json` records all
coordinates, 30 edges, 20 triangular faces, the 120-degree rotation and a
deliberately perturbed vertex. Exact tests establish edge quadrance 4,
connectivity, degree 5, and rotation determinant +1/order 3. The perturbation
changes the edge count to 25 and disconnects the graph, so the negative
control is detected. Fixture SHA-256 is pinned in the test as
`02e4265f511a968d4926e3e60dbc339e7bda58cdb49dfeeb6a984bd51ce92fca`.

The retained A₅ oracle supplies a broader independent proper-rotation check:
it derives 60 exact rotations and verifies orthogonality, determinant +1,
vertex preservation, closure and inverses. GC-3 reuses this evidence rather
than rebuilding that catalog. This result establishes the stated icosahedron
and one proper rotation in the new reference; it does not qualify the full
symmetry group or general golden geometry.

## Visual demonstrator

`examples/golden_core/icosahedron_phi.html` embeds the fixture's exact vertex,
edge and face data. Visitors can select vertices by dropdown or by clicking
the mesh and see their symbolic `a+bφ` coordinates. The view-yaw control is
display-only. JavaScript approximates `φ` and the camera projection with
floating point; its pixel positions and face shading are not exact geometry
results and do not use the SPU GPU.

## Reproduction

```sh
python3 software/tests/test_golden_core_gc3.py
python3 software/tests/test_icosahedral_catalog.py
python3 software/tests/test_tensegrity_balancer.py
```

The GC-3 tests also verify that the browser page embeds the frozen fixture and
states the approximate-display boundary. A separate mock-DOM interaction check
passed for vertex selection and view changes. No timing, physical, or hardware
claim follows from these results.
