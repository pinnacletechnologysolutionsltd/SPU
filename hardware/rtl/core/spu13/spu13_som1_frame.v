`timescale 1ns / 1ps

// spu13_som1_frame.v -- Versioned SOM decision-evidence frame encoder.
//
// The 48-byte payload is snapshotted on build and protected by an IEEE
// CRC-32 appended in big-endian order.  CRC work is byte-serial (48 clocks),
// keeping the encoder small and making the published frame stable while SPI
// shifts it out.
module spu13_som1_frame (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         build,
    input  wire         result_valid,
    input  wire         result_busy,
    input  wire         has_second,
    input  wire         ambiguous,
    input  wire         map_valid,
    input  wire [7:0]   error_code,
    input  wire [31:0]  map_generation,
    input  wire [31:0]  result_generation,
    input  wire [15:0]  best_node,
    input  wire [15:0]  second_node,
    input  wire [15:0]  label,
    input  wire [63:0]  best_q,
    input  wire [63:0]  second_q,
    input  wire [63:0]  confidence_gap,
    output reg  [415:0] frame,
    output reg          frame_ready,
    output reg          encoder_busy
);

    localparam [7:0] SOM1_VERSION = 8'd1;
    localparam [7:0] SOM1_LENGTH  = 8'd52;

    wire [7:0] flags = {
        3'b000, map_valid, ambiguous, has_second, result_busy, result_valid
    };

    reg [383:0] payload;
    reg [31:0]  crc_work;
    reg [5:0]   byte_index;

    function [31:0] crc32_byte;
        input [31:0] crc;
        input [7:0] byte_data;
        reg [31:0] s;
        integer bit_index;
        begin
            s = crc ^ byte_data;
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1)
                s = s[0] ? ((s >> 1) ^ 32'hEDB88320) : (s >> 1);
            crc32_byte = s;
        end
    endfunction

    function [7:0] payload_byte;
        input [383:0] value;
        input [5:0] index;
        begin
            payload_byte = value[(47 - index) * 8 +: 8];
        end
    endfunction

    wire [31:0] crc_next = crc32_byte(
        crc_work, payload_byte(payload, byte_index)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            payload <= 384'd0;
            crc_work <= 32'hFFFFFFFF;
            byte_index <= 6'd0;
            frame <= 416'd0;
            frame_ready <= 1'b0;
            encoder_busy <= 1'b0;
        end else begin
            if (build && !encoder_busy) begin
                payload <= {
                    32'h534F4D31,       // ASCII "SOM1"
                    SOM1_VERSION,
                    SOM1_LENGTH,
                    flags,
                    error_code,
                    map_generation,
                    result_generation,
                    best_node,
                    second_node,
                    label,
                    16'd0,              // reserved, must remain zero
                    best_q,
                    second_q,
                    confidence_gap
                };
                crc_work <= 32'hFFFFFFFF;
                byte_index <= 6'd0;
                frame_ready <= 1'b0;
                encoder_busy <= 1'b1;
            end else if (encoder_busy) begin
                crc_work <= crc_next;
                if (byte_index == 6'd47) begin
                    frame <= {payload, ~crc_next};
                    frame_ready <= 1'b1;
                    encoder_busy <= 1'b0;
                end else begin
                    byte_index <= byte_index + 1'b1;
                end
            end
        end
    end

endmodule
