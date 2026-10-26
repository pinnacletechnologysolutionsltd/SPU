// Wukong XC7A100T Base SPU CPU top (CPU-BASE-TOP-1, contract A1). ENABLE_REGEN=0.
// 50 MHz board clock in; the CPU and its synthetic workload run at 25 MHz (cpu_clk).
// uart_tx is NOT UART data: it carries checksum_parity_out, the parity of the workload's
// rotating checksum (pin E3 kept for continuity). Clock/reset topology follows the
// silicon-proven spu_a7_tensegrity_link_top.v, plus a 25 MHz release synchronizer that
// has NO silicon evidence yet. Rules: the raw rst_n pad feeds only rst_sync[0]; BUFG
// inputs are fabric flop outputs, never another BUFG.
module spu_a7_surd_cpu_base_top (
    input  wire sys_clk,     // M21, 50 MHz oscillator
    input  wire rst_n,       // H7, PULLUP, raw pad
    output wire uart_tx      // E3, checksum_parity_out
);
    // ---- 50 MHz domain: input conditioning (as proven) ----
    reg [1:0] rst_sync  = 2'b00;
    reg [7:0] rst_count = 8'd0;
    wire rst_n_int = (rst_count == 8'hff);
    always @(posedge sys_clk) begin
        rst_sync <= {rst_sync[0], rst_n};
        if (!rst_sync[1])
            rst_count <= 8'd0;
        else if (!rst_n_int)
            rst_count <= rst_count + 1'b1;
    end

    // ---- divide-by-two CPU clock; held low while reset is asserted ----
    reg cpu_clk_div = 1'b0;
    always @(posedge sys_clk) begin
        if (!rst_n_int)
            cpu_clk_div <= 1'b0;
        else
            cpu_clk_div <= ~cpu_clk_div;
    end
    wire cpu_clk;
`ifdef SYNTHESIS
    BUFG u_cpu_clk_buf (.I(cpu_clk_div), .O(cpu_clk));
`else
    assign cpu_clk = cpu_clk_div;
`endif

    // ---- 25 MHz domain: asynchronous assert, synchronous release (2 stages) ----
    reg [1:0] cpu_rst_sync = 2'b00;
    always @(posedge cpu_clk or negedge rst_n_int) begin
        if (!rst_n_int)
            cpu_rst_sync <= 2'b00;
        else
            cpu_rst_sync <= {cpu_rst_sync[0], 1'b1};
    end
    wire cpu_rst_n = cpu_rst_sync[1];

    // ---- Base CPU workload: REGEN explicitly disabled in this file ----
    wire checksum_parity_out;
    spu_a7_surd_cpu_bench_top #(.ENABLE_SURD_CPU(1), .ENABLE_REGEN(0)) u_workload (
        .sys_clk(cpu_clk), .rst_n(cpu_rst_n), .uart_tx(checksum_parity_out));
    assign uart_tx = checksum_parity_out;
endmodule
