// spu_multiplier_serial.v
// A 16-bit sequential (shift-and-add) multiplier.
// Saves LUTs on DSP-less FPGAs (iCE40 LP1K).

module spu_multiplier_serial (
    input  wire        clk,
    input  wire        reset,
    input  wire        start,
    input  wire [15:0] a,
    input  wire [15:0] b,
    output reg  [31:0] product,
    output reg         done
);

    reg [31:0] a_shifted;
    reg [15:0] b_reg;
    reg [4:0]  count;
    reg        busy;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            product <= 32'h0;
            done <= 0;
            busy <= 0;
            count <= 0;
            a_shifted <= 0;
        end else if (start && !busy) begin
            a_shifted <= {16'h0, a};
            b_reg <= b;
            product <= 32'h0;
            count <= 5'd16;
            busy <= 1;
            done <= 0;
        end else if (busy) begin
            if (count > 0) begin
                if (b_reg[0]) begin
                    product <= product + a_shifted;
                end
                a_shifted <= a_shifted << 1;
                b_reg <= b_reg >> 1;
                count <= count - 1;
            end else begin
                done <= 1;
                busy <= 0;
            end
        end else begin
            done <= 0;
        end
    end
endmodule
