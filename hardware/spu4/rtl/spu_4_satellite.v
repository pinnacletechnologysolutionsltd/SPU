// spu_4_satellite.v
// Lightweight 4D± Quadray Core for iCE40 Nano deployment.
// Functions as a Topological Satellite, streaming dissonance metrics.

module spu_4_satellite (
    input clk,
    input rst_n,
    input [15:0] anchor_in,    // Streamed from SPU-13 Mother
    input [15:0] sensor_in,    // Local reality input
    output [7:0] dissonance,   // 8-bit noise report
    output reg snap_alert      // Local 15-Sigma Snap indicator
);
    // Simplified Active Inference loop
    reg [15:0] local_state;
    
    // We compute the divergence from the local reality.
    // Fixed: The error needs to be unsigned or handled as magnitude in the field.
    wire [15:0] err = (sensor_in > local_state) ? (sensor_in - local_state) : (local_state - sensor_in);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            local_state <= 16'h0;
            snap_alert <= 0;
        end else begin
            // Local state update based on the 8/9 Spread
            // The "anchor_in" acts as a structural guide from the Mother
            local_state <= local_state + (err >> 4) + (anchor_in >> 8); 
            
            // If error is within the "Stiffness" threshold, signal a Snap
            snap_alert <= (err < 16'h0010);
        end
    end
    
    // Normalized noise reporting piped to CLI
    assign dissonance = err[11:4]; 
endmodule
