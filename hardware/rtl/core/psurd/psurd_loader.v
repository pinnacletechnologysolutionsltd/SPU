// psurd_loader.v — v0.3 RTL-0B SPUI loader (frozen contract §10; RTL-0B plan §2 corrections A, B).
// Commands (from psurd_link, payload byte i = payload[8*i +: 8]):
//   1 LOAD_BEGIN  the 12-byte SPUI header: checks magic, profile 0x01, revision 0x03, 1 <= L <= 256 in that
//                 order; clears image-valid whether accepted or refused; opens a load transaction if accepted.
//   2 LOAD_WORD   index (u16 LE) + word (8 bytes, big-endian as in SPUI): only the next expected index is
//                 accepted; the word enters the streaming CRC-32/ISO-HDLC (bit-serial, 64 cycles) and is then
//                 written through a REGISTERED imem write port (plan B5: hold margin at the imem inputs).
//   3 LOAD_END    the only commit point: word count = L and CRC match set image-valid = 1 atomically.
// Any refusal of a load command aborts the open transaction and leaves image-valid = 0. A LOAD_WORD or
// LOAD_END with no transaction open is a refused load and also clears image-valid (fail-safe reading of §10).
// xerr (a malformed frame, from the link) aborts an open transaction and changes nothing else.
// While busy (run in flight or record finalizing) every load command answers BUSY with no state change.
// Reason byte of a REFUSED response: 1 framing, 2 identity, 3 length, 4 CRC, 5 order, 6 count, 7 no load open.
module psurd_loader (
    input  wire clk, rst,
    input  wire cmd_valid,
    input  wire [2:0] cmd,
    input  wire [95:0] payload,
    input  wire busy, xerr,
    output reg  image_valid, load_open,
    output reg  [8:0] img_len,                  // L of the last accepted header
    output reg  imem_we,
    output reg  [7:0] imem_waddr,
    output reg  [63:0] imem_wdata,
    output reg  rsp_valid,                      // one cycle; status and reason hold until the next response
    output reg  [7:0] rsp_status, rsp_reason
);
    localparam OK = 8'h00, REFUSED = 8'h20, BUSY = 8'h22;
    reg [8:0] cnt;                              // next expected word index, 0..L
    reg [31:0] crc, crc_exp;
    reg [63:0] sr;                              // word in file byte order, byte 0 bit 0 first (reflected CRC)
    reg [6:0] bits;                             // CRC bits left for the word in flight; 0 = idle
    wire [15:0] hdr_len = payload[63:48];
    wire [2:0] hdr_bad = payload[31:0] != 32'h49555053 ? 3'd1 :            // "SPUI"
                         payload[47:32] != 16'h0301 ? 3'd2 :                 // profile 01, revision 03
                         (hdr_len == 16'd0 || hdr_len > 16'd256) ? 3'd3 : 3'd0;
    wire [63:0] word;
    genvar g;
    generate for (g = 0; g < 8; g = g + 1) begin : be
        assign word[8 * (7 - g) +: 8] = payload[16 + 8 * g +: 8];
    end endgenerate
    wire fb = crc[0] ^ sr[0];
    task answer(input [7:0] s, input [7:0] r); begin rsp_valid <= 1'b1; rsp_status <= s; rsp_reason <= r; end endtask
    task refuse(input [7:0] r); begin answer(REFUSED, r); image_valid <= 1'b0; load_open <= 1'b0; end endtask
    always @(posedge clk) begin
        rsp_valid <= 1'b0; imem_we <= 1'b0;
        if (rst) begin
            image_valid <= 1'b0; load_open <= 1'b0; img_len <= 9'd1; cnt <= 9'd0; bits <= 7'd0;
            rsp_status <= OK; rsp_reason <= 8'd0;
        end else if (bits != 7'd0) begin                                    // CRC over the accepted word
            crc <= {1'b0, crc[31:1]} ^ (fb ? 32'hEDB88320 : 32'd0);
            sr <= {1'b0, sr[63:1]}; bits <= bits - 7'd1;
            if (bits == 7'd1) begin imem_we <= 1'b1; cnt <= cnt + 9'd1; answer(OK, 8'd0); end
        end else if (xerr) load_open <= 1'b0;
        else if (cmd_valid && cmd >= 3'd1 && cmd <= 3'd3) begin
            if (busy) answer(BUSY, 8'd0);
            else case (cmd)
                3'd1: if (hdr_bad != 3'd0) refuse({5'd0, hdr_bad});
                      else begin
                          image_valid <= 1'b0; load_open <= 1'b1; cnt <= 9'd0; img_len <= hdr_len[8:0];
                          crc_exp <= payload[95:64]; crc <= 32'hFFFFFFFF; answer(OK, 8'd0);
                      end
                3'd2: if (!load_open) refuse(8'd7);
                      else if (payload[15:0] != {7'd0, cnt} || cnt == img_len) refuse(8'd5);
                      else begin
                          sr <= payload[79:16]; bits <= 7'd64;
                          imem_waddr <= cnt[7:0]; imem_wdata <= word;
                      end
                default: if (!load_open) refuse(8'd7);
                         else if (cnt != img_len) refuse(8'd6);
                         else if (~crc != crc_exp) refuse(8'd4);
                         else begin image_valid <= 1'b1; load_open <= 1'b0; answer(OK, 8'd0); end
            endcase
        end
    end
endmodule
