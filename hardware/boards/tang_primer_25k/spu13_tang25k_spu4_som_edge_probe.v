// spu13_tang25k_spu4_som_edge_probe.v -- Tang 25K silicon probe for the
// SPU-4 edge SOM product, spu4_som_edge_wrapper (step 4 of the edge-node
// programme, docs/SESSION_HANDOVER_2026-08-16.md 9).
//
// Exercises the real customer wrapper through its actual path: boot
// hydration from the PMOD J4 SPI flash chip (the same chip already proven
// for RPLU2's boot tables at 0x110000 -- FLASH_SPU4_SOM_BASE=0x120000 sits
// 64KB clear of that region, no new wiring), then one classification, then
// reports the result plus MEASURED LATENCY over UART -- same rationale as
// spu13_tang25k_spu4_abi_probe.v: a number off real silicon closes a gate a
// simulation figure cannot.
//
// ── What must be flashed before this probe means anything ────────────────
// tools/gen_spu4_som_boot_image.py --profile oracle_fixture --output
// tools/build/spu4_som_boot_image.bin, then
// tools/rp2040_flash_pmod.py write <that file> --offset 0x120000.
// That profile reproduces, byte-for-byte, the exact fixture already proven
// in simulation by software/lib/spu4_som_edge_oracle.py and
// hardware/tests/spu4/spu4_som_edge_full_chain_tb.v -- so a PASS here is the
// same fixture the software oracle and the RTL testbench already agree on,
// now agreeing a third way, off silicon.
//
// The single query this probe drives is that fixture's "far from all
// nodes, mixed sign" vector -- deliberately the one whose correct verdict
// (node 1, Q=6400) depends on feature index 3 being included in the
// quadrance sum. That is not an arbitrary choice: it is the exact
// regression case for the dropped-feature bug found and fixed in
// spu4_som_edge.v while building the full-chain testbench (2026-08-17,
// commit efc7466) -- an exact-match query cannot distinguish working
// silicon from silicon with that bug reintroduced, because a dropped
// feature contributes zero delta either way when weights equal features.
// This query can.
//
// UART protocol (41 bytes = 39 visible chars + CRLF, repeats every
// LINE_PERIOD):
//   SOM:. N=x Q=xxxxxxxx S=xx L=xxx I=xxxx\r\n   -- still running
//   SOM:P N=1 Q=00001900 S=07 L=xxx I=1120\r\n   -- PASS (Q=6400=0x1900)
//   SOM:F N=x Q=xxxxxxxx S=xx L=xxx I=xxxx\r\n   -- FAIL
//
//   N   best_node, one hex digit (the port is only 2 bits wide).
//   Q   best_quadrance, full 32 bits as 8 hex digits -- no truncation risk.
//   S   the wrapper's status byte: {0000, start_ignored, hydrated, done, busy}.
//       Read it, do not assume it.
//   L   measured latency in clocks from the accepted `start` to `done`,
//       three hex digits, saturating at FFF.
//   I   the wrapper's `id` port: ABI_MAJOR=1 ABI_MINOR=0 WRAPPER_ID=2
//       reserved=0 -> 0x1020 (docs/SPU4_ABI.md 2a), wired through with no
//       decoding here.
//
// The UART engine is the same single-owner pattern as
// spu13_tang25k_spu4_abi_probe.v; do not restructure it.

module spu13_tang25k_spu4_som_edge_probe #(
    parameter CLK_FREQ     = 50000000,
    parameter CLKS_PER_BIT = 434,             // 115200 baud at 50 MHz
    parameter START_DELAY  = 50000000 / 2,
    parameter LINE_PERIOD  = 50000000 / 5
) (
    input  wire       sys_clk,
    output wire [2:0] led,
    output wire       uart_tx,

    // PMOD J4 SPI flash -- same chip and pins as tang_primer_25k.cst's
    // "PMOD J4 SPI Flash" block, already J4-sweep-verified.
    output wire        flash_cs,
    output wire        flash_sck,
    output wire        flash_mosi,
    input  wire        flash_miso
);

    // ── Reset ────────────────────────────────────────────────────────
    reg [7:0] rst_cnt = 0;
    wire rst_n = (rst_cnt == 8'hFF);
    always @(posedge sys_clk) begin
        if (!rst_n) rst_cnt <= rst_cnt + 1;
    end

    // ── The module under test: the SOM edge-node customer wrapper ────
    reg         start;
    wire        busy, done;
    wire [1:0]  best_node;
    wire [31:0] best_quadrance;
    wire [7:0]  status;
    wire [15:0] id;

    spu4_som_edge_wrapper #(
        .NUM_FEATURES(4), .WIDTH(16)
    ) u_som (
        .clk(sys_clk), .rst_n(rst_n),
        .start(start), .busy(busy), .done(done),
        // The oracle fixture's "far from all nodes, mixed sign" query --
        // see file header. Packed the same way the RTL expects: feature 0
        // in the low bits, each feature {P, Q} with P upper 16 bits.
        //   f0=(-5,5) f1=(5,-5) f2=(-5,5) f3=(5,-5)
        .features({16'sh0005, 16'shFFFB,   // f3: P=5,  Q=-5
                    16'shFFFB, 16'sh0005,   // f2: P=-5, Q=5
                    16'sh0005, 16'shFFFB,   // f1: P=5,  Q=-5
                    16'shFFFB, 16'sh0005}), // f0: P=-5, Q=5
        .best_node(best_node), .best_quadrance(best_quadrance),
        .status(status), .id(id),
        .flash_sclk(flash_sck), .flash_cs_n(flash_cs),
        .flash_mosi(flash_mosi), .flash_miso(flash_miso)
    );

    // ── Drive exactly one classification, once hydrated, and time it ──
    // No manual reset-release cushion is needed here the way
    // spu13_tang25k_spu4_abi_probe.v needed one for spu4_customer_wrapper's
    // G6 -- spu4_som_edge_wrapper synchronises its own reset internally and
    // reports `busy` for the whole boot-hydration phase, so waiting on
    // `!busy` is both necessary and sufficient.
    localparam S_WAIT_BOOT = 3'd0, S_LAUNCH = 3'd1, S_RUN = 3'd2;
    localparam S_CHECK     = 3'd3, S_PASS = 3'd4, S_FAIL = 3'd5;

    reg [2:0]  test_state = S_WAIT_BOOT;
    reg [11:0] latency;               // clocks, saturating at 0xFFF
    reg [31:0] timeout;
    reg        launched;

    always @(posedge sys_clk) begin
        if (!rst_n) begin
            test_state <= S_WAIT_BOOT;
            start      <= 1'b0;
            latency    <= 12'd0;
            timeout    <= 32'd0;
            launched   <= 1'b0;
        end else begin
            start <= 1'b0;                         // one-cycle pulse
            case (test_state)
                S_WAIT_BOOT: begin
                    if (!busy) test_state <= S_LAUNCH;
                end
                S_LAUNCH: begin
                    // One launch only, ever -- re-running would overwrite a
                    // recorded latency with a later one and make the line
                    // non-reproducible.
                    if (!launched) begin
                        start      <= 1'b1;
                        launched   <= 1'b1;
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
                    // 6400 (0x1900), not 0 -- a stuck-at-zero or dead
                    // feature-3 port also reads plausible-looking small
                    // values here, so the check has to land on the exact
                    // oracle number, not just "nonzero."
                    if (best_node == 2'd1 && best_quadrance == 32'h00001900 &&
                        status[2] == 1'b1 &&      // hydrated
                        status[1] == 1'b1 &&      // done
                        status[0] == 1'b0 &&      // not busy
                        status[3] == 1'b0)        // no handshake violation
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
                6'd0:  msg_byte = "S";
                6'd1:  msg_byte = "O";
                6'd2:  msg_byte = "M";
                6'd3:  msg_byte = ":";
                6'd4:  msg_byte = status_ch;
                6'd5:  msg_byte = " ";
                6'd6:  msg_byte = "N";
                6'd7:  msg_byte = "=";
                6'd8:  msg_byte = h({2'b00, best_node});
                6'd9:  msg_byte = " ";
                6'd10: msg_byte = "Q";
                6'd11: msg_byte = "=";
                6'd12: msg_byte = h(best_quadrance[31:28]);
                6'd13: msg_byte = h(best_quadrance[27:24]);
                6'd14: msg_byte = h(best_quadrance[23:20]);
                6'd15: msg_byte = h(best_quadrance[19:16]);
                6'd16: msg_byte = h(best_quadrance[15:12]);
                6'd17: msg_byte = h(best_quadrance[11:8]);
                6'd18: msg_byte = h(best_quadrance[7:4]);
                6'd19: msg_byte = h(best_quadrance[3:0]);
                6'd20: msg_byte = " ";
                6'd21: msg_byte = "S";
                6'd22: msg_byte = "=";
                6'd23: msg_byte = h(status[7:4]);
                6'd24: msg_byte = h(status[3:0]);
                6'd25: msg_byte = " ";
                6'd26: msg_byte = "L";
                6'd27: msg_byte = "=";
                6'd28: msg_byte = h(latency[11:8]);
                6'd29: msg_byte = h(latency[7:4]);
                6'd30: msg_byte = h(latency[3:0]);
                6'd31: msg_byte = " ";
                6'd32: msg_byte = "I";
                6'd33: msg_byte = "=";
                6'd34: msg_byte = h(id[15:12]);
                6'd35: msg_byte = h(id[11:8]);
                6'd36: msg_byte = h(id[7:4]);
                6'd37: msg_byte = h(id[3:0]);
                6'd38: msg_byte = 8'h0D;
                6'd39: msg_byte = 8'h0A;
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
                if (msg_idx == 6'd39) begin
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
