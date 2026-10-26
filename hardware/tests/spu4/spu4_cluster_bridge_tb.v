// spu4_cluster_bridge_tb.v — Testbench for SPU-4 cluster bridge.
// Verifies: status packing, SOM label, command decode.

`timescale 1ns / 1ps

module spu4_cluster_bridge_tb;
    reg clk, rst_n;
    reg snap_locked;
    reg [7:0] dissonance;
    reg [9:0] status_payload;
    reg [3:0] som_label;
    reg       som_valid;
    reg [31:0] node_rx;
    wire [23:0] node_tx;
    wire cmd_start;
    wire [7:0] cmd_payload;

    spu4_cluster_bridge u_bridge (
        .clk(clk), .rst_n(rst_n),
        .snap_locked(snap_locked),
        .dissonance(dissonance),
        .status_payload(status_payload),
        .som_label(som_label), .som_valid(som_valid),
        .node_rx(node_rx), .node_tx(node_tx),
        .cmd_start(cmd_start), .cmd_payload(cmd_payload)
    );

    always #41.66 clk = ~clk;
    integer pass, fail;

    initial begin
        clk = 0; rst_n = 0;
        snap_locked = 0; dissonance = 0; status_payload = 0;
        som_label = 0; som_valid = 0; node_rx = 0;
        pass = 0; fail = 0;
        #200; rst_n = 1; #200;

        // Test 1: Status packing with SOM classification
        snap_locked = 1; dissonance = 8'hAB; status_payload = 10'h155;
        som_label = 4'hD; som_valid = 1;
        #200;
        if (node_tx[23:20] !== 4'hD)
            begin $display("FAIL T1: som_label"); fail = fail + 1; end
        else if (node_tx[19] !== 1'b1)
            begin $display("FAIL T1: som_valid"); fail = fail + 1; end
        else if (node_tx[18] !== 1'b1)
            begin $display("FAIL T1: snap bit"); fail = fail + 1; end
        else if (node_tx[17:10] !== 8'hAB)
            begin $display("FAIL T1: dissonance"); fail = fail + 1; end
        else if (node_tx[9:0] != 10'h155)
            begin $display("FAIL T1: payload"); fail = fail + 1; end
        else begin $display("PASS T1: status+SOM packing"); pass = pass + 1; end

        // Test 2: SOM invalid — classification not present
        som_valid = 0; som_label = 4'h0;
        #200;
        if (node_tx[19] !== 1'b0)
            begin $display("FAIL T2: som_valid clear"); fail = fail + 1; end
        else begin $display("PASS T2: SOM invalid flag"); pass = pass + 1; end

        // Test 3: START command
        node_rx = 32'h00000001;
        #200;
        if (!cmd_start)
            begin $display("FAIL T3: cmd_start"); fail = fail + 1; end
        else begin $display("PASS T3: START decode"); pass = pass + 1; end

        // Test 4: Config data command
        node_rx = 32'h00000042;
        #200;
        if (cmd_payload !== 8'h42)
            begin $display("FAIL T4: payload"); fail = fail + 1; end
        else begin $display("PASS T4: config data"); pass = pass + 1; end

        // Test 5: NOP
        node_rx = 0;
        #200;
        if (cmd_start)
            begin $display("FAIL T5: unexpected start"); fail = fail + 1; end
        else begin $display("PASS T5: NOP ignored"); pass = pass + 1; end

        if (fail == 0) $display("PASS");
        else $display("FAIL");
        $finish;
    end
endmodule
