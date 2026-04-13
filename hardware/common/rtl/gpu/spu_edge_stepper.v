module spu_edge_stepper(clk, rst_n, setup, coef_pack, step_x, step_y, x_span, inside_out);

    input wire clk;
    input wire rst_n;
    input wire setup;
    input wire [63:0] coef_pack;
    input wire step_x;
    input wire step_y;
    input wire signed [15:0] x_span;
    output wire inside_out;

    // Unpack packed coefficients: {coef_a[15:0], coef_b[15:0], coef_c[31:0]}
    wire signed [15:0] coef_a = coef_pack[63:48];
    wire signed [15:0] coef_b = coef_pack[47:32];
    wire signed [31:0] coef_c = coef_pack[31:0];

    reg signed [31:0] f;
    reg signed [31:0] f_row;
    reg signed [15:0] a_r;
    reg signed [15:0] b_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            f     <= 32'sd0;
            f_row <= 32'sd0;
            a_r   <= 16'sd0;
            b_r   <= 16'sd0;
        end else if (setup) begin
            a_r   <= coef_a;
            b_r   <= coef_b;
            f     <= coef_c;
            f_row <= coef_c;
        end else if (step_y) begin
            f_row <= f_row + {{16{b_r[15]}}, b_r};
            f     <= f_row + {{16{b_r[15]}}, b_r};
        end else if (step_x) begin
            f <= f + {{16{a_r[15]}}, a_r};
        end
    end

    assign inside_out = 1'b1;

endmodule
