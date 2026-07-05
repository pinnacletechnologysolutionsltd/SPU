// spu13_tang25k_neuro_guard_probe.v -- Tang 25K neuro-safe guard probe.
//
// Standalone board proof for the deterministic neuro epoch sidecar.  It runs
// four self-checking epochs and reports PASS/FAIL plus the last guard vector
// over UART.  No SPU-13 core, SPI, flash, or external event hardware is used.

module spu13_tang25k_neuro_guard_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;  // 115200 baud at 50 MHz
    localparam START_DELAY = CLK_FREQ / 2;
    localparam LINE_PERIOD = CLK_FREQ / 5;

    // Reset
    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            rst_cnt <= rst_cnt + 1'b1;
        end
    end

    // Advance the guard domain at 1/8 board clock.  The registers are still
    // clocked by sys_clk, but state only changes on probe_tick, giving the
    // combinational norm/reduction path a deterministic multicycle window.
    reg [2:0] probe_div = 3'd0;
    always @(posedge sys_clk) begin
        if (!rst_n) begin
            probe_div <= 3'd0;
        end else begin
            probe_div <= probe_div + 3'd1;
        end
    end
    wire probe_tick = (probe_div == 3'd0);

    // Main two-neuron epoch sidecar.
    reg        epoch_start = 1'b0;
    reg [1:0]  spike_in = 2'b00;
    reg [15:0] weights = {8'd5, 8'd3};
    reg [15:0] thresholds = {8'd5, 8'd5};
    reg [9:0]  expected_norm = 10'd11;
    reg [9:0]  fallback_a = 10'd7;
    reg [9:0]  fallback_b = 10'd8;

    wire        busy;
    wire        done;
    wire        accepted;
    wire        rejected;
    wire        norm_ok;
    wire        overflow_fault;
    wire [1:0]  token_mask;
    wire [15:0] spike_total;
    wire [9:0]  proposal_a;
    wire [9:0]  proposal_b;
    wire [9:0]  norm_value;
    wire [9:0]  commit_a;
    wire [9:0]  commit_b;

    spu13_neuro_epoch_sidecar #(
        .NUM_NEURONS(2),
        .POT_WIDTH(8),
        .COUNT_WIDTH(4),
        .EPOCH_CYCLES(2),
        .EPOCH_COUNT_WIDTH(2),
        .LEAK(1),
        .RESET_VAL(0),
        .L_P(521),
        .L_P_BITS(10)
    ) u_epoch (
        .clk(sys_clk),
        .rst_n(rst_n),
        .clk_en(probe_tick),
        .start_epoch(epoch_start),
        .spike_in(spike_in),
        .weights(weights),
        .thresholds(thresholds),
        .expected_norm(expected_norm),
        .fallback_a(fallback_a),
        .fallback_b(fallback_b),
        .busy(busy),
        .done(done),
        .accepted(accepted),
        .rejected(rejected),
        .norm_ok(norm_ok),
        .overflow_fault(overflow_fault),
        .token_mask(token_mask),
        .spike_total(spike_total),
        .proposal_a(proposal_a),
        .proposal_b(proposal_b),
        .norm_value(norm_value),
        .commit_a(commit_a),
        .commit_b(commit_b)
    );

    // Saturation sidecar uses a tiny counter to prove overflow forces fallback.
    reg overflow_start = 1'b0;
    reg overflow_spike = 1'b0;

    wire        overflow_done;
    wire        overflow_accepted;
    wire        overflow_rejected;
    wire        overflow_norm_ok;
    wire        overflow_fault_seen;
    wire [15:0] overflow_total;
    wire [9:0]  overflow_proposal_a;
    wire [9:0]  overflow_proposal_b;
    wire [9:0]  overflow_norm_value;
    wire [9:0]  overflow_commit_a;
    wire [9:0]  overflow_commit_b;

    spu13_neuro_epoch_sidecar #(
        .NUM_NEURONS(1),
        .POT_WIDTH(4),
        .COUNT_WIDTH(2),
        .EPOCH_CYCLES(5),
        .EPOCH_COUNT_WIDTH(3),
        .LEAK(0),
        .RESET_VAL(0),
        .L_P(521),
        .L_P_BITS(10)
    ) u_overflow_epoch (
        .clk(sys_clk),
        .rst_n(rst_n),
        .clk_en(probe_tick),
        .start_epoch(overflow_start),
        .spike_in(overflow_spike),
        .weights(4'd1),
        .thresholds(4'd1),
        .expected_norm(10'd9),
        .fallback_a(10'd7),
        .fallback_b(10'd8),
        .busy(),
        .done(overflow_done),
        .accepted(overflow_accepted),
        .rejected(overflow_rejected),
        .norm_ok(overflow_norm_ok),
        .overflow_fault(overflow_fault_seen),
        .token_mask(),
        .spike_total(overflow_total),
        .proposal_a(overflow_proposal_a),
        .proposal_b(overflow_proposal_b),
        .norm_value(overflow_norm_value),
        .commit_a(overflow_commit_a),
        .commit_b(overflow_commit_b)
    );

    // Test sequencer.
    localparam [5:0] S_RESET          = 6'd0;
    localparam [5:0] S_ACCEPT_ARM     = 6'd1;
    localparam [5:0] S_ACCEPT_C0      = 6'd2;
    localparam [5:0] S_ACCEPT_C1      = 6'd3;
    localparam [5:0] S_ACCEPT_C2      = 6'd4;
    localparam [5:0] S_ACCEPT_CHECK   = 6'd5;
    localparam [5:0] S_REJECT_ARM     = 6'd6;
    localparam [5:0] S_REJECT_C0      = 6'd7;
    localparam [5:0] S_REJECT_C1      = 6'd8;
    localparam [5:0] S_REJECT_C2      = 6'd9;
    localparam [5:0] S_REJECT_CHECK   = 6'd10;
    localparam [5:0] S_CARRY_ARM      = 6'd11;
    localparam [5:0] S_CARRY_C0       = 6'd12;
    localparam [5:0] S_CARRY_C1       = 6'd13;
    localparam [5:0] S_CARRY_C2       = 6'd14;
    localparam [5:0] S_CARRY_CHECK    = 6'd15;
    localparam [5:0] S_OVERFLOW_ARM   = 6'd16;
    localparam [5:0] S_OVERFLOW_C0    = 6'd17;
    localparam [5:0] S_OVERFLOW_C1    = 6'd18;
    localparam [5:0] S_OVERFLOW_C2    = 6'd19;
    localparam [5:0] S_OVERFLOW_C3    = 6'd20;
    localparam [5:0] S_OVERFLOW_C4    = 6'd21;
    localparam [5:0] S_OVERFLOW_C5    = 6'd22;
    localparam [5:0] S_OVERFLOW_CHECK = 6'd23;
    localparam [5:0] S_PASS           = 6'd24;
    localparam [5:0] S_FAIL           = 6'd25;

    reg [5:0] test_state = S_RESET;
    reg [3:0] test_id = 4'd0;
    reg [7:0] fail_code = 8'd0;

    reg [9:0] last_proposal_a = 10'd0;
    reg [9:0] last_proposal_b = 10'd0;
    reg [9:0] last_norm = 10'd0;
    reg [9:0] last_commit_a = 10'd0;
    reg [9:0] last_commit_b = 10'd0;

    task capture_epoch;
        begin
            last_proposal_a <= proposal_a;
            last_proposal_b <= proposal_b;
            last_norm <= norm_value;
            last_commit_a <= commit_a;
            last_commit_b <= commit_b;
        end
    endtask

    task capture_overflow_epoch;
        begin
            last_proposal_a <= overflow_proposal_a;
            last_proposal_b <= overflow_proposal_b;
            last_norm <= overflow_norm_value;
            last_commit_a <= overflow_commit_a;
            last_commit_b <= overflow_commit_b;
        end
    endtask

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            test_id <= 4'd0;
            fail_code <= 8'd0;
            epoch_start <= 1'b0;
            spike_in <= 2'b00;
            weights <= {8'd5, 8'd3};
            thresholds <= {8'd5, 8'd5};
            expected_norm <= 10'd11;
            fallback_a <= 10'd7;
            fallback_b <= 10'd8;
            overflow_start <= 1'b0;
            overflow_spike <= 1'b0;
            last_proposal_a <= 10'd0;
            last_proposal_b <= 10'd0;
            last_norm <= 10'd0;
            last_commit_a <= 10'd0;
            last_commit_b <= 10'd0;
        end else if (probe_tick) begin
            epoch_start <= 1'b0;
            overflow_start <= 1'b0;

            case (test_state)
                S_RESET: begin
                    spike_in <= 2'b00;
                    overflow_spike <= 1'b0;
                    test_state <= S_ACCEPT_ARM;
                end

                S_ACCEPT_ARM: begin
                    test_id <= 4'd1;
                    weights <= {8'd5, 8'd3};
                    thresholds <= {8'd5, 8'd5};
                    expected_norm <= 10'd11;
                    fallback_a <= 10'd7;
                    fallback_b <= 10'd8;
                    epoch_start <= 1'b1;
                    spike_in <= 2'b00;
                    test_state <= S_ACCEPT_C0;
                end
                S_ACCEPT_C0: begin spike_in <= 2'b11; test_state <= S_ACCEPT_C1; end
                S_ACCEPT_C1: begin spike_in <= 2'b01; test_state <= S_ACCEPT_C2; end
                S_ACCEPT_C2: begin spike_in <= 2'b00; test_state <= S_ACCEPT_CHECK; end
                S_ACCEPT_CHECK: begin
                    if (done) begin
                        capture_epoch();
                        if (accepted && !rejected && norm_ok &&
                            !overflow_fault && token_mask == 2'b11 &&
                            spike_total == 16'd2 &&
                            proposal_a == 10'd3 && proposal_b == 10'd2 &&
                            norm_value == 10'd11 &&
                            commit_a == 10'd3 && commit_b == 10'd2) begin
                            test_state <= S_REJECT_ARM;
                        end else begin
                            fail_code <= 8'hA1;
                            test_state <= S_FAIL;
                        end
                    end
                end

                S_REJECT_ARM: begin
                    test_id <= 4'd2;
                    weights <= {8'd5, 8'd3};
                    thresholds <= {8'd5, 8'd5};
                    expected_norm <= 10'd12;
                    fallback_a <= 10'd7;
                    fallback_b <= 10'd8;
                    epoch_start <= 1'b1;
                    spike_in <= 2'b00;
                    test_state <= S_REJECT_C0;
                end
                S_REJECT_C0: begin spike_in <= 2'b11; test_state <= S_REJECT_C1; end
                S_REJECT_C1: begin spike_in <= 2'b01; test_state <= S_REJECT_C2; end
                S_REJECT_C2: begin spike_in <= 2'b00; test_state <= S_REJECT_CHECK; end
                S_REJECT_CHECK: begin
                    if (done) begin
                        capture_epoch();
                        if (!accepted && rejected && !norm_ok &&
                            !overflow_fault && token_mask == 2'b11 &&
                            spike_total == 16'd2 &&
                            proposal_a == 10'd3 && proposal_b == 10'd2 &&
                            norm_value == 10'd11 &&
                            commit_a == 10'd7 && commit_b == 10'd8) begin
                            test_state <= S_CARRY_ARM;
                        end else begin
                            fail_code <= 8'hB2;
                            test_state <= S_FAIL;
                        end
                    end
                end

                S_CARRY_ARM: begin
                    test_id <= 4'd3;
                    weights <= {8'd0, 8'd8};
                    thresholds <= {8'd0, 8'd15};
                    expected_norm <= 10'd1;
                    fallback_a <= 10'd7;
                    fallback_b <= 10'd8;
                    epoch_start <= 1'b1;
                    spike_in <= 2'b00;
                    test_state <= S_CARRY_C0;
                end
                S_CARRY_C0: begin spike_in <= 2'b01; test_state <= S_CARRY_C1; end
                S_CARRY_C1: begin spike_in <= 2'b01; test_state <= S_CARRY_C2; end
                S_CARRY_C2: begin spike_in <= 2'b00; test_state <= S_CARRY_CHECK; end
                S_CARRY_CHECK: begin
                    if (done) begin
                        capture_epoch();
                        if (accepted && !rejected && norm_ok &&
                            !overflow_fault && token_mask == 2'b01 &&
                            proposal_a == 10'd1 && proposal_b == 10'd1 &&
                            norm_value == 10'd1 &&
                            commit_a == 10'd1 && commit_b == 10'd1) begin
                            test_state <= S_OVERFLOW_ARM;
                        end else begin
                            fail_code <= 8'hC3;
                            test_state <= S_FAIL;
                        end
                    end
                end

                S_OVERFLOW_ARM: begin
                    test_id <= 4'd4;
                    overflow_start <= 1'b1;
                    overflow_spike <= 1'b0;
                    test_state <= S_OVERFLOW_C0;
                end
                S_OVERFLOW_C0: begin overflow_spike <= 1'b1; test_state <= S_OVERFLOW_C1; end
                S_OVERFLOW_C1: begin overflow_spike <= 1'b1; test_state <= S_OVERFLOW_C2; end
                S_OVERFLOW_C2: begin overflow_spike <= 1'b1; test_state <= S_OVERFLOW_C3; end
                S_OVERFLOW_C3: begin overflow_spike <= 1'b1; test_state <= S_OVERFLOW_C4; end
                S_OVERFLOW_C4: begin overflow_spike <= 1'b1; test_state <= S_OVERFLOW_C5; end
                S_OVERFLOW_C5: begin overflow_spike <= 1'b0; test_state <= S_OVERFLOW_CHECK; end
                S_OVERFLOW_CHECK: begin
                    if (overflow_done) begin
                        capture_overflow_epoch();
                        if (!overflow_accepted && overflow_rejected &&
                            !overflow_norm_ok && overflow_fault_seen &&
                            overflow_total == 16'd3 &&
                            overflow_norm_value == 10'd9 &&
                            overflow_commit_a == 10'd7 &&
                            overflow_commit_b == 10'd8) begin
                            test_state <= S_PASS;
                        end else begin
                            fail_code <= 8'hD4;
                            test_state <= S_FAIL;
                        end
                    end
                end

                S_PASS: begin
                    spike_in <= 2'b00;
                    overflow_spike <= 1'b0;
                end

                S_FAIL: begin
                    spike_in <= 2'b00;
                    overflow_spike <= 1'b0;
                end

                default: begin
                    fail_code <= 8'hEE;
                    test_state <= S_FAIL;
                end
            endcase
        end
    end

    // LEDs
    reg [25:0] blink_cnt = 26'd0;
    always @(posedge sys_clk) begin
        blink_cnt <= blink_cnt + 1'b1;
    end

    assign led[0] = ~blink_cnt[24];              // heartbeat
    assign led[1] = ~(test_state == S_PASS);     // off = PASS
    assign led[2] = ~(test_state == S_FAIL);     // off = FAIL

    // UART telemetry:
    // N:<status> T:<id> P:<a>/<b> K:<norm> C:<a>/<b> E:<fail_code>
    wire [7:0] status_char =
        (test_state == S_PASS) ? "P" :
        (test_state == S_FAIL) ? "F" : ".";

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
                6'd8:  msg_byte = "P";
                6'd9:  msg_byte = ":";
                6'd10: msg_byte = hex2ascii({2'b00, last_proposal_a[9:8]});
                6'd11: msg_byte = hex2ascii(last_proposal_a[7:4]);
                6'd12: msg_byte = hex2ascii(last_proposal_a[3:0]);
                6'd13: msg_byte = "/";
                6'd14: msg_byte = hex2ascii({2'b00, last_proposal_b[9:8]});
                6'd15: msg_byte = hex2ascii(last_proposal_b[7:4]);
                6'd16: msg_byte = hex2ascii(last_proposal_b[3:0]);
                6'd17: msg_byte = " ";
                6'd18: msg_byte = "K";
                6'd19: msg_byte = ":";
                6'd20: msg_byte = hex2ascii({2'b00, last_norm[9:8]});
                6'd21: msg_byte = hex2ascii(last_norm[7:4]);
                6'd22: msg_byte = hex2ascii(last_norm[3:0]);
                6'd23: msg_byte = " ";
                6'd24: msg_byte = "C";
                6'd25: msg_byte = ":";
                6'd26: msg_byte = hex2ascii({2'b00, last_commit_a[9:8]});
                6'd27: msg_byte = hex2ascii(last_commit_a[7:4]);
                6'd28: msg_byte = hex2ascii(last_commit_a[3:0]);
                6'd29: msg_byte = "/";
                6'd30: msg_byte = hex2ascii({2'b00, last_commit_b[9:8]});
                6'd31: msg_byte = hex2ascii(last_commit_b[7:4]);
                6'd32: msg_byte = hex2ascii(last_commit_b[3:0]);
                6'd33: msg_byte = " ";
                6'd34: msg_byte = "E";
                6'd35: msg_byte = ":";
                6'd36: msg_byte = hex2ascii(fail_code[7:4]);
                6'd37: msg_byte = hex2ascii(fail_code[3:0]);
                6'd38: msg_byte = 8'h0D;
                6'd39: msg_byte = 8'h0A;
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
                    if (msg_idx == 6'd39) begin
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
            tx_shift <= 10'h3FF;
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
