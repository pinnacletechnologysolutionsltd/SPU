Gowin Sierpinski Constraint Generator (POC)

Files:
- generate_gowin_constraints.py : simple generator (Sierpinski carpet -> INS_LOC .cst + CSV mapping)
- gowin_example_coords.json    : example parameters for quick testing

Quick test:
  python3 generate_gowin_constraints.py --depth 2 --rows 64 --cols 128 --prefix u_spu26/node \
    --output-cst example.cst --output-csv example_map.csv

Next steps:
- Tune map_ivm_to_gowin to match Tang-25k CLB grid, rows/cols and offsets.
- Implement collision resolution (spread points) and minimum spacing.
- Translate row/col -> Gowin LOC tokens if your toolchain expects a different syntax.
- Optionally emit a Verilog wrapper or .ucf/.xdc-style mapping for comparison.
