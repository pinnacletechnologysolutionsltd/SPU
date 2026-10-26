// SU(3) accelerator stub (prototype)
// Approximates matrix exponential exp(X) ≈ I + X (Q16 fixed-point)

module su3_accel_stub (
    input  wire clk,
    input  wire rst_n,
    input  wire start,

    input  wire signed [31:0] g00, g01, g02,
    input  wire signed [31:0] g10, g11, g12,
    input  wire signed [31:0] g20, g21, g22,

    output reg  signed [31:0] e00, e01, e02,
    output reg  signed [31:0] e10, e11, e12,
    output reg  signed [31:0] e20, e21, e22,

    output reg done,
    output reg busy
);

localparam IDLE = 2'd0, BUSY = 2'd1, DONE = 2'd2;
reg [1:0] state;
reg [3:0] ctr;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        done <= 1'b0;
        busy <= 1'b0;
        ctr <= 4'd0;
        e00 <= 32'sd0; e01 <= 32'sd0; e02 <= 32'sd0;
        e10 <= 32'sd0; e11 <= 32'sd0; e12 <= 32'sd0;
        e20 <= 32'sd0; e21 <= 32'sd0; e22 <= 32'sd0;
    end else begin
        case (state)
            IDLE: begin
                done <= 1'b0;
                busy <= 1'b0;
                ctr <= 4'd0;
                if (start) begin
                    busy <= 1'b1;
                    ctr <= 4'd0;
                    state <= BUSY;
                end
            end
            BUSY: begin
                ctr <= ctr + 1'd1;
                if (ctr == 4'd4) begin
                    // exp(X) ≈ I + X  (Q16 fixed-point: 1.0 == 65536)
                    e00 <= (32'sd65536) + g00;
                    e01 <= g01;
                    e02 <= g02;

                    e10 <= g10;
                    e11 <= (32'sd65536) + g11;
                    e12 <= g12;

                    e20 <= g20;
                    e21 <= g21;
                    e22 <= (32'sd65536) + g22;

                    busy <= 1'b0;
                    done <= 1'b1; // one-cycle pulse
                    state <= DONE;
                end
            end
            DONE: begin
                // clear done and return to IDLE
                done <= 1'b0;
                state <= IDLE;
            end
            default: state <= IDLE;
        endcase
    end
end

endmodule
