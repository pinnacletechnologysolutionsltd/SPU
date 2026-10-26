// spu13_tang25k_neuro_sidecar_probe.v -- Tang 25K neuro sidecar adapter probe.
//
// Self-checking board proof for the SPI-visible neuro epoch sidecar adapter.
// The on-board sequencer drives the adapter through all four opcodes
// (NEURO_CFG, NEURO_START, NEURO_SPIKE, NEURO_READ) and reports PASS/FAIL
// over UART.  This validates the adapter's control path end-to-end without
// requiring an external SPI master.
//
// Two epoch instances are tested:
//   epoch_a  —  2-neuron, EPOCH_CYCLES=6 (accept + reject tests)
//   epoch_b  —  1-neuron, EPOCH_CYCLES=5, COUNT_WIDTH=2 (overflow test)

module spu13_tang25k_neuro_sidecar_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;  // 115200 baud at 50 MHz
    localparam START_DELAY = CLK_FREQ / 2;
    localparam LINE_PERIOD = CLK_FREQ / 5;

    // ── Reset ────────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1'b1;
    end

    // ── Epoch A: 2-neuron adapter ────────────────────────────────────
    reg        epA_inst_valid;
    reg [63:0] epA_inst_word;
    wire       epA_inst_claimed;
    wire       epA_busy, epA_error;
    wire       epA_qr_valid;
    wire [3:0] epA_qr_lane;
    wire [63:0] epA_qr_A, epA_qr_B;
    wire       epA_epoch_busy, epA_epoch_done;
    wire       epA_accepted, epA_rejected, epA_norm_ok, epA_overflow;
    wire       epA_latched_accepted, epA_latched_rejected;
    wire       epA_latched_overflow, epA_latched_norm_ok;
    wire [1:0] epA_token_mask;
    wire [15:0] epA_spike_total;
    wire [9:0] epA_norm_value, epA_commit_a, epA_commit_b;

    spu13_neuro_sidecar_adapter #(
        .NUM_NEURONS(2), .POT_WIDTH(8), .COUNT_WIDTH(4),
        .EPOCH_CYCLES(6), .EPOCH_COUNT_WIDTH(3),
        .LEAK(1), .RESET_VAL(0), .L_P(521), .L_P_BITS(10)
    ) u_epochA (
        .clk(sys_clk), .rst_n(rst_n),
        .inst_valid(epA_inst_valid), .inst_word(epA_inst_word),
        .inst_claimed(epA_inst_claimed),
        .busy(epA_busy), .error(epA_error),
        .qr_commit_valid(epA_qr_valid), .qr_commit_lane(epA_qr_lane),
        .qr_commit_A(epA_qr_A), .qr_commit_B(epA_qr_B),
        .qr_commit_C(), .qr_commit_D(),
        .epoch_busy(epA_epoch_busy), .epoch_done(epA_epoch_done),
        .accepted(epA_accepted), .rejected(epA_rejected),
        .norm_ok(epA_norm_ok), .overflow_fault(epA_overflow),
        .epoch_latched_accepted(epA_latched_accepted),
        .epoch_latched_rejected(epA_latched_rejected),
        .epoch_latched_overflow(epA_latched_overflow),
        .epoch_latched_norm_ok(epA_latched_norm_ok),
        .epoch_token_mask(epA_token_mask),
        .epoch_spike_total(epA_spike_total),
        .epoch_norm_value(epA_norm_value),
        .epoch_commit_a(epA_commit_a), .epoch_commit_b(epA_commit_b)
    );

    // ── Epoch B: 1-neuron overflow adapter ───────────────────────────
    reg        epB_inst_valid;
    reg [63:0] epB_inst_word;
    wire       epB_inst_claimed;
    wire       epB_busy, epB_error;
    wire       epB_qr_valid;
    wire [3:0] epB_qr_lane;
    wire [63:0] epB_qr_A, epB_qr_B;
    wire       epB_epoch_busy, epB_epoch_done;
    wire       epB_accepted, epB_rejected, epB_norm_ok, epB_overflow;
    wire       epB_latched_accepted, epB_latched_rejected;
    wire       epB_latched_overflow, epB_latched_norm_ok;
    wire [15:0] epB_spike_total;
    wire [9:0] epB_norm_value, epB_commit_a, epB_commit_b;

    spu13_neuro_sidecar_adapter #(
        .NUM_NEURONS(1), .POT_WIDTH(4), .COUNT_WIDTH(2),
        .EPOCH_CYCLES(5), .EPOCH_COUNT_WIDTH(3),
        .LEAK(0), .RESET_VAL(0), .L_P(521), .L_P_BITS(10)
    ) u_epochB (
        .clk(sys_clk), .rst_n(rst_n),
        .inst_valid(epB_inst_valid), .inst_word(epB_inst_word),
        .inst_claimed(epB_inst_claimed),
        .busy(epB_busy), .error(epB_error),
        .qr_commit_valid(epB_qr_valid), .qr_commit_lane(epB_qr_lane),
        .qr_commit_A(epB_qr_A), .qr_commit_B(epB_qr_B),
        .qr_commit_C(), .qr_commit_D(),
        .epoch_busy(epB_epoch_busy), .epoch_done(epB_epoch_done),
        .accepted(epB_accepted), .rejected(epB_rejected),
        .norm_ok(epB_norm_ok), .overflow_fault(epB_overflow),
        .epoch_latched_accepted(epB_latched_accepted),
        .epoch_latched_rejected(epB_latched_rejected),
        .epoch_latched_overflow(epB_latched_overflow),
        .epoch_latched_norm_ok(epB_latched_norm_ok),
        .epoch_token_mask(),
        .epoch_spike_total(epB_spike_total),
        .epoch_norm_value(epB_norm_value),
        .epoch_commit_a(epB_commit_a), .epoch_commit_b(epB_commit_b)
    );

    // ── Sequencer with explicit state machine ────────────────────────
    // (No task-based timing controls; Yosys can't synthesize @ inside tasks.)
    localparam [8:0] S_RESET          = 9'd0;
    localparam [8:0] S_A_CFG0         = 9'd1;
    localparam [8:0] S_A_CFG0_W       = 9'd2;
    localparam [8:0] S_A_CFG1         = 9'd3;
    localparam [8:0] S_A_CFG1_W       = 9'd4;
    localparam [8:0] S_A_START        = 9'd5;
    localparam [8:0] S_A_WAIT         = 9'd6;
    localparam [8:0] S_A_CHECK        = 9'd7;
    localparam [8:0] S_A_READ         = 9'd8;
    localparam [8:0] S_A_READ_W       = 9'd9;
    localparam [8:0] S_A_CHECK_READ   = 9'd10;
    localparam [8:0] S_A_START2       = 9'd11;
    localparam [8:0] S_A_WAIT2        = 9'd12;
    localparam [8:0] S_A_CHECK2       = 9'd13;
    localparam [8:0] S_A_READ2        = 9'd14;
    localparam [8:0] S_A_READ2_W      = 9'd15;
    localparam [8:0] S_A_CHECK_READ2  = 9'd16;
    localparam [8:0] S_B_CFG0         = 9'd17;
    localparam [8:0] S_B_CFG0_W       = 9'd18;
    localparam [8:0] S_B_START        = 9'd19;
    localparam [8:0] S_B_SPIKE_LOOP   = 9'd20;
    localparam [8:0] S_B_SPIKE_WAIT   = 9'd21;
    localparam [8:0] S_B_WAIT         = 9'd22;
    localparam [8:0] S_B_CHECK        = 9'd23;
    localparam [8:0] S_PASS           = 9'd24;
    localparam [8:0] S_FAIL           = 9'd25;

    // One-hot state; first cycle of each instruction asserts inst_valid,
    // second cycle deasserts.
    reg [8:0] test_state = S_RESET;
    reg [3:0] test_id = 4'd0;
    reg [7:0] fail_code = 8'd0;
    reg       all_pass = 1'b1;
    reg [3:0] b_spike_count = 4'd0;
    reg [3:0] wait_count = 4'd0;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            test_id <= 4'd0;
            fail_code <= 8'd0;
            all_pass <= 1'b1;
            epA_inst_valid <= 1'b0;
            epA_inst_word <= 64'd0;
            epB_inst_valid <= 1'b0;
            epB_inst_word <= 64'd0;
            b_spike_count <= 4'd0;
            wait_count <= 4'd0;
        end else begin
            epA_inst_valid <= 1'b0;
            epB_inst_valid <= 1'b0;

            case (test_state)
                S_RESET: begin
                    if (rst_cnt == 8'hFF) test_state <= S_A_CFG0;
                end

                // ── Epoch A CFG: neuron0 w=5 t=5 ─────────────────────
                S_A_CFG0: begin
                    test_id <= 4'd1;
                    epA_inst_valid <= 1'b1;
                    epA_inst_word <= {8'hE0, 4'd0, {2'd0, 8'd5}, {2'd0, 8'd5}, 10'd0, 22'd0};
                    test_state <= S_A_CFG0_W;
                end
                S_A_CFG0_W: begin
                    test_state <= S_A_CFG1;
                end

                // ── Epoch A CFG: neuron1 w=3 t=5 ─────────────────────
                S_A_CFG1: begin
                    epA_inst_valid <= 1'b1;
                    epA_inst_word <= {8'hE0, 4'd1, {2'd0, 8'd3}, {2'd0, 8'd5}, 10'd0, 22'd0};
                    test_state <= S_A_CFG1_W;
                end
                S_A_CFG1_W: begin
                    test_state <= S_A_START;
                end

                // ── Epoch A START with initial_spike=2'b11 ───────────
                S_A_START: begin
                    epA_inst_valid <= 1'b1;
                    // expected_norm=171, fallback=(7,8), initial_spike=3
                    epA_inst_word <= {8'hE1, 4'd0, 10'd171, 10'd7, 10'd8, 10'd3, 12'd0};
                    test_state <= S_A_WAIT;
                end
                S_A_WAIT: begin
                    if (epA_epoch_done) begin
                        test_state <= S_A_CHECK;
                    end
                end
                S_A_CHECK: begin
                    if (epA_latched_accepted && !epA_latched_rejected &&
                        epA_latched_norm_ok && !epA_latched_overflow &&
                        epA_spike_total == 16'd9 &&
                        epA_commit_a == 10'd12 && epA_commit_b == 10'd9) begin
                        test_state <= S_A_READ;
                    end else begin
                        fail_code <= 8'hA1; all_pass <= 1'b0; test_state <= S_FAIL;
                    end
                end

                // ── Epoch A NEURO_READ lane 5 ────────────────────────
                S_A_READ: begin
                    epA_inst_valid <= 1'b1;
                    epA_inst_word <= {8'hE3, 4'd5, 10'd0, 10'd0, 10'd0, 10'd0, 12'd0};
                    wait_count <= 4'd0;
                    test_state <= S_A_READ_W;
                end
                S_A_READ_W: begin
                    // Board sequencer issues inst_valid from a flop, so the
                    // adapter sees NEURO_READ one clock later than the state
                    // that launches it.  Wait until READY has had a clock to
                    // register qr_commit_valid before checking the readback.
                    if (wait_count == 4'd1) begin
                        test_state <= S_A_CHECK_READ;
                    end else begin
                        wait_count <= wait_count + 1'b1;
                    end
                end
                S_A_CHECK_READ: begin
                    if (epA_qr_valid && epA_qr_lane == 4'd5 &&
                        epA_qr_A[9:0] == 10'd12 && epA_qr_A[41:32] == 10'd9) begin
                        test_state <= S_A_START2;
                    end else begin
                        fail_code <= 8'hA2; all_pass <= 1'b0; test_state <= S_FAIL;
                    end
                end

                // ── Epoch A START2: reject (expected_norm=99 wrong) ──
                S_A_START2: begin
                    test_id <= 4'd2;
                    epA_inst_valid <= 1'b1;
                    epA_inst_word <= {8'hE1, 4'd0, 10'd99, 10'd7, 10'd8, 10'd3, 12'd0};
                    test_state <= S_A_WAIT2;
                end
                S_A_WAIT2: begin
                    if (epA_epoch_done) begin
                        test_state <= S_A_CHECK2;
                    end
                end
                S_A_CHECK2: begin
                    if (!epA_latched_accepted && epA_latched_rejected &&
                        !epA_latched_norm_ok &&
                        epA_commit_a == 10'd7 && epA_commit_b == 10'd8) begin
                        test_state <= S_A_READ2;
                    end else begin
                        fail_code <= 8'hB2; all_pass <= 1'b0; test_state <= S_FAIL;
                    end
                end

                // ── Epoch A NEURO_READ2 (check rejected bit) ─────────
                S_A_READ2: begin
                    epA_inst_valid <= 1'b1;
                    epA_inst_word <= {8'hE3, 4'd0, 10'd0, 10'd0, 10'd0, 10'd0, 12'd0};
                    wait_count <= 4'd0;
                    test_state <= S_A_READ2_W;
                end
                S_A_READ2_W: begin
                    if (wait_count == 4'd1) begin
                        test_state <= S_A_CHECK_READ2;
                    end else begin
                        wait_count <= wait_count + 1'b1;
                    end
                end
                S_A_CHECK_READ2: begin
                    if (epA_qr_valid && epA_qr_B[62] &&  // rejected bit
                        epA_qr_A[9:0] == 10'd7 && epA_qr_A[41:32] == 10'd8) begin
                        test_state <= S_B_CFG0;
                    end else begin
                        fail_code <= 8'hB3; all_pass <= 1'b0; test_state <= S_FAIL;
                    end
                end

                // ── Epoch B: overflow → fallback ─────────────────────
                S_B_CFG0: begin
                    test_id <= 4'd3;
                    epB_inst_valid <= 1'b1;
                    epB_inst_word <= {8'hE0, 4'd0, {6'd0, 4'd1}, {6'd0, 4'd1}, 10'd0, 22'd0};
                    test_state <= S_B_CFG0_W;
                end
                S_B_CFG0_W: begin
                    test_state <= S_B_START;
                end
                S_B_START: begin
                    epB_inst_valid <= 1'b1;
                    // expected_norm=9, fallback=(7,8), initial_spike=1
                    epB_inst_word <= {8'hE1, 4'd0, 10'd9, 10'd7, 10'd8, 10'd1, 12'd0};
                    b_spike_count <= 4'd0;
                    test_state <= S_B_SPIKE_LOOP;
                end
                S_B_SPIKE_LOOP: begin
                    if (b_spike_count < 5) begin
                        epB_inst_valid <= 1'b1;
                        epB_inst_word <= {8'hE2, 4'd0, 10'd0, 10'd0, 10'd1, 10'd0, 12'd0};
                        b_spike_count <= b_spike_count + 1'b1;
                        test_state <= S_B_SPIKE_WAIT;
                    end else begin
                        test_state <= S_B_WAIT;
                    end
                end
                S_B_SPIKE_WAIT: begin
                    test_state <= S_B_SPIKE_LOOP;
                end
                S_B_WAIT: begin
                    if (epB_epoch_done || epB_latched_accepted ||
                        epB_latched_rejected || epB_latched_overflow) begin
                        test_state <= S_B_CHECK;
                    end
                end
                S_B_CHECK: begin
                    if (!epB_latched_accepted && epB_latched_rejected &&
                        epB_latched_overflow &&
                        epB_commit_a == 10'd7 && epB_commit_b == 10'd8) begin
                        test_state <= S_PASS;
                    end else begin
                        fail_code <= 8'hC3; all_pass <= 1'b0; test_state <= S_FAIL;
                    end
                end

                S_PASS: begin end
                S_FAIL: begin end
                default: begin fail_code <= 8'hEE; all_pass <= 1'b0; test_state <= S_FAIL; end
            endcase
        end
    end

    // ── LEDs ─────────────────────────────────────────────────────────
    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) blink_cnt <= blink_cnt + 1'b1;
    assign led[0] = ~blink_cnt[24];                // heartbeat
    assign led[1] = ~(test_state == S_PASS);       // off = PASS
    assign led[2] = ~(test_state == S_FAIL);       // off = FAIL

    // ── UART telemetry ───────────────────────────────────────────────
    wire [7:0] status_char =
        (test_state == S_PASS) ? "P" : (test_state == S_FAIL) ? "F" : ".";

    function [7:0] hex2ascii;
        input [3:0] h;
        begin
            hex2ascii = (h < 4'd10) ? (8'h30 + h) : (8'h37 + h);
        end
    endfunction

    function [7:0] msg_byte;
        input [5:0] idx;
        begin
            case (idx)
                6'd0:  msg_byte = "N";
                6'd1:  msg_byte = ":";
                6'd2:  msg_byte = status_char;
                6'd3:  msg_byte = " ";
                6'd4:  msg_byte = "T";
                6'd5:  msg_byte = ":";
                6'd6:  msg_byte = hex2ascii(test_id);
                6'd7:  msg_byte = " ";
                6'd8:  msg_byte = "E";
                6'd9:  msg_byte = ":";
                6'd10: msg_byte = hex2ascii(fail_code[7:4]);
                6'd11: msg_byte = hex2ascii(fail_code[3:0]);
                6'd12: msg_byte = 8'h0D;
                6'd13: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits_remaining = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg [5:0]  msg_idx = 6'd0;
    reg        tx_busy = 1'b0;
    reg        line_active = 1'b0;
    reg        launch_line = 1'b0;
    reg [27:0] start_cnt = 28'd0;
    reg [27:0] line_timer = 28'd0;
    reg        start_ready = 1'b0;

    assign uart_tx = tx_shift[0];

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF;
            tx_bits_remaining <= 4'd0;
            baud_cnt <= 16'd0;
            msg_idx <= 6'd0;
            tx_busy <= 1'b0;
            line_active <= 1'b0;
            launch_line <= 1'b0;
            start_cnt <= 28'd0;
            line_timer <= 28'd0;
            start_ready <= 1'b0;
        end else if (tx_busy) begin
            if (baud_cnt < CLKS_PER_BIT - 1) begin
                baud_cnt <= baud_cnt + 1'b1;
            end else begin
                baud_cnt <= 16'd0;
                tx_shift <= {1'b1, tx_shift[9:1]};
                if (tx_bits_remaining == 4'd1) begin
                    tx_busy <= 1'b0;
                    tx_bits_remaining <= 4'd0;
                    if (msg_idx == 6'd13) begin
                        msg_idx <= 6'd0;
                        line_active <= 1'b0;
                    end else begin
                        msg_idx <= msg_idx + 1'b1;
                    end
                end else begin
                    tx_bits_remaining <= tx_bits_remaining - 1'b1;
                end
            end
        end else if (line_active || launch_line) begin
            launch_line <= 1'b0;
            line_active <= 1'b1;
            tx_shift <= {1'b1, msg_byte(msg_idx), 1'b0};
            tx_bits_remaining <= 4'd10;
            baud_cnt <= 16'd0;
            tx_busy <= 1'b1;
        end else if (!start_ready) begin
            if (start_cnt < START_DELAY - 1) begin
                start_cnt <= start_cnt + 1'b1;
            end else begin
                start_ready <= 1'b1;
            end
        end else if (line_timer < LINE_PERIOD - 1) begin
            line_timer <= line_timer + 1'b1;
        end else begin
            line_timer <= 28'd0;
            launch_line <= 1'b1;
        end
    end
endmodule
