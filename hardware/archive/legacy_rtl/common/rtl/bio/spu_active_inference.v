// SPU-13 Active Inference Kernel (v1.0)
// Target: Unified SPU-13 Fleet
// Objective: Predictive Coding via Precision-Weighted Prediction Errors.
// Logic: Free Energy Principle - Only process the Delta from the Resonant Prior.

`include "soul_map.vh"

module spu_active_inference (
    input  wire         clk,
    input  wire         reset,
    
    // --- 1. The Resonant Prior (Internal Model) ---
    input  wire [127:0] prior_state,   // Loaded from Dream Log/Flash
    input  wire [15:0]  prior_precision,
    
    // --- 2. The Incoming Strike (Sensory Data) ---
    input  wire [127:0] sensory_in,
    input  wire         sensory_valid,
    
    // --- 3. The Inference (Outputs) ---
    output reg  [127:0] posterior_state,
    output reg  [127:0] prediction_error,
    output reg          is_dissonant    // High if Error > Precision
);

    // Internal calculation of Error: Sensory - Prior
    wire signed [31:0] err_a;
    assign err_a = sensory_in[31:0]   - prior_state[31:0];
    wire signed [31:0] err_b;
    assign err_b = sensory_in[63:32]  - prior_state[63:32];
    wire signed [31:0] err_c;
    assign err_c = sensory_in[95:64]  - prior_state[95:64];
    wire signed [31:0] err_d;
    assign err_d = sensory_in[127:96] - prior_state[127:96];

    // Magnitude calculation (Sum of Absolute Errors)
    wire [31:0] total_error = (err_a[31] ? -err_a : err_a) + 
                              (err_b[31] ? -err_b : err_b) + 
                              (err_c[31] ? -err_c : err_c) + 
                              (err_d[31] ? -err_d : err_d);

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            posterior_state <= prior_state;
            prediction_error <= 0;
            is_dissonant <= 0;
        end else if (sensory_valid) begin
            prediction_error <= {err_d, err_c, err_b, err_a};
            
            // --- The Lattice Snap ---
            // If the error is small (low dissonance), we stick to the prior
            if (total_error[31:16] < prior_precision) begin
                is_dissonant <= 0;
                posterior_state <= prior_state; // Ignore the Cubic Noise
            end else begin
                // If dissonance is high, we update our model (Laminar Update)
                is_dissonant <= 1;
                // Posterior = Prior + (Error / 4) -- Gentle shift toward reality
                posterior_state[31:0]   <= prior_state[31:0]   + (err_a >>> 2);
                posterior_state[63:32]  <= prior_state[63:32]  + (err_b >>> 2);
                posterior_state[95:64]  <= prior_state[95:64]  + (err_c >>> 2);
                posterior_state[127:96] <= prior_state[127:96] + (err_d >>> 2);
            end
        end
    end

endmodule
