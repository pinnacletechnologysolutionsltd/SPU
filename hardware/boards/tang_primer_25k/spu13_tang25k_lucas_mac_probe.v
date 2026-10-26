// spu13_tang25k_lucas_mac_probe.v — Lucas Phinary MAC Zero-Drift Probe
//
// Minimal Tang 25K probe that instantiates the Lucas MAC co-processor,
// runs the zero-DSP fast-path proof (PSCALE, PCHIRAL, and PSCALE
// zero-drift), and outputs PASS/FAIL via UART + LED.
//
// No SPU-13 core, no SPI, no M31 — just the Lucas MAC and a test sequencer.

module spu13_tang25k_lucas_mac_probe (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);
    localparam L_P = 521;
    localparam L_P_BITS = 10;
    localparam PERIOD = 26;
    localparam CLK_FREQ = 50000000;
    localparam CLKS_PER_BIT = 434;  // 115200 baud at 50 MHz

    // ── Reset ───────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) if (!rst_n) rst_cnt <= rst_cnt + 1;

    // ── Lucas MAC instantiation ────────────────────────────────────
    reg         mac_start = 0;
    reg  [2:0]  mac_opcode = 0;
    reg  [9:0]  mac_a = 0, mac_b = 0, mac_c = 0, mac_d = 0;
    wire        mac_busy, mac_done, mac_error;
    wire [9:0]  mac_res_a, mac_res_b;

    spu13_lucas_mac #(
        .L_P(L_P),
        .L_P_BITS(L_P_BITS),
        .FAST_ONLY(1)
    ) u_mac (
        .clk(sys_clk), .rst_n(rst_n),
        .start(mac_start), .opcode(mac_opcode),
        .op_a(mac_a), .op_b(mac_b),
        .op_c(mac_c), .op_d(mac_d),
        .phslk_n2_a(10'd0), .phslk_n2_b(10'd0),
        .phslk_d2_a(10'd0), .phslk_d2_b(10'd0),
        .busy(mac_busy), .done(mac_done),
        .result_a(mac_res_a), .result_b(mac_res_b),
        .phslk_coherent(), .phslk_zero_divisor(),
        .error(mac_error),
        .norm_violation()
    );

    // ── Test sequencer ─────────────────────────────────────────────
    localparam [3:0] S_RESET   = 0;
    localparam [3:0] S_PSCALE  = 1;  // PSCALE sanity: φ·(3+5φ) = (5+8φ)
    localparam [3:0] S_PCHIRAL = 2;  // PCHIRAL sanity: conj(3+5φ) = (8+516φ)
    localparam [3:0] S_DRIFT_LOOP = 3;  // Zero-drift marathon
    localparam [3:0] S_PASS = 4;
    localparam [3:0] S_FAIL = 5;

    reg [3:0]  test_state = S_RESET;
    reg [3:0]  test_substate = 0;
    reg [15:0] test_step = 0;
    reg [9:0]  drift_a = 3, drift_b = 5;  // seed (3+5φ)
    reg [15:0] drift_periods = 0;
    reg        all_pass = 1;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_RESET;
            test_substate <= 0;
            test_step <= 0;
            drift_a <= 3; drift_b <= 5;
            drift_periods <= 0;
            all_pass <= 1;
            mac_start <= 0;
        end else if (!mac_busy) begin
            mac_start <= 0;
            case (test_state)
                S_RESET: begin
                    if (rst_cnt == 8'hFF) test_state <= S_PSCALE;
                end

                S_PSCALE: begin  // φ·(3+5φ) = (5+8φ)
                    if (test_substate == 0) begin
                        mac_a <= 3; mac_b <= 5; mac_opcode <= 0; mac_start <= 1;
                        test_substate <= 1;
                    end else if (mac_done) begin
                        if (mac_res_a == 5 && mac_res_b == 8)
                            test_state <= S_PCHIRAL;
                        else test_state <= S_FAIL;
                        test_substate <= 0;
                    end
                end

                S_PCHIRAL: begin  // conj(3+5φ) = (8+516φ)
                    if (test_substate == 0) begin
                        mac_a <= 3; mac_b <= 5; mac_opcode <= 1; mac_start <= 1;
                        test_substate <= 1;
                    end else if (mac_done) begin
                        if (mac_res_a == 8 && mac_res_b == 516) begin
                            test_state <= S_DRIFT_LOOP;
                            drift_a <= 3; drift_b <= 5; test_step <= 0;
                        end
                        else test_state <= S_FAIL;
                        test_substate <= 0;
                    end
                end

                S_DRIFT_LOOP: begin
                    if (test_substate == 0) begin
                        mac_a <= drift_a; mac_b <= drift_b;
                        mac_opcode <= 0; mac_start <= 1;
                        test_substate <= 1;
                    end else if (mac_done) begin
                        drift_a <= mac_res_a; drift_b <= mac_res_b;
                        test_step <= test_step + 1;
                        test_substate <= 0;

                        if (test_step + 1 == PERIOD * 100) begin
                            test_state <= S_PASS;
                        end else if ((test_step + 1) % PERIOD == 0) begin
                            if (mac_res_a != 3 || mac_res_b != 5) begin
                                test_state <= S_FAIL;
                            end
                        end
                    end
                end

                S_PASS: ;  // done, hold
                S_FAIL: ;  // done, hold
            endcase
        end
    end

    // ── LEDs ───────────────────────────────────────────────────────
    reg [25:0] blink_cnt = 0;
    always @(posedge sys_clk) blink_cnt <= blink_cnt + 1;

    assign led[0] = ~blink_cnt[24];                     // heartbeat
    assign led[1] = ~(test_state == S_PASS);             // off = PASS
    assign led[2] = ~(test_state == S_FAIL);             // off = FAIL

    // ── UART telemetry ────────────────────────────────────────────
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 0;
    reg [15:0] baud_cnt = 0;
    reg        tx_busy = 0;
    reg [7:0]  tx_byte = 0;
    reg        tx_go = 0;
    reg [27:0] line_timer = 0;
    reg        start_ready = 0;
    reg [27:0] start_cnt = 0;
    reg [3:0]  msg_idx = 0;
    reg        line_active = 0;

    assign uart_tx = tx_shift[0];

    function [7:0] hex2ascii;
        input [3:0] h;
        begin hex2ascii = (h < 10) ? (8'h30 + h) : (8'h37 + h); end
    endfunction

    function [7:0] msg_byte;
        input [3:0] idx;
        begin
            case (idx)
                4'd0: msg_byte = "L";
                4'd1: msg_byte = "U";
                4'd2: msg_byte = "C";
                4'd3: msg_byte = "A";
                4'd4: msg_byte = "S";
                4'd5: msg_byte = ":";
                4'd6: msg_byte = (test_state == S_PASS) ? "P" :
                                  (test_state == S_FAIL) ? "F" : ".";
                4'd7: msg_byte = 8'h0D;
                4'd8: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    // Simple UART byte transmitter
    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 0; baud_cnt <= 0;
            tx_busy <= 0; tx_go <= 0; start_ready <= 0;
            start_cnt <= 0; line_timer <= 0; msg_idx <= 0; line_active <= 0;
        end else begin
            if (tx_busy) begin
                if (baud_cnt < CLKS_PER_BIT - 1) baud_cnt <= baud_cnt + 1;
                else begin
                    baud_cnt <= 0;
                    tx_shift <= {1'b1, tx_shift[9:1]};
                    if (tx_bits == 1) begin tx_busy <= 0; tx_bits <= 0; end
                    else tx_bits <= tx_bits - 1;
                end
            end else if (tx_go) begin
                tx_go <= 0;
                tx_shift <= {1'b1, tx_byte, 1'b0};
                tx_bits <= 10; tx_busy <= 1;
                baud_cnt <= 0;
            end else if (!start_ready) begin
                if (start_cnt < CLK_FREQ/2 - 1) start_cnt <= start_cnt + 1;
                else start_ready <= 1;
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1;
                if (msg_idx == 4'd8) begin
                    msg_idx <= 0;
                    line_active <= 0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < CLK_FREQ/5 - 1) begin
                line_timer <= line_timer + 1;
            end else begin
                line_timer <= 0;
                msg_idx <= 0;
                line_active <= 1;
            end
        end
    end

endmodule
