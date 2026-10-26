// Exact common-GCD canonicalizer for (A+B*sqrt(3))/D.
module surd_normalize_unit #(
    parameter integer W = 16
) (
    input wire clk, input wire rst, input wire start,
    input wire signed [2*W+1:0] value_a,
    input wire signed [2*W+1:0] value_b,
    input wire [2*W-1:0] value_d,
    output reg busy, output reg done, output reg valid,
    output reg invalid, output reg fault, output reg fits_W,
    output reg signed [2*W+1:0] norm_a,
    output reg signed [2*W+1:0] norm_b,
    output reg [2*W+1:0] norm_d
);
    localparam integer N = 2*W+2;
    localparam [1:0] IDLE=0, WAIT_GCD=1, WAIT_QUOTIENTS=2;
    reg [1:0] state;
    reg negative_a, negative_b;
    reg [N-1:0] magnitude_a, magnitude_b, denominator;
    reg gcd_start, quotient_start;
    wire gcd_busy, gcd_done, gcd_fault;
    wire [N-1:0] gcd_value;
    wire qa_busy, qa_done, qa_fault, qb_busy, qb_done, qb_fault;
    wire qd_busy, qd_done, qd_fault;
    wire [N-1:0] qa, qb, qd;
    wire [N:0] ra, rb, rd;
    wire [N-1:0] norm_a_bits = negative_a ? (~qa + {{N-1{1'b0}},1'b1}) : qa;
    wire [N-1:0] norm_b_bits = negative_b ? (~qb + {{N-1{1'b0}},1'b1}) : qb;
    wire fit_a = norm_a_bits[N-1:W] == {(N-W){norm_a_bits[W-1]}};
    wire fit_b = norm_b_bits[N-1:W] == {(N-W){norm_b_bits[W-1]}};
    wire fit_d = (qd[N-1:W] == {(N-W){1'b0}}) && (qd[W-1:0] != 0);

    function [N-1:0] magnitude;
        input signed [N-1:0] value;
        begin magnitude = value[N-1] ? (~value + {{N-1{1'b0}},1'b1}) : value; end
    endfunction

    surd_binary_gcd3 #(.N(N)) gcd3 (
        .clk(clk),.rst(rst),.start(gcd_start),
        .value_a(magnitude_a),.value_b(magnitude_b),.value_d(denominator),
        .busy(gcd_busy),.done(gcd_done),.fault(gcd_fault),.gcd_value(gcd_value)
    );
    surd_exact_quotient #(.N(N)) divide_a (
        .clk(clk),.rst(rst),.start(quotient_start),.dividend(magnitude_a),
        .divisor(gcd_value),.busy(qa_busy),.done(qa_done),.fault(qa_fault),
        .quotient(qa),.remainder(ra)
    );
    surd_exact_quotient #(.N(N)) divide_b (
        .clk(clk),.rst(rst),.start(quotient_start),.dividend(magnitude_b),
        .divisor(gcd_value),.busy(qb_busy),.done(qb_done),.fault(qb_fault),
        .quotient(qb),.remainder(rb)
    );
    surd_exact_quotient #(.N(N)) divide_d (
        .clk(clk),.rst(rst),.start(quotient_start),.dividend(denominator),
        .divisor(gcd_value),.busy(qd_busy),.done(qd_done),.fault(qd_fault),
        .quotient(qd),.remainder(rd)
    );

    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE; busy <= 0; done <= 0; valid <= 0;
            invalid <= 0; fault <= 0; fits_W <= 0;
            norm_a <= 0; norm_b <= 0; norm_d <= 1;
            negative_a <= 0; negative_b <= 0;
            magnitude_a <= 0; magnitude_b <= 0; denominator <= 1;
            gcd_start <= 0; quotient_start <= 0;
        end else begin
            done <= 0; valid <= 0; invalid <= 0; fault <= 0;
            gcd_start <= 0; quotient_start <= 0;
            case (state)
                IDLE: if (start) begin
                    fits_W <= 0;
                    if (value_d == 0) begin done <= 1; invalid <= 1; end
                    else if (value_a == 0 && value_b == 0) begin
                        norm_a <= 0; norm_b <= 0; norm_d <= 1;
                        fits_W <= 1; valid <= 1; done <= 1;
                    end else begin
                        negative_a <= value_a[2*W+1];
                        negative_b <= value_b[2*W+1];
                        magnitude_a <= magnitude(value_a);
                        magnitude_b <= magnitude(value_b);
                        denominator <= {{2{1'b0}},value_d};
                        gcd_start <= 1; busy <= 1; state <= WAIT_GCD;
                    end
                end
                WAIT_GCD: if (gcd_done) begin
                    if (gcd_fault || gcd_value == 0) begin
                        fault <= 1; done <= 1; busy <= 0; state <= IDLE;
                    end else begin quotient_start <= 1; state <= WAIT_QUOTIENTS; end
                end
                WAIT_QUOTIENTS: if (qa_done && qb_done && qd_done) begin
                    if (qa_fault || qb_fault || qd_fault || ra != 0 || rb != 0 || rd != 0) begin
                        fault <= 1; done <= 1; busy <= 0; state <= IDLE;
                    end else begin
                        norm_a <= norm_a_bits; norm_b <= norm_b_bits; norm_d <= qd;
                        fits_W <= fit_a && fit_b && fit_d;
                        valid <= 1; done <= 1; busy <= 0; state <= IDLE;
                    end
                end
                default: begin fault <= 1; done <= 1; busy <= 0; state <= IDLE; end
            endcase
        end
    end
endmodule
