# Arlinghaus Spatial Analysis — Application to the SPU-13 Geometry Engine

**Reference:** Sandra Lach Arlinghaus, *Practical Handbook of Spatial Statistics*
(and associated spatial analysis works on hexagonal hierarchies, GIS theory,
and visualization methods)

**Status:** Theoretical alignment document — informs physics layer design,
Davis Law visualisation, and future hierarchical destructible geometry.

---

## 1. Why This Matters

The SPU-13 already lives in the isotropic vector matrix (IVM) — the 3D
hexagonal close-packed lattice Fuller identified as nature's zero-energy ground
state, with Quadray coordinates and the 13-axis cuboctahedron (Vector
Equilibrium) as its natural basis.

Arlinghaus arrives at the same structural conclusion from a completely
independent direction: GIS spatial analysis, cartography, and computational
geography. Her hex-net hierarchies are not an analogy to the SPU-13 geometry —
they are the *same geometry* rediscovered from empirical spatial statistics.
This is independent validation that the IVM/Q(√3) approach is not idiosyncratic
but reflects a deeper truth about how spatial data behaves at scale.

---

## 2. Hex Hierarchies and the Pell Octave

**Arlinghaus's observation:** Hexagonal cell hierarchies allow spatial data to
scale between resolutions without the distortion that plagues square-grid
(cubic) hierarchies. A micro-cell hex breaks cleanly into sub-hexes; a macro
region is a coherent assembly of micro-cells. No irrational distortion is
introduced at the boundary between levels.

**SPU-13 parallel:** The Pell Octave rotor system (see `PELL_OCTAVE.md`)
achieves exactly this: rational rotations that close after 8 steps, with each
step remaining in Q(√3). The Pell orbit `a² − 3b² = 1` is the algebraic
expression of hex-lattice scale invariance.

**Practical implication for the physics layer:**
When implementing hierarchical destructible geometry (future milestone), the
`DavisGasket` must be evaluated at *each LOD level independently* and
propagated upward — a micro-cell fracture (broken tetra bond) must not
corrupt the Davis Ratio of its parent macro-cell. The Arlinghaus hierarchy
model prescribes exactly this independence-then-aggregation structure.

```
Macro-cell: ΣABCD == 0 (Laminar)
  ├── Micro-cell A: ΣABCD == 0 (Laminar)
  ├── Micro-cell B: ΣABCD == ε  (Henosis pending)  ← local fracture initiates
  └── Micro-cell C: ΣABCD == 0 (Laminar)
```

If micro B's Henosis fails, the cubic leak propagates upward and the
macro-cell Davis Gasket fires. This is coherent multi-scale physics without
any floating-point drift accumulating between levels.

---

## 3. Transformations and Pressure-Mediated Impact Regions

**Arlinghaus Chapter 3** covers buffer zones, bisectors, and proximity
transformations — the geometry of "how does an event at point P affect
region R?"

**SPU-13 parallel:** In the Laminar-Doom physics model, a pressure impact at
a Quadray coordinate generates a Quadrance-bounded zone of effect. Since
Quadrance is `Q(u,v) = (u−v)·(u−v)` computed entirely in Q(√3), the impact
radius is an *exact rational boundary* — no square root, no float, no
approximation.

The Arlinghaus buffer zone is thus a Davis-Law-compliant pressure region:

```
Impact at Q0, pressure P:
  Affected zone = { x : Quadrance(x, Q0) ≤ P·K }  — exact, rational
  Outside zone  = ΣABCD unchanged
  Inside zone   = Henosis triggered, Davis Ratio recalculated
```

This maps directly to the `henosis_pulse()` function in `spu_physics.h`.

---

## 4. Colour Classification and the Davis Ratio Display

**Arlinghaus Chapter 4–6** on colour ramps, pixel algebra, and data
classification is directly applicable to the Davis Law live monitor.

The key insight: **geometric interval classification** produces thresholds
that are themselves geometrically coherent — the boundary between LAMINAR
and HENOSIS is not an arbitrary constant but a natural break in Davis Ratio
space. For Q(√3) arithmetic, natural breaks occur at Pell orbit crossings.

### Recommended Davis Ratio colour mapping

| Davis State  | C = τ/K range     | Rational threshold | ANSI Colour |
|-------------|-------------------|--------------------|-------------|
| LAMINAR     | C = (8, 0) ± δ   | Quadrance ≤ unity  | Green       |
| HENOSIS     | C drifting        | ΣABCD ≠ 0, small   | Yellow      |
| CUBIC-LEAK  | C unbounded       | ΣABCD ≠ 0, large   | Red         |
| RECOVERED   | C returned        | post-Henosis       | Cyan        |

The thresholds are *rational* — no float comparison needed. The colour
assignment can be done with a pure integer comparator on the Quadrance of
(C − unity).

This directly informs `software/demos/davis_monitor/main.cpp`.

---

## 5. Map Projections and the Cubic Distortion Argument

**Arlinghaus Chapters 8–9** systematically catalogue how map projections
introduce distortion, and why the choice of projection fundamentally shapes
what the data *appears* to say.

This is the SPU-13's core architectural argument stated from a GIS perspective:
any computation system that forces IVM-native geometry (tetrahedral, hexagonal,
60°) into a Cartesian (cubic, 90°) basis is performing an implicit projection
at every operation. The distortion is not visible as an error — it is baked
into the result as "correct" floating-point output that silently diverges from
physical reality.

The IVM/Q(√3) choice is the equivalent of working in the *native projection*
of the geometry being computed. No reprojection, no drift.

---

## 6. Hierarchical Destructible Geometry (Future Milestone)

Combining Arlinghaus's LOD framework with the Davis Law gasket:

### Fracture propagation model
1. **Micro-cell** — single tetra bond (4 Quadray vertices). Fracture = one
   A_CLKOUT bond breaks, ΣABCD deviates.
2. **Meso-cell** — 13-vertex cuboctahedron. Fracture = multiple micro-cells.
   Davis Gasket fires Henosis if sum of micro-deviations exceeds K.
3. **Macro-cell** — environmental chunk. Assembly of meso-cells. Fracture =
   chunk separation event. Visual LOD switch occurs here.

At each level, `is_cubic_leak()` is evaluated. Laminar recovery via
`henosis_pulse()` is attempted before propagation. Only unrecoverable leaks
propagate upward — exactly matching real material fracture mechanics where
micro-cracks accumulate before macro failure.

### Q(√3) field closure guarantee
Because every computation at every LOD level stays in Q(√3), there is no
float precision cliff at the boundary between LOD levels. The transition from
micro to meso to macro is algebraically exact. This is the property Arlinghaus
was seeking in her spatial hierarchies — she was working around floating-point
projection distortion; we eliminate it at the arithmetic level.

---

## 7. Relationship to Other Knowledge Docs

| Doc | Arlinghaus connection |
|-----|-----------------------|
| `MATHEMATICAL_FOUNDATIONS.md` | Shared lineage: hex basis as "necessary" |
| `PELL_OCTAVE.md` | Hex-hierarchy scale invariance = Pell orbit |
| `RATIONAL_SHADER.md` | Pixel algebra, colour ramps without banding |
| `CLOCK_ARCHITECTURE.md` | Fibonacci timing = hex-hierarchy temporal analogue |

---

## 8. References

- Arlinghaus, S.L. (1994). *Practical Handbook of Spatial Statistics*. CRC Press.
- Arlinghaus, S.L. & Arlinghaus, W.C. Various papers on hexagonal hierarchies
  and spatial synthesis (Solstice: An Electronic Journal of Geography and
  Mathematics).
- Fuller, R.B. (1975). *Synergetics*. Macmillan. (IVM geometry foundation)
- Wildberger, N.J. (2005). *Divine Proportions*. (Q(√3) rational arithmetic)
- Davis, B.R. Universal Geometry framework. (Davis Law Gasket)

---

*CC0 1.0 Universal.*
