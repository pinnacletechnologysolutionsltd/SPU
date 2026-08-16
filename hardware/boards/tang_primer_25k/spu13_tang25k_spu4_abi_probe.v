// spu13_tang25k_spu4_abi_probe.v — Tang 25K silicon probe for SPU-4 ABI v1.0
//
// Exercises `spu4_customer_wrapper` -- the module a customer integrates
// against -- through its real start/busy/done handshake, and reports the
// result plus the MEASURED LATENCY over UART.
//
// Why this exists separately from spu13_tang25k_spu4_probe:
//   That probe drives spu4_standalone_top, the bring-up vehicle. Its
//   bitstream is pinned by docs/hardware_evidence.md §3.2j and by a
//   pre-registered bench procedure with both images already staged, so
//   adding the wrapper to it would void that preparation. This is a
//   separate target; §3.2j is untouched.
//
// Why it reports latency:
//   Bounded latency is an OPEN product gate in docs/SPU4_PRODUCT_CLAIMS.md.
//   Simulation measured 180-183 clocks over 124 operations against a bound of
//   200 (SPU4_ABI.md §4). A number printed off real silicon closes that gate
//   with hardware evidence instead of a simulation figure -- and if silicon
//   disagrees with simulation, that is worth knowing loudly.
//
// UART protocol (44 bytes = 42 visible chars + CRLF, repeats every LINE_PERIOD):
//   ABI:. B=xxxx C=xxxx D=xxxx R=xx S=xx L=xxx\r\n   — still running
//   ABI:P B=0155 C=0155 D=0155 R=FF S=xx L=xxx\r\n   — PASS
//   ABI:F B=xxxx C=xxxx D=xxxx R=xx S=xx L=xxx\r\n   — FAIL
//
//   B/C/D  registered wrapper results. A is omitted -- it is 0000 for this
//          fixture and the line has to stay inside a sane width; the
//          interesting axes are the three that rotate.
//   R      dissonance, the saturating Quadray residual. FF is CORRECT here:
//          the QROT fixture settles at A=0 B=C=D=0x155, a residual of 0x3FF.
//   S      the ABI status byte: {000, start_ignored, saturated, henosis,
//          done, busy}. Read it, do not assume it -- henosis is not
//          predicted here, and the testbench pins whatever the RTL yields.
//   L      measured latency in clocks from the accepted `start` to `done`,
//          three hex digits, saturating at FFF.
//
// The UART engine is copied from spu13_tang25k_spu4_probe, which is the
// silicon-proven single-owner pattern; do not restructure it. The original
// SPU-4 probe was mute on its first flash because the message pump and bit
// engine lived in separate always blocks.

module spu13_tang25k_spu4_abi_probe #(
    parameter CLK_FREQ     = 50000000,
    parameter CLKS_PER_BIT = 434,             // 115200 baud at 50 MHz
    parameter START_DELAY  = 50000000 / 2,
    parameter LINE_PERIOD  = 50000000 / 5
) (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx
);

    // ── Reset ────────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1;
    end

    // ── The module under test: the customer ABI ──────────────────────
    reg         start;
    wire        busy, done;
    wire signed [15:0] a_out, b_out, c_out, d_out;
    wire [7:0]  dissonance, status;

    spu4_customer_wrapper u_abi (
        .clk(sys_clk), .rst_n(rst_n),
        .start(start), .busy(busy), .done(done),
        // The QROT reference fixture, identical to the vector proven in
        // silicon at §3.2j: B=C=D=0x0100 under F=0x50, G=0xB5, H=0x50
        // rotates to B=C=D=0x0155.
        .a_in(16'sh0000), .b_in(16'sh0100), .c_in(16'sh0100), .d_in(16'sh0100),
        .coeff_f(16'sh0050), .coeff_g(16'sh00B5), .coeff_h(16'sh0050),
        .a_out(a_out), .b_out(b_out), .c_out(c_out), .d_out(d_out),
        .dissonance(dissonance), .status(status)
    );

    // ── Drive exactly one operation, and time it ─────────────────────
    // `start` is a single-cycle pulse. Asserting it while busy would be a
    // handshake violation, which the wrapper would report in status[4] --
    // so a nonzero S bit 4 on the line means this probe is buggy, not the
    // wrapper.
    localparam S_IDLE = 3'd0, S_RUN = 3'd1, S_CHECK = 3'd2;
    localparam S_PASS = 3'd3, S_FAIL = 3'd4;

    reg [2:0]  test_state = S_IDLE;
    reg [11:0] latency;               // clocks, saturating at 0xFFF
    reg [31:0] timeout;
    reg        launched;

    // ABI v1.0 requires `start` to be held off until the wrapper's reset
    // synchroniser has released -- at least 2 clocks after rst_n rises, per
    // SPU4_ABI.md G6. Found the hard way: the first version of this probe
    // asserted start on the first cycle after rst_n and the wrapper, still
    // held in reset, swallowed it. The line read L=FFF S=00 forever.
    // 16 clocks is comfortable margin over the required 2.
    reg [4:0] abi_ready_cnt;
    wire abi_ready = abi_ready_cnt[4];
    always @(posedge sys_clk) begin
        if (!rst_n)            abi_ready_cnt <= 5'd0;
        else if (!abi_ready)   abi_ready_cnt <= abi_ready_cnt + 1'b1;
    end

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_IDLE;
            start      <= 1'b0;
            latency    <= 12'd0;
            timeout    <= 32'd0;
            launched   <= 1'b0;
        end else begin
            start <= 1'b0;                         // one-cycle pulse
            case (test_state)
                S_IDLE: begin
                    // One launch only, ever. Re-running would overwrite a
                    // recorded latency with a later one and make the line
                    // non-reproducible.
                    if (!launched && abi_ready) begin
                        start     <= 1'b1;
                        launched  <= 1'b1;
                        test_state <= S_RUN;
                    end
                end
                S_RUN: begin
                    if (done) begin
                        test_state <= S_CHECK;
                    end else begin
                        if (latency != 12'hFFF) latency <= latency + 1'b1;
                        if (timeout > 32'd10000000) test_state <= S_FAIL;
                        else timeout <= timeout + 1'b1;
                    end
                end
                S_CHECK: begin
                    // Assert the saturated 0xFF rather than a laminar 0x00:
                    // 0x00 is also what a stripped or stuck-at-zero port
                    // reads, so it cannot distinguish a working signal from
                    // a dead one.
                    if (b_out == 16'sh0155 && c_out == 16'sh0155 &&
                        d_out == 16'sh0155 && dissonance == 8'hFF &&
                        status[1] == 1'b1 &&      // done
                        status[0] == 1'b0 &&      // not busy
                        status[4] == 1'b0)        // no handshake violation
                        test_state <= S_PASS;
                    else
                        test_state <= S_FAIL;
                end
                default: ;                        // PASS/FAIL are terminal
            endcase
        end
    end

    // ── UART + status line (single-owner engine, proven pattern) ─────
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits = 4'd0;
    reg [15:0] baud_cnt = 16'd0;
    reg        tx_busy = 1'b0;
    reg [7:0]  tx_byte = 8'd0;
    reg        tx_go = 1'b0;
    reg [27:0] line_timer = 28'd0;
    reg [27:0] start_cnt = 28'd0;
    reg        start_ready = 1'b0;
    reg [5:0]  msg_idx = 6'd0;
    reg        line_active = 1'b0;

    assign uart_tx = tx_shift[0];

    function [7:0] h;
        input [3:0] n;
        begin h = (n < 10) ? ("0" + n) : ("A" + n - 10); end
    endfunction

    function [7:0] msg_byte;
        input [5:0] idx;
        reg [7:0] status_ch;
        begin
            status_ch = (test_state == S_PASS) ? "P" :
                        (test_state == S_FAIL) ? "F" : ".";
            case (idx)
                6'd0:  msg_byte = "A";
                6'd1:  msg_byte = "B";
                6'd2:  msg_byte = "I";
                6'd3:  msg_byte = ":";
                6'd4:  msg_byte = status_ch;
                6'd5:  msg_byte = " ";
                6'd6:  msg_byte = "B";
                6'd7:  msg_byte = "=";
                6'd8:  msg_byte = h(b_out[15:12]);
                6'd9:  msg_byte = h(b_out[11:8]);
                6'd10: msg_byte = h(b_out[7:4]);
                6'd11: msg_byte = h(b_out[3:0]);
                6'd12: msg_byte = " ";
                6'd13: msg_byte = "C";
                6'd14: msg_byte = "=";
                6'd15: msg_byte = h(c_out[15:12]);
                6'd16: msg_byte = h(c_out[11:8]);
                6'd17: msg_byte = h(c_out[7:4]);
                6'd18: msg_byte = h(c_out[3:0]);
                6'd19: msg_byte = " ";
                6'd20: msg_byte = "D";
                6'd21: msg_byte = "=";
                6'd22: msg_byte = h(d_out[15:12]);
                6'd23: msg_byte = h(d_out[11:8]);
                6'd24: msg_byte = h(d_out[7:4]);
                6'd25: msg_byte = h(d_out[3:0]);
                6'd26: msg_byte = " ";
                6'd27: msg_byte = "R";
                6'd28: msg_byte = "=";
                6'd29: msg_byte = h(dissonance[7:4]);
                6'd30: msg_byte = h(dissonance[3:0]);
                6'd31: msg_byte = " ";
                6'd32: msg_byte = "S";
                6'd33: msg_byte = "=";
                6'd34: msg_byte = h(status[7:4]);
                6'd35: msg_byte = h(status[3:0]);
                6'd36: msg_byte = " ";
                6'd37: msg_byte = "L";
                6'd38: msg_byte = "=";
                6'd39: msg_byte = h(latency[11:8]);
                6'd40: msg_byte = h(latency[7:4]);
                6'd41: msg_byte = h(latency[3:0]);
                6'd42: msg_byte = 8'h0D;
                6'd43: msg_byte = 8'h0A;
                default: msg_byte = 8'h20;
            endcase
        end
    endfunction

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; tx_bits <= 4'd0; baud_cnt <= 16'd0;
            tx_busy <= 1'b0; tx_byte <= 8'd0; tx_go <= 1'b0;
            line_timer <= 28'd0; start_cnt <= 28'd0; start_ready <= 1'b0;
            msg_idx <= 6'd0; line_active <= 1'b0;
        end else begin
            if (tx_busy) begin
                if (baud_cnt < CLKS_PER_BIT - 1) begin
                    baud_cnt <= baud_cnt + 1'b1;
                end else begin
                    baud_cnt <= 16'd0;
                    tx_shift <= {1'b1, tx_shift[9:1]};
                    if (tx_bits == 1) begin
                        tx_busy <= 1'b0; tx_bits <= 4'd0;
                    end else begin
                        tx_bits <= tx_bits - 1'b1;
                    end
                end
            end else if (tx_go) begin
                tx_go <= 1'b0;
                tx_shift <= {1'b1, tx_byte, 1'b0};
                tx_bits <= 4'd10;
                tx_busy <= 1'b1;
                baud_cnt <= 16'd0;
            end else if (!start_ready) begin
                if (start_cnt < START_DELAY - 1) start_cnt <= start_cnt + 1'b1;
                else start_ready <= 1'b1;
            end else if (line_active) begin
                tx_byte <= msg_byte(msg_idx);
                tx_go <= 1'b1;
                if (msg_idx == 6'd43) begin
                    msg_idx <= 6'd0;
                    line_active <= 1'b0;
                end else begin
                    msg_idx <= msg_idx + 1'b1;
                end
            end else if (line_timer < LINE_PERIOD - 1) begin
                line_timer <= line_timer + 1'b1;
            end else begin
                line_timer <= 28'd0;
                msg_idx <= 6'd0;
                line_active <= 1'b1;
            end
        end
    end

    // ── LEDs ─────────────────────────────────────────────────────────
    reg [24:0] blink;
    always @(posedge sys_clk) blink <= blink + 1;
    assign led[0] = ~blink[24];
    assign led[1] = ~(test_state == S_PASS);
    assign led[2] = ~(test_state == S_FAIL);

endmodule
