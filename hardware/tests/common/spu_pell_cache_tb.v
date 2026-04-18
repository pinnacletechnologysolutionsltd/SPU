// spu_pell_cache_tb.v — last-known-good snapshot tests
`timescale 1ns/1ps

module spu_pell_cache_tb;

    reg         clk, rst_n, stable;
    reg [831:0] manifold_in;
    wire [831:0] cached_state;
    wire         restore_valid;

    spu_pell_cache dut (
        .clk(clk), .rst_n(rst_n),
        .manifold_in(manifold_in),
        .stable(stable),
        .cached_state(cached_state),
        .restore_valid(restore_valid)
    );

    always #20.833 clk = ~clk;

    integer fail = 0;

    initial begin
        clk = 0; rst_n = 0; stable = 0;
        manifold_in = 832'h0;
        #200; rst_n = 1; #50;

        // T1: no snapshot yet — restore_valid = 0
        @(posedge clk); #1;
        if (restore_valid === 1'b0)
            $display("T1 PASS: restore_valid=0 before first snapshot");
        else begin
            $display("T1 FAIL: restore_valid should be 0");
            fail = fail + 1;
        end

        // T2: assert stable — snapshot commits
        manifold_in = 832'hDEAD_BEEF_1234_5678_ABCD_EF01_2345_6789;
        @(posedge clk); #1; stable = 1;
        @(posedge clk); #1; stable = 0;
        @(posedge clk); #1;
        if (restore_valid === 1'b1 && cached_state === manifold_in) begin
            $display("T2 PASS: snapshot committed, restore_valid=1");
        end else begin
            $display("T2 FAIL: restore_valid=%b cached=%0h", restore_valid, cached_state[31:0]);
            fail = fail + 1;
        end

        // T3: manifold changes but stable=0 — cache must NOT update
        manifold_in = 832'hFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF;
        @(posedge clk); @(posedge clk); #1;
        if (cached_state[31:0] !== 32'hFFFF_FFFF)
            $display("T3 PASS: cache unchanged when stable=0");
        else begin
            $display("T3 FAIL: cache updated without stable strobe");
            fail = fail + 1;
        end

        // T4: new stable pulse — cache updates to new value
        @(posedge clk); #1; stable = 1;
        @(posedge clk); #1; stable = 0;
        @(posedge clk); #1;
        if (cached_state === manifold_in)
            $display("T4 PASS: cache updated on second stable pulse");
        else begin
            $display("T4 FAIL: cache not updated");
            fail = fail + 1;
        end

        // T5: reset clears restore_valid
        rst_n = 0; @(posedge clk); #1;
        if (restore_valid === 1'b0 && cached_state === 832'b0)
            $display("T5 PASS: reset clears cache and restore_valid");
        else begin
            $display("T5 FAIL: restore_valid=%b after reset", restore_valid);
            fail = fail + 1;
        end
        rst_n = 1;

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

    initial #1000000 begin $display("FAIL (timeout)"); $finish; end

endmodule
