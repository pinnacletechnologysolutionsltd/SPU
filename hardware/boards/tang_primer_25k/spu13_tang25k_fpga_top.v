// spu13_tang25k_fpga_top.v — SPU-13 FPGA core + SPI interface to RP2350 Southbridge
// Target: Tang Primer 25K (GW5A-LV25MG121NES)
//
// Architecture:
//   FPGA does ONE thing: run the SPU-13 core.
//   Everything else (boot sequencing, table hydration, UART, telemetry,
//   instruction streaming) is owned by the RP2350 southbridge over SPI.
//
// SPI pins (Mode 0, CPOL=0 CPHA=0, 2 MHz):
//   PMOD J4 header — same physical pins as the old flash probe.
//   RP2350-Zero connects header GP0-3 to PMOD J4.
//
//   PMOD J4 pin   Signal     RP2350-Zero GPIO
//   ───────────   ──────     ───────────────
//   G10 (CS)   →  SPI_CS     GP1
//   D10 (SCK)  →  SPI_SCK    GP2
//   C10 (MOSI) →  SPI_MOSI   GP3
//   B10 (MISO) ←  SPI_MISO   GP0
//
// SPI Commands (spu_spi_slave.v protocol v1.1):
//   0xA0 — read 32-byte manifold burst (4 axes)
//   0xAC — read 4-byte status
//   0xAD — read 9-byte scale table + overflow
//   0xB0 — read 64-byte sentinel telemetry burst
//   0xB1 — write one 64-bit instruction/chord
//   0xA5 — write RPLU config (HEADER + DATA chords)
//
// The RP2350 boots first, then hydrates FPGA tables/instructions via SPI,
// then streams chords. No FPGA-side boot ROM, no flash boot, no SDRAM.

module spu13_tang25k_southbridge_top (
    input  wire        sys_clk,       // 50 MHz crystal at E2
    output wire [2:0]  led,           // on-board LEDs, active low
    // SPI southbridge (PMOD J4 pins, to RP2350)
    input  wire        spi_cs_n,      // G10
    input  wire        spi_sck,       // D10
    input  wire        spi_mosi,      // C10
    output wire        spi_miso       // B10
);

    // ── Clock ──────────────────────────────────────────────────
    wire clk_50m;
    BUFG u_bufg_50m (.I(sys_clk), .O(clk_50m));

    wire clk_core;  // ~6.25 MHz (50 MHz / 8)
    reg [2:0] clk_div = 0;
    always @(posedge clk_50m) clk_div <= clk_div + 1;

    wire clk_core_raw = clk_div[2];
    BUFG u_bufg_core (.I(clk_core_raw), .O(clk_core));

    // ── Reset ──────────────────────────────────────────────────
    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge clk_core) if (rst_cnt != 8'hFF) rst_cnt <= rst_cnt + 1;

    // ── Fibonacci Timing Pulses (phi 8, 13, 21) ────────────────
    reg [8:0] phi_cnt = 273;
    always @(posedge clk_core) begin
        if (!rst_n)                     phi_cnt <= 273;
        else if (pulse_p_trigger)       phi_cnt <= 0;
        else if (phi_cnt < 273)         phi_cnt <= phi_cnt + 1;
    end
    wire [4:0] phi_sub = (phi_cnt < 273) ? (phi_cnt % 21) : 5'd0;
    wire phi_8  = (phi_sub == 5'd7);
    wire phi_13 = (phi_sub == 5'd12);
    wire phi_21 = (phi_sub == 5'd20);

    // ── Heartbeat trigger (1.5 Hz from clk_core) ───────────────
    reg [22:0] heartbeat = 0;
    reg pulse_p_last = 0;
    always @(posedge clk_core) begin
        heartbeat <= heartbeat + 1;
        pulse_p_last <= heartbeat[22];
    end
    wire pulse_p_trigger = (heartbeat[22] && !pulse_p_last);

    // ── SPI Slave ──────────────────────────────────────────────
    // Sample 2 MHz SPI with the raw 50 MHz clock. The core clock is only
    // 6.25 MHz, which is too slow for the receiver's synchronised edge
    // detector. Payloads remain stable while a toggle carries each event
    // safely into the core clock domain.
    wire        spi_inst_valid_fast;
    wire [63:0] spi_inst_word_fast;
    reg         spi_inst_toggle = 0;
    reg  [2:0]  spi_inst_toggle_sync = 0;
    reg         spi_inst_toggle_seen = 0;
    reg         inst_valid = 0;
    reg  [63:0] inst_word = 0;
    wire        inst_done;

    always @(posedge clk_50m or negedge rst_n) begin
        if (!rst_n)
            spi_inst_toggle <= 1'b0;
        else if (spi_inst_valid_fast)
            spi_inst_toggle <= ~spi_inst_toggle;
    end

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            spi_inst_toggle_sync <= 3'b000;
            spi_inst_toggle_seen <= 1'b0;
            inst_valid <= 1'b0;
            inst_word <= 64'd0;
        end else begin
            spi_inst_toggle_sync <= {spi_inst_toggle_sync[1:0], spi_inst_toggle};
            inst_valid <= 1'b0;
            if (spi_inst_toggle_sync[2] != spi_inst_toggle_seen) begin
                spi_inst_toggle_seen <= spi_inst_toggle_sync[2];
                inst_word <= spi_inst_word_fast;
                inst_valid <= 1'b1;
            end
        end
    end
    wire        hex_valid;
    wire [15:0] hex_q, hex_r;
    wire        qr_commit_valid;
    wire [3:0]  qr_commit_lane;
    wire [63:0] qr_commit_A, qr_commit_B, qr_commit_C, qr_commit_D;
    wire signed [2:0] ratio_cmp_res;
    wire        ratio_cmp_valid;
    wire [831:0] manifold_state;
    wire [51:0]  scale_table;
    wire [12:0]  scale_overflow;
    wire         is_janus_point;
    wire [31:0]  quadrance_out;

    wire        rplu_cfg_wr_en_fast;
    wire [2:0]  rplu_cfg_sel_fast;
    wire [7:0]  rplu_cfg_material_fast;
    wire [9:0]  rplu_cfg_addr_fast;
    wire [63:0] rplu_cfg_data_fast;
    reg         rplu_cfg_toggle = 0;
    reg  [2:0]  rplu_cfg_toggle_sync = 0;
    reg         rplu_cfg_toggle_seen = 0;
    reg         rplu_cfg_wr_en = 0;
    reg  [2:0]  rplu_cfg_sel = 0;
    reg  [7:0]  rplu_cfg_material = 0;
    reg  [9:0]  rplu_cfg_addr = 0;
    reg  [63:0] rplu_cfg_data = 0;

    always @(posedge clk_50m or negedge rst_n) begin
        if (!rst_n)
            rplu_cfg_toggle <= 1'b0;
        else if (rplu_cfg_wr_en_fast)
            rplu_cfg_toggle <= ~rplu_cfg_toggle;
    end

    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            rplu_cfg_toggle_sync <= 3'b000;
            rplu_cfg_toggle_seen <= 1'b0;
            rplu_cfg_wr_en <= 1'b0;
            rplu_cfg_sel <= 3'd0;
            rplu_cfg_material <= 8'd0;
            rplu_cfg_addr <= 10'd0;
            rplu_cfg_data <= 64'd0;
        end else begin
            rplu_cfg_toggle_sync <= {rplu_cfg_toggle_sync[1:0], rplu_cfg_toggle};
            rplu_cfg_wr_en <= 1'b0;
            if (rplu_cfg_toggle_sync[2] != rplu_cfg_toggle_seen) begin
                rplu_cfg_toggle_seen <= rplu_cfg_toggle_sync[2];
                rplu_cfg_sel <= rplu_cfg_sel_fast;
                rplu_cfg_material <= rplu_cfg_material_fast;
                rplu_cfg_addr <= rplu_cfg_addr_fast;
                rplu_cfg_data <= rplu_cfg_data_fast;
                rplu_cfg_wr_en <= 1'b1;
            end
        end
    end

    // 0x13A5 means idle. 0xB1xx means an opcode is pending. Once the core
    // pulses inst_done, status becomes {opcode,destination} and stays there.
    reg         spi_inst_pending = 0;
    reg         spi_inst_done_seen = 0;
    reg  [7:0]  last_spi_opcode = 0;
    reg  [7:0]  last_spi_dest = 0;
    always @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) begin
            spi_inst_pending <= 1'b0;
            spi_inst_done_seen <= 1'b0;
            last_spi_opcode <= 8'd0;
            last_spi_dest <= 8'd0;
        end else begin
            if (inst_valid) begin
                spi_inst_pending <= 1'b1;
                spi_inst_done_seen <= 1'b0;
                last_spi_opcode <= inst_word[63:56];
                last_spi_dest <= inst_word[55:48];
            end
            if (inst_done && spi_inst_pending) begin
                spi_inst_pending <= 1'b0;
                spi_inst_done_seen <= 1'b1;
            end
        end
    end
    wire [15:0] southbridge_status = spi_inst_done_seen ?
                                      {last_spi_opcode, last_spi_dest} :
                                      (spi_inst_pending ?
                                       {8'hB1, last_spi_opcode} : 16'h13A5);

    spu_spi_slave u_spi (
        .clk(clk_50m),
        .rst_n(rst_n),
        .spi_cs_n(spi_cs_n),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),

        .manifold_state(manifold_state),
        .satellite_snaps(4'b0000),
        .is_janus_point(is_janus_point),
        .dissonance(quadrance_out[15:0]),

        .scale_table(scale_table),
        .scale_overflow(scale_overflow),

        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),

        .rplu_ratio_res(ratio_cmp_res),
        .rplu_ratio_valid(ratio_cmp_valid),

        .rplu_cfg_wr_en(rplu_cfg_wr_en_fast),
        .rplu_cfg_sel(rplu_cfg_sel_fast),
        .rplu_cfg_material(rplu_cfg_material_fast),
        .rplu_cfg_addr(rplu_cfg_addr_fast),
        .rplu_cfg_data(rplu_cfg_data_fast),

        .inst_valid(spi_inst_valid_fast),
        .inst_word(spi_inst_word_fast),

        .fifo_full(1'b0),
        // Bring-up signature plus persistent instruction completion tag.
        .laminar_index(southbridge_status),
        .turbulence(1'b0),
        .rplu_mode(1'b0),
        .sentinel_telemetry(512'd0)
    );

    // ── ISA Decoder (Wheeler-Feynman v1.0) ─────────────────────
    // Watches the instruction bus and produces decoded control signals
    // for the twin-register file, RAU, RPLU, and telemetry mux.
    wire        dec_instr_valid;
    wire [63:0] dec_instr_word;
    assign dec_instr_valid = inst_valid;
    assign dec_instr_word  = inst_word;

    wire [ 7:0] dec_opcode;
    wire [ 4:0] dec_dest, dec_srcA, dec_srcB;
    wire [ 9:0] dec_offset;
    wire [50:0] dec_immediate;
    wire        dec_rplu_cfg_wr_en;
    wire [ 2:0] dec_rplu_cfg_sel;
    wire [ 7:0] dec_rplu_cfg_material;
    wire [ 9:0] dec_rplu_cfg_addr;
    wire [63:0] dec_rplu_cfg_data;
    wire        dec_rau_start;
    wire [ 2:0] dec_rau_opcode;
    wire        dec_phslk_start, dec_invj_en, dec_phclr_en;
    wire        dec_branch_taken;
    wire [50:0] dec_branch_offset;
    wire        dec_mfold_en, dec_stat_en, dec_hex_en;
    wire        dec_reg_write_en;
    wire [ 4:0] dec_reg_write_addr;
    wire        dec_reg_offer_sel;
    wire [ 4:0] dec_reg_readA_addr, dec_reg_readB_addr;
    wire        dec_reg_readA_O_sel, dec_reg_readB_O_sel;
    wire        dec_halt, dec_sync;

    spu_isa_decoder u_decoder (
        .instr_word(dec_instr_word),
        .instr_valid(dec_instr_valid),
        .dec_opcode(dec_opcode),
        .dec_dest(dec_dest),
        .dec_srcA(dec_srcA),
        .dec_srcB(dec_srcB),
        .dec_offset(dec_offset),
        .dec_immediate(dec_immediate),
        .rplu_cfg_wr_en(dec_rplu_cfg_wr_en),
        .rplu_cfg_sel(dec_rplu_cfg_sel),
        .rplu_cfg_material(dec_rplu_cfg_material),
        .rplu_cfg_addr(dec_rplu_cfg_addr),
        .rplu_cfg_data(dec_rplu_cfg_data),
        .rau_start(dec_rau_start),
        .rau_opcode(dec_rau_opcode),
        .phslk_start(dec_phslk_start),
        .invj_en(dec_invj_en),
        .phclr_en(dec_phclr_en),
        .branch_taken(dec_branch_taken),
        .branch_offset(dec_branch_offset),
        .mfold_en(dec_mfold_en),
        .stat_en(dec_stat_en),
        .hex_en(dec_hex_en),
        .reg_write_en(dec_reg_write_en),
        .reg_write_addr(dec_reg_write_addr),
        .reg_offer_sel(dec_reg_offer_sel),
        .reg_readA_addr(dec_reg_readA_addr),
        .reg_readB_addr(dec_reg_readB_addr),
        .reg_readA_O_sel(dec_reg_readA_O_sel),
        .reg_readB_O_sel(dec_reg_readB_O_sel),
        .halt(dec_halt),
        .sync(dec_sync)
    );

    // ── SPU-13 Core ────────────────────────────────────────────
    // boot_done = 1: RP2350 owns boot sequencing entirely.
    // phinary_cfg: enable all logic, identity chirality.
    // No SDRAM, no lattice, no SOM — math-only for minimum LUT footprint.
    // RPLU is intentionally disabled for the first SPI demo; CMD 0xA5 still
    // exercises the southbridge receive path but does not hydrate a live RPLU.
    spu13_core #(
        .DEVICE("GW5A"),
        .ENABLE_RPLU(0),    // RAM16 placement limits on GW5A; enable on SDRAM boards
        .ENABLE_LATTICE(0),
        .ENABLE_MATH(1),
        .ENABLE_SEQUENCER(0),
        .ENABLE_CORE_SOM(0)
    ) u_core (
        .clk(clk_core),
        .rst_n(rst_n),
        .phi_8(phi_8),
        .phi_13(phi_13),
        .phi_21(phi_21),

        // RPLU fast-domain cfg from SPI slave
        .dec_fast_cfg_wr_en(rplu_cfg_wr_en),
        .dec_fast_cfg_sel(rplu_cfg_sel),
        .dec_fast_cfg_material(rplu_cfg_material),
        .dec_fast_cfg_addr(rplu_cfg_addr),
        .dec_fast_cfg_data(rplu_cfg_data),
        .phinary_cfg(16'h0001),

        // No boot ROM, no Pell vault, no manual rotor
        .prime_data(24'd0),
        .prime_addr(4'd0),
        .prime_we(1'b0),
        .boot_done(1'b1),
        .pell_data(32'd0),
        .pell_addr(3'd0),
        .pell_we(1'b0),
        .manual_rotor_en(1'b0),
        .manual_rotor_data(64'd0),

        // No SDRAM — manifold lives in registers only
        .mem_ready(1'b1),
        .mem_burst_rd(),
        .mem_burst_wr(),
        .mem_addr(),
        .mem_rd_manifold(832'd0),
        .mem_wr_manifold(),
        .mem_burst_done(1'b1),

        // Instruction port from SPI slave
        .inst_valid(inst_valid),
        .inst_word(inst_word),
        .inst_done(inst_done),

        .qr_commit_valid(qr_commit_valid),
        .qr_commit_lane(qr_commit_lane),
        .qr_commit_A(qr_commit_A), .qr_commit_B(qr_commit_B),
        .qr_commit_C(qr_commit_C), .qr_commit_D(qr_commit_D),

        // Telemetry to SPI slave
        .ratio_cmp_res(ratio_cmp_res),
        .ratio_cmp_valid(ratio_cmp_valid),
        .manifold_out(manifold_state),
        .scale_table_out(scale_table),
        .scale_overflow_out(scale_overflow),
        .is_janus_point(is_janus_point),
        .quadrance_out(quadrance_out),

        // Unused outputs
        .artery_wr_en(), .artery_wr_data(),
        .hex_valid(hex_valid), .hex_q(hex_q), .hex_r(hex_r),
        .current_axis_ptr(), .current_axis_data(),
        .bloom_complete(), .cycle_wrap(),
        .audio_mode(), .gasket_sum_out(),
        .rplu_dissoc_out(), .rplu_dissoc_mask_out(), .rplu_addr_out(),
        .i2s_bclk(), .i2s_lrclk(), .i2s_dout(),
        .laminar_flow_index_out(), .thermal_pressure_out(),
        .audio_p_out(), .audio_q_out(),
        .axiomatic_fault(), .fault_type(), .fault_count()
    );

    // ── LEDs ───────────────────────────────────────────────────
    reg [25:0] sys_blink = 0;
    always @(posedge clk_50m) sys_blink <= sys_blink + 1;
    assign led[0] = ~sys_blink[24];

    reg led1_q = 0;
    always @(posedge clk_core) if (hex_valid) led1_q <= ~led1_q;
    assign led[1] = ~led1_q;

    reg [19:0] spi_led_stretch = 0;
    always @(posedge clk_core)
        if (inst_valid)       spi_led_stretch <= 20'hFFFFF;
        else if (|spi_led_stretch) spi_led_stretch <= spi_led_stretch - 1;
    assign led[2] = ~(|spi_led_stretch);

endmodule

// Gowin global clock buffer primitive.
(* blackbox *)
module BUFG (
    input  wire I,
    output wire O
);
endmodule
