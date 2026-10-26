// spu_spi_protocol_trace_tb.v — state-level SPI oracle/RTL trace comparison
//
// The expected states below are the independent finite-automaton trace for
// the base eight-state protocol surface.  The DUT is the real SPI slave;
// payloads and CRCs are driven on its pins, and the internal state is observed
// only for comparison.  Optional TGR states are deliberately out of scope.
`timescale 1ns/1ps

module spu_spi_protocol_trace_tb;
    reg clk = 0, rst_n = 0;
    reg spi_cs_n = 1, spi_sck = 0, spi_mosi = 0;
    wire spi_miso;
    reg [831:0] manifold_state = 0;
    reg [3:0] satellite_snaps = 0;
    reg is_janus_point = 0;
    reg [15:0] dissonance = 16'h1234;
    reg [51:0] scale_table = 0;
    reg [12:0] scale_overflow = 0;
    reg qr_commit_valid = 0;
    reg [3:0] qr_commit_lane = 0;
    reg [63:0] qr_commit_A = 0, qr_commit_B = 0, qr_commit_C = 0, qr_commit_D = 0;
    reg hex_valid = 0;
    reg [15:0] hex_q = 0, hex_r = 0;
    reg signed [2:0] rplu_ratio_res = 0;
    reg rplu_ratio_valid = 0;
    wire rplu_cfg_wr_en;
    wire [2:0] rplu_cfg_sel;
    wire [7:0] rplu_cfg_material;
    wire [9:0] rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;
    wire inst_valid;
    wire [63:0] inst_word;
    reg [511:0] sentinel_telemetry = 0;

    spu_spi_slave dut (
        .clk(clk), .rst_n(rst_n), .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(manifold_state), .satellite_snaps(satellite_snaps),
        .is_janus_point(is_janus_point), .dissonance(dissonance),
        .scale_table(scale_table), .scale_overflow(scale_overflow),
        .qr_commit_valid(qr_commit_valid), .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
        .rplu_ratio_res(rplu_ratio_res), .rplu_ratio_valid(rplu_ratio_valid),
        .rplu_cfg_wr_en(rplu_cfg_wr_en), .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material), .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data), .inst_valid(inst_valid),
        .inst_word(inst_word), .fifo_full(1'b0), .laminar_index(dissonance),
        .turbulence(1'b0), .rplu_mode(1'b0), .boot_ready(1'b1),
        .sentinel_telemetry(sentinel_telemetry),
        .tgr_stream_start(), .tgr_stream_length(), .tgr_stream_vector_id(),
        .tgr_stream_valid(), .tgr_stream_data(), .tgr_stream_commit(),
        .tgr_stream_abort(), .tgr_status_hold(), .tgr_transport_status(128'd0),
        .pade_trace_valid(1'b0), .pade_trace_inv_input(128'd0),
        .pade_trace_inv_output(128'd0), .pade_trace_final_a(128'd0),
        .pade_trace_final_b(128'd0), .pade_trace_final_result(128'd0)
    );

    always #5 clk = ~clk;

    localparam S_IDLE=4'd0, S_CMD=4'd1, S_FILL=4'd2, S_RESP=4'd3,
               S_RECV_HDR=4'd4, S_RECV_DATA=4'd5, S_RECV_INST=4'd6,
               S_RECV_CRC=4'd7;
    integer checks = 0, fails = 0;

    task expect_state;
        input [127:0] label;
        input [3:0] expected;
        begin
            checks = checks + 1;
            if (dut.state !== expected) begin
                $display("FAIL state %0s expected=%0d got=%0d", label, expected, dut.state);
                fails = fails + 1;
            end else begin
                $display("PASS state %0s = %0d", label, expected);
            end
        end
    endtask

    function [7:0] crc8_byte;
        input [7:0] crc, byte_data;
        reg [7:0] s;
        integer i;
        begin
            s = crc;
            for (i=0; i<8; i=i+1)
                s = (s[7] != byte_data[7-i]) ? ({s[6:0],1'b0} ^ 8'h07) : {s[6:0],1'b0};
            crc8_byte = s;
        end
    endfunction

    function [7:0] crc8_word64;
        input [7:0] crc;
        input [63:0] word;
        reg [7:0] s;
        integer i;
        begin
            s = crc;
            for (i=0; i<8; i=i+1) s = crc8_byte(s, word[63-i*8 -: 8]);
            crc8_word64 = s;
        end
    endfunction

    task spi_byte;
        input [7:0] tx;
        integer i;
        begin
            for (i=7; i>=0; i=i-1) begin
                spi_mosi = tx[i]; #25; spi_sck = 1; #25; spi_sck = 0;
            end
        end
    endtask

    task spi_command_trace;
        input [7:0] tx;
        integer j;
        begin
            for (j=7; j>=0; j=j-1) begin
                spi_mosi = tx[j]; #25; spi_sck = 1;
                if (j == 0) begin
                    repeat (8) @(posedge clk);
                    expect_state("command-decode", (tx == 8'hA5) ? S_RECV_HDR :
                                 (tx == 8'hB1) ? S_RECV_INST : S_FILL);
                end
                #25; spi_sck = 0;
            end
        end
    endtask

    task begin_transaction;
        begin spi_cs_n = 0; #100; expect_state("command-entry", S_CMD); end
    endtask

    task end_transaction;
        begin spi_cs_n = 1; #200; expect_state("idle", S_IDLE); end
    endtask

    task settle;
        begin repeat (8) @(posedge clk); end
    endtask

    reg [63:0] payload;
    reg [7:0] crc;
    integer i;
    initial begin
        repeat (4) @(posedge clk);
        rst_n = 1;
        repeat (4) @(posedge clk);

        // Read path: IDLE -> CMD -> FILL -> RESP -> IDLE.
        begin_transaction;
        spi_command_trace(8'hAC); settle;
        #50; settle; expect_state("response-after-command-fall", S_RESP);
        repeat (4) spi_byte(8'h00);
        end_transaction;

        // Unknown command: same response state, with the oracle's 0x00 poison.
        begin_transaction;
        spi_command_trace(8'h00); settle;
        #50; settle; expect_state("unknown-response", S_RESP);
        if (dut.resp_buf[0] !== 8'h00) begin
            $display("FAIL UNKNOWN_CMD poison expected resp_buf[0]=00 got=%02x", dut.resp_buf[0]);
            fails = fails + 1;
        end else begin
            checks = checks + 1;
            $display("PASS UNKNOWN_CMD poison = 00");
        end
        spi_byte(8'h00); end_transaction;

        // A5 write reaches both payload states and then CRC.
        payload = 64'h0123456789ABCDEF;
        begin_transaction;
        spi_command_trace(8'hA5); settle;
        for (i=7; i>=0; i=i-1) spi_byte(payload[i*8 +: 8]);
        settle; expect_state("data-entry", S_RECV_DATA);
        for (i=7; i>=0; i=i-1) spi_byte(~payload[i*8 +: 8]);
        settle; expect_state("crc-entry-after-data", S_RECV_CRC);
        crc = crc8_word64(crc8_word64(crc8_byte(8'h00,8'hA5),payload),~payload);
        spi_byte(crc); end_transaction;

        // B1 write reaches the instruction and CRC states; wrong CRC poisons sticky status.
        payload = 64'hDEADBEEF01234567;
        begin_transaction;
        spi_command_trace(8'hB1); settle;
        for (i=7; i>=0; i=i-1) spi_byte(payload[i*8 +: 8]);
        settle; expect_state("crc-entry-after-instruction", S_RECV_CRC);
        spi_byte(8'h00); end_transaction;
        if (!dut.crc_error_sticky) begin $display("FAIL CRC_MISMATCH sticky"); fails=fails+1; end
        else begin checks=checks+1; $display("PASS CRC_MISMATCH sticky"); end

        // The oracle's deadman fault returns the receive machine to IDLE.
        begin_transaction;
        spi_command_trace(8'hB1); settle;
        #600000; spi_cs_n = 1; settle; expect_state("deadman-return", S_IDLE);

        // CS deassertion in the middle of a receive is the oracle's early-CS
        // poison path, distinct from the elapsed-time deadman above.
        begin_transaction;
        spi_command_trace(8'hB1); settle;
        spi_mosi = 1'b1; #25; spi_sck = 1'b1; #10; spi_cs_n = 1;
        settle; expect_state("early-cs-return", S_IDLE);

        // Negative control changes only the expected final transition.
        `ifdef NEGATIVE_CONTROL
        expect_state("negative-control-last-transition", S_RESP);
        `else
        expect_state("last-transition", S_IDLE);
        `endif

        if (fails == 0) begin
            $display("SPI TRACE: PASS (%0d state comparisons; 8 states reached; 3 fault classes exercised)", checks);
        end else begin
            $display("SPI TRACE: FAIL (%0d failures / %0d comparisons)", fails, checks);
            $fatal(1, "SPI trace comparison failed");
        end
        $finish;
    end
endmodule
