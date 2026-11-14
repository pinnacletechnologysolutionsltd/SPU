// psurd_record.v — v0.3 RTL-0B result-record builder (frozen contract §11; RTL-0B plan D4, D5, correction C).
// On go (the core has finished; it stays idle with done = 1) it reads the eight registers through the core's
// dump port (bank read port A), then writes the 213 record bytes to a byte memory in order:
//   0 A5, 1 version 03, 2 profile 01, 3 cause, 4-5 PC, 6 flags, 7 status, 8-11 retired, 12-15 budget,
//   16 initialized mask, 17-208 S0..S7 as a, b, d (little-endian; an uninitialized register is 24 zero bytes,
//   whatever its storage holds), 209-212 CRC-32/ISO-HDLC over bytes 0-208 (little-endian).
// done pulses once after the last CRC byte is stored; psurd_runctl publishes record-valid from it, so a
// record is never visible half-written. The memory read is synchronous (one cycle after raddr).
module psurd_record (
    input  wire clk, rst, go,
    input  wire [2:0] cause,
    input  wire [8:0] pc,
    input  wire [5:0] flags,                    // {RS, R, CV, P, N, Z}
    input  wire [1:0] status,
    input  wire [31:0] retired, budget,
    output wire [2:0] dump_ra,
    input  wire [191:0] dump_q,
    input  wire dump_valid,
    output reg  done,
    input  wire [7:0] raddr,
    output reg  [7:0] rdata
);
    localparam S_IDLE = 2'd0, S_MASK = 2'd1, S_BODY = 2'd2, S_CRC = 2'd3;
    reg [1:0] state;
    reg [7:0] idx, mask;                        // idx: record byte being written
    reg [2:0] r;                                // register being read
    reg [4:0] j;                                // byte within the register, 0..23
    reg [31:0] crc;
    reg [7:0] mem [0:255];
    wire [135:0] head = {mask, budget, retired, 6'd0, status, 2'd0, flags, 7'd0, pc, 5'd0, cause, 24'h0103A5};
    wire [7:0] body = idx < 8'd17 ? head[8 * idx[4:0] +: 8] : (mask[r] ? dump_q[8 * j +: 8] : 8'd0);
    wire [31:0] crc_out = ~crc;
    wire [1:0] ck = idx[1:0] - 2'd1;            // idx 209..212 -> CRC bytes 0..3
    wire [7:0] wbyte = state == S_CRC ? crc_out[8 * ck +: 8] : body;
    function [31:0] crc8(input [31:0] c, input [7:0] d);
        integer k; reg [31:0] t;
        begin
            t = c ^ {24'd0, d};
            for (k = 0; k < 8; k = k + 1) t = {1'b0, t[31:1]} ^ (t[0] ? 32'hEDB88320 : 32'd0);
            crc8 = t;
        end
    endfunction
    assign dump_ra = r;
    always @(posedge clk) begin
        rdata <= mem[raddr];
        if (state == S_BODY || state == S_CRC) mem[idx] <= wbyte;
    end
    always @(posedge clk) begin
        done <= 1'b0;
        if (rst) state <= S_IDLE;
        else case (state)
            S_IDLE: if (go) begin state <= S_MASK; r <= 3'd0; end
            S_MASK: begin                                               // collect the initialized mask first (byte 16)
                mask[r] <= dump_valid; r <= r + 3'd1;
                if (r == 3'd7) begin state <= S_BODY; idx <= 8'd0; j <= 5'd0; crc <= 32'hFFFFFFFF; end
            end
            S_BODY: begin
                crc <= crc8(crc, wbyte); idx <= idx + 8'd1;
                if (idx >= 8'd17) begin
                    if (j == 5'd23) begin j <= 5'd0; r <= r + 3'd1; end else j <= j + 5'd1;
                end
                if (idx == 8'd208) state <= S_CRC;
            end
            default: begin
                idx <= idx + 8'd1;
                if (idx == 8'd212) begin state <= S_IDLE; done <= 1'b1; end
            end
        endcase
    end
endmodule
