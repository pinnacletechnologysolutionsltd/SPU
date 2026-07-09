// spu13_tang25k_satellite_aggregator_probe.v — Tang 25K 13-satellite
// aggregator silicon probe
//
// On-fabric loopback, same pattern as spu_tang25k_whisper_v1_probe.v but
// through the full Arlinghaus meso-tier governor component: four whisper
// v1 emitters with distinct identities drive four of the aggregator's 13
// listener channels; the other nine lines idle high so the 3-miss deadman
// path is exercised for real. Self-checking FSM verifies:
//
//   1. status_table packing for all four driven satellites (som_valid,
//      som_label, snap, dissonance) against the driven constants.
//   2. som_labels nibble extraction.
//   3. worst_axis / worst_dissonance point at the hottest satellite.
//   4. After the deadman window: incoherent_count == 9, driven
//      satellites still coherent, idle satellites all flagged.
//   5. Command bus: opcode shifts out MSB-first with bus_cs holding the
//      addressed satellite, cmd_done pulses, chip-select deselects.
//
// UART output on pin C3 (115200 baud), one line every ~0.5 s:
//   SAGG:P W:2 I:9 E:00   PASS (worst axis 2, 9 incoherent idles)
//   SAGG:F W:x I:x E:xx   FAIL (error bitmask reported)
//
// Error bitmask: bit0 status_table, bit1 som_labels, bit2 worst axis,
// bit3 incoherent_count, bit4 driven sat false-incoherent, bit5 idle sat
// not incoherent, bit6 bus opcode shift, bit7 bus done/deselect.
//
// LEDs: heartbeat on led[0], PASS=led[1] off, FAIL=led[2] on.
//
// Parameters are overridable so the testbench can run an accelerated
// clock-per-bit ratio and whisper period; board defaults give real
// 115200-baud whisper traffic at 50 MHz.
//
// Single clock domain: unlike the two-module whisper probe, this design
// spreads 17 UART actors across the fabric, and a fabric-routed divided
// clock (sys_clk/4) accumulates enough skew to fail hold at that spread.
// The whisper fabric therefore runs directly on sys_clk — the UART
// modules only care about the CLK_HZ/BAUD ratio, and the loopback never
// leaves the FPGA, so the absolute whisper clock rate is irrelevant.

module spu13_tang25k_satellite_aggregator_probe #(
    parameter WHISPER_CLK_HZ = 50000000,             // = sys_clk
    parameter WHISPER_BAUD   = 115200,
    parameter PERIOD_CYCLES  = 120000                // > one 18-byte frame (~78.1k cycles)
) (
    input  wire       sys_clk,     // E2, 50 MHz
    output wire [2:0] led,         // L6, E8, D7 (active-low)
    output wire       uart_tx      // C3, 115200 baud
);

    localparam CLK_FREQ     = 50000000;
    localparam CLKS_PER_BIT = 434;                   // report UART, 115200 @ 50 MHz
    localparam LINE_PERIOD  = CLK_FREQ / 2;          // ~0.5 s between report lines
    localparam NUM_SATS     = 13;
    localparam NUM_DRIVEN   = 4;

    wire whisper_clk = sys_clk;

    // ── Reset ───────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge whisper_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1'b1;
    end

    // ── Driven satellite identities (golden constants) ──────────────
    // Satellite 2 carries the highest dissonance → expected worst_axis.
    localparam [3:0] NODE0 = 4'h1, NODE1 = 4'h2, NODE2 = 4'h3, NODE3 = 4'h4;
    localparam [2:0] FLG0 = 3'b001, FLG1 = 3'b000, FLG2 = 3'b101, FLG3 = 3'b011;
    localparam [7:0] DIS0 = 8'h20, DIS1 = 8'h50, DIS2 = 8'hAA, DIS3 = 8'h11;
    localparam [7:0] SOM0 = 8'h03, SOM1 = 8'h07, SOM2 = 8'h0C, SOM3 = 8'h09;
    localparam [3:0] EXPECT_WORST_AXIS = 4'd2;
    localparam [7:0] EXPECT_WORST_DISS = DIS2;
    localparam [3:0] EXPECT_INCOHERENT = 4'd9;       // 13 - 4 driven

    // Expected status_table entry per driven satellite:
    // {incoherent, som_valid, reserved, som_label[3:0], snap, dissonance}
    localparam [15:0] EXP_ST0 = {1'b0, 1'b1, 1'b0, SOM0[3:0], FLG0[0], DIS0};
    localparam [15:0] EXP_ST1 = {1'b0, 1'b1, 1'b0, SOM1[3:0], FLG1[0], DIS1};
    localparam [15:0] EXP_ST2 = {1'b0, 1'b1, 1'b0, SOM2[3:0], FLG2[0], DIS2};
    localparam [15:0] EXP_ST3 = {1'b0, 1'b1, 1'b0, SOM3[3:0], FLG3[0], DIS3};

    localparam [7:0] BUS_OPCODE   = 8'hB4;
    localparam [3:0] BUS_TARGET   = 4'd5;

    // ── Emitters (4 driven, 9 idle-high lines) ──────────────────────
    wire [NUM_DRIVEN-1:0] em_tx;

    spu_whisper_v1_emitter #(
        .CLK_HZ(WHISPER_CLK_HZ), .BAUD(WHISPER_BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)
    ) u_em0 (
        .clk(whisper_clk), .rst_n(rst_n),
        .is_laminar(1'b1), .node_id(NODE0), .flags_in(FLG0),
        .dissonance(DIS0), .som_label(SOM0),
        .tx(em_tx[0]), .busy()
    );
    spu_whisper_v1_emitter #(
        .CLK_HZ(WHISPER_CLK_HZ), .BAUD(WHISPER_BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)
    ) u_em1 (
        .clk(whisper_clk), .rst_n(rst_n),
        .is_laminar(1'b1), .node_id(NODE1), .flags_in(FLG1),
        .dissonance(DIS1), .som_label(SOM1),
        .tx(em_tx[1]), .busy()
    );
    spu_whisper_v1_emitter #(
        .CLK_HZ(WHISPER_CLK_HZ), .BAUD(WHISPER_BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)
    ) u_em2 (
        .clk(whisper_clk), .rst_n(rst_n),
        .is_laminar(1'b1), .node_id(NODE2), .flags_in(FLG2),
        .dissonance(DIS2), .som_label(SOM2),
        .tx(em_tx[2]), .busy()
    );
    spu_whisper_v1_emitter #(
        .CLK_HZ(WHISPER_CLK_HZ), .BAUD(WHISPER_BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)
    ) u_em3 (
        .clk(whisper_clk), .rst_n(rst_n),
        .is_laminar(1'b1), .node_id(NODE3), .flags_in(FLG3),
        .dissonance(DIS3), .som_label(SOM3),
        .tx(em_tx[3]), .busy()
    );

    wire [NUM_SATS-1:0] whisper_rx;
    assign whisper_rx = {{(NUM_SATS-NUM_DRIVEN){1'b1}}, em_tx};

    // ── DUT: full 13-listener aggregator ────────────────────────────
    reg        cmd_valid;
    wire       cmd_done, cmd_error;
    wire [3:0] bus_cs;
    wire       bus_sck, bus_mosi;
    wire [NUM_SATS*16-1:0] status_table;
    wire [3:0]  worst_axis;
    wire [7:0]  worst_dissonance;
    wire [3:0]  incoherent_count;
    wire [51:0] som_labels;

    spu13_satellite_aggregator #(
        .NUM_SATELLITES(NUM_SATS), .CLK_HZ(WHISPER_CLK_HZ),
        .BAUD(WHISPER_BAUD), .PERIOD_CYCLES(PERIOD_CYCLES)
    ) u_agg (
        .clk(whisper_clk), .rst_n(rst_n),
        .whisper_rx(whisper_rx),
        .bus_cs(bus_cs), .bus_sck(bus_sck), .bus_mosi(bus_mosi), .bus_miso(1'b0),
        .status_table(status_table),
        .worst_axis(worst_axis), .worst_dissonance(worst_dissonance),
        .incoherent_count(incoherent_count), .som_labels(som_labels),
        .cmd_valid(cmd_valid), .cmd_satellite(BUS_TARGET), .cmd_opcode(BUS_OPCODE),
        .cmd_done(cmd_done), .cmd_error(cmd_error)
    );

    // ── Self-check FSM (whisper_clk domain) ─────────────────────────
    localparam S_WAIT_FRAMES  = 4'd0;
    localparam S_CHECK_STATUS = 4'd1;
    localparam S_WAIT_DEADMAN = 4'd2;
    localparam S_CHECK_COHER  = 4'd3;
    localparam S_BUS_ISSUE    = 4'd4;
    localparam S_BUS_SYNC     = 4'd5;
    localparam S_BUS_CAPTURE  = 4'd6;
    localparam S_BUS_DONE     = 4'd7;
    localparam S_BUS_VERIFY   = 4'd8;
    localparam S_PASS         = 4'd9;
    localparam S_FAIL         = 4'd10;
    localparam S_BUS_SYNC2    = 4'd11;

    // All driven satellites have reported by 4 periods; idle deadman
    // (3 periods) has certainly fired by 8.
    localparam [31:0] T_CHECK_STATUS = PERIOD_CYCLES * 4;
    localparam [31:0] T_CHECK_COHER  = PERIOD_CYCLES * 8;

    reg [3:0]  probe_state = S_WAIT_FRAMES;
    reg [7:0]  fail_code = 8'd0;
    reg        pass_flag = 1'b0;
    reg        done_flag = 1'b0;
    reg [31:0] tick = 32'd0;
    reg [7:0]  bus_shift = 8'd0;
    reg [3:0]  bus_bits = 4'd0;
    reg [15:0] bus_guard = 16'd0;
    reg [3:0]  rep_worst = 4'd0;      // latched for the UART report
    reg [3:0]  rep_incoh = 4'd0;

    integer k;

    always @(posedge whisper_clk) begin
        if (!rst_n) begin
            probe_state <= S_WAIT_FRAMES;
            fail_code   <= 8'd0;
            pass_flag   <= 1'b0;
            done_flag   <= 1'b0;
            tick        <= 32'd0;
            cmd_valid   <= 1'b0;
            bus_shift   <= 8'd0;
            bus_bits    <= 4'd0;
            bus_guard   <= 16'd0;
            rep_worst   <= 4'd0;
            rep_incoh   <= 4'd0;
        end else begin
            tick <= tick + 32'd1;

            case (probe_state)
                S_WAIT_FRAMES: begin
                    if (tick >= T_CHECK_STATUS)
                        probe_state <= S_CHECK_STATUS;
                end

                S_CHECK_STATUS: begin
                    if (status_table[0*16 +: 16] !== EXP_ST0 ||
                        status_table[1*16 +: 16] !== EXP_ST1 ||
                        status_table[2*16 +: 16] !== EXP_ST2 ||
                        status_table[3*16 +: 16] !== EXP_ST3)
                        fail_code[0] <= 1'b1;
                    if (som_labels[0*4 +: 4] !== SOM0[3:0] ||
                        som_labels[1*4 +: 4] !== SOM1[3:0] ||
                        som_labels[2*4 +: 4] !== SOM2[3:0] ||
                        som_labels[3*4 +: 4] !== SOM3[3:0])
                        fail_code[1] <= 1'b1;
                    if (worst_axis !== EXPECT_WORST_AXIS ||
                        worst_dissonance !== EXPECT_WORST_DISS)
                        fail_code[2] <= 1'b1;
                    probe_state <= S_WAIT_DEADMAN;
                end

                S_WAIT_DEADMAN: begin
                    if (tick >= T_CHECK_COHER)
                        probe_state <= S_CHECK_COHER;
                end

                S_CHECK_COHER: begin
                    if (incoherent_count !== EXPECT_INCOHERENT)
                        fail_code[3] <= 1'b1;
                    for (k = 0; k < NUM_DRIVEN; k = k + 1)
                        if (status_table[k*16 + 15])
                            fail_code[4] <= 1'b1;   // driven sat false-incoherent
                    for (k = NUM_DRIVEN; k < NUM_SATS; k = k + 1)
                        if (!status_table[k*16 + 15])
                            fail_code[5] <= 1'b1;   // idle sat not incoherent
                    rep_worst <= worst_axis;
                    rep_incoh <= incoherent_count;
                    probe_state <= S_BUS_ISSUE;
                end

                S_BUS_ISSUE: begin
                    cmd_valid   <= 1'b1;
                    probe_state <= S_BUS_SYNC;
                end

                S_BUS_SYNC: begin
                    // Aggregator registers BUS_IDLE→BUS_SEND on this edge.
                    cmd_valid   <= 1'b0;
                    bus_shift   <= 8'd0;
                    bus_bits    <= 4'd0;
                    probe_state <= S_BUS_SYNC2;
                end

                S_BUS_SYNC2: begin
                    // Aggregator registers the first opcode bit onto
                    // bus_mosi on this edge; it is sampleable next cycle.
                    probe_state <= S_BUS_CAPTURE;
                end

                S_BUS_CAPTURE: begin
                    bus_shift <= {bus_shift[6:0], bus_mosi};
                    if (bus_cs !== BUS_TARGET)
                        fail_code[7] <= 1'b1;       // deselected mid-transfer
                    if (bus_bits == 4'd7) begin
                        bus_guard   <= 16'd0;
                        probe_state <= S_BUS_DONE;
                    end else begin
                        bus_bits <= bus_bits + 4'd1;
                    end
                end

                S_BUS_DONE: begin
                    bus_guard <= bus_guard + 16'd1;
                    if (cmd_done)
                        probe_state <= S_BUS_VERIFY;
                    else if (bus_guard == 16'hFFFF) begin
                        fail_code[7] <= 1'b1;       // cmd_done never pulsed
                        probe_state  <= S_BUS_VERIFY;
                    end
                end

                S_BUS_VERIFY: begin
                    if (bus_shift !== BUS_OPCODE)
                        fail_code[6] <= 1'b1;
                    if (bus_cs !== 4'hF)
                        fail_code[7] <= 1'b1;       // not deselected after done
                    probe_state <= (fail_code == 8'd0 && bus_shift === BUS_OPCODE
                                    && bus_cs === 4'hF) ? S_PASS : S_FAIL;
                end

                S_PASS: begin
                    pass_flag <= 1'b1;
                    done_flag <= 1'b1;
                end

                S_FAIL: begin
                    pass_flag <= 1'b0;
                    done_flag <= 1'b1;
                end

                default: probe_state <= S_FAIL;
            endcase
        end
    end

    // ── LED heartbeat (sys_clk domain; active-low) ─────────────────
    reg [24:0] led_cnt = 25'd0;
    always @(posedge sys_clk) led_cnt <= led_cnt + 25'd1;

    assign led[0] = ~(led_cnt[24]);              // heartbeat ~1.5 Hz
    assign led[1] = ~(done_flag && pass_flag);   // off when pass
    assign led[2] = ~(done_flag && !pass_flag);  // on when fail

    // ── Bit-bang UART TX report (sys_clk domain, 115200 baud) ──────
    function [7:0] hex_nibble;
        input [3:0] n;
        begin
            hex_nibble = (n < 4'd10) ? (8'h30 + n) : (8'h37 + n);
        end
    endfunction

    // "SAGG:P W:2 I:9 E:00\n" (20 bytes)
    function [7:0] msg_byte;
        input [7:0] idx;
        begin
            case (idx)
                8'd0:  msg_byte = 8'h53;                          // S
                8'd1:  msg_byte = 8'h41;                          // A
                8'd2:  msg_byte = 8'h47;                          // G
                8'd3:  msg_byte = 8'h47;                          // G
                8'd4:  msg_byte = 8'h3A;                          // :
                8'd5:  msg_byte = pass_flag ? 8'h50 : 8'h46;      // P or F
                8'd6:  msg_byte = 8'h20;                          // space
                8'd7:  msg_byte = 8'h57;                          // W
                8'd8:  msg_byte = 8'h3A;                          // :
                8'd9:  msg_byte = hex_nibble(rep_worst);
                8'd10: msg_byte = 8'h20;                          // space
                8'd11: msg_byte = 8'h49;                          // I
                8'd12: msg_byte = 8'h3A;                          // :
                8'd13: msg_byte = hex_nibble(rep_incoh);
                8'd14: msg_byte = 8'h20;                          // space
                8'd15: msg_byte = 8'h45;                          // E
                8'd16: msg_byte = 8'h3A;                          // :
                8'd17: msg_byte = hex_nibble(fail_code[7:4]);
                8'd18: msg_byte = hex_nibble(fail_code[3:0]);
                8'd19: msg_byte = 8'h0A;                          // \n
                default: msg_byte = 8'h00;
            endcase
        end
    endfunction

    reg        uart_busy = 1'b0;
    reg [15:0] uart_bit_cnt = 16'd0;
    reg [3:0]  uart_bit_idx = 4'd0;
    reg [9:0]  uart_shift = 10'd0;
    reg        uart_tx_reg = 1'b1;
    reg [31:0] line_timer = 32'd0;
    reg [4:0]  msg_idx = 5'd0;
    assign uart_tx = uart_tx_reg;

    always @(posedge sys_clk) begin
        if (!rst_cnt[7]) begin
            uart_busy    <= 1'b0;
            uart_bit_cnt <= 16'd0;
            uart_bit_idx <= 4'd0;
            uart_shift   <= 10'd0;
            uart_tx_reg  <= 1'b1;
            line_timer   <= 32'd0;
            msg_idx      <= 5'd0;
        end else begin
            if (uart_busy) begin
                if (uart_bit_cnt < CLKS_PER_BIT - 1) begin
                    uart_bit_cnt <= uart_bit_cnt + 16'd1;
                end else begin
                    uart_bit_cnt <= 16'd0;
                    if (uart_bit_idx > 0) begin
                        uart_tx_reg  <= uart_shift[0];
                        uart_shift   <= {1'b1, uart_shift[9:1]};
                        uart_bit_idx <= uart_bit_idx - 4'd1;
                    end else begin
                        uart_busy   <= 1'b0;
                        uart_tx_reg <= 1'b1;
                    end
                end
            end else if (line_timer == 0) begin
                if (msg_idx < 5'd20) begin
                    uart_shift   <= {1'b1, msg_byte({3'd0, msg_idx}), 1'b0};
                    uart_bit_idx <= 4'd10;
                    uart_bit_cnt <= 16'd0;
                    uart_busy    <= 1'b1;
                    msg_idx      <= msg_idx + 5'd1;
                end else begin
                    line_timer <= LINE_PERIOD;
                    msg_idx    <= 5'd0;
                end
            end else begin
                line_timer <= line_timer - 32'd1;
            end
        end
    end

endmodule
