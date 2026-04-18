// spu_governor_mux.v (v1.0)
// Multiplexes up to NUM_SATELLITES Artery serial RX streams into the single
// write port of the Governor's SPU_ARTERY_FIFO.
//
// Each satellite drives a 1-cycle rx_valid pulse when a frame arrives.
// The mux selects one chord per clock cycle and presents it at the FIFO
// write port.  When multiple satellites fire in the same cycle, lowest
// NODE_ID wins (node 0 = highest priority).
//
// Error signals from all satellites are ORed into mux_error so the Governor
// can trigger Henosis if needed.
//
// Port arrays are flattened for Verilog-2001 compatibility:
//   sat_chord[i*64 +: 64] = chord from satellite i
//   sat_node_id[i*3  +: 3] = node_id field from satellite i (should match i)
//
// The output is registered (1-cycle latency from sat_valid to mux_valid).
// This is safe because the satellite sends only one frame per Piranha Pulse,
// and the FIFO is 64 deep — there is no flow-control issue at human timescales.

module spu_governor_mux #(
    parameter NUM_SATELLITES = 4   // 1–7
) (
    input  wire                          clk,
    input  wire                          rst_n,

    // Flattened per-satellite RX inputs from spu_artery_serial_rx instances
    input  wire [NUM_SATELLITES-1:0]     sat_valid,    // rx_valid from each sat
    input  wire [NUM_SATELLITES-1:0]     sat_error,    // rx_error from each sat
    input  wire [NUM_SATELLITES*3-1:0]   sat_node_id,  // 3-bit node_id per sat
    input  wire [NUM_SATELLITES*64-1:0]  sat_chord,    // 64-bit chord per sat

    // Output to Governor SPU_ARTERY_FIFO write port
    output reg         mux_valid,    // = wr_en
    output reg [63:0]  mux_chord,    // = wr_data
    output reg [2:0]   mux_node_id,  // which satellite this chord came from

    // Error aggregation (any satellite reported a bad frame)
    output reg         mux_error
);

    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mux_valid   <= 1'b0;
            mux_chord   <= 64'h0;
            mux_node_id <= 3'h0;
            mux_error   <= 1'b0;
        end else begin
            // Default: nothing valid this cycle
            mux_valid   <= 1'b0;
            mux_chord   <= 64'h0;
            mux_node_id <= 3'h0;
            mux_error   <= |sat_error;

            // Priority mux: iterate high→low so that node 0 (last write) wins.
            // If sat_valid[i] is set, overwrite outputs with satellite i's data.
            for (i = NUM_SATELLITES - 1; i >= 0; i = i - 1) begin
                if (sat_valid[i]) begin
                    mux_valid   <= 1'b1;
                    mux_chord   <= sat_chord  [i*64 +: 64];
                    mux_node_id <= sat_node_id[i*3  +:  3];
                end
            end
        end
    end

endmodule
