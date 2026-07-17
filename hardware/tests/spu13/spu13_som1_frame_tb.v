`timescale 1ns / 1ps

module spu13_som1_frame_tb;
    reg clk = 0;
    reg rst_n = 0;
    reg build = 0;
    wire [415:0] frame;
    wire ready;
    wire busy;
    integer failures = 0;

    always #5 clk = ~clk;

    spu13_som1_frame dut (
        .clk(clk), .rst_n(rst_n), .build(build),
        .result_valid(1'b1), .result_busy(1'b0),
        .has_second(1'b1), .ambiguous(1'b1), .map_valid(1'b1),
        .error_code(8'd0), .map_generation(32'h01020304),
        .result_generation(32'h05060708),
        .best_node(16'h0004), .second_node(16'h0002),
        .label(16'h0001),
        .best_q(64'h1122334455667788),
        .second_q(64'h99AABBCCDDEEFF00),
        .confidence_gap(64'h0123456789ABCDEF),
        .frame(frame), .frame_ready(ready), .encoder_busy(busy)
    );

    function [31:0] crc32_byte;
        input [31:0] crc;
        input [7:0] byte_data;
        reg [31:0] s;
        integer b;
        begin
            s = crc ^ byte_data;
            for (b = 0; b < 8; b = b + 1)
                s = s[0] ? ((s >> 1) ^ 32'hEDB88320) : (s >> 1);
            crc32_byte = s;
        end
    endfunction

    function [31:0] payload_crc;
        input [415:0] value;
        reg [31:0] crc;
        integer i;
        begin
            crc = 32'hFFFFFFFF;
            for (i = 0; i < 48; i = i + 1)
                crc = crc32_byte(crc, value[(51-i)*8 +: 8]);
            payload_crc = ~crc;
        end
    endfunction

    task check;
        input condition;
        input [255:0] description;
        begin
            if (!condition) begin
                $display("FAIL: %0s", description);
                failures = failures + 1;
            end else
                $display("PASS: %0s", description);
        end
    endtask

    initial begin
        repeat (3) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
        build = 1;
        @(posedge clk);
        build = 0;
        wait (ready);

        check(frame[415:384] == 32'h534F4D31, "magic");
        check(frame[383:376] == 8'd1, "version");
        check(frame[375:368] == 8'd52, "declared length");
        check(frame[367:360] == 8'h1D, "flags");
        check(frame[359:352] == 8'd0, "error");
        check(frame[351:320] == 32'h01020304, "map generation");
        check(frame[319:288] == 32'h05060708, "result generation");
        check(frame[287:272] == 16'h0004, "winner");
        check(frame[271:256] == 16'h0002, "runner-up");
        check(frame[255:240] == 16'h0001, "label");
        check(frame[239:224] == 16'd0, "reserved zero");
        check(frame[223:160] == 64'h1122334455667788, "best quadrance");
        check(frame[159:96] == 64'h99AABBCCDDEEFF00, "second quadrance");
        check(frame[95:32] == 64'h0123456789ABCDEF, "gap");
        check(frame[31:0] == payload_crc(frame), "CRC-32");

        if (failures == 0)
            $display("PASS: SOM1 frame encoder");
        else
            $display("FAIL: SOM1 frame encoder failures=%0d", failures);
        $finish;
    end
endmodule
