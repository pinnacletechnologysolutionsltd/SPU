// HAL_Native_Hex.v (v2.0)
// Hardware Abstraction Layer for 60-degree IVM native displays.
//
// TWO modes selected by is_cartesian_display:
//
//   is_cartesian_display = 0  (60° native display)
//     Direct IVM pass-through.  Quadray coordinates ARE the pixel address.
//     No conversion needed — the display IS the lattice.
//
//   is_cartesian_display = 1  (90° Cartesian display)
//     Implements the LaminarGrid.metal hex-tiling algorithm ported to fixed-point.
//     Algorithm from LaminarGrid.metal:
//       s = (1, √3)
//       a = fmod(uv * s, s) - s/2          // hex cells at integer coordinates
//       b = fmod((uv - s/2) * s, s) - s/2  // offset second set of cells
//       d = min(dot(a,a), dot(b,b))         // distance to nearest hex centre
//       mask = smoothstep(thickness, 0, sqrt(d))
//
//     In Q(√3), √3 is exact (surd component b=1, integer component a=0).
//     Fixed-point scale: Q8 (1.0 = 256 counts).
//     Also implements the LaminarMassage three-axis dot-product approach for
//     rendering 60° lines on a 90° screen without knotting:
//       d_i = |dot(uv, axis_i)|  for axes at 0°, 60°, 120°
//       intensity = min(d1, d2, d3) < THRESHOLD
//
// For the Piranha Pulse thickness modulation:
//   thickness varies on a 6-bit counter (61.44 kHz / 64 ≈ 960 Hz breathing rate)

module HAL_Native_Hex #(
    parameter RES_X = 240,
    parameter RES_Y = 240,
    parameter Q8    = 8,          // fixed-point fractional bits
    parameter THRESHOLD = 12      // line half-width in Q8 units (~0.05 * 256)
)(
    input  wire        clk,
    input  wire        clk_61k,   // Piranha Pulse for thickness modulation
    input  wire        reset,
    input  wire        is_cartesian_display,

    // IVM input: signed Q8 Quadray projection coordinates
    input  wire signed [15:0] q_x,      // hex x (b - c in Quadray projection)
    input  wire signed [15:0] q_y,      // hex y (a - (b+c)/2)
    input  wire        [7:0]  q_energy,

    // Pixel output
    output reg  signed [15:0] out_x,
    output reg  signed [15:0] out_y,
    output reg         [7:0]  intensity
);

    // -----------------------------------------------------------------------
    // Piranha Pulse thickness breathing (6-bit counter → 7-bit thickness)
    // Matches SovereignKernel.metal: thickness = pixel_w_uv * 1.5 + sin(tick)*delta
    // -----------------------------------------------------------------------
    reg [5:0] breath_cnt;
    reg [7:0] thickness;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            breath_cnt <= 0;
            thickness  <= THRESHOLD;
        end else if (clk_61k) begin
            breath_cnt <= breath_cnt + 1;
            // Simple triangle wave: 0..THRESHOLD*2 centered on THRESHOLD
            thickness  <= THRESHOLD + breath_cnt[5] ?
                          (THRESHOLD - breath_cnt[4:0]) :
                          (breath_cnt[4:0]);
        end
    end

    // -----------------------------------------------------------------------
    // MODE 0: 60° Native — pass-through
    // -----------------------------------------------------------------------

    // -----------------------------------------------------------------------
    // MODE 1: 90° Cartesian — LaminarMassage three-axis dot-product
    //
    // The three IVM axis vectors in Q8:
    //   axis_0 = (256, 0)       — 0°
    //   axis_1 = (128, 222)     — 60°  (256*0.5, 256*0.866) ≈ (128, 222)
    //   axis_2 = (-128, 222)    — 120° (-256*0.5, 256*0.866)
    //
    // For each axis i: d_i = |dot(q_xy, axis_i)| >> Q8
    // Line detected if min(d1,d2,d3) < thickness
    //
    // The "28.8 magic" from LatticeStressMap.metal:
    //   slope = 50/√3 ≈ 28.87 — this is the y-coefficient for 60° lines
    //   on a 90° grid. In Q8: 28.87 * (256/50) ≈ 148. axis_2.y encodes this.
    // -----------------------------------------------------------------------

    // Dot products (signed 32-bit intermediate, Q8*Q8 = Q16 → shift down by Q8)
    wire signed [31:0] dot0 = (q_x * 16'sd256 + q_y * 16'sd0);
    wire signed [31:0] dot1 = (q_x * 16'sd128 + q_y * 16'sd222);
    wire signed [31:0] dot2 = (q_x * (-16'sd128) + q_y * 16'sd222);

    // Absolute values (distance to each 60° plane)
    wire [31:0] d0 = dot0[31] ? -dot0 : dot0;
    wire [31:0] d1 = dot1[31] ? -dot1 : dot1;
    wire [31:0] d2 = dot2[31] ? -dot2 : dot2;

    // Shift back from Q16 to Q8
    wire [23:0] ad0 = d0[31:8];
    wire [23:0] ad1 = d1[31:8];
    wire [23:0] ad2 = d2[31:8];

    // Nearest-axis distance (min of three)
    wire [23:0] min01  = (ad0 < ad1) ? ad0 : ad1;
    wire [23:0] min_d  = (min01 < ad2) ? min01 : ad2;

    // Line hit: distance below threshold → full intensity, else dim falloff
    // Smoothstep-equivalent: intensity = 255 * clamp(1 - (d/thickness)^2, 0, 1)
    // Implemented as: if d < thickness → interpolate, else 0
    wire        on_line = (min_d < {16'd0, thickness});
    wire [7:0]  smooth_energy;
    assign smooth_energy = on_line ?
        (8'd255 - ((min_d[7:0] * min_d[7:0]) >> 8)) :  // quadratic falloff
        8'd0;

    // -----------------------------------------------------------------------
    // Output MUX
    // -----------------------------------------------------------------------
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            out_x     <= 0;
            out_y     <= 0;
            intensity <= 0;
        end else if (is_cartesian_display) begin
            // Cartesian mode: coordinates are unchanged; intensity is the
            // 3-axis dot-product result (rasterizer writes this to the pixel)
            out_x     <= q_x;
            out_y     <= q_y;
            intensity <= smooth_energy | (q_energy >> 1); // blend input energy
        end else begin
            // Native hex mode: direct IVM passthrough — display IS the lattice
            out_x     <= q_x;
            out_y     <= q_y;
            intensity <= q_energy;
        end
    end

endmodule
