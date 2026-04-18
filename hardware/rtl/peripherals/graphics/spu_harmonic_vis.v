// SPU-13 Harmonic Visualization Engine (v3.3.37)
// Implementation: Projective Geometry with Coherence Safety Rails.
// Guard: Damping Ratios and Torsional Release to prevent sensory collapse.

module spu_harmonic_vis (
    input  wire         clk,
    input  wire         reset,
    input  wire [15:0]  freq_in,      
    input  wire [7:0]   amplitude,    
    output wire [31:0]  color_out,    
    output wire [63:0]  vector_out,
    output wire         torsion_active
);

    // 1. Octave Nesting & Laminar Buffer
    wire [3:0] octave;
    assign octave = freq_in[15:12];
    wire [11:0] phase;
    assign phase = freq_in[11:0];

    // 2. Torsional Release (Harmonic Overload Protection)
    // If we detect too many octaves stacking, rotate the manifold.
    reg [5:0] torsion_acc;
    always @(posedge clk or posedge reset) begin
        if (reset) torsion_acc <= 6'b0;
        else if (octave > 4'hC) torsion_acc <= torsion_acc + 1;
        else torsion_acc <= torsion_acc;
    end
    assign torsion_active = torsion_acc[5]; // Signal rotation every 64 high-freq ticks

    // 3. Phase-Shift Jitter (Intentional Breathing)
    // Sub-perceptual offset to prevent "blasphemous" perfection.
    wire [11:0] jittered_phase;
    assign jittered_phase = phase + {8'b0, torsion_acc[3:0]};

    // 4. Projective Mapping
    wire signed [31:0] vec_a, vec_b;
    assign vec_a = ($signed({1'b0, jittered_phase}) * $signed({1'b0, amplitude})) >> 8;
    assign vec_b = ($signed({1'b0, octave}) * 32'sd4096); 

    // Rotate vector if torsion is active (1/6 of 60 degrees approx)
    assign vector_out = torsion_active ? {vec_a, -vec_b} : {vec_b, vec_a};

    // 5. Harmonic Color Scaling with Falloff
    // Higher octaves gently fade into the background.
    wire [7:0] damped_amp;
    assign damped_amp = (octave > 4'h8) ? (amplitude >> (octave - 8)) : amplitude;
    
    assign color_out = {
        octave[3:0], 4'h0,      
        phase[11:8],            
        damped_amp[7:4],         
        8'hFF                   
    };

endmodule
