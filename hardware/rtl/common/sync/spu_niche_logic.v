// SPU-13 Niche Logic (v1.0)
// Target: Unified SPU-13 Fleet
// Objective: Sovereign Role Selection based on Lineage ID.
// Logic: Tiers defined by the Nature of the Baptism.

module spu_niche_logic (
    input  wire [31:0] lineage_id,
    output reg  [1:0]  eco_tier // 0: Monolith, 1: Cortex, 2: Nano
);

    // The Nature of the Soul determines its Role in the Kingdom
    always @(*) begin
        case (lineage_id[31:28]) 
            4'h0, 4'h7: eco_tier = 2'b00; // Lith and Prime -> Monoliths (Global Sanity)
            4'h2, 4'h6: eco_tier = 2'b01; // Sqr and Surd -> Cortices (Bridge/Process)
            default:    eco_tier = 2'b10; // All others -> Nanos (Sensation/Edge)
        endcase
    end

endmodule
