// spu_pell_cache.v — Last-Known-Good Pell Octave Snapshot (v1.0)
// CC0 1.0 Universal.
//
// Single-register snapshot of the full 832-bit manifold state.
// The register updates only when `stable` is asserted — i.e., the Davis Gate
// has cleared and no cubic leak is present.
//
// On a hard reset following a cubic-leak fault, the caller may load
// `cached_state` back into int_mem instead of re-running the full VE boot
// sequence.  This preserves continuity of the physics manifold across
// transient faults.
//
// Ports:
//   manifold_in[831:0] — live manifold state (from spu_system manifold_state)
//   stable             — 1 = commit snapshot this cycle (connect to ~fault_detected
//                        or davis_gate ok signal)
//   cached_state[831:0]— last committed snapshot
//   restore_valid      — 1 = cached_state holds at least one committed snapshot
//
// Latency: 1 clock cycle (registered snapshot).
// Depends on: nothing.

`timescale 1ns/1ps

module spu_pell_cache (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [831:0] manifold_in,    // live manifold from spu_system
    input  wire         stable,         // commit strobe: Davis Gate cleared
    output reg  [831:0] cached_state,   // last-known-good snapshot
    output reg          restore_valid   // at least one good snapshot exists
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cached_state  <= 832'b0;
            restore_valid <= 1'b0;
        end else if (stable) begin
            cached_state  <= manifold_in;
            restore_valid <= 1'b1;
        end
    end

endmodule
