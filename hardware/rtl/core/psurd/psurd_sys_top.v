// psurd_sys_top.v — v0.3 RTL-0B system: UART host link + SPUI loader + run control + record builder + psurd_core.
// One clock domain (plan D3), synchronous active-high reset. Not a board top: no pins, PLL or reset
// conditioning (RTL-0C). Protocol H0-UART-1B v2 (plan §3); every command and the RESULT transmission go
// through the single psurd_link FSM, so image, run state and record cannot change while a response is sent.
// Response payload: the 213-byte record for an accepted RESULT, the 7 STATUS bytes, or the reason byte of a
// REFUSED response. BUSY, BAD_FRAME, TIMEOUT and plain OK carry no payload.
module psurd_sys_top #(
    parameter CLK_HZ  = 25000000,
    parameter BAUD    = 115200,
    parameter TIMEOUT = 17360                   // psurd_link inter-byte limit, cycles (8 byte-times)
) (
    input  wire clk, rst,
    input  wire uart_rx,
    output wire uart_tx,
    output wire busy, image_valid, record_valid
);
    wire [7:0] rx_data, tx_data, rsp_addr, rec_byte, l_status, l_reason, r_status, r_reason, r_len;
    wire rx_valid, rx_err, tx_send, tx_done, tx_busy, cmd_valid, xerr, l_rsp, r_rsp, load_open;
    wire [2:0] cmd, cause, dump_ra;
    wire [95:0] payload;
    wire [8:0] img_len, pc;
    wire imem_we, core_start, core_done, rec_go, rec_done, dump_valid, Z, N, P, CV, R, RS;
    wire [7:0] imem_waddr;
    wire [63:0] imem_wdata;
    wire [31:0] budget, retired;
    wire [1:0] status;
    wire [191:0] dump_q;
    wire [55:0] status_bytes;
    psurd_uart_rx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) urx (.clk(clk), .rst_n(!rst), .rx(uart_rx),
        .data(rx_data), .valid(rx_valid), .frame_err(rx_err));
    spu_uart_tx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) utx (.clk(clk), .rst_n(!rst), .data(tx_data), .send(tx_send),
        .tx(uart_tx), .busy(tx_busy), .done(tx_done));
    wire sel_record = cmd == 3'd6 && r_status == 8'h00;
    wire [7:0] rsp_data = sel_record ? rec_byte :
                          cmd == 3'd5 ? status_bytes[8 * rsp_addr[2:0] +: 8] :
                          cmd <= 3'd3 ? l_reason : r_reason;
    psurd_link #(.TIMEOUT(TIMEOUT)) link (.clk(clk), .rst(rst), .rx_data(rx_data), .rx_valid(rx_valid),
        .rx_err(rx_err), .tx_data(tx_data), .tx_send(tx_send), .tx_done(tx_done), .cmd_valid(cmd_valid),
        .cmd(cmd), .payload(payload), .rsp_valid(l_rsp || r_rsp), .rsp_status(l_rsp ? l_status : r_status),
        .rsp_len(l_rsp ? {7'd0, l_status == 8'h20} : r_len), .rsp_addr(rsp_addr), .rsp_data(rsp_data), .xerr(xerr));
    psurd_loader loader (.clk(clk), .rst(rst), .cmd_valid(cmd_valid), .cmd(cmd), .payload(payload), .busy(busy),
        .xerr(xerr), .image_valid(image_valid), .load_open(load_open), .img_len(img_len), .imem_we(imem_we),
        .imem_waddr(imem_waddr), .imem_wdata(imem_wdata), .rsp_valid(l_rsp), .rsp_status(l_status),
        .rsp_reason(l_reason));
    psurd_runctl runctl (.clk(clk), .rst(rst), .cmd_valid(cmd_valid), .cmd(cmd), .budget_in(payload[31:0]),
        .image_valid(image_valid), .load_open(load_open), .core_done(core_done), .core_cause(cause),
        .rec_done(rec_done), .busy(busy), .record_valid(record_valid), .core_start(core_start), .budget(budget),
        .rec_go(rec_go), .status_bytes(status_bytes), .rsp_valid(r_rsp), .rsp_status(r_status),
        .rsp_reason(r_reason), .rsp_len(r_len));
    psurd_core core (.clk(clk), .rst(rst), .start(core_start), .budget(budget), .img_len(img_len),
        .imem_we(imem_we), .imem_waddr(imem_waddr), .imem_wdata(imem_wdata), .dump_ra(dump_ra), .dump_q(dump_q),
        .dump_valid(dump_valid), .done(core_done), .cause(cause), .pc(pc), .retired(retired),
        .Z(Z), .N(N), .P(P), .CV(CV), .R(R), .RS(RS), .status(status));
    psurd_record record (.clk(clk), .rst(rst), .go(rec_go), .cause(cause), .pc(pc), .flags({RS, R, CV, P, N, Z}),
        .status(status), .retired(retired), .budget(budget), .dump_ra(dump_ra), .dump_q(dump_q),
        .dump_valid(dump_valid), .done(rec_done), .raddr(rsp_addr), .rdata(rec_byte));
endmodule
