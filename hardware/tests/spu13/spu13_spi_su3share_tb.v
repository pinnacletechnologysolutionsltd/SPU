`timescale 1ns/1ps

module spu13_spi_su3share_tb;
    localparam [7:0] OP_SU3_LOAD_A = 8'hE8;
    localparam [7:0] OP_SU3_LOAD_B = 8'hE9;
    localparam [7:0] OP_SU3_START  = 8'hEA;
    localparam [7:0] OP_SU3_READ   = 8'hEB;

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
    wire su3_inst_claimed;
    wire su3_busy;
    wire su3_error;
    wire su3_qr_commit_valid;
    wire [3:0] su3_qr_commit_lane;
    wire [63:0] su3_qr_commit_A;
    wire [63:0] su3_qr_commit_B;
    wire [63:0] su3_qr_commit_C;
    wire [63:0] su3_qr_commit_D;
    wire [7:0] su3_debug_status;
    wire [2:0] su3_debug_state;

    wire shared_mult_start;
    wire [31:0] shared_mult_a0, shared_mult_a1, shared_mult_a2, shared_mult_a3;
    wire [31:0] shared_mult_b0, shared_mult_b1, shared_mult_b2, shared_mult_b3;
    wire [31:0] shared_mult_r0, shared_mult_r1, shared_mult_r2, shared_mult_r3;
    wire shared_mult_done, shared_mult_busy;

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
            if (su3_inst_claimed)
                sidecar_claim_seen <= 1'b1;
            if (su3_qr_commit_valid)
                sidecar_commit_seen <= 1'b1;
        end
    end

    spu13_m31_multiplier u_shared_m31_mult (
        .clk(clk),
        .rst_n(rst_n),
        .start(shared_mult_start),
        .a0(shared_mult_a0),
        .a1(shared_mult_a1),
        .a2(shared_mult_a2),
        .a3(shared_mult_a3),
        .b0(shared_mult_b0),
        .b1(shared_mult_b1),
        .b2(shared_mult_b2),
        .b3(shared_mult_b3),
        .r0(shared_mult_r0),
        .r1(shared_mult_r1),
        .r2(shared_mult_r2),
        .r3(shared_mult_r3),
        .done(shared_mult_done),
        .busy(shared_mult_busy),
        .rns_error()
    );

    spu13_su3_sidecar #(
        .EXTERNAL_MULT(1)
    ) u_su3_sidecar (
        .clk(clk),
        .rst_n(rst_n),
        .inst_valid(spi_inst_valid),
        .inst_word(spi_inst_word),
        .inst_claimed(su3_inst_claimed),
        .busy(su3_busy),
        .error(su3_error),
        .qr_commit_valid(su3_qr_commit_valid),
        .qr_commit_lane(su3_qr_commit_lane),
        .qr_commit_A(su3_qr_commit_A),
        .qr_commit_B(su3_qr_commit_B),
        .qr_commit_C(su3_qr_commit_C),
        .qr_commit_D(su3_qr_commit_D),
        .debug_status(su3_debug_status),
        .debug_state(su3_debug_state),
        .shared_mult_start(shared_mult_start),
        .shared_mult_a0(shared_mult_a0),
        .shared_mult_a1(shared_mult_a1),
        .shared_mult_a2(shared_mult_a2),
        .shared_mult_a3(shared_mult_a3),
        .shared_mult_b0(shared_mult_b0),
        .shared_mult_b1(shared_mult_b1),
        .shared_mult_b2(shared_mult_b2),
        .shared_mult_b3(shared_mult_b3),
        .shared_mult_r0(shared_mult_r0),
        .shared_mult_r1(shared_mult_r1),
        .shared_mult_r2(shared_mult_r2),
        .shared_mult_r3(shared_mult_r3),
        .shared_mult_done(shared_mult_done),
        .shared_mult_busy(shared_mult_busy)
    );

    spu_spi_slave u_spi (
        .clk(clk),
        .rst_n(rst_n),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .manifold_state(832'd0),
        .satellite_snaps({1'b0, su3_error, sidecar_claim_seen, sidecar_commit_seen}),
        .is_janus_point(sidecar_claim_seen),
        .dissonance(16'd0),
        .scale_table(52'd0),
        .scale_overflow(13'd0),
        .qr_commit_valid(su3_qr_commit_valid),
        .qr_commit_lane(su3_qr_commit_lane),
        .qr_commit_A(su3_qr_commit_A),
        .qr_commit_B(su3_qr_commit_B),
        .qr_commit_C(su3_qr_commit_C),
        .qr_commit_D(su3_qr_commit_D),
        .hex_valid(1'b0),
        .hex_q(16'd0),
        .hex_r(16'd0),
        .rplu_ratio_res(su3_debug_state),
        .rplu_ratio_valid(1'b1),
        .rplu_cfg_wr_en(),
        .rplu_cfg_sel(),
        .rplu_cfg_material(),
        .rplu_cfg_addr(),
        .rplu_cfg_data(),
        .inst_valid(spi_inst_valid),
        .inst_word(spi_inst_word),
        .fifo_full(1'b0),
        .laminar_index({su3_debug_status, last_opcode}),
        .turbulence(su3_error),
        .rplu_mode(su3_busy),
        .boot_ready(1'b1),  // no boot FSM in this top — always ready
        .sentinel_telemetry(512'd0)
    );

    function [255:0] dense_a_elem(input integer idx);
        begin
            case (idx)
                0: dense_a_elem = 256'h000000190000001700000013000000110000000a000000080000000600000004;
                1: dense_a_elem = 256'h0000002f0000002d00000029000000270000001500000013000000110000000f;
                2: dense_a_elem = 256'h00000045000000430000003f0000003d000000200000001e0000001c0000001a;
                3: dense_a_elem = 256'h00000023000000210000001d0000001b0000000f0000000d0000000b00000009;
                4: dense_a_elem = 256'h000000390000003700000033000000310000001a000000180000001600000014;
                5: dense_a_elem = 256'h0000004f0000004d00000049000000470000002500000023000000210000001f;
                6: dense_a_elem = 256'h0000002d0000002b00000027000000250000001400000012000000100000000e;
                7: dense_a_elem = 256'h00000043000000410000003d0000003b0000001f0000001d0000001b00000019;
                default: dense_a_elem = 256'h000000590000005700000053000000510000002a000000280000002600000024;
            endcase
        end
    endfunction

    function [255:0] dense_b_elem(input integer idx);
        begin
            case (idx)
                0: dense_b_elem = 256'h0000004d0000004b00000047000000450000002400000022000000200000001e;
                1: dense_b_elem = 256'h0000006700000065000000610000005f000000310000002f0000002d0000002b;
                2: dense_b_elem = 256'h000000810000007f0000007b000000790000003e0000003c0000003a00000038;
                3: dense_b_elem = 256'h0000005b0000005900000055000000530000002b000000290000002700000025;
                4: dense_b_elem = 256'h00000075000000730000006f0000006d00000038000000360000003400000032;
                5: dense_b_elem = 256'h0000008f0000008d00000089000000870000004500000043000000410000003f;
                6: dense_b_elem = 256'h0000006900000067000000630000006100000032000000300000002e0000002c;
                7: dense_b_elem = 256'h00000083000000810000007d0000007b0000003f0000003d0000003b00000039;
                default: dense_b_elem = 256'h0000009d0000009b00000097000000950000004c0000004a0000004800000046;
            endcase
        end
    endfunction

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

    task spi_u64_send;
        input [63:0] word;
        integer b;
        reg [7:0] dummy;
        begin
            for (b = 7; b >= 0; b = b - 1)
                spi_byte_send(word[b*8 +: 8], dummy);
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

    task load_elem;
        input [7:0] op;
        input integer elem;
        input [255:0] value;
        integer word_idx;
        reg [31:0] word_data;
        begin
            for (word_idx = 0; word_idx < 8; word_idx = word_idx + 1) begin
                word_data = value[word_idx * 32 +: 32];
                spi_inst_write({op, elem[3:0], 1'b0, word_idx[2:0], 16'd0, word_data});
            end
        end
    endtask

    task expect_qr0;
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
            if (rx_buf[0] !== 8'h01 || rx_buf[1][3:0] !== 4'd2 ||
                got_A !== 64'h7ffe271f7ffc43ef ||
                got_B !== 64'h7fff6b677ffed36f ||
                got_C !== 64'h00021510000446a0 ||
                got_D !== 64'h0000a30000014f30) begin
                $display("FAIL: QR valid=%02h lane=%02h", rx_buf[0], rx_buf[1]);
                $display("      got A=%h B=%h C=%h D=%h",
                         got_A, got_B, got_C, got_D);
                errors = errors + 1;
            end else begin
                $display("PASS: SPI SU3 QR2 element 0");
            end
        end
    endtask

    integer matrix_idx;

    initial begin
        $display("=== SPI SU3SHARE Sidecar Testbench ===");
        #5000;
        rst_n = 1'b1;
        repeat (32) @(posedge clk);

        spi_inst_write({OP_SU3_START, 4'd0, 4'd0, 48'd0});
        for (matrix_idx = 0; matrix_idx < 9; matrix_idx = matrix_idx + 1)
            load_elem(OP_SU3_LOAD_A, matrix_idx, dense_a_elem(matrix_idx));
        for (matrix_idx = 0; matrix_idx < 9; matrix_idx = matrix_idx + 1)
            load_elem(OP_SU3_LOAD_B, matrix_idx, dense_b_elem(matrix_idx));

        repeat (4000) @(posedge clk);
        if (su3_busy) begin
            $display("FAIL: SU3 sidecar still busy status=%02h state=%0d mult_busy=%0d",
                     su3_debug_status, su3_debug_state, shared_mult_busy);
            errors = errors + 1;
        end
        if (su3_error) begin
            $display("FAIL: SU3 sidecar error asserted");
            errors = errors + 1;
        end

        spi_read_status();
        $display("status raw=%02h %02h %02h %02h", rx_buf[0], rx_buf[1], rx_buf[2], rx_buf[3]);

        spi_inst_write({OP_SU3_READ, 4'd2, 4'd0, 48'd0});
        repeat (512) @(posedge clk);
        expect_qr0();

        if (errors == 0)
            $display("spu13_spi_su3share_tb: PASS");
        else
            $display("spu13_spi_su3share_tb: FAIL (%0d errors)", errors);
        $finish;
    end
endmodule
