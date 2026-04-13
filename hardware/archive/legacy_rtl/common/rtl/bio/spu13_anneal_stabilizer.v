// SPU-13 Anneal Stabilizer (v1.0)
// Objective: Resolve sub-pixel entropy into Sovereign Stillness.
// Logic: Moves raw coordinates toward the nearest lattice center based on a temperature scale.
// This module acts as the "Cooling Guard" before the Parabolic Projector.

module spu13_anneal_stabilizer (
    input  wire        clk,
    input  wire        reset,
    input  wire [11:0] raw_coord,      // High-precision input from Decoder/CPU
    input  wire [3:0]  temp_scale,     // The "Cooling" factor (higher = faster snap)
    output reg  [11:0] annealed_coord  // The stabilized "Still" coordinate
);

    // Internal "Lattice Center" (The target of the anneal)
    // Snapping to a 64-unit grid (Ultrafinite Lattice Anchor)
    wire [11:0] lattice_center;
    assign lattice_center = (raw_coord + 12'd32) & 12'hFC0; 

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            annealed_coord <= 12'h0;
        end else begin
            // THE COOLING STEP:
            // We move the raw coordinate toward the lattice center 
            // by an amount dictated by the temp_scale (Physical Cooling).
            // This prevents "High-Frequency Wiggle" in the output.
            if (raw_coord > lattice_center) begin
                if ((raw_coord - lattice_center) <= temp_scale)
                    annealed_coord <= lattice_center;
                else
                    annealed_coord <= raw_coord - temp_scale;
            end else if (raw_coord < lattice_center) begin
                if ((lattice_center - raw_coord) <= temp_scale)
                    annealed_coord <= lattice_center;
                else
                    annealed_coord <= raw_coord + temp_scale;
            end else begin
                annealed_coord <= lattice_center; // Locked in Stillness
            end
        end
    end

endmodule
