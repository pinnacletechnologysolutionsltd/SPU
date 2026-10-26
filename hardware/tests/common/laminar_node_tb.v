`timescale 1ns/1ps

module laminar_node_tb();
    reg clk = 0;
    reg rst_n = 0;
    reg enable = 1'b1;
    reg [63:0] surd_in = 64'h0000000000000000;
    wire [63:0] surd_out;

    // Instantiate the unit under test (pack two 32-bit RationalSurd5 words)
    laminar_node #(.WIDTH(64)) uut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .surd_in(surd_in),
        .surd_out(surd_out)
    );

    // Clock
    always #5 clk = ~clk;

    initial begin
        // release reset after a few cycles
        #12 rst_n = 1;
        #10;
        // a: P=2,Q=3 -> 0x0002_0003 ; b: P=4,Q=5 -> 0x0004_0005
        surd_in = 64'h00020003_00040005;
        #10;
        // Expected: P_out = 2*4 + 5*3*5 = 8 + 75 = 83 (0x53)
        //           Q_out = 2*5 + 4*3 = 10 + 12 = 22 (0x16)
        if (surd_out === 64'h00000053_00000016) begin
            $display("PASS");
        end else begin
            $display("FAIL: got %h", surd_out);
        end
        $finish;
    end
endmodule
