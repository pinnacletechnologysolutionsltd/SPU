module surd_mul_normalizer_tb #(
    parameter integer W = 16,
    parameter integer LANES = 5
);
    localparam integer N=2*W+2;
    localparam signed [W-1:0] POS_MAX={1'b0,{(W-1){1'b1}}};
    reg clk=0, rst=1, start=0;
    reg signed [W-1:0] a=0,b=0,c=0,e=0,dst_a=0,dst_b=0;
    reg [W-1:0] d=1,f=1,dst_d=1;
    wire signed [W-1:0] result_a,result_b;
    wire [W-1:0] result_d;
    wire busy,done,overflow,invalid,norm_req;
    wire signed [N-1:0] raw_a,raw_b;
    wire [2*W-1:0] raw_d;
    wire norm_busy,norm_done,norm_valid,norm_invalid,norm_fault,norm_fits;
    wire signed [N-1:0] norm_a,norm_b;
    wire [N-1:0] norm_d;
    reg [W-1:0] rescue_denominator;
    wire norm_start=norm_req && !norm_busy && !norm_valid;
    integer cycles;

    always #5 clk=~clk;
    surd_smul_unit #(.W(W),.LANES(LANES)) mul (
        .clk(clk),.rst(rst),.start(start),.a_in(a),.b_in(b),.d_in(d),
        .c_in(c),.e_in(e),.f_in(f),.dst_a(dst_a),.dst_b(dst_b),.dst_d(dst_d),
        .result_a(result_a),.result_b(result_b),.result_d(result_d),
        .busy(busy),.done(done),.overflow(overflow),.invalid(invalid),
        .norm_req(norm_req),.raw_a(raw_a),.raw_b(raw_b),.raw_d(raw_d),
        .norm_valid(norm_valid),.norm_a(norm_a),.norm_b(norm_b),.norm_d(norm_d[2*W-1:0])
    );
    surd_normalize_unit #(.W(W)) normalizer (
        .clk(clk),.rst(rst),.start(norm_start),
        .value_a(raw_a),.value_b(raw_b),.value_d(raw_d),
        .busy(norm_busy),.done(norm_done),.valid(norm_valid),
        .invalid(norm_invalid),.fault(norm_fault),.fits_W(norm_fits),
        .norm_a(norm_a),.norm_b(norm_b),.norm_d(norm_d)
    );

    task issue;
        input signed [W-1:0] av,bv,cv,ev;
        input [W-1:0] dv,fv;
        begin
            @(negedge clk); dst_a=result_a; dst_b=result_b; dst_d=result_d;
            a=av; b=bv; c=cv; e=ev; d=dv; f=fv; start=1;
            @(negedge clk); start=0; cycles=0;
            while (!done && cycles<20000) begin @(negedge clk); cycles=cycles+1; end
            if (!done) $fatal(1,"W=%0d LANES=%0d integrated multiply/normalizer timeout",W,LANES);
            if (norm_fault || norm_invalid) $fatal(1,"W=%0d normalizer internal error",W);
        end
    endtask

    initial begin
        repeat (2) @(negedge clk); rst=0;
        rescue_denominator=1; rescue_denominator=rescue_denominator << (W-1);
        issue(17,-19,1,0,23,1);
        if (result_a!==17 || result_b!==-19 || result_d!==23 || overflow || invalid)
            $fatal(1,"W=%0d destination seed mismatch",W);

        // Raw denominator 2^W cannot fit; common factor 2 rescues it exactly.
        issue(1,0,2,0,rescue_denominator,2);
        if (result_a!==1 || result_b!==0 || result_d!==rescue_denominator || overflow || invalid)
            $fatal(1,"W=%0d integrated normalization rescue mismatch",W);

        // The exact product remains too large after reduction; destination holds.
        issue(POS_MAX,0,POS_MAX,0,1,3);
        if (result_a!==1 || result_b!==0 || result_d!==rescue_denominator || !overflow || invalid)
            $fatal(1,"W=%0d integrated overflow preservation mismatch",W);
        $display("PASS integrated exact multiply/normalizer W=%0d LANES=%0d",W,LANES);
        $finish;
    end
    initial begin #2500000; $fatal(1,"W=%0d integrated testbench timeout",W); end
endmodule
