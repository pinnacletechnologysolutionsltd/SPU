// SPU-13 Whisper Bus Arbiter v1.0
// Manages contention between multiple SPU-4 "Nerve" nodes
// communicating with the SPU-13 "Governor".
// Protocol: Priority-based Request/Grant with Manifold Strike pre-emption.

module spu_bus_arbiter #(
    parameter NUM_NODES = 8
) (
    input  wire                    clk,
    input  wire                    rst_n,
    
    // Request lines from each SPU-4 node (sync_alert/strike bit)
    input  wire [NUM_NODES-1:0]    req_lines,
    
    // Grant lines to each SPU-4 node
    output reg  [NUM_NODES-1:0]    grant_lines,
    
    // Governor (SPU-13) Interface
    output reg                     governor_busy,
    output reg  [2:0]              active_node_id
);

    // Arbiter State
    reg [2:0] priority_ptr; // Round-robin or Priority Pointer

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant_lines <= {NUM_NODES{1'b0}};
            governor_busy <= 1'b0;
            priority_ptr <= 0;
            active_node_id <= 3'd0;
        end else begin
            // 1. Manifold Strike Pre-emption (Highest Priority)
            // If any node signals a Manifold Strike, it gets immediate access
            if (|req_lines) begin
                governor_busy <= 1'b1;
                
                // Priority Encoder (Simple implementation)
                // In a production "Bunker" Forge, this uses a combinatorial
                // priority tree for zero-latency grant.
                casex (req_lines)
                    8'b1xxxxxxx: begin grant_lines <= 8'b10000000; active_node_id <= 3'd7; end
                    8'b01xxxxxx: begin grant_lines <= 8'b01000000; active_node_id <= 3'd6; end
                    8'b001xxxxx: begin grant_lines <= 8'b00100000; active_node_id <= 3'd5; end
                    8'b0001xxxx: begin grant_lines <= 8'b00010000; active_node_id <= 3'd4; end
                    8'b00001xxx: begin grant_lines <= 8'b00001000; active_node_id <= 3'd3; end
                    8'b000001xx: begin grant_lines <= 8'b00000100; active_node_id <= 3'd2; end
                    8'b0000001x: begin grant_lines <= 8'b00000010; active_node_id <= 3'd1; end
                    8'b00000001: begin grant_lines <= 8'b00000001; active_node_id <= 3'd0; end
                    default: begin grant_lines <= 8'b0; governor_busy <= 1'b0; end
                endcase
            end else begin
                governor_busy <= 1'b0;
                grant_lines <= {NUM_NODES{1'b0}};
            end
        end
    end
endmodule
