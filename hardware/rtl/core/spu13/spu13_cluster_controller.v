`timescale 1ns / 1ps

// spu13_cluster_controller.v — SPU-13 side arbitrator for N SPU-4 satellites.
//
// Manages bidirectional communication with up to 8 SPU-4 satellites
// over spu_node_link protocol.  Exposes a register interface to the
// SPU-13 core.

module spu13_cluster_controller #(
    parameter NUM_SATELLITES = 4
) (
    input  wire         clk,            // SPU-13 domain clock
    input  wire         rst_n,

    // Satellite links (one port per satellite)
    input  wire [31:0]  sat_rx [0:NUM_SATELLITES-1],
    output wire [15:0]  sat_tx [0:NUM_SATELLITES-1],

    // Status registers (readable by SPU-13)
    output reg  [15:0]  sat_status [0:NUM_SATELLITES-1],
    output wire [15:0]  sat_quad_A [0:NUM_SATELLITES-1],
    output wire [15:0]  sat_quad_B [0:NUM_SATELLITES-1],
    output wire [15:0]  sat_quad_C [0:NUM_SATELLITES-1],
    output wire [15:0]  sat_quad_D [0:NUM_SATELLITES-1],

    // Command broadcast (to all or selected satellite)
    input  wire         cmd_valid,
    input  wire [3:0]   cmd_target,     // 0 = broadcast, 1-N = specific
    input  wire [15:0]  cmd_frame
);

    genvar s;
    generate
        for (s = 0; s < NUM_SATELLITES; s = s + 1) begin : g_sat
            // Demux: only selected satellite gets the command
            wire send = cmd_valid && (cmd_target == 0 || cmd_target == s + 1);
            assign sat_tx[s] = send ? cmd_frame : 16'h0000;

            // Status: unpack from sat_rx[31:0]
            // sat_rx[31:16] = prime anchor (top), sat_rx[15:0] = snap/dissonance/payload
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    sat_status[s] <= 0;
                else
                    sat_status[s] <= sat_rx[s][15:0];
            end
        end
    endgenerate

endmodule
