`timescale 1ns/1ps
// Parameterized testbench for chiral_phinary_adder_param (WIDTH=4, INT_BITS=2)
module chiral_phinary_adder_param_tb;

parameter WIDTH = 4;
parameter INT_BITS = 2;
localparam SURD_BITS = WIDTH - INT_BITS;

reg clk;
reg rst;
reg [WIDTH-1:0] A;
reg [WIDTH-1:0] B;
reg chir;

wire [WIDTH-1:0] S;
wire void_out;
wire overflow;

chiral_phinary_adder_param #(
    .WIDTH(WIDTH),
    .INT_BITS(INT_BITS),
    .LAMINAR_THR(5'd10)
) uut (
    .clk(clk),
    .rst(rst),
    .surd_A(A),
    .surd_B(B),
    .chirality(chir),
    .surd_Sum(S),
    .void_state(void_out),
    .overflow(overflow)
);

initial clk = 0;
always #5 clk = ~clk;

// golden model state
reg expected_void;
reg [WIDTH-1:0] expected_sum;
reg [INT_BITS:0] tb_int_sum;
reg [SURD_BITS:0] tb_surd_sum;
reg [WIDTH:0] tb_sumv;
reg [WIDTH:0] tb_delta;
reg [INT_BITS-1:0] tb_new_int;

task compute_gold;
    input [WIDTH-1:0] a; input [WIDTH-1:0] b; input c;
    begin
        tb_int_sum = a[INT_BITS-1:0] + b[INT_BITS-1:0];
        tb_surd_sum = a[WIDTH-1:INT_BITS] + b[WIDTH-1:INT_BITS];
        tb_sumv = (tb_surd_sum << INT_BITS) + tb_int_sum; // full packing
        if (tb_sumv > 5'd10) begin
            if (c == 0) begin
                expected_void = ~expected_void;
                tb_delta = tb_sumv - 5'd10;
                expected_sum = tb_delta[WIDTH-1:0];
            end else begin
                tb_new_int = (tb_int_sum + 1) & ((1<<INT_BITS)-1);
                expected_sum = {tb_surd_sum[SURD_BITS-1:0], tb_new_int};
            end
        end else begin
            expected_sum = tb_sumv[WIDTH-1:0];
        end
    end
endtask

integer i;
reg pass;

initial begin
    pass = 1;
    expected_void = 0;

    // reset
    rst = 1; A = {WIDTH{1'b0}}; B = {WIDTH{1'b0}}; chir = 0;
    #20;
    rst = 0;

    // test vectors
    A = 4'b0001; B = 4'b0001; chir = 0; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 0: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 0: expected %b got %b", expected_void, void_out); pass = 0; end

    A = 4'b0011; B = 4'b0010; chir = 0; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 1: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 1: expected %b got %b", expected_void, void_out); pass = 0; end

    // cross-threshold cases
    A = 4'b1111; B = 4'b1111; chir = 0; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 2: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 2: expected %b got %b", expected_void, void_out); pass = 0; end

    A = 4'b1111; B = 4'b1111; chir = 1; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 3: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 3: expected %b got %b", expected_void, void_out); pass = 0; end

    A = 4'b0101; B = 4'b1011; chir = 1; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 4: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 4: expected %b got %b", expected_void, void_out); pass = 0; end

    A = 4'b0010; B = 4'b0010; chir = 0; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 5: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 5: expected %b got %b", expected_void, void_out); pass = 0; end

    if (pass) $display("PASS"); else $display("FAIL");
    $finish;
end

endmodule
