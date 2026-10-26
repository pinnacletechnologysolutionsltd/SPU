    // Simulation-only bank snapshots and normalizer terminal fault injection.
    reg [191:0] saved_tuples[0:7];
    reg [7:0] saved_initialized;
    integer checked_preservations=0,checked_aliases=0,injected_faults=0;
    reg injected;
    task snapshot_bank;
        integer i;
        begin
            saved_initialized=dut.gen_surd_cpu.u_surd.bank.initialized;
            for(i=0;i<8;i=i+1)
                saved_tuples[i]=dut.gen_surd_cpu.u_surd.bank.tuples[i];
            injected=0;
        end
    endtask
    task inject_terminal_failure;
        begin
            if((kind==5 || kind==6) && !injected &&
               dut.gen_surd_cpu.u_surd.arithmetic_unit.n_done) begin
                if(!busy || (dut.gen_surd_cpu.u_surd.phase!=2 &&
                             dut.gen_surd_cpu.u_surd.phase!=6) ||
                   !dut.gen_surd_cpu.u_surd.arithmetic_unit.n_valid)
                    $fatal(1,"fault injection missed a valid busy normalizer completion");
                if(kind==5)
                    force dut.gen_surd_cpu.u_surd.arithmetic_unit.n_fault=1'b1;
                else
                    force dut.gen_surd_cpu.u_surd.arithmetic_unit.n_valid=1'b0;
                injected=1;injected_faults=injected_faults+1;
            end
        end
    endtask
    task release_terminal_failure;
        begin
            if(injected) begin
                release dut.gen_surd_cpu.u_surd.arithmetic_unit.n_fault;
                release dut.gen_surd_cpu.u_surd.arithmetic_unit.n_valid;
            end
        end
    endtask
    task check_bank;
        input count_checks;
        integer i;
        reg [7:0] expected_initialized;
        begin
            expected_initialized=saved_initialized;
            if(writes) expected_initialized[word[50:48]]=1'b1;
            if(dut.gen_surd_cpu.u_surd.bank.initialized!==expected_initialized)
                $fatal(1,"bank validity changed unexpectedly word=%h",word);
            for(i=0;i<8;i=i+1) begin
                if(writes && i==word[50:48]) begin
                    if(dut.gen_surd_cpu.u_surd.bank.tuples[i]!=={exp_d,exp_b,exp_a})
                        $fatal(1,"retired destination mismatch word=%h",word);
                end else if(dut.gen_surd_cpu.u_surd.bank.tuples[i]!==saved_tuples[i])
                    $fatal(1,"preservation failure bank=%d word=%h",i,word);
            end
            if(code!=0 && count_checks) checked_preservations=checked_preservations+1;
            if(kind==5 || kind==6) begin
                if(!injected || status!==4'd3 || observed_writes!=0)
                    $fatal(1,"ENGINE_FAULT injection/status/write mismatch");
            end
            if(kind>=11 && kind<=13) begin
                if((kind==11 && rescues!=0) || (kind!=11 && rescues!=1))
                    $fatal(1,"alias fit/rescue path not exercised kind=%d",kind);
                if(count_checks) checked_aliases=checked_aliases+1;
            end
        end
    endtask
    task check_quiet;
        integer i;
        begin
            // No issue during the guard: detect stale completion or hidden writes.
            repeat(4) begin
                @(negedge clk);
                if(we || retire || inst_done || busy || !ready)
                    $fatal(1,"late write/retirement or recovery-readiness failure");
                check_bank(0);
            end
        end
    endtask
