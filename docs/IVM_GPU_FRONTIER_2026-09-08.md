# Rung 4 — native IVM GPU feasibility

Status: research finding and proposed experiment, NOT a ratified RTL contract.
Baseline HEAD: `0891e56`. No RTL, existing oracle or GPU contract changed.
Preserve all qualifications in [the takeover checkpoint](archive/bench_sessions/TAKEOVER_CHECKPOINT_2026-09-08.md).

## Conclusion

A native triangular sample lattice is compatible with integer edge functions.
It does not require a new coverage algebra. Integer IVM vertices do not imply
integer interpolated depth, but exact rational visibility can be implemented
using integer numerators and cross-products. For two affine-depth triangles,
the comparison itself can be an incrementally stepped affine field. This is
mathematically useful but neither IVM-exclusive nor a measured FPGA advantage.

Native means geometry is projected into a declared IVM plane and sampled on
that plane's triangular lattice BEFORE any conventional-display conversion.
It does not mean merely accepting Quadray coordinates before square sampling.
This proposal is point-sampled opaque surface rendering, not volume/voxel
rasterisation, exact area coverage, antialiasing or a perspective renderer.

## Explicit candidate representation and projection

Derivation convention (scale and orientation are explicit choices):

```
eA=(1,1,1), eB=(1,-1,-1), eC=(-1,1,-1), eD=(-1,-1,1)
P = a*eA + b*eB + c*eC + d*eD
E1=eB-eD=(2,0,-2), E2=eC-eD=(0,2,-2)
U=2b-c-d, V=-b+2c-d, h=3a-b-c-d
P = (U*E1 + V*E2 + h*eA)/3
u=U/3, v=V/3
```

E1/E2 have equal squared length 8 and dot product 4: a 60-degree basis.
Orthographic viewing along the eA axis discards the normal term. A depth
convention can define increasing h as farther; its physical scale is fixed.
For zero-sum integer Quadray input, h=4a, U=a+3b and V=a+3c.
Example `(1,0,0,-1)` projects to `(u,v)=(1/3,1/3)`, not an integer site.
Thus even a fixed lattice-aligned view needs an explicit subsite representation.

Use integer (U,V,h) vertices with common denominator 3, and native sample
sites `(U,V)=(3i,3j)` for integer i,j. Do not snap projected vertices silently.
Native unit-pitch metric: `Q(du,dv)=du^2+du*dv+dv^2`; the embedding above adds
a common factor 8. This distinguishes the 3D world lattice from its 2D sample
lattice and from projected vertices; they are not interchangeable objects.

Quadray gauge equivalence follows from the four e vectors summing to zero;
see [Tom Ace's formulas](https://www.minortriad.com/quadray.html). The equations
above are the explicit derivation used here, not an assumed existing GPU ABI.
An integer zero-sum representative is a real restriction: subtracting a tuple's
mean can require quarters. Proposed input validation must check the exact wide
sum, not rely on the legacy 16-bit modular Davis check.

## Coverage, depth and arithmetic boundaries

For counterclockwise vertices p,q,r in the scaled axial chart:

```
E_pq(s) = (q.u-p.u)*(s.v-p.v) - (q.v-p.v)*(s.u-p.u)
D = E_pq(r) > 0
N(s) = E_qr(s)*h_p + E_rp(s)*h_q + E_pq(s)*h_r
h(s) = N(s)/D
```

All E,D,N are integer; depth generally is rational. The constant physical
area factor cancels in barycentric ratios. No square root is needed here.
Shared-edge ownership must be half-open, not three unconditional `>=0` tests.
The probe uses symbolic sample displacement `(+epsilon,+epsilon^2)` to select
one owner. Reverse winding is normalised; zero area is rejected. Production
contract must also pin degenerate handling, sample origin, clipping and ties.

Compare triangles 0 and 1 by `N0*D1 <= N1*D0`, with positive denominators.
For fixed two-triangle rendering, precompute affine coefficients of
`H(s)=D1*N0(s)-D0*N1(s)`; coverage plus H's sign determines the winner with
add-only sample stepping. No reciprocal is necessary for exact visibility in
this narrow case. The same technique works on square lattices.

This does NOT make general depth storage free: serial multi-triangle rendering
needs comparable stored depth (e.g. rational pairs or winner IDs and retained
planes), additional products, or a declared bounded-error depth representation.
Precomputing all pair fields grows quadratically with triangle count.

Widths need proof. If vertices AND evaluated sites satisfy |u|,|v| <= R in the
integer chart and |h| <= Z, conservative bounds are |E|,D <= 8R^2,
|N| <= 24R^2 Z and |H| <= 384R^4 Z. These are deliberately loose full-scan
bounds; inside a covered triangle convexity gives |N| <= D*Z. Include scaled
coordinates, off-triangle scan sites and setup intermediates when sizing.
Python arbitrary precision is not evidence that current 32/56-bit RTL fits.

General camera rotations, perspective, clipping intersections and filtered
attributes extend this domain. Some can retain rational/homogeneous forms;
arbitrary rotations are not closed over integer coordinates or Q(sqrt3).
Do not silently expand this orthographic proposal into a general GPU claim.

## Completed cheapest mathematical probe

Run directly (does not depend on the imperfect aggregate runner):

```bash
python3 software/tools/ivm_raster_feasibility_probe.py
```

| Test | Observed result |
| --- | --- |
| Zero-sum Quadray projection/reconstruction and gauge controls | 343 pass |
| Quadray-generated triangles -> scaled native sites; coverage and depth against Fraction references | 8,100 pass |
| Precomputed affine depth-order field, stepped by additions, versus Fraction plane comparisons | 4,050 pass |
| Two triangles sharing a diagonal | Exactly one owner at all nine interior lattice sites |
| Deliberately all-inclusive edge rule | Three double-owned diagonal sites, as predicted |
| Integer IVM geometry with fractional depth | Depths 12/7 and 3/2 at site (1,1); truncation ties them and selects the wrong first triangle |

Reference coverage uses exact ray crossings in a different affine chart;
reference depth uses Fraction Gaussian elimination. The projection is checked
against a Cartesian tetrahedral embedding. The fixed-seed small population is
not exhaustive; the finite epsilon is sufficient for these bounded cases, not
a proposed hardware implementation. No synthesis, hardware or display-quality
claim. The depth counterexample falsifies integer-valued depth, not integer
representation of rational arithmetic.

## Native/display boundary

Native output should identify epoch, lattice profile, site (i,j), coverage,
colour and optional primitive/depth evidence. Its scan order is a storage and
transport choice, not VGA timing. A rectangular index array is legitimate:
its physical interpretation remains an oblique lattice.

In unit-pitch display coordinates, `x=u+v/2`, `y=sqrt(3)*v/2`.
The geometric mapping introduces sqrt(3), but a surd ALU is NOT mandatory:
fixed display profiles can use precomputed maps or bounded fixed-point
conversion checked against an exact reference. Nearest-site, interpolation,
area filtering and their error/aliasing policies are separate choices.
The existing Bresenham line block is not a 2D reconstruction filter.

A finite set of point samples does not preserve arbitrary subsite triangle
detail. The adapter cannot promise lossless reconstruction of arbitrary sharp
boundaries. Native-first output must accept a defined sampling/filtering loss
or retain richer information. No universal sample-count/quality advantage is
claimed. A half-line CRT stagger alone also does not prove an equilateral
lattice: vertical pitch, beam footprint and colour mask remain physical issues.

## Reuse and contract impact

| Existing component | Disposition proposed, not yet implemented |
| --- | --- |
| Integer edge stepping / row anchoring | Reuse arithmetic pattern; revise widths, site increments and edge ownership |
| Attribute accumulator | Reuse accumulator pattern for N or H; do not silently retain shifted depth as exact |
| Depth reciprocal/dispatch | Retain as measured approximate legacy path; not required by exact two-plane visibility |
| Depth comparator | Coverage mux useful; compare H sign/rational values for proposed exact mode |
| VGA/HDMI timing/HAL | Keep at conventional-output boundary |
| GPU top and board scene constants | Preserve baseline; current video-coupled assembly is not the native scheduler/runtime interface |
| Quadrance accumulator / Bresenham | No automatic raster/filter role from their names |

Existing GPU tranche contract is partially obsolete, not worthless. T1's
shadow-bank principle survives but coefficient-only commit is insufficient.
T2's square-grid colour/Z formats and BRAM assumptions are conditional on
output/depth policy; it is not a prerequisite for a dynamic two-triangle native
experiment. T3 determinant setup remains valid in an oblique chart. T4's camera,
perspective and clipping assumptions are outside the proposed first profile.
Revise and ratify before implementation; preserve old evidence and contracts.

## Minimum coherent runtime interface

Propose one versioned, fixed orthographic Quadray profile first, not an arbitrary
shader/camera language. Packets carry length, epoch, opcode and CRC; semantic
records are BEGIN_SCENE(profile,count), TRI(id, three signed zero-sum Quadrays,
flat colour), PREPARE/COMMIT, and status. Sample pitch/origin/viewport belong to
the profile and epoch. Range, winding, depth and tie rules must be specified.
Receipt acknowledgement is distinct from activation acknowledgement.

Prepare the complete inactive scene: projected vertices, edges, ownership,
depth N/D or H, colours, valid bits, viewport and scaling metadata. COMMIT only
queues a bank already complete and validated. Activate its epoch at a frame
boundary; if not ready, repeat the previous complete frame. No partial commit.
Truncation, bad CRC, bad sum/range and busy requests have deterministic refusal
semantics. Reset discards pending work and starts a defined blank frame.

Explicit snapshot state is required for uninterrupted reception/rendering, but
a framebuffer is NOT required for scene atomicity. Two scene-state banks can
suffice for two triangles. Pipeline tokens must retain their epoch until drained
or activation must occur across a proven empty pipeline; swapping an input
table while depth setup is still running is insufficient. The adapter must not
combine buffered samples from different epochs. Keep one clock for the first
experiment; add a proved handshake if domains are later separated.

## Recommended next experiment and decision gates

One bounded software tranche, estimated 1–2 engineering days: a two-triangle
transactional native-sample renderer using this profile, plus a deliberately
simple declared square-output adapter and matched direct-square reference.
This is a proposed experiment, not authorisation to implement raster RTL.

Exercise the actual software path: packet/Quadray -> validation -> prepared
scene -> epoch activation -> native sites -> adapter. Use deterministic random
and adversarial scenes: projected thirds, both windings, degeneracy, shared
edges, unequal depth denominators, ties, negative coordinates, range extrema,
incomplete transfers and commits around frame boundaries. Record width maxima,
integer operation counts, required scene/line storage and adapter errors. Python
wall-clock speed is not a hardware baseline. Compare at matched physical view,
sample/storage budget and declared filter; report lost subsite features rather
than treating all differences as implementation bugs.

Falsification/stop criteria:

- Any coverage/depth disagreement with independent exact reference falsifies
  the implementation/profile as tested; do not adjust the oracle to pass it.
- Any shared-edge double ownership or hole on a conforming shared tessellation
  fails acceptance (using the declared boundary rule).
- Any mixed-epoch frame, including scale/colour/adapter state, fails atomicity.
  A deliberately swap-before-ready control must fail to make that test useful.
- Any arithmetic overflow within the declared domain fails the proposed width
  contract; revise domain/widths explicitly before synthesis.
- A requirement for lossless conventional reconstruction of arbitrary geometry
  falsifies the sufficiency of point-sample-only native output; choose richer
  samples or a bounded-error output contract, not a hidden extra render.
- If claimed compute/storage savings disappear against the same exact square
  algorithm, reject that claimed advantage. This does not falsify the owner's
  choice of a native representation. Numerical quality/cost thresholds must be
  frozen with the chosen use case before comparative testing, not chosen after.

Owner ratification needed before RTL: fixed orthographic point-sampled first
profile; exact visibility versus approximate stored depth; permitted display
conversion loss and initial scene/domain bounds. No PCB or larger GPU redesign
is justified by these software results. Rung 4 stops here.
