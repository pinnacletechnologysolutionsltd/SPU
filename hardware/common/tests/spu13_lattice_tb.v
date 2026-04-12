`timescale 1ns/1ps

module spu13_lattice_tb();
    reg clk = 0;
    reg rst_n = 0;
    reg enable = 1'b1;
    reg [13*64-1:0] manifold_in = 0;
    wire [13*64-1:0] manifold_out;

    spu13_lattice #(.NODES(13), .WIDTH(64)) uut (
        .clk(clk), .rst_n(rst_n), .enable(enable), .manifold_in(manifold_in), .manifold_out(manifold_out)
    );

    always #5 clk = ~clk;

    integer i;
    reg signed [31:0] pval;
    reg signed [31:0] qval;

    initial begin
        #12 rst_n = 1;
        // Fill manifold_in with simple surd tuples: P=i, Q=i+1
        for (i = 0; i < 13; i = i + 1) begin
            pval = i + 1;
            qval = i + 2;
            manifold_in[i*64 +: 64] = {pval, qval};
        end
        #10;
        $display("manifold_out[0] = %h", manifold_out[0*64 +: 64]);
        $display("manifold_out[1] = %h", manifold_out[1*64 +: 64]);
        $finish;
    end
endmodule
