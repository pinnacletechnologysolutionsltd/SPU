# Golden Core GC-4 — exact icosahedral symmetry classification

**Status:** COMPLETE within the tested finite geometry and software scope

**Date:** 2026-10-16

**Hardware / ISA:** unchanged; no hardware qualification

## Result

The reference model enumerates all 120 adjacency automorphisms of the frozen
12-vertex icosahedron. For each permutation, it derives the unique linear map
from an exact three-vertex basis over `Q(√5)` and checks the map against every
vertex. Exact matrix arithmetic verifies orthogonality and determinant `+1` or
`−1`; the implementation also checks preservation of all 30 edges and 20
triangular faces.

| Carried structure | Admissible maps | Proper | Orientation-reversing |
|---|---:|---:|---:|
| Unlabelled geometry | 120 | 60 | 60 |
| One distinguished vertex / unequal weight at `v00` | 10 | 5 | 5 |
| Unique label on every vertex | 1 | 1 | 0 |

The unlabelled icosahedron has orientation-reversing self-symmetries, so its
mirror is superposable by a proper rotation. A single distinguished vertex
still leaves orientation-reversing maps. Unique labels eliminate every
non-identity map, so that labelled structure is chiral relative to the
specified labels. These are structure-relative finite geometry results, not
claims about physical chirality.

## Evidence and controls

`software/golden_core/symmetry.py` enumerates graph automorphisms by exact
adjacency backtracking and recovers their linear maps. The test suite checks:

- all 120 exact vertex permutations and the `60/60` determinant split;
- exact vertex, edge, face, and metric preservation for every map;
- closure of the enumerated permutations under composition;
- inversion as an orientation-reversing map;
- the label and weight stabilizers in the table;
- rejection of an arbitrary vertex transposition as a geometric symmetry;
- equality of the 60 proper matrices with the retained, independently derived
  flag-based `Q(φ)` rotation catalog in
  `software/tests/test_icosahedral_catalog.py`.

The fixture `fixtures/golden_core_gc4_icosahedral_symmetries.json` freezes all
120 permutations and determinant signs. Its SHA-256 is
`6321eb4d3f753094cabd210588edfc38d726fa4aef4c0b70e39f7e597390d776`.

## Demonstrator

`examples/golden_core/icosahedron_phi.html` now lets the viewer choose the
unlabelled solid, a distinguished/weighted vertex, or unique vertex labels;
selects an admissible exact symmetry; and highlights a vertex and its image.
The distinguished-weight mode marks `v00` with a gold outline and `w2` label;
the other vertices have weight 1. The readout gives exact symbolic coordinates
and the determinant sign. Only the SVG camera, perspective and pixel positions
use approximate floating-point values. The page does not use the SPU GPU.

## Reproduction

```sh
python3 software/tests/test_golden_core_gc4.py
python3 software/tests/test_golden_core_gc3.py
python3 software/tests/test_icosahedral_catalog.py
```

This finite classification completes the stated GC-4 demonstrator scope. It
does not classify arbitrary labelled polyhedra, all golden geometries, or
aperiodic complexes, and it does not qualify a general-purpose symmetry engine
or hardware implementation.

The embedded JavaScript passes `node --check`. Firefox desktop screenshots
were visually reviewed for the unlabelled and distinguished-weight modes; a
mock-DOM interaction check passed for the 120-, 10-, and 1-map structure
filters and vertex selection.
