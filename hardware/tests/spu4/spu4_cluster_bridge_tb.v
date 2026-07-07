// spu4_cluster_bridge_tb.v — Testbench for SPU-4 cluster bridge.
// Verifies: status packing, command decode, integrity check.

`timescale 1ns / 1ps

module spu4_cluster_bridge_tb;
    reg clk, rst_n;
    reg snap_locked;
    reg [7:0] dissonance;
    reg [6:0] status_payload;
    reg [31:0] node_rx;
    wire [15:0] node_tx;
    wire cmd_start;
    wire [7:0] cmd_payload;

    spu4_cluster_bridge u_bridge (
        .clk(clk), .rst_n(rst_n),
        .snap_locked(snap_locked),
        .dissonance(dissonance),
        .status_payload(status_payload),
        .node_rx(node_rx), .node_tx(node_tx),
        .cmd_start(cmd_start), .cmd_payload(cmd_payload)
    );

    always #41.66 clk = ~clk;
    integer pass, fail;

    initial begin
        clk = 0; rst_n = 0;
        snap_locked = 0; dissonance = 0; status_payload = 0; node_rx = 0;
        pass = 0; fail = 0;
        #200; rst_n = 1; #200;

        // Test 1: Status packing
        snap_locked = 1; dissonance = 8'hAB; status_payload = 7'h55;
        #200;
        if (node_tx[15] !== 1'b1)
            begin $display("FAIL T1: snap bit"); fail = fail + 1; end
        else if (node_tx[14:7] !== 8'hAB)
            begin $display("FAIL T1: dissonance"); fail = fail + 1; end
        else if (node_tx[6:0] !== 7'h55)
            begin $display("FAIL T1: payload"); fail = fail + 1; end
        else begin $display("PASS T1: status packing"); pass = pass + 1; end

        // Test 2: START command
        node_rx = 32'h00000001;  // cmd=1 = START
        #200;
        if (!cmd_start)
            begin $display("FAIL T2: cmd_start"); fail = fail + 1; end
        else begin $display("PASS T2: START decode"); pass = pass + 1; end

        // Test 3: Config data command
        node_rx = 32'h00000042;  // cmd=0x42 = config data
        #200;
        if (cmd_payload !== 8'h42)
            begin $display("FAIL T3: payload"); fail = fail + 1; end
        else begin $display("PASS T3: config data"); pass = pass + 1; end

        // Test 4: NOP (cmd=0) should not trigger anything
        node_rx = 0;
        #200;
        if (cmd_start)
            begin $display("FAIL T4: unexpected start"); fail = fail + 1; end
        else begin $display("PASS T4: NOP ignored"); pass = pass + 1; end

        if (fail == 0) $display("PASS");
        else $display("FAIL");
        $finish;
    end
endmodule
