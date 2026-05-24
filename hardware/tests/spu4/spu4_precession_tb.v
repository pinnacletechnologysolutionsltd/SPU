`timescale 1ns/1ps

module spu4_precession_tb;

    reg clk;
    reg rst_n;
    wire [23:0] inst_data;
    wire [9:0] pc;
    wire snap_alert;
    wire whisper_tx;
    wire [1:0] state_out;
    wire [63:0] debug_reg_r0;

    // 1. Program Memory (BRAM Simulation)
    reg [23:0] prog_mem [0:1023];
    integer i;
    initial begin
        for (i = 0; i < 1024; i = i + 1) prog_mem[i] = 24'h0;
        $readmemh("hardware/tests/spu4/precession.hex", prog_mem);
    end
    assign inst_data = (pc < 1024) ? prog_mem[pc] : 24'h0;

    // 2. Unit Under Test
    spu4_top #(
        .ENABLE_RPLU_BRAM(0)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .rplu_cfg_wr_en(1'b0),
        .rplu_cfg_sel(3'd0),
        .rplu_cfg_material(1'b0),
        .rplu_cfg_addr(10'd0),
        .rplu_cfg_data(64'd0),
        .inst_data(inst_data),
        .pc(pc),
        .sentinel_mode(1'b0),
        .piranha_pulse(1'b0),
        .bank_sel(1'b0),
        .snap_alert(snap_alert),
        .whisper_tx(whisper_tx),
        .state_out(state_out),
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
