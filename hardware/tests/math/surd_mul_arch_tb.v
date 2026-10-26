module surd_mul_arch_case #(
    parameter integer LANES = 5,
    parameter integer W = 16
) (
    input wire clk,
    output reg passed = 0
);
    localparam signed [W-1:0] POS_MAX = {1'b0,{(W-1){1'b1}}};
    localparam signed [W-1:0] NEG_MIN = {1'b1,{(W-1){1'b0}}};
    localparam [W-1:0] DEN_MAX = {W{1'b1}};
    localparam signed [2*W-1:0] POS_EXT = {{W{1'b0}},POS_MAX};
    localparam [2*W-1:0] DEN_EXT = {{W{1'b0}},DEN_MAX};
    localparam signed [2*W+1:0] RAW_ONE = {{(2*W+1){1'b0}},1'b1};
    localparam signed [2*W+1:0] EXPECT_FULL_A = RAW_ONE <<< (2*W);
    localparam signed [2*W+1:0] EXPECT_FULL_B = RAW_ONE <<< (2*W-1);
    localparam signed [2*W-1:0] EXPECT_BAD_A = POS_EXT * POS_EXT;
    localparam [2*W-1:0] EXPECT_BAD_D = DEN_EXT * {{(2*W-2){1'b0}},2'd3};
    localparam [2*W-1:0] EXPECT_RESCUE_D = POS_EXT * {{(2*W-2){1'b0}},2'd3};
    reg rst=1, start=0, norm_valid=0;
    reg signed [W-1:0] a_in=0, b_in=0, c_in=0, e_in=0;
    reg [W-1:0] d_in=1, f_in=1, dst_d=7;
    reg signed [W-1:0] dst_a=10, dst_b=-4;
    reg signed [2*W+1:0] norm_a=0, norm_b=0;
    reg [2*W-1:0] norm_d=1;
    wire signed [W-1:0] result_a, result_b;
    wire [W-1:0] result_d;
    wire busy, done, overflow, invalid, norm_req;
    wire signed [2*W+1:0] raw_a, raw_b;
    wire [2*W-1:0] raw_d;
    integer cycles;

    surd_smul_unit #(.W(W),.LANES(LANES)) dut (
        .clk(clk),.rst(rst),.start(start),.a_in(a_in),.b_in(b_in),.d_in(d_in),
        .c_in(c_in),.e_in(e_in),.f_in(f_in),
        .dst_a(dst_a),.dst_b(dst_b),.dst_d(dst_d),
        .result_a(result_a),.result_b(result_b),.result_d(result_d),
        .busy(busy),.done(done),.overflow(overflow),.invalid(invalid),
        .norm_req(norm_req),.raw_a(raw_a),.raw_b(raw_b),.raw_d(raw_d),
        .norm_valid(norm_valid),.norm_a(norm_a),.norm_b(norm_b),.norm_d(norm_d)
    );

    task begin_op;
        input signed [W-1:0] av, bv, cv, ev;
        input [W-1:0] dv, fv;
        begin
            @(negedge clk);
            dst_a=result_a; dst_b=result_b; dst_d=result_d;
            a_in=av; b_in=bv; d_in=dv; c_in=cv; e_in=ev; f_in=fv; start=1;
            @(negedge clk); start=0;
        end
    endtask
    task wait_done;
        begin
            cycles=0;
            while (!done && cycles < 40) begin @(negedge clk); cycles=cycles+1; end
            if (!done) $fatal(1,"LANES=%0d completion timeout",LANES);
        end
    endtask
    task wait_norm;
        begin
            cycles=0;
            while (!norm_req && cycles < 40) begin @(negedge clk); cycles=cycles+1; end
            if (!norm_req) $fatal(1,"LANES=%0d normalization request timeout",LANES);
        end
    endtask

    initial begin
        repeat (2) @(negedge clk); rst=0;
        // Hold start high through completion to measure the next acceptance.
        // (2+sqrt(3))/3 * (4+2sqrt(3))/5 = (14+8sqrt(3))/15.
        @(negedge clk); dst_a=result_a; dst_b=result_b; dst_d=result_d;
        a_in=2; b_in=1; c_in=4; e_in=2; d_in=3; f_in=5; start=1;
        @(posedge clk); #1;
        if (!busy) $fatal(1,"LANES=%0d first request not accepted",LANES);
        cycles=0;
        while (!done && cycles < 40) begin @(posedge clk); #1; cycles=cycles+1; end
        if (!done) $fatal(1,"LANES=%0d first completion timeout",LANES);
        @(posedge clk); #1;
        if (!busy) $fatal(1,"LANES=%0d held request was not accepted",LANES);
        $display("LANES=%0d measured fit latency=%0d cycles; non-pipelined II=%0d cycles",LANES,cycles,cycles+1);
        @(negedge clk); start=0;
        wait_done();
        if (result_a !== 14 || result_b !== 8 || result_d !== 15 || overflow || invalid)
            $fatal(1,"LANES=%0d exact product mismatch",LANES);
        begin_op(-2,1,4,-2,3,5); wait_done();
        if (result_a !== -14 || result_b !== 8 || result_d !== 15 || overflow || invalid)
            $fatal(1,"LANES=%0d signed product mismatch",LANES);
        begin_op(NEG_MIN,0,1,0,1,1); wait_done();
        if (result_a !== NEG_MIN || result_b !== 0 || result_d !== 1 || overflow || invalid)
            $fatal(1,"LANES=%0d signed minimum boundary mismatch",LANES);
        begin_op(POS_MAX,0,1,0,1,1); wait_done();
        if (result_a !== POS_MAX || result_b !== 0 || result_d !== 1 || overflow || invalid)
            $fatal(1,"LANES=%0d signed maximum boundary mismatch",LANES);

        // Full-width signed products: (-2^(W-1))^2 terms stress the
        // multiplier sign correction and the widened Surd accumulators.
        begin_op(NEG_MIN,NEG_MIN,NEG_MIN,NEG_MIN,1,1); wait_norm();
        if (raw_a !== EXPECT_FULL_A || raw_b !== EXPECT_FULL_B || raw_d !== 1)
            $fatal(1,"LANES=%0d full-width raw product mismatch",LANES);
        @(negedge clk); norm_a=raw_a; norm_b=raw_b; norm_d=raw_d; norm_valid=1;
        @(negedge clk); norm_valid=0; wait_done();
        if (result_a !== POS_MAX || result_b !== 0 || result_d !== 1 || !overflow)
            $fatal(1,"LANES=%0d full-width overflow preservation mismatch",LANES);

        // max_signed/max_signed * max_signed/3 = 1/3 after exact reduction.
        begin_op(1,0,POS_MAX,0,POS_MAX,3); wait_norm();
        if (raw_a !== POS_MAX || raw_b !== 0 || raw_d !== EXPECT_RESCUE_D)
            $fatal(1,"LANES=%0d raw tuple mismatch",LANES);
        @(negedge clk); norm_a=1; norm_b=0; norm_d=3; norm_valid=1;
        @(negedge clk); norm_valid=0; wait_done();
        if (result_a !== 1 || result_b !== 0 || result_d !== 3 || overflow)
            $fatal(1,"LANES=%0d normalization rescue mismatch",LANES);

        // Coprime result cannot fit: preserve the destination and flag overflow.
        begin_op(POS_MAX,0,POS_MAX,0,DEN_MAX,3); wait_norm();
        if (raw_a !== EXPECT_BAD_A || raw_d !== EXPECT_BAD_D)
            $fatal(1,"LANES=%0d overflow raw tuple mismatch",LANES);
        @(negedge clk); norm_a=raw_a; norm_b=raw_b; norm_d=raw_d; norm_valid=1;
        @(negedge clk); norm_valid=0; wait_done();
        if (result_a !== 1 || result_b !== 0 || result_d !== 3 || !overflow)
            $fatal(1,"LANES=%0d destination was not preserved on overflow",LANES);

        begin_op(2,1,4,2,0,5); wait_done();
        if (!invalid || overflow || result_a !== 1 || result_b !== 0 || result_d !== 3)
            $fatal(1,"LANES=%0d zero denominator handling mismatch",LANES);
        passed=1;
    end
endmodule

module surd_mul_arch_tb #(
    parameter integer W = 16
);
    reg clk=0;
    wire p1,p2,p5;
    always #5 clk=~clk;
    surd_mul_arch_case #(.LANES(1),.W(W)) c1(clk,p1);
    surd_mul_arch_case #(.LANES(2),.W(W)) c2(clk,p2);
    surd_mul_arch_case #(.LANES(5),.W(W)) c5(clk,p5);
    initial begin
        wait(p1 && p2 && p5);
        $display("PASS surd multiply lane architecture comparison W=%0d",W);
        $finish;
    end
    initial begin #100000; $fatal(1,"testbench timeout"); end
endmodule
