// psurd_link.v — v0.3 RTL-0B host link: H0-UART-1B v2 frame parser and response builder (plan §3).
// Request:  A5 02 cmd len_lo len_hi payload checksum      (checksum = XOR of every preceding byte)
// Response: A5 02 (cmd|80) status len_lo len_hi payload checksum
// Stop-and-wait: one FSM parses, waits for the backend and transmits, so bytes arriving while a request
// is pending or a response is being sent are ignored. A command is issued (cmd_valid, one cycle) only
// after the whole frame and its checksum have passed. Payload byte i is payload[8*i +: 8].
// Transport errors (response has no payload; xerr pulses once so an open load can be aborted):
//  - wrong version, unknown command or a length that is not the command's length: the declared payload
//    (clamped to 12) and the checksum are drained, then BAD_FRAME;
//  - checksum mismatch: BAD_FRAME;
//  - more than TIMEOUT cycles between two bytes of a frame: TIMEOUT (BAD_FRAME if already draining);
//  - UART framing error inside a frame: input is discarded until RX is quiet for TIMEOUT, then BAD_FRAME.
// Outside a frame, bytes other than A5 and framing errors are ignored. An error before the command byte
// is answered with command 80.
module psurd_link #(
    parameter TIMEOUT = 17360                   // inter-byte limit in cycles: 8 byte-times at 217 cycles/bit
) (
    input  wire clk, rst,
    input  wire [7:0] rx_data,
    input  wire rx_valid, rx_err,
    output reg  [7:0] tx_data,
    output wire tx_send,
    input  wire tx_done,
    output reg  cmd_valid,
    output wire [2:0] cmd,
    output reg  [95:0] payload,
    input  wire rsp_valid,                      // one cycle, with rsp_status and rsp_len (0..213)
    input  wire [7:0] rsp_status, rsp_len,
    output wire [7:0] rsp_addr,                 // response payload byte index
    input  wire [7:0] rsp_data,                 // valid one cycle after rsp_addr (or combinational)
    output reg  xerr
);
    localparam ST_BAD_FRAME = 8'h01, ST_TIMEOUT = 8'h04;
    localparam S_IDLE = 4'd0, S_HDR = 4'd1, S_PAY = 4'd2, S_CSUM = 4'd3, S_DRAIN = 4'd4, S_QUIET = 4'd5,
               S_EXEC = 4'd6, S_TPREP = 4'd7, S_TLOAD = 4'd8, S_TWAIT = 4'd9;
    reg [3:0] state, n;
    reg [7:0] cmdb, len_lo, x, st, rl, ti, xs;
    reg [15:0] tcnt;
    reg ver_ok;
    reg [3:0] exp;                              // payload length of the received command; 15 = unknown command
    always @* case (cmdb)
        8'd1: exp = 4'd12;  8'd2: exp = 4'd10;  8'd4: exp = 4'd4;
        8'd3, 8'd5, 8'd6: exp = 4'd0;
        default: exp = 4'd15;
    endcase
    wire [15:0] len = {rx_data, len_lo};        // valid while the fifth header byte is on rx_data
    wire [8:0] last = {1'b0, rl} + 9'd6;        // index of the response checksum
    wire expired = tcnt == TIMEOUT - 1;
    assign cmd = cmdb[2:0];
    assign rsp_addr = ti - 8'd6;
    assign tx_send = state == S_TLOAD;
    always @* case (1'b1)
        ti == 8'd0: tx_data = 8'hA5;
        ti == 8'd1: tx_data = 8'h02;
        ti == 8'd2: tx_data = cmdb | 8'h80;
        ti == 8'd3: tx_data = st;
        ti == 8'd4: tx_data = rl;
        ti == 8'd5: tx_data = 8'h00;
        {1'b0, ti} == last: tx_data = xs;
        default: tx_data = rsp_data;
    endcase
    task respond(input [7:0] s, input [7:0] l); begin st <= s; rl <= l; ti <= 8'd0; xs <= 8'd0; state <= S_TPREP; end endtask
    task fail(input [7:0] s); begin xerr <= 1'b1; respond(s, 8'd0); end endtask
    always @(posedge clk) begin
        cmd_valid <= 1'b0; xerr <= 1'b0;
        tcnt <= (rx_valid || rx_err) ? 16'd0 : tcnt + 16'd1;
        if (rst) begin state <= S_IDLE; cmdb <= 8'd0; end
        else case (state)
            S_IDLE: if (rx_valid && rx_data == 8'hA5) begin
                        state <= S_HDR; n <= 4'd1; x <= 8'hA5; cmdb <= 8'd0;
                    end
            S_HDR: if (rx_err) state <= S_QUIET;
                   else if (rx_valid) begin
                       x <= x ^ rx_data; n <= n + 4'd1;
                       case (n)
                           4'd1: ver_ok <= rx_data == 8'h02;
                           4'd2: cmdb <= rx_data;
                           4'd3: len_lo <= rx_data;
                           default: begin
                               n <= 4'd0;
                               if (ver_ok && exp != 4'd15 && len == {12'd0, exp}) state <= exp == 4'd0 ? S_CSUM : S_PAY;
                               else begin state <= S_DRAIN; n <= len > 16'd12 ? 4'd12 : len[3:0]; end
                           end
                       endcase
                   end else if (expired) fail(ST_TIMEOUT);
            S_PAY: if (rx_err) state <= S_QUIET;
                   else if (rx_valid) begin
                       x <= x ^ rx_data; payload[8 * n +: 8] <= rx_data; n <= n + 4'd1;
                       if (n == exp - 4'd1) state <= S_CSUM;
                   end else if (expired) fail(ST_TIMEOUT);
            S_CSUM: if (rx_err) state <= S_QUIET;
                    else if (rx_valid) begin
                        if (x == rx_data) begin cmd_valid <= 1'b1; state <= S_EXEC; end
                        else fail(ST_BAD_FRAME);
                    end else if (expired) fail(ST_TIMEOUT);
            S_DRAIN: if (rx_err) state <= S_QUIET;              // n payload bytes, then the checksum
                     else if (rx_valid) begin
                         n <= n - 4'd1;
                         if (n == 4'd0) fail(ST_BAD_FRAME);
                     end else if (expired) fail(ST_BAD_FRAME);
            S_QUIET: if (expired && !rx_valid && !rx_err) fail(ST_BAD_FRAME);
            S_EXEC: if (rsp_valid) respond(rsp_status, rsp_len);
            S_TPREP: state <= S_TLOAD;                          // rsp_addr settles; synchronous payload read
            S_TLOAD: begin xs <= xs ^ tx_data; state <= S_TWAIT; end
            S_TWAIT: if (tx_done) begin
                         ti <= ti + 8'd1;
                         state <= {1'b0, ti} == last ? S_IDLE : S_TPREP;
                     end
            default: state <= S_IDLE;
        endcase
    end
endmodule
