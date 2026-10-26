`timescale 1ns / 1ps
module spu13_jet_sparse_mac_tb;
    parameter N=2, DELAY=0;
    localparam T=$clog2(N+2), P=32'h7fffffff;
    reg clk=0, rst_n=0, fabric_rst_n=0, start=0, op_mul=1, hold_response=0;
    reg [31:0] j_coeff [0:N][0:3], k_coeff [0:N][0:3];
    wire [31:0] r_coeff [0:N][0:3];
    reg [T-1:0] j_lo=0,j_hi=N,k_lo=0,k_hi=N;
    wire [T-1:0] r_lo,r_hi;
    wire busy,done,err_zero_divisor,mult_start;
    wire [31:0] a0,a1,a2,a3,b0,b1,b2,b3,raw0,raw1,raw2,raw3;
    wire raw_done,raw_busy,rns_error;
    reg [31:0] delayed [0:3];
    reg delay_done=0;
    integer delay_left=-1;
    wire reply = DELAY == 0 ? raw_done : delay_done;
    wire mult_done = !hold_response && reply;
    wire [31:0] mr0=DELAY==0?raw0:delayed[0], mr1=DELAY==0?raw1:delayed[1];
    wire [31:0] mr2=DELAY==0?raw2:delayed[2], mr3=DELAY==0?raw3:delayed[3];
    integer flight=0,issued=0,completed=0,checks=0,case_id=0;
    spu13_jet_sparse_mac #(.N(N)) uut (
        .clk(clk),.rst_n(rst_n),.start(start),.op_mul(op_mul),
        .j_coeff(j_coeff),.k_coeff(k_coeff),.j_lo(j_lo),.j_hi(j_hi),.k_lo(k_lo),.k_hi(k_hi),
        .r_coeff(r_coeff),.r_lo(r_lo),.r_hi(r_hi),.busy(busy),.done(done),.err_zero_divisor(err_zero_divisor),
        .mult_start(mult_start),.mult_a0(a0),.mult_a1(a1),.mult_a2(a2),.mult_a3(a3),
        .mult_b0(b0),.mult_b1(b1),.mult_b2(b2),.mult_b3(b3),
        .mult_r0(mr0),.mult_r1(mr1),.mult_r2(mr2),.mult_r3(mr3),.mult_done(mult_done)
    );
    spu13_m31_multiplier fabric (
        .clk(clk),.rst_n(fabric_rst_n),.start(mult_start),
        .a0(a0),.a1(a1),.a2(a2),.a3(a3),.b0(b0),.b1(b1),.b2(b2),.b3(b3),
        .r0(raw0),.r1(raw1),.r2(raw2),.r3(raw3),.done(raw_done),.busy(raw_busy),.rns_error(rns_error)
    );
    always @(posedge clk or negedge fabric_rst_n) begin
        if (!fabric_rst_n) begin delay_left<=-1; delay_done<=0; end
        else begin
            delay_done<=0;
            if (raw_done) begin
                delayed[0]<=raw0; delayed[1]<=raw1; delayed[2]<=raw2; delayed[3]<=raw3;
                delay_left<=DELAY+(issued & 3);
            end else if (delay_left==0) begin delay_done<=1; delay_left<=-1; end
            else if (delay_left>0) delay_left<=delay_left-1;
        end
    end
    integer row,lane,expected_count,expected_lo,expected_hi,ek,ei,ej,cycles,fd,scan,mode;
    reg active=0,old_done=0;
    reg [31:0] accepted_a [0:N][0:3],accepted_b [0:N][0:3];
    reg [31:0] expected [0:N][0:3],prior [0:N][0:3];
    integer al,ah,bl,bh,prior_lo,prior_hi;
    reg mul;
    reg [1023:0] path;
    reg [31:0] word,word_b,word_r;
    `include "hardware/tests/spu13/spu13_jet_sparse_checks.vh"
    initial begin
        clear_inputs(); tick(); rst_n=1; fabric_rst_n=1; tick();
        if ($value$plusargs("NEGATIVE=%d",mode)) negative_control(mode);
        if ($test$plusargs("WIDTH_ONLY")) begin
            if(N!=15 || T!=5) $fatal(1,"width configuration");
            clear_inputs();j_lo=16;j_hi=0;k_lo=16;k_hi=0;
            expected_lo=16;expected_hi=0;expected_count=0;
            for(row=0;row<=N;row=row+1) for(lane=0;lane<4;lane=lane+1) expected[row][lane]=0;
            #1;if(uut.lo_sum!=32) $fatal(1,"tag sum narrowed");run_case();
            $display("PASS: N15 tag width only");$finish;
        end
        if ($value$plusargs("VECTORS=%s",path)) begin
            fd=$fopen(path,"r"); if (!fd) $fatal(1,"fixture open failed");
            while (!$feof(fd)) begin
                scan=$fscanf(fd,"%d %d %d %d %d %d %d %d\n",mode,al,ah,bl,bh,expected_lo,expected_hi,expected_count);
                if (scan==8) begin
                    op_mul=mode; j_lo=al; j_hi=ah; k_lo=bl; k_hi=bh;
                    for(row=0;row<=N;row=row+1) for(lane=0;lane<4;lane=lane+1) begin
                        scan=$fscanf(fd,"%h %h %h\n",word,word_b,word_r);
                        if(scan!=3) $fatal(1,"truncated fixture");
                        j_coeff[row][lane]=word;k_coeff[row][lane]=word_b;expected[row][lane]=word_r;
                    end
                    run_case();
                end else if(scan!=-1) $fatal(1,"bad fixture header");
            end
            $fclose(fd);
        end else begin
            clear_inputs(); j_coeff[0][0]=2; k_coeff[0][0]=3;
            for(row=0;row<=N;row=row+1) for(lane=0;lane<4;lane=lane+1) expected[row][lane]=0;
            expected[0][0]=6; expected_lo=0; expected_hi=N; expected_count=(N+1)*(N+2)/2;
            run_case();
        end
        reset_controls();
        $display("PASS: sparse N=%0d delay=%0d vectors=%0d checks=%0d",N,DELAY,case_id,checks);
        $finish;
    end
    initial begin #10000000; $fatal(1,"testbench timeout"); end
endmodule
