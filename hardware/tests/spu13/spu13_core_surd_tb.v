`timescale 1ns/1ps
module spu13_core_surd_tb;
    reg clk=0,rst_n=0,inst_valid=0;
    reg [63:0] inst_word=0;
    wire inst_done,ready,busy,retire,we,rd,boot;
    wire [3:0] status;wire [2:0] dst;wire [31:0] data;
    wire qr_commit;wire [3:0] qr_lane;
    wire [63:0] qr_a,qr_b,qr_c,qr_d;
    integer cycles=0,fd,rc,kind,code,writes,cache_index,group,tag;
    integer before_cycle,waited,norm_cycles,align_cycles,product_cycles,stalls;
    integer observed_writes,observed_retires,rescues,starts;
    integer group_start=0;
    reg [63:0] word,exp_a,exp_b,exp_d;
    reg [31:0] exp_read,cache[0:255];
    reg [4095:0] path;
    always #5 clk=~clk;
    always @(posedge clk) cycles<=cycles+1;
    spu13_core #(.DEVICE("SIM"),.ENABLE_SURD_CPU(1),.ENABLE_SEQUENCER(0),
        .ENABLE_RPLU(0),.ENABLE_LATTICE(0),.ENABLE_MATH(0),
        .ENABLE_CORE_RPLU_V2(1),.ENABLE_CORE_RPLU_V2_PIPELINE(0),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0)) dut (
        .clk(clk),.rst_n(rst_n),.phi_8(1'b0),.phi_13(1'b0),.phi_21(1'b0),
        .dec_fast_cfg_wr_en(1'b0),.dec_fast_cfg_sel(3'd0),
        .dec_fast_cfg_material(8'd0),.dec_fast_cfg_addr(10'd0),
        .dec_fast_cfg_data(64'd0),.phinary_cfg(16'd0),
        .prime_data(24'd0),.prime_addr(4'd0),.prime_we(1'b0),.boot_done(1'b1),
        .pell_data(32'd0),.pell_addr(3'd0),.pell_we(1'b0),
        .manual_rotor_en(1'b0),.manual_rotor_data(64'd0),.regen_dphi_cfg(8'd0),
        .mem_ready(1'b1),.mem_rd_manifold(832'd0),.mem_burst_done(1'b0),
        .inst_valid(inst_valid),.inst_word(inst_word),.inst_done(inst_done),
        .surd_issue_ready(ready),.surd_busy(busy),.surd_retire_valid(retire),
        .surd_write_valid(we),.surd_read_valid(rd),.surd_status(status),
        .surd_retire_dst(dst),.surd_read_data(data),.boot_ready(boot),
        .qr_commit_valid(qr_commit),.qr_commit_lane(qr_lane),
        .qr_commit_A(qr_a),.qr_commit_B(qr_b),.qr_commit_C(qr_c),.qr_commit_D(qr_d));
    `include "hardware/tests/spu13/spu13_core_surd_guards.vh"
    `include "hardware/tests/spu13/spu13_core_surd_tasks.vh"
    initial begin
        reset_core;
        if(!$value$plusargs("PROGRAM=%s",path)) begin
            word=64'h7600000000000000;code=1;writes=0;cache_index=-1;group=-1;tag=0;kind=1;
            issue;
            load_smoke(0,64'd1,64'd2,64'd3);
            word=64'h7300000000000000;code=0;writes=1;exp_a=13;exp_b=4;exp_d=9;
            issue;
            $display("spu13_core_surd_tb: PASS");$finish;
        end
        fd=$fopen(path,"r");if(!fd) $fatal(1,"cannot open CPU program");
        while(!$feof(fd)) begin
            rc=$fscanf(fd,"%d %h %d %d %h %h %h %d %h %d %d\n",
                kind,word,code,writes,exp_a,exp_b,exp_d,cache_index,exp_read,group,tag);
            if(rc==11) begin
                if(kind==8) reset_core;
                else if(kind==9) group_start=cycles;
                else if(kind==10) $display("GROUP %0d %0d",group,cycles-group_start);
                else begin
                    if(kind==2) word[39:8]=cache[cache_index];
                    issue;
                end
            end else if(!$feof(fd)) $fatal(1,"malformed CPU program row");
        end
        $fclose(fd);
        $display("VERIFICATION preservation=%0d aliases=%0d injections=%0d",
            checked_preservations,checked_aliases,injected_faults);
        $display("PASS canonical CPU directed execution and complete kernel stream");$finish;
    end
endmodule
