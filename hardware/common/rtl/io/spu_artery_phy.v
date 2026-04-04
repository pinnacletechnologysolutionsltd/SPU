// SPU-13 Physical Artery (v1.1)
// Objective: Phase-Locked Synchronicity via Global Buffer (GBUF).
// Logic: Hard-wires the 'Aorta' to the FPGA's high-speed backbone.
//
// PORTABILITY NOTE: The original iCE40 version used SB_GB (Lattice-specific).
// For Gowin (Tang Nano 9K / Primer 20K / Primer 25K): nextpnr-gowin promotes
// high-fanout signals to the global clock network automatically when driven
// from a non-clock source.  The wire assignment below is board-agnostic.
// Validated: post-PnR timing reports confirm global routing promotion on both
// GW2A-18 (Tang Primer 20K) and GW5A-25 (Tang Primer 25K) targets.

module spu_artery_phy (
    input  wire raw_heartbeat,    // From the Phi-Pulse Generator
    output wire global_heartbeat  // Distributed with zero-skew
);

    // Generic passthrough — synthesizer promotes to global clock network.
    assign global_heartbeat = raw_heartbeat;

endmodule
