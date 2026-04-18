// spu_governor_mux_tb.v — testbench for spu_governor_mux
// Tests: single satellite, priority contention, error aggregation, idle cycle
`timescale 1ns/1ps

module spu_governor_mux_tb;

    localparam N = 3;  // 3 satellites under test

    reg        clk, rst_n;
    reg [N-1:0]    sat_valid;
    reg [N-1:0]    sat_error;
    reg [N*3-1:0]  sat_node_id;
    reg [N*64-1:0] sat_chord;

    wire        mux_valid;
    wire [63:0] mux_chord;
    wire [2:0]  mux_node_id;
    wire        mux_error;

    spu_governor_mux #(.NUM_SATELLITES(N)) dut (
        .clk(clk), .rst_n(rst_n),
        .sat_valid(sat_valid), .sat_error(sat_error),
        .sat_node_id(sat_node_id), .sat_chord(sat_chord),
        .mux_valid(mux_valid), .mux_chord(mux_chord),
        .mux_node_id(mux_node_id), .mux_error(mux_error)
    );

    initial clk = 0;
    always #20.833 clk = ~clk;

    integer pass_count, fail_count;

    // Pulse sat_valid[idx] for 1 cycle and capture output 1 cycle later
    task fire_sat;
        input integer idx;
        input [63:0]  chord_val;
        begin
            @(posedge clk); #1;
            sat_valid[idx] = 1'b1;
            sat_chord[idx*64 +: 64] = chord_val;
            @(posedge clk); #1;
            sat_valid = {N{1'b0}};
        end
    endtask

    // Pulse multiple sats simultaneously
    task fire_multi;
        input [N-1:0] mask;
        begin
            @(posedge clk); #1;
            sat_valid = mask;
            @(posedge clk); #1;
            sat_valid = {N{1'b0}};
        end
    endtask

    initial begin
        rst_n = 0; sat_valid = 0; sat_error = 0;
        pass_count = 0; fail_count = 0;

        // Pre-load node IDs and chords
        sat_node_id[0*3 +: 3] = 3'd0;
        sat_node_id[1*3 +: 3] = 3'd1;
        sat_node_id[2*3 +: 3] = 3'd2;
        sat_chord[0*64 +: 64] = 64'hAAAA_0000_0000_0000;
        sat_chord[1*64 +: 64] = 64'hBBBB_1111_1111_1111;
        sat_chord[2*64 +: 64] = 64'hCCCC_2222_2222_2222;

        #200; rst_n = 1; #100;

        // --- T1: Only satellite 2 fires ---
        fire_sat(2, 64'hCCCC_2222_2222_2222);
        // Output appears 1 cycle after the valid pulse
        @(posedge clk); // let the registered output settle one more cycle
        if (mux_valid === 1'b1 && mux_node_id === 3'd2 &&
            mux_chord === 64'hCCCC_2222_2222_2222) begin
            $display("T1 PASS: single satellite 2 fires");
            pass_count = pass_count + 1;
        end else begin
            $display("T1 FAIL: valid=%b node=%0d chord=%016h (exp: 1, 2, CCCC...)",
                mux_valid, mux_node_id, mux_chord);
            fail_count = fail_count + 1;
        end

        @(posedge clk); #1;  // idle check
        if (mux_valid === 1'b0) begin
            $display("T2 PASS: idle cycle has mux_valid=0");
            pass_count = pass_count + 1;
        end else begin
            $display("T2 FAIL: expected mux_valid=0 in idle, got %b", mux_valid);
            fail_count = fail_count + 1;
        end

        // --- T3: Satellites 1 and 2 fire simultaneously; node 1 wins ---
        sat_chord[1*64 +: 64] = 64'hBBBB_1111_1111_1111;
        sat_chord[2*64 +: 64] = 64'hCCCC_2222_2222_2222;
        fire_multi(3'b110);  // sat 1 and 2 both valid
        @(posedge clk);
        if (mux_valid === 1'b1 && mux_node_id === 3'd1 &&
            mux_chord === 64'hBBBB_1111_1111_1111) begin
            $display("T3 PASS: sat1 wins over sat2 (lower ID priority)");
            pass_count = pass_count + 1;
        end else begin
            $display("T3 FAIL: valid=%b node=%0d chord=%016h (exp: 1, 1, BBBB...)",
                mux_valid, mux_node_id, mux_chord);
            fail_count = fail_count + 1;
        end

        // --- T4: All three fire; node 0 wins ---
        sat_chord[0*64 +: 64] = 64'hAAAA_0000_0000_0000;
        fire_multi(3'b111);
        @(posedge clk);
        if (mux_valid === 1'b1 && mux_node_id === 3'd0 &&
            mux_chord === 64'hAAAA_0000_0000_0000) begin
            $display("T4 PASS: node 0 wins 3-way contention");
            pass_count = pass_count + 1;
        end else begin
            $display("T4 FAIL: valid=%b node=%0d chord=%016h (exp: 1, 0, AAAA...)",
                mux_valid, mux_node_id, mux_chord);
            fail_count = fail_count + 1;
        end

        // --- T5: Error aggregation — sat 2 fires error, no valid ---
        @(posedge clk); #1;
        sat_error[2] = 1'b1;
        @(posedge clk); #1;
        sat_error = {N{1'b0}};
        @(posedge clk);
        if (mux_error === 1'b1 && mux_valid === 1'b0) begin
            $display("T5 PASS: mux_error asserted, mux_valid low");
            pass_count = pass_count + 1;
        end else begin
            $display("T5 FAIL: mux_error=%b mux_valid=%b (exp: 1, 0)",
                mux_error, mux_valid);
            fail_count = fail_count + 1;
        end

        // --- T6: Only satellite 0 fires ---
        fire_sat(0, 64'hAAAA_DEAD_BEEF_0000);
        @(posedge clk);
        if (mux_valid === 1'b1 && mux_node_id === 3'd0 &&
            mux_chord === 64'hAAAA_DEAD_BEEF_0000) begin
            $display("T6 PASS: single satellite 0 fires");
            pass_count = pass_count + 1;
        end else begin
            $display("T6 FAIL: valid=%b node=%0d chord=%016h",
                mux_valid, mux_node_id, mux_chord);
            fail_count = fail_count + 1;
        end

        if (fail_count == 0)
            $display("PASS");
        else
            $display("FAIL (%0d failures)", fail_count);
        $finish;
    end

    initial #500000 begin $display("FAIL (timeout)"); $finish; end

endmodule
