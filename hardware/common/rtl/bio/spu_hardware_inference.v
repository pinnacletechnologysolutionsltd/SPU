// SPU-13 Hardware-Level Inference (v1.0)
// Target: iCE40LP1K (Nano Sentinel)
// Objective: Autonomous Surprise Detection & Local Self-Correction.
// Logic: Free Energy Principle for Coin-Cell Operation.

module spu_hardware_inference (
    input  wire        clk,
    input  wire        reset,
    
    // --- 1. Sensors (Incoming Wave) ---
    input  wire [31:0] sensor_k,      // Real-time tension from haptics/pulse
    input  wire        sensor_valid,
    
    // --- 2. The Prior (Biological Baseline) ---
    input  wire [31:0] prior_k,       // Your '20-at-40' baseline
    
    // --- 3. Surprise Diagnostic (Outputs) ---
    output reg  [7:0]  free_energy,   // Magnitude of 'Surprise'
    output reg         is_surprised,  // 1: Crimson (Dissonance), 0: Emerald (Laminar)
    output reg  [31:0] correction_v   // Vector to restore equilibrium
);

    // Compute absolute Surprise: |Sensor - Prior|
    wire signed [31:0] diff = sensor_k - prior_k;
    wire [31:0] surprise_mag = diff[31] ? -diff : diff;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            free_energy <= 0;
            is_surprised <= 0;
            correction_v <= 0;
        end else if (sensor_valid) begin
            // Calculate absolute Surprise: |Sensor - Prior|
            // Wires moved outside the block
            
            free_energy <= surprise_mag[31:24]; // Scaled 8-bit energy report
            
            // Threshold for 'High Surprise' (Cubic Pathogen detection)
            if (surprise_mag > 32'h00100000) begin
                is_surprised <= 1;
                correction_v <= prior_k - sensor_k; // Inverse vector to pull back
            end else begin
                is_surprised <= 0;
                correction_v <= 0;
            end
        end
    end

endmodule
