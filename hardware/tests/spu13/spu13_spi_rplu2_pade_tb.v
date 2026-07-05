`timescale 1ns/1ps

module spu13_spi_rplu2_pade_tb;
    localparam [7:0] OP_RPLU2_START = 8'h2A;

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg spi_cs_n = 1'b1;
    reg spi_sck = 1'b0;
    reg spi_mosi = 1'b0;
    wire spi_miso;

    // Match the Wukong divided bring-up clock: 100 MHz / 64.
    always #320 clk = ~clk;

    wire spi_inst_valid;
    wire [63:0] spi_inst_word;
    wire cfg_wr_en;
    wire [2:0] cfg_sel;
    wire [7:0] cfg_material;
    wire [9:0] cfg_addr;
    wire [63:0] cfg_data;

    wire sidecar_inst_claimed;
    wire sidecar_busy;
    wire sidecar_error;
    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A;
    wire [63:0] qr_commit_B;
    wire [63:0] qr_commit_C;
    wire [63:0] qr_commit_D;
    wire [7:0] debug_status;
    wire [2:0] debug_state;

    reg [7:0] last_opcode = 8'h00;
    reg sidecar_claim_seen = 1'b0;
    reg sidecar_commit_seen = 1'b0;
    reg [7:0] rx_buf [0:63];
    integer errors = 0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            last_opcode <= 8'h00;
            sidecar_claim_seen <= 1'b0;
            sidecar_commit_seen <= 1'b0;
        end else begin
            if (spi_inst_valid)
                last_opcode <= spi_inst_word[63:56];
            if (sidecar_inst_claimed)
                sidecar_claim_seen <= 1'b1;
            if (qr_commit_valid)
                sidecar_commit_seen <= 1'b1;
        end
    end

    spu13_rplu2_pade_sidecar u_sidecar (
        .clk(clk),
        .rst_n(rst_n),
        .inst_valid(spi_inst_valid),
        .inst_word(spi_inst_word),
        .inst_claimed(sidecar_inst_claimed),
        .busy(sidecar_busy),
        .error(sidecar_error),
        .cfg_wr_en(cfg_wr_en),
        .cfg_sel(cfg_sel),
        .cfg_addr(cfg_addr),
        .cfg_data(cfg_data),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A),
        .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C),
        .qr_commit_D(qr_commit_D),
        .debug_status(debug_status),
        .debug_state(debug_state)
    );

    spu_spi_slave u_spi (
        .clk(clk),
        .rst_n(rst_n),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .manifold_state(832'd0),
        .satellite_snaps({1'b0, sidecar_error, sidecar_claim_seen, sidecar_commit_seen}),
        .is_janus_point(sidecar_claim_seen),
        .dissonance(16'd0),
        .scale_table(52'd0),
        .scale_overflow(13'd0),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A),
        .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C),
        .qr_commit_D(qr_commit_D),
        .hex_valid(1'b0),
        .hex_q(16'd0),
        .hex_r(16'd0),
        .rplu_ratio_res(debug_state),
        .rplu_ratio_valid(1'b1),
        .rplu_cfg_wr_en(cfg_wr_en),
        .rplu_cfg_sel(cfg_sel),
        .rplu_cfg_material(cfg_material),
        .rplu_cfg_addr(cfg_addr),
        .rplu_cfg_data(cfg_data),
        .inst_valid(spi_inst_valid),
        .inst_word(spi_inst_word),
        .fifo_full(1'b0),
        .laminar_index({debug_status, last_opcode}),
        .turbulence(sidecar_error),
        .rplu_mode(sidecar_busy),
        .sentinel_telemetry(512'd0)
    );

    task spi_byte_send;
        input [7:0] tx;
        output [7:0] rx;
        integer i;
        begin
            rx = 8'h00;
            for (i = 7; i >= 0; i = i - 1) begin
                spi_mosi = tx[i];
                #5000;
                spi_sck = 1'b1;
                #5000;
                rx[i] = spi_miso;
                spi_sck = 1'b0;
            end
        end
    endtask

    function [7:0] crc8_byte;
        input [7:0] crc;
        input [7:0] byte_data;
        reg [7:0] s;
        integer i;
        begin
            s = crc;
            for (i = 0; i < 8; i = i + 1) begin
                if (s[7] != byte_data[7-i])
                    s = {s[6:0], 1'b0} ^ 8'h07;
                else
                    s = {s[6:0], 1'b0};
            end
            crc8_byte = s;
        end
    endfunction

    function [7:0] crc8_word64;
        input [7:0] crc;
        input [63:0] word_data;
        reg [7:0] s;
        integer i;
        begin
            s = crc;
            for (i = 0; i < 8; i = i + 1)
                s = crc8_byte(s, word_data[63 - i*8 -: 8]);
            crc8_word64 = s;
        end
    endfunction

    function [63:0] rplu_header;
        input [2:0] sel;
        input [9:0] addr;
        begin
            rplu_header = {8'hA5, 5'd0, sel, 4'd0, addr, 34'd0};
        end
    endfunction

    task spi_u64_send;
        input [63:0] word;
        integer b;
        reg [7:0] dummy;
        begin
            for (b = 7; b >= 0; b = b - 1)
                spi_byte_send(word[b*8 +: 8], dummy);
        end
    endtask

    task spi_cfg_write;
        input [2:0] sel;
        input [9:0] addr;
        input [63:0] data;
        reg [7:0] dummy;
        reg [7:0] crc;
        reg [63:0] header;
        begin
            header = rplu_header(sel, addr);
            crc = crc8_word64(crc8_word64(crc8_byte(8'h00, 8'hA5), header), data);
            spi_cs_n = 1'b0;
            #20000;
            spi_byte_send(8'hA5, dummy);
            spi_u64_send(header);
            spi_u64_send(data);
            spi_byte_send(crc, dummy);
            #50000;
            spi_cs_n = 1'b1;
            repeat (512) @(posedge clk);
        end
    endtask

    task spi_inst_write;
        input [63:0] word;
        reg [7:0] dummy;
        reg [7:0] crc;
        begin
            crc = crc8_word64(crc8_byte(8'h00, 8'hB1), word);
            spi_cs_n = 1'b0;
            #20000;
            spi_byte_send(8'hB1, dummy);
            spi_u64_send(word);
            spi_byte_send(crc, dummy);
            #50000;
            spi_cs_n = 1'b1;
            repeat (512) @(posedge clk);
        end
    endtask

    task spi_read_status;
        reg [7:0] dummy;
        begin
            spi_cs_n = 1'b0;
            #20000;
            spi_byte_send(8'hAC, dummy);
            spi_byte_send(8'h00, rx_buf[0]);
            spi_byte_send(8'h00, rx_buf[1]);
            spi_byte_send(8'h00, rx_buf[2]);
            spi_byte_send(8'h00, rx_buf[3]);
            #50000;
            spi_cs_n = 1'b1;
            repeat (32) @(posedge clk);
        end
    endtask

    task spi_read_qr;
        integer b;
        reg [7:0] dummy;
        begin
            spi_cs_n = 1'b0;
            #20000;
            spi_byte_send(8'hAE, dummy);
            for (b = 0; b < 34; b = b + 1)
                spi_byte_send(8'h00, rx_buf[b]);
            #50000;
            spi_cs_n = 1'b1;
            repeat (32) @(posedge clk);
        end
    endtask

    task expect_status;
        input [7:0] min_dbg_mask;
        begin
            spi_read_status();
            $display("status raw=%02h %02h %02h %02h side_dbg=%02h state=%0d busy=%0d",
                     rx_buf[0], rx_buf[1], rx_buf[2], rx_buf[3],
                     debug_status, debug_state, sidecar_busy);
            if ((rx_buf[0] & min_dbg_mask) !== min_dbg_mask) begin
                $display("FAIL: status debug mask %02h missing from %02h",
                         min_dbg_mask, rx_buf[0]);
                errors = errors + 1;
            end
            if (rx_buf[3][1]) begin
                $display("FAIL: SPI CRC sticky error set");
                errors = errors + 1;
            end
        end
    endtask

    task expect_qr;
        reg [63:0] got_A, got_B, got_C, got_D;
        begin
            spi_read_qr();
            got_A = {rx_buf[2], rx_buf[3], rx_buf[4], rx_buf[5],
                     rx_buf[6], rx_buf[7], rx_buf[8], rx_buf[9]};
            got_B = {rx_buf[10], rx_buf[11], rx_buf[12], rx_buf[13],
                     rx_buf[14], rx_buf[15], rx_buf[16], rx_buf[17]};
            got_C = {rx_buf[18], rx_buf[19], rx_buf[20], rx_buf[21],
                     rx_buf[22], rx_buf[23], rx_buf[24], rx_buf[25]};
            got_D = {rx_buf[26], rx_buf[27], rx_buf[28], rx_buf[29],
                     rx_buf[30], rx_buf[31], rx_buf[32], rx_buf[33]};
            if (rx_buf[0] !== 8'h01 || rx_buf[1][3:0] !== 4'd4 ||
                got_A !== 64'd2 || got_B !== 64'd0 ||
                got_C !== 64'd0 || got_D !== 64'd0) begin
                $display("FAIL: QR valid=%02h lane=%02h", rx_buf[0], rx_buf[1]);
                $display("      got A=%h B=%h C=%h D=%h",
                         got_A, got_B, got_C, got_D);
                errors = errors + 1;
            end else begin
                $display("PASS: SPI RPLU2PADE QR lane 4");
            end
        end
    endtask

    initial begin
        $display("=== SPI RPLU2PADE Sidecar Testbench ===");
        #5000;
        rst_n = 1'b1;
        repeat (32) @(posedge clk);

        spi_cfg_write(3'd1, 10'd0, 64'h00000000_00000002);
        spi_cfg_write(3'd1, 10'd8, 64'h00000000_00000000);
        spi_cfg_write(3'd2, 10'd0, 64'h00000000_00000001);
        spi_cfg_write(3'd2, 10'd8, 64'h00000000_00000000);
        spi_cfg_write(3'd3, 10'd1, 64'h00000000_00000001);
        spi_cfg_write(3'd3, 10'd65, 64'h00000000_00000000);
        expect_status(8'h01);

        spi_inst_write({OP_RPLU2_START, 8'd4, 48'd0});
        repeat (4000) @(posedge clk);
        expect_status(8'h07);
        expect_qr();

        if (sidecar_error) begin
            $display("FAIL: RPLU2PADE sidecar error asserted");
            errors = errors + 1;
        end
        if (sidecar_busy) begin
            $display("FAIL: RPLU2PADE sidecar still busy");
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS: spu13_spi_rplu2_pade_tb");
        else
            $display("FAIL: spu13_spi_rplu2_pade_tb (%0d errors)", errors);
        $finish;
    end
endmodule
