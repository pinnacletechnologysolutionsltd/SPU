    task reset_core;
        integer guard;
        begin
            @(negedge clk);rst_n=0;inst_valid=0;inst_word=0;
            repeat(3) @(negedge clk);
            rst_n=1;guard=0;
            while(!ready && guard<500) begin @(negedge clk);guard=guard+1;end
            if(!ready) $fatal(1,"CPU boot/reset timeout");
        end
    endtask
    task issue;
        integer p;
        begin
            @(negedge clk);stalls=0;
            while(!ready) begin @(negedge clk);stalls=stalls+1;
                if(stalls>40000) $fatal(1,"issue readiness timeout");end
            snapshot_bank;
            before_cycle=cycles;inst_word=word;inst_valid=1;
            waited=0;observed_writes=0;observed_retires=0;
            norm_cycles=0;align_cycles=0;product_cycles=0;rescues=0;starts=0;
            @(negedge clk);inst_valid=0;inst_word=0;
            // kind 4 attempts a second issue while the first instruction is busy.
            if(kind==4) begin
                if(!busy) $fatal(1,"busy test did not exercise an active operation");
                inst_word=64'h7107000000000000;inst_valid=1;
            end
            while(!inst_done && waited<40000) begin
                if(we) begin
                    observed_writes=observed_writes+1;
                    if(dst!==word[50:48]) $fatal(1,"destination identity changed while busy");
                    if(dut.gen_surd_cpu.u_surd.bank.tuples[dst]!=={exp_d,exp_b,exp_a})
                        $fatal(1,"atomic tuple mismatch word=%h",word);
                end
                if(retire) observed_retires=observed_retires+1;
                if(rd) begin
                    if(data!==exp_read) $fatal(1,"readback mismatch word=%h got=%h expected=%h",word,data,exp_read);
                    if(cache_index>=0 && kind!=2) cache[cache_index]=data;
                end
                p=dut.gen_surd_cpu.u_surd.phase;
                if(p==5 || p==6) norm_cycles=norm_cycles+1;
                if(p==1 || p==2) align_cycles=align_cycles+1;
                if(p==3 || p==4) product_cycles=product_cycles+1;
                if(dut.gen_surd_cpu.u_surd.rescue_request) rescues=rescues+1;
                if(dut.gen_surd_cpu.u_surd.normalization_start) starts=starts+1;
                inject_terminal_failure;
                @(negedge clk);waited=waited+1;inst_valid=0;inst_word=0;
                release_terminal_failure;
                if(kind==3 && waited==20) begin
                    if(observed_retires || observed_writes || !busy)
                        $fatal(1,"reset cancellation did not exercise pending normalization");
                    reset_core;
                    repeat(500) begin @(negedge clk);
                        if(we || retire || inst_done) $fatal(1,"stale post-reset retirement");end
                    waited=40001;
                end
            end
            if(kind!=3) begin
                if(!inst_done || status!==code[3:0] || observed_writes!=writes || observed_retires!=1)
                    $fatal(1,"retirement mismatch word=%h status=%d writes=%d retires=%d",word,status,observed_writes,observed_retires);
                check_bank(1);
                $display("INS %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",group,
                    word[63:56],tag,cycles-before_cycle,norm_cycles,align_cycles,
                    product_cycles,rescues,starts,stalls,status);
                if(code!=0 || (kind>=11 && kind<=13)) check_quiet;
            end
            @(negedge clk);
        end
    endtask
    task load_smoke;
        input [7:0] index;input [63:0] a,b,d;
        reg [191:0] tuple;
        integer j;
        begin
            tuple={d,b,a};code=0;writes=0;cache_index=-1;exp_read=0;kind=1;
            for(j=0;j<6;j=j+1) begin
                word={8'h70,index,j[7:0],tuple[32*j +:32],8'd0};issue;
            end
            word={8'h71,index,48'd0};writes=1;exp_a=a;exp_b=b;exp_d=d;issue;
        end
    endtask
