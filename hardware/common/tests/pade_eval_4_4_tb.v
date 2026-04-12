`timescale 1ns/1ps
module pade_eval_4_4_tb;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst_n = 0;

    initial begin
        #20; rst_n = 1;
    end

    // DUT
    reg start;
    reg signed [63:0] x_q32;
    wire signed [31:0] exp_q16;
    wire done;
    wire busy;
    // runtime config interface (defaults to no-op)
    reg cfg_wr_en = 1'b0;
    reg [2:0] cfg_wr_sel = 3'd0;
    reg [2:0] cfg_wr_addr = 3'd0;
    reg [63:0] cfg_wr_data = 64'd0;

    pade_eval_4_4 dut (
        .clk(clk), .rst_n(rst_n), .start(start), .x_q32(x_q32), .cfg_wr_en(cfg_wr_en), .cfg_wr_sel(cfg_wr_sel), .cfg_wr_addr(cfg_wr_addr), .cfg_wr_data(cfg_wr_data), .exp_q16(exp_q16), .done(done), .busy(busy)
    );

    // load coeff mems for reference calculation
    reg signed [63:0] num[0:4];
    reg signed [63:0] den[0:4];
    initial begin
        $readmemh("hardware/common/rtl/gpu/pade_num_4_4_q32.mem", num);
        $readmemh("hardware/common/rtl/gpu/pade_den_4_4_q32.mem", den);
    end

    // reference Horner in testbench (high precision)
    function signed [127:0] horner_num;
        input signed [63:0] xin;
        reg signed [127:0] acc;
        reg signed [191:0] tmp;
        begin
            acc = num[4];
            tmp = acc * xin;
            acc = (tmp >>> 32) + num[3];
            tmp = acc * xin;
            acc = (tmp >>> 32) + num[2];
            tmp = acc * xin;
            acc = (tmp >>> 32) + num[1];
            tmp = acc * xin;
            acc = (tmp >>> 32) + num[0];
            horner_num = acc;
        end
    endfunction

    function signed [127:0] horner_den;
        input signed [63:0] xin;
        reg signed [127:0] acc;
        reg signed [191:0] tmp;
        begin
            acc = den[4];
            tmp = acc * xin;
            acc = (tmp >>> 32) + den[3];
            tmp = acc * xin;
            acc = (tmp >>> 32) + den[2];
            tmp = acc * xin;
            acc = (tmp >>> 32) + den[1];
            tmp = acc * xin;
            acc = (tmp >>> 32) + den[0];
            horner_den = acc;
        end
    endfunction

    integer i;
    reg signed [63:0] test_x [0:7];
    // temporaries for reference calculation (module scope)
    reg signed [127:0] accn;
    reg signed [127:0] accd;
    reg signed [127:0] numer;
    reg signed [127:0] quot;
    initial begin
        // some representative x_q32 values (small to medium range)
        test_x[0] = 64'sh0000000100000000; // 1.0 in Q32
        test_x[1] = 64'shFFFFFFFF00000000; // -1.0 in Q32
        test_x[2] = 64'sh0000000080000000; // 0.5
        test_x[3] = 64'shFFFFFFFF80000000; // -0.5
        test_x[4] = 64'sh0000000040000000; // 0.25
        test_x[5] = 64'shFFFFFFFFC0000000; // -0.25
        test_x[6] = 64'sh0000000000000000; // 0
        test_x[7] = 64'sh0000000200000000; // 2.0

        #50;
        for (i = 0; i < 8; i = i + 1) begin
            x_q32 = test_x[i];
            start = 1'b1;
            // hold start for a few clocks to ensure DUT samples it
            repeat (5) @(posedge clk);
            start = 1'b0;
            // wait for DUT done
            wait (done == 1'b1);
            @(posedge clk);
            // compute reference: acc_num/acc_den -> exp (Q16)
            accn = horner_num(x_q32);
            accd = horner_den(x_q32);
            if (accd == 0) begin
                $display("TB_FAIL: denom zero for x=%h", x_q32);
                $finish;
            end
            numer = accn << 16; // scale to Q48-ish
            quot = numer / accd; // result in Q16 as expected
            // compare lower 16 bits tolerance of 1 LSB
            if (quot[31:0] !== exp_q16) begin
                $display("TB_FAIL: x=%h expected=%0d got=%0d", x_q32, quot[31:0], exp_q16);
                $finish;
            end else begin
                $display("TB_PASS: x=%h exp=%0d", x_q32, exp_q16);
            end
            #10;
        end
        $display("ALL_PASS");
        $finish;
    end
endmodule
