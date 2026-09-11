# Wukong GPU Procedural and Hierarchical Materials Note

Date: 2026-09-11
Status: Deferred research direction; not an engineering contract

## Research premise

Treat a texture as a spatial function attached to a surface rather than only
as a densely stored rectangular image. A future Wukong material path could
evaluate colour or other material properties from surface coordinates and a
compact descriptor.

This direction is deliberately deferred until dynamic geometry loading and
the basic GPU pipeline are stable. It is not part of T1c and authorizes no RTL,
synthesis, or hardware work.

## Candidate representation classes

1. **Procedural material.** Store a generator identifier and parameters, then
   evaluate a deterministic function at `(u,v)`. Early examples include
   checkerboards, stripes, gradients, triangular or hexagonal lattice cells,
   radial regions, distance fields, brick patterns, and deterministic noise.
2. **Hierarchical or fractal material.** Store a compact recursive
   description such as a quadtree, substitution rule, tile grammar, wavelet
   hierarchy, or iterated-function representation. Sampling descends the
   hierarchy and reconstructs a local value.
3. **Procedural base plus sparse corrections.** Generate the structured base
   material and apply optional residual tiles or patches for irregular detail.
   This is the leading long-term candidate because it can retain compactness
   without requiring every surface to be perfectly procedural.
4. **Conventional sampled image.** Retain bitmap textures as a comparison and
   fallback for imagery that does not compress well procedurally.

A possible backend taxonomy is:

```text
TEX0  constant / flat colour
TEX1  procedural primitive
TEX2  hierarchical / fractal material
TEX3  conventional sampled image
```

## Conceptual pipeline

```text
surface coordinate
        |
coordinate transform
        |
procedural or hierarchical evaluator
        |
local material parameters
        |
RGB / normal / roughness / other outputs
```

The representation need not use square texels. Region functions on rational,
triangular, hexagonal, or IVM-aligned lattices may fit the SPU arithmetic model
more naturally.

## Smallest future experiment

The first experiment should be a deterministic procedural colour unit, not a
general fractal engine. A minimal descriptor could contain:

```text
material_type = CHECKER
scale_u
scale_v
colour_a
colour_b
```

Given already-established fixed-point or exact surface coordinates, the unit
would select between the two colours from the parity of the scaled coordinate
cells. The experiment should compare its state, latency, and resource cost
against the simplest conventional lookup that provides the same visible
pattern.

Only after that bounded result should hierarchical subdivision be considered.
A later experiment could ask whether a deterministic hierarchy produces useful
structured surfaces from tens or hundreds of descriptor bytes instead of a
dense texel array.

## Evaluation cautions

- Procedural evaluation is not automatically cheaper than a cached bitmap
  fetch; arithmetic latency and throughput must be measured.
- Simple generators and hierarchies may represent structured patterns well but
  perform poorly on arbitrary photographic imagery.
- Recursion must become a bounded iterative hardware process with a frozen
  maximum detail level.
- Texture-coordinate representation and interpolation must be specified before
  implementation; this note does not select them.
- Any claimed SPU/IVM advantage requires comparison evidence. Mathematical fit
  alone is not a measured hardware advantage.
- A future tranche must remain separate from geometry loading, raster/depth
  stabilization, and framebuffer work.

## Future owner gate

Before implementation, draft a separate owner-authorized contract that freezes
one material primitive, coordinate representation, descriptor format, maximum
evaluation latency, expected vectors, comparison baseline, and simulation-only
or synthesis boundary.
