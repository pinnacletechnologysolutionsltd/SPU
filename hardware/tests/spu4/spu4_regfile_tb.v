// spu4_regfile_tb.v — Standalone testbench for SPU-4 register file.
// 8 × 64-bit regs.  Verifies writes, reads, reset behaviour.

`timescale 1ns / 1ps

module spu4_regfile_tb;
    reg clk, rst_n, we;
    reg [2:0] addr_a, addr_b;
    reg [63:0] din;
    wire [63:0] dout_a, dout_b, r0_out;

    spu4_regfile u_dut (clk, rst_n, we, addr_a, addr_b, din, dout_a, dout_b, r0_out);

    always #5 clk = ~clk;
    integer pass, fail;

    initial begin
        clk = 0; rst_n = 0; we = 0; addr_a = 0; addr_b = 0; din = 0;
        pass = 0; fail = 0;
        #20; rst_n = 1; #10;

        // R0 should be unit vector [1,0,0,0] after reset
        if (r0_out !== 64'h0100_0000_0000_0000)
            begin $display("FAIL R0 init"); fail = fail + 1; end
        else begin $display("PASS R0 init"); pass = pass + 1; end

        // Write R3 = 0xDEAD_BEEF_CAFE_F00D
        addr_a = 3; din = 64'hDEAD_BEEF_CAFE_F00D; we = 1;
        #10; we = 0;
        // Read back via dout_a
        addr_a = 3;
        #10;
        if (dout_a !== 64'hDEAD_BEEF_CAFE_F00D)
            begin $display("FAIL R3 write"); fail = fail + 1; end
        else begin $display("PASS R3 write"); pass = pass + 1; end

        // Read via dout_b at same time
        addr_b = 3;
        #10;
        if (dout_b !== 64'hDEAD_BEEF_CAFE_F00D)
            begin $display("FAIL R3 read_b"); fail = fail + 1; end
        else begin $display("PASS R3 read_b"); pass = pass + 1; end

        // Write R0 = 0x1234 (should overwrite unit vector)
        addr_a = 0; din = 64'h1234; we = 1;
        #10; we = 0;
        addr_a = 0;
        #10;
        if (r0_out !== 64'h1234)
            begin $display("FAIL R0 write"); fail = fail + 1; end
        else begin $display("PASS R0 write"); pass = pass + 1; end

        // Reset clears R3, R0 back to unit vector
        rst_n = 0; #10; rst_n = 1; #10;
        if (r0_out !== 64'h0100_0000_0000_0000)
            begin $display("FAIL R0 reset"); fail = fail + 1; end
        else begin $display("PASS R0 reset"); pass = pass + 1; end
        addr_a = 3;
        #10;
        if (dout_a !== 64'h0)
            begin $display("FAIL R3 reset"); fail = fail + 1; end
        else begin $display("PASS R3 reset"); pass = pass + 1; end

        if (fail == 0) $display("PASS");
        else $display("FAIL");
        $finish;
    end
endmodule
