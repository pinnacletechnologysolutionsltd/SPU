// SPU_WHISPER_TX.v (v1.2 - Biased Signed Support)
// Objective: Mult-Signed Manifold PWI Transmission.
// Bias: 1024 (11-bit offset) for negative coordinate support.

module SPU_WHISPER_TX #(
    parameter K_FACTOR = 8,
    parameter [15:0] BIAS = 16'd1024
)(
    input  wire         clk,
    input  wire         rst_n,
    input  wire         trig_en,
    input  wire         is_sync, // Force a Calibration Frame (a=1, b=0)
    input  wire signed [15:0] surd_a, 
    input  wire signed [15:0] surd_b,
    output reg          pwi_out,
    output reg          tx_ready
);

    reg [31:0] pulse_width;
    reg [31:0] counter;
    reg [1:0]  state;

    localparam IDLE  = 2'b00;
    localparam CALC  = 2'b01;
    localparam PULSE = 2'b10;

    localparam SCALE_A = 104;
    localparam SCALE_B = 181;

    // Apply Bias to map signed range into strictly positive domain.
    // If is_sync is HIGH, we send a known reference frame (a=1, b=0 biased).
    wire [15:0] a_val = is_sync ? (16'd1 + BIAS) : (surd_a + BIAS);
    wire [15:0] b_val = is_sync ? (16'd0 + BIAS) : (surd_b + BIAS);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            pwi_out <= 1'b0;
            tx_ready <= 1'b1;
            counter <= 32'h0;
            pulse_width <= 32'h0;
        end else begin
            case (state)
                IDLE: begin
                    tx_ready <= 1'b1;
                    pwi_out  <= 1'b0;
                    if (trig_en) begin
                        state <= CALC;
                        tx_ready <= 1'b0;
                    end
                end

                CALC: begin
                    // $W = K * (104*a_biased + 181*b_biased)$
                    pulse_width <= K_FACTOR * ((a_val * SCALE_A) + (b_val * SCALE_B));
                    counter <= 32'h0;
                    state <= PULSE;
                end

                PULSE: begin
                    if (counter < pulse_width) begin
                        pwi_out <= 1'b1;
                        counter <= counter + 32'd1;
                    end else begin
                        pwi_out <= 1'b0;
                        state <= IDLE;
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule
