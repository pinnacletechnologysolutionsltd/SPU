// spu_bus_arbiter_tb.v — Fibonacci round-robin arbiter tests
// Tests: single request, round-robin fairness, strike pre-emption,
//        idle Phi-advance, simultaneous requests served in rotation
`timescale 1ns/1ps

module spu_bus_arbiter_tb;

    localparam N = 4;  // use 4 nodes for tractable test

    reg        clk, rst_n;
    reg [N-1:0] req_lines, strike_req;
    wire [N-1:0] grant_lines;
    wire          governor_busy;
    wire [2:0]    active_node_id;

    // PHI_ADVANCE=5 so idle-advance fires quickly in simulation
    spu_bus_arbiter #(.NUM_NODES(N), .PHI_ADVANCE(5)) dut (
        .clk(clk), .rst_n(rst_n),
        .req_lines(req_lines), .strike_req(strike_req),
        .grant_lines(grant_lines), .governor_busy(governor_busy),
        .active_node_id(active_node_id)
    );

    always #20.833 clk = ~clk;
    integer fail = 0;

    task expect_grant;
        input [2:0] node;
        input [63:0] tag;
        begin
            @(posedge clk); #1;
            if (grant_lines[node] === 1'b1 && active_node_id === node && governor_busy === 1'b1)
                $display("PASS %0s: node %0d granted", tag, node);
            else begin
                $display("FAIL %0s: grant=%04b active=%0d busy=%b (exp node %0d)",
                    tag, grant_lines, active_node_id, governor_busy, node);
                fail = fail + 1;
            end
        end
    endtask

    integer i;
    reg [2:0] last_granted;

    initial begin
        clk = 0; rst_n = 0; req_lines = 0; strike_req = 0;
        #200; rst_n = 1; #100;

        // --- T1: Single request — node 1 ---
        @(posedge clk); #1; req_lines = 4'b0010;
        expect_grant(3'd1, "T1_single_node1");
        req_lines = 0; @(posedge clk); #1;

        // --- T2: Single request — node 0 ---
        req_lines = 4'b0001;
        expect_grant(3'd0, "T2_single_node0");
        req_lines = 0; @(posedge clk); #1;

        // --- T3: Round-robin — nodes 0,1,2,3 all request simultaneously
        //         Should be served in rotating order starting from current ptr
        begin : rr_test
            reg [2:0] seen [0:3];
            reg [2:0] seen_count;
            seen_count = 0;
            req_lines = 4'b1111;
            for (i = 0; i < 4; i = i + 1) begin
                @(posedge clk); #1;
                if (governor_busy) begin
                    seen[seen_count] = active_node_id;
                    seen_count = seen_count + 1;
                end
            end
            req_lines = 0;
            // All 4 nodes should have been granted exactly once
            if (seen_count === 4 &&
                seen[0] !== seen[1] && seen[0] !== seen[2] && seen[0] !== seen[3] &&
                seen[1] !== seen[2] && seen[1] !== seen[3] &&
                seen[2] !== seen[3]) begin
                $display("PASS T3: all 4 nodes granted once in round-robin");
            end else begin
                $display("FAIL T3: seen %0d/%0d unique grants (%0d,%0d,%0d,%0d)",
                    seen_count, 4, seen[0], seen[1], seen[2], seen[3]);
                fail = fail + 1;
            end
        end

        // --- T4: Strike pre-empts normal request ---
        @(posedge clk); #1;
        req_lines  = 4'b0100;   // node 2 requests normally
        strike_req = 4'b0001;   // node 0 strikes
        @(posedge clk); #1;
        if (active_node_id === 3'd0 && grant_lines[0] === 1'b1) begin
            $display("PASS T4: strike node 0 pre-empts normal node 2");
        end else begin
            $display("FAIL T4: active=%0d grant=%04b (expected node 0 via strike)",
                active_node_id, grant_lines);
            fail = fail + 1;
        end
        req_lines = 0; strike_req = 0; @(posedge clk); #1;

        // --- T5: Idle Phi-advance — ptr rotates after PHI_ADVANCE cycles ---
        begin : phi_test
            reg [2:0] ptr_before, ptr_after;
            // Request to see current ptr
            req_lines = 4'b1111;
            @(posedge clk); #1;
            ptr_before = active_node_id;
            req_lines = 0;
            // Wait > PHI_ADVANCE idle cycles
            repeat(8) @(posedge clk);
            // Request again — ptr should have advanced
            req_lines = 4'b1111;
            @(posedge clk); #1;
            ptr_after = active_node_id;
            req_lines = 0;
            if (ptr_after !== ptr_before) begin
                $display("PASS T5: Phi-advance moved ptr from %0d to %0d",
                    ptr_before, ptr_after);
            end else begin
                $display("FAIL T5: ptr did not advance after idle (before=%0d after=%0d)",
                    ptr_before, ptr_after);
                fail = fail + 1;
            end
        end

        // --- T6: No grant when no requests ---
        @(posedge clk); #1;
        req_lines = 0; strike_req = 0;
        @(posedge clk); #1;
        if (governor_busy === 1'b0 && grant_lines === {N{1'b0}}) begin
            $display("PASS T6: idle — no grant, governor_busy=0");
        end else begin
            $display("FAIL T6: spurious grant in idle (busy=%b grant=%04b)",
                governor_busy, grant_lines);
            fail = fail + 1;
        end

        if (fail == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail);
        $finish;
    end

    initial #5000000 begin $display("FAIL (timeout)"); $finish; end

endmodule
