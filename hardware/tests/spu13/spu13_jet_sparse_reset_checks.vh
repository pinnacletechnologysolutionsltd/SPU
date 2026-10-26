task reset_controls;
    integer phase,x,c,before_completed;
    begin
        // Common reset cancellation in ISSUE, WAIT and RETIRE.
        for(phase=1;phase<=3;phase=phase+1) begin
            clear_inputs(); start=1;tick();start=0;
            cycles=0;
            while(uut.state!=phase && cycles<400) begin tick();cycles=cycles+1;end
            if(uut.state!=phase) $fatal(1,"reset phase unreachable");
            if(phase==2) tick(); // Reset after the shared fabric captures a launch.
            before_completed=completed;
            rst_n=0;fabric_rst_n=0;start=1;tick();start=0;
            rst_n=1;fabric_rst_n=1;
            repeat(12) tick();
            if(completed!=before_completed) $fatal(1,"stale reset completion");
        end
        // MAC-only reset: retain ownership until the old response is discarded.
        clear_inputs();start=1;tick();start=0;tick();
        if(flight!=1) $fatal(1,"drain control did not launch");
        tick(); // Supplier samples the registered launch before MAC-only reset.
        rst_n=0;tick();rst_n=1;
        before_completed=completed;cycles=0;
        while((flight!=0 || raw_busy || (DELAY!=0 && delay_left>=0)) && cycles<30) begin
            tick();cycles=cycles+1;
        end
        if(flight!=0 || completed!=before_completed) $fatal(1,"old response not drained");
        clear_inputs();expected_lo=0;expected_hi=N;expected_count=(N+1)*(N+2)/2;
        for(x=0;x<=N;x=x+1) for(c=0;c<4;c=c+1) expected[x][c]=0;
        run_case();
        // A withheld response must leave busy high; reset releases the stall.
        clear_inputs();hold_response=1;start=1;tick();start=0;
        repeat(100) begin tick();if(!busy || done) $fatal(1,"fabric stall fabricated completion");end
        rst_n=0;fabric_rst_n=0;tick();hold_response=0;
        rst_n=1;fabric_rst_n=1;tick();
        // Following-edge acceptance after empty completion.
        clear_inputs();j_lo=N+1;j_hi=0;k_lo=N+1;k_hi=0;
        expected_lo=N+1;expected_hi=0;expected_count=0;
        start=1;tick();start=0;tick();if(!done) $fatal(1,"empty retirement");
        start=1;tick();if(done || !busy) $fatal(1,"following-edge acceptance");
        start=0;tick();if(!done) $fatal(1,"second empty completion");tick();
    end
endtask
task negative_control;
    input integer control;
    begin
        clear_inputs();expected_lo=0;expected_hi=N;expected_count=(N+1)*(N+2)/2;
        for(row=0;row<=N;row=row+1) for(lane=0;lane<4;lane=lane+1) expected[row][lane]=0;
        case(control)
            1: begin j_lo=N+1;j_hi=0;j_coeff[0][0]=1;start=1;tick();end
            2: begin j_lo=N;j_hi=0;start=1;tick();end
            3: begin j_coeff[0][0]=P;start=1;tick();end
            4: begin expected_count=0;run_case();end
            5: begin expected[0][0]=1;run_case();end
            6: begin
                start=1;tick();start=0;tick();tick();rst_n=0;tick();rst_n=1;
                start=1;tick(); // No drain: owner monitor must reject reuse.
            end
            7: begin start=1;tick();start=0;force uut.state=0;tick();end
            8: begin force uut.done=1;tick();end
            9: begin force uut.mult_start=1;tick();end
            default: $fatal(1,"unknown control");
        endcase
        $fatal(1,"negative control did not trip its monitor");
    end
endtask
