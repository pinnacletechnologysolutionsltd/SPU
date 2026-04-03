// SPU_WHISPER_RX.v (v1.2 - Gearbox Calibration & Signed Support)
// Objective: Dynamic Clock Calibration & Bias Removal.
// Bias: 1024 (11-bit offset) for negative coordinate support.

module SPU_WHISPER_RX #(
    parameter [15:0] BIAS = 16'd1024
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        pwi_in,
    input  wire        is_cal,   // Trigger Calibration on next pulse (W_sync)
    output reg signed [15:0] surd_a,
    output reg signed [15:0] surd_b,
    output reg         rx_ready
);

    reg [31:0] counter;
    reg        pwi_last;
    reg [1:0]  state;

    // The Gearbox (Dynamic K)
    // N_REF = (1+B)*104 + B*181 for the reference sync frame (a=1, b=0 biased)
    localparam [31:0] N_REF = (1 + BIAS) * 104 + BIAS * 181;
    reg [31:0] k_width_ref; // Measured W_sync
    initial k_width_ref = (1 + BIAS) * 104 + BIAS * 181; // Default: K=1

    localparam IDLE  = 2'b00;
    localparam COUNT = 2'b01;
    localparam SOLVE = 2'b10;

    localparam INV_104_181 = 47;
    localparam MOD_181     = 181;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            counter <= 32'h0;
            pwi_last <= 1'b0;
            surd_a <= 16'h0;
            surd_b <= 16'h0;
            rx_ready <= 1'b0;
            k_width_ref <= N_REF; // use parameterized default, not hardcoded K=8/BIAS=1024
        end else begin
            pwi_last <= pwi_in;
            rx_ready <= 1'b0;

            case (state)
                IDLE: begin
                    if (pwi_in && !pwi_last) begin
                        state <= COUNT;
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
                        // Calibration Frame: Update Gearbox
                        k_width_ref <= counter;
                        state <= IDLE;
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
                            
                            // 3. Bias Removal: surd_a = a_biased - BIAS
                            surd_a <= a_calc[15:0] - BIAS;
                            surd_b <= ((n_val - (a_calc[15:0] * 32'd104)) / 32'd181) - BIAS;
                            
                            rx_ready <= 1'b1;
                            state <= IDLE;
                        end
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule
