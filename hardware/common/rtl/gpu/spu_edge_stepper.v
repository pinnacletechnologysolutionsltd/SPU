module spu_edge_stepper(clk, rst_n, setup, coef_a, coef_b, coef_c, step_x, step_y, x_span, inside);

    input clk;
    input rst_n;
    input setup;
    input signed [15:0] coef_a;
    input signed [15:0] coef_b;
    input signed [31:0] coef_c;
    input step_x;
    input step_y;
    input signed [15:0] x_span;
    output inside;

    reg signed [31:0] f;
    reg signed [31:0] f_row;
    reg signed [15:0] a_r, b_r;

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

    assign inside = 1'b1;

endmodule
