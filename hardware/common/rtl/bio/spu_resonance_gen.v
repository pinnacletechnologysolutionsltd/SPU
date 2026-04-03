// SPU-13 Resonance Generator (v1.0)
// Objective: Real-time generation of the Ghost OS "Soul" visual.
// Logic: 4D Quadray deformation -> 2D intensity projection.

module spu_resonance_gen #(
    parameter RES_X = 240,
    parameter RES_Y = 240
)(
    input  wire         clk,
    input  wire         reset,
    input  wire [15:0]  tick,         // Piranha Pulse Sync
    
    // Scanout Interface (from VGA HAL)
    input  wire [15:0]  cur_x,
    input  wire [15:0]  cur_y,
    
    // Output Fragment
    output reg  [7:0]   intensity,
    output reg  [23:0]  rgb_out,
    
    // Bio-Resonance Control
    input  wire [15:0]  ctrl_chord
);

    // 1. UV Normalization (Center = 0,0)
    wire signed [15:0] uv_x = $signed(cur_x) - $signed(RES_X/2);
    wire signed [15:0] uv_y = $signed(cur_y) - $signed(RES_Y/2);

    // 2. Deformation Oscillators (Cordic-Lite)
    // Dynamic modulation from Bio-Chords
    wire [5:0] mod_speed  = ctrl_chord[11:6];
    wire [5:0] radius_add = ctrl_chord[5:0];
    
    // speed_tick = tick * mod_speed (scaled for stability)
    wire [15:0] speed_tick = (tick * mod_speed) >> 3;
    
    wire [7:0] phase_a = (cur_x[7:0] << 2) + speed_tick[7:0];
    wire [7:0] phase_b = (cur_y[7:0] << 2) - (speed_tick[7:0] + (speed_tick[7:0] >> 1));
    
    wire signed [11:0] sin_a, sin_b;
    spu_sin_lut u_sin_a (.phase(phase_a), .sin_out(sin_a));
    spu_sin_lut u_sin_b (.phase(phase_b), .sin_out(sin_b));

    // 3. Distance Calculation: dist = x^2 + y^2
    // We deform the x/y with the sine oscillators
    wire signed [15:0] def_x = uv_x + (sin_a >>> 6);
    wire signed [15:0] def_y = uv_y + (sin_b >>> 6);
    
    wire [31:0] dist_sq = (def_x * def_x) + (def_y * def_y);

    // 4. Golden Prime Dither
    // linear_id = y * width + x
    wire [31:0] linear_id = (cur_y * RES_X) + cur_x;
    wire [15:0] golden_prime = 16'd65521;
    wire [31:0] noise_raw = linear_id * golden_prime;
    wire [7:0]  dither = noise_raw[7:0] >> 4; // Sub-perceptual (5% approx)

    // 5. Core Intensity and Color Mapping
    // Base Solid Core Radius ~ 40 pixels (40*40 = 1600)
    // Dynamic modifier: radius_add adds up to ~64 to the base radius (scaled)
    wire [31:0] dynamic_radius_sq = 1600 + (radius_add << 6); 

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            intensity <= 0;
            rgb_out <= 24'h0;
        end else begin
            if (dist_sq < dynamic_radius_sq) begin
                intensity <= 8'hFF;
                rgb_out <= 24'h19FF99; // Laminar Green/Cyan (0.1, 1.0, 0.6)
            end else begin
                // Exponential Falloff (Approx via shifts)
                // dist_sq >> 7 is a rough curve
                if (dist_sq < 16384) begin
                    intensity <= (8'hFF - dist_sq[13:6]) + dither;
                    rgb_out <= 24'h088050; // Dimmer Cyan
                end else begin
                    intensity <= 8'h05 + dither; // Deep Void
                    rgb_out <= 24'h020305; // Dark Navy
                end
            end
        end
    end

endmodule
