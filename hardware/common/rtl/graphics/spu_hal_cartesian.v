// spu_hal_cartesian.v (v2.0)
// Hardware Abstraction Layer for 90-degree (Cartesian) SPI displays.
//
// Pipeline:
//   1. Quadray → centered Q8 screen coordinates
//   2. LaminarMassage 3-axis dot-product (ported from LaminarMassage.metal)
//      Three NORMAL vectors at 0°/120°/240° detect lines at 90°/30°/150° —
//      a 60°-symmetric IVM star that "de-cubes" the Cartesian grid.
//        d_i = |dot(uv_centred, normal_i)|  →  min(d1,d2,d3)  →  linear smoothstep
//   3. Sub-pixel RGB prime weighting (from DQFA.metal r_weights/g_weights)
//      Weights 179/59/17 (primes, sum=255) applied per sub-pixel channel.
//   4. RGB565 packing
//   5. ST7789 SPI state machine (8-bit shift register, 4-wire SPI)
//
// Normal vectors for 60°-symmetric line set (Q8 unit circle × 256):
//   n1 = ( 256,   0)   → detects vertical line  (x=0 axis)
//   n2 = ( 128, 222)   → detects line at 30°     (cos30=0.866, sin30=0.5 swapped)
//   n3 = (-128, 222)   → detects line at 150°
//
// LaminarMassage reference: reference/synergeticrenderer/demos/renderer/LaminarMassage.metal
// Sub-pixel weights:        reference/synergeticrenderer/demos/renderer/DQFA.metal L67-69

// Hardware Abstraction Layer for 90-degree (Cartesian) SPI displays.
//
// Pipeline:
//   1. Quadray → centered screen coordinates (Q8 fixed-point)
//   2. LaminarMassage 3-axis dot-product (ported from LaminarMassage.metal)
//      Three axes at 0°/60°/120° — the "de-cuber" for 90° screens.
//      d_i = |dot(uv_centred, axis_i)|  →  min(d1,d2,d3)  →  smoothstep
//   3. Sub-pixel RGB prime weighting (from DQFA.metal r_weights/g_weights)
//      Weights 179/59/17 (primes, sum=255) applied per sub-pixel channel.
//   4. RGB565 packing
//   5. ST7789 SPI state machine (8-bit shift register, 4-wire SPI)
//
// Axis vectors in Q8 (×256 from unit circle):
//   Axis 1 ( 0°): ( 256,   0)   → d1 = |uv_x|
//   Axis 2 (60°): ( 128, 222)   → cos60*256=128, sin60*256≈222
//   Axis 3 (120°):(-128, 222)   → cos120*256=-128, sin120*256≈222
//
// LaminarMassage reference: reference/synergeticrenderer/demos/renderer/LaminarMassage.metal
// Sub-pixel weights: reference/synergeticrenderer/demos/renderer/DQFA.metal lines 67-69

module spu_hal_cartesian #(
    parameter RES_X    = 240,
    parameter RES_Y    = 240,
    parameter Q8       = 8,         // fixed-point fractional bits
    parameter THRESHOLD = 20,       // line half-width in Q8 units
    parameter CLK_DIV  = 4          // SPI clock divider (clk / CLK_DIV = SPI rate)
)(
    input  wire        clk,
    input  wire        reset,

    // Laminar display bus signals (from spu_hal_interface.vh convention)
    input  wire [15:0] q_a,
    input  wire [15:0] q_b,
    input  wire [15:0] q_c,
    input  wire [15:0] q_energy,
    input  wire [15:0] rational_scale,
    input  wire        pulse_61k,
    output wire        display_ready,

    // SPI display interface (ST7789 / compatible 4-wire)
    output reg         spi_cs_n,
    output reg         spi_sck,
    output reg         spi_mosi,
    output reg         spi_dc
);

    // -------------------------------------------------------------------------
    // 1. Quadray → centered Q8 screen coordinates
    // -------------------------------------------------------------------------
    // Projection: x = b - c,  y = a - (b+c)/2  (IVM → Cartesian isometric)
    wire signed [16:0] raw_x = $signed({1'b0, q_b}) - $signed({1'b0, q_c});
    wire signed [16:0] raw_y = $signed({1'b0, q_a}) -
                               (($signed({1'b0, q_b}) + $signed({1'b0, q_c})) >>> 1);

    wire [47:0] scaled_x  = raw_x * rational_scale;
    wire [47:0] scaled_y  = raw_y * rational_scale;

    // Pixel coordinates (screen origin at top-left)
    wire [15:0] target_x  = scaled_x[31:16] + (RES_X >> 1);
    wire [15:0] target_y  = scaled_y[31:16] + (RES_Y >> 1);

    // Centre the UV for the LaminarMassage — signed offset from screen centre
    wire signed [15:0] uv_x = $signed(target_x) - (RES_X >> 1);
    wire signed [15:0] uv_y = $signed(target_y) - (RES_Y >> 1);

    // -------------------------------------------------------------------------
    // 2. LaminarMassage — three 60°-axis dot products
    // Axis vectors (Q8 unit circle × 256):
    //   axis1 = ( 256,   0)   axis2 = (128, 222)   axis3 = (-128, 222)
    // dot products are Q8×Q8 = Q16; take [15:8] to restore Q8 magnitude.
    // -------------------------------------------------------------------------
    wire signed [31:0] dot1 = (uv_x * 16'sd256  + uv_y * 16'sd0  );  // |uv_x| * 256
    wire signed [31:0] dot2 = (uv_x * 16'sd128  + uv_y * 16'sd222);
    wire signed [31:0] dot3 = (uv_x * (-16'sd128) + uv_y * 16'sd222);

    // Absolute values, scaled back to Q8
    wire [15:0] d1 = (dot1[31] ? ~dot1[23:8] + 1 : dot1[23:8]);
    wire [15:0] d2 = (dot2[31] ? ~dot2[23:8] + 1 : dot2[23:8]);
    wire [15:0] d3 = (dot3[31] ? ~dot3[23:8] + 1 : dot3[23:8]);

    wire [15:0] min_d2  = (d2 < d3) ? d2 : d3;
    wire [15:0] min_d   = (d1 < min_d2) ? d1 : min_d2;

    // Piranha Pulse thickness breathing: ±4 Q8 units at ~960 Hz
    reg [5:0] breath_cnt;
    always @(posedge clk or posedge reset)
        if (reset) breath_cnt <= 0;
        else if (pulse_61k) breath_cnt <= breath_cnt + 1;

    wire [7:0] threshold_live = THRESHOLD + breath_cnt[5:3]; // 3-bit modulation

    // Quadratic smoothstep: intensity = 255 * (T - min_d)^2 / T^2  (clamp to 0)
    wire signed [15:0] remain = $signed({1'b0, threshold_live}) - $signed({1'b0, min_d[7:0]});
    wire        [7:0]  base_i = (remain > 0) ?
                                  ((remain * remain * 8'd255) >> 14) :
                                  8'd0;

    // Blend with q_energy so manifold tension darkens the line
    wire [7:0] intensity = base_i;

    // -------------------------------------------------------------------------
    // 3. Sub-pixel RGB prime weighting  (DQFA.metal lines 67-69)
    //    R = intensity × 179/255 ≈ intensity × (128+32+16+2+1) >> 8
    //    G = intensity × 59/255  ≈ intensity × (32+16+8+2+1)   >> 8
    //    B = intensity × 17/255  ≈ intensity × (16+1)           >> 8
    // -------------------------------------------------------------------------
    wire [15:0] chan_r = (intensity << 7) + (intensity << 5) +
                         (intensity << 4) + (intensity << 1) + intensity;
    wire [15:0] chan_g = (intensity << 5) + (intensity << 4) +
                         (intensity << 3) + (intensity << 1) + intensity;
    wire [15:0] chan_b = (intensity << 4) + intensity;

    wire [7:0] r8 = chan_r[15:8];   // >> 8
    wire [7:0] g8 = chan_g[15:8];
    wire [7:0] b8 = chan_b[15:8];

    // -------------------------------------------------------------------------
    // 4. RGB565 packing
    // -------------------------------------------------------------------------
    wire [15:0] rgb565 = {r8[7:3], g8[7:2], b8[7:3]};

    // -------------------------------------------------------------------------
    // 5. ST7789 SPI state machine
    //    Streams one 16-bit pixel per pulse_61k tick.
    //    DC=1 for data bytes; the display is assumed pre-initialised in RAMWR mode.
    //    Bit-bangs at clk/CLK_DIV rate.
    // -------------------------------------------------------------------------

    // SPI shift engine: load 16-bit word, clock out MSB-first
    localparam SPI_IDLE  = 2'd0;
    localparam SPI_LOAD  = 2'd1;
    localparam SPI_SHIFT = 2'd2;
    localparam SPI_DONE  = 2'd3;

    reg [1:0]  spi_state;
    reg [15:0] spi_shreg;   // shift register
    reg [3:0]  spi_bit_cnt; // bits remaining (0..15)
    reg [2:0]  clk_div_cnt; // CLK_DIV counter

    // Latch pixel on pulse_61k rising edge; start SPI burst
    reg [15:0] pixel_latch;
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            pixel_latch  <= 16'h0;
            spi_state    <= SPI_IDLE;
            spi_shreg    <= 16'h0;
            spi_bit_cnt  <= 4'd0;
            clk_div_cnt  <= 3'd0;
            spi_cs_n     <= 1'b1;
            spi_sck      <= 1'b0;
            spi_mosi     <= 1'b0;
            spi_dc       <= 1'b0;
        end else begin
            case (spi_state)
                SPI_IDLE: begin
                    spi_cs_n <= 1'b1;
                    spi_sck  <= 1'b0;
                    if (pulse_61k) begin
                        pixel_latch <= rgb565;
                        spi_state   <= SPI_LOAD;
                    end
                end

                SPI_LOAD: begin
                    spi_cs_n    <= 1'b0;   // assert chip select
                    spi_dc      <= 1'b1;   // data (not command)
                    spi_shreg   <= pixel_latch;
                    spi_bit_cnt <= 4'd15;
                    clk_div_cnt <= 3'd0;
                    spi_sck     <= 1'b0;
                    spi_state   <= SPI_SHIFT;
                end

                SPI_SHIFT: begin
                    clk_div_cnt <= clk_div_cnt + 1;
                    if (clk_div_cnt == CLK_DIV - 1) begin
                        clk_div_cnt <= 3'd0;
                        spi_sck <= ~spi_sck;
                        if (!spi_sck) begin
                            // Rising edge: present next bit
                            spi_mosi  <= spi_shreg[15];
                            spi_shreg <= {spi_shreg[14:0], 1'b0};
                        end else begin
                            // Falling edge: advance bit counter
                            if (spi_bit_cnt == 0)
                                spi_state <= SPI_DONE;
                            else
                                spi_bit_cnt <= spi_bit_cnt - 1;
                        end
                    end
                end

                SPI_DONE: begin
                    spi_cs_n  <= 1'b1;
                    spi_sck   <= 1'b0;
                    spi_state <= SPI_IDLE;
                end
            endcase
        end
    end

    assign display_ready = (spi_state == SPI_IDLE);

endmodule
