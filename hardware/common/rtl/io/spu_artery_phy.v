// SPU-13 Physical Artery (v1.1)
// Objective: Phase-Locked Synchronicity via Global Buffer (GBUF).
// Logic: Hard-wires the 'Aorta' to the FPGA's high-speed backbone.
//
// PORTABILITY NOTE: The original iCE40 version used SB_GB (Lattice-specific).
// For Gowin (Tang Nano 9K / Primer 20K): replace with a BUFG or simply assign
// directly — nextpnr-gowin promotes high-fanout signals to the global network
// automatically.  The wire assignment below is board-agnostic and zero-latency.
//
// TODO(gowin): validate global routing promotion in post-PnR timing report.

module spu_artery_phy (
    input  wire raw_heartbeat,    // From the Phi-Pulse Generator
    output wire global_heartbeat  // Distributed with zero-skew
);

    // Generic passthrough — synthesizer promotes to global clock network.
    assign global_heartbeat = raw_heartbeat;

endmodule
