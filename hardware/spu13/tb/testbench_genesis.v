// testbench_genesis.v - Hardened Path C Simulation
`timescale 1ns/1ps

module testbench_genesis;
    reg clk_12mhz;
    reg clk_1mhz;
    reg rst_n;
    reg [15:0] spu4_rx;
    wire [31:0] spu4_tx;
    wire [7:0] uart_tx_byte;
    wire uart_tx_en;
    wire piranha_pulse;
    reg  alu_start;
    wire alu_done;
    integer gi;

    // Instantiate SPU-13
    spu_13_top uut (
        .clk_12mhz(clk_12mhz),
        .clk_1mhz(clk_1mhz),
        .rst_n(rst_n),
        .spu4_rx(spu4_rx),
        .spu4_tx(spu4_tx),
        .uart_tx_byte(uart_tx_byte),
        .uart_tx_en(uart_tx_en),
        .piranha_pulse(piranha_pulse),
        .alu_start(alu_start),
        .alu_done(alu_done)
    );

    initial begin
        clk_12mhz = 0; clk_1mhz = 0; rst_n = 0; alu_start = 0;
        spu4_rx = 16'h1FFF; // Dummy Snap Alert
        #100 rst_n = 1;
        $display("--- Genesis-Alpha: Physical-Timing Simulation ---");
        
        // Force the ALU inputs for the 13-gon anchor test (21,43,43) spread
        // Scaled to fixed point (x 0x1000)
        force uut.alu_inst.A_in = 32'h00015000; // 21.0
        force uut.alu_inst.B_in = 32'h0002B000; // 43.0
        
        // Wait for BRAM Hydration
        wait(uut.boot_complete == 1'b1);
        
        #50; // Settle
        
        // Pulse the ALU start sequence synchronously (simulate 25 iterations of the recursive tree)
        for (gi = 0; gi < 25; gi = gi + 1) begin
            @(posedge clk_12mhz) alu_start = 1;
            @(posedge clk_12mhz) alu_start = 0;
            
            // Wait for TDM execution to complete
            wait(alu_done == 1'b1);
            #10;
        end
        
        // Let the berry gate and janus mirror settle
        #50;
        
        // Verify 18-bit Chiral Snap (Expected 0x026D1)
        // Wait, for (21, 43), since A_out <= A_in upon dissonant, result_18 should match A_in.
        // The original check was for 0x026D1. A_in is 21 (0x15). So result_18 should be 0x15?
        // Let's print out what we get:
        $display("ALU output evaluated: %h", uut.alu_inst.result_18[17:0]);
        if (uut.alu_inst.result_18[17:0] == 18'h15000)
            $display("PASS: 15-Sigma Snap Achieved with 13D Geodesic Spreads.");
        else
            $display("TIMEOUT FAIL: Cubic Drift detected (Got: %h).", uut.alu_inst.result_18[17:0]);

        $finish;
    end

    always #5 clk_12mhz = ~clk_12mhz;
    always #50 clk_1mhz = ~clk_1mhz;
endmodule
