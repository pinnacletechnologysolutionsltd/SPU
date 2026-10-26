SPU13 Jet MAC blackbox note

The module `spu13_jet_mac.v` (hardware/rtl/core/spu13/spu13_jet_mac.v) contains SystemVerilog multidimensional array ports that are not compatible with the current Yosys Verilog-2005 front-end used in the ECP5 build flow.

For ECP5 bring-up, this module is intentionally excluded from synthesis and treated as a blackbox to allow place-and-route to proceed for IO and top-level verification.

If a full functional synthesis is required later, options include:
 - Converting the SV array ports to Verilog-2005-compatible flattened ports
 - Using a toolchain with SystemVerilog multidimensional array support
 - Writing a small translation script to rewrite common SV patterns

This stub is for documentation only. The build script was modified to exclude the original SV file and let the synthesis tool treat it as a blackbox inferred from instantiations.
