// spu_node_link.v - Implemented Mother-Satellite Sync Protocol
module spu_node_link (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [23:0] prime_anchor_in, // Broadcast from Mother Laminar Boot
    
    input  wire [15:0] rx_frame,        // [15] snap_alert | [14:7] dissonance | [6:0] payload
    output reg  [31:0] tx_frame,        // [31:16] prime_anchor broadcast | [15:0] payload
    output reg         sync_alert,
    output wire [7:0]  satellite_dissonance
);
    assign satellite_dissonance = rx_frame[14:7];
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sync_alert <= 0;
            tx_frame <= 32'h0;
        end else begin
            // Pack the prime anchor (top 16 bits of the 24-bit prime) and send down
            tx_frame <= {prime_anchor_in[23:8], 16'h0000}; 
            
            // Trigger alert if the Satellite loses 15-Sigma Snap lock
            sync_alert <= (rx_frame[15] == 1'b0); 
        end
    end
endmodule
