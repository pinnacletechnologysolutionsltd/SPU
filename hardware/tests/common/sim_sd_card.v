// sim_sd_card.v — behavioral SD card model for SPI-mode used in testbench
`timescale 1ns / 1ps

module sim_sd_card(
    input  wire sd_cs,
    input  wire sd_sck,
    input  wire sd_mosi,
    output reg  sd_miso
);

// Incoming command assembly
reg [7:0] in_shift;
reg [2:0] in_bit_cnt;
reg [7:0] cmd_bytes [0:5];
integer cmd_byte_idx;

// Outgoing response queue
reg [7:0] resp_queue [0:2047];
integer resp_head;
integer resp_len;
reg [7:0] out_shift;
reg [2:0] out_bit_cnt;

integer i;
reg [31:0] last_cmd_arg;
reg [5:0] cmd_idx;
reg [31:0] arg;

initial begin
    sd_miso = 1'b1;
    in_shift = 8'h00;
    in_bit_cnt = 3'd0;
    cmd_byte_idx = 0;
    resp_head = 0;
    resp_len = 0;
    out_shift = 8'hFF;
    out_bit_cnt = 3'd0;
    last_cmd_arg = 32'd0;
end

// Sample MOSI on rising edge of SPI clock
always @(posedge sd_sck) begin
    if (sd_cs) begin
        in_bit_cnt <= 3'd0;
        cmd_byte_idx <= 0;
    end else begin
        in_shift <= {in_shift[6:0], sd_mosi};
        if (in_bit_cnt == 3'd7) begin
            // full byte received
            cmd_bytes[cmd_byte_idx] <= {in_shift[6:0], sd_mosi};
            cmd_byte_idx <= cmd_byte_idx + 1;
            in_bit_cnt <= 3'd0;
            if (cmd_byte_idx == 5) begin
                // received 6 bytes (cmd frame)
                // decode command
                cmd_idx = cmd_bytes[0] & 6'h3F;
                arg = {cmd_bytes[1], cmd_bytes[2], cmd_bytes[3], cmd_bytes[4]};
                last_cmd_arg = arg;
                // Prepare response depending on command
                if (cmd_idx == 6'd0) begin
                    // CMD0 -> R1 = 0x01 (idle)
                    resp_head = 0;
                    resp_len = 2;
                    resp_queue[0] = 8'hFF; // preamble
                    resp_queue[1] = 8'h01;
                end else if (cmd_idx == 6'd17) begin
                    // CMD17 -> R1 = 0x00, then after some 0xFF filler, token 0xFE and 512 bytes + 2 CRC
                    resp_head = 0;
                    // build queue: [0xFF, 0x00, 0xFF, 0xFE, data(512), crc1, crc2]
                    // data pattern: low byte of block address + index
                    resp_len = 4 + 512 + 2; // preamble(0xFF), R1, filler(0xFF), token + data + crc
                    resp_queue[0] = 8'hFF;
                    resp_queue[1] = 8'h00; // R1
                    resp_queue[2] = 8'hFF; // filler
                    resp_queue[3] = 8'hFE; // data token
                    // populate 512 data bytes
                    for (i = 0; i < 512; i = i + 1) begin
                        resp_queue[4 + i] = last_cmd_arg[7:0] + (i & 8'hFF);
                    end
                    resp_queue[4 + 512] = 8'h00; // CRC1 (ignored)
                    resp_queue[4 + 512 + 1] = 8'h00; // CRC2
                end else begin
                    // Default: no response (keep sending 0xFF)
                    resp_head = 0;
                    resp_len = 0;
                end
                // reset command accumulation
                cmd_byte_idx <= 0;
            end
        end else begin
            in_bit_cnt <= in_bit_cnt + 1;
        end
    end
end

// Drive MISO on falling edge of SPI clock
always @(negedge sd_sck) begin
    if (sd_cs) begin
        sd_miso <= 1'b1;
        out_bit_cnt <= 3'd0;
    end else begin
        // load next byte into out_shift when starting a new byte
        if (out_bit_cnt == 3'd0) begin
            if (resp_head < resp_len) begin
                out_shift <= resp_queue[resp_head];
            end else begin
                out_shift <= 8'hFF;
            end
        end
        // output MSB first
        sd_miso <= out_shift[7 - out_bit_cnt];
        out_bit_cnt <= out_bit_cnt + 1;
        if (out_bit_cnt == 3'd7) begin
            // finished a byte, advance head
            if (resp_head < resp_len) resp_head <= resp_head + 1;
            out_bit_cnt <= 3'd0;
        end
    end
end

endmodule
