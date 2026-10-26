# Hosted demonstration pages

These static pages are published by MkDocs from this directory and are linked
from the [guided newcomer tour](../NEWCOMER_TOUR.md). Their source counterparts
in the repository are:

| Hosted page | Source file |
| --- | --- |
| `baby-quadray.html` | `examples/gpu/baby_quadray_covariance.html` |
| `icosahedron_phi.html` | `examples/golden_core/icosahedron_phi.html` |
| `gc5b_seed_dynamics.html` | `examples/golden_core/gc5b_seed_dynamics.html` |

The hosted copies are standalone HTML and do not fetch data or execute SPU
instructions. The Quadray and icosahedron pages visualize exact coefficient
operations in browser code; their screen projection is for display. The
dynamics page visualizes a bounded software experiment. None of these pages
establish FPGA pixel equality, compute-shader execution, hardware performance,
or physical claims.

When updating a source page, copy the complete file to its hosted counterpart
and review both files together. Keep the source and hosted versions identical.
