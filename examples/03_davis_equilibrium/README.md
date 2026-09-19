# Example 3: Vector Equilibrium & Davis Gate

Loads all 6 cuboctahedron edge-midpoint vectors into Quadray registers QR0–QR5.

## The Math
These vectors are permutations of $(1,1,0,0)$ in Quadray space. Their hexagonal projections sum to exactly $(0,0)$ — Fuller's Vector Equilibrium (VE).
The `EQUIL` instruction asserts that the manifold has zero tension residual.

## Running in the Emulator
```bash
spu sim examples/03_davis_equilibrium/equilibrium.sas --quiet
```
