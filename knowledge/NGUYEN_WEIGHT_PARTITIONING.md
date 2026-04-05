# Nguyen Weight Partitioning — Laminar Translation for SPU-13

## Source
Distilled from Nguyen's recursive metric-space subdivision algorithm (weight-based
treemap / cone-tree partitioning). The Java implementation is discarded; only the
geometric logic is preserved and re-expressed in Q(√3).

## The Three Mappings

### 1. Weight Calculation → Manifold Quadrance Sum

**Nguyen original:**
```
W(v) = 1 + Σ W(child_i)
```

**SPU-13 translation — `laminar_weight()`:**
```
W(axis_i) = quadrance(QR[i])          # scalar weight of one axis
W(manifold) = Σᵢ W(axis_i)           # total manifold weight
```
Weight is the *Total Quadrance* of the 13-axis manifold sector, or more precisely
the sum of all 13 Quadray quadrances. This is a RationalSurd — exact, no float.

**Hardware use:** The Davis Gate uses W(manifold) to allocate the 832-bit register
file. High-weight axes receive full 64-bit (p:32 / q:32) depth; low-weight axes
get the "Shim" (16-bit packed). This is a synthesis-time decision on the 25K BRAM18
blocks (26 available on GW5A-25A).

### 2. Area Partitioning → IVM Wedge Allocation

**Nguyen original (rectangular):**
```
A_i = (W_i / Σ W_j) × A_total
```

**SPU-13 translation — `wedge_fraction()`:**
```
wedge_i = (W(QR[i]), W(manifold))     # exact rational pair (numer, denom)
```
Instead of A_total being a rectangle, it is the *Vector Equilibrium* — the 360°
solid angle of the 13-axis IVM nucleus. The `wedge_fraction` is a RationalSurd
pair (numer, denom) — no atan2, no π, no float.

**60° guarantee:** Because weights are Quadray quadrances (sum of Q(√3) differences),
and the Pell invariant norm==1 holds for all rotors, the wedge boundaries are
bit-exact. No two axes ever collide in memory or on screen.

**Render graph use:** `wedge_fraction` directly drives the hex-hierarchy LOD
decision. High-weight axes get micro-cell resolution; low-weight get macro-cell.
This is the bridge between Nguyen's tree and Arlinghaus's hex hierarchy.

### 3. Wedge Angle → Rational Spread

**Nguyen original:**
```
ψ_i = (W_i / Σ W_children) × Ψ_parent
```

**SPU-13 translation:**
Ψ_parent = total spread of parent sector = Σ spread(QR[i], QR[j]) over active axes.
This replaces atan2 with Wildberger's Rational Spread (always rational in Q(√3)).

**Implementation:** `manifold_spread_sum()` in `spu_ivm.h` computes this.

### 4. Distortion / Semantic Zoom → Pell Octave Snap

**Nguyen original (transcendental):**
```
d(P', F) = ((s+1) × d(P,F)) / (s × d(P,F) + 1)
```

**SPU-13 translation — `pell_zoom()`:**
Replace the smooth fish-eye with *discrete Pell Octave steps*. As the user zooms
into the Laminar-Doom map, the geometry snaps to the next IVM scale level:
```
scale_n = pell_orbit[n]   # (1,0), (2,1), (7,4), (26,15), (97,56)...
```
Each "zoom level" is a Pell step — exact in Q(√3), no distortion, no float.
The map "breathes" between scales rather than smoothly warping.

## RAM Mapping: Fractal vs. Nguyen-Weight

These are **orthogonal** and should be combined:

| Layer | Mechanism | What it optimises |
|-------|-----------|-------------------|
| **Fractal leaves** | Bit-interleaved addressing, "7-pixel sip" | *Spatial* locality (IVM neighbours near in memory) |
| **Nguyen weight** | Quadrance-sum priority | *Semantic* locality (hot axes in BRAM, cold in PSRAM) |

The fractal layer is already correct and should remain. The Nguyen weight layer
sits above it as a *cache placement policy*: at synthesis time, `laminar_weight()`
decides which of the 13 manifold axes gets BRAM18 (fast, synchronous) vs.
PSRAM/SDRAM (slow, burst). On the GW5A-25A, this is the difference between
1-cycle and 8-cycle memory access.

## Software Distribution Use

`CalculateLaminarWeight()` is a natural linker/loader primitive:

1. Parse the `.sas` Lithic-L program AST
2. For each referenced manifold sector, compute W(sector) = Σ quadrances
3. Sort sectors by weight → pre-position in memory layout:
   - W > threshold_high → BRAM18 (on-chip)
   - W > threshold_mid  → SDRAM (burst cached)
   - W ≤ threshold_mid  → PSRAM (background load)

Because thresholds are RationalSurd comparisons (rs_lt), this decision is
**bit-exact at compile time** — the loader never guesses.

## Implementation Target in spu_ivm.h

```cpp
// Weight of a single axis
RationalSurd axis_weight(const Quadray& q);

// Total manifold weight: Σ axis_weight(QR[i]) for i in 0..12
RationalSurd laminar_weight(const Manifold13& m);

// Wedge fraction for axis i: (W(QR[i]), W(manifold)) — exact rational
struct WeightFraction { RationalSurd numer, denom; };
WeightFraction wedge_fraction(const Manifold13& m, int axis_i);

// BRAM tier for an axis given total manifold weight
enum class BramTier { BRAM18, SDRAM, PSRAM };
BramTier bram_tier(const WeightFraction& wf);
```

## Connection to `CalculateLaminarWeight()` Demo

As the first real use case: implement a terminal display of the weight tree for
a 13-axis manifold initialised with the IVM canonical basis. Show:
```
Axis  QR[i]           Weight    Wedge%    Tier
 0    [(2,1)(0,0)...]  (7,4)     8.3%     BRAM18
 1    [(0,0)(2,1)...]  (7,4)     8.3%     BRAM18
...
12    [(0,0)...]       (0,0)     0.0%     PSRAM
```
This is the "Heartbeat" function — it tells the 25K how to breathe the 13D data.

## Reference
- Nguyen, Q.V. (2005 era) — recursive metric-space treemap with weight-proportional
  partitioning and distortion-based semantic zoom
- Wildberger, N.J. — Rational Trigonometry: Spread replaces angle
- Fuller, R.B. — Synergetics: IVM as zero-energy ground state
- Arlinghaus, S.L. — Hex hierarchies as natural scale-invariant partitioning
- Davis Law: ΣABCD == 0 is the global laminar stability predicate
