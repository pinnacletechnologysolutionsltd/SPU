// spu_i2s_out.v
// Master I2S Controller for PCM5102A DAC.
// Converts 24-bit internal surd resonance to standard I2S protocol.
//
// Target: ~61.44 kHz - 62.5 kHz Sample Rate.
// BCLK = clk / 6 = 4 MHz (assuming clk = 24 MHz)
// LRCLK = BCLK / 64 = 62.5 kHz

module spu_i2s_out (
    input  wire        clk,      // System Clock (24 MHz)
    input  wire        rst_n,

    // Audio Control
    input  wire [1:0]  mode,     // 00: Mute, 01: Passthrough (AX0/1), 10: Triage (VCO)
    input  wire [15:0] lfi,      // Laminar Flow Index (from Proprioception)

    // Audio Data (Input)
    input  wire [23:0] left_data,
    input  wire [23:0] right_data,

    // I2S Interface (Output)
    output reg         i2s_bclk,
    output reg         i2s_lrclk,
    output reg         i2s_dout
);

`ifdef DEBUG_VOICE
    // --- Phase Accumulator for Diagnostic Resonance (Triage Mode) ---
    reg [23:0] phase_acc;
    wire [23:0] vco_inc;
    // Map LFI to pitch: 0xFFFF -> ~440Hz, lower LFI -> higher, harsher pitch
    assign vco_inc = 24'd307 + {8'h0, (~lfi[15:0])}; 

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) phase_acc <= 24'd0;
        else        phase_acc <= phase_acc + vco_inc;
    end
    
    // Simple square wave from high-bit of phase accumulator
    wire [23:0] resonance_tone;
    assign resonance_tone = phase_acc[23] ? 24'h1FFFFF : 24'hE00000; // Pulsed resonance
`else
    wire [23:0] resonance_tone = 24'h0;
`endif

    // Mode Multiplexer
    wire [23:0] mux_left, mux_right;
    assign mux_left  = (mode == 2'b01) ? left_data :
                       (mode == 2'b10) ? resonance_tone : 24'd0;
    assign mux_right = (mode == 2'b01) ? right_data :
                       (mode == 2'b10) ? resonance_tone : 24'd0;

    // 1. Clock Dividers
    // BCLK Generation: 24 MHz / 6 = 4 MHz
    reg [2:0] bclk_div;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bclk_div <= 3'd0;
            i2s_bclk <= 1'b0;
        end else begin
            if (bclk_div == 3'd2) begin
                bclk_div <= 3'd0;
                i2s_bclk <= ~i2s_bclk;
            end else begin
                bclk_div <= bclk_div + 3'd1;
            end
        end
    end

    // Detect BCLK falling edge for updating data
    wire bclk_falling = (bclk_div == 3'd2) && i2s_bclk;
    // Detect BCLK rising edge (for tracking bit position)
    wire bclk_rising  = (bclk_div == 3'd2) && !i2s_bclk;

    // 2. Serialization State Machine
    // We use a 6-bit counter (0-63) to track the bit position in the 64-bit frame.
    reg [5:0] bit_cnt;
    reg [31:0] shift_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bit_cnt   <= 6'd0;
            i2s_lrclk <= 1'b0;
            i2s_dout  <= 1'b0;
            shift_reg <= 32'd0;
        end else if (bclk_falling) begin
            bit_cnt <= bit_cnt + 6'd1;

            // LRCLK logic (0 = Left, 1 = Right)
            // Toggles at bit 31 and 63
            if (bit_cnt == 6'd31) begin
                i2s_lrclk <= 1'b1;
                // Load Right Data (MSB first, into position 31 of 32-bit slot)
                shift_reg[31:8] <= mux_right;
                shift_reg[7:0]  <= 8'h0;
            end else if (bit_cnt == 6'd63) begin
                i2s_lrclk <= 1'b0;
                // Load Left Data
                shift_reg[31:8] <= mux_left;
                shift_reg[7:0]  <= 8'h0;
            end else begin
                // Shift data out
                shift_reg <= {shift_reg[30:0], 1'b0};
            end

            // Drive data pin
            i2s_dout <= shift_reg[31];
        end
    end

endmodule
