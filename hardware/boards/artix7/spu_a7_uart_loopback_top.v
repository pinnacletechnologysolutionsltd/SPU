// spu_a7_uart_loopback_top.v — GPU tranche T1, gate step 1: prove UART RX on
// pin F3 IN ISOLATION, before any loader touches the GPU.
//
// WHY THIS EXISTS AS ITS OWN SPIN. spu_a7_100t.xdc records that the bridge's
// TXD "is available on F3, but spu_a7_top currently exposes TX only" -- the
// receive direction has never been used on this board. The GPU tranche
// contract (spu_strategy/contract_gpu_pipeline_tranche_2026-09-06.md, T1)
// requires an actual loopback bitstream built and loaded before the triangle
// loader is integrated, for the reason spu_a7_gpu_vga_top.v's header gives:
// bring a link and its consumer up together and a failure localises to
// neither.
//
// WHAT IT DOES, on the uart_tx line only:
//   - idle: emits "UARTLOOP:READY\r\n" about once per second
//   - on a received byte: echoes it immediately, banner deferred
// A terminal at 115200 8N1 on the onboard bridge (/dev/ttyUSB0 here) shows the
// banner repeating; typing a character returns that character.
//
// THE POSITIVE CONTROL IS THE BANNER, NOT AN LED -- deliberately.
// spu_a7_100t.xdc documents led_out[3:0] (V17/W21/Y21/V26) as a real,
// stable, reproducible I/O anomaly on this unit: non-logic-level voltages
// measured across multiple known-good bitstreams, mechanism unknown, closed
// but not fixed. Its own words: "Do not trust led_out for a new claim on
// this unit without a fresh isolated loopback/probe check first." Using it
// as the liveness indicator here would make a broken control the reference
// for a working one. E3 already carries proof-of-life duty and is
// silicon-proven for it.
//
// So the three outcomes are distinguishable without any other instrument:
//   no banner            -> the bitstream is not running, or TX/E3 is dead
//   banner, no echo      -> TX works, RX on F3 specifically does not
//   banner and echo      -> F3 receive works; T1 may proceed
//
// CLOCK. The board pin is called clk_100mhz elsewhere in this tree, but the
// oscillator is 50 MHz -- BAUD_DIV 434 = 50e6/115200 in
// spu_a7_uart_probe_top.v, and the SPI ratio work recorded the same. CLK_HZ
// is 50e6 for that reason.
//
// CC0 1.0 Universal.

module spu_a7_uart_loopback_top #(
    parameter CLK_HZ     = 50_000_000,
    parameter BAUD       = 115200,
    parameter BANNER_DIV = 50_000_000,  // ~1 s; overridden small in the bench
    // Reset debounce width. 16 bits is 65,536 cycles at 50 MHz (~1.3 ms),
    // which is right on silicon and absurd in simulation -- a bench would
    // burn 65k cycles before the DUT even leaves reset. Parameterised for
    // the same reason spu_gpu_top's video timing is (commit 3c241b9):
    // the default is unchanged, the bench overrides it.
    parameter DEBOUNCE_BITS = 16
) (
    input  wire sys_clk,     // M21, 50 MHz
    input  wire rst_n,       // H7, active low, board PULLUP
    input  wire uart_rx,     // F3, USB-UART bridge TXD -> FPGA
    output wire uart_tx      // E3, FPGA -> USB-UART bridge RXD
);

    localparam BIT_CYC = CLK_HZ / BAUD;

    // ── Reset conditioning ───────────────────────────────────────────────
    // As in spu_a7_vga_top/spu_a7_gpu_vga_top: rst_n (H7) has no external
    // pull-down, and feeding it straight into async resets left this board
    // dead for three weeks (hardware_evidence.md 3.2m). Debounce first.
    reg [DEBOUNCE_BITS-1:0] db_cnt   = {DEBOUNCE_BITS{1'b0}};
    reg                     rst_n_db = 1'b0;
    always @(posedge sys_clk) begin
        if (rst_n == rst_n_db)   db_cnt <= {DEBOUNCE_BITS{1'b0}};
        else if (&db_cnt) begin  rst_n_db <= rst_n; db_cnt <= {DEBOUNCE_BITS{1'b0}}; end
        else                     db_cnt <= db_cnt + 1'b1;
    end

    // ── Receive ──────────────────────────────────────────────────────────
    wire [7:0] rx_data;
    wire       rx_valid, rx_frame_err;
    spu_uart_rx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_rx (
        .clk(sys_clk), .rst_n(rst_n_db), .rx(uart_rx),
        .data(rx_data), .valid(rx_valid), .frame_err(rx_frame_err));

    // ── Banner source ────────────────────────────────────────────────────
    localparam MSG_LEN = 16;
    reg [7:0] msg [0:MSG_LEN-1];
    initial begin
        msg[0]="U"; msg[1]="A"; msg[2]="R"; msg[3]="T"; msg[4]="L";
        msg[5]="O"; msg[6]="O"; msg[7]="P"; msg[8]=":"; msg[9]="R";
        msg[10]="E"; msg[11]="A"; msg[12]="D"; msg[13]="Y";
        msg[14]=8'h0D; msg[15]=8'h0A;
    end

    reg [31:0] banner_cnt = 32'd0;
    reg [4:0]  banner_idx = MSG_LEN[4:0];   // == MSG_LEN means "not sending"
    wire       banner_active = (banner_idx < MSG_LEN[4:0]);

    // ── Transmit ─────────────────────────────────────────────────────────
    // 10 bits, LSB first: start, 8 data, stop. Echo takes priority over the
    // banner; a byte arriving mid-transmission is dropped rather than
    // corrupting the frame in flight. At 115200 with a human typing that
    // cannot happen, and a silent drop beats a malformed echo that would
    // look like a wiring fault.
    reg [9:0]  tx_shift = 10'h3FF;
    reg [3:0]  tx_bits  = 4'd0;
    reg [15:0] tx_cnt   = 16'd0;
    wire       tx_busy  = (tx_bits != 4'd0);

    always @(posedge sys_clk or negedge rst_n_db) begin
        if (!rst_n_db) begin
            tx_shift   <= 10'h3FF;
            tx_bits    <= 4'd0;
            tx_cnt     <= 16'd0;
            banner_cnt <= 32'd0;
            banner_idx <= MSG_LEN[4:0];
        end else begin
            if (!banner_active) begin
                if (banner_cnt >= BANNER_DIV - 1) begin
                    banner_cnt <= 32'd0;
                    banner_idx <= 5'd0;
                end else begin
                    banner_cnt <= banner_cnt + 32'd1;
                end
            end

            if (!tx_busy) begin
                if (rx_valid) begin
                    tx_shift <= {1'b1, rx_data, 1'b0};
                    tx_bits  <= 4'd10;
                    tx_cnt   <= BIT_CYC[15:0] - 16'd1;
                end else if (banner_active) begin
                    tx_shift   <= {1'b1, msg[banner_idx], 1'b0};
                    tx_bits    <= 4'd10;
                    tx_cnt     <= BIT_CYC[15:0] - 16'd1;
                    banner_idx <= banner_idx + 5'd1;
                end
            end else if (tx_cnt == 16'd0) begin
                tx_shift <= {1'b1, tx_shift[9:1]};
                tx_bits  <= tx_bits - 4'd1;
                tx_cnt   <= BIT_CYC[15:0] - 16'd1;
            end else begin
                tx_cnt <= tx_cnt - 16'd1;
            end
        end
    end

    assign uart_tx = tx_shift[0];

endmodule
