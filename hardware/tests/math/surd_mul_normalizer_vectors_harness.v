module surd_mul_normalizer_vectors_tb #(
    parameter integer W=32,
    parameter integer LANES=5
);
    localparam integer N=2*W+2;
    reg clk=0,rst=1,start=0,norm_valid=0;
    reg signed [W-1:0] a=0,b=0,c=0,e=0,dst_a=0,dst_b=0;
    reg [W-1:0] d=1,f=1,dst_d=1;
    reg signed [N-1:0] supplied_a=0,supplied_b=0;
    reg [2*W-1:0] supplied_d=1;
    wire signed [W-1:0] result_a,result_b;
    wire [W-1:0] result_d;
    wire busy,done,overflow,invalid,norm_req;
    wire signed [N-1:0] raw_a,raw_b;
    wire [2*W-1:0] raw_d;
    wire n_busy,n_done,n_valid,n_invalid,n_fault,n_fits;
    wire signed [N-1:0] norm_a,norm_b;
    wire [N-1:0] norm_d;
    wire norm_start=norm_req && !n_busy && !n_valid;
    integer fd,rc,cycles,count,pre_norm_cycles,total_latency;
    integer fit_count,fit_sum,fit_min,fit_max;
    integer norm_count,norm_sum,norm_min,norm_max,invalid_count;
    reg [W-1:0] v_a,v_b,v_d,v_c,v_e,v_f;
    reg [N-1:0] exp_raw_a,exp_raw_b,exp_raw_d;
    reg [N-1:0] exp_red_a,exp_red_b,exp_red_d;
    reg [W-1:0] exp_out_a,exp_out_b,exp_out_d;
    reg exp_request,exp_invalid,exp_overflow;
    reg [8*512-1:0] vector_path;

    always #5 clk=~clk;
    surd_smul_unit #(.W(W),.LANES(LANES)) mul (
        .clk(clk),.rst(rst),.start(start),.a_in(a),.b_in(b),.d_in(d),
        .c_in(c),.e_in(e),.f_in(f),.dst_a(dst_a),.dst_b(dst_b),.dst_d(dst_d),
        .result_a(result_a),.result_b(result_b),.result_d(result_d),
        .busy(busy),.done(done),.overflow(overflow),.invalid(invalid),
        .norm_req(norm_req),.raw_a(raw_a),.raw_b(raw_b),.raw_d(raw_d),
        .norm_valid(norm_valid),.norm_a(supplied_a),.norm_b(supplied_b),.norm_d(supplied_d)
    );
    surd_normalize_unit #(.W(W)) normalizer (
        .clk(clk),.rst(rst),.start(norm_start),.value_a(raw_a),.value_b(raw_b),.value_d(raw_d),
        .busy(n_busy),.done(n_done),.valid(n_valid),.invalid(n_invalid),.fault(n_fault),
        .fits_W(n_fits),.norm_a(norm_a),.norm_b(norm_b),.norm_d(norm_d)
    );
    always @* begin
        norm_valid=n_valid;
        supplied_a=norm_a; supplied_b=norm_b; supplied_d=norm_d[2*W-1:0];
    end

    task issue_seed;
        begin
            @(negedge clk); dst_a=result_a;dst_b=result_b;dst_d=result_d;
            a=17;b=-19;c=1;e=0;d=23;f=1;start=1;
            @(negedge clk);start=0;cycles=0;
            while(!done && cycles<20) begin @(negedge clk);cycles=cycles+1;end
            if(!done || result_a!==17 || result_b!==-19 || result_d!==23)
                $fatal(1,"W=%0d LANES=%0d destination seed failed",W,LANES);
        end
    endtask

    task issue_vector;
        begin
            @(negedge clk);dst_a=result_a;dst_b=result_b;dst_d=result_d;
            a=v_a;b=v_b;d=v_d;c=v_c;e=v_e;f=v_f;start=1;
            @(negedge clk);start=0;cycles=0;
            while(!done && !norm_req && cycles<40) begin @(negedge clk);cycles=cycles+1;end
            if(norm_req!==exp_request)
                $fatal(1,"W=%0d LANES=%0d normalization request mismatch vector=%0d",W,LANES,count);
            if(!exp_invalid) begin
                if(raw_a!==exp_raw_a || raw_b!==exp_raw_b || raw_d!==exp_raw_d)
                    $fatal(1,"W=%0d LANES=%0d raw tuple mismatch vector=%0d",W,LANES,count);
            end
            if(norm_req) begin
                pre_norm_cycles=cycles;
                cycles=0;
                while(!done && cycles<40000) begin
                    @(negedge clk);cycles=cycles+1;
                    if(n_valid && (norm_a!==exp_red_a || norm_b!==exp_red_b || norm_d!==exp_red_d || n_fits!==!exp_overflow))
                        $fatal(1,"W=%0d LANES=%0d normalized tuple mismatch vector=%0d",W,LANES,count);
                end
                total_latency=pre_norm_cycles+cycles;
                norm_count=norm_count+1; norm_sum=norm_sum+total_latency;
                if(total_latency<norm_min) norm_min=total_latency;
                if(total_latency>norm_max) norm_max=total_latency;
            end else if(!exp_invalid) begin
                fit_count=fit_count+1; fit_sum=fit_sum+cycles;
                if(cycles<fit_min) fit_min=cycles;
                if(cycles>fit_max) fit_max=cycles;
            end else begin
                invalid_count=invalid_count+1;
            end
            if(!done) $fatal(1,"W=%0d LANES=%0d completion timeout vector=%0d",W,LANES,count);
            if(invalid!==exp_invalid || overflow!==exp_overflow || result_a!==exp_out_a ||
               result_b!==exp_out_b || result_d!==exp_out_d || n_fault || n_invalid)
                $fatal(1,"W=%0d LANES=%0d result/status mismatch vector=%0d",W,LANES,count);
        end
    endtask

    initial begin
        if(!$value$plusargs("VECTORS=%s",vector_path)) $fatal(1,"missing +VECTORS=path");
        fd=$fopen(vector_path,"r"); if(!fd) $fatal(1,"cannot open vector file");
        repeat(2) @(negedge clk); rst=0; count=0;
        fit_count=0;fit_sum=0;fit_min=32'h7fffffff;fit_max=0;
        norm_count=0;norm_sum=0;norm_min=32'h7fffffff;norm_max=0;invalid_count=0;
        while(!$feof(fd)) begin
            rc=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                v_a,v_b,v_d,v_c,v_e,v_f,exp_raw_a,exp_raw_b,exp_raw_d,
                exp_red_a,exp_red_b,exp_red_d,exp_out_a,exp_out_b,exp_out_d,
                exp_request,exp_invalid,exp_overflow);
            if(rc==18) begin
                issue_seed(); issue_vector(); count=count+1;
            end else if(rc!= -1) $fatal(1,"malformed vector file record rc=%0d",rc);
        end
        $fclose(fd);
        $display("PASS W=%0d LANES=%0d vectors=%0d fit=%0d latency[min/avg/max]=%0d/%0d/%0d norm=%0d latency[min/avg/max]=%0d/%0d/%0d invalid=%0d",
            W,LANES,count,fit_count,fit_min,fit_sum/fit_count,fit_max,
            norm_count,norm_min,norm_sum/norm_count,norm_max,invalid_count);
        $finish;
    end
    initial begin #200000000; $fatal(1,"W=%0d LANES=%0d vector testbench timeout",W,LANES); end
endmodule
