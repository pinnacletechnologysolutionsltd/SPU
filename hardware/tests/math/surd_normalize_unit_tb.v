module surd_normalize_unit_tb #(
    parameter integer W = 16
);
    localparam integer N = 2*W+2;
    reg clk=0, rst=1, start=0;
    reg signed [N-1:0] value_a=0, value_b=0;
    reg [2*W-1:0] value_d=1;
    wire busy, done, valid, invalid, fault, fits_W;
    wire signed [N-1:0] norm_a, norm_b;
    wire [N-1:0] norm_d;
    integer cycles;
    reg signed [N-1:0] wide_a, wide_b, min_a;
    reg [2*W-1:0] wide_d;

    always #5 clk=~clk;
    surd_normalize_unit #(.W(W)) dut (
        .clk(clk),.rst(rst),.start(start),
        .value_a(value_a),.value_b(value_b),.value_d(value_d),
        .busy(busy),.done(done),.valid(valid),.invalid(invalid),
        .fault(fault),.fits_W(fits_W),.norm_a(norm_a),.norm_b(norm_b),.norm_d(norm_d)
    );

    task check_case;
        input signed [N-1:0] in_a, in_b;
        input [2*W-1:0] in_d;
        input signed [N-1:0] exp_a, exp_b;
        input [N-1:0] exp_d;
        input exp_valid, exp_invalid, exp_fit;
        begin
            @(negedge clk); value_a=in_a; value_b=in_b; value_d=in_d; start=1;
            @(negedge clk); start=0; cycles=0;
            while (!done && cycles < 5000) begin @(negedge clk); cycles=cycles+1; end
            if (!done) $fatal(1,"W=%0d normalize timeout",W);
            if (valid !== exp_valid || invalid !== exp_invalid || fault || fits_W !== exp_fit)
                $fatal(1,"W=%0d status mismatch valid=%b invalid=%b fault=%b fits=%b",W,valid,invalid,fault,fits_W);
            if (exp_valid && (norm_a !== exp_a || norm_b !== exp_b || norm_d !== exp_d))
                $fatal(1,"W=%0d tuple mismatch got (%0d,%0d,%0d)",W,norm_a,norm_b,norm_d);
        end
    endtask

    initial begin
        repeat (2) @(negedge clk); rst=0;
        wide_a=1; wide_a=wide_a <<< (2*W); wide_b=wide_a >>> 1;
        wide_d=1; wide_d=wide_d << (2*W-1);
        min_a={1'b1,{(N-1){1'b0}}};

        check_case(45,-30,75,3,-2,5,1,0,1);
        check_case(360,-252,108,10,-7,3,1,0,1);
        check_case(0,84,126,0,2,3,1,0,1);
        check_case(0,0,123,0,0,1,1,0,1);
        check_case(7,-5,11,7,-5,11,1,0,1);
        check_case(wide_a,wide_b,wide_d,2,1,1,1,0,1);
        check_case(min_a,0,wide_d,-4,0,1,1,0,1);
        check_case(wide_a,wide_b,1,wide_a,wide_b,1,1,0,0);
        check_case(0,0,0,wide_a,wide_b,1,0,1,0);
        if (fault || valid || norm_a !== wide_a || norm_b !== wide_b || norm_d !== 1)
            $fatal(1,"W=%0d invalid denominator changed normalized result",W);
        $display("PASS exact Surd normalizer W=%0d",W);
        $finish;
    end
    initial begin #1000000; $fatal(1,"W=%0d testbench timeout",W); end
endmodule
