// SPU_WHISPER_RX.v (v1.3 - Variance Accumulator & Channel Stress)
// Objective: Dynamic Clock Calibration, Bias Removal, and channel health monitoring.
// Bias: 1024 (11-bit offset) for negative coordinate support.
//
// New in v1.3:
//   variance_acc  — 16-frame IIR of |pulse_width - k_width_ref|, in units of
//                   clock cycles.  Uses shift-right approximation (÷16 per frame)
//                   so no division hardware is needed.
//   channel_stress[7:0] — saturating right-shift of variance_acc[DEV_SHIFT+7:DEV_SHIFT].
//                   Reaches 0xFF when accumulated deviation ≥ 256 × 2^DEV_SHIFT cycles.
//   variance_alert — asserted when channel_stress hits 0xFF (sustained channel degradation).
//
// DEV_SHIFT (default 4): sets the sensitivity floor.  At DEV_SHIFT=4 one unit of
// channel_stress represents ~16 clock cycles of accumulated pulse deviation.

module SPU_WHISPER_RX #(
    parameter [15:0] BIAS      = 16'd1024,
    parameter        DEV_SHIFT = 4          // sensitivity: 1 stress-unit = 2^DEV_SHIFT cycles
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        pwi_in,
    input  wire        is_cal,        // Trigger Calibration on next pulse (W_sync)
    output reg signed [15:0] surd_a,
    output reg signed [15:0] surd_b,
    output reg         rx_ready,
    // Channel health outputs
    output reg  [7:0]  channel_stress,  // 0x00 = clean, 0xFF = severe degradation
    output reg         variance_alert   // 1 = channel_stress saturated at 0xFF
);

    reg [31:0] counter;
    reg        pwi_last;
    reg [1:0]  state;

    // ── Gearbox (Dynamic K) ───────────────────────────────────────────────
    // N_REF = (1+B)*104 + B*181 for the reference sync frame (a=1, b=0 biased)
    localparam [31:0] N_REF = (1 + BIAS) * 104 + BIAS * 181;
    reg [31:0] k_width_ref;
    initial k_width_ref = (1 + BIAS) * 104 + BIAS * 181;

    // ── Variance Accumulator ──────────────────────────────────────────────
    // IIR: variance_acc += |counter - k_width_ref| - variance_acc>>4
    // (16-tap leaky integrator; no division, pure shifts)
    reg [31:0] variance_acc;
    wire [31:0] dev_raw = (counter >= k_width_ref)
                        ? (counter - k_width_ref)
                        : (k_width_ref - counter);
    wire [31:0] variance_next;
    assign variance_next = variance_acc + dev_raw - (variance_acc >> 4);

    localparam IDLE  = 2'b00;
    localparam COUNT = 2'b01;
    localparam SOLVE = 2'b10;

    localparam INV_104_181 = 47;
    localparam MOD_181     = 181;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state          <= IDLE;
            counter        <= 32'h0;
            pwi_last       <= 1'b0;
            surd_a         <= 16'h0;
            surd_b         <= 16'h0;
            rx_ready       <= 1'b0;
            k_width_ref    <= N_REF;
            variance_acc   <= 32'h0;
            channel_stress <= 8'h0;
            variance_alert <= 1'b0;
        end else begin
            pwi_last <= pwi_in;
            rx_ready <= 1'b0;

            case (state)
                IDLE: begin
                    if (pwi_in && !pwi_last) begin
                        state   <= COUNT;
                        counter <= 32'd1;
                    end
                end

                COUNT: begin
                    if (pwi_in) begin
                        counter <= counter + 32'd1;
                    end else begin
                        state <= SOLVE;
                    end
                end

                SOLVE: begin
                    if (is_cal) begin
                        // Calibration Frame: Update Gearbox; reset variance baseline
                        k_width_ref  <= counter;
                        variance_acc <= 32'h0;
                        state        <= IDLE;
                    end else begin
                        // Data Frame: Reconstruct using Gearbox
                        begin : gear_reconstruct
                            reg [63:0] n_val_long;
                            reg [31:0] n_val;
                            reg [31:0] a_calc;
                            
                            // 1. Reconstruct N = W_data * (N_REF / W_sync)
                            n_val_long = (counter * N_REF) / k_width_ref;
                            n_val = n_val_long[31:0];
                            
                            // 2. Euclidean Decoder: a_biased = (N * 47) % 181
                            a_calc = (n_val * INV_104_181) % MOD_181;
                            
                            // 3. Bias Removal
                            surd_a <= a_calc[15:0] - BIAS;
                            surd_b <= ((n_val - (a_calc[15:0] * 32'd104)) / 32'd181) - BIAS;
                            
                            rx_ready <= 1'b1;
                            state    <= IDLE;
                        end

                        // 4. Update variance accumulator (IIR leaky integrator)
                        variance_acc <= variance_next;

                        // 5. Saturating stress byte: top 8 bits above DEV_SHIFT
                        channel_stress <= (variance_next[31:DEV_SHIFT] >= 32'hFF)
                                        ? 8'hFF
                                        : variance_next[DEV_SHIFT+7:DEV_SHIFT];
                        variance_alert <= (variance_next[31:DEV_SHIFT] >= 32'hFF);
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule
