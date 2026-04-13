Tools/floorplanner — Master Coordinate Transformer

This folder contains a Master Coordinate Transformer prototype to map Sierpinski
(or other tilings) coordinates to Gowin Tang-25k (GW2A-LV18) device grid and
emit INS_LOC (.cst) constraint lines plus a CSV mapping for verification.

Files:
- coordinate_transformer.py : Master script (CLI)
- gowin_tang25k_grid.json  : Default grid parameters (tune for your board)

Quick test:
  python3 coordinate_transformer.py --depth 3 --config gowin_tang25k_grid.json \
    --prefix u_spu26/node --output-cst example_master.cst --output-csv example_master_map.csv

Next improvements:
- Add alternative tilings (Penrose, Ammann-Beenker)
- Add configurable minimum spacing and smarter spread algorithms
- Integrate with build system to emit constraints per-build
- Add a validation pass to check for resource exhaustion
