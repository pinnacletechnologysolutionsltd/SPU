// psurd_board_top.v — v0.3 RTL-0C board top for the QMTECH Wukong XC7A100T (plan SPU_V03_RTL0C_PLAN.md, D1-D3).
// Wraps the unchanged psurd_sys_top (25 MHz, 115200 baud, default parameters; no override here).
// Clock and reset conditioning follow spu_a7_surd_cpu_base_top.v:
//  - 50 MHz sys_clk; the raw rst_n pad (KEY0, active low, PULLUP) feeds ONLY rst_sync[0];
//  - a 255-cycle release counter in the 50 MHz domain gives rst_n_int;
//  - cpu_clk is a divide-by-two fabric flop (held low while rst_n_int is low) through a BUFG;
//  - an asynchronous-assert, synchronous-release pair in the 25 MHz domain gives cpu_rst_n;
//  - psurd_sys_top takes the active-high level !cpu_rst_n: it is asserted for the first two cpu_clk
//    edges after every release, which is what its synchronous resets need.
// Pins: sys_clk M21, rst_n H7, uart_rx F3, uart_tx E3. No LEDs; the status outputs are unconnected.
// No silicon evidence exists for this file (RTL-0C gates C2-C4 are simulation and tool reports).
module psurd_board_top (
    input  wire sys_clk,     // M21, 50 MHz oscillator
    input  wire rst_n,       // H7, KEY0, active low, raw pad
    input  wire uart_rx,     // F3, host -> FPGA
    output wire uart_tx      // E3, FPGA -> host
);
    // ---- 50 MHz domain: input conditioning ----
    (* ASYNC_REG = "TRUE" *) reg [1:0] rst_sync = 2'b00;
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
    psurd_sys_top u_sys (.clk(cpu_clk), .rst(!cpu_rst_n), .uart_rx(uart_rx), .uart_tx(uart_tx),
        .busy(), .image_valid(), .record_valid());
endmodule
