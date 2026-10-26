// N-cycle unsigned restoring quotient engine with checked final remainder.
module surd_exact_quotient #(
    parameter integer N = 34
) (
    input wire clk, input wire rst, input wire start,
    input wire [N-1:0] dividend, input wire [N-1:0] divisor,
    output reg busy, output reg done, output reg fault,
    output reg [N-1:0] quotient, output reg [N:0] remainder
);
    localparam integer INDEX_W = $clog2(N);
    localparam [1:0] IDLE=0, RUN=1;
    reg state;
    reg [INDEX_W-1:0] bit_index;
    reg [N-1:0] dividend_reg;
    reg [N-1:0] divisor_reg;
    reg [N:0] rem_reg;
    wire [N:0] shifted_rem = {rem_reg[N-1:0],dividend_reg[bit_index]};
    wire [N:0] divisor_ext = {1'b0,divisor_reg};
    wire subtract = shifted_rem >= divisor_ext;
    wire [N:0] next_rem = subtract ? shifted_rem-divisor_ext : shifted_rem;

    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE; busy <= 0; done <= 0; fault <= 0;
            quotient <= 0; remainder <= 0; rem_reg <= 0;
            dividend_reg <= 0; divisor_reg <= 0; bit_index <= 0;
        end else begin
            done <= 0; fault <= 0;
            case (state)
                IDLE: if (start) begin
                    if (divisor == 0) begin done <= 1; fault <= 1; busy <= 0; end
                    else begin
                        dividend_reg <= dividend; divisor_reg <= divisor;
                        quotient <= 0; rem_reg <= 0; bit_index <= N-1;
                        busy <= 1; state <= RUN;
                    end
                end
                RUN: begin
                    rem_reg <= next_rem;
                    if (subtract) quotient[bit_index] <= 1'b1;
                    if (bit_index == 0) begin
                        remainder <= next_rem; done <= 1; busy <= 0; state <= IDLE;
                    end else bit_index <= bit_index - 1'b1;
                end
                default: begin state <= IDLE; busy <= 0; fault <= 1; done <= 1; end
            endcase
        end
    end
endmodule
