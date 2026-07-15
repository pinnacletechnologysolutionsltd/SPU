`timescale 1ns/1ps

// End-to-end shared-SPI proof for CMD B2 table load and CMD B3 status.
module spu13_tensegrity_transport_tb;
    reg clk = 0;
    always #10 clk = ~clk;
    reg rst_n = 0;
    reg spi_cs_n = 1;
    reg spi_sck = 0;
    reg spi_mosi = 0;
    wire spi_miso;

    wire tgr_stream_start, tgr_stream_valid, tgr_stream_commit, tgr_stream_abort;
    wire tgr_status_hold;
    wire [15:0] tgr_stream_length;
    wire [31:0] tgr_stream_vector_id;
    wire [7:0] tgr_stream_data;
    wire [127:0] tgr_transport_status;
    wire tgr_active_valid, tgr_busy;
    wire [7:0] tgr_loader_error;

    reg [7:0] packet [0:18];
    reg [7:0] response [0:15];
    reg [7:0] crc;
    reg [7:0] dummy;
    integer i;
    integer errors = 0;

    spu_spi_slave #(
        .ENABLE_TENSEGRITY(1),
        .TENSEGRITY_ONLY(1)
    ) u_spi (
        .clk(clk), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(832'd0), .satellite_snaps(4'd0),
        .is_janus_point(1'b0), .dissonance(16'd0),
        .scale_table(52'd0), .scale_overflow(13'd0),
        .qr_commit_valid(1'b0), .qr_commit_lane(4'd0),
        .qr_commit_A(64'd0), .qr_commit_B(64'd0),
        .qr_commit_C(64'd0), .qr_commit_D(64'd0),
        .hex_valid(1'b0), .hex_q(16'd0), .hex_r(16'd0),
        .rplu_ratio_res(3'sd0), .rplu_ratio_valid(1'b0),
        .fifo_full(1'b0), .laminar_index(16'd0), .turbulence(1'b0),
        .rplu_mode(1'b0), .boot_ready(1'b1),
        .sentinel_telemetry(512'd0),
        .tgr_stream_start(tgr_stream_start),
        .tgr_stream_length(tgr_stream_length),
        .tgr_stream_vector_id(tgr_stream_vector_id),
        .tgr_stream_valid(tgr_stream_valid), .tgr_stream_data(tgr_stream_data),
        .tgr_stream_commit(tgr_stream_commit), .tgr_stream_abort(tgr_stream_abort),
        .tgr_status_hold(tgr_status_hold),
        .tgr_transport_status(tgr_transport_status)
    );

    spu13_tensegrity_sidecar u_sidecar (
        .clk(clk), .rst_n(rst_n),
        .stream_start(tgr_stream_start), .stream_length(tgr_stream_length),
        .stream_vector_id(tgr_stream_vector_id),
        .stream_valid(tgr_stream_valid), .stream_data(tgr_stream_data),
        .stream_commit(tgr_stream_commit), .stream_abort(tgr_stream_abort),
        .status_hold(tgr_status_hold),
        .transport_status(tgr_transport_status), .active_valid(tgr_active_valid),
        .busy(tgr_busy), .loader_error(tgr_loader_error)
    );

    function [7:0] crc8_byte;
        input [7:0] crc_in;
        input [7:0] byte_data;
        reg [7:0] s;
        integer b;
        begin
            s = crc_in;
            for (b = 0; b < 8; b = b + 1) begin
                if (s[7] != byte_data[7-b])
                    s = {s[6:0], 1'b0} ^ 8'h07;
                else
                    s = {s[6:0], 1'b0};
            end
            crc8_byte = s;
        end
    endfunction

    task spi_byte;
        input [7:0] value;
        output [7:0] received;
        integer bit_index;
        begin
            received = 0;
            for (bit_index = 7; bit_index >= 0; bit_index = bit_index - 1) begin
                spi_mosi = value[bit_index];
                #100; spi_sck = 1;
                received[bit_index] = spi_miso;
                #100; spi_sck = 0;
            end
        end
    endtask

    task build_empty_table_packet;
        input [31:0] vector_id;
        begin
            // B2 + length(12) + vector id + TGR1 header. Empty payload CRC32=0.
            packet[0]=8'hB2; packet[1]=0; packet[2]=12;
            packet[3]=vector_id[31:24]; packet[4]=vector_id[23:16];
            packet[5]=vector_id[15:8]; packet[6]=vector_id[7:0];
            packet[7]="T"; packet[8]="G"; packet[9]="R"; packet[10]="1";
            packet[11]=1; packet[12]=0; packet[13]=0; packet[14]=0;
            packet[15]=0; packet[16]=0; packet[17]=0; packet[18]=0;
        end
    endtask

    task send_b2;
        input bad_crc;
        begin
            crc = 0;
            for (i = 0; i < 19; i = i + 1)
                crc = crc8_byte(crc, packet[i]);
            spi_cs_n = 0; #400;
            for (i = 0; i < 19; i = i + 1)
                spi_byte(packet[i], dummy);
            spi_byte(bad_crc ? (crc ^ 8'h01) : crc, dummy);
            #400; spi_cs_n = 1; #800;
        end
    endtask

    task send_b2_deadman_stall;
        begin
            // Complete command + prefix so the sidecar has opened its staging
            // bank, send one table byte, then hold CS active without SCK long
            // enough for the slave's 128-fabric-cycle deadman to abort it.
            spi_cs_n = 0; #400;
            for (i = 0; i < 8; i = i + 1)
                spi_byte(packet[i], dummy);
            #4000;
            spi_cs_n = 1; #800;
        end
    endtask

    task read_b3;
        begin
            spi_cs_n = 0; #400;
            spi_byte(8'hB3, dummy);
            for (i = 0; i < 16; i = i + 1)
                spi_byte(8'h00, response[i]);
            #400; spi_cs_n = 1; #800;
        end
    endtask

    initial begin
        repeat (8) @(posedge clk);
        rst_n = 1;
        #200;

        build_empty_table_packet(32'd1);
        send_b2(1'b0);
        i = 0;
        while (tgr_busy && i < 20000) begin #20; i = i + 1; end
        if (i == 20000) begin errors = errors + 1; $display("FAIL B2 verify timeout"); end
        read_b3;
        if (response[0] !== 1 || response[1] !== 7 || response[2] !== 4 ||
            response[3] !== 0 || {response[4],response[5],response[6],response[7]} !== 32'd1 ||
            response[8] !== 8'h08 || response[9] !== 0 ||
            response[10] !== 0 || response[11] !== 0 ||
            {response[12],response[13]} !== 16'd12 ||
            {response[14],response[15]} !== 16'd12) begin
            errors = errors + 1;
            $display("FAIL B2/B3 valid path status=%02x %02x %02x %02x vec=%02x%02x%02x%02x diag=%02x %02x %02x %02x %02x%02x %02x%02x",
                     response[0],response[1],response[2],response[3],
                     response[4],response[5],response[6],response[7],
                     response[8],response[9],response[10],response[11],
                     response[12],response[13],response[14],response[15]);
        end else begin
            $display("PASS B2 valid load + B3 exact status");
        end

        build_empty_table_packet(32'd2);
        send_b2(1'b1);
        #1000;
        read_b3;
        if ({response[4],response[5],response[6],response[7]} !== 32'd1 ||
            response[1] !== 7 || response[2] !== 4 ||
            response[8] !== 8'h09 || response[9] !== 1) begin
            errors = errors + 1;
            $display("FAIL bad transport CRC rollback vec=%02x%02x%02x%02x state=%0d fault=%0d flags=%02x error=%0d",
                     response[4],response[5],response[6],response[7],
                     response[1],response[2],response[8],response[9]);
        end else begin
            $display("PASS B2 transport CRC rollback + B3 diagnostic");
        end

        build_empty_table_packet(32'd3);
        send_b2_deadman_stall;
        #1000;
        read_b3;
        if ({response[4],response[5],response[6],response[7]} !== 32'd1 ||
            response[1] !== 7 || response[2] !== 4 ||
            response[8] !== 8'h09 || response[9] !== 1 ||
            {response[12],response[13]} !== 16'd1 ||
            {response[14],response[15]} !== 16'd12) begin
            errors = errors + 1;
            $display("FAIL B2 deadman rollback vec=%02x%02x%02x%02x state=%0d fault=%0d flags=%02x error=%0d received=%0d expected=%0d",
                     response[4],response[5],response[6],response[7],
                     response[1],response[2],response[8],response[9],
                     {response[12],response[13]}, {response[14],response[15]});
        end else begin
            $display("PASS B2 deadman timeout rollback + B3 diagnostic");
        end

        if (errors == 0)
            $display("SPU13_TENSEGRITY_TRANSPORT_TB: PASS");
        else
            $display("SPU13_TENSEGRITY_TRANSPORT_TB: FAIL errors=%0d", errors);
        $finish(errors != 0);
    end
endmodule
