`timescale 1ns/1ps
// Testbench for chiral_phinary_adder
module chiral_phinary_adder_tb;

reg clk;
reg rst;
reg [3:0] A;
reg [3:0] B;
reg chir;

wire [3:0] S;
wire void_out;
wire overflow;

chiral_phinary_adder uut (
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
reg [3:0] expected_sum;
reg [3:0] tb_int_sum;
reg [3:0] tb_surd_sum;
reg [4:0] tb_sumv;
reg [4:0] tb_delta;
reg [1:0] tb_new_int;

task compute_gold;
    input [3:0] a; input [3:0] b; input c;
    begin
        tb_int_sum = a[1:0] + b[1:0];
        tb_surd_sum = a[3:2] + b[3:2];
        tb_sumv = (tb_surd_sum << 2) + tb_int_sum; // full packing before threshold
        if (tb_sumv > 5'd10) begin
            if (c == 0) begin
                expected_void = ~expected_void;
                tb_delta = tb_sumv - 5'd10;
                expected_sum = tb_delta[3:0];
            end else begin
                tb_new_int = (tb_int_sum + 2'd1) & 2'b11;
                expected_sum = {tb_surd_sum[1:0], tb_new_int};
            end
        end else begin
            expected_sum = tb_sumv[3:0];
        end
    end
endtask

integer i;
reg pass;

initial begin
    pass = 1;
    expected_void = 0;

    // reset
    rst = 1; A = 4'b0000; B = 4'b0000; chir = 0;
    #20;
    rst = 0;

    // test vectors
    // format: A, B, chirality
    A = 4'b0001; B = 4'b0001; chir = 0; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 0: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 0: expected %b got %b", expected_void, void_out); pass = 0; end

    A = 4'b0011; B = 4'b0010; chir = 0; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 1: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 1: expected %b got %b", expected_void, void_out); pass = 0; end

    // cross-threshold cases
    A = 4'b1111; B = 4'b1111; chir = 0; @(posedge clk); #1; compute_gold(A,B,chir);
    $display("DEBUG T2: A=%b B=%b tb_surd_sum=%d tb_int_sum=%d tb_sumv=%d expected_sum=%b S=%b void_out=%b expected_void=%b", A, B, tb_surd_sum, tb_int_sum, tb_sumv, expected_sum, S, void_out, expected_void);
    if (S !== expected_sum) begin $display("Mismatch 2: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 2: expected %b got %b", expected_void, void_out); pass = 0; end

    A = 4'b1111; B = 4'b1111; chir = 1; @(posedge clk); #1; compute_gold(A,B,chir);
    $display("DEBUG T3: A=%b B=%b tb_surd_sum=%d tb_surd_sum[1:0]=%b tb_int_sum=%d tb_int_plus1_2bits=%b tb_sumv=%d expected_sum=%b S=%b void_out=%b expected_void=%b", A, B, tb_surd_sum, tb_surd_sum[1:0], tb_int_sum, (tb_int_sum + 2'd1) & 2'b11, tb_sumv, expected_sum, S, void_out, expected_void);
    if (S !== expected_sum) begin $display("Mismatch 3: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 3: expected %b got %b", expected_void, void_out); pass = 0; end

    A = 4'b0101; B = 4'b1011; chir = 1; @(posedge clk); #1; compute_gold(A,B,chir);
    $display("DEBUG T4: A=%b B=%b tb_surd_sum=%d tb_int_sum=%d tb_sumv=%d expected_sum=%b S=%b void_out=%b expected_void=%b", A, B, tb_surd_sum, tb_int_sum, tb_sumv, expected_sum, S, void_out, expected_void);
    if (S !== expected_sum) begin $display("Mismatch 4: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 4: expected %b got %b", expected_void, void_out); pass = 0; end

    A = 4'b0010; B = 4'b0010; chir = 0; @(posedge clk); #1; compute_gold(A,B,chir);
    if (S !== expected_sum) begin $display("Mismatch 5: S expected %b got %b", expected_sum, S); pass = 0; end
    if (void_out !== expected_void) begin $display("Void mismatch 5: expected %b got %b", expected_void, void_out); pass = 0; end

    if (pass) $display("PASS"); else $display("FAIL");
    $finish;
end

endmodule
