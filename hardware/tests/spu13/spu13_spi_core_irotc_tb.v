// spu13_spi_core_irotc_tb.v — IROTC over the real SPI instruction path
// (clone of the proven spu13_spi_core_rotc_tb harness).
//
// Drives spu_spi_slave pins with CRC'd 0xB1 instruction writes and 0xAE
// QR-commit readbacks against spu13_core(ENABLE_IROTC=1): LOAD2X, main
// and CONJUGATE idx 36 rotations, a CATMIX fault whose absent commit is
// proven over the link, and SCALE2 recondition -> legal catalog switch.
// Expected values from the exact-Fraction oracle, 2026-07-11.
`timescale 1ns/1ps

module spu13_spi_core_irotc_tb;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg spi_cs_n = 1'b1;
    reg spi_sck = 1'b0;
    reg spi_mosi = 1'b0;
    wire spi_miso;

    // Match the current Wukong bring-up ratio: 100 MHz / 64 core clock,
    // with the RP2350 SPI driver slowed to 25 kHz.
    always #320 clk = ~clk;

    wire rplu_cfg_wr_en;
    wire [2:0] rplu_cfg_sel;
    wire [7:0] rplu_cfg_material;
    wire [9:0] rplu_cfg_addr;
    wire [63:0] rplu_cfg_data;
    wire spi_inst_valid;
    wire [63:0] spi_inst_word;

    wire qr_commit_valid;
    wire [3:0] qr_commit_lane;
    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    wire inst_done;
    wire core_boot_ready;
    wire [831:0] manifold_state;
    wire [51:0] scale_table;
    wire [12:0] scale_overflow;
    wire is_janus_point;
    wire [31:0] quadrance_out;
    wire [7:0] laminar_flow_index;
    wire signed [2:0] ratio_cmp_res;
    wire ratio_cmp_valid;
    wire rns_error;
    wire ecc_single_err, ecc_double_err;

    integer errors = 0;
    reg [7:0] rx_buf [0:63];

    spu13_core #(
        .DEVICE("SIM"),
        .ENABLE_RPLU(0),
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(0),  // lean spin config: no TDM rotor, IROTC self-sufficient
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(0),
        .ENABLE_CORE_RPLU_V2_PIPELINE(0),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .ENABLE_TORUS(0),
        .ENABLE_IROTC(1)
    ) u_core (
        .clk(clk), .rst_n(rst_n),
        .phi_8(1'b0), .phi_13(1'b0), .phi_21(1'b0),
        .dec_fast_cfg_wr_en(rplu_cfg_wr_en),
        .dec_fast_cfg_sel(rplu_cfg_sel),
        .dec_fast_cfg_material(rplu_cfg_material),
        .dec_fast_cfg_addr(rplu_cfg_addr),
        .dec_fast_cfg_data(rplu_cfg_data),
        .phinary_cfg(16'd0),
        .prime_data(24'd0), .prime_addr(4'd0), .prime_we(1'b0),
        .boot_done(1'b1),
        .pell_data(32'd0), .pell_addr(3'd0), .pell_we(1'b0),
        .manual_rotor_en(1'b0), .manual_rotor_data(64'd0),
        .mem_ready(1'b1), .mem_burst_rd(), .mem_burst_wr(),
        .mem_addr(), .mem_rd_manifold(832'd0), .mem_wr_manifold(),
        .mem_burst_done(1'b0),
        .artery_wr_en(), .artery_wr_data(),
        .current_axis_ptr(), .current_axis_data(),
        .qr_commit_valid(qr_commit_valid), .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),
        .inst_valid(spi_inst_valid), .inst_word(spi_inst_word),
        .inst_done(inst_done),
        .ratio_cmp_res(ratio_cmp_res), .ratio_cmp_valid(ratio_cmp_valid),
        .manifold_out(manifold_state), .bloom_complete(),
        .scale_table_out(scale_table), .scale_overflow_out(scale_overflow),
        .is_janus_point(is_janus_point),
        .audio_mode(), .gasket_sum_out(), .quadrance_out(quadrance_out),
        .cycle_wrap(), .rplu_dissoc_out(), .rplu_dissoc_mask_out(),
        .rplu_addr_out(), .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),
        .laminar_flow_index_out(laminar_flow_index), .thermal_pressure_out(),
        .hex_valid(), .hex_q(), .hex_r(), .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(), .fault_type(), .fault_count(),
        .rns_error(rns_error),
        .ecc_single_err(ecc_single_err), .ecc_double_err(ecc_double_err),
        .boot_ready(core_boot_ready)
    );

    spu_spi_slave u_spi (
        .clk(clk), .rst_n(rst_n),
        .spi_cs_n(spi_cs_n), .spi_sck(spi_sck),
        .spi_mosi(spi_mosi), .spi_miso(spi_miso),
        .manifold_state(manifold_state),
        .satellite_snaps(4'd0),
        .is_janus_point(is_janus_point),
        .dissonance(quadrance_out[15:0]),
        .scale_table(scale_table),
        .scale_overflow(scale_overflow),
        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),
        .hex_valid(1'b0), .hex_q(16'd0), .hex_r(16'd0),
        .rplu_ratio_res(ratio_cmp_res),
        .rplu_ratio_valid(ratio_cmp_valid),
        .rplu_cfg_wr_en(rplu_cfg_wr_en),
        .rplu_cfg_sel(rplu_cfg_sel),
        .rplu_cfg_material(rplu_cfg_material),
        .rplu_cfg_addr(rplu_cfg_addr),
        .rplu_cfg_data(rplu_cfg_data),
        .inst_valid(spi_inst_valid),
        .inst_word(spi_inst_word),
        .fifo_full(1'b0),
        .laminar_index({8'd0, laminar_flow_index}),
        .turbulence(rns_error || ecc_double_err),
        .rplu_mode(1'b0),
        .boot_ready(core_boot_ready),
        .sentinel_telemetry(512'd0)
    );

    function [63:0] load2x;
        input [7:0] lane;
        input signed [7:0] a;
        input signed [7:0] b;
        input signed [7:0] c;
        input signed [7:0] d;
        begin
            load2x = {8'hD7, lane, 8'd0, a[7:0], b[7:0], c[7:0], d[7:0], 8'd0};
        end
    endfunction

    function [63:0] irotc;
        input [7:0] dst;
        input [7:0] src;
        input conj;
        input [5:0] idx;
        begin
            // sel in p1_a[6:0]: word[30]=conjugate, word[29:24]=index
            irotc = {8'hD6, dst, src, 8'd0, 1'b0, conj, idx, 24'd0};
        end
    endfunction

    function [63:0] scale2;
        input [7:0] dst;
        input [7:0] src;
        begin
            scale2 = {8'hD8, dst, src, 40'd0};
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
                #20000;
                spi_sck = 1'b1;
                #20000;
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
            repeat (128) @(posedge clk);
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
            repeat (16) @(posedge clk);
        end
    endtask

    task expect_qr;
        input [3:0] lane;
        input [63:0] A;
        input [63:0] B;
        input [63:0] C;
        input [63:0] D;
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
            if (rx_buf[0] !== 8'h01 || rx_buf[1][3:0] !== lane ||
                got_A !== A || got_B !== B || got_C !== C || got_D !== D) begin
                $display("FAIL: QR commit valid=%02h lane=%02h", rx_buf[0], rx_buf[1]);
                $display("      got A=%h B=%h C=%h D=%h", got_A, got_B, got_C, got_D);
                $display("      exp A=%h B=%h C=%h D=%h", A, B, C, D);
                errors = errors + 1;
            end else begin
                $display("PASS: SPI QR%0d commit A=%h B=%h C=%h D=%h",
                         lane, A, B, C, D);
            end
        end
    endtask

    initial begin
        $dumpfile("build/spu13_spi_core_irotc_tb.vcd");
        $dumpvars(0, spu13_spi_core_irotc_tb);

        #5000;
        rst_n = 1'b1;
        repeat (32) @(posedge clk);

        // LOAD2X QR1 <- (0,3,-6,9): doubled, FRESH
        spi_inst_write(load2x(8'd1, 8'sd0, 8'sd3, -8'sd6, 8'sd9));
        expect_qr(4'd1, 64'h0000_0000_0000_0000,
                       64'h0000_0000_0000_0006,
                       64'h0000_0000_FFFF_FFF4,
                       64'h0000_0000_0000_0012);

        // IROTC QR2 <- QR1, idx 36 main (period-5, phi-arithmetic).
        // Oracle: A=(-3,6) B=(-12,9) C=(3,-15) D=(12,0); pack {b,a}.
        spi_inst_write(irotc(8'd2, 8'd1, 1'b0, 6'd36));
        expect_qr(4'd2, 64'h0000_0006_FFFF_FFFD,
                       64'h0000_0009_FFFF_FFF4,
                       64'hFFFF_FFF1_0000_0003,
                       64'h0000_0000_0000_000C);

        // IROTC QR3 <- QR1, CONJUGATE catalog idx 36 — the dual
        // icosahedron's rotation, not yet witnessed in silicon.
        // Oracle: A=(3,-6) B=(-3,-9) C=(-12,15) D=(12,0).
        spi_inst_write(irotc(8'd3, 8'd1, 1'b1, 6'd36));
        expect_qr(4'd3, 64'hFFFF_FFFA_0000_0003,
                       64'hFFFF_FFF7_FFFF_FFFD,
                       64'h0000_000F_FFFF_FFF4,
                       64'h0000_0000_0000_000C);

        // CATMIX: conjugate rotation on MAIN-locked QR2 must fault at
        // dispatch — no commit fires, so 0xAE still returns the QR3
        // commit above (the no-corruption proof over the real link).
        spi_inst_write(irotc(8'd4, 8'd2, 1'b1, 6'd3));
        expect_qr(4'd3, 64'hFFFF_FFFA_0000_0003,
                       64'hFFFF_FFF7_FFFF_FFFD,
                       64'h0000_000F_FFFF_FFF4,
                       64'h0000_0000_0000_000C);

        // SCALE2 QR5 <- 2*QR2: recondition to FRESH.
        // Oracle: A=(-6,12) B=(-24,18) C=(6,-30) D=(24,0).
        spi_inst_write(scale2(8'd5, 8'd2));
        expect_qr(4'd5, 64'h0000_000C_FFFF_FFFA,
                       64'h0000_0012_FFFF_FFE8,
                       64'hFFFF_FFE2_0000_0006,
                       64'h0000_0000_0000_0018);

        // Conjugate idx 3 on the reconditioned register: legal again.
        // Oracle: A=(12,9) B=(24,-18) C=(-21,24) D=(-15,-15).
        spi_inst_write(irotc(8'd6, 8'd5, 1'b1, 6'd3));
        expect_qr(4'd6, 64'h0000_0009_0000_000C,
                       64'hFFFF_FFEE_0000_0018,
                       64'h0000_0018_FFFF_FFEB,
                       64'hFFFF_FFF1_FFFF_FFF1);

        if (errors == 0)
            $display("spu13_spi_core_irotc_tb: PASS");
        else
            $display("spu13_spi_core_irotc_tb: FAIL (%0d errors)", errors);
        $finish;
    end
endmodule

module MULT27X36(
    output [62:0] DOUT,
    input  [26:0] A,
    input  [35:0] B,
    input  [25:0] D,
    input  [1:0]  CLK,
    input  [1:0]  CE,
    input  [1:0]  RESET,
    input         PSEL,
    input         PADDSUB
);
    assign DOUT = $signed(A) * $signed(B);
endmodule

module MULT18X18 #(
    parameter ASIGN = 1,
    parameter BSIGN = 1
) (
    input  [17:0] A,
    input  [17:0] B,
    output [35:0] P
);
    assign P = (ASIGN || BSIGN) ? ($signed(A) * $signed(B)) : (A * B);
endmodule

module SDPB #(
    parameter BIT_WIDTH_0 = 16,
    parameter BIT_WIDTH_1 = 16
) (
    input                         CLKA,
    input                         CEA,
    input                         RESETA,
    input  [13:0]                 ADA,
    input  [BIT_WIDTH_0-1:0]      DIA,
    input                         CLKB,
    input                         CEB,
    input                         RESETB,
    input  [13:0]                 ADB,
    output [BIT_WIDTH_1-1:0]      DOB
);
    assign DOB = {BIT_WIDTH_1{1'b0}};
endmodule
