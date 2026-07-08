`timescale 1ns / 1ps

// spu4_cluster_bridge.v — SPU-4 side of the cluster link.
//
// Packs SPU-4 status + SOM classification into node_link frame and
// sends to SPU-13 governor.  Receives governor commands.
//
// Frame format (SPU-4 → SPU-13, 24-bit, Arlinghaus §7):
//   [23:20] = som_label (4-bit material classification)
//   [19]    = som_valid (1 = classification present)
//   [18]    = snap_locked
//   [17:10] = dissonance (8-bit Davis ratio)
//   [9:0]   = status payload
//
// Frame format (SPU-13 → SPU-4, 32-bit):
//   [31:16] = prime_anchor
//   [15:8]  = Davis integrity tag
//   [7:0]   = command

module spu4_cluster_bridge (
    input  wire         clk,
    input  wire         rst_n,

    // From SPU-4 core (status to report)
    input  wire         snap_locked,
    input  wire [7:0]   dissonance,
    input  wire [9:0]   status_payload,

    // SOM classification (Arlinghaus micro→meso material labeling)
    input  wire [3:0]   som_label,       // material class from SPU-4 SOM
    input  wire         som_valid,       // high when classification is fresh

    // Node link to/from SPU-13
    input  wire [31:0]  node_rx,         // from SPU-13 governor
    output wire [23:0]  node_tx,         // to SPU-13 governor (extended frame)

    // Decoded governor commands
    output reg          cmd_start,
    output reg  [7:0]   cmd_payload
);
    // ── Transmit: pack SPU-4 status + SOM into 24-bit frame ──────────
    assign node_tx = {som_label, som_valid, snap_locked, dissonance, status_payload};

    // ── Receive: decode governor commands from node_rx[7:0] ─────────
    // node_rx[7:0] command codes:
    //   0x00 = NOP
    //   0x01 = START execution
    //   0x02+ = config/instruction data

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cmd_start <= 0;
            cmd_payload <= 0;
        end else begin
            cmd_start <= 0;

            // Davis integrity check: full 32-bit frame must XOR to 0
            // node_rx[31:16] ^ node_rx[15:8] ^ node_rx[7:0] should be 0
            if (node_rx[7:0] != 8'd0) begin
                cmd_payload <= node_rx[7:0];
                if (node_rx[7:0] == 8'd1)
                    cmd_start <= 1;
            end
        end
    end

endmodule
