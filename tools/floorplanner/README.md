# Floorplanner research tools

This directory generates deterministic **abstract anchor plans** for physical
design experiments. It does not currently generate build-ready FPGA placement
constraints.

That distinction matters. A Gowin `INS_LOC` constraint targets a packed
primitive at a concrete `R...C...[side][lut]` location. Yosys normally flattens
logical RTL instances, and the FPGA contains heterogeneous LUT, DSP, BSRAM,
clock, and I/O sites. Mapping a logical module name to an approximate row and
column therefore does not constitute a legal floorplan.

The older version of these tools emitted such approximate `INS_LOC` lines. They
were never included by an active build, used names absent from the packed
netlist, omitted slice/LUT indices, and described a GW2A-LV18 approximation even
though the current Tang Primer 25K target is `GW5A-LV25MG121NES`. Those generated
`.cst` files were invalid and have been removed.

## Tools

- `coordinate_transformer.py` maps an **already ordered** list of logical groups
  onto a discrete Hilbert traversal or a Sierpinski-carpet point set. Hilbert is
  the locality-preserving default. The carpet geometry is retained only as an
  explicit de-clustering experiment; it is not called a space-filling traversal.
- `generate_spu4_floorplan.py` generates the historical center-plus-12-neighbor
  SPU-13/Vector-Equilibrium projection as an abstract anchor plan.
- `gowin_tang25k_grid.json` records the nextpnr X/Y bounding box observed for the
  current device. It is not a legal-BEL database.
- `floorplanner_test.py` pins traversal, bounds, collision, and netlist-name
  validation behavior.

## Examples

Generate 13 logical groups in Hilbert order:

```bash
python3 tools/floorplanner/coordinate_transformer.py \
  --geometry hilbert --order 2 --count 13 \
  --prefix spu13_group --output-csv /tmp/spu13_hilbert_plan.csv
```

Generate the projected center-plus-12-neighbor plan:

```bash
python3 tools/floorplanner/generate_spu4_floorplan.py \
  --radius 0.12 --output-csv /tmp/spu13_axis_plan.csv
```

Validate that an explicit ordered list contains exact cell names from a packed
Yosys/nextpnr JSON netlist:

```bash
python3 tools/floorplanner/coordinate_transformer.py \
  --instances /tmp/packed_cell_order.txt \
  --netlist-json build/design.json \
  --output-csv /tmp/validated_anchor_plan.csv
```

Run the focused tests:

```bash
python3 tools/floorplanner/floorplanner_test.py
```

## Required path to a physical experiment

Bartholdi's space-filling-curve heuristic begins with an ordering problem; the
curve does not infer netlist adjacency. A defensible SPU experiment therefore
has four separate stages:

1. Build a weighted connectivity graph from a synthesized design and derive a
   linear order by recursive hypergraph partitioning or another declared
   heuristic.
2. Map that order onto Hilbert anchors, respecting clock regions and the
   LUT/DSP/BSRAM column structure.
3. Legalize packed primitive cells and apply the result with a nextpnr
   `--pre-place` hook or fully specified device constraints.
4. Compare matched unconstrained and seeded builds across multiple seeds using
   route completion, Fmax/WNS, wirelength, congestion, runtime, and variance.

Until all four stages exist and matched builds improve, this directory is a
floorplanning research aid—not evidence that SPU placement uses a Sierpinski or
Hilbert floorplan.

## Attribution

- John J. Bartholdi III, *A Routing System Based on Spacefilling Curves*,
  revised 2003: <https://www2.isye.gatech.edu/~jjb/research/mow/mow.pdf>
- P. Banerjee et al., *FPGA Placement Using Space-Filling Curves: Theory Meets
  Practice*, ACM TECS 9(2), 2009: <https://doi.org/10.1145/1596543.1596546>

`MOW` in Bartholdi's case study means **Meals on Wheels**. The primary paper
does not introduce a data structure called a “MOW-tree”.
