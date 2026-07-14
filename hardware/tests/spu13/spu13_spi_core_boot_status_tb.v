// spu13_spi_core_boot_status_tb.v — real spu13_core + spu_spi_slave, real
// boot FSM (not a hand-driven boot_ready reg). Closes a gap the rest of the
// suite left open: spu_spi_slave_tb.v ties boot_ready to a constant 1'b1,
// and spu13_spi_core_irotc_tb.v never issues a 0xAC status read at all, so
// nothing exercised "does a real 0xAC read reflect a real core's boot_ready
// once it reaches READY." Added 2026-07-14 while chasing the A7 Wukong
// bring-up finding of "boot_state_dbg=READY but the live SPI status byte
// still reported boot_ready=0" — this passes cleanly, which rules out an
// RTL latching bug in spu_spi_slave.v as the cause (see AGENTS.md/session
// notes for the hardware-side follow-up that finding still needs).
`timescale 1ns/1ps

module spu13_spi_core_boot_status_tb;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg spi_cs_n = 1'b1;
    reg spi_sck = 1'b0;
    reg spi_mosi = 1'b0;
    wire spi_miso;

    always #320 clk = ~clk;  // matches spu13_spi_core_irotc_tb's clk_fast ratio

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
    wire [1:0] core_boot_state_dbg;
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
        .boot_ready(core_boot_ready),
        .boot_state_dbg(core_boot_state_dbg)
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

    task spi_status_read;
        integer b;
        reg [7:0] dummy;
        begin
            spi_cs_n = 1'b0;
            #20000;
            spi_byte_send(8'hAC, dummy);
            for (b = 0; b < 4; b = b + 1)
                spi_byte_send(8'h00, rx_buf[b]);
            #50000;
            spi_cs_n = 1'b1;
            repeat (16) @(posedge clk);
        end
    endtask

    integer wait_cycles;

    initial begin
        #5000;
        rst_n = 1'b1;

        // Poll boot_state_dbg directly via RTL tap until READY (2), exactly
        // mirroring what the A7_UART_DIAG channel showed on real hardware.
        wait_cycles = 0;
        while (core_boot_state_dbg !== 2'd2 && wait_cycles < 5000) begin
            @(posedge clk);
            wait_cycles = wait_cycles + 1;
        end
        if (core_boot_state_dbg !== 2'd2) begin
            $display("FAIL: boot FSM never reached READY (state=%0d after %0d cycles)",
                      core_boot_state_dbg, wait_cycles);
            errors = errors + 1;
            $display("FAIL (%0d errors)", errors);
            $finish;
        end

        // Settle in READY before reading status, same as the real session
        // (RDY:1 observed continuously via the diagnostic UART tap).
        repeat (100) @(posedge clk);

        spi_status_read();
        if (rx_buf[3][2] !== 1'b1) begin
            $display("FAIL: first AC read byte3=%02h, boot_ready bit clear despite READY",
                      rx_buf[3]);
            errors = errors + 1;
        end else begin
            $display("PASS: first AC read after settled READY reflects boot_ready");
        end

        // Second consecutive read: clear-on-read of crc_error_sticky must
        // not disturb the live boot_ready bit, and no CRC error should be
        // latent from the earlier command/response transaction.
        spi_status_read();
        if (rx_buf[3] !== 8'h04) begin
            $display("FAIL: second consecutive AC read byte3=%02h, expected 0x04",
                      rx_buf[3]);
            errors = errors + 1;
        end else begin
            $display("PASS: second consecutive AC read stable (boot_ready set, no stuck CRC error)");
        end

        if (errors == 0)
            $display("PASS");
        else
            $display("FAIL (%0d errors)", errors);
        $finish;
    end

    initial #20000000000 begin $display("FAIL (timeout)"); $finish; end
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
