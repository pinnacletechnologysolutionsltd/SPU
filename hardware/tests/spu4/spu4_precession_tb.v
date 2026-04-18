`timescale 1ns/1ps

module spu4_precession_tb;

    reg clk;
    reg rst_n;
    wire [23:0] inst_data;
    wire [9:0] pc;
    wire snap_alert;
    wire whisper_tx;
    wire [63:0] debug_reg_r0;

    // 1. Program Memory (BRAM Simulation)
    reg [23:0] prog_mem [0:1023];
    integer i;
    initial begin
        for (i = 0; i < 1024; i = i + 1) prog_mem[i] = 24'h0;
        $readmemh("hardware/spu4/tests/precession.hex", prog_mem);
    end
    assign inst_data = (pc < 1024) ? prog_mem[pc] : 24'h0;

    // 2. Unit Under Test
    spu4_top uut (
        .clk(clk),
        .rst_n(rst_n),
        .inst_data(inst_data),
        .pc(pc),
        .snap_alert(snap_alert),
        .whisper_tx(whisper_tx),
        .debug_reg_r0(debug_reg_r0)
    );

    // 3. Clock Generation
    always #40 clk = ~clk; // ~12.5 MHz

    reg whisper_caught;
    always @(posedge clk) if (whisper_tx) whisper_caught <= 1;

    // 4. Test Sequence
    initial begin
        $dumpfile("precession_trace.vcd");
        $dumpvars(0, spu4_precession_tb);
        
        clk = 0;
        rst_n = 0;
        whisper_caught = 0;
        #100;
        rst_n = 1;
        
        $display("--- SPU-4 Precession Test Start ---");
        
        // Let it run for 4000 cycles (80ns * 4000 = 320,000 ns)
        #320000;
        
        $display("R0 State Final: %h", debug_reg_r0);
        $display("Snap Alert (Latch): %b, Whisper Tx (Latch): %b", snap_alert, whisper_caught);
        
        if (whisper_caught) begin
            $display("PASS: Precession Kernel completed Whisper broadcast.");
        end else begin
            $display("FAIL: Precession Kernel did not reach Whisper Tx.");
        end
        
        $finish;
    end

endmodule
