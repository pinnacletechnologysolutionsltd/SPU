// Event scoreboard samples supplier response before the edge and DUT after it.
task clear_inputs;
    begin
        start=0;op_mul=1;j_lo=0;j_hi=N;k_lo=0;k_hi=N;
        for(row=0;row<=N;row=row+1) for(lane=0;lane<4;lane=lane+1) begin
            j_coeff[row][lane]=0;k_coeff[row][lane]=0;
        end
    end
endtask
task tag_monitor;
    integer x,c;
    begin
        if (!((j_lo==N+1 && j_hi==0)||(j_lo<=j_hi && j_hi<=N))) $fatal(1,"invalid J tag");
        if (!((k_lo==N+1 && k_hi==0)||(k_lo<=k_hi && k_hi<=N))) $fatal(1,"invalid K tag");
        for(x=0;x<=N;x=x+1) for(c=0;c<4;c=c+1) begin
            if(j_coeff[x][c]>=P || k_coeff[x][c]>=P) $fatal(1,"noncanonical coefficient");
            if((x<j_lo || x>j_hi) && j_coeff[x][c]!=0) $fatal(1,"J tag promise violated");
            if((x<k_lo || x>k_hi) && k_coeff[x][c]!=0) $fatal(1,"K tag promise violated");
        end
    end
endtask
task tick;
    reg accepting, response;
    integer x,c;
    begin
        accepting=rst_n && start && !busy;
        response=mult_done;
        if(accepting) begin
            if(flight!=0 || raw_busy || (DELAY!=0 && delay_left>=0)) $fatal(1,"premature fabric reuse");
            tag_monitor(); active=1;issued=0;ek=0;ei=0;mul=op_mul;
            al=j_lo;ah=j_hi;bl=k_lo;bh=k_hi;
            prior_lo=r_lo;prior_hi=r_hi;
            for(x=0;x<=N;x=x+1) for(c=0;c<4;c=c+1) begin
                accepted_a[x][c]=j_coeff[x][c];accepted_b[x][c]=k_coeff[x][c];prior[x][c]=r_coeff[x][c];
            end
        end
        if(!rst_n) active=0;
        if(!fabric_rst_n) flight=0;
        else if(response && flight!=0) flight=flight-1;
        #5 clk=1; #1;
        if(rns_error) $fatal(1,"shared multiplier parity");
        if(mult_start) begin
            if(!active || !mul || flight!=0) $fatal(1,"extra multiply issue");
            while(ek<=N && !(ei>=al && ei<=ah && ek-ei>=bl && ek-ei<=bh)) begin
                if(ei==ek) begin ek=ek+1;ei=0;end else ei=ei+1;
            end
            if(ek>N) $fatal(1,"unexpected pair");
            ej=ek-ei;
            if(a0!==accepted_a[ei][0] || a1!==accepted_a[ei][1] || a2!==accepted_a[ei][2] || a3!==accepted_a[ei][3] ||
               b0!==accepted_b[ej][0] || b1!==accepted_b[ej][1] || b2!==accepted_b[ej][2] || b3!==accepted_b[ej][3])
                $fatal(1,"issue order/operand mismatch");
            if(ei==ek) begin ek=ek+1;ei=0;end else ei=ei+1;
            issued=issued+1;flight=1;
        end
        if(!rst_n) begin
            if(busy || done || mult_start || r_lo!=N+1 || r_hi!=0) $fatal(1,"reset outputs");
            for(x=0;x<=N;x=x+1) for(c=0;c<4;c=c+1) if(r_coeff[x][c]!=0) $fatal(1,"reset result");
        end else if(active) begin
            if(err_zero_divisor) $fatal(1,"unexpected MAC fault");
            if(done) begin
                if(busy || flight!=0 || issued!=expected_count) $fatal(1,"completion/count mismatch");
                if(r_lo!=expected_lo || r_hi!=expected_hi) $fatal(1,"result tag mismatch");
                for(x=0;x<=N;x=x+1) for(c=0;c<4;c=c+1)
                    if(r_coeff[x][c]!==expected[x][c]) $fatal(1,"result mismatch case %0d",case_id);
                active=0;completed=completed+1;
            end else begin
                if(!busy) $fatal(1,"early busy drop");
                if(r_lo!=prior_lo || r_hi!=prior_hi) $fatal(1,"tag changed before retirement");
                for(x=0;x<=N;x=x+1) for(c=0;c<4;c=c+1)
                    if(r_coeff[x][c]!==prior[x][c]) $fatal(1,"result changed before retirement");
            end
        end else if(done) $fatal(1,"unsolicited completion");
        if(done && old_done) $fatal(1,"wide done pulse");
        old_done=done;checks=checks+1;
        #4 clk=0;
    end
endtask
task run_case;
    begin
        start=1;tick();if(done || !busy) $fatal(1,"acceptance completion collision");
        // Poison live inputs after capture; busy-time starts cannot replace operation.
        for(row=0;row<=N;row=row+1) for(lane=0;lane<4;lane=lane+1) begin
            j_coeff[row][lane]=0;k_coeff[row][lane]=0;
        end
        op_mul=!op_mul;cycles=0;
        while(!done && cycles<400) begin tick();cycles=cycles+1;end
        if(!done) $fatal(1,"operation timeout");
        start=0;tick();if(done) $fatal(1,"done not pulsed");
        case_id=case_id+1;
    end
endtask
`include "hardware/tests/spu13/spu13_jet_sparse_reset_checks.vh"
