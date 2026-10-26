`timescale 1ns/1ps

module spu13_spi_core_qsub_tb;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg spi_cs_n = 1'b1;
    reg spi_sck = 1'b0;
    reg spi_mosi = 1'b0;
    wire spi_miso;

    // Wukong RPLU2CORE bring-up timing: 100 MHz / 64 core clock and
    // 25 kHz RP2350 bitbang SPI.
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
        .ENABLE_MATH(0),
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0),
        .ENABLE_CORE_RPLU_V2(1),
        .ENABLE_CORE_RPLU_V2_PIPELINE(0),
        .ENABLE_CORE_RPLU_V2_EXTENSIONS(0),
        .ENABLE_TORUS(0)
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
        .rotc_debug_status(), .boot_ready(core_boot_ready)
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

    function [63:0] qldi;
        input [7:0] lane;
        input signed [7:0] a;
        input signed [7:0] b;
        input signed [7:0] c;
        input signed [7:0] d;
        begin
            qldi = {8'h1D, lane, 8'd0, a[7:0], b[7:0], c[7:0], d[7:0], 8'd0};
        end
    endfunction

    function [63:0] qsub;
        input [7:0] dst;
        input [7:0] lhs;
        input [7:0] rhs;
        begin
            qsub = {8'h1B, dst, lhs, 16'h0000, {12'h000, rhs[3:0]}, 8'h00};
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
            repeat (256) @(posedge clk);
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
        $dumpfile("build/spu13_spi_core_qsub_tb.vcd");
        $dumpvars(0, spu13_spi_core_qsub_tb);

        #5000;
        rst_n = 1'b1;
        repeat (32) @(posedge clk);

        spi_inst_write(qldi(8'd1, 8'sd10, 8'sd20, 8'sd30, 8'sd40));
        expect_qr(4'd1, 64'd10, 64'd20, 64'd30, 64'd40);

        spi_inst_write(qldi(8'd2, 8'sd1, 8'sd2, 8'sd3, 8'sd4));
        expect_qr(4'd2, 64'd1, 64'd2, 64'd3, 64'd4);

        spi_inst_write(qsub(8'd3, 8'd1, 8'd2));
        expect_qr(4'd3, 64'd9, 64'd18, 64'd27, 64'd36);

        if (errors == 0)
            $display("spu13_spi_core_qsub_tb: PASS");
        else
            $display("spu13_spi_core_qsub_tb: FAIL (%0d errors)", errors);
        $finish;
    end
endmodule
