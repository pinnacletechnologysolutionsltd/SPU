// spu_tang25k_whisper_v1_probe.v — Tang 25K Whisper v1 silicon probe
//
// Emitter→listener loopback on the FPGA fabric. Self-checking: verifies
// that the first received frame has correct node_id, flags, dissonance,
// and seq, with no frame_err. Reports over bit-bang UART at 115200 baud.
//
// UART output on pin C3:
//   WHSP:P F:1 E:00   PASS  (1 frame verified, no errors)
//   WHSP:F F:1 E:xx   FAIL  (error code reported)
//
// LEDs: heartbeat on led[0], PASS=off/FAIL=on for led[2].

module spu_tang25k_whisper_v1_probe (
    input  wire       sys_clk,     // E2, 50 MHz
    output wire [2:0] led,         // L6, E8, D7 (active-low)
    output wire       uart_tx      // C3, 115200 baud
);

    localparam CLK_FREQ        = 50000000;
    localparam CLKS_PER_BIT    = 434;  // 115200 baud at 50 MHz
    localparam LINE_PERIOD     = CLK_FREQ / 2;  // ~0.5s between lines
    localparam WHISPER_CLK_HZ  = 12500000;       // 50 MHz / 4

    // ── Clock divider for whisper modules (50 MHz → 12.5 MHz) ──────
    reg [1:0] clk_div = 2'd0;
    wire whisper_clk;
    assign whisper_clk = clk_div[1];  // toggles at 12.5 MHz

    always @(posedge sys_clk) begin
        clk_div <= clk_div + 2'd1;
    end

    // ── Reset ───────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 8'd0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge whisper_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1'b1;
    end

    // ── Whisper emitter + listener loopback ─────────────────────────
    reg        is_laminar;
    reg  [3:0] node_id;
    reg  [2:0] flags_in;
    reg  [7:0] dissonance;
    wire       tx_wire;
    wire       em_busy;
    wire [3:0] rx_node_id;
    wire [2:0] rx_flags;
    wire [7:0] rx_dissonance;
    wire [7:0] rx_seq;
    wire       rx_valid;
    wire       rx_err;
    wire       incoherent;

    spu_whisper_v1_emitter #(
        .CLK_HZ(WHISPER_CLK_HZ), .BAUD(115200), .PERIOD_CYCLES(WHISPER_CLK_HZ / 6000)
    ) u_em (
        .clk(whisper_clk), .rst_n(rst_n),
        .is_laminar(is_laminar), .node_id(node_id),
        .flags_in(flags_in), .dissonance(dissonance),
        .tx(tx_wire), .busy(em_busy)
    );

    spu_whisper_v1_listener #(
        .CLK_HZ(WHISPER_CLK_HZ), .BAUD(115200), .PERIOD_CYCLES(WHISPER_CLK_HZ / 6000)
    ) u_list (
        .clk(whisper_clk), .rst_n(rst_n),
        .rx(tx_wire),
        .node_id(rx_node_id), .flags(rx_flags),
        .dissonance(rx_dissonance), .seq(rx_seq),
        .frame_valid(rx_valid), .frame_err(rx_err),
        .incoherent(incoherent)
    );

    // ── Self-check FSM (runs on whisper_clk) ───────────────────────
    localparam S_RESET  = 3'd0;
    localparam S_WAIT   = 3'd1;
    localparam S_CHECK  = 3'd2;
    localparam S_PASS   = 3'd3;
    localparam S_FAIL   = 3'd4;

    reg [2:0] state = S_RESET;
    reg [3:0] error_code = 4'd0;
    reg       frame_seen = 1'b0;
    reg       pass_flag  = 1'b0;  // latched, read by UART FSM

    always @(posedge whisper_clk) begin
        if (!rst_n) begin
            state      <= S_RESET;
            error_code <= 4'd0;
            frame_seen <= 1'b0;
            pass_flag  <= 1'b0;
            is_laminar <= 1'b0;
            node_id    <= 4'h5;
            flags_in   <= 3'b101;
            dissonance <= 8'h2A;
        end else begin
            case (state)
                S_RESET: begin
                    is_laminar <= 1'b1;
                    state <= S_WAIT;
                end

                S_WAIT: begin
                    if (rx_valid && !frame_seen) begin
                        frame_seen <= 1'b1;
                        state <= S_CHECK;
                    end
                end

                S_CHECK: begin
                    // Verify the first received frame
                    if (rx_node_id !== 4'h5)     error_code[0] <= 1'b1;
                    if (rx_flags !== 3'b101)      error_code[1] <= 1'b1;
                    if (rx_dissonance !== 8'h2A)  error_code[2] <= 1'b1;
                    if (rx_seq !== 8'h00)         error_code[2] <= 1'b1;
                    if (rx_err)                   error_code[3] <= 1'b1;

                    if (error_code == 4'd0)
                        state <= S_PASS;
                    else
                        state <= S_FAIL;
                end

                S_PASS: begin
                    pass_flag <= 1'b1;
                end

                S_FAIL: begin
                    pass_flag <= 1'b0;
                end

                default: state <= S_RESET;
            endcase
        end
    end

    // ── LED heartbeat (sys_clk domain; active-low) ─────────────────
    reg [24:0] led_cnt = 25'd0;
    always @(posedge sys_clk) begin
        led_cnt <= led_cnt + 25'd1;
    end

    assign led[0] = ~(led_cnt[24]);             // heartbeat ~1.5 Hz
    assign led[1] = ~(frame_seen && pass_flag); // off when pass
    assign led[2] = ~(!pass_flag && frame_seen);// on when fail

    // ── Bit-bang UART TX (sys_clk domain, 115200 baud) ─────────────
    reg        uart_busy = 1'b0;
    reg [15:0] uart_bit_cnt = 16'd0;
    reg [3:0]  uart_bit_idx = 4'd0;
    reg [9:0]  uart_shift = 10'd0;
    reg        uart_tx_reg = 1'b1;
    assign uart_tx = uart_tx_reg;

    // Message ROM
    function [7:0] msg_byte;
        input [7:0] idx;
        begin
            case (idx)
                // "WHSP:P F:1 E:00  PASS\n"  or  "WHSP:F F:1 E:XX  FAIL\n"
                8'd0:  msg_byte = 8'h57;  // W
                8'd1:  msg_byte = 8'h48;  // H
                8'd2:  msg_byte = 8'h53;  // S
                8'd3:  msg_byte = 8'h50;  // P
                8'd4:  msg_byte = pass_flag ? 8'h3A : 8'h3A;  // :
                8'd5:  msg_byte = pass_flag ? 8'h50 : 8'h46;  // P or F
                8'd6:  msg_byte = 8'h20;  // space
                8'd7:  msg_byte = 8'h46;  // F
                8'd8:  msg_byte = 8'h3A;  // :
                8'd9:  msg_byte = 8'h31;  // 1
                8'd10: msg_byte = 8'h20;  // space
                8'd11: msg_byte = 8'h45;  // E
                8'd12: msg_byte = 8'h3A;  // :
                8'd13: msg_byte = pass_flag ? 8'h30 : hex_nibble(4'd0);
                8'd14: msg_byte = pass_flag ? 8'h30 : hex_nibble(error_code[3:0]);
                8'd15: msg_byte = 8'h20;  // space
                8'd16: msg_byte = 8'h20;  // space
                8'd17: msg_byte = pass_flag ? 8'h50 : 8'h46;  // P or F
                8'd18: msg_byte = pass_flag ? 8'h41 : 8'h41;  // A
                8'd19: msg_byte = pass_flag ? 8'h53 : 8'h49;  // S or I
                8'd20: msg_byte = pass_flag ? 8'h53 : 8'h4C;  // S or L
                8'd21: msg_byte = 8'h0A;  // \n
                default: msg_byte = 8'h00;
            endcase
        end
    endfunction

    function [7:0] hex_nibble;
        input [3:0] n;
        begin
            hex_nibble = (n < 4'd10) ? (8'h30 + n) : (8'h37 + n);
        end
    endfunction

    // UART TX FSM
    reg [31:0] line_timer = 32'd0;
    reg [4:0]  msg_idx = 5'd0;

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
                if (msg_idx < 5'd22) begin
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
