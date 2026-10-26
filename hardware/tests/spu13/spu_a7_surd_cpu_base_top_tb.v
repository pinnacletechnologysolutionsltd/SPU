`timescale 1ns/1ps
// spu_a7_surd_cpu_base_top_tb.v -- CPU-BASE-TOP-1 S1: clock/reset topology of the Base top.
// Checks (zero-delay BUFG model: BUFG insertion delay, skew and metastability are NOT exercised):
//  1 release-phase sweep   2 no runt cpu_clk   3 pulse widths   4 mid-run restart to step 0 (register level + short trace)
//  5 cpu_clk stopped (no rising edge) after rst_n_int falls   6 release timing (257-259 sample edges; exactly 2 cpu_clk edges in reset)
// Not covered here: long golden parity trace (build/ harness), pad fanout / BUFG topology (structural script).
module spu_a7_surd_cpu_base_top_tb;
    reg sys_clk = 0, rst_n = 0;
    always #10 sys_clk = ~sys_clk;
    wire uart_tx;
    spu_a7_surd_cpu_base_top dut (.sys_clk(sys_clk), .rst_n(rst_n), .uart_tx(uart_tx));

    integer errors = 0;
    task check(input [255:0] label, input cond);
        begin
            if (!cond) begin errors = errors + 1; $display("CHECK_FAILED: %0s", label); end
        end
    endtask

    // ---- monitors ----
    real t_cpu_rise = 0, t_cpu_fall = 0, min_high = 1e9, min_low = 1e9;
    always @(posedge dut.cpu_clk) begin
        if (t_cpu_fall > 0 && ($realtime - t_cpu_fall) < min_low) min_low = $realtime - t_cpu_fall;
        t_cpu_rise = $realtime;
    end
    always @(negedge dut.cpu_clk) begin
        if (t_cpu_rise > 0 && ($realtime - t_cpu_rise) < min_high) min_high = $realtime - t_cpu_rise;
        t_cpu_fall = $realtime;
    end
    integer rel_off_edge = 0;                 // cpu_rst_n rises not on a cpu_clk edge
    always @(posedge dut.cpu_rst_n) if ($realtime != t_cpu_rise) rel_off_edge = rel_off_edge + 1;
    integer edges_in_reset = 0, last_edges_in_reset = -1;   // cpu_clk rising edges between rst_n_int rise and cpu_rst_n rise
    always @(posedge dut.rst_n_int) edges_in_reset = 0;
    always @(posedge dut.cpu_clk) if (dut.rst_n_int && !dut.cpu_rst_n) edges_in_reset = edges_in_reset + 1;
    always @(posedge dut.cpu_rst_n) last_edges_in_reset = edges_in_reset;
    integer low_seen = 0, edges_after_assert = 0;   // consecutive sys edges at which rst_n_int was already low (pre-edge value)
    always @(posedge sys_clk) if (dut.rst_n_int === 1'b0) low_seen = low_seen + 1; else low_seen = 0;
    always @(posedge dut.cpu_clk) if (low_seen >= 1) edges_after_assert = edges_after_assert + 1;   // the edge coincident with the fall has low_seen == 0
    integer sys_edges = 0, rel_latency = 0;   // sys_clk edges from last pad rise to rst_n_int rise
    always @(posedge sys_clk) sys_edges = sys_edges + 1;
    integer pad_rise_edge = 0;
    always @(posedge rst_n) pad_rise_edge = sys_edges;
    always @(posedge dut.rst_n_int) rel_latency = sys_edges - pad_rise_edge;
    always @(dut.u_workload.rst_n or dut.cpu_rst_n) check("workload reset is exactly cpu_rst_n", dut.u_workload.rst_n === dut.cpu_rst_n);

    // ---- helpers ----
    task pad_pulse(input real start_off_ns, input integer width_cycles, input real rel_off_ns);
        begin
            @(posedge sys_clk); #(start_off_ns); rst_n = 0;
            repeat (width_cycles) @(posedge sys_clk);
            #(rel_off_ns); rst_n = 1;
        end
    endtask
    task run_cpu(input integer n);
        begin repeat (n) @(posedge dut.cpu_clk); end
    endtask
    task wait_cpu_released;
        integer g;
        begin g = 0; while (!dut.cpu_rst_n && g < 2000) begin @(posedge sys_clk); g = g + 1; end
              check("cpu_rst_n released within 2000 sys cycles", dut.cpu_rst_n === 1'b1); end
    endtask

    // short golden trace: parity transitions + checksum over the first 800 workload cycles
    reg [15:0] tr_a [0:7], tr_b [0:7]; reg [31:0] ck_a, ck_b; integer na, nb;
    task capture(input integer which);
        integer c, n; reg last; reg [31:0] ck;
        begin
            n = 0; last = uart_tx;
            for (c = 1; c <= 800; c = c + 1) begin
                @(posedge dut.cpu_clk);
                if (uart_tx !== last) begin last = uart_tx; if (n < 8) begin if (which == 0) tr_a[n] = c; else tr_b[n] = c; end n = n + 1; end
            end
            ck = dut.u_workload.checksum;
            if (which == 0) begin ck_a = ck; na = n; end else begin ck_b = ck; nb = n; end
        end
    endtask

    integer k, w, i;
    real offs [0:7];
    integer widths [0:4];
    initial begin
        offs[0]=0.0; offs[1]=3.0; offs[2]=6.0; offs[3]=9.0; offs[4]=12.0; offs[5]=15.0; offs[6]=18.0; offs[7]=19.5;
        widths[0]=1; widths[1]=2; widths[2]=3; widths[3]=10; widths[4]=300;
        // startup release (pad low from t=0), first trace
        #200; @(posedge sys_clk); #5; rst_n = 1;
        wait_cpu_released; capture(0);
        check("startup release latency 257..259 sample edges", rel_latency >= 257 && rel_latency <= 259);
        check("exactly 2 cpu_clk edges while cpu_rst_n low after release", last_edges_in_reset == 2);
        // 1 release-phase sweep
        for (k = 0; k < 8; k = k + 1) begin
            pad_pulse(7.0, 3, offs[k]);
            wait_cpu_released; run_cpu(20);
            check("sweep: release latency 257..259", rel_latency >= 257 && rel_latency <= 259);
            check("sweep: exactly 2 cpu_clk edges in reset", last_edges_in_reset == 2);
        end
        // 3 pulse widths (width 1 recorded only: one sampled edge)
        for (w = 1; w < 5; w = w + 1) begin
            run_cpu(60);
            pad_pulse(5.0, widths[w], 5.0);
            repeat (5) @(posedge sys_clk);
            check("pulse asserts internal reset", dut.rst_n_int === 1'b0);
            wait_cpu_released; run_cpu(5);
            check("pulse: release latency 257..259", rel_latency >= 257 && rel_latency <= 259);
        end
        // pulse inside the stable-high window: release must follow the SECOND pulse
        pad_pulse(5.0, 3, 5.0);
        repeat (100) @(posedge sys_clk);
        check("window still open after 100 cycles", dut.rst_n_int === 1'b0);
        pad_pulse(5.0, 3, 5.0);
        wait_cpu_released;
        check("window restart: latency measured from second pulse", rel_latency >= 257 && rel_latency <= 259);
        // sub-sample glitch between two sys_clk edges is not sampled in this zero-delay model (informational scope)
        run_cpu(40);
        @(posedge sys_clk); #6; rst_n = 0; #5; rst_n = 1;
        run_cpu(10);
        check("sub-sample glitch not sampled (zero-delay model)", dut.cpu_rst_n === 1'b1);
        // 4 mid-run restart to step 0
        run_cpu(300);
        check("workload advanced before restart (non-vacuous)", dut.u_workload.rng !== 64'h13579bdf2468ace1 && dut.u_workload.tick != 0);
        pad_pulse(5.0, 300, 5.0);
        @(posedge dut.cpu_rst_n);
        check("restart: tick 0", dut.u_workload.tick === 6'd0);
        check("restart: step 0", dut.u_workload.step === 5'd0);
        check("restart: pending/valid 0", dut.u_workload.pending === 1'b0 && dut.u_workload.valid === 1'b0);
        check("restart: instruction 0", dut.u_workload.instruction === 64'd0);
        check("restart: checksum 0", dut.u_workload.checksum === 32'd0);
        check("restart: rng seed", dut.u_workload.rng === 64'h13579bdf2468ace1);
        check("restart: index regs", dut.u_workload.index_a === 3'd0 && dut.u_workload.index_b === 3'd1 && dut.u_workload.index_c === 3'd2);
        capture(1);
        check("restart reproduces first-800-cycle checksum", ck_a === ck_b);
        check("restart reproduces parity transition count", na == nb);
        check("restart reproduces parity transition times", tr_a[0]===tr_b[0] && tr_a[1]===tr_b[1] && tr_a[2]===tr_b[2] && tr_a[3]===tr_b[3]);
        check("trace is non-trivial", na >= 1);
        // 2 / 5 clock integrity over the whole run
        check("no runt cpu_clk high phase (>= 19.9 ns)", min_high >= 19.9);
        check("no runt cpu_clk low phase (>= 19.9 ns)", min_low >= 19.9);
        check("cpu_rst_n only rises on a cpu_clk edge", rel_off_edge == 0);
        check("cpu_clk stopped after reset assertion", edges_after_assert == 0);
        if (errors == 0) $display("PASS: spu_a7_surd_cpu_base_top_tb (latency=%0d min_high=%0f min_low=%0f)", rel_latency, min_high, min_low);
        else $display("%0d checks did not hold", errors);
        $finish;
    end
    initial begin #50000000; $display("TIMEOUT_NO_VERDICT"); $finish; end
endmodule
